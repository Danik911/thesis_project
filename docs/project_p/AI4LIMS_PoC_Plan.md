# AI4LIMS Proof of Concept - Implementation Plan

## Context

The project scope is a **2-week Proof of Concept** that demonstrates AI-powered extraction from pharmaceutical test method PDFs into structured LabWare LIMS MDA (Method Definition and Analysis) templates, with interactive chat refinement.

**Branch**: `prjoject_p_protatype` (created from `thesis_project`)

**Approach**: Reuse `thesis_project` infrastructure (Next.js, FastAPI, LlamaIndex, ChromaDB, Docker). All new code is **additive** — existing thesis functionality is preserved via feature flags and separate files.

### What the PoC must demonstrate:
1. Upload an actual PDF test method (e.g., LAB-2499: Dye-Binding Identity Test, 19 pages)
2. AI extracts all structured information (equipment, reagents, procedures, calculations, acceptance criteria)
3. AI generates a preliminary MDA template (the 10-sheet XLSX format used by LabWare)
4. Operator chats with AI: asks questions, requests modifications ("change this compound", "why did you choose this?")
5. AI produces a refined final MDA after the conversation
6. Small vector store with a few example MDA templates for reference (not 22K, just demo samples)

### Existing assets to reuse:
- **thesis_project**: Next.js UI, LlamaIndex workflows, ChromaDB, FastAPI, Docker, AWS deployment scripts
- **Example files**: 2 PDF inputs + 2 XLSX outputs in `project_docs/parced_example_files/`

---

## Architecture

```
User -> Next.js Frontend -> FastAPI (/lims/*) -> Processing Pipeline
         |                      |
         |-- PDF Upload         |-- /lims/extract  (PDF -> LlamaExtract -> structured MDA)
         |-- MDA Table View     |-- /lims/chat     (conversational MDA refinement)
         |-- Chat Interface     |-- /lims/export   (XLSX download)
         |-- XLSX Download      |-- /lims/status   (extraction progress)

Processing Pipeline:
  1. PDF Upload -> Store locally
  2. LlamaExtract: Schema-based extraction -> structured JSON
  3. ChromaDB RAG: Query mda_templates for similar examples
  4. LlamaIndex Workflow: Combine extraction + RAG -> full MDA template (Pydantic)
  5. Chat Engine: LlamaIndex chat with MDA + PDF context
  6. XLSX Export: openpyxl -> 10-sheet LabWare format
```

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **UI** | Next.js (reuse thesis_project) | Already built: 3D effects, Framer Motion, responsive. Production-quality for stakeholder demo. |
| **Not Streamlit** | Rejected | Would lose existing polished UI, require rebuilding from scratch. |
| **Auth** | Clerk with feature flag OFF | `NEXT_PUBLIC_AUTH_ENABLED=false`. Already integrated, toggle via env var. No auth for PoC. |
| **Extraction** | LlamaExtract (LlamaIndex Cloud) | Schema-based, native LlamaIndex integration, citations + confidence scores. |
| **Migration strategy** | Additive (never modify, always add) | New files alongside existing. Both thesis and LIMS coexist on same branch. |

---

## Tech Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **UI** | Next.js 14 (reuse from thesis_project) | Already built: 3D effects, Framer Motion, responsive. Production-quality for demo. |
| **Extraction** | LlamaExtract (LlamaIndex Cloud) | Schema-based, native LlamaIndex integration, citations + confidence scores. |
| **Extraction Backup** | AWS Bedrock Data Automation | Available in eu-west-2, Blueprint-driven. For production path. |
| **Chat LLM** | GPT-5 / Claude Opus 4.6 via OpenRouter | Best quality vision + reasoning. OpenRouter provides model routing. |
| **RAG Framework** | LlamaIndex (reuse patterns) | Existing team expertise. Workflow + @step patterns. |
| **Vector Store** | ChromaDB (separate `mda_templates` collection) | Reuse adapter, different data. Isolated from thesis `pharmaceutical_regulations`. |
| **PDF Parsing** | LlamaExtract (built-in) + PyMuPDF (fallback/preview) | LlamaExtract handles parsing internally. PyMuPDF for preview rendering. |
| **Data Models** | Pydantic v2 | Structured MDA output (10 sheets as typed models). |
| **Export** | openpyxl | Generate downloadable XLSX matching LabWare format. |
| **Deployment** | Docker (local first) | `docker-compose.lims.yml` for PoC. AWS ECS available post-PoC. |

---

## Document Extraction: Service Evaluation

### LLM Landscape (February 2026)

| Model | Vision Quality | Structured Output | API Price (input/output per 1M tokens) |
|-------|---------------|-------------------|----------------------------------------|
| **GPT-5** | 84.2% MMMU (best) | Responses API | ~$10/$30 |
| **GPT-5.2 Thinking** | Best charts/diagrams (half error rate) | Yes | Higher |
| **Claude Opus 4.6** | Excellent reasoning | Tool use | ~$15/$75 |
| **Claude Sonnet 4.5** | Good | Yes | ~$3/$15 |
| **GPT-4o** | Good | Yes | ~$2.50/$10 |

All available via [OpenRouter](https://openrouter.ai/models). GPT-5 and Claude Opus 4.6 also available on [AWS Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html).

### Extraction Services Compared

| Service | Rating | Setup Time | PoC Cost (380 pages) | Key Strength | Key Weakness |
|---------|--------|-----------|----------|--------------|--------------|
| **LlamaExtract** (chosen) | 4/5 | 0.5 day | $2-23 | Native LlamaIndex, schema-based, citations | Newer for complex pharma tables |
| AWS Bedrock Data Automation | 4/5 | 1-2 days | ~$4 | AWS ecosystem, Blueprint optimization | 20-page limit, newer service |
| Azure Content Understanding | 4.5/5 | 0.5-1 day | $2-8 | Zero-shot, best for quick PoC | Very new (GA Nov 2025), hallucination risk |
| AWS Textract | 3/5 | 2-3 days | ~$15 | Best table extraction | Requires LLM orchestration on top |
| Azure Document Intelligence | 3.5/5 | 3-5 days | $4-11 | Custom model training | Training loop too slow for 2-week PoC |
| Vision LLM Direct (GPT-5/Claude) | 3.5/5 | 0.5 day | $4-20 | Maximum flexibility | Non-deterministic for stakeholder demo |
| LlamaParse (parsing only) | 3/5 | 0.5 day | $1-43 | Good parser | Not an extractor, needs LLM layer |
| Google Document AI | 2.5/5 | 2-3 days | ~$40 | Custom extractor | Hosting cost, separate cloud |
| Unstructured.io | 2.5/5 | 1-2 days | Free | Open source | Parser only, needs LLM layer |

### Decision: LlamaExtract (Primary)

**Why LlamaExtract wins:**
1. Native LlamaIndex integration — team already has expertise
2. Schema-based extraction maps directly to MDA Pydantic models
3. Built on LlamaParse (best PDF parser) + LLM extraction
4. Citations and confidence scores for auditability
5. Progressive quality tiers: Balanced ($7.60 for PoC) to Premium ($22.80)
6. Python SDK: `pip install llama-cloud`

**Backup: AWS Bedrock Data Automation** — available in eu-west-2, Blueprint-driven, for production path.

### LlamaExtract Integration Pattern

```python
from llama_cloud import LlamaExtract

extractor = LlamaExtract(api_key=os.getenv("LIMS_LLAMAEXTRACT_API_KEY"))

# Define schema matching MDA Pydantic models
mda_schema = {
    "analyses": {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Analysis name e.g. AND_ACS_DYE"},
                "analysis_type": {"type": "string", "description": "Type: ID, APPEARANCE, QC_SAMPLES"},
                "description": {"type": "string"},
                # ... all Analysis fields
            }
        }
    },
    "components": { ... },
    "calculations": { ... },
    # ... all 10 MDA sheets
}

# Extract structured data from pharmaceutical PDF
result = extractor.extract(
    file="test_method.pdf",
    schema=mda_schema,
    mode="balanced"  # Options: fast, balanced, multimodal, premium
)

# Direct Pydantic parsing
mda_template = MDATemplate(**result.data)
```

### Sources

- [LlamaExtract Getting Started](https://developers.llamaindex.ai/python/cloud/llamaextract/getting_started/)
- [LlamaExtract Overview](https://www.llamaindex.ai/llamaextract)
- [LlamaIndex Cloud](https://developers.llamaindex.ai/python/cloud/)
- [AWS Bedrock Data Automation](https://docs.aws.amazon.com/bedrock/latest/userguide/bda.html)
- [AWS BDA Blueprint Optimization (Dec 2025)](https://aws.amazon.com/about-aws/whats-new/2025/12/bedrock-data-automation-optimization-document-blueprints/)
- [Azure Content Understanding](https://learn.microsoft.com/en-us/azure/ai-services/content-understanding/overview)
- [Azure Document Intelligence](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/model-overview)
- [GPT-5](https://openai.com/index/introducing-gpt-5/) | [GPT-5.2](https://openai.com/index/introducing-gpt-5-2/) | [GPT-5.3 Codex](https://openai.com/index/introducing-gpt-5-3-codex/)
- [Claude Opus 4.6 on Bedrock](https://aws.amazon.com/about-aws/whats-new/2026/2/claude-opus-4.6-available-amazon-bedrock/)
- [OpenRouter Models](https://openrouter.ai/models)
- [BDA vs Textract Analysis](https://community.mantelgroup.com.au/articles/post/an-analysis-of-traditional-document-automation-vs-bedrock-data-automation-AGIT3tU0nZcKzgP)

---

## Data Models (Pydantic v2)

Based on the example XLSX files, the MDA template has 10 sheets:

```python
class Analysis(BaseModel):
    name: str                    # e.g. "AND_ACS_DYE"
    version: int
    group_name: str              # e.g. "ANDOVER"
    active: bool
    reported_name: str           # e.g. "ACS Dye Binding"
    common_name: str
    analysis_type: str           # e.g. "ID", "APPEARANCE", "QC_SAMPLES"
    description: str
    # ... ~80 more fields (most are flags/defaults)

class Component(BaseModel):
    analysis: str
    component_name: str
    version: int
    order_number: int
    result_type: str             # N=numeric, T=text, L=list, K=calculated, D=date
    units: str
    minimum: Optional[float]
    maximum: Optional[float]
    uses_instrument: bool
    auto_calc: bool
    list_key: Optional[str]      # e.g. "YES_NO_2", "PASS_FAIL"
    reportable: bool
    # ...

class CalcVariable(BaseModel):
    analysis: str
    component: str
    name: str                    # variable name used in LIMS Basic
    version: int
    reference_type: str          # C=component, A=attribute
    reference_name: str
    attribute_1: str
    return_value: str
    scope: str
    function: str

class Calculation(BaseModel):
    analysis: str
    component: str
    version: int
    description: str
    source_code: str             # LIMS Basic code

class MDATemplate(BaseModel):
    """Complete 10-sheet MDA template"""
    analyses: List[Analysis]
    components: List[Component]
    component_codes: List[ComponentCode]
    component_factors: List[ComponentFactor]
    component_variations: List[ComponentVariation]
    calc_variables: List[CalcVariable]
    calculations: List[Calculation]
    analysis_limits: List[AnalysisLimit]
    analysis_methods: List[AnalysisMethod]
    analysis_variations: List[AnalysisVariation]
```

---

## Migration Strategy: Safe, Additive

### Principle: Never Modify, Always Add

Both the thesis system and LIMS PoC coexist on the same branch. Toggle via environment variables.

| Risk Area | Strategy | Implementation |
|-----------|----------|----------------|
| Frontend auth | Feature flag | `NEXT_PUBLIC_AUTH_ENABLED=false` in `.env.local` |
| Frontend pages | New pages alongside existing | `pages/lims.tsx` alongside `pages/generate.tsx` |
| API routes | Separate router | `lims_router.py` mounted at `/lims/*` |
| Docker stack | Separate compose file | `docker-compose.lims.yml` (minimal: frontend + API) |
| ChromaDB | Separate collection | `mda_templates` at `chroma_db_lims/` (thesis `pharmaceutical_regulations` untouched) |
| Config | Separate namespace | `LIMS_*` prefixed env vars, `LIMSConfig` class |
| Dependencies | Test compatibility first | Verify before adding to `pyproject.toml` |

### Files to Modify (MINIMAL, non-destructive)

| File | Change | Risk |
|------|--------|------|
| `main/frontend/pages/_app.tsx` | Conditional ClerkProvider wrapper (feature flag) | LOW |
| `main/frontend/components/Layout.tsx` | Add "LIMS" nav link alongside existing links | LOW |
| `main/frontend/middleware.ts` | Add `/lims` to public routes list | LOW |
| `main/api/app.py` | Mount lims_router: `app.include_router(lims_router, prefix="/lims")` | LOW |
| `pyproject.toml` | Add `llama-cloud`, `openpyxl`, `PyMuPDF` (test compatibility first) | MEDIUM |

### Files to Create (NEW, nothing replaced)

```
thesis_project/                      # Existing repo
├── docker-compose.lims.yml          # NEW: Minimal Docker stack (frontend + API)
├── main/
│   ├── api/
│   │   └── lims_router.py           # NEW: LIMS API endpoints (/extract, /chat, /export)
│   ├── src/
│   │   └── lims/                    # NEW: All LIMS logic in separate package
│   │       ├── __init__.py
│   │       ├── mda_models.py        # 10-sheet MDA Pydantic models
│   │       ├── pdf_extractor.py     # LlamaExtract integration
│   │       ├── mda_generator.py     # LlamaIndex workflow for MDA generation
│   │       ├── chat_agent.py        # Chat engine for interactive refinement
│   │       ├── xlsx_exporter.py     # XLSX export (openpyxl)
│   │       ├── config.py            # LIMS-specific config (LIMS_* env vars)
│   │       └── prompts/
│   │           ├── extraction_prompt.py
│   │           ├── mda_generation_prompt.py
│   │           └── chat_system_prompt.py
│   └── frontend/
│       ├── pages/
│       │   └── lims.tsx             # NEW: Main LIMS page (upload -> extract -> chat -> export)
│       └── components/
│           ├── ChatInterface.tsx     # NEW: Chat UI component (streaming)
│           ├── MDAViewer.tsx         # NEW: Tabbed MDA table viewer (10 sheets)
│           └── PDFPreview.tsx        # NEW: PDF preview component
```

### Files Untouched (ZERO changes)

- `main/frontend/pages/generate.tsx`, `history.tsx` — thesis job flows preserved
- `docker-compose.dev.yml` — original 5-service stack preserved
- `main/api/worker.py`, `dependencies.py` — thesis infrastructure preserved
- `main/src/agents/` — all thesis agents preserved
- `main/src/core/unified_workflow.py` — thesis workflow preserved
- `chroma_db/` — `pharmaceutical_regulations` collection preserved

---

## Reusable from thesis_project

| Component | Source | How to Reuse |
|-----------|--------|--------------|
| Next.js UI shell | `main/frontend/` (Layout, Header, 3D effects, styles, fonts) | Direct reuse, add LIMS nav link |
| FileUpload | `main/frontend/components/FileUpload.tsx` | Copy pattern, change `.md` filter to `.pdf` |
| Job progress pattern | `main/frontend/components/JobProgress.tsx` | Adapt stages for extraction pipeline |
| ChromaDB adapter | `main/src/adapters/chroma_adapter.py` | Reuse for `mda_templates` collection |
| LlamaIndex workflow | `main/src/core/unified_workflow.py` | Reuse `Workflow` + `@step` patterns |
| Storage adapters | `main/src/adapters/storage.py`, `local_adapter.py` | Reuse for PDF/XLSX file storage |
| Docker patterns | `docker-compose.dev.yml`, `Dockerfile.api` | Adapt for minimal LIMS stack |
| FastAPI patterns | `main/api/app.py` | Reuse lifespan, middleware, healthcheck patterns |
| AWS deployment | `aws/terraform/`, `aws/scripts/` | Available for post-PoC production |
| Framer Motion + 3D | `main/frontend/components/3d/`, `landing/` | Direct reuse for visual polish |

---

## LLM Prompt Strategy

### Extraction Schema Prompt (Critical)
The LlamaExtract schema must:
1. Define all 10 MDA sheets as nested JSON schema objects
2. Include field descriptions with LIMS-specific context (e.g., "result_type: N=numeric, T=text, L=list, K=calculated, D=date")
3. Explain naming conventions (e.g., "AND_ACS_DYE" = site_prefix + method_abbreviation)
4. Reference LIMS Basic code patterns for calculation fields

The RAG context (from ChromaDB `mda_templates`) provides 1-2 similar MDA templates as few-shot examples.

### Chat System Prompt
The chat agent must:
1. Know the full content of the uploaded PDF
2. Know the current state of the MDA template (all 10 sheets)
3. Be able to explain why it made specific extraction decisions (using LlamaExtract citations)
4. Modify the MDA when the operator requests changes
5. Ask clarifying questions when modifications are ambiguous
6. Know LIMS conventions (naming patterns, result types, calculation variable scoping)

---

## Implementation Plan (2 Weeks)

### Day 0: Setup (Pre-work)
- [ ] Sign up for [LlamaIndex Cloud](https://developers.llamaindex.ai/python/cloud/), get API key
- [ ] Test `pip install llama-cloud openpyxl PyMuPDF` compatibility with existing deps
- [ ] Create `docker-compose.lims.yml` (minimal: frontend + API)
- [ ] Create `main/src/lims/` package structure
- [ ] Set up `LIMS_*` environment variables in `.env.local`

### Week 1: Core Pipeline

#### Day 1-2: Extraction + Models
- [ ] Define all 10 MDA Pydantic models (`main/src/lims/mda_models.py`)
- [ ] Build LlamaExtract schema matching Pydantic models
- [ ] Implement `pdf_extractor.py` with LlamaExtract integration
- [ ] Test extraction on example PDF (ex_2_was_pdf)
- [ ] Create `lims_router.py` with `/lims/extract` endpoint

#### Day 3-4: RAG + MDA Generation
- [ ] Populate ChromaDB `mda_templates` collection with 2-5 example MDAs
- [ ] Build LlamaIndex workflow for MDA generation (`mda_generator.py`):
  - Step 1: Extract raw data (LlamaExtract)
  - Step 2: Query ChromaDB for similar MDA templates
  - Step 3: Generate full MDA using extracted data + RAG context
  - Step 4: Generate LIMS Basic code for calculations
- [ ] Wire workflow to `/lims/extract` endpoint

#### Day 5: Frontend MDA Display
- [ ] Build `MDAViewer.tsx` (tabbed tables, one tab per MDA sheet, using `@tanstack/react-table`)
- [ ] Build `pages/lims.tsx` (upload -> extract -> display flow)
- [ ] Modify `Layout.tsx` to add "LIMS" nav link
- [ ] Modify `_app.tsx` with conditional ClerkProvider
- [ ] Wire API -> frontend data flow

### Week 2: Chat + Polish

#### Day 6-7: Chat Interface
- [ ] Build `ChatInterface.tsx` (streaming responses, markdown rendering)
- [ ] Build `chat_agent.py` (LlamaIndex chat engine with MDA + PDF context)
- [ ] Enable MDA modification via conversation:
  - "Change the units for component X to milligrams"
  - "Add a new component for temperature measurement"
  - "Why did you set result_type to K for this component?"
  - "The calculation for dye volume is wrong, it should be..."
- [ ] Create `/lims/chat` endpoint
- [ ] After each modification, update displayed MDA tables in real-time

#### Day 8: XLSX Export + Testing
- [ ] Build `xlsx_exporter.py` (openpyxl, 10-sheet format matching LabWare)
- [ ] Create `/lims/export` endpoint
- [ ] Test full pipeline: Upload ex_2_was_pdf -> extract -> compare with ex_2_was_xlsx
- [ ] Accuracy assessment: compare AI output vs. human-created MDA

#### Day 9-10: Polish + Demo
- [ ] PDF preview component (`PDFPreview.tsx`) - optional
- [ ] Progress indicators during extraction
- [ ] Confidence indicators on extracted fields (from LlamaExtract citations)
- [ ] Error handling for edge cases
- [ ] Demo preparation and rehearsal
- [ ] Deployment option: Local Docker (always works) or AWS ECS (reuse thesis Terraform)

---

## Risk Analysis & Mitigations

### Migration Risks (Breaking Existing Functionality)

| Risk | Severity | Mitigation |
|------|----------|-----------|
| **Dependency conflicts** (`llama-cloud` + existing pinned versions) | HIGH | Test installation in isolation first (Day 0). Separate virtualenv if needed. |
| **Frontend auth breakage** (removing Clerk breaks all pages) | HIGH | Feature flag `NEXT_PUBLIC_AUTH_ENABLED`, NOT removal. Both modes coexist. |
| **Docker compose changes** break thesis dev stack | MEDIUM | Separate `docker-compose.lims.yml`. Original `docker-compose.dev.yml` untouched. |
| **Modifying `app.py`** breaks existing API | MEDIUM | Mount new router at `/lims/*`. One-line addition, existing routes untouched. |
| **ChromaDB corruption** (thesis `pharmaceutical_regulations`) | MEDIUM | Separate collection `mda_templates` at `chroma_db_lims/`. |
| **Shared config conflicts** | LOW | `LIMS_*` prefixed env vars. Separate `LIMSConfig` class. |
| **Frontend page conflicts** | LOW | New `pages/lims.tsx`. Existing `pages/generate.tsx` untouched. |

### PoC-Specific Risks

| Risk | Severity | Mitigation |
|------|----------|-----------|
| LlamaExtract can't handle complex pharmaceutical tables | MEDIUM | Test on example PDF Day 1. Fallback: GPT-5 vision via OpenRouter or AWS BDA. |
| 19-page PDF exceeds extraction limits | MEDIUM | Page-by-page extraction with cross-page context assembly. |
| Chat modifications break MDA consistency | MEDIUM | Pydantic validation after each modification rejects invalid state. |
| LLM hallucinates LIMS Basic code | MEDIUM | RAG provides real examples. Post-processing validates syntax. |
| 2-week timeline too tight | MEDIUM | Week 1 = MVP (extraction + display). Chat = Week 2 stretch goal. |
| LlamaExtract API quota/access issues | LOW | Sign up early (Day 0), verify API access before committing. |

---

## Verification Plan

1. **Extraction accuracy**: Upload `ex_2_was_pdf` -> compare AI-generated MDA against human-created `ex_2_was_xlsx`
   - All Analysis objects identified correctly
   - Components match (names, types, units, order)
   - Calculation variables correctly cross-referenced
   - LIMS Basic code logic matches (conditional logic, formulas)
2. **Chat functionality**: Can the operator successfully:
   - Ask why a component was created a certain way
   - Request a modification and see it reflected in the table
   - Ask questions about the source PDF content
3. **XLSX export**: Generated file opens in Excel with correct 10-sheet formatting
4. **End-to-end demo**: PDF upload -> AI extraction -> MDA display -> chat refinement -> XLSX download
5. **Thesis preservation**: Run `docker-compose -f docker-compose.dev.yml up -d` -> verify original thesis system still works

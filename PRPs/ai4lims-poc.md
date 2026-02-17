# AI4LIMS Proof of Concept - Production Readiness Plan (PRP)

**Owner:** Platform Engineering (AI Systems)
**Date:** 2026-02-16
**Version:** 1.2
**Scope:** 2-week Proof of Concept — AI-powered extraction from pharmaceutical test method PDFs into structured LabWare LIMS MDA (Method Definition and Analysis) templates, with interactive chat refinement.
**Branch:** `prjoject_p_protatype`
**Source Plan:** `docs/project_p/AI4LIMS_PoC_Plan.md`

---

## Executive Summary

This PRP outlines a 2-week Proof of Concept that demonstrates AI-powered extraction from pharmaceutical test method PDFs into structured LabWare LIMS MDA templates. The system reuses the existing `thesis_project` infrastructure (Next.js, FastAPI, LlamaIndex, ChromaDB, Docker) with a strict **additive-only** migration strategy — no existing thesis code is modified beyond minimal, non-destructive additions.

**What the PoC must demonstrate:**
1. Upload a real PDF test method (e.g., LAB-2499: Dye-Binding Identity Test, 19 pages)
2. AI extracts all structured information (equipment, reagents, procedures, calculations, acceptance criteria)
3. AI generates a preliminary MDA template (4 core sheets: Analysis, Component, CalcVariable, Calculation)
4. Operator chats with AI: asks questions, requests modifications
5. AI produces a refined final MDA after conversation
6. Small vector store with example MDA templates for reference (demo samples, not 22K)

**Key Decisions:**
- **Extraction:** LlamaExtract (LlamaIndex Cloud) — schema-based, native LlamaIndex integration, citations + confidence scores
- **Chat LLM:** GPT-5 / Claude Opus 4.6 via OpenRouter — best quality vision + reasoning
- **RAG:** ChromaDB (`mda_templates` collection) — separate from thesis `pharmaceutical_regulations`
- **Export:** openpyxl — 4-sheet XLSX matching LabWare format
- **Auth:** Clerk with route-based exclusion (`/lims` routes not in `isProtectedRoute`)
- **Docker:** `docker-compose.lims.yml` — minimal stack (frontend + API only)
- **Migration:** Additive only — never modify thesis files, always add new ones
- **Estimated PoC cost:** $2-23 (LlamaExtract) + OpenRouter LLM costs

---

## 1. Architecture Overview

### 1.1 Local Development Stack (AI4LIMS PoC)

```
+-----------------------------------------------------------------+
|                   AI4LIMS PoC - LOCAL DEVELOPMENT                |
+-----------------------------------------------------------------+
|                                                                   |
|  +---------------+      +------------------+                     |
|  |   Next.js     |----->|   FastAPI         |                    |
|  |   Frontend    |      |   Backend         |                    |
|  |  (Port 3000)  |      |  (Port 8080)      |                   |
|  |               |      |                    |                   |
|  |  pages/       |      |  /lims/extract     |                   |
|  |    lims.tsx   |      |  /lims/chat        |                   |
|  |               |      |  /lims/export      |                   |
|  |  components/  |      |  /lims/status      |                   |
|  |    MDAViewer  |      |                    |                   |
|  |    ChatUI     |      +--------+-----------+                   |
|  +---------------+               |                               |
|                         +--------+-----------+                   |
|                         |                    |                   |
|                         v                    v                   |
|                  +-------------+    +-----------------+          |
|                  |  ChromaDB   |    |  LlamaExtract   |          |
|                  | mda_templates|   |  (Cloud API)    |          |
|                  | Port 8001   |    |                 |          |
|                  +-------------+    +-----------------+          |
|                                                                   |
|  PDF Storage: ./uploads/lims/                                    |
|  XLSX Output: ./output/lims/                                     |
|  Config: .env.local (LIMS_* prefixed)                            |
+-----------------------------------------------------------------+
```

### 1.2 Processing Pipeline

```
PDF Upload
    |
    v
[1. Store PDF locally]
    |
    v
[2. LlamaExtract: Schema-based extraction -> structured JSON]
    |
    v
[3. ChromaDB RAG: Query mda_templates for similar examples]
    |
    v
[4. LlamaIndex Workflow: Combine extraction + RAG -> full MDA (Pydantic)]
    |
    v
[5. Chat Engine: LlamaIndex chat with MDA + PDF context]
    |
    v
[6. XLSX Export: openpyxl -> 4-sheet LabWare format]
```

### 1.3 Refinement Workflow (Initial vs Final)

To avoid ambiguity between "first draft" and "final output," the PoC uses two explicit flows:

1. **Initial generation flow (deterministic):**
  - PDF upload -> LlamaExtract -> MDA generation workflow -> initial `MDATemplate`
2. **Refinement flow (interactive):**
  - User chat messages -> structured edit actions -> Pydantic validation -> in-memory state update
3. **Finalization step (explicit):**
  - User requests final output -> latest validated MDA state is exported to XLSX

This means chat does not bypass the workflow; it proposes/executes bounded edits on the generated MDA state, then final export uses the refined state.

### 1.4 Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **UI** | Next.js (reuse thesis_project) | Already built: 3D effects, Framer Motion, responsive. Production-quality for stakeholder demo. |
| **Not Streamlit** | Rejected | Would lose existing polished UI, require rebuilding from scratch. |
| **Auth** | Clerk with route-based exclusion | `/lims` routes excluded from `isProtectedRoute` in `middleware.ts`. ClerkProvider stays in `_app.tsx` (unchanged). No auth for LIMS pages; thesis pages retain auth. |
| **Extraction** | LlamaExtract (LlamaIndex Cloud) | Schema-based, native LlamaIndex integration, citations + confidence scores. |
| **Migration strategy** | Additive (never modify, always add) | New files alongside existing. Both thesis and LIMS coexist on same branch. |
| **Orchestration** | LlamaIndex `Workflow` as primary orchestrator | Deterministic state transitions, easier contract testing and auditability. |
| **Agent usage** | Bounded sub-tasks only | Use agent-like behavior for edit proposal/explanation, not for top-level orchestration. |
| **Task ID prefix** | `L` (L0.1, L1.1, etc.) | Avoids collision with existing thesis PRP task IDs (0.1-7.1). |

---

## 2. Tech Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **UI** | Next.js 14 (reuse from thesis_project) | Already built: 3D effects, Framer Motion, responsive. Production-quality for demo. |
| **Extraction** | LlamaExtract (LlamaIndex Cloud) | Schema-based, native LlamaIndex integration, citations + confidence scores. |
| **Extraction Backup** | AWS Bedrock Data Automation | Available in eu-west-2, Blueprint-driven. For production path. |
| **Chat LLM** | GPT-5 / Claude Opus 4.6 via OpenRouter | Best quality vision + reasoning. OpenRouter provides model routing. |
| **RAG Framework** | LlamaIndex (reuse patterns) | Existing team expertise. Workflow + @step patterns. |
| **Vector Store** | ChromaDB (separate `mda_templates` collection) | Reuse adapter, different data. Isolated from thesis `pharmaceutical_regulations`. |
| **PDF Parsing** | LlamaExtract (built-in) + PyMuPDF (preview) | LlamaExtract handles parsing internally. PyMuPDF for preview rendering. |
| **Data Models** | Pydantic v2 | 4 core sheets as typed models. Full schema in `mda_schema.py`. |
| **Export** | openpyxl | Generate downloadable XLSX matching LabWare format. |
| **Deployment** | Docker (local first) | `docker-compose.lims.yml` for PoC. AWS ECS available post-PoC. |

---

## 3. Document Extraction Research

### 3.1 LLM Landscape (February 2026)

| Model | Vision Quality | Structured Output | API Price (input/output per 1M tokens) |
|-------|---------------|-------------------|----------------------------------------|
| **GPT-5** | 84.2% MMMU (best) | Responses API | ~$10/$30 |
| **GPT-5.2 Thinking** | Best charts/diagrams (half error rate) | Yes | Higher |
| **Claude Opus 4.6** | Excellent reasoning | Tool use | ~$15/$75 |
| **Claude Sonnet 4.5** | Good | Yes | ~$3/$15 |
| **GPT-4o** | Good | Yes | ~$2.50/$10 |

All available via [OpenRouter](https://openrouter.ai/models). GPT-5 and Claude Opus 4.6 also available on [AWS Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html).

### 3.2 Extraction Services Compared

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

### 3.3 Decision: LlamaExtract (Primary)

**Why LlamaExtract wins:**
1. Native LlamaIndex integration — team already has expertise
2. Schema-based extraction maps directly to MDA Pydantic models
3. Built on LlamaParse (best PDF parser) + LLM extraction
4. Citations and confidence scores for auditability
5. Progressive quality tiers: Balanced ($7.60 for PoC) to Premium ($22.80)
6. Python SDK: `pip install llama-cloud`

**Backup: AWS Bedrock Data Automation** — available in eu-west-2, Blueprint-driven, for production path.

### 3.4 LlamaExtract Integration Pattern

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
    "components": { "..." },
    "calculations": { "..." },
    # ... all 4 core MDA sheets
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

### 3.5 Sources

- [LlamaExtract Getting Started](https://developers.llamaindex.ai/python/cloud/llamaextract/getting_started/)
- [LlamaExtract Overview](https://www.llamaindex.ai/llamaextract)
- [LlamaIndex Cloud](https://developers.llamaindex.ai/python/cloud/)
- [AWS Bedrock Data Automation](https://docs.aws.amazon.com/bedrock/latest/userguide/bda.html)
- [Azure Content Understanding](https://learn.microsoft.com/en-us/azure/ai-services/content-understanding/overview)
- [GPT-5](https://openai.com/index/introducing-gpt-5/) | [Claude Opus 4.6 on Bedrock](https://aws.amazon.com/about-aws/whats-new/2026/2/claude-opus-4.6-available-amazon-bedrock/)
- [OpenRouter Models](https://openrouter.ai/models)

---

## 4. Data Models (Pydantic v2) — Ground Truth Corrected

All models live in `main/src/lims/mda_schema.py`. Schemas are based on ground truth from a real LabWare LIMS build (ACS Dye-Binding Identity Test), not PDF prediction alone.

### 4.1 PoC Scope: 4 Core Sheets

The PoC targets 4 of the 10 MDA sheets. Ground truth analysis of the ACS Dye-Binding test method shows only 25 components across 3 analyses — the remaining 6 sheets (ComponentCode, ComponentFactor, ComponentVariation, AnalysisLimit, AnalysisMethod, AnalysisVariation) are empty or trivial for this test method and can be added post-PoC.

| Sheet # | Sheet Name | Model | Purpose | Expected Count (Ground Truth) |
|---------|-----------|-------|---------|-------------------------------|
| 1 | Analysis | `Analysis` | Top-level test method definitions | 3 (Primary + CTL + META) |
| 2 | Component | `Component` | Individual test parameters per analysis | 25 (9 + 7 + 9) |
| 6 | Calc Variable | `CalcVariable` | Variables used in LIMS Basic calculations | ~15-20 |
| 7 | Calculation | `Calculation` | LIMS Basic code for K-type components | ~10-15 |

Full schema with 9 enums, 4 models, and cross-sheet referential integrity validators: see `main/src/lims/mda_schema.py`.

### 4.2 Three-Analysis Pattern

Ground truth reveals that a single PDF test method maps to **three** LabWare analyses, not one:

| Analysis Name | Type | Components | Role |
|---------------|------|-----------|------|
| `AND_ACS_DYE` | `ID` | 9 | **Primary** — core test parameters (absorbances, dye volume, pass/fail) |
| `AND_ACS_DYE_CTL` | `QC_SAMPLES` | 7 | **Control** — owns Sponge Size (the conditional driver), equipment pickers |
| `AND_ACS_DYE_META` | `QC_SAMPLES` | 9 | **Metadata** — operator, date, equipment IDs, batch-level information |

**Naming convention:** `{SITE_PREFIX}_{METHOD_ABBREV}[_{SUFFIX}]` where:
- Site prefix = `AND` (Andover) — validated by the `Analysis.validate_site_prefix` validator
- CTL/META suffixes = `QC_SAMPLES` type — enforced by the `Analysis.validate_qc_samples_suffix` validator

**Critical insight:** The CTL analysis owns the conditional driver component (Sponge Size). The primary analysis references it **cross-analysis** via CALC_VARIABLES to compute Dye Volume Expected. This means extraction must correctly identify which analysis owns which component.

### 4.3 Component Type Classification Rules

Mapping PDF text patterns to `ResultType` is the most error-prone part of extraction. These rules are derived from ground truth:

| PDF Pattern | Result Type | LIMS Mechanism | Example |
|-------------|-------------|----------------|---------|
| Visual yes/no question | `L` | `YES_NO_2` list | "Is the solution clear?" |
| Measurement with instrument | `N` | `uses_instrument=True` | Absorbance at 595nm |
| Value from formula | `K` | LIMS Basic calculation (`auto_calc=True`) | Dye Volume Expected |
| Equipment selection | `K` | `GOSUB CALC_INST_PICKER` | Spectrophotometer |
| Reagent/standard selection | `K` | `GOSUB CALC_SR_PICKER` | Petri Dish, Direct Red 80 |
| Date entry | `D` | Date picker | Analysis Date |
| Free text | `T` | Text entry | Analyst Comment |

**Common misclassifications from PDF text:**

| PDF Text | Wrong Guess | Correct Type | Why |
|----------|------------|-------------|-----|
| "Direct Red 80 Solution Used" | L (looks like a list) | **K** | IF/ELSE conditional in LIMS Basic |
| "Petri Dish" | L (looks like equipment list) | **K** | GOSUB CALC_SR_PICKER |
| "Timer" | N (looks numeric) | **K** | Instrument Group code, not a measurement |
| Reagent prep steps | N (measurement decomposition) | **K** | Reagents use S/R Pickers, NOT measurement decomposition |

**Validation rules enforced in `Component` model:**
- `K` requires `auto_calc=True`
- `L` requires a `list_key` (e.g., `YES_NO_2`, `PASS_FAIL`)
- `N` with `uses_instrument=True` should have an `instrument_group`

### 4.4 Cross-Analysis CALC_VARIABLES Pattern

CALC_VARIABLES enable calculations to reference values from other components — either within the same analysis or across analyses.

| Reference Type | Scope | Use Case | Example |
|---------------|-------|----------|---------|
| `C` (within-analysis) | `CR` (CurrentResult) | Formula references a sibling component | Absorbance_1 -> Dye Volume calc |
| `A` (cross-analysis) | `B` (Batch) | Formula references a component in another analysis | CTL.Sponge_Size -> Primary.Dye_Volume_Expected |

**Key example:** Sponge Size lives in `AND_ACS_DYE_CTL` (Control analysis). The primary analysis `AND_ACS_DYE` needs Sponge Size to compute Dye Volume Expected. This is achieved via:
```
CalcVariable(
    analysis="AND_ACS_DYE",
    component="DYE_VOLUME_EXPECTED",
    name="SPONGE_SIZE",
    reference_type="A",           # Cross-analysis
    reference_analysis="AND_ACS_DYE_CTL",
    reference_component="SPONGE_SIZE",
    scope="B",                    # Batch-level resolution
    function="ENTRY",
)
```

**Validation:** The `CalcVariable` model requires `reference_analysis` when `reference_type=A`. The `MDATemplate` root validator ensures all referenced analyses exist.

### 4.5 Aggregate Model Summary

```python
class MDATemplate(BaseModel):
    """4 core sheets with cross-sheet referential integrity."""
    analyses: List[Analysis]          # Sheet 1
    components: List[Component]       # Sheet 2
    calc_variables: List[CalcVariable] # Sheet 6
    calculations: List[Calculation]   # Sheet 7
```

**Cross-sheet validators (on `MDATemplate`):**
1. Every component references a valid analysis
2. Every K-type component has at least one calculation
3. CalcVariable references resolve to existing analyses/components
4. Calculation references point to valid analyses

All models use `model_config = ConfigDict(extra="allow", str_strip_whitespace=True, use_enum_values=True)` to handle unexpected fields from LlamaExtract.

---

## 5. API Endpoints

All LIMS endpoints are mounted under `/lims/*` via a separate `lims_router.py`. Existing thesis routes are untouched.

| Endpoint | Method | Purpose | Request | Response |
|----------|--------|---------|---------|----------|
| `/lims/extract` | POST | Upload PDF, trigger extraction pipeline | `multipart/form-data` (PDF file) | `{ job_id, status }` |
| `/lims/status/{job_id}` | GET | Poll extraction progress | - | `{ status, progress_pct, current_step, mda_template? }` |
| `/lims/chat` | POST | Send chat message, receive MDA modifications | `{ job_id, message }` | `{ response, updated_mda?, citations? }` |
| `/lims/export/{job_id}` | GET | Download MDA as XLSX | - | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |

---

## 6. Migration Strategy: Safe, Additive

### 6.1 Principle: Never Modify, Always Add

Both the thesis system and LIMS PoC coexist on the same branch. Toggle via environment variables.

| Risk Area | Strategy | Implementation |
|-----------|----------|----------------|
| Frontend auth | Route-based exclusion | `/lims` not added to `isProtectedRoute` in `middleware.ts` — unprotected by default. `_app.tsx` unchanged. |
| Frontend pages | New pages alongside existing | `pages/lims.tsx` alongside `pages/generate.tsx` |
| API routes | Separate router | `lims_router.py` mounted at `/lims/*` |
| Docker stack | Separate compose file | `docker-compose.lims.yml` (minimal: frontend + API) |
| ChromaDB | Separate collection | `mda_templates` at `chroma_db_lims/` (thesis `pharmaceutical_regulations` untouched) |
| Config | Separate namespace | `LIMS_*` prefixed env vars, `LIMSConfig` class |
| Dependencies | Test compatibility first | Verify before adding to `pyproject.toml` |

### 6.2 Files to Modify (MINIMAL, non-destructive)

| File | Change | Risk |
|------|--------|------|
| `main/frontend/components/Layout.tsx` | Add "LIMS" nav link alongside existing links | LOW |
| `main/frontend/middleware.ts` | Ensure `/lims` is NOT in `isProtectedRoute` (it's already unprotected by default) | LOW |
| `main/api/app.py` | Mount lims_router: `app.include_router(lims_router, prefix="/lims")` | LOW |
| `pyproject.toml` | Add `llama-cloud`, `openpyxl`, `PyMuPDF` (test compatibility first) | MEDIUM |

> **Note:** `_app.tsx` is NOT modified. The `<ClerkProvider>` wrapper stays as-is. Auth exclusion is handled entirely via route matching in `middleware.ts` — `/lims` routes are simply not added to `isProtectedRoute`, making them public by default.

### 6.3 Files to Create (NEW, nothing replaced)

```
thesis_project/                      # Existing repo
+-- docker-compose.lims.yml          # NEW: Minimal Docker stack (frontend + API)
+-- main/
|   +-- api/
|   |   +-- lims_router.py           # NEW: LIMS API endpoints (/extract, /chat, /export)
|   +-- src/
|   |   +-- lims/                    # NEW: All LIMS logic in separate package
|   |       +-- __init__.py
|   |       +-- mda_schema.py        # 4 core sheet MDA Pydantic models
|   |       +-- pdf_extractor.py     # LlamaExtract integration
|   |       +-- mda_generator.py     # LlamaIndex workflow for MDA generation
|   |       +-- chat_agent.py        # Chat engine for interactive refinement
|   |       +-- xlsx_exporter.py     # XLSX export (openpyxl)
|   |       +-- config.py            # LIMS-specific config (LIMS_* env vars)
|   |       +-- prompts/
|   |           +-- extraction_prompt.py
|   |           +-- mda_generation_prompt.py
|   |           +-- chat_system_prompt.py
|   +-- frontend/
|       +-- pages/
|       |   +-- lims.tsx             # NEW: Main LIMS page
|       +-- components/
|           +-- ChatInterface.tsx     # NEW: Chat UI component (streaming)
|           +-- MDAViewer.tsx         # NEW: Tabbed MDA table viewer (4 core sheets)
|           +-- PDFPreview.tsx        # NEW: PDF preview component
```

### 6.4 Files Untouched (ZERO changes)

- `main/frontend/pages/generate.tsx`, `history.tsx` — thesis job flows preserved
- `docker-compose.dev.yml` — original 5-service stack preserved
- `main/api/worker.py`, `dependencies.py` — thesis infrastructure preserved
- `main/src/agents/` — all thesis agents preserved
- `main/src/core/unified_workflow.py` — thesis workflow preserved
- `chroma_db/` — `pharmaceutical_regulations` collection preserved

---

## 7. Reusable Components from thesis_project

| Component | Source | How to Reuse |
|-----------|--------|--------------|
| Next.js UI shell | `main/frontend/` (Layout, Header, 3D effects, styles, fonts) | Direct reuse, add LIMS nav link |
| FileUpload pattern | `main/frontend/components/FileUpload.tsx` | Copy pattern, change `.md` filter to `.pdf` |
| Job progress pattern | `main/frontend/components/JobProgress.tsx` | Adapt stages for extraction pipeline |
| ChromaDB adapter | `main/src/adapters/chroma_adapter.py` | Reuse for `mda_templates` collection |
| LlamaIndex workflow | `main/src/core/unified_workflow.py` | Reuse `Workflow` + `@step` patterns |
| Storage adapters | `main/src/adapters/storage.py`, `local_adapter.py` | Reuse for PDF/XLSX file storage |
| Docker patterns | `docker-compose.dev.yml`, `Dockerfile.api` | Adapt for minimal LIMS stack |
| FastAPI patterns | `main/api/app.py` | Reuse lifespan, middleware, healthcheck patterns |
| Framer Motion + 3D | `main/frontend/components/3d/`, `landing/` | Direct reuse for visual polish |

---

## 8. LLM Prompt Strategy

### 8.1 Extraction Schema Prompt (Critical)

The LlamaExtract schema must:
1. Define 4 core MDA sheets as nested JSON schema objects
2. Include field descriptions with LIMS-specific context (e.g., "result_type: N=numeric, T=text, L=list, K=calculated, D=date")
3. Explain naming conventions (e.g., "AND_ACS_DYE" = site_prefix + method_abbreviation)
4. Reference LIMS Basic code patterns for calculation fields

The RAG context (from ChromaDB `mda_templates`) provides 1-2 similar MDA templates as few-shot examples.

### 8.2 Chat System Prompt

The chat agent must:
1. Know the full content of the uploaded PDF
2. Know the current state of the MDA template (all 4 core sheets)
3. Be able to explain why it made specific extraction decisions (using LlamaExtract citations)
4. Modify the MDA when the operator requests changes
5. Ask clarifying questions when modifications are ambiguous
6. Know LIMS conventions (naming patterns, result types, calculation variable scoping)

### 8.3 Prompt Versioning & Edit Contract

Prompts must be versioned and separated by purpose. Minimum prompt files:

- `prompts/extraction_prompt.py`
- `prompts/mda_generation_prompt.py`
- `prompts/chat_system_prompt.py`
- `prompts/edit_contract_prompt.py` (NEW)

The edit contract prompt must require structured edit actions only (no free-form mutation), e.g.:

```json
{
  "sheet": "components",
  "action": "modify",
  "target": {"analysis": "AND_ACS_DYE", "component_name": "DYE_VOLUME"},
  "changes": {"units": "mg"},
  "reason": "User requested units change"
}
```

Backend applies changes only after Pydantic validation. Invalid edits are rejected and state remains unchanged.

### 8.4 Chat Memory Policy (Short-Term Only)

For PoC, memory is short-lived and scoped to `job_id`:

- Store in-memory only: message history, applied edits, current MDA snapshot
- No long-term/persistent memory requirement for PoC
- Add TTL (e.g., 2 hours) and max-turn limit (e.g., 50 messages) to prevent context bloat
- On server restart, chat state may be lost (acceptable for PoC; document clearly in UX)

This satisfies user-to-LLM refinement needs without introducing durable memory infrastructure.

---

## 9. Delivery Structure & Phase Gates

### 9.1 Overview

The PoC is delivered in 6 phases across 2 weeks. Each phase has a concrete, testable gate that must pass before proceeding.

| Phase | Name | Duration | Gate |
|-------|------|----------|------|
| Phase 0 | Setup & Validation | Day 0 | Dependencies install clean, Docker runs, LlamaExtract API key verified |
| Phase 1 | Data Models & Extraction | Day 1-2 | PDF extracts into valid Pydantic MDA models |
| Phase 2 | MDA Generation & Export | Day 3-4 | Full MDA generated from PDF, XLSX matches format. RAG optional enhancement. |
| Phase 3 | Frontend | Day 5-6 | Upload PDF in browser -> see MDA tables -> download XLSX |
| Phase 4 | Chat & Refinement | Day 7-8 | Chat modifies MDA, Pydantic validates, tables update |
| Phase 5 | Integration & Demo | Day 9-10 | Full demo works, thesis system unaffected |

### 9.2 Phase Gate Criteria (Pass/Fail)

**Phase 0 Gate: Environment Ready**
- [ ] `pip install llama-cloud openpyxl PyMuPDF` succeeds without dependency conflicts
- [ ] `docker-compose -f docker-compose.lims.yml up -d` starts frontend + API containers
- [ ] `curl http://localhost:8080/lims/health` returns 200
- [ ] LlamaExtract API key validated: `python -c "from llama_cloud import LlamaExtract; LlamaExtract(api_key='...')"` succeeds
- [ ] `main/src/lims/` package imports without error

**Phase 1 Gate: Extraction Works (3 Core Sheets)**
- [ ] **3 core sheet** models (Analysis, Component, Calculation) instantiate with example data (no ValidationError)
- [ ] 4 core sheet models with enums and validators defined in `mda_schema.py`
- [ ] `POST /lims/extract` with example PDF returns structured JSON
- [ ] JSON validates against `MDATemplate` Pydantic model
- [ ] At least 1 Analysis, 3+ Components, and 1+ Calculation extracted from test PDF
- [ ] LlamaExtract citations present in response
- [ ] Raw extraction results logged for schema refinement iteration
- [ ] **No regression:** `uv run pytest main/tests/ -v` — all existing thesis tests pass

**Phase 2 Gate: Full MDA Pipeline**
- [ ] LlamaIndex workflow produces complete MDA (all 4 core sheets populated)
- [ ] `GET /lims/export/{job_id}` returns XLSX file
- [ ] XLSX opens in Excel with correct 4-sheet structure
- [ ] Generated XLSX field names match LabWare MDA format
- [ ] **(Optional)** ChromaDB `mda_templates` collection populated with 2+ example MDAs
- [ ] **(Optional)** RAG retrieval returns similar templates for a given extraction

> **Note:** RAG (L2.1) is an optional enhancement for Phase 2. The core gate is "extraction + LLM generates valid MDA + XLSX export works". With only 2 example templates, RAG adds minimal value — prove extraction quality first, add RAG if time permits.

- [ ] **No regression:** `uv run pytest main/tests/ -v` — all existing thesis tests pass

**Phase 3 Gate: Frontend Displays MDA**
- [ ] `pages/lims.tsx` renders without errors
- [ ] PDF upload triggers extraction (visible progress indicator)
- [ ] MDA tables display with one tab per core sheet (4 tabs)
- [ ] Tables show correct column headers and data
- [ ] XLSX download button works
- [ ] "LIMS" nav link visible in header
- [ ] Thesis pages (`/generate`, `/history`) still accessible
- [ ] **No regression:** `uv run pytest main/tests/ -v` — all existing thesis tests pass

**Phase 4 Gate: Chat Modifies MDA**
- [ ] Chat interface renders with message input
- [ ] User can send a message and receive a streaming response
- [ ] Chat can explain extraction decisions with PDF citations
- [ ] Chat can modify MDA (e.g., "change units for component X to milligrams")
- [ ] After modification, Pydantic validates the updated MDA (no silent corruption)
- [ ] Updated MDA tables reflect changes in real-time
- [ ] Chat memory persists across turns for the same `job_id` during the active session window
- [ ] **No regression:** `uv run pytest main/tests/ -v` — all existing thesis tests pass

**Phase 5 Gate: Demo-Ready**
- [ ] Full end-to-end: PDF upload -> extraction -> MDA display -> chat refinement -> XLSX download
- [ ] XLSX export after chat uses latest validated refined MDA state
- [ ] `docker-compose -f docker-compose.dev.yml up -d` starts thesis system without errors
- [ ] Thesis job submission (`POST /jobs`) still works
- [ ] No LIMS code imported by thesis code paths
- [ ] Demo rehearsal completed successfully

### 9.3 Kill Criteria (Stop/Pivot Triggers)

If any of the following are true after the stated deadline, stop the current approach and pivot:

| Criterion | Threshold | Deadline | Pivot Action |
|-----------|-----------|----------|-------------|
| **Extraction accuracy** | < 40% of components correctly typed after 3 schema iterations | End of Day 2 | Abandon LlamaExtract. Switch to Vision LLM direct (GPT-5/Claude) with structured output. |
| **Per-document extraction cost** | > $5 per PDF (balanced mode) | End of Day 1 | Switch to `fast` mode or Vision LLM direct. |
| **Full pipeline runtime** | > 10 minutes for a single 19-page PDF | End of Day 4 | Profile bottleneck. If LlamaExtract, switch to parallel page-by-page. If LLM generation, reduce context. |
| **Dependency conflicts** | `llama-cloud` breaks existing thesis tests | End of Day 0 | Isolate LIMS in a separate virtualenv or pin conflicting packages. |
| **LlamaExtract API access** | Cannot obtain working API key or quota within 4 hours | Day 0 | Switch to AWS Bedrock Data Automation (backup extractor). |
| **Cross-sheet extraction** | AI cannot identify the 3-analysis pattern (Primary/CTL/META) after 3 attempts | End of Day 2 | Hard-code the analysis structure; let AI fill component details only. |

> **Decision authority:** Engineer makes the pivot call. No stakeholder approval required for PoC-phase pivots — document the decision and rationale in the PR description.

---

## 10. Task Breakdown (21 Tasks)

### Phase 0: Setup & Validation (4 tasks)

---

### Task L0.1 - Validate Dependencies, API Access & Test Data

**Phase:** 0 (Setup) | **Dependencies:** None

> **WARNING:** `project_docs/parced_example_files/` does not exist in the repository. At least 1 PDF + 1 XLSX pair must be committed before Phase 1 can begin. Tasks L1.1, L1.2, L2.1, and L2.4 all depend on this data existing.

#### What to Do
- **Obtain/create example test data:** At least 1 PDF test method + 1 corresponding XLSX MDA template pair must be committed to the repo (e.g., in `project_docs/parced_example_files/`). This is a hard prerequisite for Phase 1.
- Test installation of `llama-cloud`, `openpyxl`, and `PyMuPDF` alongside existing thesis dependencies.
- Verify no version conflicts with pinned packages in `pyproject.toml`.
- After verifying compatibility, also regenerate `requirements-prod.txt` — Docker pip builds use `requirements-prod.txt`, NOT `pyproject.toml`.
- Sign up for [LlamaIndex Cloud](https://developers.llamaindex.ai/python/cloud/) and obtain API key.
- Validate LlamaExtract API access with a simple test call.
- Configure `LIMS_*` environment variables in `.env.local`.

#### Dependencies
- None; prerequisite to all other tasks.

#### Best Practices
- Test installation in an isolated environment first before adding to `pyproject.toml`.
- Use `LIMS_` prefix for all new environment variables to avoid conflicts.
- Store API keys in `.env.local` (gitignored), never in code.

#### Code Example
```bash
# Test dependency compatibility
uv pip install llama-cloud openpyxl PyMuPDF --dry-run

# Validate API access
python -c "
from llama_cloud import LlamaExtract
import os
client = LlamaExtract(api_key=os.getenv('LIMS_LLAMAEXTRACT_API_KEY'))
print('LlamaExtract API access verified')
"
```

#### Environment Variables
```bash
# .env.local additions
LIMS_LLAMAEXTRACT_API_KEY=llx-...
LIMS_OPENROUTER_API_KEY=sk-or-...
LIMS_OPENROUTER_MODEL=openai/gpt-5
LIMS_CHROMADB_COLLECTION=mda_templates
LIMS_CHROMADB_PATH=./chroma_db_lims
LIMS_UPLOAD_DIR=./uploads/lims
LIMS_OUTPUT_DIR=./output/lims
```

#### Links
- [LlamaIndex Cloud Signup](https://developers.llamaindex.ai/python/cloud/)
- [LlamaExtract Getting Started](https://developers.llamaindex.ai/python/cloud/llamaextract/getting_started/)

#### Testing Strategy
- Run `uv pip install` and verify no dependency resolution errors.
- Execute API validation script — must return success, not timeout or 401.
- Run `uv run pytest main/tests/ -v` to confirm existing thesis tests still pass after adding dependencies.

#### Common Issues to Avoid
- LlamaExtract requires a separate API key from LlamaParse — don't confuse them.
- `PyMuPDF` package name is `pymupdf` on PyPI but imports as `fitz` — document this.
- Don't add dependencies to `pyproject.toml` until compatibility is verified.
- **Docker pip builds use `requirements-prod.txt`, not `pyproject.toml`.** After adding new deps to `pyproject.toml`, always regenerate `requirements-prod.txt` (e.g., `uv pip compile pyproject.toml -o requirements-prod.txt`).
- **Test data must exist before Phase 1.** If `project_docs/parced_example_files/` is empty or missing, no extraction or model validation can proceed.

---

### Task L0.2 - Create LIMS Package Structure

**Phase:** 0 (Setup) | **Dependencies:** L0.1

#### What to Do
- Create the `main/src/lims/` package directory with `__init__.py`.
- Create empty module files with docstrings: `config.py`, `mda_schema.py`, `pdf_extractor.py`, `mda_generator.py`, `chat_agent.py`, `xlsx_exporter.py`.
- Create `main/src/lims/prompts/` directory with prompt module stubs.
- Implement `config.py` with `LIMSConfig` class reading all `LIMS_*` environment variables.

#### Dependencies
- L0.1 (environment variables defined).

#### Best Practices
- Use a dedicated `LIMSConfig` Pydantic `BaseSettings` class — never read `os.getenv` directly in business logic.
- All LIMS imports must be self-contained — no circular dependencies with thesis code.
- Include `__all__` exports in `__init__.py`.

#### Code Example
```python
# main/src/lims/config.py
from pydantic_settings import BaseSettings

class LIMSConfig(BaseSettings):
    llamaextract_api_key: str
    openrouter_api_key: str
    openrouter_model: str = "openai/gpt-5"
    chromadb_collection: str = "mda_templates"
    chromadb_path: str = "./chroma_db_lims"
    upload_dir: str = "./uploads/lims"
    output_dir: str = "./output/lims"

    class Config:
        env_prefix = "LIMS_"
```

#### Links
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)

#### Testing Strategy
- Import `from main.src.lims import LIMSConfig` — must not raise ImportError.
- Instantiate `LIMSConfig()` with env vars set — must not raise ValidationError.
- Verify no thesis module imports LIMS modules (grep for `from main.src.lims`).

#### Common Issues to Avoid
- Don't create `__init__.py` files that eagerly import heavy dependencies (LlamaExtract, ChromaDB) — use lazy imports.
- Don't put LIMS config in the existing thesis `Settings` class — keep it separate.
- **Import convention:** Use `main.src.lims.*` pattern (e.g., `from main.src.lims.config import LIMSConfig`). This matches the active codebase convention used in `worker.py` and `worker_executor.py`. Do NOT use `from src.lims...` — that convention is inconsistent with the rest of the project.

---

### Task L0.3 - Create Docker Compose for LIMS

**Phase:** 0 (Setup) | **Dependencies:** L0.2

#### What to Do
- Create `docker-compose.lims.yml` with minimal services: frontend + API only.
- No worker, no SQS, no Phoenix — just the two containers needed for the PoC.
- Mount `uploads/lims/` and `output/lims/` as volumes for file persistence.
- Add health check for the API container.
- Original `docker-compose.dev.yml` remains untouched.

#### Dependencies
- L0.2 (package structure exists).

#### Best Practices
- Keep the compose file minimal — fewer services means faster startup and fewer failure modes.
- Use the same Dockerfile as the thesis API but with additional LIMS dependencies.
- Mount `.env.local` for secrets — don't bake API keys into images.

#### Code Example
```yaml
# docker-compose.lims.yml
version: '3.8'
services:
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://api:8080
    depends_on:
      api:
        condition: service_healthy

  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    ports:
      - "8080:8080"
    env_file:
      - .env.local
    volumes:
      - ./uploads/lims:/app/uploads/lims
      - ./output/lims:/app/output/lims
      - ./chroma_db_lims:/app/chroma_db_lims
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 10s
      timeout: 5s
      retries: 3
```

#### Links
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)

#### Testing Strategy
- `docker-compose -f docker-compose.lims.yml up -d` starts both containers.
- `curl http://localhost:8080/health` returns 200.
- `curl http://localhost:3000` returns HTML.
- `docker-compose -f docker-compose.dev.yml up -d` still starts the thesis stack (run separately).

#### Common Issues to Avoid
- Don't modify `docker-compose.dev.yml` — create a new file.
- Don't include ChromaDB as a separate service — the API container connects to the local directory.
- Don't forget to add `docker-compose.lims.yml` to `.dockerignore` template list.

---

### Task L0.4 - CI Smoke Checks for LIMS PRs

**Phase:** 0 (Setup) | **Dependencies:** L0.2

#### What to Do
- Add a CI job (GitHub Actions) that runs on every PR touching `main/src/lims/` or `main/api/lims_router.py`.
- Three checks, all fast (< 30 seconds total):
  1. **Import check:** `python -c "from main.src.lims.mda_schema import MDATemplate"` — catches broken imports.
  2. **Mocked extraction test:** Instantiate `MDATemplate` with fixture data, verify serialization roundtrip — catches schema regressions.
  3. **Router health test:** Start the API with `--no-reload`, hit `GET /lims/health`, assert 200 — catches router mount failures.
- These run alongside existing thesis tests (`uv run pytest main/tests/ -v`) to enforce the no-regression gate.

#### Dependencies
- L0.2 (LIMS package structure must exist for import checks).

#### Best Practices
- Keep CI checks fast — no LlamaExtract API calls, no Docker builds, no LLM calls.
- Use fixture/mock data only — CI must work without API keys.
- Run thesis tests in the same CI job so a single PR cannot break either system.
- Fail the PR if any check fails — no "allowed to fail" exceptions.

#### Code Example
```yaml
# .github/workflows/lims-smoke.yml (or add to existing CI)
- name: LIMS import check
  run: python -c "from main.src.lims.mda_schema import MDATemplate; print('OK')"

- name: LIMS schema roundtrip
  run: |
    python -c "
    from main.src.lims.mda_schema import MDATemplate, Analysis, Component, Calculation
    mda = MDATemplate(
        analyses=[Analysis(name='AND_TEST', reported_name='T', common_name='T', analysis_type='ID')],
        components=[Component(analysis='AND_TEST', component_name='C1', order_number=1, result_type='T')],
        calculations=[],
    )
    assert MDATemplate.model_validate(mda.model_dump())
    print('Roundtrip OK')
    "

- name: Thesis regression check
  run: uv run pytest main/tests/ -v
```

#### Testing Strategy
- CI job triggers on PR — all 3 checks pass.
- Intentionally break an import — CI fails.
- Intentionally break a model validator — CI fails.
- Thesis tests still included and passing.

#### Common Issues to Avoid
- Don't add API key requirements to CI — use mocks/fixtures only.
- Don't skip thesis tests in the LIMS CI job — the whole point is catching cross-contamination.
- Don't make CI checks slow — no Docker builds, no external API calls.

---

### Phase 1: Data Models & Extraction (3 tasks)

---

### Task L1.1 - Implement MDA Pydantic Schema (4 Core Sheets)

**Phase:** 1 (Data Models) | **Dependencies:** L0.2

#### What to Do
- Implement 4 core sheet models + 9 enums + cross-sheet validators in `main/src/lims/mda_schema.py`.
- **Models:** `Analysis` (Sheet 1), `Component` (Sheet 2), `CalcVariable` (Sheet 6), `Calculation` (Sheet 7).
- **Enums:** `AnalysisType`, `ResultType`, `RoundType`, `UnitCode`, `CalcVariableReferenceType`, `CalcVariableReturnValue`, `CalcVariableScope`, `CalcVariableFunction`, `CalculationType`.
- Define the `MDATemplate` root model with 4 lists and cross-sheet referential integrity validators.
- Include JSON schema export method for LlamaExtract schema generation.
- Parse the example XLSX files (`project_docs/parced_example_files/`) to verify field names and types against ground truth.
- Use `model_config = ConfigDict(extra="allow", str_strip_whitespace=True, use_enum_values=True)` on all models.

**Domain insights to encode:**
- **Three-analysis pattern:** Primary (AND_ACS_DYE, type=ID), Control (AND_ACS_DYE_CTL, type=QC_SAMPLES), Metadata (AND_ACS_DYE_META, type=QC_SAMPLES). Total: 25 components across 3 analyses.
- **Component classification rules:** K requires auto_calc, L requires list_key, N with uses_instrument should have instrument_group. See Section 4.3 for full mapping.
- **S/R Picker handling:** Reagents and equipment selections are K-type (GOSUB CALC_SR_PICKER / CALC_INST_PICKER), NOT L-type list selections.
- **Cross-analysis CALC_VARIABLES:** reference_type=A with scope=B for batch-level cross-analysis references.
- **Site prefix validation:** Analysis names must start with site prefix + underscore (e.g., AND_).

#### Dependencies
- L0.2 (LIMS package structure).

#### Best Practices
- Parse the actual example XLSX files to determine field names — don't guess from documentation.
- Use `Optional` for fields that may be empty in the XLSX.
- Add `model_config = ConfigDict(extra="allow", str_strip_whitespace=True, use_enum_values=True)` on every model class.
- Include `to_json_schema()` class method for LlamaExtract integration.
- **Log raw extraction results** before Pydantic parsing — this enables iterative schema refinement.
- Reagents use S/R Pickers (GOSUB), NOT measurement decomposition — do not create N-type numeric components for reagent steps.

#### Code Example
```python
# main/src/lims/mda_schema.py
from pydantic import BaseModel, field_validator, model_validator, ConfigDict
from typing import List, Optional
from enum import Enum

class ResultType(str, Enum):
    N = "N"  # Numeric (measurement with instrument)
    K = "K"  # Calculated (LIMS Basic formula, GOSUB, or conditional)
    L = "L"  # List selection (YES_NO_2, PASS_FAIL)
    T = "T"  # Free text
    D = "D"  # Date picker

class Component(BaseModel):
    model_config = ConfigDict(extra="allow", str_strip_whitespace=True, use_enum_values=True)

    analysis: str
    component_name: str
    version: int = 1
    order_number: int
    result_type: ResultType
    units: Optional[str] = None
    uses_instrument: bool = False
    auto_calc: bool = False
    list_key: Optional[str] = None
    sr_picker: Optional[str] = None

    @model_validator(mode="after")
    def validate_result_type_constraints(self) -> "Component":
        if self.result_type == ResultType.K and not self.auto_calc:
            raise ValueError(f"Component '{self.component_name}': K requires auto_calc=True")
        if self.result_type == ResultType.L and not self.list_key:
            raise ValueError(f"Component '{self.component_name}': L requires a list_key")
        return self
```

#### Links
- [Pydantic v2 Models](https://docs.pydantic.dev/latest/concepts/models/)
- [LabWare LIMS MDA Format](https://www.labware.com/)

#### Testing Strategy
- Instantiate each of the 4 models with example data from ground truth — no ValidationError.
- Instantiate `MDATemplate` with 3 analyses, 25 components — serializes to JSON and back.
- Test cross-sheet integrity: orphan component referencing non-existent analysis raises ValidationError.
- Test K-type validation: K-type component without auto_calc raises ValidationError.
- Test QC_SAMPLES validation: CTL-suffixed analysis with type=ID raises ValidationError.
- Export JSON schema via `MDATemplate.model_json_schema()` — valid JSON schema output.

#### Common Issues to Avoid
- Don't hardcode field names — parse them from actual XLSX column headers.
- Don't make all fields required — many MDA fields are optional/empty in practice.
- Don't forget `extra="allow"` — LlamaExtract may return fields not in our model.
- **Known ground truth issues:** typos in some analysis names, `g_na` inconsistency across sheets, Round type "U" (Up) not documented in LabWare manuals, Places: 0 appearing on some components.
- **Don't decompose reagents into measurement steps** — reagents use S/R Pickers (K-type), not N-type numeric components.

---

### Task L1.2 - Implement LlamaExtract PDF Extraction

**Phase:** 1 (Extraction) | **Dependencies:** L0.1, L1.1

#### What to Do
- Implement `main/src/lims/pdf_extractor.py` with LlamaExtract integration.
- Build extraction schema from MDA Pydantic model JSON schemas.
- Handle multi-page PDF extraction (19+ pages).
- Return structured data as `MDATemplate` Pydantic object.
- Include extraction metadata: confidence scores, citations, page references.
- Implement error handling — fail loudly with full diagnostic information on extraction failure.

#### Dependencies
- L0.1 (LlamaExtract API key, dependencies installed).
- L1.1 (Pydantic models for schema generation and result parsing).

#### Best Practices
- Use `mode="balanced"` for initial development, upgrade to `"premium"` for final demo.
- Log the full extraction schema sent to LlamaExtract for debugging.
- Store raw extraction results alongside parsed Pydantic models for audit.
- Never silently drop extraction results that fail Pydantic validation — log the raw data and the validation error.
- **Iterative schema refinement:** Expect 3-5 iterations of schema tuning. LlamaExtract's output depends heavily on schema quality. After each extraction attempt, compare raw results against expected Pydantic fields and adjust the JSON schema accordingly. Budget at least half a day for this refinement loop.

#### Code Example
```python
# main/src/lims/pdf_extractor.py
from llama_cloud import LlamaExtract
from main.src.lims.config import LIMSConfig
from main.src.lims.mda_schema import MDATemplate
import json
from pathlib import Path

class PDFExtractor:
    def __init__(self, config: LIMSConfig):
        self.client = LlamaExtract(api_key=config.llamaextract_api_key)
        self.schema = MDATemplate.model_json_schema()

    async def extract(self, pdf_path: Path) -> MDATemplate:
        """Extract MDA data from pharmaceutical PDF.

        Raises on failure — no fallbacks.
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        result = self.client.extract(
            file=str(pdf_path),
            schema=self.schema,
            mode="balanced"
        )

        if not result.data:
            raise RuntimeError(
                f"LlamaExtract returned empty data for {pdf_path}. "
                f"Status: {result.status}, Errors: {result.errors}"
            )

        # Parse into Pydantic — will raise ValidationError if data is malformed
        mda = MDATemplate(**result.data)
        return mda
```

#### Links
- [LlamaExtract API Reference](https://developers.llamaindex.ai/python/cloud/llamaextract/getting_started/)
- [LlamaExtract Schema Definition](https://developers.llamaindex.ai/python/cloud/llamaextract/)

#### Testing Strategy
- Unit test with a mock LlamaExtract client returning known JSON — Pydantic parses correctly.
- Integration test: extract from `project_docs/parced_example_files/` PDF — returns non-empty MDATemplate.
- Verify at least 1 Analysis, 3+ Components, 1+ Calculation in extraction result.
- Test error cases: missing file raises FileNotFoundError, empty result raises RuntimeError.
- Verify raw extraction result is logged/stored for debugging.

#### Common Issues to Avoid
- Don't catch and swallow LlamaExtract errors — let them propagate with full context.
- Don't assume all 4 sheets will have data — some may be empty for a given test method.
- Don't forget to test with the actual 19-page example PDF, not just small test files.

---

### Task L1.3 - Create LIMS API Router & Extract Endpoint

**Phase:** 1 (API) | **Dependencies:** L0.3, L1.2

#### What to Do
- Create `main/api/lims_router.py` with FastAPI router.
- Implement `POST /lims/extract` endpoint: accepts PDF upload, triggers extraction, returns job ID.
- Implement `GET /lims/status/{job_id}` endpoint: returns extraction progress.
- Implement `GET /lims/health` endpoint: returns LIMS subsystem health.
- Mount router in `main/api/app.py` with `app.include_router(lims_router, prefix="/lims")`.
- Store extraction jobs in-memory dict (no database for PoC).

#### Dependencies
- L0.3 (Docker compose for API container).
- L1.2 (PDF extractor for extraction logic).

#### Best Practices
- Use `BackgroundTasks` for extraction — don't block the request.
- Return a job ID immediately; client polls `/lims/status/{job_id}` for progress.
- Store uploaded PDFs in `LIMS_UPLOAD_DIR`.
- Include progress tracking: received -> extracting -> generating -> complete.
- Mount the router as a single line in `app.py` — minimal change to thesis code.

#### Code Example
```python
# main/api/lims_router.py
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from main.src.lims.config import LIMSConfig
from main.src.lims.pdf_extractor import PDFExtractor
import uuid
from pathlib import Path

router = APIRouter(tags=["lims"])
jobs: dict = {}  # In-memory job store for PoC

@router.post("/extract")
async def extract_pdf(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    job_id = str(uuid.uuid4())
    config = LIMSConfig()

    # Save uploaded file
    upload_dir = Path(config.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = upload_dir / f"{job_id}.pdf"
    content = await file.read()
    pdf_path.write_bytes(content)

    jobs[job_id] = {"status": "received", "progress": 0}
    background_tasks.add_task(run_extraction, job_id, pdf_path, config)
    return {"job_id": job_id, "status": "received"}
```

#### Links
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [FastAPI File Upload](https://fastapi.tiangolo.com/tutorial/request-files/)

#### Testing Strategy
- `POST /lims/extract` with a PDF file returns `{ job_id, status: "received" }`.
- `GET /lims/status/{job_id}` returns progress updates.
- `GET /lims/health` returns 200.
- Invalid file upload (non-PDF) returns 400.
- After extraction completes, `GET /lims/status/{job_id}` returns `status: "complete"` with MDA data.
- Verify `app.py` change is a single `include_router` line — no other modifications.

#### Common Issues to Avoid
- Don't add authentication to LIMS endpoints for PoC — auth is feature-flagged off.
- Don't use a database for job storage in PoC — in-memory dict is sufficient.
- Don't forget to handle file upload size limits.

---

### Phase 2: MDA Generation & Export (4 tasks)

---

### Task L2.1 - Populate ChromaDB with MDA Templates (OPTIONAL — Parallel Enhancement)

**Phase:** 2 (RAG — Optional) | **Dependencies:** L1.1 | **Priority:** Nice-to-have

> **Note:** With only 2 example templates, RAG adds minimal value. This task can run in parallel with L2.2 but is NOT a hard dependency. Prove extraction quality first without RAG. Add RAG context as an enhancement if time permits.

#### What to Do
- Create a script to populate ChromaDB `mda_templates` collection with example MDA data.
- Parse the 2 example XLSX files from `project_docs/parced_example_files/` into `MDATemplate` objects.
- Chunk and embed the MDA data for RAG retrieval.
- Store in `chroma_db_lims/` directory (separate from thesis `chroma_db/`).
- Reuse the existing `chroma_adapter.py` pattern but pointing to the new collection.

#### Dependencies
- L1.1 (MDA Pydantic models for parsing XLSX into structured data).

#### Best Practices
- Use the same embedding model as the thesis project for consistency.
- Store full MDA templates as metadata alongside embeddings for retrieval.
- Include analysis type, component count, and method name as filterable metadata.
- Create a separate script `scripts/populate_lims_chroma.py` for reproducibility.

#### Code Example
```python
# scripts/populate_lims_chroma.py
import chromadb
from pathlib import Path
import openpyxl

CHROMA_PATH = "./chroma_db_lims"
COLLECTION_NAME = "mda_templates"

client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(name=COLLECTION_NAME)

# Parse example XLSX files
xlsx_dir = Path("project_docs/parced_example_files")
for xlsx_file in xlsx_dir.glob("*.xlsx"):
    wb = openpyxl.load_workbook(xlsx_file)
    # ... parse sheets into documents and embed
```

#### Links
- [ChromaDB Quickstart](https://docs.trychroma.com/getting-started)
- [openpyxl Reading XLSX](https://openpyxl.readthedocs.io/)

#### Testing Strategy
- Run population script — completes without errors.
- Query `mda_templates` collection — returns 2+ documents.
- Verify `chroma_db_lims/` directory exists and is separate from `chroma_db/`.
- Verify thesis `pharmaceutical_regulations` collection is untouched.
- Similarity search for "dye binding identity test" returns relevant MDA template.

#### Common Issues to Avoid
- Don't write to `chroma_db/` — that's the thesis collection. Use `chroma_db_lims/`.
- Don't embed entire XLSX files as single documents — chunk by sheet/analysis for better retrieval.
- Don't forget to add `chroma_db_lims/` to `.gitignore`.

---

### Task L2.2 - Build MDA Generation Workflow

**Phase:** 2 (Workflow) | **Dependencies:** L1.2 | **Optional Enhancement:** L2.1

#### What to Do
- Implement `main/src/lims/mda_generator.py` as a LlamaIndex `Workflow` with `@step` decorators.
- **Core pipeline (works without RAG):**
  1. Extract raw data from PDF (LlamaExtract — Task L1.2)
  2. Generate full MDA using extracted data (LLM via OpenRouter)
  3. Generate LIMS Basic code for calculation fields
  4. Validate complete MDA against Pydantic models
- **Optional RAG enhancement (if L2.1 is completed):**
  5. Query ChromaDB for similar MDA templates (RAG context)
  6. Pass RAG results as few-shot examples in the generation prompt
- **Phase 1 validated 3 core sheets; this task expands to all 4 core sheets** in the generation workflow.
- Use OpenRouter for LLM calls (GPT-5 or Claude Opus 4.6).

#### Dependencies
- L1.2 (PDF extractor).
- L2.1 (ChromaDB populated with examples) — **OPTIONAL.** Workflow must function without RAG. RAG adds quality but is not required for the Phase 2 gate.

#### Best Practices
- Reuse `Workflow` + `@step` patterns from thesis `unified_workflow.py`.
- Pass RAG results as few-shot examples in the generation prompt.
- Validate output at each step — fail early if extraction is incomplete.
- Log every step with timing for performance analysis.
- Keep `Workflow` as the top-level orchestrator; do NOT replace the end-to-end pipeline with autonomous agents.
- If agent-style components are used, limit them to bounded sub-tasks (edit proposal, rationale explanation), with deterministic validation gates between steps.

#### Code Example
```python
# main/src/lims/mda_generator.py
from llama_index.core.workflow import Workflow, step, StartEvent, StopEvent, Event
from main.src.lims.pdf_extractor import PDFExtractor
from main.src.lims.mda_schema import MDATemplate
from main.src.lims.config import LIMSConfig

class ExtractionDone(Event):
    raw_mda: MDATemplate

class RAGContextReady(Event):
    raw_mda: MDATemplate
    similar_templates: list

class MDAGenerationWorkflow(Workflow):
    def __init__(self, config: LIMSConfig):
        super().__init__()
        self.config = config
        self.extractor = PDFExtractor(config)

    @step
    async def extract_pdf(self, ev: StartEvent) -> ExtractionDone:
        raw_mda = await self.extractor.extract(ev.pdf_path)
        return ExtractionDone(raw_mda=raw_mda)

    @step
    async def retrieve_rag_context(self, ev: ExtractionDone) -> RAGContextReady:
        # Query ChromaDB for similar templates
        similar = await self._query_chroma(ev.raw_mda)
        return RAGContextReady(raw_mda=ev.raw_mda, similar_templates=similar)

    @step
    async def generate_full_mda(self, ev: RAGContextReady) -> StopEvent:
        # LLM generates complete MDA using extraction + RAG
        full_mda = await self._llm_generate(ev.raw_mda, ev.similar_templates)
        return StopEvent(result=full_mda)
```

#### Links
- [LlamaIndex Workflows](https://docs.llamaindex.ai/en/stable/module_guides/workflow/)
- [OpenRouter API](https://openrouter.ai/docs)

#### Testing Strategy
- Unit test each workflow step individually with mocked dependencies.
- Integration test: run full workflow with example PDF — produces valid `MDATemplate`.
- Verify RAG retrieval returns relevant templates (not random data).
- Verify LLM generation fills in fields that extraction missed.
- Verify LIMS Basic calculation code is syntactically reasonable.
- Time the full workflow — should complete within 2 minutes for a 19-page PDF.

#### Common Issues to Avoid
- Don't call LlamaExtract AND the LLM in the same step — keep steps focused.
- Don't forget to pass RAG context as few-shot examples in the generation prompt.
- Don't validate only the final output — validate intermediate results too.
- Don't let agent/tool autonomy mutate MDA state directly without explicit schema-validated transitions.

---

### Task L2.3 - Implement XLSX Export

**Phase:** 2 (Export) | **Dependencies:** L1.1

#### What to Do
- Implement `main/src/lims/xlsx_exporter.py` using openpyxl.
- Generate 4-sheet XLSX matching LabWare MDA format.
- Each sheet corresponds to one of the 4 core Pydantic models (Analysis, Component, CalcVariable, Calculation).
- Include column headers matching LabWare field names.
- Wire to `GET /lims/export/{job_id}` endpoint.

#### Dependencies
- L1.1 (MDA Pydantic models define the sheet structure).

#### Best Practices
- Match column names exactly to LabWare import format — this is critical for real-world usability.
- Use the example XLSX files as the formatting reference.
- Include data validation dropdowns for enum fields (e.g., result_type: N/T/L/K/D).
- Set column widths for readability.

#### Code Example
```python
# main/src/lims/xlsx_exporter.py
from openpyxl import Workbook
from main.src.lims.mda_schema import MDATemplate
from pathlib import Path

class XLSXExporter:
    SHEET_MAP = {
        "Analysis": "analyses",
        "Component": "components",
        "Calc Variable": "calc_variables",
        "Calculation": "calculations",
    }

    def export(self, mda: MDATemplate, output_path: Path) -> Path:
        wb = Workbook()
        wb.remove(wb.active)  # Remove default sheet

        for sheet_name, attr_name in self.SHEET_MAP.items():
            ws = wb.create_sheet(title=sheet_name)
            items = getattr(mda, attr_name)
            if not items:
                continue
            # Write headers from model fields
            headers = list(items[0].model_fields.keys())
            ws.append(headers)
            # Write data rows
            for item in items:
                ws.append([getattr(item, h, None) for h in headers])

        wb.save(str(output_path))
        return output_path
```

#### Links
- [openpyxl Documentation](https://openpyxl.readthedocs.io/)

#### Testing Strategy
- Export a known `MDATemplate` to XLSX — file is created.
- Open in openpyxl and verify 4 sheets exist with correct names.
- Verify column headers match Pydantic model field names.
- Compare generated XLSX structure against example XLSX files from `project_docs/`.
- Verify the exported file opens in Microsoft Excel without errors.

#### Common Issues to Avoid
- Sheet names in Excel have a 31-character limit — ensure all names fit.
- Don't use `None` values in cells that LabWare expects empty strings.
- Don't forget to handle the case where a sheet has no data (empty list).

---

### Task L2.4 - End-to-End Pipeline Test & Contract Tests

**Phase:** 2 (Integration) | **Dependencies:** L1.3, L2.2, L2.3

#### What to Do
- Create an integration test that runs the complete pipeline: PDF upload -> extraction -> MDA generation -> XLSX export.
- Use the example PDF from `project_docs/parced_example_files/`.
- Compare generated MDA against the human-created example XLSX.
- Document accuracy metrics: how many fields match, what's missing, what's wrong.
- This is the Phase 2 gate validation.
- **Add explicit schema contract tests** (use this pattern for all subsequent phases):
  - API response schema matches TypeScript types (JSON shape consistency)
  - XLSX sheet names are constant strings (invariant across runs)
  - Pydantic model serialization roundtrips (`model.model_dump()` -> `Model(**data)` is lossless)
  - Export field names match LabWare import format exactly

#### Dependencies
- L1.3 (API endpoint for upload).
- L2.2 (MDA generation workflow).
- L2.3 (XLSX export).

#### Best Practices
- Run the test via API endpoints (not direct function calls) to validate the full stack.
- Log detailed comparison metrics — don't just pass/fail.
- Accept that PoC accuracy won't be 100% — document gaps for improvement.
- Store the test results in `output/lims/test_results/`.

#### Code Example
```python
# tests/lims/test_e2e_pipeline.py
import httpx
from pathlib import Path

async def test_full_pipeline():
    pdf_path = Path("project_docs/parced_example_files/ex_2_was_pdf.pdf")

    async with httpx.AsyncClient(base_url="http://localhost:8080") as client:
        # Upload PDF
        with open(pdf_path, "rb") as f:
            resp = await client.post("/lims/extract", files={"file": f})
        assert resp.status_code == 200
        job_id = resp.json()["job_id"]

        # Poll until complete
        for _ in range(60):
            status = await client.get(f"/lims/status/{job_id}")
            if status.json()["status"] == "complete":
                break
            await asyncio.sleep(2)

        # Export XLSX
        export = await client.get(f"/lims/export/{job_id}")
        assert export.status_code == 200
        assert "spreadsheetml" in export.headers["content-type"]
```

#### Links
- [httpx async client](https://www.python-httpx.org/async/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)

#### Testing Strategy
- This task IS the test — it validates Phase 2 gate criteria.
- PDF extraction returns non-empty `MDATemplate`.
- Generated XLSX has 4 sheets.
- At least 70% of Analysis and Component fields match the example XLSX.
- XLSX downloads successfully via API.
- **Contract tests pass:**
  - `MDATemplate.model_validate(MDATemplate(**data).model_dump())` — roundtrip lossless
  - XLSX sheet names exactly match `XLSXExporter.SHEET_MAP` keys
  - API `/lims/status/{job_id}` response shape matches expected TypeScript interface

#### Common Issues to Avoid
- Don't expect 100% accuracy — this is a PoC. Document gaps, don't block on them.
- Don't forget to start the API server before running the test.
- Set a reasonable timeout for extraction (2-5 minutes for a 19-page PDF).

---

### Phase 3: Frontend (4 tasks)

---

### Task L3.1 - Build LIMS Page with PDF Upload

**Phase:** 3 (Frontend) | **Dependencies:** L1.3

#### What to Do
- Create `main/frontend/pages/lims.tsx` as the main LIMS page.
- Implement PDF upload zone (drag-and-drop + file picker).
- Show upload progress and extraction status.
- Reuse the existing `FileUpload.tsx` pattern but adapt for PDF files.
- Display extraction progress with step indicators (uploading -> extracting -> generating -> complete).

#### Dependencies
- L1.3 (API endpoints to upload and poll status).

#### Best Practices
- Reuse the thesis UI patterns (Framer Motion, styling, layout components).
- Use SWR or polling for status updates.
- Show meaningful progress — not just a spinner.
- Accept only `.pdf` files in the upload component.

#### Code Example
```tsx
// main/frontend/pages/lims.tsx
import { useState } from 'react'
import Layout from '../components/Layout'

export default function LimsPage() {
  const [jobId, setJobId] = useState<string | null>(null)
  const [status, setStatus] = useState<string>('idle')

  const handleUpload = async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    const res = await fetch('/api/lims/extract', { method: 'POST', body: formData })
    const data = await res.json()
    setJobId(data.job_id)
    setStatus('extracting')
    // Start polling...
  }

  return (
    <Layout>
      <h1>AI4LIMS - MDA Generator</h1>
      {/* PDF upload zone */}
      {/* Status indicator */}
      {/* MDA viewer (after extraction) */}
    </Layout>
  )
}
```

#### Links
- [Next.js Pages Router](https://nextjs.org/docs/pages/building-your-application/routing/pages-and-layouts)
- [react-dropzone](https://react-dropzone.js.org/)

#### Testing Strategy
- Page renders at `/lims` without errors.
- PDF upload triggers API call and shows progress.
- Invalid file types are rejected client-side.
- Status polling updates the UI.
- Page is accessible from the frontend URL.

#### Common Issues to Avoid
- Don't modify existing pages — create a new one.
- Don't forget to proxy API calls through Next.js (or configure CORS).
- Don't use the thesis auth middleware on the LIMS page.

---

### Task L3.2 - Build MDA Table Viewer Component

**Phase:** 3 (Frontend) | **Dependencies:** L1.1, L3.1

#### What to Do
- Create `main/frontend/components/MDAViewer.tsx` — tabbed table viewer for 4 core MDA sheets.
- Each tab corresponds to one MDA sheet (Analysis, Component, etc.).
- Tables display field names as column headers and extracted data as rows.
- Include sorting and filtering capabilities.
- Highlight fields with low confidence scores (if available from extraction).

#### Dependencies
- L1.1 (MDA model structure defines the table columns).
- L3.1 (LIMS page to embed the viewer).

#### Best Practices
- Use `@tanstack/react-table` for powerful table features.
- Show tab count badges (e.g., "Components (15)").
- Handle empty sheets gracefully — show "No data extracted" message.
- Use Tailwind CSS consistent with thesis styling.

#### Code Example
```tsx
// main/frontend/components/MDAViewer.tsx
import { useState } from 'react'

interface MDAViewerProps {
  mda: MDATemplate
}

const SHEET_TABS = [
  { key: 'analyses', label: 'Analysis' },
  { key: 'components', label: 'Components' },
  { key: 'calc_variables', label: 'Calc Variables' },
  { key: 'calculations', label: 'Calculations' },
]

export function MDAViewer({ mda }: MDAViewerProps) {
  const [activeTab, setActiveTab] = useState('analyses')

  return (
    <div>
      <div className="tabs">
        {SHEET_TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={activeTab === tab.key ? 'active' : ''}
          >
            {tab.label} ({mda[tab.key]?.length || 0})
          </button>
        ))}
      </div>
      <table>
        {/* Render active sheet data */}
      </table>
    </div>
  )
}
```

#### Links
- [TanStack Table](https://tanstack.com/table/latest)
- [Tailwind CSS Tables](https://tailwindcss.com/docs/table-layout)

#### Testing Strategy
- MDAViewer renders with all 4 tabs visible.
- Clicking a tab switches the displayed table.
- Tables show correct column headers from MDA models.
- Empty sheets show "No data" message instead of crashing.
- Tab badges show correct item counts.

#### Common Issues to Avoid
- Don't render all 4 tables at once — use lazy rendering for performance.
- Don't assume all sheets have data — handle empty arrays.
- Don't create a new table component if the thesis already has one — check first.

---

### Task L3.3 - Modify Layout & Navigation

**Phase:** 3 (Frontend) | **Dependencies:** L3.1

#### What to Do
- Add "LIMS" navigation link to `main/frontend/components/Layout.tsx`.
- Verify `/lims` is NOT in `isProtectedRoute` in `main/frontend/middleware.ts` — the middleware already uses route matching, and `/lims` routes are unprotected by default since they're not listed in `isProtectedRoute`.
- Do NOT modify `_app.tsx` — the `<ClerkProvider>` wrapper stays unchanged. Auth exclusion is handled entirely via the middleware route matcher.
- Only 2 thesis files modified: `Layout.tsx` (nav link) and `middleware.ts` (verify route config).

#### Dependencies
- L3.1 (LIMS page must exist to link to).

#### Best Practices
- Changes must be minimal and non-destructive.
- The middleware already uses `isProtectedRoute` to determine which routes need auth. Simply ensure `/lims` is NOT in that list (it isn't by default).
- Do NOT add a global auth toggle — route-based exclusion is simpler and safer.
- Test that both thesis and LIMS pages work after modifications.

#### Code Example
```tsx
// In Layout.tsx — add alongside existing nav links
<Link href="/lims">LIMS</Link>

// In middleware.ts — verify /lims is NOT in isProtectedRoute
// The existing middleware uses createRouteMatcher for protected routes.
// /lims routes are public by default since they're not listed.
// If needed, explicitly exclude: "/lims(.*)" from the protected matcher.
```

#### Links
- [Clerk Next.js Integration](https://clerk.com/docs/quickstarts/nextjs)

#### Testing Strategy
- "LIMS" link appears in navigation header.
- Clicking "LIMS" navigates to `/lims` page.
- `/lims` page loads without Clerk authentication (public route).
- Thesis pages (`/generate`, `/history`) still require Clerk auth as before.
- Thesis pages (`/generate`, `/history`) still function correctly.

#### Common Issues to Avoid
- Don't modify `_app.tsx` — the `<ClerkProvider>` stays as-is for all pages.
- Don't add a global `NEXT_PUBLIC_AUTH_ENABLED` toggle — route-based exclusion via `middleware.ts` is simpler and doesn't risk breaking thesis auth.
- Don't add LIMS-specific imports to Layout.tsx.

---

### Task L3.4 - Wire Frontend to API (Full Data Flow)

**Phase:** 3 (Frontend) | **Dependencies:** L3.1, L3.2, L3.3, L2.3

#### What to Do
- Connect the LIMS page to all API endpoints:
  - Upload PDF -> `POST /lims/extract`
  - Poll status -> `GET /lims/status/{job_id}`
  - Display MDA in viewer (from status response)
  - Download XLSX -> `GET /lims/export/{job_id}`
- Add XLSX download button to the MDA viewer.
- Add error handling for API failures (show error messages, not silent failures).

#### Dependencies
- L3.1, L3.2, L3.3 (frontend components).
- L2.3 (XLSX export endpoint).

#### Best Practices
- Use a state machine for the page: idle -> uploading -> extracting -> viewing -> exporting.
- Show API error messages directly to the user — no generic "something went wrong".
- Add a "Try Again" button for failed extractions.

#### Code Example
```tsx
// In pages/lims.tsx — download handler
const handleExport = async () => {
  const response = await fetch(`/api/lims/export/${jobId}`)
  if (!response.ok) {
    const error = await response.json()
    throw new Error(`Export failed: ${error.detail}`)
  }
  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `mda_template_${jobId}.xlsx`
  a.click()
}
```

#### Links
- [Fetch API Blob](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)
- [Next.js API Routes Proxy](https://nextjs.org/docs/pages/building-your-application/routing/api-routes)

#### Testing Strategy
- Full browser flow: upload PDF -> see progress -> view MDA tables -> download XLSX.
- API errors display meaningful messages in the UI.
- Download button produces a valid `.xlsx` file.
- State transitions are correct (no stuck states).
- Phase 3 gate criteria met: upload -> see tables -> download.

#### Common Issues to Avoid
- Don't swallow API errors — surface the actual error message.
- Don't forget CORS configuration if frontend and API are on different ports.
- Don't use `window.location` for downloads — use blob URLs for better UX.

---

### Phase 4: Chat & Refinement (3 tasks)

---

### Task L4.1 - Build Chat Backend

**Phase:** 4 (Chat) | **Dependencies:** L2.2

#### What to Do
- Implement `main/src/lims/chat_agent.py` with a LlamaIndex chat engine.
- Chat context includes: full PDF content, current MDA state (all 4 core sheets), extraction citations.
- Chat can answer questions about extraction decisions.
- Chat can modify the MDA template when the operator requests changes.
- After each modification, validate the updated MDA against Pydantic models.
- Implement short-term chat memory per `job_id` (in-memory): messages, modification log, latest validated MDA state.
- Add memory guardrails: TTL and max-turn cap to prevent uncontrolled context growth.
- Ensure final export uses the latest validated refined MDA state (not the initial generation snapshot).
- Wire to `POST /lims/chat` endpoint.

#### Dependencies
- L2.2 (MDA generation workflow provides the initial MDA to chat about).

#### Best Practices
- Use OpenRouter for LLM calls (GPT-5 or Claude Opus 4.6).
- Include the full MDA as structured context in the system prompt.
- Use function calling / tool use to structure MDA modifications.
- Always validate modified MDA with Pydantic before accepting changes.
- Never apply modifications that fail validation — return error to user.

#### Code Example
```python
# main/src/lims/chat_agent.py
from llama_index.core.chat_engine import SimpleChatEngine
from main.src.lims.mda_schema import MDATemplate

class MDAEditAction(BaseModel):
    """Structured MDA modification from chat."""
    sheet: str           # Which sheet to modify
    action: str          # "add", "modify", "delete"
    target: str          # Component name or identifier
    changes: dict        # Field changes

class MDAChatAgent:
    def __init__(self, mda: MDATemplate, pdf_text: str, config: LIMSConfig):
        self.mda = mda
        self.pdf_text = pdf_text
        self.config = config

    async def chat(self, message: str) -> dict:
        """Process chat message, potentially modifying MDA."""
        response = await self._llm_call(message)

        if response.has_modification:
            # Apply and validate
            updated_mda = self._apply_modification(response.modification)
            # Pydantic validation — raises on invalid state
            MDATemplate.model_validate(updated_mda.model_dump())
            self.mda = updated_mda
            return {"response": response.text, "updated_mda": self.mda}

        return {"response": response.text}
```

#### Links
- [LlamaIndex Chat Engines](https://docs.llamaindex.ai/en/stable/module_guides/deploying/chat_engines/)
- [OpenRouter API](https://openrouter.ai/docs)

#### Testing Strategy
- Send a question about extraction: "Why did you set result_type to K for component X?" — returns explanation.
- Send a modification request: "Change units for component X to milligrams" — MDA is updated.
- Send an invalid modification: "Set result_type to Z" — returns Pydantic validation error, MDA unchanged.
- Chat maintains conversation context across messages.
- After modification, `GET /lims/status/{job_id}` returns the updated MDA.
- Verify chat memory expires after configured TTL and refuses additional writes once expired session state is cleared.

#### Common Issues to Avoid
- Don't apply modifications without Pydantic validation — this can corrupt the MDA.
- Don't lose conversation history between messages — maintain chat state per job.
- Don't use the LLM to validate MDA — use Pydantic (deterministic, not probabilistic).

---

### Task L4.2 - Build Chat UI Component

**Phase:** 4 (Frontend) | **Dependencies:** L4.1, L3.1

#### What to Do
- Create `main/frontend/components/ChatInterface.tsx` — streaming chat UI.
- Message input with send button.
- Display chat history with user/AI message bubbles.
- Support streaming responses (SSE or polling).
- Show "MDA Updated" indicators when chat modifies the template.
- Integrate into `pages/lims.tsx` alongside the MDA viewer.

#### Dependencies
- L4.1 (Chat backend endpoint).
- L3.1 (LIMS page to embed the chat).

#### Best Practices
- Use streaming for responsive UX — don't wait for full response.
- Show markdown rendering in AI responses.
- Indicate when the AI is modifying the MDA (visual feedback).
- Auto-scroll to newest messages.

#### Code Example
```tsx
// main/frontend/components/ChatInterface.tsx
interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  mdaUpdated?: boolean
}

export function ChatInterface({ jobId, onMDAUpdate }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')

  const sendMessage = async () => {
    const userMsg = { role: 'user', content: input }
    setMessages(prev => [...prev, userMsg])
    setInput('')

    const res = await fetch('/api/lims/chat', {
      method: 'POST',
      body: JSON.stringify({ job_id: jobId, message: input }),
    })
    const data = await res.json()

    setMessages(prev => [...prev, {
      role: 'assistant',
      content: data.response,
      mdaUpdated: !!data.updated_mda,
    }])

    if (data.updated_mda) onMDAUpdate(data.updated_mda)
  }
  // ...
}
```

#### Links
- [Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)

#### Testing Strategy
- Chat interface renders with message input.
- User can type and send a message.
- AI response appears in chat history.
- "MDA Updated" indicator shows when modifications occur.
- MDA viewer updates when chat modifies the template.
- Multiple messages maintain conversation context.

#### Common Issues to Avoid
- Don't block the UI while waiting for AI response — show a typing indicator.
- Don't lose messages on page refresh (consider session storage for PoC).
- Don't render raw JSON in chat — format AI responses as markdown.

---

### Task L4.3 - MDA Modification via Chat Integration

**Phase:** 4 (Integration) | **Dependencies:** L4.1, L4.2, L3.2

#### What to Do
- Wire the chat modification flow end-to-end:
  1. User sends modification request in chat
  2. Backend modifies MDA and validates with Pydantic
  3. Updated MDA sent back to frontend
  4. MDA viewer tables update in real-time
  5. XLSX export reflects the latest modifications
- Test common modification scenarios:
  - "Change the units for component X to milligrams"
  - "Add a new component for temperature measurement"
  - "The calculation for dye volume is wrong, it should be..."
  - "Why did you choose result_type K for this component?"

#### Dependencies
- L4.1 (Chat backend with modification capability).
- L4.2 (Chat UI).
- L3.2 (MDA viewer for displaying updates).

#### Best Practices
- Maintain an edit history — operator should be able to see what changed.
- Each modification should be atomic — either fully applied or fully rejected.
- Show a diff-like view of what changed after each modification.

#### Code Example
```python
# Modification tracking in chat_agent.py
class ModificationLog(BaseModel):
    timestamp: datetime
    message: str
    sheet: str
    changes: dict
    before: dict
    after: dict

class MDAChatAgent:
    def __init__(self, ...):
        self.modification_log: List[ModificationLog] = []

    async def chat(self, message: str) -> dict:
        # ... process message ...
        if response.has_modification:
            before = self.mda.model_dump()
            self.mda = self._apply_modification(response.modification)
            after = self.mda.model_dump()
            self.modification_log.append(ModificationLog(
                timestamp=datetime.now(),
                message=message,
                sheet=response.modification.sheet,
                changes=response.modification.changes,
                before=before,
                after=after,
            ))
```

#### Links
- [Pydantic Model Validation](https://docs.pydantic.dev/latest/concepts/validators/)

#### Testing Strategy
- Phase 4 gate validation: complete the following sequence in a browser:
  1. Extract MDA from PDF
  2. Open chat and ask: "What analyses were extracted?"
  3. Request: "Change units for component X to milligrams" — table updates
  4. Request: "Add a temperature component" — new row appears
  5. Export XLSX — contains the modifications
- Invalid modification attempt is rejected with clear error message.
- Modification log tracks all changes with before/after state.

#### Common Issues to Avoid
- Don't allow modifications that break cross-sheet references (e.g., deleting an Analysis that has Components).
- Don't lose modifications if the chat encounters an error mid-conversation.
- Don't re-extract from PDF after modifications — work with the in-memory MDA state.

---

### Phase 5: Integration & Demo (3 tasks)

---

### Task L5.1 - End-to-End Integration Test

**Phase:** 5 (Integration) | **Dependencies:** L2.4, L4.3

#### What to Do
- Run a complete end-to-end test of the full PoC:
  1. Start system with `docker-compose -f docker-compose.lims.yml up -d`
  2. Open browser to `http://localhost:3000/lims`
  3. Upload example PDF
  4. Wait for extraction to complete
  5. Review MDA tables (all 4 core sheets)
  6. Chat with AI: ask questions, make modifications
  7. Download XLSX
  8. Verify XLSX contents match expected output
- Document any issues found and fix them.
- This is the primary Phase 5 gate validation.

#### Dependencies
- L2.4 (pipeline test confirms backend works).
- L4.3 (chat modifications work).

#### Best Practices
- Run the test in Docker (not direct Python) to validate the deployment configuration.
- Record the test session (screenshots or video) for demo preparation.
- Document any manual steps needed to reproduce the test.

#### Code Example
```bash
# Integration test script
docker-compose -f docker-compose.lims.yml up -d
sleep 10

# Health check
curl -f http://localhost:8080/lims/health || exit 1

# Upload PDF
curl -X POST http://localhost:8080/lims/extract \
  -F "file=@project_docs/parced_example_files/ex_2_was_pdf.pdf" \
  > /tmp/extract_response.json

JOB_ID=$(jq -r .job_id /tmp/extract_response.json)

# Poll until complete
for i in $(seq 1 60); do
  STATUS=$(curl -s http://localhost:8080/lims/status/$JOB_ID | jq -r .status)
  [ "$STATUS" = "complete" ] && break
  sleep 5
done

# Export XLSX
curl -o /tmp/mda_output.xlsx http://localhost:8080/lims/export/$JOB_ID
echo "XLSX exported to /tmp/mda_output.xlsx"
```

#### Links
- N/A (integration test of all prior work)

#### Testing Strategy
- This task IS the test. Pass criteria:
  - Docker containers start and pass health checks.
  - PDF extraction completes within 5 minutes.
  - MDA tables display in browser.
  - Chat responds to questions.
  - Chat modifications update tables.
  - XLSX downloads with correct content.

#### Common Issues to Avoid
- Don't forget to rebuild Docker images if code has changed since last build.
- Don't run the integration test against the thesis Docker compose — use the LIMS one.
- Set adequate timeouts — extraction of a 19-page PDF may take several minutes.

---

### Task L5.2 - Progress & Confidence UI

**Phase:** 5 (Polish) | **Dependencies:** L3.4

#### What to Do
- Add detailed progress indicators during extraction:
  - "Uploading PDF..." (with file size)
  - "Extracting structured data..." (with page progress if available)
  - "Querying similar templates..." (RAG step)
  - "Generating MDA template..." (LLM step)
  - "Validating output..."
  - "Complete!"
- Add confidence indicators on extracted fields (from LlamaExtract citations/confidence scores).
- Highlight low-confidence fields in the MDA viewer (e.g., yellow background for confidence < 0.7).

#### Dependencies
- L3.4 (frontend wired to API — enhance existing UI).

#### Best Practices
- Map backend pipeline steps to user-friendly progress messages.
- Use color coding for confidence: green (> 0.8), yellow (0.5-0.8), red (< 0.5).
- Don't fabricate confidence scores — only show them if LlamaExtract provides them.

#### Code Example
```tsx
// Progress steps mapping
const PROGRESS_STEPS = [
  { key: 'uploading', label: 'Uploading PDF', icon: '...' },
  { key: 'extracting', label: 'Extracting structured data', icon: '...' },
  { key: 'rag_query', label: 'Finding similar templates', icon: '...' },
  { key: 'generating', label: 'Generating MDA template', icon: '...' },
  { key: 'validating', label: 'Validating output', icon: '...' },
  { key: 'complete', label: 'Complete', icon: '...' },
]
```

#### Links
- [Framer Motion Progress](https://www.framer.com/motion/animate-presence/)

#### Testing Strategy
- Progress indicator shows all steps during extraction.
- Steps advance as the backend progresses.
- Confidence scores display on applicable fields.
- Low-confidence fields are visually highlighted.
- No confidence indicators shown when LlamaExtract doesn't provide scores.

#### Common Issues to Avoid
- Don't show fake progress (incrementing timer) — only advance when the backend reports progress.
- Don't fabricate confidence scores — this is a PoC, honesty is better than fake metrics.
- Don't block on this task — it's polish, not core functionality.

---

### Task L5.3 - Thesis System Preservation Test

**Phase:** 5 (Validation) | **Dependencies:** L5.1

#### What to Do
- Verify the existing thesis system is completely unaffected by the LIMS PoC:
  1. Start thesis stack: `docker-compose -f docker-compose.dev.yml up -d`
  2. Run existing thesis tests: `uv run pytest main/tests/ -v`
  3. Submit a test job via `POST /jobs` — verify it completes
  4. Verify ChromaDB `pharmaceutical_regulations` collection is intact
  5. Verify all thesis frontend pages render correctly
- Document results as the final Phase 5 gate evidence.
- This is the "do no harm" verification.

#### Dependencies
- L5.1 (LIMS integration test completed — now verify thesis is unaffected).

#### Best Practices
- Run thesis tests AFTER the LIMS PoC is fully set up — this catches any accidental interference.
- Compare test results before and after LIMS changes.
- Check that no LIMS imports leak into thesis code paths.

#### Code Example
```bash
# Thesis preservation test
docker-compose -f docker-compose.dev.yml up -d
sleep 15

# Existing tests pass
uv run pytest main/tests/ -v

# Thesis API works
curl -f http://localhost:8080/health

# ChromaDB thesis collection intact
python -c "
import chromadb
client = chromadb.PersistentClient(path='./chroma_db')
collection = client.get_collection('pharmaceutical_regulations')
print(f'Thesis collection has {collection.count()} documents')
assert collection.count() > 0, 'Thesis collection is empty!'
"

# Thesis frontend pages load
curl -f http://localhost:3000/generate
curl -f http://localhost:3000/history
```

#### Links
- N/A (validation of existing functionality)

#### Testing Strategy
- All existing `main/tests/` tests pass without modification.
- Thesis job submission works.
- ChromaDB `pharmaceutical_regulations` collection has the same document count as before.
- Thesis frontend pages render correctly.
- No LIMS code is imported in thesis code paths (verified by grep).

#### Common Issues to Avoid
- Don't run both Docker compose files simultaneously — they may conflict on ports.
- Don't skip this test — it's the most important validation for the "never modify, always add" principle.
- If any thesis test fails, investigate immediately — this means the additive strategy has been violated.

---

## 11. Task Dependency Graph

```
Phase 0: Setup & Data
  L0.1 (deps + test data) ──┬──> L0.2 (package) ──> L0.3 (docker)
                             │                  └──> L0.4 (CI smoke)
                             │
Phase 1: Models (3 core)     │
  L1.1 (models) <────────────┘──> L1.2 (extract) ──> L1.3 (API)
                             │
Phase 2: MDA Generation      │
  L2.1 (chroma) <────────────┘   [OPTIONAL, parallel]
  L2.2 (workflow) <── L1.2        [L2.1 optional enhancement]
  L2.3 (xlsx) <── L1.1
  L2.4 (e2e + contract tests) <── L1.3 + L2.2 + L2.3

Phase 3: Frontend
  L3.1 (lims page) <── L1.3
  L3.2 (MDA viewer) <── L1.1 + L3.1
  L3.3 (layout/nav) <── L3.1       [_app.tsx NOT modified]
  L3.4 (wiring) <── L3.1 + L3.2 + L3.3 + L2.3

Phase 4: Chat
  L4.1 (chat backend) <── L2.2
  L4.2 (chat UI) <── L4.1 + L3.1
  L4.3 (MDA modification) <── L4.1 + L4.2 + L3.2

Phase 5: Integration
  L5.1 (e2e integration) <── L2.4 + L4.3
  L5.2 (progress UI) <── L3.4
  L5.3 (thesis preservation) <── L5.1
```

---

## 12. Risk Analysis

### 12.1 Migration Risks (Breaking Existing Functionality)

| Risk | Severity | Mitigation |
|------|----------|-----------|
| **Dependency conflicts** (`llama-cloud` + existing pinned versions) | HIGH | Test installation in isolation first (L0.1). Separate virtualenv if needed. |
| **Frontend auth breakage** (removing Clerk breaks all pages) | LOW | Route-based exclusion: `/lims` routes not in `isProtectedRoute`. `_app.tsx` unchanged. Clerk stays for thesis pages. |
| **Docker compose changes** break thesis dev stack | MEDIUM | Separate `docker-compose.lims.yml`. Original `docker-compose.dev.yml` untouched. |
| **Modifying `app.py`** breaks existing API | MEDIUM | Mount new router at `/lims/*`. One-line addition, existing routes untouched. |
| **ChromaDB corruption** (thesis `pharmaceutical_regulations`) | MEDIUM | Separate collection `mda_templates` at `chroma_db_lims/`. |
| **Shared config conflicts** | LOW | `LIMS_*` prefixed env vars. Separate `LIMSConfig` class. |
| **Frontend page conflicts** | LOW | New `pages/lims.tsx`. Existing `pages/generate.tsx` untouched. |

### 12.2 PoC-Specific Risks

| Risk | Severity | Mitigation |
|------|----------|-----------|
| LlamaExtract can't handle complex pharmaceutical tables | MEDIUM | Test on example PDF Day 1 (L1.2). Backup: GPT-5 vision via OpenRouter or AWS BDA. |
| **LlamaExtract schema tuning** (iterative refinement time) | **HIGH** | Expect 3-5 iterations of schema tuning before extraction quality stabilizes. Budget at least half a day. Log raw results for comparison. |
| 19-page PDF exceeds extraction limits | MEDIUM | Page-by-page extraction with cross-page context assembly. |
| Chat modifications break MDA consistency | MEDIUM | Pydantic validation after each modification rejects invalid state (L4.1). |
| LLM hallucinates LIMS Basic code | MEDIUM | RAG provides real examples. Post-processing validates syntax. |
| 2-week timeline too tight | MEDIUM | Week 1 = MVP (extraction + display). Chat = Week 2 stretch goal. |
| LlamaExtract API quota/access issues | LOW | Sign up early (L0.1), verify API access before committing. |

---

## 13. Cost Analysis

### 13.1 PoC Costs (2-Week Period)

| Service | Usage | Cost |
|---------|-------|------|
| **LlamaExtract** | 380 pages, balanced mode | $7.60 |
| **LlamaExtract** (premium if needed) | 380 pages, premium mode | $22.80 |
| **OpenRouter LLM** (GPT-5) | ~50 chat + generation calls | $5-15 |
| **OpenRouter LLM** (Claude Opus 4.6) | ~50 chat + generation calls | $10-30 |
| **Docker (local)** | Development machine | $0 |
| **ChromaDB** | Local storage | $0 |
| **Total (balanced + GPT-5)** | | **~$13-23** |
| **Total (premium + Claude)** | | **~$33-53** |

### 13.2 Post-PoC Production Estimate (Monthly)

| Service | Configuration | Cost |
|---------|--------------|------|
| LlamaExtract | 100 PDFs/month, balanced | ~$200 |
| OpenRouter LLM | 500 chat interactions/month | ~$50 |
| AWS ECS (API + Frontend) | 2 containers, 24h | ~$140 |
| ChromaDB on ECS | 1 small container | ~$30 |
| CloudFront + S3 | Static assets + XLSX storage | ~$10 |
| **Total** | | **~$430/month** |

---

## 14. Verification Plan

### 14.1 Phase Gate Summary

| Phase | Gate | Verification Method |
|-------|------|-------------------|
| 0 | Environment Ready | CLI commands return success, Docker starts, API key works |
| 1 | Extraction Works (3 Core Sheets) | API endpoint returns valid Pydantic JSON from PDF (Analysis, Component, Calculation) |
| 2 | Full MDA Pipeline | XLSX generated with 4 sheets, content matches format. RAG optional. |
| 3 | Frontend Displays MDA | Browser test: upload -> tables -> download |
| 4 | Chat Modifies MDA | Browser test: chat modifies tables, Pydantic validates |
| 5 | Demo-Ready | Full e2e works, thesis system unaffected |

### 14.2 Extraction Accuracy Assessment

Upload `ex_2_was_pdf` -> compare AI-generated MDA against human-created `ex_2_was_xlsx`:
- [ ] All Analysis objects identified correctly
- [ ] Components match (names, types, units, order)
- [ ] Calculation variables correctly cross-referenced
- [ ] LIMS Basic code logic matches (conditional logic, formulas)

### 14.3 Chat Functionality Verification

Can the operator successfully:
- [ ] Ask why a component was created a certain way
- [ ] Request a modification and see it reflected in the table
- [ ] Ask questions about the source PDF content

### 14.4 XLSX Export Verification

- [ ] Generated file opens in Excel with correct 4-sheet formatting
- [ ] Column headers match LabWare MDA import format
- [ ] Data values are correctly typed (numbers as numbers, not strings)

### 14.5 End-to-End Demo

- [ ] PDF upload -> AI extraction -> MDA display -> chat refinement -> XLSX download
- [ ] Complete in under 5 minutes (extraction + generation time)

### 14.6 Thesis Preservation

- [ ] `docker-compose -f docker-compose.dev.yml up -d` starts thesis system without errors
- [ ] `uv run pytest main/tests/ -v` all existing tests pass
- [ ] Thesis job submission (`POST /jobs`) still works
- [ ] ChromaDB `pharmaceutical_regulations` collection intact

---

## 15. Acceptance Criteria

### Functional
- [ ] End-to-end workflow completes: PDF upload -> MDA extraction -> table display -> chat refinement -> XLSX download
- [ ] Extraction produces structured data for at least 1 Analysis, 3+ Components, 1+ Calculation
- [ ] Chat can explain extraction decisions and modify MDA template
- [ ] XLSX export matches LabWare 4-sheet format
- [ ] Thesis system fully functional after LIMS PoC deployment

### Extraction Quality
- [ ] LlamaExtract returns structured JSON matching MDA Pydantic schema
- [ ] At least 70% of extracted fields match the human-created example MDA
- [ ] Confidence scores (where available) correctly identify uncertain extractions
- [ ] Citations link extracted data to source PDF locations

### Chat Capabilities
- [ ] Chat explains extraction decisions with PDF citations
- [ ] Chat modifies MDA components (add, update, delete)
- [ ] Modified MDA passes Pydantic validation (no silent corruption)
- [ ] Chat maintains conversation context across multiple messages

### Export Quality
- [ ] XLSX opens in Microsoft Excel without errors
- [ ] All 4 sheets present with correct names
- [ ] Column headers match LabWare field names
- [ ] Data types are correct (numeric, text, date)

---

## Appendix A: Files Created/Modified

### New Files (14+)

| File | Purpose |
|------|---------|
| `docker-compose.lims.yml` | Minimal Docker stack (frontend + API) |
| `main/api/lims_router.py` | LIMS API endpoints |
| `main/src/lims/__init__.py` | LIMS package init |
| `main/src/lims/config.py` | LIMS configuration (LIMS_* env vars) |
| `main/src/lims/mda_schema.py` | 4 core sheet MDA Pydantic models (9 enums, 4 models, cross-sheet validators) |
| `main/src/lims/pdf_extractor.py` | LlamaExtract integration |
| `main/src/lims/mda_generator.py` | LlamaIndex MDA generation workflow |
| `main/src/lims/chat_agent.py` | Chat engine for MDA refinement |
| `main/src/lims/xlsx_exporter.py` | XLSX export (openpyxl) |
| `main/src/lims/prompts/extraction_prompt.py` | Extraction schema prompt |
| `main/src/lims/prompts/mda_generation_prompt.py` | MDA generation prompt |
| `main/src/lims/prompts/chat_system_prompt.py` | Chat system prompt |
| `main/frontend/pages/lims.tsx` | Main LIMS page |
| `main/frontend/components/ChatInterface.tsx` | Chat UI component |
| `main/frontend/components/MDAViewer.tsx` | Tabbed MDA table viewer |
| `main/frontend/components/PDFPreview.tsx` | PDF preview component (optional) |
| `scripts/populate_lims_chroma.py` | ChromaDB population script |

### Modified Files (4, minimal changes)

| File | Change | Lines Changed |
|------|--------|---------------|
| `main/api/app.py` | Add `app.include_router(lims_router, prefix="/lims")` | ~2 lines |
| `main/frontend/components/Layout.tsx` | Add "LIMS" nav link | ~1 line |
| `main/frontend/middleware.ts` | Verify `/lims` not in `isProtectedRoute` (may need 0 changes) | ~0-1 lines |
| `pyproject.toml` | Add `llama-cloud`, `openpyxl`, `PyMuPDF` + regenerate `requirements-prod.txt` | ~3 lines |

### Untouched Files

All thesis files not listed above remain completely unchanged:
- `main/frontend/pages/generate.tsx`, `history.tsx`
- `docker-compose.dev.yml`
- `main/api/worker.py`, `dependencies.py`
- `main/src/agents/`, `main/src/core/`
- `chroma_db/`

---

## Appendix B: Environment Variables

```bash
# .env.local additions for LIMS PoC
# (All prefixed with LIMS_ to avoid conflicts)

# LlamaExtract
LIMS_LLAMAEXTRACT_API_KEY=llx-...

# OpenRouter (LLM)
LIMS_OPENROUTER_API_KEY=sk-or-...
LIMS_OPENROUTER_MODEL=openai/gpt-5

# ChromaDB
LIMS_CHROMADB_COLLECTION=mda_templates
LIMS_CHROMADB_PATH=./chroma_db_lims

# Storage
LIMS_UPLOAD_DIR=./uploads/lims
LIMS_OUTPUT_DIR=./output/lims

# Auth: No feature flag needed — /lims routes are public by default via middleware.ts route matcher
```

---

## Appendix C: Reusable Components

| Component | Source | Reuse Strategy |
|-----------|--------|----------------|
| Next.js UI shell | `main/frontend/` | Direct reuse |
| FileUpload pattern | `main/frontend/components/FileUpload.tsx` | Copy pattern, adapt for PDF |
| Job progress pattern | `main/frontend/components/JobProgress.tsx` | Adapt stages for extraction |
| ChromaDB adapter | `main/src/adapters/chroma_adapter.py` | Reuse for `mda_templates` |
| LlamaIndex workflow | `main/src/core/unified_workflow.py` | Reuse `Workflow` + `@step` |
| Storage adapters | `main/src/adapters/storage.py` | Reuse for PDF/XLSX storage |
| Docker patterns | `docker-compose.dev.yml` | Adapt for minimal stack |
| FastAPI patterns | `main/api/app.py` | Reuse lifespan, middleware |
| Framer Motion + 3D | `main/frontend/components/3d/` | Direct reuse for polish |

---

**Document Version:** 1.2
**Last Updated:** 2026-02-16
**Next Review:** After Phase 0 completion
**Approved By:** [Pending stakeholder review]

---

*This Production Readiness Plan is a living document and will be updated as the PoC progresses. All changes should be tracked in version control and communicated to stakeholders.*

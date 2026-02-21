# AI4LIMS Proof of Concept - Production Readiness Plan (PRP)

**Owner:** Platform Engineering (AI Systems)
**Date:** 2026-02-19
**Version:** 1.4
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

#### Single-Layer Pipeline (Phase 1-7, TestType.OTHER)

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

#### Two-Layer Pipeline (Phase 8+, HPLC/LOD/Titration/Identity)

```
PDF Upload
    |
    v
[1. CLASSIFY] -- Detect test type (HPLC/LOD/Titration/Identity) via hybrid rules+LLM
    |
    v
[2. TEMPLATE] -- Load curated skeleton for that test type (~46% of components)
    |
    v
[3. EXTRACT] -- Focused extraction from PDF (only variable fields)
    |
    v
[4. AUGMENT] -- AI fills template gaps via standards RAG (CD-026972, SOP-00597)
    |
    v
[5. MERGE] -- Combine Template + Variable + Augmented, detect conflicts
    |          Every component tagged with source (Template/Extracted/Inferred/SME Required)
    v
[6. SME REVIEW] -- Step-by-step visual workflow with provenance badges
    |               Conflict resolution panel, chat refinement
    v
[7. EXPORT] -- XLSX with optional provenance sheet
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
| `/lims/extract` | POST | Upload PDF, trigger two-layer pipeline | `multipart/form-data` (PDF file) | `{ job_id, status, trace_id, trace_url }` |
| `/lims/classify` | POST | Test type classification only | `multipart/form-data` (PDF file) | `{ test_type, confidence, method }` |
| `/lims/template/{type}` | GET | Get curated template skeleton | - | `{ template }` |
| `/lims/status/{job_id}` | GET | Poll extraction progress | - | `{ status, progress_pct, current_step, mda_template? }` |
| `/lims/chat` | POST | HITL refinement chat | `{ job_id, message }` | `{ response, updated_mda?, citations? }` |
| `/lims/approve/{job_id}` | POST | Human approval | - | `{ status }` |
| `/lims/export/{job_id}` | GET | Download MDA as XLSX (APPROVED only) | - | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |

The `/lims/extract` response includes `trace_id` and `trace_url` — direct links to the Langfuse Cloud trace for the pipeline run. All pipeline stages (classify, extract, augment, merge) are auto-nested under the parent trace.

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

The PoC follows a **strict test-first, gated pipeline**. Each feature is built backend-first, tested in both local and Docker environments, then gets a UI. Every phase has explicit pass/fail gate criteria that must be met before the next phase begins.

| Phase | Name | Gate |
|-------|------|------|
| Phase 1 | PDF Extraction Backend | **DONE** — Validated per LIMS-001 |
| Phase 2 | Extraction Testing (Local + Docker) | Extraction works in both environments, pytest passes |
| Phase 3 | Extraction UI | User sees extracted MDA in tabbed tables in browser |
| Phase 4 | MDA Workflow + Mandatory HITL + Export | Full pipeline with mandatory human review, no skip path |
| Phase 5 | Full Pipeline Testing (Local + Docker) | E2E works in both environments, thesis preserved |
| Phase 6 | Full HITL UI | Demo-ready: Upload -> Extract -> Review -> Chat -> Approve -> Export |
| Phase 8 | Two-Layer Pipeline Architecture | Full pipeline: Classify -> Template -> Extract -> Augment -> Merge -> Review with provenance |

### 9.2 Phase Gate Criteria (Pass/Fail)

**Phase 1 Gate: Extraction Works — DONE**
- [x] `POST /lims/extract` with demo PDF returns structured JSON
- [x] At least 1 Analysis, 3+ Components extracted
- [x] Raw extraction results logged

**Phase 2 Gate: Extraction Verified in Both Environments**
- [ ] Local: `curl POST /lims/extract` returns valid MDA JSON (1+ analyses, 3+ components)
- [ ] Docker: same test passes from containerized API via `docker-compose.lims.yml`
- [ ] `uv run pytest main/tests/lims/ -v` passes (mock + integration tests)
- [ ] Thesis tests unaffected: `uv run pytest main/tests/ -v` passes

**Phase 3 Gate: User Can See Extracted Data**
- [ ] Upload PDF in browser -> see loading spinner -> see MDA in 4 tabbed tables
- [ ] Each tab (Analysis, Component, CalcVariable, Calculation) shows correct columns and data
- [ ] Works at `localhost:3000/lims`
- [ ] Thesis pages (`/generate`, `/history`) still accessible

**Phase 4 Gate: Full Pipeline with Mandatory HITL**
- [ ] Full pipeline: PDF -> extract -> RAG -> preliminary MDA -> chat review -> approve -> XLSX
- [ ] Chat can explain extraction decisions
- [ ] Chat can modify MDA, changes validated by Pydantic
- [ ] Invalid modifications rejected (MDA unchanged)
- [ ] XLSX has correct 4-sheet structure
- [ ] **No path exists to produce XLSX without human approval**
- [ ] Thesis tests unaffected

**Phase 5 Gate: Pipeline Works in Both Environments**
- [ ] Local: full pipeline succeeds including chat HITL and XLSX export
- [ ] Docker: full pipeline succeeds
- [ ] Thesis system: `docker-compose.dev.yml` starts, job submission works
- [ ] No LIMS imports in thesis code paths

**Phase 6 Gate: PoC Demo-Ready**
- [ ] Full visual flow: Upload -> Extract -> See Table -> Chat -> Modify -> Approve -> Download XLSX
- [ ] Step indicator shows current pipeline stage
- [ ] Chat modifications reflect immediately in MDA table
- [ ] Export only available after human approval
- [ ] Demo rehearsal completed

### 9.3 Mandatory HITL Design

**Critical difference from thesis system:** The thesis HITL (`main/src/core/human_consultation.py`) uses confidence-threshold triggers — consultation only activates when AI confidence is low. The LIMS PoC uses **always-mandatory HITL** — every MDA must be reviewed by a human before finalization.

```
PDF → Extract → RAG → Preliminary MDA → [PENDING_REVIEW]
                                              ↓
                                    Human reviews MDA tables
                                    Human chats: asks questions, requests changes
                                    AI applies structured edits (Pydantic validated)
                                              ↓
                                    Human clicks "Approve & Finalize"
                                              ↓
                                    Final MDA → XLSX Export
```

**Rules:**
- After preliminary MDA generation, job status = `PENDING_REVIEW`
- No confidence threshold — review is always mandatory
- No timeout auto-approval — human must explicitly approve
- Human interacts via chat only (no inline table editing)
- Each chat modification validated by Pydantic before applying
- Human must explicitly approve to move job to `APPROVED` status
- XLSX export endpoint returns 403 for non-`APPROVED` jobs

**Reusable patterns from thesis (adapt, don't import):**
- Session management from `HumanConsultationManager`
- Audit trail logging patterns from `GAMP5ComplianceLogger`
- `HumanApprovalRequired` exception pattern from `ConsultationEventHandler`

### 9.4 Kill Criteria (Stop/Pivot Triggers)

If any of the following are true after the stated deadline, stop the current approach and pivot:

| Criterion | Threshold | Deadline | Pivot Action |
|-----------|-----------|----------|-------------|
| **Extraction accuracy** | < 40% of components correctly typed after 3 schema iterations | End of Phase 2 | Switch to Vision LLM direct (GPT-5/Claude) with structured output |
| **Per-document extraction cost** | > $5 per PDF (balanced mode) | Phase 2 | Switch to `fast` mode or Vision LLM direct |
| **Full pipeline runtime** | > 10 minutes for a single 19-page PDF | Phase 4 | Profile bottleneck; reduce context if LLM generation |
| **Cross-sheet extraction** | AI cannot identify the 3-analysis pattern after 3 attempts | Phase 2 | Hard-code analysis structure; let AI fill component details only |

---

## 10. Task Breakdown (18 Tasks)

### Phase 1: PDF Extraction Backend — DONE (0 tasks)

Completed per LIMS-001 documentation. Working files:
- `main/src/lims/pdf_extractor.py` — LlamaExtract extraction
- `main/src/lims/extraction_schema.py` — Simplified schema for LlamaExtract
- `main/src/lims/mda_schema.py` — Full Pydantic MDA schema with validators
- `main/src/lims/config.py` — LIMS configuration from env vars
- `main/api/lims_router.py` — `POST /lims/extract` endpoint
- `main/frontend/pages/lims.tsx` — Basic upload UI + JSON display

---

### Phase 2: Extraction Testing — Local + Docker (3 tasks)

---

### Task L2.1 — Local Extraction Test

**Phase:** 2 (Testing) | **Dependencies:** Phase 1 (done)

**What to Do:**
- Start the API server locally using `uvicorn` or `uv run`
- Test `POST /lims/extract` with the demo PDF (`demo_data/AND_ACS_AQ126-LAB-2349.pdf`)
- Verify the response contains valid structured MDA data
- Document the exact commands and expected output

**Testing Strategy:**
```bash
# Start local server
uv run uvicorn main.api.app:app --port 8080

# Test extraction
curl -X POST http://localhost:8080/lims/extract \
  -F "file=@demo_data/AND_ACS_AQ126-LAB-2349.pdf"
```
- Response must contain `raw_extraction` with at least 1 analysis, 3+ components
- If WSL numpy import error occurs (known issue per LIMS-001), fall back to Docker

---

### Task L2.2 — Docker Extraction Test

**Phase:** 2 (Testing) | **Dependencies:** L2.1

**What to Do:**
- Ensure `docker-compose.lims.yml` exists and builds correctly
- Start containers: `docker compose -f docker-compose.lims.yml up -d`
- Test `POST /lims/extract` from the containerized API
- Verify same structured output as local test

**Testing Strategy:**
```bash
docker compose -f docker-compose.lims.yml up -d
curl -X POST http://localhost:8080/lims/extract \
  -F "file=@demo_data/AND_ACS_AQ126-LAB-2349.pdf"
docker compose -f docker-compose.lims.yml down
```
- Response must match local test output structure
- Container must start without errors, health check passes

---

### Task L2.3 — Extraction Pytest Suite

**Phase:** 2 (Testing) | **Dependencies:** L2.1

**What to Do:**
- Create `main/tests/lims/` directory with `conftest.py` and `test_extraction.py`
- Write unit tests: mock LlamaExtract client, verify Pydantic parsing
- Write schema roundtrip test: create `MDATemplate`, serialize, deserialize, compare
- Write integration test (marked `@pytest.mark.integration`): real API call if key available
- Verify thesis tests still pass

**Testing Strategy:**
```bash
uv run pytest main/tests/lims/ -v          # LIMS tests
uv run pytest main/tests/ -v               # All tests (includes thesis)
```

---

### Phase 3: Extraction UI (3 tasks)

---

### Task L3.1 — MDA Table Viewer Component

**Phase:** 3 (UI) | **Dependencies:** Phase 2 gate passed

**What to Do:**
- Create `main/frontend/components/MDAViewer.tsx`
- Tabbed interface with 4 tabs: Analysis, Components, CalcVariables, Calculations
- Each tab renders a data table with appropriate columns
- Handle empty sheets gracefully (show "No data" message)
- Use the emerald color scheme from existing `lims.tsx`

**Testing Strategy:**
- Component renders without errors with sample MDA data
- Each tab shows correct columns
- Empty data shows appropriate message

---

### Task L3.2 — Wire Extraction Result to Table Viewer

**Phase:** 3 (UI) | **Dependencies:** L3.1

**What to Do:**
- Update `main/frontend/pages/lims.tsx` to replace raw JSON `<pre>` display with `<MDAViewer>`
- Pass extraction result (either `mda_template` or `raw_extraction`) as props
- Show validated badge if Pydantic validation passed, warning if raw data only

**Testing Strategy:**
- Upload PDF -> extraction completes -> tabbed tables appear instead of raw JSON
- Both validated and raw extraction data render correctly

---

### Task L3.3 — Extraction Progress Indicators

**Phase:** 3 (UI) | **Dependencies:** L3.2

**What to Do:**
- Improve loading state during extraction (currently just spinner text)
- Add extraction stage indicators: "Uploading..." -> "Extracting..." -> "Validating..."
- Improve error display with actionable messages

**Testing Strategy:**
- Loading state shows progress stages during extraction
- Error messages are clear and actionable

---

### Phase 4: MDA Generation Workflow + Mandatory HITL + Export (6 tasks)

---

### Task L4.1 — ChromaDB MDA Templates Collection

**Phase:** 4 (Workflow) | **Dependencies:** Phase 3 gate passed

**What to Do:**
- Create `main/src/lims/rag_loader.py` to seed ChromaDB `mda_templates` collection
- Parse 2-5 example MDA XLSX files into `MDATemplate` Pydantic objects
- Embed and store in ChromaDB at `chroma_db_lims/` directory
- Provide query interface: given extraction result, find similar templates

**Testing Strategy:**
- Collection has 2+ documents after seeding
- Query returns relevant results for a test extraction

---

### Task L4.2 — MDA Generation Workflow

**Phase:** 4 (Workflow) | **Dependencies:** L4.1

**What to Do:**
- Create `main/src/lims/mda_generator.py` with LlamaIndex workflow
- Pipeline: raw extraction + RAG context -> LLM generates complete preliminary MDA
- Use OpenRouter (GPT-5 or Claude Opus 4.6) via OpenAI-compatible SDK
- After generation, set job status to `PENDING_REVIEW` (mandatory HITL)
- Store preliminary MDA in in-memory job store

**Testing Strategy:**
- Workflow produces `MDATemplate` with all 4 sheets populated
- Job status is `PENDING_REVIEW` after workflow completes
- MDA validates against Pydantic schema

---

### Task L4.3 — Chat Agent for MDA Refinement

**Phase:** 4 (Workflow) | **Dependencies:** L4.2

**What to Do:**
- Create `main/src/lims/chat_agent.py` with `MDAChatAgent` class
- LLM context: full PDF content + current MDA state + extraction citations
- Use OpenRouter via OpenAI-compatible SDK with function calling
- Structured `MDAEditAction` tool for modifications (sheet, action, target, changes, reason)
- Pydantic validation after every edit — reject invalid changes
- Short-term memory per `job_id`: messages, modification log, current MDA state
- Memory guardrails: TTL (2 hours), max turns (50 messages)

**Testing Strategy:**
- Chat answers questions about extraction decisions
- Chat modifies MDA via structured edit actions
- Invalid modification returns error, MDA unchanged
- Conversation history maintained across messages

---

### Task L4.4 — Mandatory HITL Integration

**Phase:** 4 (Workflow) | **Dependencies:** L4.3

**What to Do:**
- Implement job state machine: `EXTRACTING` -> `GENERATING` -> `PENDING_REVIEW` -> `APPROVED` -> `EXPORTED`
- After preliminary MDA generation, job enters `PENDING_REVIEW` — **no automatic progression**
- Human must explicitly call `POST /lims/approve/{job_id}` to move to `APPROVED`
- No confidence threshold check — review is always mandatory
- No timeout auto-approval — job stays in `PENDING_REVIEW` indefinitely until human acts
- Adapt session/audit patterns from `main/src/core/human_consultation.py` (but simplified: no timeout monitoring, no escalation — just mandatory approval gate)
- XLSX export returns 403 for non-`APPROVED` jobs

**Testing Strategy:**
- Job in `PENDING_REVIEW` cannot produce XLSX (403 error)
- Job must be explicitly approved via API call
- After approval, job moves to `APPROVED` and XLSX export works
- No path exists to bypass approval

---

### Task L4.5 — XLSX Export

**Phase:** 4 (Workflow) | **Dependencies:** L4.2

**What to Do:**
- Create `main/src/lims/xlsx_exporter.py` using openpyxl
- Export `MDATemplate` to 4-sheet XLSX matching LabWare format
- Sheet names: "Analysis", "Component", "Calc Variable", "Calculation"
- Column headers match LabWare MDA field names
- Exports the **final** (human-approved) MDA state, not the preliminary version

**Testing Strategy:**
- Generated XLSX opens in Excel with 4 sheets
- Column headers match expected LabWare format
- Data matches the MDA Pydantic model content

---

### Task L4.6 — LIMS Router Endpoints

**Phase:** 4 (Workflow) | **Dependencies:** L4.2, L4.3, L4.4, L4.5

**What to Do:**
- Add to `main/api/lims_router.py`:
  - `GET /lims/status/{job_id}` — job status + current MDA state
  - `POST /lims/chat` — send chat message, receive response + optional MDA updates
  - `POST /lims/approve/{job_id}` — human approval endpoint (mandatory HITL gate)
  - `GET /lims/export/{job_id}` — download XLSX (only for `APPROVED` jobs, 403 otherwise)
- Update `POST /lims/extract` to return `job_id` and trigger async pipeline

**Testing Strategy:**
- Full API flow: extract -> status (PENDING_REVIEW) -> chat -> approve -> export
- Export returns 403 before approval
- Chat returns updated MDA after modification

---

### Phase 5: Full Pipeline Testing — Local + Docker (3 tasks)

---

### Task L5.1 — Local End-to-End Test

**Phase:** 5 (Testing) | **Dependencies:** Phase 4 gate passed

**What to Do:**
- Run full pipeline locally: PDF upload -> extract -> generate -> chat review -> approve -> XLSX
- Document exact commands and expected responses at each stage
- Verify XLSX content matches expected MDA structure

**Testing Strategy:**
```bash
# 1. Start server
uv run uvicorn main.api.app:app --port 8080

# 2. Upload and extract
curl -X POST http://localhost:8080/lims/extract -F "file=@demo.pdf"
# Returns: { "job_id": "..." }

# 3. Check status
curl http://localhost:8080/lims/status/{job_id}
# Returns: { "status": "PENDING_REVIEW", "mda_template": {...} }

# 4. Chat (ask question)
curl -X POST http://localhost:8080/lims/chat \
  -H "Content-Type: application/json" \
  -d '{"job_id": "...", "message": "Why is DYE_VOLUME result_type K?"}'

# 5. Approve
curl -X POST http://localhost:8080/lims/approve/{job_id}
# Returns: { "status": "APPROVED" }

# 6. Export
curl -O http://localhost:8080/lims/export/{job_id}
# Downloads XLSX file
```

---

### Task L5.2 — Docker End-to-End Test

**Phase:** 5 (Testing) | **Dependencies:** L5.1

**What to Do:**
- Run full pipeline in Docker: `docker compose -f docker-compose.lims.yml up -d`
- Execute same test sequence as L5.1 against containerized API
- Verify identical results

**Testing Strategy:**
- Same curl commands as L5.1 but against Docker container
- Results must match local test

---

### Task L5.3 — Thesis Preservation Test

**Phase:** 5 (Testing) | **Dependencies:** L5.1

**What to Do:**
- Start thesis system: `docker compose -f docker-compose.dev.yml up -d`
- Verify thesis job submission still works
- Verify no LIMS code is imported by thesis code paths
- Grep for cross-contamination: `grep -r "from main.src.lims" main/src/core/ main/src/agents/`

**Testing Strategy:**
- `docker compose -f docker-compose.dev.yml up -d` starts without errors
- `curl POST /jobs` thesis endpoint works
- No LIMS imports found in thesis code

---

### Phase 6: Full HITL UI (4 tasks)

---

### Task L6.1 — Chat Interface Component

**Phase:** 6 (UI) | **Dependencies:** Phase 5 gate passed

**What to Do:**
- Create `main/frontend/components/ChatInterface.tsx`
- Streaming chat responses with markdown rendering
- Message history display (user messages + AI responses)
- Input field with send button
- Show modification log when AI applies structured edits

**Testing Strategy:**
- Send message -> see streaming response
- Message history persists across turns
- Modification actions highlighted in chat

---

### Task L6.2 — HITL Review Flow UI

**Phase:** 6 (UI) | **Dependencies:** L6.1

**What to Do:**
- Update `main/frontend/pages/lims.tsx` with multi-step flow
- Step indicator: Extract -> Review -> Approve -> Export
- Visual state transitions based on job status
- "Approve & Finalize" button (calls `POST /lims/approve/{job_id}`)
- Button disabled until human has reviewed (at minimum viewed the MDA tables)

**Testing Strategy:**
- Step indicator shows correct current stage
- Approve button triggers status change
- UI updates to show approved state

---

### Task L6.3 — Real-Time MDA Table Updates

**Phase:** 6 (UI) | **Dependencies:** L6.1, L3.1

**What to Do:**
- After each chat edit, re-fetch MDA and update `MDAViewer` component
- Show modification highlight (changed cells/rows)
- Show modification history/log sidebar

**Testing Strategy:**
- Chat modification -> table updates immediately
- Modified fields visually highlighted
- Modification log shows edit history

---

### Task L6.4 — Export Download Button

**Phase:** 6 (UI) | **Dependencies:** L6.2

**What to Do:**
- Add XLSX download button to `lims.tsx`
- Button only enabled when job status = `APPROVED`
- Calls `GET /lims/export/{job_id}` and triggers browser download
- Filename includes timestamp: `MDA_{analysis_name}_{timestamp}.xlsx`

**Testing Strategy:**
- Button disabled before approval
- Button enabled after approval
- Click triggers XLSX download with correct filename

---

### Phase 7: Optimization — Data Quality, RAG & Evaluation (3 tasks)

---

### Task L7 — Extraction Data Quality: Post-Processing, Normalization & SDK Migration

**Phase:** 7 (Optimization) | **Dependencies:** Phase 6 gate passed
**PRP Task File:** `PRPs/tasks/L7-extraction-normalization-sdk-migration.md`
**Status:** ✅ Done (2026-02-18)

**Completion Snapshot:**
- Added normalization layer in `main/src/lims/data_normalizer.py` and integrated it in `main/src/lims/pdf_extractor.py` before strict Pydantic validation.
- Added semantic enum/value normalization and cross-sheet reference normalization for extraction outputs.
- Added extraction API switch in `main/src/lims/config.py` (`llamaextract|llamaparse_v2`) with fail-loud handling for unimplemented runtime path.
- Resolved SDK compatibility with deterministic pins in `pyproject.toml`: `llama-cloud-services==0.6.93`, `llama-cloud==0.1.46`.
- Added regression coverage in `main/tests/lims/test_data_normalizer.py` and extractor assertions in `main/tests/lims/test_extraction.py`.
- Added extraction traceability/monitoring metadata (`agent_name`, `run_id`, `run_status`, `duration_ms`, `pdf_sha256`) persisted on job state and exposed via `/lims/extract` and `/lims/status/{job_id}`.

**Verification Results:**
- `uv run pytest main/tests/lims/test_data_normalizer.py main/tests/lims/test_extraction.py -v` → `11 passed, 1 skipped`
- `uv run pytest main/tests/lims/ -v` → `96 passed, 4 skipped`

**Issue Tracking:**
- Detailed records: `ISSUE-028`, `ISSUE-029`, `ISSUE-030`, `ISSUE-031`
- Consolidated rollup: `docs/issues/ISSUE-032-l7-extraction-quality-consolidated.md`

**What to Do:**
- Create `main/src/lims/data_normalizer.py` for post-extraction normalization (symbol cleanup, type coercion, naming conventions, LIMS defaults)
- Integrate normalization into `pdf_extractor.py` between raw extraction and Pydantic validation
- Research and document SDK migration path: `llama-cloud-services` (deprecated EOL May 2026) vs `llama-cloud` v1.4.0 vs LlamaParse v2
- Add `extraction_api` config field for A/B testing extraction approaches

**Testing Strategy:**
- Unit tests for all normalization functions
- Integration test: extract + normalize + validate on 3+ demo PDFs
- Existing LIMS tests still pass

---

### Phase 8: Two-Layer Pipeline Architecture (7 tasks)

The AI4LIMS pilot revealed only ~54% of MDA components exist in the test method PDF (range: 21-96% across 18 test methods). Phase 8 implements a test-method agnostic two-layer architecture: curated templates (~46%) + focused PDF extraction + standards RAG augmentation, with full provenance tracking.

---

### Task L10 — Foundation Models: Provenance, TestType & Template Base Classes

**Phase:** 8a (Foundation) | **Dependencies:** L7 (done)
**PRP Task File:** `PRPs/tasks/L10-foundation-provenance-testtype-templates-base.md`
**Status:** ✅ Done (2026-02-19)

**What to Do:**
- Create `provenance.py`: ComponentSource enum, FieldProvenance, ProvenanceMap
- Create `test_type.py`: TestType enum (HPLC, LOD, Titration, Identity, Other), ClassificationResult
- Create `templates/base.py`: TestTypeTemplate base class, TemplateComponent dataclass
- Create `templates/__init__.py`: TemplateLibrary registry
- Extend `job_store.py`: Add CLASSIFYING, LOADING_TEMPLATE, AUGMENTING, MERGING states
- Extend `config.py`: Add classification_mode, confidence_threshold, standards/calculations collections

---

### Task L11 — Template Library: HPLC, LOD, Titration & Identity Skeletons

**Phase:** 8b (Templates) | **Dependencies:** L10
**PRP Task File:** `PRPs/tasks/L11-template-library-hplc-lod-titration-identity.md`
**Status:** ✅ Done (2026-02-19)

**What to Do:**
- Curate HPLC template from AND_BCMA_CEX, FRE_BOSU ground truth XLSX
- Curate LOD template from AND_USP_LOD XLSX
- Curate Titration template from FRE_KF_USP XLSX
- Curate Identity template from AND_ACS_DYE ground truth (25 components, 3 analyses)
- Register all 4 templates in TemplateLibrary

---

### Task L12 — Hybrid Test Type Classifier

**Phase:** 8c (Classification) | **Dependencies:** L10
**PRP Task File:** `PRPs/tasks/L12-classifier-hybrid-test-type-detection.md`
**Status:** ✅ Done (2026-02-19)

**What to Do:**
- Build hybrid classifier: filename rules -> keyword matching -> LLM fallback
- Create classification system prompt for LLM fallback
- Target >90% accuracy on 18+ demo PDFs

---

### Task L13 — Standards RAG & Augmentation Prompt

**Phase:** 8d (Standards RAG) | **Dependencies:** L10
**PRP Task File:** `PRPs/tasks/L13-standards-rag-augmentation.md`
**Status:** ✅ Done (2026-02-19)

**What to Do:**
- Create standards_loader.py for CD-026972, SOP-00597, gLIMS training PDF ingestion
- Create `lims_standards` and `calculation_patterns` ChromaDB collections
- Build augmentation prompt for gap-filling with citations
- Extend rag_loader.py to support configurable collection names

---

### Task L14 — Pipeline Core: Focused Extractor, Merger & Orchestrator

**Phase:** 8e (Pipeline Core) | **Dependencies:** L10, L11, L12, L13
**PRP Task File:** `PRPs/tasks/L14-pipeline-core-extractor-merger-orchestrator.md`
**Status:** ✅ Done (2026-02-19)

**Completion Snapshot:**
- Created `focused_extractor.py`: text extraction (PyMuPDF), focused schema narrowing (`build_focused_schema()`, `_filter_to_variable_fields()`), full LlamaExtract extraction with output narrowed to variable + identity fields only.
- Created `merger.py`: three-layer merge (Template → Extracted → Augmented → SME_REQUIRED), conflict detection, full provenance tracking via `ProvenanceMap`, cross-sheet Pydantic validation.
- Created `pipeline.py`: `TwoLayerPipeline` orchestrator with 6 stages (CLASSIFY → TEMPLATE → EXTRACT → AUGMENT → MERGE → REVIEW), single-layer fallback for `TestType.OTHER`, job state machine transitions.
- Rewrote `lims_router.py` extract endpoint to use `TwoLayerPipeline`; added `POST /lims/classify` and `GET /lims/template/{type}` endpoints.
- Fixed state machine transitions: added `CLASSIFYING→EXTRACTING` and `EXTRACTING→PENDING_REVIEW` in `job_store.py` for single-layer fallback path.
- Removed all no-fallback violations: `_augment_gaps` (removed try/except), `_transition_job` (removed try/except), `_apply_suggestion_to_dict` (raise ValueError instead of silent return).
- Implemented focused schema narrowing: `build_focused_schema()` analyzes template variable fields, `_filter_to_variable_fields()` strips non-variable fields from extraction data.

**Verification Results:**
- `conda run -n base python -m pytest main/tests/lims/test_merger.py main/tests/lims/test_pipeline.py main/tests/lims/test_lims_router.py -v` → `51 passed, 1 skipped`

**Files Created:**
- `main/src/lims/focused_extractor.py` — Text extraction + focused schema narrowing + LlamaExtract
- `main/src/lims/merger.py` — Three-layer merge with provenance tracking
- `main/src/lims/pipeline.py` — TwoLayerPipeline orchestrator
- `main/src/lims/prompts/augmentation_prompt.py` — Standards RAG augmentation prompt
- `main/tests/lims/test_merger.py` — 24 tests (normalization, matching, merge, conflicts, augmentation, SME_REQUIRED, stats, E2E, error handling)
- `main/tests/lims/test_pipeline.py` — 13 tests (classification, single-layer fallback, two-layer pipeline, state transitions, augmentation error propagation, backward compat)

**Files Modified:**
- `main/api/lims_router.py` — Rewrote extract endpoint, added classify/template endpoints
- `main/src/lims/job_store.py` — Added CLASSIFYING→EXTRACTING and EXTRACTING→PENDING_REVIEW transitions
- `main/tests/lims/test_lims_router.py` — Updated tests for new pipeline-based endpoints

**What was Done:**
- Created focused_extractor.py: builds reduced schema per test type
- Created merger.py: merges Template + Variable + Augmented layers with provenance
- Created pipeline.py: TwoLayerPipeline orchestrator
- Rewrote lims_router.py extract endpoint; added /classify and /template/{type} endpoints

---

### Task L15 — Frontend: Provenance Badges, Classification & Pipeline Workflow UI

**Phase:** 8f (Frontend) | **Dependencies:** L14
**PRP Task File:** `PRPs/tasks/L15-frontend-provenance-workflow-transformation.md`
**Status:** NOT STARTED

**What to Do:**
- Create ProvenanceBadge, ClassificationPanel, TemplatePreview, MergeConflictPanel, PipelineStageDetail components
- Update LIMSStepIndicator to 6 stages
- Update MDAViewer with provenance badges
- Rewrite lims.tsx for 8-state workflow

---

### Task L16 — Validation: E2E Tests & Backward Compatibility

**Phase:** 8g (Validation) | **Dependencies:** L14, L15
**PRP Task File:** `PRPs/tasks/L16-two-layer-pipeline-validation-e2e.md`
**Status:** NOT STARTED

**What to Do:**
- Create test_provenance.py, test_templates.py, test_classifier.py, test_merger.py, test_pipeline.py, test_standards_loader.py
- Verify AND_ACS_DYE backward compatibility
- Classification accuracy >90% on demo PDFs
- Template coverage comparison against ground truth XLSX
- Full E2E per test type

---

### Task L8 — RAG Optimization: Hybrid Search, Smart Chunking & Reranking (DEPRIORITIZED — after Phase 8)

**Phase:** 7 (Optimization) | **Dependencies:** Phase 6 gate passed
**PRP Task File:** `PRPs/tasks/L8-rag-hybrid-chunking-reranking.md`

**What to Do:**
- Create `main/src/lims/chunking.py` for sheet-level markdown table chunks + workbook summary (~5 chunks per XLSX vs 1)
- Replace whole-workbook chunking in `rag_loader.py` with hybrid chunking
- Add BM25 keyword scoring + Reciprocal Rank Fusion for hybrid semantic+keyword search
- Add Cohere Rerank v3 post-retrieval reranking (`llama-index-postprocessor-cohere-rerank`)
- Update `scripts/populate_lims_chroma.py` for new chunking (~125 chunks total)

**Testing Strategy:**
- ChromaDB re-seeded with hybrid chunks
- Hybrid search returns more relevant results than embedding-only
- Cohere reranking improves precision
- Full pipeline test: extract -> RAG -> generate with improved context

---

### Task L9 — Ground Truth Evaluation: Accuracy Scoring (DEPRIORITIZED — after Phase 8)

**Phase:** 7 (Optimization) | **Dependencies:** L7, L8
**PRP Task File:** `PRPs/tasks/L9-ground-truth-evaluation.md`

**What to Do:**
- Create `main/src/lims/evaluator.py` to parse 16 ground truth XLSX files and compare against AI-generated MDA templates
- Create `scripts/run_evaluation.py` for batch evaluation with score table output
- Per-sheet accuracy metrics: Analysis (10%), Component (40%), CalcVariable (25%), Calculation (25%)
- Establish baseline accuracy scores before/after L7+L8 optimizations

**Testing Strategy:**
- Ground truth parser reads all 16 LabWare XLSX files
- Batch evaluation completes for 5+ PDF+XLSX pairs
- Baseline vs optimized scores documented for thesis

---

## 11. Task Dependency Graph

```
Phase 1: PDF Extraction Backend — DONE
  (pdf_extractor.py, extraction_schema.py, mda_schema.py, config.py, lims_router.py, lims.tsx)

Phase 2: Extraction Testing
  L2.1 (local test) ──> L2.2 (docker test)
  L2.1 ──> L2.3 (pytest suite)
                         │
  ═══════════════════ GATE 2 ═══════════════════
                         │
Phase 3: Extraction UI
  L3.1 (MDA viewer) ──> L3.2 (wire to lims.tsx) ──> L3.3 (progress indicators)
                         │
  ═══════════════════ GATE 3 ═══════════════════
                         │
Phase 4: Workflow + HITL + Export
  L4.1 (ChromaDB RAG) ──> L4.2 (MDA workflow) ──> L4.3 (chat agent)
                                                        │
  L4.5 (XLSX export) <── L4.2                    L4.4 (mandatory HITL) <── L4.3
                    │                                   │
                    └──────────── L4.6 (router endpoints) <──┘
                         │
  ═══════════════════ GATE 4 ═══════════════════
                         │
Phase 5: Full Pipeline Testing
  L5.1 (local e2e) ──> L5.2 (docker e2e)
  L5.1 ──> L5.3 (thesis preservation)
                         │
  ═══════════════════ GATE 5 ═══════════════════
                         │
Phase 6: Full HITL UI
  L6.1 (chat UI) ──> L6.2 (HITL review flow) ──> L6.4 (export button)
  L6.1 + L3.1 ──> L6.3 (real-time MDA updates)
                         │
  ═══════════════════ GATE 6: DEMO-READY ═══════════════════
                         │
Phase 7: Optimization (Quality & RAG)
  L7 (extraction normalization + SDK)
                         │
  ═══════════════════ GATE 7: DATA QUALITY IMPROVED ═══════════════════
                         │
Phase 8: Two-Layer Pipeline Architecture
  L10 (foundation models) ──> L11 (template library)
  L10 ──> L12 (classifier)
  L10 ──> L13 (standards RAG)
  L11 + L12 + L13 ──> L14 (pipeline core)
  L14 ──> L15 (frontend transformation)
  L14 + L15 ──> L16 (validation & E2E)
                         │
  ═══════════════════ GATE 8: TWO-LAYER PIPELINE COMPLETE ═══════════════════
                         │
Phase 9: Optimization (DEPRIORITIZED)
  L8 (RAG: chunking + hybrid + reranking)
  L9 (ground truth evaluation) <── L7, L8
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

**Document Version:** 1.4
**Last Updated:** 2026-02-19
**Next Review:** After Phase 8 completion
**Approved By:** [Pending stakeholder review]

---

*This Production Readiness Plan is a living document and will be updated as the PoC progresses. All changes should be tracked in version control and communicated to stakeholders.*

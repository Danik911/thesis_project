# Project Structure

Core files and directory layout for the pharmaceutical test generation system.

---

## Overview

```
thesis_project/
├── main/                    # Legacy thesis + AI4LIMS
│   ├── api/                 # FastAPI backend (includes BI routers for backwards compat)
│   ├── src/                 # Core logic
│   │   ├── agents/          # Multi-agent system
│   │   ├── adapters/        # Storage adapters
│   │   ├── bi/              # BI modules (legacy copy, still works)
│   │   ├── compliance/      # Regulatory validators
│   │   ├── config/          # Configuration
│   │   └── core/            # Workflow orchestration
│   └── tests/               # Test suite
├── mes-agentic-bi/          # Standalone MES Agentic BI service
│   ├── api/                 # FastAPI app + routers
│   │   ├── app.py           # Standalone entry point
│   │   ├── bi_router.py     # BI data endpoints
│   │   └── bi_voice_router.py
│   ├── src/bi/              # Business logic (copilot, filters, charts, exporters)
│   ├── frontend/            # Next.js (no Clerk, standalone)
│   │   ├── pages/           # agentic-bi, bi-charts
│   │   ├── components/bi/   # Grid, sidebar, chat, charts
│   │   └── lib/apiBase.ts   # API URL utility (no auth)
│   ├── Dockerfile.api
│   ├── Dockerfile.frontend
│   ├── docker-compose.yml
│   └── pyproject.toml       # 14 deps (vs 85 in legacy)
├── frontend/                # Next.js dashboard (thesis + AI4LIMS)
│   ├── components/bi/       # MES Agentic BI UI components (legacy copy)
│   ├── pages/               # Next.js pages
│   └── types/               # Shared TypeScript type definitions
├── aws/                     # AWS infrastructure
│   ├── terraform/           # IaC modules
│   └── scripts/             # Deployment automation
├── docs/                    # Documentation
└── .github/workflows/       # CI/CD pipelines
```

---

## Core Components

### API Layer (`main/api/`)

| File | Purpose |
|------|---------|
| `app.py` | FastAPI application, routes, lifespan |
| `worker.py` | Background job processor |
| `worker_executor.py` | Workflow execution wrapper |
| `models.py` | Pydantic models (JobRecord, JobStatus) |
| `dependencies.py` | FastAPI DI (auth, storage, queue) |
| `observability.py` | LangFuse Cloud client |
| `audit.py` | ALCOA+ audit logger |

### Multi-Agent System (`main/src/agents/`)

```
agents/
├── categorization/          # GAMP-5 categorization
│   ├── agent.py             # Category 1/3/4/5 logic
│   └── confidence_scorer.py # Confidence threshold
├── oq_generator/            # Test generation
│   ├── workflow.py          # Generation orchestration
│   ├── generator_v2.py      # Risk-based generation
│   └── yaml_parser.py       # Output parsing
└── parallel/                # Context agents
    ├── context_provider.py  # ChromaDB RAG
    ├── research_agent.py    # Regulatory research
    └── sme_agent.py         # SME validation
```

### Storage Adapters (`main/src/adapters/`)

| File | Purpose |
|------|---------|
| `storage.py` | Abstract base class |
| `local_adapter.py` | Filesystem (dev) |
| `s3_adapter.py` | S3 (production) |
| `chroma_adapter.py` | ChromaDB vectors |

### Compliance (`main/src/compliance/`)

| File | Purpose |
|------|---------|
| `alcoa_validator.py` | ALCOA+ principles |
| `part11_signatures.py` | 21 CFR Part 11 |
| `rbac_system.py` | Role-based access |

---

## Configuration Files

### Root Level

| File | Purpose |
|------|---------|
| `docker-compose.dev.yml` | 5-service stack (full thesis system) |
| `docker-compose.lims.yml` | AI4LIMS PoC stack (frontend + API only) |
| `mes-agentic-bi/docker-compose.yml` | MES Agentic BI standalone stack (frontend + API, no Clerk) |
| `Dockerfile.api` | API/Worker container |
| `Dockerfile.frontend` | Next.js container |
| `.env.example` | Configuration template |
| `pyproject.toml` | Python dependencies |
| `CLAUDE.md` | Claude Code guidance |

### AWS (`aws/terraform/`)

| File | Purpose |
|------|---------|
| `main.tf` | Core resources |
| `variables.tf` | Configuration |
| `outputs.tf` | Exported values |
| `route53.tf` | DNS configuration |
| `modules/` | ECR, ECS, ALB, CloudFront |
| `task-definition-*.json` | Golden task configs |

---

## Frontend (`frontend/`)

```
frontend/
├── pages/
│   ├── _app.tsx             # ClerkProvider wrapper
│   ├── index.tsx            # Landing page
│   ├── dashboard.tsx        # Job management
│   ├── lims.tsx             # AI4LIMS PoC HITL workflow (641 lines)
│   ├── agentic-bi.tsx       # MES Agentic BI data copilot page
│   ├── sign-in/             # Clerk auth
│   └── sign-up/
├── components/
│   ├── JobList.tsx          # Job table
│   ├── FileUpload.tsx       # URS upload
│   ├── Layout.tsx           # Page wrapper
│   ├── LIMSStepIndicator.tsx # AI4LIMS: 8-stage pipeline progress bar
│   ├── ChatInterface.tsx    # AI4LIMS: MDA refinement chat panel
│   ├── MDAViewer.tsx        # AI4LIMS: MDA display with provenance badges
│   ├── ClassificationPanel.tsx # AI4LIMS: test type classification display
│   ├── ProvenanceBadge.tsx  # AI4LIMS: source provenance indicators
│   ├── MergeConflictPanel.tsx # AI4LIMS: conflict resolution panel
│   ├── PipelineStageDetail.tsx # AI4LIMS: pipeline stage detail view
│   ├── TemplatePreview.tsx  # AI4LIMS: template skeleton preview
│   └── bi/                  # MES Agentic BI components
│       ├── Sidebar.tsx      # Data source + field list sidebar (B1)
│       ├── DataGrid.tsx     # TanStack Table v8 grid + pagination (B1)
│       ├── ChatDrawer.tsx   # Bottom expandable copilot chat drawer with Framer Motion + suggestion chips (B3)
│       ├── ColumnSelector.tsx # Column visibility toggle (B2)
│       └── ExportButtons.tsx  # PDF/Excel export controls (B4)
├── types/
│   ├── lims.ts              # AI4LIMS TypeScript types
│   └── bi.ts                # BI types: BIChatMessage, BIToolCall, BIChatResponse (B3)
├── utils/
│   └── api.ts               # API client
├── middleware.ts            # Route protection
└── next.config.mjs          # Next.js config
```

---

## AI4LIMS PoC (`main/src/lims/`, `docs/project_p/`)

**Branch**: `prjoject_p_protatype` | **Routes**: `/lims/*` | **Compose**: `docker-compose.lims.yml`

### Backend (`main/src/lims/`)

| File | Purpose |
|------|---------|
| `mda_schema.py` | Pydantic schema for MDA extraction (4 core sheets, 9 enums) |
| `pdf_extractor.py` | LlamaExtract integration |
| `focused_extractor.py` | Text extraction (PyMuPDF) + focused schema narrowing |
| `pipeline.py` | TwoLayerPipeline orchestrator (6 stages) |
| `merger.py` | Three-layer merge with provenance tracking; protects template analysis names during overlay; rewrites extraction refs to template names via exact + word-subset matching; template-locked mode rejects unmatched extracted entities for known test types (TestType != OTHER) |
| `classifier.py` | Hybrid test type classifier (filename + keyword + LLM) |
| `test_type.py` | TestType enum and ClassificationResult |
| `provenance.py` | ComponentSource, FieldProvenance, ProvenanceMap |
| `job_store.py` | In-memory job store with state machine |
| `config.py` | LIMS configuration (LIMS_* env vars) |
| `data_normalizer.py` | Post-extraction normalization; infers analysis type from name keywords when extraction returns NULL type |
| `mda_generator.py` | MDA generation workflow |
| `chat_agent.py` | Chat engine for MDA refinement |
| `xlsx_exporter.py` | 4-sheet XLSX generation (openpyxl) |
| `standards_loader.py` | Standards RAG (ChromaDB) |
| `langfuse_tracing.py` | LIMS Langfuse client init, get, flush |
| `templates/` | Curated template library (base, identity, hplc, lod, titration) |
| `prompts/` | LLM prompts (extraction, generation, chat, augmentation) |

### API Routes (`main/api/lims_router.py`)

| Endpoint | Purpose |
|----------|---------|
| `POST /lims/extract` | PDF upload + two-layer pipeline extraction |
| `POST /lims/classify` | Test type classification only |
| `GET /lims/template/{type}` | Get curated template skeleton |
| `GET /lims/status/{job_id}` | Job status + current MDA state |
| `POST /lims/chat` | HITL refinement chat |
| `POST /lims/approve/{job_id}` | Human approval endpoint |
| `GET /lims/export/{job_id}` | XLSX export (APPROVED jobs only) |

### Frontend Components

| Component | Purpose |
|-----------|---------|
| `pages/lims.tsx` | Multi-step HITL workflow (8 stages) |
| `LIMSStepIndicator.tsx` | 8-stage pipeline progress bar |
| `ChatInterface.tsx` | Chat panel for MDA refinement |
| `MDAViewer.tsx` | MDA display with provenance badges |
| `ClassificationPanel.tsx` | Test type classification display (L15) |
| `ProvenanceBadge.tsx` | Source provenance indicators (L15) |
| `MergeConflictPanel.tsx` | Conflict resolution panel (L15) |
| `PipelineStageDetail.tsx` | Pipeline stage detail view (L15) |
| `TemplatePreview.tsx` | Template skeleton preview (L15) |

### Documentation (`docs/project_p/`)

| File | Purpose |
|------|---------|
| `AI4LIMS_PoC_Plan.md` | PoC roadmap and architecture |
| `LIMS-001-pdf-extraction-setup.md` | Task L3: PDF extraction setup |
| `LIMS-002-mda-generation-rag-xlsx.md` | Task L4a: MDA generation with RAG |
| `LIMS-003-chat-agent-hitl-router.md` | Task L4b: Chat agent HITL router |
| `LIMS-004-full-hitl-ui.md` | Task L6: Full HITL UI implementation |
| `LIMS-014-pipeline-core-extractor-merger-orchestrator.md` | Task L14: Pipeline core implementation |
| `LIMS-017-l18-run-validation-remediation-task.md` | L18 run validation remediation (7 phases) |
| `LIMS-020-template-locked-merge-quality-fix.md` | Template-locked merge mode: rejects unmatched extracted entities for known test types; consolidates LIMS-018 and LIMS-019 |
| `archived/LIMS-018-mda-merger-validation-analysis-matching-fixes.md` | Archived — superseded by LIMS-020; merger analysis matching, name protection, ref rewriting fixes |
| `archived/LIMS-019-l18-rerun-checklist-and-audit-protocol.md` | Archived — superseded by LIMS-020; L18 strict rerun checklist and audit protocol |

---

## MES Agentic BI (Standalone) (`mes-agentic-bi/`)

**Branch**: `feature/mes-agentic-bi` | **Routes**: `/bi/*` | **Compose**: `mes-agentic-bi/docker-compose.yml`

Extracted from the monolithic `main/` directory into a self-contained service with its own API, frontend, Dockerfiles, and dependencies.

### Key Files (`mes-agentic-bi/`)

| File | Purpose |
|------|---------|
| `api/app.py` | FastAPI application, CORS, health endpoint, router registration |
| `api/bi_router.py` | Upload, data, filter, chat, chart, export, Snowflake endpoints |
| `api/bi_voice_router.py` | Voice session bootstrap, Polly TTS |
| `src/bi/copilot.py` | LLM copilot (AWS Bedrock Converse API) |
| `src/bi/filter_engine.py` | In-memory DataFrame filter engine |
| `src/bi/chart_engine.py` | Chart data aggregation |
| `src/bi/session_store.py` | In-memory session management |
| `frontend/lib/apiBase.ts` | API base URL utility (no auth) |

### Backend (`mes-agentic-bi/src/bi/`)

| File | Purpose |
|------|---------|
| `__init__.py` | BI package exports |
| `config.py` | BI configuration (`BI_*` env vars, `copilot_model` field) |
| `session_store.py` | In-memory upload session management |
| `data_parser.py` | XLSX/CSV ingestion via pandas (~15K rows) |
| `filter_engine.py` | Server-side pandas filtering engine; exposes `get_filtered_dataframe()` for copilot tool access (B2) |
| `chart_engine.py` | Chart data aggregation for visualizations |
| `copilot.py` | AI copilot agentic loop via AWS Bedrock Converse API: apply_filter, remove_filter, search_data, summarize_column, answer_question (B3) |
| `pdf_exporter.py` | Filtered PDF export with row cap + filter summary (B4) |
| `excel_exporter.py` | Filtered Excel export + "Filters Applied" sheet (B4) |

### API Routes (`mes-agentic-bi/api/bi_router.py`)

| Endpoint | Purpose |
|----------|---------|
| `POST /bi/upload` | XLSX/CSV upload + parse into session |
| `GET /bi/data/{session_id}` | Paginated filtered data rows (B1/B2) |
| `GET /bi/schema/{session_id}` | Column metadata for sidebar (B1) |
| `POST /bi/filter/{session_id}` | Filter updates (B2) |
| `POST /bi/chat/{session_id}` | Copilot agentic loop message (B3) |
| `GET /bi/export/pdf/{session_id}` | Filtered PDF export (B4) |
| `GET /bi/export/excel/{session_id}` | Filtered Excel export (B4) |

### Frontend Components (`mes-agentic-bi/frontend/`)

| Component | Purpose |
|-----------|---------|
| `pages/agentic-bi.tsx` | Main BI page (upload, filters, visibility, data sync, ChatDrawer integration) |
| `components/bi/Sidebar.tsx` | Data source, field list, expandable per-field filters (B2) |
| `components/bi/DataGrid.tsx` | TanStack Table + react-virtual grid + footer counts (B2) |
| `components/bi/ChatDrawer.tsx` | Bottom expandable copilot chat drawer; Framer Motion animation, suggestion chips, filter action badges (B3) |
| `components/bi/ColumnSelector.tsx` | Column visibility toggle (B2) |
| `components/bi/ExportButtons.tsx` | PDF/Excel export controls (B4) |
| `lib/apiBase.ts` | API base URL utility (no Clerk auth) |

### Legacy Copy (`main/src/bi/`, `main/api/bi_router.py`)

The original BI modules remain under `main/` for backwards compatibility. The standalone `mes-agentic-bi/` service is the canonical location going forward.

| File | Purpose |
|------|---------|
| `main/src/bi/copilot.py` | Legacy copilot (OpenRouter, pre-extraction) |
| `main/src/bi/filter_engine.py` | Legacy filter engine |
| `main/src/bi/session_store.py` | Legacy session store |
| `main/api/bi_router.py` | Legacy BI router (still mounted in thesis API) |

---

## Entry Points

### Production (Recommended)

```bash
# Docker Compose (Full Thesis System)
docker-compose -f docker-compose.dev.yml up -d

# Access
# Frontend: http://localhost:3000
# API: http://localhost:8080
```

### AI4LIMS PoC

```bash
# Docker Compose (Minimal Stack)
docker-compose -f docker-compose.lims.yml up -d

# Access
# LIMS UI: http://localhost:3000/lims
# API: http://localhost:8080/lims/*
```

### MES Agentic BI (Standalone)

```bash
# Docker Compose (Standalone Stack)
docker-compose -f mes-agentic-bi/docker-compose.yml up -d

# Local dev (API)
uv run uvicorn mes_agentic_bi.api.app:app --port 8080 --reload

# Local dev (Frontend)
cd mes-agentic-bi/frontend && npm run dev

# Access
# BI UI: http://localhost:3000/agentic-bi
# API: http://localhost:8080/bi/*
```

### AWS

```bash
# Deploy
python aws/scripts/deploy.py

# Access
# https://csvgeneration.com
```

### Direct Python (Legacy)

```bash
# Workflow only (no API)
uv run python main/main.py path/to/urs.md

# API only (no worker)
uv run uvicorn main.api.app:app
```

---

## Documentation (`docs/`)

| File | Purpose |
|------|---------|
| `README.md` | Navigation hub |
| `ARCHITECTURE.md` | System design |
| `AWS_DEPLOYMENT.md` | AWS guide |
| `GITHUB_ACTIONS_DEPLOYMENT.md` | CI/CD pipeline |
| `DOCKER.md` | Local development |
| `PROJECT_STRUCTURE.md` | This file |
| `TROUBLESHOOTING.md` | Common issues |

---

## Testing

```bash
# Unit tests
uv run pytest main/tests/ -v

# Linting
uv run ruff check --fix

# Type checking
uv run mypy .
```

---

## File Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Python modules | lowercase_underscore | `unified_workflow.py` |
| TypeScript | PascalCase | `JobList.tsx` |
| Dockerfiles | `Dockerfile.{service}` | `Dockerfile.api` |
| Docs | UPPERCASE | `ARCHITECTURE.md` |
| Config | lowercase | `.env.local` |

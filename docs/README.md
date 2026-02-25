# Documentation

## Quick Navigation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture, multi-agent design, Docker stack |
| [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md) | AWS ECS/Fargate infrastructure, deployment commands |
| [GITHUB_ACTIONS_DEPLOYMENT.md](GITHUB_ACTIONS_DEPLOYMENT.md) | CI/CD pipeline with OIDC authentication |
| [DOCKER.md](DOCKER.md) | Local Docker Compose development |
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | Core files and directory layout |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Common issues and solutions |
| [AI4LIMS PoC Plan](project_p/AI4LIMS_PoC_Plan.md) | LIMS document extraction prototype (branch: `prjoject_p_protatype`) |

## Getting Started

1. **Local Development**: See [DOCKER.md](DOCKER.md) for Docker Compose quickstart
2. **AWS Deployment**: See [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md) or use `/deploy` command
3. **CI/CD**: Push to `deploy` branch triggers [GitHub Actions](GITHUB_ACTIONS_DEPLOYMENT.md)

## AI4LIMS PoC

AI-powered extraction from pharmaceutical test method PDFs into LabWare LIMS MDA templates.

- **Branch**: `prjoject_p_protatype`
- **Plan**: [AI4LIMS PoC Plan](project_p/AI4LIMS_PoC_Plan.md)
- **Stack**: LlamaExtract + Next.js + FastAPI + ChromaDB
- **Routes**: `/lims/*` (separate from thesis `/jobs/*` routes)

### Implementation Status

Full HITL workflow complete (Tasks L1-L6). Phase 8 (Two-Layer Pipeline Architecture) in progress (L10-L14 complete):

| Phase | Status | Documentation |
|-------|--------|---------------|
| L1: PDF Extraction | Complete | [LIMS-001](project_p/LIMS-001-pdf-extraction-setup.md) |
| L2: MDA Generation + RAG | Complete | [LIMS-002](project_p/LIMS-002-mda-generation-rag-xlsx.md) |
| L3: Chat Agent + HITL Router | Complete | [LIMS-003](project_p/LIMS-003-chat-agent-hitl-router.md) |
| L4: Multi-Step Frontend UI | Complete | [LIMS-004](project_p/LIMS-004-full-hitl-ui.md) |
| L7: Extraction Quality | Complete | — |
| L10: Foundation Models | Complete | — |
| L11: Template Library | Complete | — |
| L12: Hybrid Classifier | Complete | — |
| L13: Standards RAG | Complete | — |
| L14: Pipeline Core | Complete | [LIMS-014](project_p/LIMS-014-pipeline-core-extractor-merger-orchestrator.md) |
| L15: Frontend Provenance UI | In Progress | — |
| L16: E2E Validation | Not Started | — |
| L18: Run Validation Remediation | Complete | [LIMS-017](project_p/LIMS-017-l18-run-validation-remediation-task.md) |
| L18+: Merger Analysis Matching Fixes | Complete | [LIMS-018](project_p/LIMS-018-mda-merger-validation-analysis-matching-fixes.md) |

**Current Workflow**: Upload PDF -> Classify Test Type -> Load Template -> Focused Extract -> Augment from Standards -> Merge with Provenance -> SME Review -> Chat Refinement -> Human Approval -> XLSX Export

**Key Components**:
- `LIMSStepIndicator.tsx` — 8-stage pipeline progress (EXTRACTING -> GENERATING -> PENDING_REVIEW -> APPROVED -> EXPORTED, extended for two-layer pipeline)
- `ChatInterface.tsx` — Interactive chat for MDA refinement with edit badges and suggestion chips
- `MDAViewer.tsx` — Tabbed table viewer for 4 MDA sheets (Analysis, Components, Calc Variables, Calculations) with cell-level highlighting
- `lims.tsx` — Main page with conditional views for each workflow stage
- `pipeline.py` — TwoLayerPipeline orchestrator (Classify -> Template -> Extract -> Augment -> Merge -> Review)
- `focused_extractor.py` — Focused extraction with schema narrowing
- `merger.py` — Three-layer merge with provenance tracking
- `classifier.py` — Hybrid test type classifier
- `templates/` — Curated template library (HPLC, LOD, Titration, Identity)
- `standards_loader.py` — Standards RAG for augmentation
- `ProvenanceBadge.tsx`, `ClassificationPanel.tsx`, `MergeConflictPanel.tsx`, `PipelineStageDetail.tsx`, `TemplatePreview.tsx` — New frontend components (L15, in progress)

**Local Testing**:
```bash
# Backend
uv run uvicorn main.api.app:app --port 8080

# Frontend
cd main/frontend && npm run dev

# Access at http://localhost:3000/lims
```

## Live System

| Environment | URL |
|-------------|-----|
| Production | https://csvgeneration.com |
| API Health | https://csvgeneration.com/health |

## MES Agentic BI for PPRS

Data copilot PoC for Plant Performance Reporting System (PPRS).

- **Branch**: `feature/mes-agentic-bi`
- **PRP**: `PRPs/data-copilot-poc.md`
- **Stack**: TanStack Table v8 + AWS Bedrock (Claude Sonnet 4.6) + pandas + fpdf2 + openpyxl
- **Routes**: `/bi/*` (separate from thesis `/jobs/*` and LIMS `/lims/*` routes)

**Current status (B2 validated)**: Upload XLSX/CSV, session-backed parsing, schema sidebar, per-field sidebar filters, column visibility toggle, and virtualized grid rendering.

**Planned next phases**: Bedrock chat copilot (B3), PDF/Excel export (B4), polish/deploy (B5).

**Local Testing**:
```bash
# Backend
uv run uvicorn main.api.app:app --port 8080 --reload

# Frontend
cd main/frontend && npm run dev

# Access
http://localhost:3000/agentic-bi
```

## Issues

Active issues are tracked in [issues/](issues/) directory. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common solutions.

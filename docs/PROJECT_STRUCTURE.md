# Project Structure

Core files and directory layout for the pharmaceutical test generation system.

---

## Overview

```
thesis_project/
├── main/                    # Application code
│   ├── api/                 # FastAPI backend
│   ├── src/                 # Core logic
│   │   ├── agents/          # Multi-agent system
│   │   ├── adapters/        # Storage adapters
│   │   ├── compliance/      # Regulatory validators
│   │   ├── config/          # Configuration
│   │   └── core/            # Workflow orchestration
│   └── tests/               # Test suite
├── frontend/                # Next.js dashboard
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
│   ├── sign-in/             # Clerk auth
│   └── sign-up/
├── components/
│   ├── JobList.tsx          # Job table
│   ├── FileUpload.tsx       # URS upload
│   ├── Layout.tsx           # Page wrapper
│   ├── LIMSStepIndicator.tsx # AI4LIMS: 5-stage pipeline indicator
│   ├── ChatInterface.tsx    # AI4LIMS: MDA refinement chat panel
│   └── MDAViewer.tsx        # AI4LIMS: MDA display with highlighting
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
| `mda_schema.py` | Pydantic schema for MDA extraction |
| `extractor.py` | LlamaExtract integration |
| `chat_service.py` | GPT-5/Opus chat for refinement |
| `rag_service.py` | ChromaDB RAG (`mda_templates` collection) |
| `xlsx_exporter.py` | 4-sheet XLSX generation (openpyxl) |

### API Routes (`main/api/lims_router.py`)

| Endpoint | Purpose |
|----------|---------|
| `/lims/extract-mda` | PDF extraction via LlamaExtract |
| `/lims/chat` | HITL refinement chat |
| `/lims/export` | XLSX export (4 sheets) |

### Frontend Components

| Component | Purpose |
|-----------|---------|
| `pages/lims.tsx` | Multi-step HITL workflow (5 stages) |
| `LIMSStepIndicator.tsx` | Horizontal pipeline progress bar |
| `ChatInterface.tsx` | Chat panel for MDA refinement |
| `MDAViewer.tsx` | MDA display with field highlighting |

### Documentation (`docs/project_p/`)

| File | Purpose |
|------|---------|
| `AI4LIMS_PoC_Plan.md` | PoC roadmap and architecture |
| `LIMS-001-pdf-extraction-setup.md` | Task L3: PDF extraction setup |
| `LIMS-002-mda-generation-rag-xlsx.md` | Task L4a: MDA generation with RAG |
| `LIMS-003-chat-agent-hitl-router.md` | Task L4b: Chat agent HITL router |
| `LIMS-004-full-hitl-ui.md` | Task L6: Full HITL UI implementation |

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

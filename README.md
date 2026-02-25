# Pharmaceutical Test Generation System

Multi-agent LLM system for automated OQ (Operational Qualification) test generation with GAMP-5 compliance.

**Live:** https://csvgeneration.com

> **AI4LIMS PoC** (branch: `prjoject_p_protatype`): **Demo-ready** AI-powered extraction from pharmaceutical test method PDFs into structured LabWare LIMS MDA templates with full HITL workflow and two-layer pipeline architecture. Phase 8 in progress (L10-L14 complete): Classify Test Type -> Load Template -> Focused Extract -> Augment from Standards -> Merge with Provenance -> SME Review. See [AI4LIMS PoC Plan](docs/project_p/AI4LIMS_PoC_Plan.md).

> **MES Agentic BI for PPRS** (branch: `feature/mes-agentic-bi`): Data copilot PoC for Plant Performance Reporting System. Upload XLSX/CSV (~15K rows), explore via virtual-scrolling grid with sidebar filters, and chat with an AWS Bedrock copilot (Claude Sonnet 4.6) that applies filters and answers analytical questions via tool use. Export filtered data as PDF/Excel. See [PRP](PRPs/data-copilot-poc.md).

---

## Overview

Automated generation of pharmaceutical test suites from User Requirements Specifications (URS) documents using:
- GAMP-5 categorization (Categories 1, 3, 4, 5)
- ALCOA+ compliant audit trails
- 21 CFR Part 11 electronic records
- LangFuse Cloud observability (EU)

---

## Quick Start

### Prerequisites

- Docker & Docker Compose (WSL2 recommended)
- OpenRouter API key (DeepSeek V3)
- Clerk account (authentication)
- LangFuse Cloud account (EU)

### Local Development

```bash
# Clone and configure
git clone https://github.com/Danik911/thesis_project.git
cd thesis_project
cp .env.example .env.local
# Edit .env.local with API keys

# Start services (from WSL2 terminal)
docker-compose -f docker-compose.dev.yml up -d

# Verify
docker ps  # 4 containers: postgres, localstack, api, worker
curl http://localhost:8080/health

# Access
# Frontend: http://localhost:3000
# API: http://localhost:8080

# AI4LIMS PoC (minimal setup)
docker-compose -f docker-compose.lims.yml up -d
# Frontend: http://localhost:3000/lims

# MES Agentic BI PoC (minimal setup)
docker-compose -f docker-compose.bi.yml up -d
# Frontend: http://localhost:3000/agentic-bi
```

### AWS Deployment

```bash
# Full deployment
python aws/scripts/deploy.py

# Quick redeploy (no Docker builds)
python aws/scripts/redeploy.py

# Check status
python aws/scripts/redeploy.py --status-only
```

---

## Architecture

```
User → Frontend (Next.js) → API (FastAPI) → Job Queue (SQS)
                                              │
                                              ▼
                                           Worker
                                              │
              ┌───────────────────────────────┼───────────────────────────────┐
              │                               │                               │
              ▼                               ▼                               ▼
    GAMP-5 Categorization           Context Provider            OQ Test Generator
         Agent                      (ChromaDB RAG)              (DeepSeek V3)
```

---

## AI4LIMS PoC Workflow

**Status**: Phase 8 In Progress (L10-L14 Complete) | **Branch**: `prjoject_p_protatype`

```
User Uploads PDF -> Classify Test Type (Hybrid: filename + keywords)
                           |
              +------------+------------+
              |                         |
     Known Test Type               TestType.OTHER
     (HPLC/LOD/Titration/ID)      (Single-layer fallback)
              |                         |
              v                         v
     Load Curated Template     LlamaExtract (full)
              |                         |
              v                         v
     Focused Extract            MDA Generation
     (variable fields only)     (OpenRouter LLM)
              |                         |
              v                         |
     Augment from Standards             |
     (ChromaDB RAG + LLM)              |
              |                         |
              v                         |
     Merge with Provenance              |
     (Template + Extracted + Inferred)  |
              |                         |
              +------------+------------+
                           |
                           v
                   SME Review (HITL)
                           |
                           v
                   Human Approval
                           |
                           v
                 XLSX Export (4 sheets)
```

**Key Features**:
- PDF extraction via LlamaExtract API
- RAG-enhanced MDA generation (ChromaDB: `mda_templates` collection)
- Two-layer pipeline: curated templates (~46%) + focused PDF extraction
- Hybrid test type classifier (HPLC, LOD, Titration, Identity, Other)
- Full provenance tracking (Template/Extracted/Inferred/SME_REQUIRED)
- Merge conflict detection and resolution
- Real-time chat interface for data refinement
- Cell-level highlighting for AI-suggested changes
- HITL approval workflow with state machine
- Multi-sheet XLSX export (openpyxl)

**Components**: `TwoLayerPipeline`, `FocusedExtractor`, `Merger`, `Classifier`, `TemplateLibrary`, `LIMSStepIndicator`, `ChatInterface`, `MDAViewer` | **Route**: `/lims` | **Docs**: `docs/project_p/`

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| LLM | DeepSeek V3.1 via OpenRouter |
| Backend | FastAPI + Python 3.12 |
| Frontend | Next.js 14 (Pages Router) |
| Database | PostgreSQL + pgvector (local dev only) |
| Vector Store | ChromaDB (26 regulatory docs) |
| Queue | AWS SQS / LocalStack (dev) |
| Auth | Clerk (EU) |
| Observability | LangFuse Cloud (EU) |
| Infrastructure | Terraform + ECS Fargate |

---

## Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE](docs/ARCHITECTURE.md) | System design, agents, code structure |
| [AWS_DEPLOYMENT](docs/AWS_DEPLOYMENT.md) | AWS ECS/Fargate deployment |
| [GITHUB_ACTIONS](docs/GITHUB_ACTIONS_DEPLOYMENT.md) | CI/CD pipeline |
| [DOCKER](docs/DOCKER.md) | Local development |
| [PROJECT_STRUCTURE](docs/PROJECT_STRUCTURE.md) | File layout |
| [TROUBLESHOOTING](docs/TROUBLESHOOTING.md) | Common issues |
| [AI4LIMS PoC Plan](docs/project_p/AI4LIMS_PoC_Plan.md) | LIMS document extraction prototype |
| [MES Agentic BI PRP](PRPs/data-copilot-poc.md) | PPRS data copilot PoC plan |

---

## Commands

```bash
# Local development (Thesis system)
docker-compose -f docker-compose.dev.yml up -d
docker-compose -f docker-compose.dev.yml logs -f

# AI4LIMS PoC development
docker-compose -f docker-compose.lims.yml up -d
docker-compose -f docker-compose.lims.yml logs -f

# MES Agentic BI development
docker-compose -f docker-compose.bi.yml up -d
docker-compose -f docker-compose.bi.yml logs -f

# Testing
uv run pytest main/tests/ -v
uv run ruff check --fix

# AWS deployment
python aws/scripts/deploy.py          # Full deploy
python aws/scripts/redeploy.py        # Quick update
python aws/scripts/redeploy.py --status-only  # Check status
```

---

## Project Structure

```
thesis_project/
├── main/
│   ├── api/              # FastAPI backend
│   ├── frontend/         # Next.js dashboard
│   └── src/
│       ├── agents/       # Multi-agent system
│       ├── adapters/     # Storage (local/S3)
│       ├── compliance/   # ALCOA+, 21 CFR Part 11
│       ├── lims/         # AI4LIMS PoC (MDA extraction)
│       └── bi/           # MES Agentic BI (data copilot)
├── aws/
│   ├── terraform/        # Infrastructure as Code
│   └── scripts/          # Deploy automation
└── docs/                 # Documentation
```

---

## Security & Compliance

### OWASP LLM Top 10 Mitigations
- Prompt Injection: Structured queries
- Data Poisoning: Isolated environments
- Output Handling: Validation layer
- Access Control: Zero-trust architecture

### Regulatory Alignment
- **GAMP 5**: Risk-based validation
- **21 CFR Part 11**: Electronic signatures & audit trails
- **ALCOA+**: Data integrity principles

---

## License

MIT

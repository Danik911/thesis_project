# Pharmaceutical Test Generation System

Multi-agent LLM system for automated OQ (Operational Qualification) test generation with GAMP-5 compliance.

**Live:** https://csvgeneration.com

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

---

## Commands

```bash
# Local development
docker-compose -f docker-compose.dev.yml up -d
docker-compose -f docker-compose.dev.yml logs -f

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
│   └── src/
│       ├── agents/       # Multi-agent system
│       ├── adapters/     # Storage (local/S3)
│       └── compliance/   # ALCOA+, 21 CFR Part 11
├── frontend/             # Next.js dashboard
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

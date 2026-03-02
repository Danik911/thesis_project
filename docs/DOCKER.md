# Docker Development & Architecture Guide

**Last Updated:** 2026-02-26
**Infrastructure:** Docker Compose Multi-Service Stack

Local development using Docker Compose 5-service stack with production-ready patterns.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture Overview](#architecture-overview)
3. [Service Specifications](#service-specifications)
4. [Networking](#networking)
5. [Volume Management](#volume-management)
6. [Commands](#commands)
7. [Environment Variables](#environment-variables)
8. [Development Workflow](#development-workflow)
9. [Health Checks](#health-checks)
10. [Troubleshooting](#troubleshooting)
11. [AWS Migration Path](#aws-migration-path)

---

## Quick Start

```bash
# Navigate to project (WSL)
cd /mnt/c/Users/anteb/Desktop/Courses/Projects/thesis_project

# Configure environment
cp .env.example .env.local
# Edit .env.local with API keys

# Start stack
docker-compose -f docker-compose.dev.yml up -d

# Verify health
docker ps
curl http://localhost:8080/health

# Access
# Frontend: http://localhost:3000
# API: http://localhost:8080
```

---

## Architecture Overview

### System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Docker Host (Windows 11)                    │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                     pharma-dev Network (Bridge)               │   │
│  │                                                               │   │
│  │  ┌────────────────┐         ┌────────────────┐               │   │
│  │  │   Frontend     │◄────────┤   Browser      │               │   │
│  │  │  (Next.js)     │         │  localhost:3000│               │   │
│  │  │  Port: 3000    │         └────────────────┘               │   │
│  │  └───────┬────────┘                                          │   │
│  │          │ HTTP                                              │   │
│  │          ▼                                                   │   │
│  │  ┌────────────────┐         ┌────────────────┐               │   │
│  │  │   API          │◄────────┤   cURL/Postman │               │   │
│  │  │  (FastAPI)     │         │  localhost:8080│               │   │
│  │  │  Port: 8080    │         └────────────────┘               │   │
│  │  └───────┬────────┘                                          │   │
│  │          │                                                   │   │
│  │          │ PostgreSQL                                        │   │
│  │          ▼                                                   │   │
│  │  ┌────────────────┐         ┌────────────────┐               │   │
│  │  │   Postgres     │         │   Worker       │               │   │
│  │  │  (pgvector)    │◄────────┤  (Background)  │               │   │
│  │  │  Port: 5432    │         │  No ports      │               │   │
│  │  └────────────────┘         └───────┬────────┘               │   │
│  │                                     │                        │   │
│  │                                     │ SQS Polling            │   │
│  │                                     ▼                        │   │
│  │                            ┌────────────────┐                │   │
│  │                            │  LocalStack    │                │   │
│  │                            │  (SQS Mock)    │                │   │
│  │                            │  Port: 4566    │                │   │
│  │                            └────────────────┘                │   │
│  │                                                               │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                     Docker Volumes (Persistent)               │   │
│  │                                                               │   │
│  │  postgres-data   │  chroma-data   │  output-data              │   │
│  │  (Job metadata)  │  (26 reg docs) │  (Test suites)            │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                     External Services (Cloud)                 │   │
│  │                                                               │   │
│  │  LangFuse Cloud (EU)  │  OpenRouter API  │  Clerk Auth (EU)   │   │
│  │  Trace storage        │  DeepSeek V3     │  JWT tokens        │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Communication Flow

```
User → Frontend (3000) → API (8080) → PostgreSQL (5432)
                            ↓
                          Enqueue → LocalStack SQS (4566)
                                        ↓
                                     Worker polls SQS
                                        ↓
                    Execute Workflow → ChromaDB (volume)
                                        ↓
                                    LangFuse Cloud (EU)
                                        ↓
                                    Update PostgreSQL
                                        ↓
                                    Write output (volume)
                                        ↓
Frontend polls API → GET /jobs/{id} → Return status
```

### Key Metrics

| Metric | Value |
|--------|-------|
| Services | 5 (postgres, localstack, api, worker, frontend) |
| Startup Time | 30-45 seconds (all services healthy) |
| Development Iteration | 5 seconds (restart only, no rebuild) |
| Full Rebuild | 5-10 minutes (when changing dependencies) |

---

## Service Specifications

| Service | Image | Port | Purpose | Health Check |
|---------|-------|------|---------|--------------|
| postgres | ankane/pgvector:v0.8.1 | 5432 | Job metadata, pgvector | `pg_isready -U postgres` |
| localstack | localstack:3.9.0 | 4566 | SQS emulation | service_started |
| api | Dockerfile.api | 8080 | FastAPI backend | `curl -f http://localhost:8080/health` |
| worker | Dockerfile.api | - | Background processor | None (background) |
| frontend | Dockerfile.frontend | 3000 | Next.js dashboard | None |

### PostgreSQL Database

**Purpose:** Job queue metadata storage and user session management

```yaml
postgres:
  image: ankane/pgvector:v0.8.1
  container_name: pharma-postgres-dev
  ports:
    - "5432:5432"
  environment:
    POSTGRES_DB: pharma_tests
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
  volumes:
    - postgres-data:/var/lib/postgresql/data
```

**Database Schema:**
- **jobs** table: job_id, user_id, status, gamp_category, created_at, updated_at
- **pgvector** extension: Vector similarity search (future use)

### LocalStack (SQS Mock)

**Purpose:** AWS SQS queue emulation for local job queue

```yaml
localstack:
  image: localstack/localstack:3.9.0
  container_name: pharma-localstack-dev
  ports:
    - "4566:4566"
  environment:
    SERVICES: sqs
    AWS_DEFAULT_REGION: eu-west-2
```

**Queue:** `pharma-test-generation-queue` (600s visibility timeout)

### FastAPI Backend

**Purpose:** REST API for job submission and status retrieval

**Endpoints:**
- `GET /health` - Health check (ECS Fargate compatible)
- `POST /jobs` - Submit URS file (requires Clerk JWT)
- `GET /jobs/{job_id}` - Get job status and results
- `GET /jobs` - List all jobs (filtered by user_id)

### Background Worker

**Purpose:** Async workflow executor (polls SQS, runs test generation)

**Command:** `python main/api/worker.py`

**Why Separate Service?** Isolates long-running workflows from API requests, prevents request timeouts.

### Next.js Frontend

**Purpose:** User-facing dashboard for job submission and monitoring

**Features:**
- Clerk JWT authentication (EU endpoints)
- Drag-and-drop URS submission
- Real-time status polling
- YAML test suite download
- GAMP category display

---

## Networking

### Bridge Network: `pharma-dev`

All services communicate via Docker bridge network.

**Service DNS Resolution:**
- `postgres:5432` - Accessible from api/worker
- `localstack:4566` - Accessible from api/worker
- `pharma-api-dev:8080` - Accessible from frontend

**Port Mappings (Host → Container):**
- `localhost:3000` → `frontend:3000`
- `localhost:4566` → `localstack:4566`
- `localhost:5432` → `postgres:5432`
- `localhost:8080` → `api:8080`

**Security:** No services exposed to public internet (localhost only)

---

## Volume Management

### Named Volumes (Persistent)

| Volume | Mount | Purpose | Size |
|--------|-------|---------|------|
| postgres-data | /var/lib/postgresql/data | Database files | ~100 MB |
| chroma-data | /app/chroma_db | Vector store (26 docs) | ~500 MB |
| output-data | /app/output | Generated test suites | Variable |
| localstack-data | /var/lib/localstack | SQS state | ~50 MB |

### Bind Mounts (Development)

| Host Path | Container Path | Purpose |
|-----------|----------------|---------|
| ./main | /app/main | Python live reload |
| ./frontend | /app | Next.js hot reload |
| ./main/logs | /app/main/logs:rw | ALCOA+ audit trail |

### Volume Commands

```bash
# List all volumes
docker volume ls

# Backup chroma-data
docker run --rm \
  -v pharma-dev_chroma-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/chroma-backup.tar.gz -C /data .

# Remove all volumes (DANGER)
docker-compose down -v
```

---

## Commands

### Start/Stop

```bash
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# Stop services (keep volumes)
docker-compose -f docker-compose.dev.yml down

# Stop and remove volumes (data loss)
docker-compose -f docker-compose.dev.yml down -v
```

### Logs

```bash
# All services
docker-compose -f docker-compose.dev.yml logs -f

# Specific service
docker-compose -f docker-compose.dev.yml logs -f api

# Last 100 lines
docker-compose -f docker-compose.dev.yml logs --tail=100 worker
```

### Restart

```bash
# Quick restart (no rebuild)
docker-compose -f docker-compose.dev.yml restart api

# Full rebuild
docker-compose -f docker-compose.dev.yml build --no-cache api
docker-compose -f docker-compose.dev.yml up -d api
```

### Debug

```bash
# Container shell
docker exec -it pharma-api-dev sh

# Database access
docker exec -it pharma-postgres-dev psql -U postgres -d pharma_tests

# Check ChromaDB
docker exec -it pharma-api-dev python -c "
import chromadb
client = chromadb.PersistentClient(path='/app/chroma_db')
for c in client.list_collections():
    print(f'{c.name}: {c.count()} docs')
"
```

---

## Environment Variables

### Required (.env.local)

```bash
# LLM (REQUIRED)
OPENROUTER_API_KEY=sk-or-v1-...
OPENAI_API_KEY=sk-or-v1-...  # Same as OPENROUTER

# LangFuse (REQUIRED)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com

# Clerk (REQUIRED)
CLERK_SECRET_KEY=sk_test_...
CLERK_PEM_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----..."
CLERK_ISSUER=https://your-instance.clerk.accounts.dev
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...

# Database (REQUIRED)
POSTGRES_PASSWORD=your_secure_password
```

### Security Best Practices

- Use `.env.local` (gitignored) for secrets
- NEVER commit `.env.local` to Git
- Use `.env.example` as template
- Rotate secrets regularly

---

## Development Workflow

### Fast Iteration (5 seconds)

```bash
# Edit code in ./main/
vim main/src/core/unified_workflow.py

# Restart container (volume mount = live reload)
docker-compose -f docker-compose.dev.yml restart api

# Test immediately
curl http://localhost:8080/health
```

### Full Rebuild (5-10 minutes)

```bash
# After changing pyproject.toml
docker-compose -f docker-compose.dev.yml build --no-cache api worker
docker-compose -f docker-compose.dev.yml up -d
```

---

## Health Checks

### PostgreSQL

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U postgres"]
  interval: 5s
  timeout: 5s
  retries: 5
```

### API

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

**Health Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-09T12:34:56Z",
  "services": {
    "database": "connected",
    "queue": "connected",
    "langfuse": "connected",
    "chromadb": "initialized"
  }
}
```

### Monitoring

```bash
# Check all container health
docker ps --format "table {{.Names}}\t{{.Status}}"

# Expected output:
# pharma-frontend-dev       Up 2 minutes
# pharma-worker-dev         Up 2 minutes
# pharma-api-dev            Up 2 minutes (healthy)
# pharma-localstack-dev     Up 2 minutes
# pharma-postgres-dev       Up 2 minutes (healthy)
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose -f docker-compose.dev.yml logs api

# Common causes:
# - Missing env var: Check .env.local
# - Port conflict: `netstat -ano | findstr :8080`
# - DB not ready: Restart postgres first
```

### Worker Not Processing Jobs

```bash
# Check worker logs
docker-compose -f docker-compose.dev.yml logs worker

# Restart worker
docker-compose -f docker-compose.dev.yml restart worker

# Recreate localstack
docker-compose -f docker-compose.dev.yml restart localstack worker
```

### ChromaDB Empty

```bash
# Check collection status
docker exec -it pharma-api-dev python -c "
import chromadb
client = chromadb.PersistentClient(path='/app/chroma_db')
for c in client.list_collections():
    print(f'{c.name}: {c.count()}')
"
# Expected: 26 documents

# Re-seed if empty
docker exec -it pharma-api-dev python scripts/seed_chroma.py
```

### Volume Permission Errors

```bash
# Use named volumes (not bind mounts)
volumes:
  - output-data:/app/output  # Correct
  # NOT ./output:/app/output
```

### Frontend Not Loading

```bash
# Restart frontend
docker-compose -f docker-compose.dev.yml restart frontend

# If still failing, rebuild
docker-compose -f docker-compose.dev.yml build frontend
docker-compose -f docker-compose.dev.yml up -d frontend

# Check Clerk keys
grep CLERK .env.local
```

### Resource Monitoring

```bash
# Monitor containers
docker stats

# Expected usage:
# postgres:   ~50MB RAM
# localstack: ~200MB RAM
# api:        ~500MB RAM
# worker:     ~1GB RAM (during workflow)
# frontend:   ~200MB RAM
```

---

## MES Agentic BI (Standalone Docker)

MES Agentic BI has been extracted into a self-contained `mes-agentic-bi/` directory with its own Dockerfiles and Compose file. It is completely independent from the thesis `docker-compose.dev.yml` and the AI4LIMS `docker-compose.lims.yml` stacks.

### Quick Start

```bash
cd mes-agentic-bi
cp .env.example .env.local
# Edit .env.local — set OPENROUTER_API_KEY and any BI_* vars

docker compose up -d

# API: http://localhost:8080
# UI:  http://localhost:3000/agentic-bi
```

### Services

| Service | Dockerfile | Port | Purpose |
|---------|-----------|------|---------|
| api | `mes-agentic-bi/Dockerfile.api` | 8080 | FastAPI BI backend (pandas, fpdf2, openpyxl) |
| frontend | `mes-agentic-bi/Dockerfile.frontend` | 3000 | Next.js BI dashboard |

Both services run on the `bi-dev` bridge network defined in `mes-agentic-bi/docker-compose.yml`.

### Dockerfile Notes

- **`Dockerfile.api`**: Multi-stage Python 3.12. No `libpq` / no PostgreSQL dependency. Uses `tini` as PID 1, runs as non-root user.
- **`Dockerfile.frontend`**: 3-stage Node 20 Alpine build (deps → builder → runner). No Clerk build argument — auth is disabled for this PoC.

### Port Conflicts

The BI stack exposes the same host ports as the other stacks (API `8080`, frontend `3000`). Do NOT run the BI stack simultaneously with `docker-compose.dev.yml` (thesis) or `docker-compose.lims.yml` (AI4LIMS).

### Required Environment Variables

```bash
# LLM (REQUIRED)
OPENROUTER_API_KEY=sk-or-v1-...

# BI session limits (optional — defaults shown)
BI_MAX_UPLOAD_SIZE_MB=50
BI_MAX_ROWS=100000
BI_SESSION_TTL_SECONDS=3600
BI_MAX_SESSIONS=20
```

### Commands

```bash
# Start
docker compose -f mes-agentic-bi/docker-compose.yml up -d

# Logs
docker compose -f mes-agentic-bi/docker-compose.yml logs -f

# Stop
docker compose -f mes-agentic-bi/docker-compose.yml down

# Rebuild after dependency changes
docker compose -f mes-agentic-bi/docker-compose.yml build --no-cache
docker compose -f mes-agentic-bi/docker-compose.yml up -d
```

---

## AWS Migration Path

### ECS Fargate Compatibility

Current Docker Compose patterns map directly to AWS:

| Docker Compose | AWS Equivalent |
|----------------|----------------|
| postgres | Not used in production (stateless design) |
| localstack | Amazon SQS |
| api | ECS Fargate (2 vCPU, 4 GB) |
| worker | ECS Fargate (4 vCPU, 8 GB) |
| frontend | ECS Fargate (via CloudFront + ALB) |
| chroma-data | S3 bucket (downloaded at container startup) |
| output-data | S3 bucket |
| pharma-dev network | VPC with private subnets |
| Health checks | ALB target group health checks |

### Production Readiness Checklist

- [x] Health checks implemented (postgres, api)
- [x] Graceful shutdown (lifespan events)
- [x] Environment variable configuration
- [x] Multi-stage Dockerfile (optimized image size)
- [x] Non-root user (appuser UID 1000)
- [x] Secrets management ready (AWS Secrets Manager)
- [x] Volume persistence patterns (S3 migration)
- [x] Observability integrated (LangFuse Cloud)

**No Breaking Changes Required:** Architecture designed for AWS from Day 1.

---

## Related Documentation

- [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md) - Production deployment guide
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues

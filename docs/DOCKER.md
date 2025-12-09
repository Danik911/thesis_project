# Docker Development Guide

Local development using Docker Compose 5-service stack.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     pharma-dev Network                       │
│                                                              │
│  ┌──────────┐   ┌────────────┐   ┌─────┐   ┌────────┐     │
│  │ Postgres │   │ LocalStack │   │ API │   │ Worker │     │
│  │  :5432   │   │   :4566    │   │:8080│   │  (bg)  │     │
│  └──────────┘   └────────────┘   └─────┘   └────────┘     │
│                                      │                      │
│                                      ▼                      │
│                              ┌──────────┐                   │
│                              │ Frontend │                   │
│                              │  :3000   │                   │
│                              └──────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

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

## Services

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| postgres | ankane/pgvector:v0.8.1 | 5432 | Job metadata |
| localstack | localstack:3.9.0 | 4566 | SQS emulation |
| api | Dockerfile.api | 8080 | FastAPI backend |
| worker | Dockerfile.api | - | Background processor |
| frontend | Dockerfile.frontend | 3000 | Next.js dashboard |

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

## Volumes

| Volume | Mount | Purpose |
|--------|-------|---------|
| postgres-data | /var/lib/postgresql/data | Database files |
| chroma-data | /app/chroma_db | Vector store (26 docs) |
| output-data | /app/output | Generated test suites |
| localstack-data | /var/lib/localstack | SQS state |

**Bind mounts (development):**
- `./main` → `/app/main` (live reload)
- `./frontend` → `/app` (hot reload)
- `./main/logs` → `/app/main/logs` (audit trail)

---

## Environment Variables

```bash
# .env.local (required)
OPENROUTER_API_KEY=sk-or-v1-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
CLERK_SECRET_KEY=sk_test_...
CLERK_PEM_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----..."
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
POSTGRES_PASSWORD=your_password
```

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
test: ["CMD-SHELL", "pg_isready -U postgres"]
interval: 5s
timeout: 5s
retries: 5
```

### API
```yaml
test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
interval: 30s
timeout: 10s
retries: 3
start_period: 40s
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose -f docker-compose.dev.yml logs api

# Common causes:
# - Missing env var: Check .env.local
# - Port conflict: Check `netstat -ano | findstr :8080`
# - DB not ready: Restart postgres first
```

### Worker Not Processing Jobs

```bash
# Check worker logs
docker-compose -f docker-compose.dev.yml logs worker

# Restart worker
docker-compose -f docker-compose.dev.yml restart worker

# Recreate localstack (SQS queue issue)
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

# Re-seed if empty
docker exec -it pharma-api-dev python scripts/seed_chroma.py
```

### Volume Permission Errors

```bash
# Use named volumes (not bind mounts) for output
volumes:
  - output-data:/app/output  # Correct
  # NOT ./output:/app/output
```

---

## Resource Usage

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

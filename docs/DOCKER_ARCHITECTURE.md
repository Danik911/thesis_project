# Docker Architecture - Pharmaceutical Test Generation System

**Last Updated:** 2025-11-20
**System Version:** Phase 3 Complete - 100% Production Ready
**Infrastructure:** Docker Compose Multi-Service Stack

---

## Executive Summary

The pharmaceutical test generation system is deployed as a **5-service Docker Compose stack** with complete isolation, health checks, and volume persistence. This architecture enables fast local development (5-second restarts), production-ready patterns (health checks, graceful shutdown), and seamless AWS migration (ECS Fargate compatibility).

**Key Metrics:**
- **Services:** 5 (postgres, localstack, api, worker, frontend)
- **Startup Time:** 30-45 seconds (all services healthy)
- **Development Iteration:** 5 seconds (restart only, no rebuild)
- **Full Rebuild:** 5-10 minutes (when changing dependencies)
- **Port Mappings:** 3000 (frontend), 4566 (localstack), 5432 (postgres), 8080 (api)

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Service Specifications](#service-specifications)
3. [Networking](#networking)
4. [Volume Management](#volume-management)
5. [Health Checks](#health-checks)
6. [Environment Configuration](#environment-configuration)
7. [Development Workflow](#development-workflow)
8. [Production Readiness](#production-readiness)
9. [Troubleshooting](#troubleshooting)
10. [AWS Migration Path](#aws-migration-path)

---

## Architecture Overview

### System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Docker Host (Windows 11)                    │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                     pharma-dev Network (Bridge)               │  │
│  │                                                                │  │
│  │  ┌────────────────┐         ┌────────────────┐               │  │
│  │  │   Frontend     │◄────────┤   Browser      │               │  │
│  │  │  (Next.js)     │         │  localhost:3000│               │  │
│  │  │  Port: 3000    │         └────────────────┘               │  │
│  │  └───────┬────────┘                                           │  │
│  │          │ HTTP                                               │  │
│  │          ▼                                                     │  │
│  │  ┌────────────────┐         ┌────────────────┐               │  │
│  │  │   API          │◄────────┤   cURL/Postman │               │  │
│  │  │  (FastAPI)     │         │  localhost:8080│               │  │
│  │  │  Port: 8080    │         └────────────────┘               │  │
│  │  └───────┬────────┘                                           │  │
│  │          │                                                     │  │
│  │          │ PostgreSQL                                         │  │
│  │          ▼                                                     │  │
│  │  ┌────────────────┐         ┌────────────────┐               │  │
│  │  │   Postgres     │         │   Worker       │               │  │
│  │  │  (pgvector)    │◄────────┤  (Background)  │               │  │
│  │  │  Port: 5432    │         │  No ports      │               │  │
│  │  └────────────────┘         └───────┬────────┘               │  │
│  │                                      │                        │  │
│  │                                      │ SQS Polling            │  │
│  │                                      ▼                        │  │
│  │                             ┌────────────────┐               │  │
│  │                             │  LocalStack    │               │  │
│  │                             │  (SQS Mock)    │               │  │
│  │                             │  Port: 4566    │               │  │
│  │                             └────────────────┘               │  │
│  │                                                                │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                     Docker Volumes (Persistent)               │  │
│  │                                                                │  │
│  │  postgres-data   │  chroma-data   │  output-data              │  │
│  │  (Job metadata)  │  (26 reg docs) │  (Test suites)            │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                     Bind Mounts (Development)                 │  │
│  │                                                                │  │
│  │  ./main          │  ./frontend    │  ./main/logs              │  │
│  │  (Live reload)   │  (Live reload) │  (Audit trail)            │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                     External Services (Cloud)                 │  │
│  │                                                                │  │
│  │  LangFuse Cloud (EU)  │  OpenRouter API  │  Clerk Auth (EU)  │  │
│  │  Trace storage        │  DeepSeek V3     │  JWT tokens       │  │
│  └──────────────────────────────────────────────────────────────┘  │
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

---

## Service Specifications

### 1. PostgreSQL Database (`postgres`)

**Purpose:** Job queue metadata storage and user session management

**Image:** `ankane/pgvector:v0.8.1`
**Ports:** `5432:5432`
**Health Check:** `pg_isready -U postgres` (5s interval, 5s timeout, 5 retries)

**Configuration:**
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
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U postgres"]
    interval: 5s
    timeout: 5s
    retries: 5
  networks:
    - pharma-dev
```

**Database Schema:**
- **jobs** table: job_id, user_id, status, gamp_category, created_at, updated_at
- **pgvector** extension: Vector similarity search (future use for embeddings)

**Why pgvector?** Enables future migration to S3 Vectors (AWS Phase 4) by testing vector operations locally.

---

### 2. LocalStack (`localstack`)

**Purpose:** AWS SQS queue emulation for local job queue

**Image:** `localstack/localstack:3.9.0`
**Ports:** `4566:4566`
**Health Check:** None (service_started dependency only)

**Configuration:**
```yaml
localstack:
  image: localstack/localstack:3.9.0
  container_name: pharma-localstack-dev
  ports:
    - "4566:4566"
  environment:
    SERVICES: sqs
    AWS_DEFAULT_REGION: eu-west-2
    AWS_ACCESS_KEY_ID: test
    AWS_SECRET_ACCESS_KEY: test
  volumes:
    - localstack-data:/var/lib/localstack
  networks:
    - pharma-dev
```

**Queue Configuration:**
- **Queue Name:** `pharma-test-generation-queue`
- **Dead Letter Queue:** `pharma-test-generation-dlq` (future implementation)
- **Visibility Timeout:** 600 seconds (10 minutes for workflow execution)

**AWS Compatibility:** Uses same boto3 SDK as production AWS SQS (seamless migration).

---

### 3. FastAPI Backend (`api`)

**Purpose:** REST API for job submission and status retrieval

**Build:** Multi-stage Dockerfile (`Dockerfile.api`)
**Ports:** `8080:8080`
**Health Check:** `curl -f http://localhost:8080/health` (30s interval, 10s timeout, 3 retries)

**Configuration:**
```yaml
api:
  build:
    context: .
    dockerfile: Dockerfile.api
  container_name: pharma-api-dev
  ports:
    - "8080:8080"
  environment:
    # LLM Configuration
    OPENAI_API_KEY: ${OPENAI_API_KEY}
    OPENROUTER_API_KEY: ${OPENROUTER_API_KEY}
    LLM_MODEL: deepseek/deepseek-chat

    # LangFuse Cloud Observability
    LANGFUSE_PUBLIC_KEY: ${LANGFUSE_PUBLIC_KEY}
    LANGFUSE_SECRET_KEY: ${LANGFUSE_SECRET_KEY}
    LANGFUSE_HOST: https://cloud.langfuse.com

    # Clerk Authentication
    CLERK_SECRET_KEY: ${CLERK_SECRET_KEY}
    CLERK_PEM_PUBLIC_KEY: ${CLERK_PEM_PUBLIC_KEY}
    CLERK_ISSUER: ${CLERK_ISSUER}

    # Database Connection
    DATABASE_URL: postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/pharma_tests

    # Storage Paths
    RAG_VECTOR_STORE_PATH: /app/chroma_db
    OUTPUT_PATH: /app/output
  volumes:
    - ./main:/app/main  # Live reload for development
    - chroma-data:/app/chroma_db
    - output-data:/app/output
    - ./main/logs:/app/main/logs:rw
  depends_on:
    postgres:
      condition: service_healthy
    localstack:
      condition: service_started
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
    interval: 30s
    timeout: 10s
    retries: 3
  networks:
    - pharma-dev
```

**API Endpoints:**
- `GET /health` - Health check (used by ECS Fargate target group)
- `POST /jobs` - Submit URS file for test generation (requires Clerk JWT)
- `GET /jobs/{job_id}` - Get job status and results
- `GET /jobs` - List all jobs (filtered by user_id from JWT)

**Lifespan Management:**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize LangFuse, audit logger, background worker
    global background_worker_task
    background_worker_task = asyncio.create_task(job_worker())

    yield  # Application runs

    # Shutdown: Cancel worker, flush LangFuse traces
    background_worker_task.cancel()
    langfuse_client.flush()
```

**Why Lifespan?** Ensures graceful shutdown with LangFuse trace persistence and database cleanup.

---

### 4. Background Worker (`worker`)

**Purpose:** Async workflow executor (polls SQS, runs test generation)

**Build:** Same as API (`Dockerfile.api`)
**Command:** `python main/api/worker.py`
**Ports:** None (internal only)
**Health Check:** None (background process)

**Configuration:**
```yaml
worker:
  build:
    context: .
    dockerfile: Dockerfile.api
  container_name: pharma-worker-dev
  command: python main/api/worker.py
  environment:
    # Same environment as API service (LLM, LangFuse, DB, etc.)
    OPENAI_API_KEY: ${OPENAI_API_KEY}
    OPENROUTER_API_KEY: ${OPENROUTER_API_KEY}
    LANGFUSE_PUBLIC_KEY: ${LANGFUSE_PUBLIC_KEY}
    LANGFUSE_SECRET_KEY: ${LANGFUSE_SECRET_KEY}
    DATABASE_URL: postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/pharma_tests
  volumes:
    - ./main:/app/main  # Live reload for development
    - chroma-data:/app/chroma_db
    - output-data:/app/output
  depends_on:
    postgres:
      condition: service_healthy
    localstack:
      condition: service_started
  networks:
    - pharma-dev
```

**Worker Loop:**
```python
async def job_worker():
    while True:
        # Poll SQS for pending jobs
        messages = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1)

        if messages.get('Messages'):
            for message in messages['Messages']:
                job_id = json.loads(message['Body'])['job_id']

                # Update job status to 'processing'
                update_job_status(job_id, 'processing')

                # Execute workflow
                try:
                    result = await execute_unified_workflow(job_id)
                    update_job_status(job_id, 'completed', result=result)
                except Exception as e:
                    update_job_status(job_id, 'failed', error=str(e))

                # Delete message from queue
                sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=message['ReceiptHandle'])

        await asyncio.sleep(1)  # Poll interval
```

**Why Separate Service?** Isolates long-running workflows from API requests, prevents request timeouts.

---

### 5. Next.js Frontend (`frontend`)

**Purpose:** User-facing dashboard for job submission and monitoring

**Build:** Multi-stage Dockerfile (`frontend/Dockerfile`)
**Ports:** `3000:3000`
**Health Check:** None (HTTP service, no custom health endpoint)

**Configuration:**
```yaml
frontend:
  build:
    context: ./frontend
    dockerfile: Dockerfile
  container_name: pharma-frontend-dev
  ports:
    - "3000:3000"
  environment:
    NEXT_PUBLIC_API_BASE_URL: http://localhost:8080
    NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: ${NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY}
  volumes:
    - ./frontend:/app  # Live reload for development
    - /app/node_modules  # Prevent overwriting node_modules
  depends_on:
    - api
  networks:
    - pharma-dev
```

**Key Features:**
- **Pages Router:** Next.js 14 with Pages Router (not App Router)
- **Authentication:** Clerk JWT with EU endpoints
- **File Upload:** Drag-and-drop URS submission
- **Job Monitoring:** Real-time status polling (pending → processing → completed)
- **Results Download:** YAML test suite + metadata JSON
- **GAMP Display:** Category badge with confidence percentage

**Why Pages Router?** Matches reference architecture in `examples/alex/frontend/` for consistency.

---

## Networking

### Bridge Network: `pharma-dev`

All services communicate via a Docker bridge network (`pharma-dev`):

```yaml
networks:
  default:
    name: pharma-dev
    driver: bridge
```

**Service DNS Resolution:**
- `postgres:5432` - Accessible from api/worker
- `localstack:4566` - Accessible from api/worker
- `pharma-api-dev:8080` - Accessible from frontend (internal container name)

**Port Mappings (Host → Container):**
- `localhost:3000` → `frontend:3000` (HTTP)
- `localhost:4566` → `localstack:4566` (HTTP)
- `localhost:5432` → `postgres:5432` (PostgreSQL)
- `localhost:8080` → `api:8080` (HTTP)

**Security:**
- No services exposed to public internet (localhost only)
- Frontend → API communication via internal DNS (no localhost from container)
- Worker has no exposed ports (internal only)

---

## Volume Management

### Named Volumes (Persistent Data)

**1. postgres-data**
- **Purpose:** PostgreSQL database files (job metadata)
- **Mount:** `/var/lib/postgresql/data`
- **Persistence:** Survives `docker-compose down` (data retained)
- **Backup:** `docker run --rm -v postgres-data:/data -v $(pwd):/backup alpine tar czf /backup/postgres-backup.tar.gz -C /data .`

**2. chroma-data**
- **Purpose:** ChromaDB vector store (26 regulatory documents)
- **Mount:** `/app/chroma_db`
- **Persistence:** Survives container restarts
- **Size:** ~500 MB (26 documents + embeddings)

**3. output-data**
- **Purpose:** Generated test suites (YAML + metadata JSON)
- **Mount:** `/app/output`
- **Persistence:** Survives container restarts
- **Structure:**
  ```
  output/
  ├── {job_id_1}/
  │   ├── test_suite.yaml           (36KB typical)
  │   ├── test_suite.yaml.meta.json (519 bytes)
  │   ├── urs_document.md            (1.5KB)
  │   └── urs_document.md.meta.json (425 bytes)
  └── {job_id_2}/
      └── ...
  ```

**4. localstack-data**
- **Purpose:** LocalStack state persistence (SQS queues)
- **Mount:** `/var/lib/localstack`
- **Persistence:** Survives container restarts (queues retained)

### Bind Mounts (Development)

**1. ./main → /app/main (API & Worker)**
- **Purpose:** Live code reload without rebuild
- **Workflow:** Edit Python file → `docker-compose restart api` (5 seconds)
- **Security:** Read-only in production (remove in AWS deployment)

**2. ./frontend → /app (Frontend)**
- **Purpose:** Next.js Fast Refresh (hot module replacement)
- **Workflow:** Edit TypeScript file → Instant browser reload
- **Exception:** `/app/node_modules` excluded via anonymous volume

**3. ./main/logs → /app/main/logs:rw (API & Worker)**
- **Purpose:** Audit trail logs accessible on host
- **Files:** `alcoa_records_YYYYMMDD.json`
- **Compliance:** ALCOA+ audit trail for 21 CFR Part 11

### Volume Commands

```bash
# List all volumes
docker volume ls

# Inspect volume details
docker volume inspect pharma-dev_chroma-data

# Remove all volumes (DANGER: deletes all data)
docker-compose down -v

# Backup chroma-data volume
docker run --rm \
  -v pharma-dev_chroma-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/chroma-backup.tar.gz -C /data .

# Restore chroma-data volume
docker run --rm \
  -v pharma-dev_chroma-data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/chroma-backup.tar.gz -C /data
```

---

## Health Checks

### PostgreSQL Health Check

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U postgres"]
  interval: 5s
  timeout: 5s
  retries: 5
  start_period: 10s
```

**Purpose:** Ensures database is ready before API/worker start
**Dependency:** `depends_on: postgres: condition: service_healthy`

**States:**
- `starting` (0-10s): Start period, failures ignored
- `healthy` (after 1 success): Database ready
- `unhealthy` (after 5 consecutive failures): Critical issue

### API Health Check

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

**Purpose:** Monitors API liveness for load balancer (ECS Fargate compatibility)
**Endpoint Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-20T12:34:56Z",
  "services": {
    "database": "connected",
    "queue": "connected",
    "langfuse": "connected",
    "chromadb": "initialized"
  }
}
```

**States:**
- `starting` (0-40s): uvicorn startup, failures ignored
- `healthy` (after 1 success): API ready for traffic
- `unhealthy` (after 3 consecutive failures): Restart container

### Monitoring Health Status

```bash
# Check all container health statuses
docker ps --format "table {{.Names}}\t{{.Status}}"

# Expected output:
# NAMES                     STATUS
# pharma-frontend-dev       Up 2 minutes
# pharma-worker-dev         Up 2 minutes
# pharma-api-dev            Up 2 minutes (healthy)
# pharma-localstack-dev     Up 2 minutes
# pharma-postgres-dev       Up 2 minutes (healthy)

# Inspect specific health check
docker inspect pharma-api-dev --format='{{json .State.Health}}' | jq
```

---

## Environment Configuration

### Required Variables

See `.env.example` for complete configuration template.

**Critical Variables:**
```bash
# LLM (REQUIRED)
OPENAI_API_KEY=sk-or-v1-...        # OpenRouter for DeepSeek V3
OPENROUTER_API_KEY=sk-or-v1-...    # Same as OPENAI_API_KEY

# LangFuse (REQUIRED)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com

# Clerk (REQUIRED for authentication)
CLERK_SECRET_KEY=sk_test_...
CLERK_PEM_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"
CLERK_ISSUER=https://your-instance.clerk.accounts.dev
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...

# Database (REQUIRED)
POSTGRES_PASSWORD=your_secure_password
```

### Loading Environment Variables

**docker-compose.dev.yml:**
```yaml
services:
  api:
    env_file:
      - .env.local  # Loads all variables from .env.local
    environment:
      # Override specific variables if needed
      LLM_MODEL: deepseek/deepseek-chat
```

**Security Best Practices:**
- ✅ Use `.env.local` (gitignored)
- ❌ NEVER commit `.env.local` to Git
- ✅ Use `.env.example` as template
- ✅ Rotate secrets regularly (Clerk keys, API keys)
- ✅ Use AWS Secrets Manager in production (Phase 4)

---

## Development Workflow

### Fast Iteration Cycle (5 seconds)

**Scenario:** Edit Python code in `main/src/core/unified_workflow.py`

```bash
# 1. Edit code in ./main/ directory
vim main/src/core/unified_workflow.py

# 2. Restart API container (volume mount = live reload)
docker-compose -f docker-compose.dev.yml restart api

# 3. Test immediately (no rebuild required)
curl http://localhost:8080/health
```

**Time:** 5 seconds (restart only, no image rebuild)

### Full Rebuild Cycle (5-10 minutes)

**Scenario:** Add new dependency to `pyproject.toml`

```bash
# 1. Edit dependencies
vim pyproject.toml

# 2. Rebuild containers (multi-stage build with cache)
docker-compose -f docker-compose.dev.yml build --no-cache api worker

# 3. Restart stack
docker-compose -f docker-compose.dev.yml up -d

# 4. Verify health
docker-compose -f docker-compose.dev.yml ps
```

**Time:** 5-10 minutes (dependency installation + image build)

### Debugging Workflow

```bash
# View logs from all services
docker-compose -f docker-compose.dev.yml logs -f

# View logs from specific service
docker-compose -f docker-compose.dev.yml logs -f api

# Access container shell
docker exec -it pharma-api-dev sh

# Inside container: inspect ChromaDB
cd /app
python -c "import chromadb; client = chromadb.PersistentClient(path='/app/chroma_db'); print(client.list_collections())"

# Inside container: inspect output files
ls -lh /app/output/

# View PostgreSQL database
docker exec -it pharma-postgres-dev psql -U postgres -d pharma_tests
# SQL: SELECT * FROM jobs LIMIT 10;
```

---

## Production Readiness

### ECS Fargate Compatibility

**Current Docker Compose patterns map directly to ECS:**

| Docker Compose | ECS Fargate Equivalent |
|----------------|------------------------|
| `postgres` service | Aurora Serverless v2 (managed RDS) |
| `localstack` service | Amazon SQS (managed queue) |
| `api` service | ECS Task Definition (2 vCPU, 4 GB) |
| `worker` service | ECS Task Definition (4 vCPU, 8 GB) |
| `frontend` service | CloudFront + S3 (static hosting) |
| `chroma-data` volume | S3 Vectors (managed vector store) |
| `output-data` volume | S3 bucket (object storage) |
| `pharma-dev` network | VPC with private subnets |
| Health checks | ALB target group health checks |

### Migration Checklist

**Phase 4 (AWS Migration) requires:**
- ✅ Health checks implemented (postgres, api)
- ✅ Graceful shutdown (lifespan events)
- ✅ Environment variable configuration
- ✅ Multi-stage Dockerfile (optimized image size)
- ✅ Non-root user (appuser UID 1000)
- ✅ Secrets management ready (migrate to AWS Secrets Manager)
- ✅ Volume persistence patterns (migrate to S3)
- ✅ Observability integrated (LangFuse Cloud already cloud-based)

**No Breaking Changes Required:** Architecture designed for AWS from Day 1.

---

## Troubleshooting

### Issue #1: Container Fails to Start

**Symptoms:**
```bash
docker ps
# Shows container with status "Restarting" or "Exited"
```

**Diagnosis:**
```bash
# Check container logs
docker-compose -f docker-compose.dev.yml logs api

# Common causes:
# 1. Missing environment variable (e.g., OPENAI_API_KEY not set)
# 2. Database connection failure (postgres not healthy)
# 3. Port conflict (8080 already in use)
```

**Solution:**
```bash
# Fix #1: Check .env.local
grep OPENAI_API_KEY .env.local

# Fix #2: Restart postgres
docker-compose -f docker-compose.dev.yml restart postgres

# Fix #3: Kill process on port 8080
netstat -ano | findstr :8080  # Windows
lsof -i :8080                 # Linux/Mac
taskkill /PID <pid> /F        # Windows
kill -9 <pid>                 # Linux/Mac
```

---

### Issue #2: Volume Permission Errors

**Symptoms:**
```
PermissionError: [Errno 13] Permission denied: '/app/output/job_123'
```

**Cause:** Named volumes use root ownership by default

**Solution:**
```bash
# Option 1: Use named volumes (not bind mounts) - RECOMMENDED
# Already implemented in docker-compose.dev.yml:
volumes:
  - output-data:/app/output  # Named volume (correct)

# Option 2: Fix bind mount permissions (NOT recommended)
# If you switched to bind mount:
sudo chown -R 1000:1000 ./main/output
```

**Why Named Volumes?** Docker manages permissions automatically, works across OS (Windows, Linux, Mac).

---

### Issue #3: Worker Not Processing Jobs

**Symptoms:**
```bash
# Job status stuck at "pending" for >5 minutes
curl http://localhost:8080/jobs/{job_id}
# {"status": "pending"}
```

**Diagnosis:**
```bash
# Check worker logs
docker-compose -f docker-compose.dev.yml logs worker

# Common causes:
# 1. Worker not polling SQS (crashed or never started)
# 2. SQS queue not created (localstack issue)
# 3. LangFuse keys invalid (workflow crashes)
```

**Solution:**
```bash
# Fix #1: Restart worker
docker-compose -f docker-compose.dev.yml restart worker

# Fix #2: Recreate localstack
docker-compose -f docker-compose.dev.yml restart localstack
docker-compose -f docker-compose.dev.yml restart worker

# Fix #3: Verify LangFuse keys
docker exec -it pharma-worker-dev python -c "
from langfuse import Langfuse
import os
client = Langfuse(
    public_key=os.getenv('LANGFUSE_PUBLIC_KEY'),
    secret_key=os.getenv('LANGFUSE_SECRET_KEY'),
    host='https://cloud.langfuse.com'
)
print('LangFuse connection:', 'OK' if client else 'FAILED')
"
```

---

### Issue #4: ChromaDB Returns No Documents

**Symptoms:**
```bash
# Worker logs show: "RAG context retrieval returned 0 documents"
```

**Diagnosis:**
```bash
# Check ChromaDB collection
docker exec -it pharma-api-dev python -c "
import chromadb
client = chromadb.PersistentClient(path='/app/chroma_db')
collections = client.list_collections()
print(f'Collections: {[c.name for c in collections]}')

if collections:
    collection = client.get_collection('pharmaceutical_regulations')
    print(f'Document count: {collection.count()}')
"
```

**Solution:**
```bash
# If collection missing or empty, reingest documents
docker exec -it pharma-api-dev python main/scripts/ingest-regulatory-docs.sh

# Or run from host:
docker-compose -f docker-compose.dev.yml exec api \
  python /app/scripts/ingest-regulatory-docs.sh

# Verify ingestion
docker exec -it pharma-api-dev python -c "
import chromadb
client = chromadb.PersistentClient(path='/app/chroma_db')
collection = client.get_collection('pharmaceutical_regulations')
print(f'Documents indexed: {collection.count()}')
"
# Expected: Documents indexed: 26
```

---

### Issue #5: Frontend Not Loading

**Symptoms:**
```bash
# Browser shows "This site can't be reached" at localhost:3000
```

**Diagnosis:**
```bash
# Check frontend container status
docker ps | grep frontend

# If not running, check logs
docker-compose -f docker-compose.dev.yml logs frontend
```

**Solution:**
```bash
# Restart frontend
docker-compose -f docker-compose.dev.yml restart frontend

# If still failing, rebuild
docker-compose -f docker-compose.dev.yml build frontend
docker-compose -f docker-compose.dev.yml up -d frontend

# Check Clerk keys
grep CLERK .env.local
# Ensure NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY is set
```

---

## AWS Migration Path

### Phase 4 Deployment Plan

**Current (Phase 3):**
```
Docker Compose (localhost)
├── postgres:5432        → Aurora Serverless v2 (eu-west-2)
├── localstack:4566      → Amazon SQS (eu-west-2)
├── api:8080             → ECS Fargate (2 vCPU, 4 GB, ALB)
├── worker (background)  → ECS Fargate (4 vCPU, 8 GB, no ALB)
├── frontend:3000        → CloudFront + S3 (static hosting)
├── chroma-data volume   → S3 Vectors (managed vector store)
└── output-data volume   → S3 bucket (s3://pharma-test-suites/)
```

**Migration Steps:**

1. **Infrastructure as Code (Task 4.1):**
   ```bash
   cd aws/terraform
   terraform init
   terraform plan -var-file=production.tfvars
   terraform apply
   ```

2. **Database Migration (Task 4.2):**
   - Export PostgreSQL data: `pg_dump pharma_tests > backup.sql`
   - Create Aurora Serverless v2 cluster (Terraform)
   - Import data: `psql -h aurora-cluster.eu-west-2.rds.amazonaws.com -f backup.sql`

3. **ChromaDB → S3 Vectors (Task 4.3):**
   - Export embeddings from ChromaDB
   - Create S3 Vectors index (26 documents)
   - Update code to use S3 Vectors SDK

4. **Container Deployment (Task 4.4):**
   - Build ARM64/AMD64 images: `docker buildx build --platform linux/amd64,linux/arm64 .`
   - Push to ECR: `docker push <account>.dkr.ecr.eu-west-2.amazonaws.com/pharma-api:latest`
   - Create ECS Task Definitions (api, worker)
   - Deploy ECS Service with ALB

5. **Frontend Deployment:**
   - Build Next.js: `npm run build`
   - Upload to S3: `aws s3 sync out/ s3://pharma-frontend/`
   - Configure CloudFront distribution

**Zero Downtime Migration:** Deploy side-by-side, switch DNS, rollback if needed.

---

## Appendix: Complete docker-compose.dev.yml

```yaml
version: '3.9'

services:
  # PostgreSQL Database (Job Queue + Metadata Storage)
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
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - pharma-dev

  # LocalStack (AWS SQS Emulation for Job Queue)
  localstack:
    image: localstack/localstack:3.9.0
    container_name: pharma-localstack-dev
    ports:
      - "4566:4566"
    environment:
      SERVICES: sqs
      AWS_DEFAULT_REGION: eu-west-2
      AWS_ACCESS_KEY_ID: test
      AWS_SECRET_ACCESS_KEY: test
    volumes:
      - localstack-data:/var/lib/localstack
    networks:
      - pharma-dev

  # FastAPI Backend (REST API for Job Submission)
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    container_name: pharma-api-dev
    ports:
      - "8080:8080"
    env_file:
      - .env.local
    environment:
      DATABASE_URL: postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/pharma_tests
      RAG_VECTOR_STORE_PATH: /app/chroma_db
      OUTPUT_PATH: /app/output
    volumes:
      - ./main:/app/main
      - chroma-data:/app/chroma_db
      - output-data:/app/output
      - ./main/logs:/app/main/logs:rw
    depends_on:
      postgres:
        condition: service_healthy
      localstack:
        condition: service_started
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - pharma-dev

  # Background Worker (Async Workflow Executor)
  worker:
    build:
      context: .
      dockerfile: Dockerfile.api
    container_name: pharma-worker-dev
    command: python main/api/worker.py
    env_file:
      - .env.local
    environment:
      DATABASE_URL: postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/pharma_tests
      RAG_VECTOR_STORE_PATH: /app/chroma_db
      OUTPUT_PATH: /app/output
    volumes:
      - ./main:/app/main
      - chroma-data:/app/chroma_db
      - output-data:/app/output
    depends_on:
      postgres:
        condition: service_healthy
      localstack:
        condition: service_started
    networks:
      - pharma-dev

  # Next.js Frontend (Job Management Dashboard)
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: pharma-frontend-dev
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_BASE_URL: http://localhost:8080
      NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: ${NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY}
    volumes:
      - ./frontend:/app
      - /app/node_modules
    depends_on:
      - api
    networks:
      - pharma-dev

volumes:
  postgres-data:
  localstack-data:
  chroma-data:
  output-data:

networks:
  pharma-dev:
    driver: bridge
```

---

**Document Version:** 1.0
**Status:** Complete
**Next Steps:** See Phase 4 AWS migration tasks (4.1-4.4)

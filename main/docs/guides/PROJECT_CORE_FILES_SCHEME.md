# Project Core Files Scheme

**Last Updated:** 2025-12-05
**System Phase:** Phase 4 - AWS Staging
**Architecture:** ECS Fargate 3-service stack (Frontend, API, Worker) + CloudFront CDN
**Observability:** LangFuse Cloud (EU)
**AWS URL:** https://csvgeneration.com
**Local Dev:** Docker Compose 5-service stack (postgres, localstack, api, worker, frontend)

---

## Purpose

This document defines the **essential production files** required to run the pharmaceutical test generation system. It distinguishes between:

1. **Core files** - Required for production operation
2. **Optional files** - Development utilities, examples, documentation
3. **Deprecated files** - Legacy code to archive/remove

Use this as a reference for:
- Understanding system architecture
- Identifying dependencies
- Cleaning up legacy code
- Onboarding new developers

---

## System Overview

### Architecture

**5-Service Docker Compose Stack:**
```
┌─────────────────────────────────────────────────────────────┐
│                       Docker Compose                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐   ┌────────────┐   ┌─────┐   ┌────────┐     │
│  │ Postgres │   │ LocalStack │   │ API │   │ Worker │     │
│  │  (PG15)  │   │   (SQS)    │   │     │   │        │     │
│  │ pgvector │   │            │   │     │   │        │     │
│  └──────────┘   └────────────┘   └─────┘   └────────┘     │
│       ▲               ▲             │  ▲        │           │
│       │               │             │  │        │           │
│       └───────────────┴─────────────┘  │        │           │
│                                         │        │           │
│                  ┌──────────────────────┘        │           │
│                  │                               │           │
│              ┌───▼────┐                      ┌───▼────┐     │
│              │Frontend│                      │ Chroma │     │
│              │ Next.js│                      │   DB   │     │
│              └────────┘                      └────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Workflow:**
1. User uploads URS via frontend (port 3000)
2. Frontend calls API (port 8080) with Clerk JWT
3. API validates auth, stores URS, enqueues job
4. Worker picks up job, executes UnifiedWorkflow:
   - GAMP-5 categorization
   - Test planning
   - Parallel agent execution (Context, Research, SME)
   - OQ test generation
5. Worker saves test suite, updates job status
6. Frontend polls job status, displays result

---

## Core Infrastructure Files (9 files)

### Docker Compose & Containers

```yaml
docker-compose.dev.yml               # 5-service orchestration
                                     # Services: postgres, localstack, api, worker, frontend
                                     # Networks: pharma-dev (bridge)
                                     # Volumes: postgres-data, localstack-data, chroma-data
                                     # Healthchecks: postgres (pg_isready), api (curl /health)
                                     # Dependencies: api/worker depend on postgres+localstack
                                     #               frontend depends on api

Dockerfile.api                       # FastAPI container (multi-stage)
                                     # Base: python:3.12-slim-bookworm
                                     # Builder stage: Install uv, compile dependencies
                                     # Runtime stage: Copy venv, run as appuser (UID 1000)
                                     # CMD: uvicorn main.api.app:app --host 0.0.0.0 --port 8080
                                     # Healthcheck: curl -f http://localhost:8080/health

Dockerfile.worker                    # Worker container (multi-stage)
                                     # Base: python:3.12-slim-bookworm
                                     # Builder stage: Install uv, compile dependencies
                                     # Runtime stage: Copy venv, run as appuser (UID 1000)
                                     # CMD: python -m main.api.worker
                                     # No healthcheck (no HTTP endpoint)

Dockerfile.frontend                  # Next.js container (multi-stage)
                                     # Base: node:20-alpine
                                     # Builder stage: npm ci, npm run build (standalone output)
                                     # Runtime stage: Copy .next/standalone, run as nextjs
                                     # CMD: node server.js
                                     # ENV: NODE_ENV=production, PORT=3000
```

### Configuration

```bash
.env.example                         # Configuration template
                                     # Required keys:
                                     # - OPENROUTER_API_KEY (DeepSeek V3)
                                     # - LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY (EU)
                                     # - CLERK_SECRET_KEY, CLERK_PEM_PUBLIC_KEY, CLERK_ISSUER
                                     # - NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
                                     # - RAG_VECTOR_STORE_PATH=/app/chroma_db
                                     # - NEXT_PUBLIC_API_BASE_URL=http://localhost:8080

.env.local                           # Development secrets (GITIGNORED)
                                     # Copy from .env.example
                                     # Contains actual API keys
                                     # Loaded by docker-compose.dev.yml
```

### Deployment Scripts

```bash
scripts/postgres-init.sql            # PostgreSQL initialization script
                                     # Creates: pgvector extension, jobs table, rag_documents table
                                     # Runs once on first container startup
                                     # Volume mount: /docker-entrypoint-initdb.d/01-init.sql

scripts/init-localstack.sh           # LocalStack initialization (DEPRECATED - use docker-compose)
                                     # Creates: testgen-jobs queue, testgen-jobs-dlq queue
                                     # Note: Now handled by localstack-init service in docker-compose

scripts/seed_chroma.py               # ChromaDB document ingestion
                                     # Ingests: GAMP-5 docs, regulatory guides (ICH Q9, FDA Part 11)
                                     # Collections: gamp5_docs, regulatory_guides
                                     # Usage: docker exec pharma-api-dev python scripts/seed_chroma.py
```

---

## AWS Infrastructure (`aws/`)

**Purpose:** Production deployment on ECS Fargate with CloudFront CDN.

**→ See [aws/README.md](../../../aws/README.md) for complete deployment guide**

### Terraform Modules (`aws/terraform/`)

| File/Module | Purpose |
|-------------|---------|
| `main.tf` | Core resources (ECS cluster, S3, IAM, SQS, ALB) |
| `variables.tf` | Configuration variables |
| `outputs.tf` | Export endpoints, ARNs |
| `route53.tf` | Route 53 DNS and ACM certificate configuration |
| `csvgeneration.tfvars` | Domain-specific Terraform variables |
| `modules/ecr/` | Container registry for API, Worker, Frontend |
| `modules/ecs-service/` | ECS service + task definitions |
| `modules/cloudfront/` | CDN distribution (HTTPS termination) |
| `modules/route53/` | Route 53 module for DNS records |

### Golden Task Definitions

| File | Purpose | Resources |
|------|---------|-----------|
| `task-definition-api-v19.json` | API container config | 1 vCPU / 2 GB |
| `task-definition-worker-v21.json` | Worker container config | 2 vCPU / 4 GB |
| `task-definition-frontend-v13.json` | Frontend container config | 0.25 vCPU / 0.5 GB |

**Note:** These are the "golden" configs with secrets. Update and run `redeploy.py` for changes.

### Deployment Scripts (`aws/scripts/`)

| Script | Purpose |
|--------|---------|
| `deploy.py` | Full deployment automation |
| `redeploy.py` | Quick task definition updates (no Docker build) |
| `destroy.py` | Infrastructure teardown |
| `1_upload_chroma_to_s3.py` | Upload ChromaDB vectors to S3 |

---

## Core API Layer (7 files)

**Location:** `main/api/`

### FastAPI Application

```python
app.py                               # FastAPI application with lifespan management
                                     # Endpoints:
                                     # - GET /                Root health check
                                     # - GET /health          ECS Fargate healthcheck
                                     # - POST /jobs           Submit URS for processing
                                     # - GET /jobs            List jobs for current user
                                     # - GET /jobs/{job_id}   Get job status
                                     # - GET /jobs/{job_id}/download  Download result YAML
                                     # - GET /jobs/{job_id}/result    Get result as JSON
                                     #
                                     # Lifespan:
                                     # - Startup: Initialize audit logger, LangFuse, job infrastructure
                                     # - Startup: Start background worker task
                                     # - Shutdown: Cancel worker, flush LangFuse traces
                                     #
                                     # CORS: localhost:3000 (development)
                                     # Auth: Clerk JWT via dependencies.py
                                     # Observability: LangFuse @observe decorators
```

### Background Worker

```python
worker.py                            # Background job processor
                                     # Workflow:
                                     # 1. Wait for job_id from asyncio.Queue
                                     # 2. Get job record from repository (with lock)
                                     # 3. Skip if already FAILED (prevent infinite retry)
                                     # 4. Update status to PROCESSING
                                     # 5. Execute workflow with retry logic
                                     # 6. Update status to COMPLETED or FAILED
                                     # 7. Mark queue task done
                                     #
                                     # Retry Logic:
                                     # - Max retries: 3 (configurable via JobRecord.max_retries)
                                     # - Backoff: 1s, 2s, 4s (exponential)
                                     # - Persists retry_count in JobRecord
                                     # - CRITICAL: Checks retry_count at start to prevent infinite loops
                                     #
                                     # Audit: All events logged (start, retry, complete, fail)
                                     # Error Handling: All exceptions caught to prevent worker crash

worker_executor.py                   # Workflow execution wrapper
                                     # Purpose: Isolate UnifiedWorkflow integration from worker logic
                                     # Key functions:
                                     # - WorkflowExecutor: Initializes UnifiedWorkflow once
                                     # - execute_workflow(): Executes workflow with job context
                                     # - read_urs_from_storage(): Loads URS content from storage
                                     #
                                     # Integration:
                                     # - Calls UnifiedWorkflow.run(urs_content)
                                     # - Parses workflow result
                                     # - Returns dict with result_uri, gamp_category, execution_time
```

### Models & Dependencies

```python
models.py                            # Pydantic models
                                     # - JobRecord: Job state (mutable)
                                     #   - Fields: job_id, status, created_at, started_at, completed_at
                                     #   - Fields: urs_filename, urs_storage_key, urs_hash, urs_size_bytes
                                     #   - Fields: gamp_category, result_uri, user_id
                                     #   - Fields: retry_count, max_retries, error_message, error_type
                                     #   - Method: to_response(download_url=None) → JobStatusResponse
                                     #
                                     # - JobStatus: Enum (PENDING, PROCESSING, COMPLETED, FAILED)
                                     # - JobSubmitResponse: POST /jobs response
                                     # - JobStatusResponse: GET /jobs/{job_id} response

dependencies.py                      # FastAPI dependencies (dependency injection)
                                     # - CurrentUserDep: Clerk JWT authentication
                                     #   - Verifies JWT signature with CLERK_PEM_PUBLIC_KEY
                                     #   - Validates issuer (CLERK_ISSUER)
                                     #   - Skips audience validation (session tokens don't have 'aud')
                                     #   - Returns ClerkClaims (sub, email, iat, exp)
                                     #
                                     # - ValidatedFileDep: File upload validation
                                     #   - Max size: 10MB
                                     #   - Allowed types: text/plain, text/markdown, application/octet-stream
                                     #
                                     # - StorageAdapterDep: Storage adapter injection
                                     #   - Returns LocalStorageAdapter (base_path=/app/output)
                                     #   - TODO: Switch based on ENVIRONMENT variable (S3 for production)
                                     #
                                     # - JobQueueDep, JobRepositoryDep, JobLockDep: Job infrastructure
                                     #   - In-memory for development (shared via FastAPI state)
                                     #   - TODO: Replace with SQS + PostgreSQL for production
```

### Observability & Audit

```python
observability.py                     # LangFuse Cloud client
                                     # Initialization:
                                     # - Langfuse(public_key, secret_key, host=EU)
                                     # - Registers LangfuseCallbackHandler with LlamaIndex
                                     # - Enables automatic trace capture via @observe decorators
                                     #
                                     # Shutdown:
                                     # - Flushes pending traces to LangFuse Cloud
                                     #
                                     # Usage: Import initialize_langfuse() in app.py lifespan

audit.py                             # ALCOA+ audit logger
                                     # Log Format: JSON lines (logs/audit/jobs/YYYYMMDD.jsonl)
                                     # Fields: timestamp, job_id, event_type, user_id, status, metadata
                                     # Event Types: submit, start, retry, complete, fail
                                     # ALCOA+ Compliance:
                                     # - Attributable: user_id (Clerk), user_email
                                     # - Legible: Human-readable JSON
                                     # - Contemporaneous: datetime.now(UTC)
                                     # - Original: SHA-256 hash of URS content
                                     # - Accurate: No fallback logic
                                     # - Complete: All job lifecycle events
                                     # - Consistent: Standardized event format
                                     # - Enduring: Append-only log files
                                     # - Available: File-based, mounted to host (bind mount)
```

---

## Core Workflow (1 file)

**Location:** `main/src/core/`

```python
unified_workflow.py                  # Master LlamaIndex workflow orchestrator
                                     # Architecture: Event-driven LlamaIndex 0.12.0+ workflow
                                     # Flow:
                                     # 1. StartEvent(urs_content) → GAMPCategorizationWorkflow
                                     # 2. GAMPCategorizationEvent → PlannerAgentWorkflow
                                     # 3. PlanningEvent → Parallel agent coordination
                                     # 4. AgentResultsEvent → OQGenerationWorkflow
                                     # 5. OQTestSuiteEvent → StopEvent(test_suite)
                                     #
                                     # Features:
                                     # - Human consultation triggers (ConsultationRequiredEvent)
                                     # - Error handling with retry logic
                                     # - LangFuse @observe decorators on all steps
                                     # - ALCOA+ metadata injection
                                     # - Timeout protection (1800s)
                                     #
                                     # Entry Point: UnifiedWorkflow.run(urs_content, user_id)
```

---

## Multi-Agent System (25+ files)

**Location:** `main/src/agents/`

### Categorization Agent

```
categorization/
├── agent.py                         # GAMP-5 categorization logic (Categories 1, 3, 4, 5)
├── confidence_scorer.py             # Confidence scoring system (threshold: 70%)
├── audit_logger.py                  # Categorization audit trail
├── error_handler.py                 # Error handling with retry logic
└── workflow_integration.py          # LlamaIndex workflow integration
```

### OQ Generator Agent

```
oq_generator/
├── workflow.py                      # OQ generation workflow orchestration
├── generator_v2.py                  # V2 test generation logic (risk-based)
├── chunked_generator.py             # Chunked generation for large test suites
├── models.py                        # OQ test case models
├── templates.py                     # Test template definitions
├── events.py                        # LlamaIndex events (OQTestGenerationEvent)
└── yaml_parser.py                   # YAML output parser
```

### Parallel Agents

```
parallel/
├── context_provider.py              # RAG context retrieval agent (ChromaDB)
├── research_agent.py                # Regulatory research agent
├── sme_agent.py                     # Subject matter expert agent
├── agent_factory.py                 # Agent instantiation
└── regulatory_data_sources.py       # GAMP-5, ICH Q9, FDA Part 11 sources
```

---

## Storage & Vector Store Adapters (7 files)

**Location:** `main/src/adapters/`

```python
storage.py                           # Abstract StorageAdapter base class
local_adapter.py                     # Filesystem storage adapter (base: /app/output)
s3_adapter.py                        # S3 storage adapter (AWS migration ready)
chroma_adapter.py                    # ChromaDB vector store adapter
postgres_adapter.py                  # PostgreSQL adapter (pgvector - TODO)
vector_store.py                      # Abstract VectorStoreAdapter base class
```

---

## Compliance & Validation (8 files)

**Location:** `main/src/compliance/`

```python
alcoa_validator.py                   # ALCOA+ validator (9 principles)
part11_signatures.py                 # 21 CFR Part 11 electronic signatures
rbac_system.py                       # Role-based access control
mfa_auth.py                          # Multi-factor authentication
training_system.py                   # User training tracking
validation_framework.py              # Validation lifecycle management
worm_storage.py                      # Write-once-read-many storage
```

---

## Configuration (4 files)

**Location:** `main/src/config/`

```python
llm_config.py                        # LLM provider configuration (OpenRouter, OpenAI)
agent_llm_config.py                  # Agent-specific LLM configurations
chromadb_collections.py              # ChromaDB collection definitions
timeout_config.py                    # Timeout configurations
```

---

## Frontend (Next.js Pages Router)

**Location:** `main/frontend/`

### Pages

```typescript
pages/
├── _app.tsx                         # App wrapper with ClerkProvider
├── _document.tsx                    # Custom document (HTML metadata)
├── index.tsx                        # Home/landing page (public)
├── dashboard.tsx                    # Job dashboard (protected)
├── sign-in/[[...index]].tsx         # Clerk sign-in page
└── sign-up/[[...index]].tsx         # Clerk sign-up page
```

### Components

```typescript
components/
├── JobList.tsx                      # Job list component (table view)
├── JobDetails.tsx                   # Job detail modal
├── FileUpload.tsx                   # URS file upload component (drag-and-drop)
└── Layout.tsx                       # Layout wrapper (header, footer)
```

### Utilities

```typescript
utils/
└── api.ts                           # API client (fetch wrapper with Clerk JWT injection)
```

### Configuration

```typescript
middleware.ts                        # Clerk authentication middleware (protects /dashboard)
next.config.mjs                      # Next.js configuration (standalone output)
package.json                         # Dependencies (next@15.0.3, react@19.0.0, @clerk/nextjs@6.7.2)
```

---

## Entry Points

### Production (Docker Compose - RECOMMENDED)

```bash
# Start all 5 services
docker-compose -f docker-compose.dev.yml up -d

# Services start in dependency order:
# 1. postgres (port 5432)        → Waits for pg_isready healthcheck
# 2. localstack (port 4566)      → Creates SQS queues via init container
# 3. api (port 8080)             → Waits for postgres + localstack
# 4. worker (no port)            → Waits for postgres + localstack
# 5. frontend (port 3000)        → Waits for api

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop services
docker-compose -f docker-compose.dev.yml down
```

### Development (Direct Python - DEPRECATED)

```bash
# DEPRECATED: Use Docker Compose instead
uv run python main/main.py           # Direct workflow execution (no API)
uv run uvicorn main.api.app:app      # API only (no worker)
```

---

## Deprecated Files (ARCHIVE/REMOVE)

### Phoenix Observability (Replaced by LangFuse)

**Status:** Phoenix removed in Phase 2 (Task 2.3). LangFuse Cloud now handles all observability.

**Files to Archive (35+ files):**

```bash
# Phoenix example scripts - ARCHIVE
main/examples/phoenix_categorization_example.py
main/examples/test_phoenix_basic.py
main/examples/test_phoenix_integration.py

# Phoenix export scripts - ARCHIVE
main/scripts/export_all_phoenix_traces.py
main/scripts/export_phoenix_all_spans.py

# Phoenix launch scripts - ARCHIVE
main/launch_phoenix.py               # No local Phoenix server needed
main/setup_phoenix.py                # LangFuse Cloud replaces Phoenix setup

# Phoenix tests - ARCHIVE
main/tests/archived_root_scripts/test_phoenix_handlers.py
main/tests/integration/phoenix/*.py  # 8 test files
```

**Replacement:** All observability now handled by:
- `main/api/observability.py` (LangFuse Cloud client)
- `@observe` decorators from `langfuse` package
- LangFuse Dashboard: https://cloud.langfuse.com (EU)

### Root-Level Test Scripts

**Status:** Moved to `main/tests/archived_root_scripts/` in Phase 2.

**Files Already Archived (15 files):**

```bash
main/tests/archived_root_scripts/
├── focused_oss_test.py
├── minimal_api_debug.py
├── run_complete_oss_workflow.py
└── ... (12 more files)

# Reason: These scripts bypass API layer and don't reflect production architecture
```

---

## File Naming Conventions

### Python Modules
```python
lowercase_with_underscores.py        # All Python modules
__init__.py                          # Package initialization
```

### Configuration Files
```bash
.env.example                         # Configuration template (committed to Git)
.env.local                           # Local secrets (GITIGNORED)
docker-compose.dev.yml               # Docker Compose development stack
```

### Dockerfiles
```bash
Dockerfile.api                       # FastAPI container
Dockerfile.worker                    # Worker container
Dockerfile.frontend                  # Next.js container
```

### Documentation
```markdown
UPPERCASE_WITH_UNDERSCORES.md        # Top-level docs (README, CLAUDE)
lowercase-with-dashes.md             # Sub-level docs (task files, guides)
```

---

## Verification Checklist

### Infrastructure
- [ ] `docker-compose.dev.yml` exists and defines 5 services
- [ ] `Dockerfile.api`, `Dockerfile.worker`, `Dockerfile.frontend` exist
- [ ] `.env.example` exists with all required keys
- [ ] `.env.local` exists with actual API keys (gitignored)

### API Layer
- [ ] `main/api/app.py` exists with FastAPI routes
- [ ] `main/api/worker.py` exists with worker loop
- [ ] `main/api/observability.py` exists with LangFuse client
- [ ] `main/api/audit.py` exists with ALCOA+ logger

### Core Workflow
- [ ] `main/src/core/unified_workflow.py` exists

### Multi-Agent System
- [ ] `main/src/agents/categorization/agent.py` exists
- [ ] `main/src/agents/oq_generator/workflow.py` exists
- [ ] `main/src/agents/parallel/context_provider.py` exists

### Storage Adapters
- [ ] `main/src/adapters/storage.py` exists (abstract base)
- [ ] `main/src/adapters/local_adapter.py` exists
- [ ] `main/src/adapters/s3_adapter.py` exists

### Frontend
- [ ] `main/frontend/pages/_app.tsx` exists
- [ ] `main/frontend/pages/dashboard.tsx` exists
- [ ] `main/frontend/middleware.ts` exists

---

## Maintenance Guidelines

### When to Update This Document

Update this document when:
1. Adding new core files (e.g., new agents, adapters)
2. Removing deprecated files (archive or delete)
3. Changing system architecture (e.g., SQS migration)
4. Completing AWS migration phases

### How to Update

1. Read current project structure
2. Identify new/changed/removed files
3. Update relevant sections
4. Update "Last Updated" timestamp
5. Commit with message: `docs: Update PROJECT_CORE_FILES_SCHEME.md`

---

## Related Documentation

- **CLAUDE.md** - Project instructions for Claude Code
- **main/docs/guides/QUICK_START_GUIDE.md** - Getting started
- **PRPs/aws-migration-updated.md** - AWS migration plan
- **main/docs/compliance/** - GAMP-5, ALCOA+, 21 CFR Part 11

---

**Last Updated:** 2025-11-20
**Maintainer:** Thesis Project Team
**Review Frequency:** After each PRP task completion

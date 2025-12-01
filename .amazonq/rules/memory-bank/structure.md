# Project Structure

## Directory Organization

```
thesis_project/
├── main/                           # Main application code
│   ├── src/                        # Source code
│   │   ├── core/                   # Workflow orchestration
│   │   ├── agents/                 # Multi-agent components
│   │   ├── compliance/             # Regulatory compliance
│   │   ├── validation/             # Statistical & audit validation
│   │   ├── monitoring/             # Observability
│   │   ├── security/               # OWASP LLM controls
│   │   ├── adapters/               # Storage and vector store abstractions
│   │   └── llms/                   # LLM provider integrations
│   ├── api/                        # FastAPI backend
│   ├── frontend/                   # Next.js web UI
│   ├── tests/                      # Test suites
│   ├── scripts/                    # Utility scripts
│   ├── output/                     # Generated test outputs
│   └── chroma_db/                  # ChromaDB vector store
├── THESIS_EVIDENCE_PACKAGE/       # Complete thesis proof
│   ├── 00_URS/                    # User Requirements (30+ docs)
│   ├── 01_TEST_EXECUTION_EVIDENCE/ # Test execution data (517 traces)
│   ├── 02_STATISTICAL_ANALYSIS/   # Statistical validation
│   ├── 03_COMPLIANCE_DOCUMENTATION/ # GAMP-5, OWASP compliance
│   ├── 04_PERFORMANCE_METRICS/    # Cost & performance analysis
│   ├── 05_THESIS_DOCUMENTS/       # Academic documentation
│   ├── 06_SOURCE_CODE_EVIDENCE/   # Implementation artifacts
│   └── 07_UNIFIED_ANALYSIS/       # Visualizations & reports
├── PRPs/                          # Production Readiness Plans
│   └── tasks/                     # 23 tasks across 6 phases (0.1-5.3)
├── .claude/                       # Claude Code commands
│   ├── agents/                    # Multi-agent orchestration
│   ├── commands/                  # Custom commands (prp, review)
│   └── state/                     # Git-tracked state files
├── aws/                           # AWS deployment infrastructure
│   ├── terraform/                 # Terraform modules
│   ├── iam-policies/              # IAM policy documents
│   └── lambda/                    # Lambda functions
├── scripts/                       # Docker and deployment scripts
├── datasets/                      # URS corpora and metrics
├── compliance/                    # Compliance artifacts
├── docs/                          # Documentation
└── docker-compose.dev.yml         # 5-service development stack
```

## Core Components

### 1. Workflow Orchestration (`main/src/core/`)
- **unified_workflow.py**: Master orchestrator using LlamaIndex Workflow
  - Coordinates categorization → parallel agents → generation → validation
  - Implements event-driven architecture with typed events
  - Integrates LangFuse tracing via @observe decorators

### 2. Multi-Agent System (`main/src/agents/`)

#### Categorization Agent (`agents/categorization/`)
- **agent.py**: GAMP-5 categorization logic
  - Determines software category (3, 4, 5) per ISPE GAMP-5
  - Confidence scoring with 0.4 threshold
  - No fallback policy - explicit error handling

#### Parallel Agents (`agents/parallel/`)
- **context_provider_agent.py**: ChromaDB retrieval (26 regulatory docs)
- **research_agent.py**: External regulatory source augmentation
- **sme_agent.py**: Technical and compliance sanity checks

#### OQ Generator (`agents/oq_generator/`)
- **agent.py**: Test suite generation with DeepSeek V3
  - Produces YAML test suites (avg 13.7 tests per document)
  - Robust JSON parsing with json-repair library
  - Category-specific test count ranges (3: 5-10, 4: 10-20, 5: 25-30)

### 3. Compliance & Validation (`main/src/compliance/`, `main/src/validation/`)
- **alcoa_validator.py**: ALCOA+ data integrity validation
- **audit_coverage_validator.py**: Traceability matrix generation
- **validation_framework.py**: Regulatory compliance checks

### 4. Security (`main/src/security/`)
- **output_scanner.py**: OWASP LLM Top 10 scanning
- **owasp_test_scenarios.py**: Security test case generation

### 5. Observability (`main/src/monitoring/`)
- **trace_config.py**: LangFuse Cloud configuration
- **custom_span_exporter.py**: OpenTelemetry span export

### 6. Storage Abstractions (`main/src/adapters/`)
- **storage.py**: Abstract storage interface
- **local_adapter.py**: Local filesystem storage (development)
- **s3_adapter.py**: AWS S3 storage (production)
- **vector_store.py**: Abstract vector store interface
- **chroma_adapter.py**: ChromaDB implementation
- **postgres_adapter.py**: pgvector implementation (planned)

### 7. LLM Integrations (`main/src/llms/`)
- **openrouter_client.py**: OpenRouter API client (DeepSeek V3)
- **openai_client.py**: OpenAI API client (embeddings)

## API Layer (`main/api/`)

### FastAPI Application
- **app.py**: FastAPI application with lifespan management
  - Endpoints: POST /jobs, GET /jobs, GET /jobs/{job_id}, GET /jobs/{job_id}/download
  - Clerk JWT authentication via dependencies.py
  - LangFuse @observe decorators for endpoint tracing
  - CORS enabled for localhost:3000 (development)

### Background Worker
- **worker.py**: Background job processor
  - Polls asyncio.Queue for job_id
  - Executes UnifiedWorkflow with retry logic
  - Updates job status in PostgreSQL (PROCESSING → COMPLETED/FAILED)

### Data Models
- **models.py**: Pydantic models for API requests/responses
  - JobSubmitRequest, JobStatusResponse, JobListResponse
  - GAMP5Category enum (CATEGORY_3, CATEGORY_4, CATEGORY_5)

### Job Repository
- **job_repository.py**: PostgreSQL data access layer
  - CRUD operations for jobs table
  - Async SQLAlchemy with asyncpg driver

## Frontend (`main/frontend/`)

### Next.js Application
- **pages/**: Page components (index, generate, jobs, results)
- **components/**: Reusable UI components (FileUpload, JobStatus, TestSuiteViewer)
- **context/**: React context providers (AuthContext, JobContext)
- **hooks/**: Custom React hooks (useJobs, useAuth)
- **lib/**: API client and utilities
- **middleware.ts**: Clerk authentication middleware

## Docker Infrastructure

### 5-Service Stack (`docker-compose.dev.yml`)
1. **postgres**: PostgreSQL 15 with pgvector extension
   - Jobs table, rag_documents table
   - Healthcheck: pg_isready
2. **localstack**: LocalStack 3.x (SQS, S3 mocks)
   - testgen-jobs queue, testgen-jobs-dlq queue
3. **api**: FastAPI application (port 8080)
   - Depends on postgres (healthy) + localstack (started)
   - Volume mounts: ./main, ./main/output, chroma-data
4. **worker**: Background job processor
   - Depends on postgres (healthy) + localstack (started)
   - Shared volumes with api for storage consistency
5. **frontend**: Next.js UI (port 3000)
   - Depends on api (started)
   - Volume mounts: ./main/frontend, /app/node_modules, /app/.next

### Dockerfiles
- **Dockerfile.api**: Multi-stage build (python:3.12-slim-bookworm)
  - Builder stage: Install uv, compile dependencies
  - Runtime stage: Copy venv, run as appuser (UID 1000)
- **Dockerfile.worker**: Multi-stage build (python:3.12-slim-bookworm)
  - Builder stage: Install uv, compile dependencies
  - Runtime stage: Copy venv, run as appuser (UID 1000)
- **Dockerfile.frontend**: Multi-stage build (node:20-alpine)
  - Builder stage: npm ci, npm run build (standalone output)
  - Runtime stage: Copy .next/standalone, run as nextjs

## Thesis Evidence Package

### Evidence Categories
1. **00_URS**: 30 URS documents across 3 corpora (56.7%, 26.7%, 16.7%)
2. **01_TEST_EXECUTION_EVIDENCE**: 517 traces from corpus_1, corpus_2, corpus_3
3. **02_STATISTICAL_ANALYSIS**: Cohen's Kappa, confidence intervals, power analysis
4. **03_COMPLIANCE_DOCUMENTATION**: GAMP-5 mapping, OWASP mitigation, ALCOA+ validation
5. **04_PERFORMANCE_METRICS**: Cost reduction analysis, timing benchmarks
6. **05_THESIS_DOCUMENTS**: Academic papers, validation reports
7. **06_SOURCE_CODE_EVIDENCE**: Implementation artifacts, architecture diagrams
8. **07_UNIFIED_ANALYSIS**: Consolidated visualizations, final reports

## Architectural Patterns

### Event-Driven Workflow
- LlamaIndex Workflow with typed events (CategorizationEvent, ParallelAgentsEvent, GenerationEvent)
- Async/await throughout for non-blocking I/O
- Event handlers decorated with @step for workflow orchestration

### Dependency Injection
- Abstract interfaces (StorageAdapter, VectorStoreAdapter)
- Concrete implementations injected at runtime (LocalStorageAdapter, ChromaAdapter)
- Enables testing with mock implementations

### Observer Pattern
- LangFuse @observe decorators for automatic trace capture
- OpenTelemetry instrumentation for LlamaIndex, OpenAI, ChromaDB
- Custom span exporters for audit logging

### Repository Pattern
- JobRepository abstracts PostgreSQL access
- Async SQLAlchemy with connection pooling
- Transaction management with context managers

### Multi-Stage Docker Builds
- Builder stage: Compile dependencies with uv
- Runtime stage: Copy venv, minimal base image
- Reduces image size and attack surface

## Configuration Management

### Environment Variables
- **.env.local**: Development secrets (API keys, database URLs)
- **.env.example**: Template with placeholder values
- **.env.development**: Development-specific overrides
- **docker-compose.dev.yml**: Container environment variables

### Configuration Files
- **pyproject.toml**: Python dependencies, build system, tool configuration
- **main/config/oss_models.yaml**: LLM model configurations (DeepSeek V3, GPT-4.1-mini)
- **main/frontend/next.config.mjs**: Next.js configuration
- **main/frontend/tsconfig.json**: TypeScript configuration

## Data Flow

1. **User uploads URS** via frontend (POST /jobs)
2. **API validates auth** (Clerk JWT), stores URS in LocalStorageAdapter
3. **API enqueues job** in asyncio.Queue (in-memory for development)
4. **Worker picks up job**, executes UnifiedWorkflow:
   - GAMP-5 categorization
   - Parallel agent execution (Context, Research, SME)
   - OQ test generation with DeepSeek V3
   - ALCOA+ validation and traceability matrix
5. **Worker saves test suite** to LocalStorageAdapter, updates job status
6. **Frontend polls job status** (GET /jobs/{job_id}), displays result
7. **User downloads test suite** (GET /jobs/{job_id}/download)

## Testing Strategy

### Test Levels
1. **Unit Tests** (`main/tests/unit/`): Individual component testing
2. **Integration Tests** (`main/tests/integration/`): Multi-component workflows
3. **Compliance Tests** (`main/tests/compliance/`): Regulatory validation
4. **End-to-End Tests** (`scripts/test-e2e-local.sh`): Full workflow validation

### Test Infrastructure
- **pytest**: Test runner with async support (pytest-asyncio)
- **pytest-mock**: Mocking framework for external dependencies
- **freezegun**: Time-based test determinism
- **pytest-cov**: Code coverage reporting

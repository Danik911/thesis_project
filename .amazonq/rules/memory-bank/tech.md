# Technology Stack

## Programming Languages

### Python 3.12+
- **Core Application**: Backend API, workflow orchestration, agents
- **Async/Await**: asyncio, aiofiles, aiohttp for non-blocking I/O
- **Type Hints**: Full type annotations with mypy strict mode

### TypeScript 5.x
- **Frontend**: Next.js 14 application with React 18
- **Type Safety**: Strict TypeScript configuration
- **JSX/TSX**: React components with TypeScript

### SQL
- **PostgreSQL 15**: Relational database with pgvector extension
- **SQLAlchemy**: Async ORM with asyncpg driver

## Core Frameworks & Libraries

### Backend (Python)

#### LlamaIndex Ecosystem
- **llama-index-core** (>=0.12.0): Workflow orchestration, event-driven architecture
- **llama-index-llms-openai** (>=0.3.0): OpenAI LLM integration
- **llama-index-embeddings-openai** (>=0.2.0): Text embeddings for RAG
- **llama-index-vector-stores-chroma** (>=0.3.0): ChromaDB integration
- **llama-index-vector-stores-postgres** (>=0.2.0): pgvector integration
- **llama-index-readers-file** (>=0.2.0): Document parsing (PDF, Markdown)
- **llama-index-readers-web** (>=0.2.0): Web scraping for research agent

#### FastAPI Stack
- **fastapi**: RESTful API framework with automatic OpenAPI docs
- **uvicorn**: ASGI server with async support
- **pydantic** (v2): Data validation and serialization
- **python-multipart**: File upload handling

#### LLM Providers
- **openai** (>=1.12.0): OpenAI API client (embeddings)
- **OpenRouter**: DeepSeek V3 access via OpenAI-compatible API

#### Vector Stores
- **chromadb** (>=0.4.22): Vector database for RAG (26 regulatory docs)
- **faiss-cpu** (>=1.7.4): Facebook AI Similarity Search (alternative)

#### Observability
- **langfuse** (==3.5.2): LangFuse Cloud tracing with @observe decorators
- **opentelemetry-sdk** (>=1.24.0): OpenTelemetry instrumentation
- **opentelemetry-exporter-otlp** (>=1.24.0): OTLP exporter for traces
- **openinference-instrumentation-llama-index** (>=3.0.0): LlamaIndex tracing
- **openinference-instrumentation-openai** (>=0.1.30): OpenAI tracing
- **arize-phoenix** (>=4.0.0): Phoenix observability (legacy, replaced by LangFuse)

#### Database
- **asyncpg**: Async PostgreSQL driver
- **sqlalchemy**: Async ORM with connection pooling
- **psycopg2-binary**: PostgreSQL adapter (sync fallback)

#### Authentication
- **clerk-backend-api** (==4.0.0): Clerk JWT validation
- **pyjwt[crypto]** (==2.9.0): JWT token handling
- **cryptography** (>=45.0.6): Cryptographic operations
- **python-jose[cryptography]** (>=3.5.0): JOSE token handling

#### Document Processing
- **PyPDF2** (>=3.0.1): PDF parsing
- **pdfplumber** (>=0.10.0): Advanced PDF extraction
- **markdown** (>=3.5.0): Markdown parsing

#### Data Processing
- **numpy** (<2.0): Numerical computing (pinned for compatibility)
- **pandas** (>=2.0.0): Data manipulation and analysis
- **scipy** (>=1.11.0): Statistical analysis (Cohen's Kappa)

#### Visualization
- **plotly** (>=5.15.0): Interactive visualizations
- **matplotlib** (>=3.7.0): Static plots
- **seaborn** (>=0.12.0): Statistical data visualization
- **networkx** (>=3.1.0): Graph visualizations (traceability matrix)
- **kaleido** (>=1.0.0): Static image export for Plotly

#### AWS SDK
- **boto3** (>=1.40.61): AWS SDK for Python (S3, SQS)
- **aioboto3** (>=15.5.0): Async AWS SDK
- **aiobotocore** (>=2.11.0): Async botocore
- **moto[s3]** (>=4.2.0): AWS service mocking for tests

#### Utilities
- **python-dotenv** (>=1.0.0): Environment variable loading
- **aiofiles** (>=23.2.1): Async file I/O
- **httpx** (>=0.25.0): Async HTTP client
- **requests** (>=2.31.0): Sync HTTP client
- **aiohttp** (>=3.8.0): Async HTTP server/client
- **tiktoken** (>=0.5.0): Token counting for cost tracking
- **nest-asyncio** (>=1.6.0): Nested event loop support
- **json-repair** (>=0.54.2): Robust JSON parsing

### Frontend (TypeScript)

#### Next.js Stack
- **next** (14.x): React framework with SSR, SSG, ISR
- **react** (18.x): UI library
- **react-dom** (18.x): React DOM renderer

#### UI Components
- **@clerk/nextjs**: Clerk authentication components
- **tailwindcss**: Utility-first CSS framework
- **@headlessui/react**: Unstyled accessible UI components
- **@heroicons/react**: SVG icon library

#### State Management
- **react-query**: Server state management
- **zustand**: Client state management (lightweight)

#### HTTP Client
- **axios**: Promise-based HTTP client

## Build Systems & Package Managers

### Python
- **uv**: Fast Python package installer and resolver (Rust-based)
  - Replaces pip for faster dependency resolution
  - Used in Dockerfile multi-stage builds
- **hatchling**: Build backend for pyproject.toml
- **setuptools**: Legacy build system (fallback)

### TypeScript
- **npm**: Node.js package manager
- **next build**: Next.js production build (standalone output)

## Development Tools

### Code Quality
- **ruff** (>=0.1.0): Fast Python linter and formatter (Rust-based)
  - Replaces flake8, black, isort, pylint
  - Configuration in pyproject.toml
- **mypy** (>=1.0.0): Static type checker for Python
  - Strict mode enabled (disallow_untyped_defs, check_untyped_defs)
- **eslint**: JavaScript/TypeScript linter
- **prettier**: Code formatter for TypeScript/JavaScript

### Testing
- **pytest** (>=7.4.0): Python test framework
- **pytest-asyncio** (>=0.21.0): Async test support
- **pytest-mock** (>=3.15.1): Mocking framework
- **pytest-cov** (>=7.0.0): Code coverage reporting
- **freezegun** (>=1.5.5): Time-based test determinism

## Infrastructure & Deployment

### Containerization
- **Docker Engine** (29.x): Container runtime (WSL2 native, NOT Docker Desktop)
- **Docker Compose** (v2.x): Multi-container orchestration
- **Multi-stage Builds**: Separate builder and runtime stages

### Base Images
- **python:3.12-slim-bookworm**: Debian-based Python runtime (API, worker)
- **node:20-alpine**: Alpine-based Node.js runtime (frontend)
- **pgvector/pgvector:pg15**: PostgreSQL 15 with pgvector extension
- **localstack/localstack:3**: LocalStack for AWS service mocking
- **amazon/aws-cli:latest**: AWS CLI for LocalStack initialization

### Cloud Services (Development Mocks)
- **LocalStack 3.x**: AWS service emulation (SQS, S3)
  - testgen-jobs queue (VisibilityTimeout=300s, MessageRetentionPeriod=14 days)
  - testgen-jobs-dlq queue (dead-letter queue)

### Cloud Services (Production)
- **LangFuse Cloud**: EU-compliant observability platform
- **Clerk**: Authentication and user management
- **OpenRouter**: LLM API gateway (DeepSeek V3 access)

### Infrastructure as Code
- **Terraform** (>=1.5.0): AWS infrastructure provisioning
  - Backend: S3 + DynamoDB state locking
  - Modules: ECS Fargate, Aurora Serverless, Lambda, CloudFront

## Development Commands

### Environment Setup

```bash
# Create virtual environment
uv venv

# Activate virtual environment (Windows PowerShell)
./.venv/Scripts/Activate.ps1

# Activate virtual environment (macOS/Linux)
source .venv/bin/activate

# Install dependencies
uv pip install -e .

# Copy environment configuration
cp .env.example .env.local
# Edit .env.local with API keys
```

### Docker Compose (WSL2 Ubuntu Terminal)

```bash
# Start all services (postgres, localstack, api, worker, frontend)
docker-compose -f docker-compose.dev.yml up -d

# View logs (all services)
docker-compose -f docker-compose.dev.yml logs -f

# View logs (specific service)
docker-compose -f docker-compose.dev.yml logs -f api

# Restart service (fast iteration, volume mounts enabled)
docker-compose -f docker-compose.dev.yml restart api

# Stop all services
docker-compose -f docker-compose.dev.yml down

# Stop and remove volumes (reset database, queues, ChromaDB)
docker-compose -f docker-compose.dev.yml down --volumes

# Check service health
docker ps
curl http://localhost:8080/health  # API healthcheck
curl http://localhost:3000          # Frontend
```

### Code Quality

```bash
# Lint and format Python code
uv run ruff check --fix

# Type check Python code
uv run mypy .

# Lint TypeScript code
cd main/frontend
npm run lint

# Format TypeScript code
cd main/frontend
npm run format
```

### Testing

```bash
# Run all tests
uv run pytest main/tests/ -v

# Run specific test file
uv run pytest main/tests/unit/test_categorization.py -v

# Run with coverage
uv run pytest main/tests/ --cov=main/src --cov-report=html

# Run integration tests only
uv run pytest main/tests/integration/ -v

# Run compliance tests only
uv run pytest main/tests/compliance/ -v

# Run end-to-end test (Docker stack must be running)
./scripts/test-e2e-local.sh
```

### Database Operations

```bash
# Connect to PostgreSQL (from host)
psql postgresql://postgres:devpassword@localhost:5432/testgen

# Connect to PostgreSQL (from container)
docker exec -it pharma-postgres-dev psql -U postgres -d testgen

# View jobs table
docker exec -it pharma-postgres-dev psql -U postgres -d testgen -c "SELECT * FROM jobs;"

# Clear jobs table (development only)
./scripts/clear-jobs-dev.sh
```

### ChromaDB Operations

```bash
# Seed ChromaDB with regulatory documents
docker exec -it pharma-api-dev python scripts/seed_chroma.py

# Verify ChromaDB collections
docker exec -it pharma-api-dev python -c "
import chromadb
client = chromadb.PersistentClient(path='/app/chroma_db')
print(client.list_collections())
"
```

### API Testing

```bash
# Get Clerk JWT token
python scripts/get_clerk_token.py

# Submit job (with Clerk JWT)
curl -X POST http://localhost:8080/jobs \
  -H "Authorization: Bearer YOUR_CLERK_JWT" \
  -F "file=@datasets/urs_corpus/category_5/urs_001.md"

# Get job status
curl http://localhost:8080/jobs/{job_id}

# List jobs
curl http://localhost:8080/jobs \
  -H "Authorization: Bearer YOUR_CLERK_JWT"

# Download test suite
curl http://localhost:8080/jobs/{job_id}/download \
  -H "Authorization: Bearer YOUR_CLERK_JWT" \
  -o test_suite.yaml
```

### PRP Workflow (Task Execution)

```bash
# Execute PRP task with multi-agent orchestration
/prp 1.2  # Phase 1, Task 2

# Available tasks: 0.1-5.3 across 6 phases
# Phase 0: Foundations (0.1-0.4)
# Phase 1: Backend Abstraction (1.1-1.4)
# Phase 2: Frontend Dashboard (2.1-2.4)
# Phase 3: Containerization (3.1-3.4)
# Phase 4: AWS Deployment (4.1-4.4)
# Phase 5: Hardening (5.1-5.3)
```

### LangFuse Observability

```bash
# Access LangFuse Cloud dashboard
# https://cloud.langfuse.com

# Verify LangFuse integration
docker-compose -f docker-compose.dev.yml logs -f api | grep "langfuse"

# Check trace export
docker exec -it pharma-api-dev python -c "
from langfuse import Langfuse
langfuse = Langfuse()
print(langfuse.get_trace_url('trace_id'))
"
```

## Version Constraints

### Critical Pinned Versions
- **numpy** (<2.0): Compatibility with LlamaIndex and ChromaDB
- **clerk-backend-api** (==4.0.0): API stability for JWT validation
- **pyjwt[crypto]** (==2.9.0): Security-critical dependency
- **langfuse** (==3.5.2): Observability platform compatibility

### Minimum Versions
- **Python** (>=3.12): Required for modern async features
- **Node.js** (>=20): Required for Next.js 14
- **PostgreSQL** (>=15): Required for pgvector extension
- **Docker Engine** (>=29): Required for BuildKit features

## Platform-Specific Notes

### Windows (WSL2)
- **Docker Engine**: Install natively in Ubuntu WSL2, NOT Docker Desktop
  - Docker Desktop caused memory issues on ARM64 (Qualcomm Snapdragon X Elite)
  - Better performance with native Docker Engine
- **File Paths**: Use Unix paths in WSL2 terminal (`/mnt/c/Users/...`)
- **Volume Mounts**: Bind mounts work across WSL2 and Windows filesystem

### macOS
- **Docker Desktop**: Recommended for macOS (native integration)
- **ARM64 (M1/M2)**: Multi-platform builds supported (linux/amd64, linux/arm64)

### Linux
- **Docker Engine**: Install via official Docker repositories
- **Permissions**: Add user to docker group (`sudo usermod -aG docker $USER`)

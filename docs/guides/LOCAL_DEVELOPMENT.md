# Local Development Guide

**Docker Compose Multi-Service Stack for Pharmaceutical Test Generation System**

Version: 1.0
Created: 2025-11-15
GAMP-5 Category: 5 (Custom Software Development Environment)

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Service Architecture](#service-architecture)
5. [Environment Configuration](#environment-configuration)
6. [Common Commands](#common-commands)
7. [Troubleshooting](#troubleshooting)
8. [Parity Gaps](#parity-gaps)
9. [Migration Testing](#migration-testing)
10. [Compliance Notes](#compliance-notes)

---

## Overview

This Docker Compose stack provides a **production-like development environment** that orchestrates 4 services to mimic AWS production:

| Service      | Role                          | Production Equivalent     | Port  |
|--------------|-------------------------------|---------------------------|-------|
| `postgres`   | Database (dev only)           | Not used (stateless)      | 5432  |
| `localstack` | AWS SQS Mock                  | Amazon SQS                | 4566  |
| `api`        | FastAPI Job Submission        | ECS Fargate (API)         | 8080  |
| `worker`     | Background Job Processor      | ECS Fargate (Worker)      | -     |

**Key Benefits:**
- Test complete workflows locally without AWS credentials
- Debug job processing with live code reload
- Validate database schema locally (not used in production)
- Measure performance parity (local vs AWS)

---

## Prerequisites

### Required Software

1. **Docker Desktop** (includes Docker Compose)
   - Version: 4.25+ (with Compose V2)
   - Platform: Windows 11 (WSL2) with ARM64 (Qualcomm Oryon) support
   - Download: https://www.docker.com/products/docker-desktop/

2. **uv Package Manager** (for local Python development)
   - Version: 0.9.8+
   - Install: `curl -LsSf https://astral.sh/uv/install.sh | sh`

3. **Git** (version control)
   - Version: 2.40+

### Optional Tools

- **psql** (PostgreSQL CLI) - For database inspection
- **awslocal** (LocalStack CLI) - For SQS queue inspection (pre-installed in container)
- **curl** or **Postman** - For API testing

### System Requirements

- **RAM:** 8 GB minimum (16 GB recommended)
- **Disk:** 5 GB free space (for Docker images + volumes)
- **CPU:** 2 cores minimum (4 cores recommended)

---

## Quick Start

### 1. Clone Repository

```bash
cd C:\Users\anteb\Desktop\Courses\Projects\thesis_project
```

### 2. Configure Environment Variables

Copy the development environment template:

```bash
cp .env.development .env.development.local  # Optional: keep a local copy
```

**CRITICAL:** Edit `.env.development` and replace:
- `OPENAI_API_KEY=REPLACE_WITH_YOUR_OPENROUTER_API_KEY`

Get OpenRouter API key from: https://openrouter.ai/keys

### 3. Start Services

```bash
docker-compose -f docker-compose.dev.yml up -d
```

> **Note:** Uvicorn hot reload is now opt-in to prevent watchfiles OOM issues on Windows/WSL2. Leave the default `UVICORN_RELOAD=0` in `.env.development` for stability, and flip it to `1` only when you need live reload and have >4GB free RAM.

**Expected Output:**
```
Creating network "pharma-dev" with driver bridge
Creating volume "postgres-data" with driver local
Creating volume "localstack-data" with driver local
Creating pharma-postgres-dev ... done
Creating pharma-localstack-dev ... done
Creating pharma-api-dev ... done
Creating pharma-worker-dev ... done
```

### 4. Verify Services

Wait 30-60 seconds for initialization, then check:

```bash
# API Health Check
curl http://localhost:8080/health

# Expected: {"status":"healthy"}
```

```bash
# View Logs
docker-compose -f docker-compose.dev.yml logs -f
```

**Look for:**
- `postgres`: ✓ Database Initialization Complete!
- `localstack`: ✓ SQS Initialization Complete!
- `api`: FastAPI application ready
- `worker`: Background worker started

### 5. Test Job Submission (Optional)

Requires Clerk authentication token. See [Authentication Guide](../main/docs/guides/CLERK_INTEGRATION_TESTING.md).

```bash
# Example with test token
curl -X POST http://localhost:8080/jobs \
  -H "Authorization: Bearer $CLERK_TOKEN" \
  -F "file=@test-urs.txt"
```

---

## Service Architecture

### Startup Sequence

Docker Compose enforces dependency order via `depends_on` with health checks:

```
1. postgres starts
   └─> Runs scripts/postgres-init.sql
   └─> Health check: pg_isready -U postgres -d testgen
   └─> Status: HEALTHY (after ~10-30s)

2. localstack starts
   └─> Runs scripts/init-localstack.sh
   └─> Creates SQS queues (testgen-jobs, testgen-jobs-dlq)
   └─> Status: STARTED (after ~5-10s)

3. api starts (depends on postgres HEALTHY + localstack STARTED)
   └─> Loads .env.development
   └─> Connects to postgres:5432
   └─> Connects to localstack:4566
   └─> Starts background worker (in-process)
   └─> Status: HEALTHY (after ~10-20s)

4. worker starts (depends on postgres HEALTHY + localstack STARTED)
   └─> Loads .env.development
   └─> Polls SQS queue: testgen-jobs
   └─> Processes jobs in background
   └─> Status: RUNNING (no health check)
```

### Network Communication

All services communicate via Docker bridge network `pharma-dev`:

```
┌──────────────────┐
│   Host Machine   │
│  (localhost)     │
└────────┬─────────┘
         │
    Port Mappings:
    - 8080 → api:8080
    - 5432 → postgres:5432
    - 4566 → localstack:4566
         │
┌────────┴──────────────────────────────────────┐
│  Docker Network: pharma-dev (bridge)          │
│                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ postgres │  │localstack│  │   api    │   │
│  │  :5432   │  │  :4566   │  │  :8080   │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │             │              │          │
│       └─────────────┴──────────────┘          │
│                     │                         │
│               ┌─────┴─────┐                   │
│               │  worker   │                   │
│               │  (no port)│                   │
│               └───────────┘                   │
└───────────────────────────────────────────────┘
```

**Service Names as Hostnames:**
- API connects to `postgres:5432` (NOT `localhost:5432`)
- Worker connects to `localstack:4566` (NOT `localhost:4566`)
- Host accesses API via `localhost:8080`

---

## Environment Configuration

### File: `.env.development`

**Location:** `C:\Users\anteb\Desktop\Courses\Projects\thesis_project\.env.development`

**Key Variables:**

| Variable                 | Value (Development)                              | Purpose                          |
|--------------------------|--------------------------------------------------|----------------------------------|
| `ENVIRONMENT`            | `development`                                    | Triggers dev mode loading        |
| `STORAGE_MODE`           | `local`                                          | Use filesystem (not S3)          |
| `RAG_MODE`               | `chromadb`                                       | Use ChromaDB (not pgvector)      |
| `QUEUE_MODE`             | `sqs`                                            | Use LocalStack SQS               |
| `DATABASE_URL`           | `postgresql://postgres:devpassword@postgres:5432/testgen` | Postgres connection |
| `AWS_ENDPOINT_URL`       | `http://localstack:4566`                         | LocalStack gateway               |
| `SQS_QUEUE_URL`          | `http://localstack:4566/000000000000/testgen-jobs` | Main job queue                |
| `CLERK_ISSUER`           | `https://helped-sturgeon-19.clerk.accounts.dev`  | JWT verification issuer          |
| `OPENAI_API_KEY`         | **YOUR_OPENROUTER_KEY**                          | DeepSeek V3 API access           |
| `LLM_MODEL`              | `deepseek/deepseek-chat`                         | Required model (NO GPT-4/O3)     |

**Security Notes:**
- `.env.development` is Git-ignored (never commit secrets)
- Use test/dev instances only (NOT production credentials)
- Dummy AWS credentials: `test/test` (LocalStack requirement)

---

## Common Commands

### Start Services

```bash
# Start all services in background
docker-compose -f docker-compose.dev.yml up -d

# Start with live log output
docker-compose -f docker-compose.dev.yml up

# Start specific services
docker-compose -f docker-compose.dev.yml up -d postgres localstack
```

### View Logs

```bash
# All services
docker-compose -f docker-compose.dev.yml logs -f

# Specific service
docker-compose -f docker-compose.dev.yml logs -f api

# Last 100 lines
docker-compose -f docker-compose.dev.yml logs --tail=100
```

### Stop Services

```bash
# Stop services (keeps volumes)
docker-compose -f docker-compose.dev.yml down

# Stop and remove volumes (reset data)
docker-compose -f docker-compose.dev.yml down --volumes

# Force stop all containers
docker-compose -f docker-compose.dev.yml down --remove-orphans
```

### Restart Services

```bash
# Restart all services
docker-compose -f docker-compose.dev.yml restart

# Restart specific service
docker-compose -f docker-compose.dev.yml restart api

# Rebuild images (after code changes in Dockerfile)
docker-compose -f docker-compose.dev.yml up -d --build
```

### Inspect Services

```bash
# List running containers
docker-compose -f docker-compose.dev.yml ps

# View resource usage
docker stats pharma-api-dev pharma-worker-dev

# Inspect volumes
docker volume ls | grep pharma
docker volume inspect postgres-data
```

### Database Operations

```bash
# Connect to Postgres via psql
docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres -d testgen

# List tables
docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres -d testgen -c '\dt'

# Query jobs table
docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres -d testgen -c 'SELECT * FROM jobs;'

# Reset database (re-run init script)
docker-compose -f docker-compose.dev.yml down --volumes
docker-compose -f docker-compose.dev.yml up -d postgres
```

### SQS Operations

```bash
# List queues
docker-compose -f docker-compose.dev.yml exec localstack awslocal sqs list-queues --region eu-west-2

# Get queue attributes
docker-compose -f docker-compose.dev.yml exec localstack awslocal sqs get-queue-attributes \
  --queue-url http://localstack:4566/000000000000/testgen-jobs \
  --attribute-names All \
  --region eu-west-2

# Send test message
docker-compose -f docker-compose.dev.yml exec localstack awslocal sqs send-message \
  --queue-url http://localstack:4566/000000000000/testgen-jobs \
  --message-body '{"job_id":"test-123"}' \
  --region eu-west-2

# Receive messages
docker-compose -f docker-compose.dev.yml exec localstack awslocal sqs receive-message \
  --queue-url http://localstack:4566/000000000000/testgen-jobs \
  --region eu-west-2
```

### Code Changes

**API/Worker Hot Reload:**
1. Edit files in `main/` directory
2. Code is mounted via volume (`./main:/app/main:ro`)
3. API reload is disabled by default; set `UVICORN_RELOAD=1` in `.env.development` before running `docker-compose up` if you need uvicorn `--reload` (ensure >4GB RAM available)
4. Worker requires restart: `docker-compose -f docker-compose.dev.yml restart worker`

**Dockerfile Changes:**
1. Edit `Dockerfile.api` or `Dockerfile.worker`
2. Rebuild: `docker-compose -f docker-compose.dev.yml up -d --build`

---

## Troubleshooting

### Services Failing to Start

**Symptom:** `postgres` or `localstack` container exits immediately

**Diagnosis:**
```bash
docker-compose -f docker-compose.dev.yml logs postgres
docker-compose -f docker-compose.dev.yml logs localstack
```

**Common Causes:**
1. **Port conflict:** 5432 or 4566 already in use
   - Solution: `netstat -ano | findstr 5432` (Windows) and kill process
   - Or: Change port mapping in `docker-compose.dev.yml`

2. **Volume permissions:** WSL2 filesystem permissions
   - Solution: `docker-compose -f docker-compose.dev.yml down --volumes && docker-compose -f docker-compose.dev.yml up -d`

3. **Init script errors:** Syntax error in SQL/shell script
   - Check logs for `ERROR` or `FATAL` messages
   - Validate SQL: `psql -U postgres -f scripts/postgres-init.sql` (local psql)

### API/Worker Connection Refused

**Symptom:** `API: connection to server at "postgres" (172.x.x.x), port 5432 failed`

**Diagnosis:**
```bash
# Check if postgres is healthy
docker-compose -f docker-compose.dev.yml ps

# Expected: STATUS = healthy
```

**Common Causes:**
1. **Postgres not ready:** Healthcheck failing
   - Solution: Wait 30-60s, check `docker-compose logs postgres`

2. **Wrong hostname:** Using `localhost` instead of `postgres`
   - Solution: Update `DATABASE_URL` in `.env.development` to use `postgres:5432`

3. **Credentials mismatch:** Environment variables don't match `postgres-init.sql`
   - Solution: Verify `POSTGRES_PASSWORD=devpassword` in both files

### SQS Queue Not Found

**Symptom:** `Worker: An error occurred (AWS.SimpleQueueService.NonExistentQueue)`

**Diagnosis:**
```bash
# List queues in LocalStack
docker-compose -f docker-compose.dev.yml exec localstack awslocal sqs list-queues --region eu-west-2
```

**Common Causes:**
1. **Init script didn't run:** LocalStack started too fast
   - Solution: Restart LocalStack: `docker-compose -f docker-compose.dev.yml restart localstack`

2. **Wrong queue URL:** Using localhost instead of service name
   - Solution: Update `SQS_QUEUE_URL` in `.env.development` to use `localstack:4566`

3. **Script not executable:** `init-localstack.sh` missing execute permission
   - Solution: `chmod +x scripts/init-localstack.sh && docker-compose -f docker-compose.dev.yml restart localstack`

### Job Processing Not Working

**Symptom:** Job submitted via API but worker doesn't process it

**Diagnosis:**
```bash
# Check worker logs
docker-compose -f docker-compose.dev.yml logs -f worker

# Check SQS messages
docker-compose -f docker-compose.dev.yml exec localstack awslocal sqs receive-message \
  --queue-url http://localstack:4566/000000000000/testgen-jobs \
  --region eu-west-2
```

**Common Causes:**
1. **Queue mode mismatch:** API using `memory` queue, worker expecting SQS
   - Solution: Verify `QUEUE_MODE=sqs` in `.env.development`

2. **Worker crash loop:** Exception in job processing logic
   - Check worker logs for stack traces
   - Test job processing locally: `uv run python -m main.api.worker`

3. **Visibility timeout:** Message locked by another consumer
   - Wait 15 minutes (visibility timeout) and retry

### Docker Compose Configuration Errors

**Symptom:** `ERROR: The Compose file is invalid`

**Diagnosis:**
```bash
# Validate YAML syntax
docker-compose -f docker-compose.dev.yml config
```

**Common Causes:**
1. **Indentation errors:** YAML is whitespace-sensitive
   - Solution: Use 2-space indentation consistently

2. **Missing env file:** `.env.development` not found
   - Solution: Create file from template above

3. **Invalid depends_on condition:** Typo in service name
   - Solution: Verify service names match exactly

---

## Parity Gaps

### Critical Differences: Local vs AWS Production

Understanding these differences is essential for **validation risk assessment** (GAMP-5 requirement).

| Component       | Local (Docker Compose)                    | AWS Production                              | Impact                                      |
|-----------------|-------------------------------------------|---------------------------------------------|---------------------------------------------|
| **Database**    | Postgres 15-alpine + psycopg2/asyncpg     | Not used (stateless design)                 | Production uses S3 for ChromaDB state       |
| **Queue**       | LocalStack SQS 3.x                        | Amazon SQS                                  | FIFO guarantees, deduplication may differ   |
| **Storage**     | Local filesystem (`./output/`)            | S3 + Object Lock                            | No immutability in local mode               |
| **Auth**        | Clerk dev instance                        | Clerk production + IAM roles                | Different rate limits, user base            |
| **Observability** | LangFuse Cloud (optional)               | LangFuse Cloud (EU)                         | Same service, different retention           |
| **Networking**  | Bridge network (single host)              | VPC + security groups                       | No network isolation in local               |
| **Secrets**     | .env file                                 | AWS Secrets Manager                         | No rotation in local mode                   |
| **Scaling**     | Single container per service              | ECS Fargate autoscaling (2-10 tasks)        | No horizontal scaling in local              |

### Behavioral Differences

#### 1. State Management
- **Local Postgres:** Used for job queue metadata and development testing
- **AWS Production:** Stateless - ChromaDB stored in S3, downloaded at container startup
- **Risk:** State persistence patterns differ between environments

#### 2. Queue Delivery Guarantees
- **LocalStack SQS:** At-least-once delivery (best effort)
- **Amazon SQS:** Guaranteed at-least-once delivery, optional exactly-once (FIFO)
- **Risk:** Duplicate message handling may need additional testing in AWS

#### 3. Performance Characteristics
- **Local:** Low latency (~1-5ms database, ~10ms queue)
- **AWS:** Higher latency (~20-50ms SQS, ~100ms S3)
- **Risk:** Timeout configurations tuned for local may be too aggressive for AWS

#### 4. Error Taxonomy
- **LocalStack:** May not replicate all AWS error codes
- **AWS:** Full error taxonomy (ThrottlingException, ServiceUnavailableException, etc.)
- **Risk:** Error handling code paths not fully exercised locally

### Parity Testing Checklist

Before deploying to AWS, verify these scenarios work in local stack:

- [ ] Job submission with small URS files (<1 MB)
- [ ] Job submission with large URS files (>10 MB)
- [ ] Concurrent job processing (submit 10 jobs simultaneously)
- [ ] Queue retry logic (DLQ redrive after 3 failures)
- [ ] Database connection failures (kill postgres mid-transaction)
- [ ] Storage failures (fill disk, permission errors)
- [ ] Long-running jobs (>15 min workflow timeout)
- [ ] Authentication failures (expired Clerk tokens)
- [ ] Network partitions (disconnect localstack during job processing)
- [ ] Worker crash recovery (kill worker, verify job resumes)

---

## Migration Testing

### Schema Migration Testing

**Goal:** Validate database schema locally (PostgreSQL used for development testing only; not deployed to production).

**Procedure:**
1. Start with empty database:
   ```bash
   docker-compose -f docker-compose.dev.yml down --volumes
   docker-compose -f docker-compose.dev.yml up -d postgres
   ```

2. Run migration script (example):
   ```bash
   docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres -d testgen -f /path/to/migration.sql
   ```

3. Verify schema:
   ```bash
   docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres -d testgen -c '\d jobs'
   ```

**Note:** Production AWS deployment does not use PostgreSQL. This database is for local development workflow testing only.

### End-to-End Workflow Testing

**Goal:** Validate complete job lifecycle locally before AWS deployment.

**Test Scenario:**
1. Submit job via API
2. Verify job record in database (`status=pending`)
3. Verify message in SQS queue
4. Worker polls queue and processes job
5. Verify job completion (`status=completed`)
6. Verify result files in storage (`/app/output/`)

**Automated Test Script:**
```bash
#!/bin/bash
set -e

# 1. Submit job
JOB_RESPONSE=$(curl -s -X POST http://localhost:8080/jobs \
  -H "Authorization: Bearer $CLERK_TOKEN" \
  -F "file=@test-urs.txt")

JOB_ID=$(echo $JOB_RESPONSE | jq -r '.job_id')
echo "Job submitted: $JOB_ID"

# 2. Verify job in database
docker-compose -f docker-compose.dev.yml exec -T postgres psql -U postgres -d testgen -c \
  "SELECT status FROM jobs WHERE job_id='$JOB_ID';"

# 3. Wait for completion (max 5 minutes)
for i in {1..60}; do
  STATUS=$(curl -s http://localhost:8080/jobs/$JOB_ID | jq -r '.status')
  echo "Attempt $i: Status = $STATUS"

  if [ "$STATUS" == "completed" ]; then
    echo "Job completed successfully!"
    exit 0
  elif [ "$STATUS" == "failed" ]; then
    echo "Job failed!"
    exit 1
  fi

  sleep 5
done

echo "Job timed out (>5 minutes)"
exit 1
```

---

## Compliance Notes

### GAMP-5 Category Classification

**Development Environment:** Category 5 (Custom Software)
- Same validation rigor NOT required for dev (only production)
- Focus on **functional testing**, not validation
- Parity with production reduces validation risk

### ALCOA+ Principles in Development

| Principle          | Development Environment           | Production Environment          |
|--------------------|-----------------------------------|---------------------------------|
| **Attributable**   | Optional (developer tracking)     | Required (Clerk user ID)        |
| **Legible**        | Yes (logs, traces)                | Yes (structured logging)        |
| **Contemporaneous**| Yes (timestamps in logs)          | Yes (real-time audit trail)     |
| **Original**       | Partial (mock data)               | Yes (source URS files)          |
| **Accurate**       | Best effort                       | Required (validated system)     |
| **Complete**       | Test coverage focus               | Full data capture               |
| **Consistent**     | Code consistency                  | Data + process consistency      |
| **Enduring**       | Git versioning                    | 7-year retention (S3 Object Lock)|
| **Available**      | Developer access                  | Controlled access (IAM)         |

### Data Handling Requirements

**CRITICAL:** Development environment must NEVER contain:
- Production data (real URS files)
- Patient-identifiable information
- Regulated pharmaceutical records

**Allowed Data:**
- Synthetic URS files (test fixtures)
- Mock GAMP-5 categorization results
- Developer-generated test suites

### Audit Trail

Development logs are **informational only** (not subject to 21 CFR Part 11):
- No electronic signature requirements
- No immutability enforcement
- No 7-year retention mandates

**However:** Git commits provide version history for:
- Code changes (attributable, contemporaneous)
- Configuration changes (docker-compose.dev.yml, .env.development)
- Schema migrations (scripts/postgres-init.sql)

---

## Additional Resources

- **Docker Compose Documentation:** https://docs.docker.com/compose/
- **LocalStack Documentation:** https://docs.localstack.cloud/
- **PostgreSQL Documentation:** https://www.postgresql.org/docs/15/
- **Clerk Authentication Guide:** [../main/docs/guides/CLERK_INTEGRATION_TESTING.md](../main/docs/guides/CLERK_INTEGRATION_TESTING.md)
- **AWS Migration Plan:** [../PRPs/aws-migration-updated.md](../PRPs/aws-migration-updated.md)

---

## Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section above
2. Review container logs: `docker-compose -f docker-compose.dev.yml logs -f`
3. Validate configuration: `docker-compose -f docker-compose.dev.yml config`
4. Reset environment: `docker-compose -f docker-compose.dev.yml down --volumes && docker-compose -f docker-compose.dev.yml up -d`

---

**Document Version:** 1.0
**Last Updated:** 2025-11-15
**Maintained By:** Pharmaceutical Test Generation Team

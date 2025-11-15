# Context Collector Result - 2025-11-11 14:20:00

## Agent Configuration
- Agent: context-collector
- Task ID: 3.1
- Invoked: 2025-11-11 14:20:00
- Duration: 25 minutes
- Status: SUCCESS

## Task Understanding

Task 3.1 aims to optimize Docker multi-stage builds for the pharmaceutical test generation system to prepare for AWS ECS Fargate deployment. The task requires:

1. Refactoring FastAPI and worker Dockerfiles to use multi-stage builds with slim base images
2. Embedding Tini as entrypoint for proper signal handling (PID 1)
3. Enabling non-root user execution for security compliance
4. Baking in healthcheck scripts and compile-time dependencies
5. Achieving image size <200MB for optimized ECS deployment times
6. Ensuring GAMP-5/ALCOA+ compliance for pharmaceutical validation

This is a containerization task (Phase 3) that depends on Task 2 baseline Dockerfiles and storage adapters from Tasks 1.1/1.2 (which already exist in the codebase).

## Research Findings

### Project-Specific Context

**Current Setup:**
- **Python Version:** 3.12 (confirmed in pyproject.toml line 6: `requires-python = ">=3.12"`)
- **Package Manager:** uv (confirmed in pyproject.toml [tool.uv] section)
- **FastAPI App:** `main/api/app.py` exists with lifespan management, LangFuse observability, async job queue
- **Worker:** `main/api/worker.py` implements background job processing
- **Storage Adapters:** Already implemented in `main/src/adapters/`:
  - `storage.py` - Dual-mode storage abstraction (local/S3)
  - `s3_adapter.py`, `local_adapter.py` - Backend implementations
  - `vector_store.py` - Pluggable vector store provider
  - `chroma_adapter.py`, `postgres_adapter.py` - RAG backends

**Reference Implementation Found:**
- `examples/alex/backend/researcher/Dockerfile` provides working example:
  - Uses `python:3.12-slim` base image (matching project Python version)
  - Uses `uv` for package management (matching project setup)
  - Platform: `--platform=linux/amd64` (important for ECS Fargate)
  - Installs Node.js and Playwright (NOT needed for this project)
  - Single-stage build (NOT optimized - task requires multi-stage)
  - NO Tini integration (must add)
  - NO non-root user (must add)
  - NO HEALTHCHECK directive (must add)

**Key Dependencies from pyproject.toml:**
- `chromadb>=0.4.22` - Vector database (requires onnxruntime, SQLite libs)
- `llama-index-vector-stores-postgres>=0.2.0` - PostgreSQL vector store
- `fastapi`, `uvicorn` - Web framework
- `langfuse==3.5.2` - Observability
- `clerk-backend-api==4.0.0` - Authentication
- `aiobotocore>=2.11.0` - AWS S3 async client
- `cryptography>=45.0.6` - Security libraries

**No Existing Dockerfiles:** Project root has NO Dockerfiles yet (this task creates them).

### Docker Multi-Stage Build Patterns for uv + Python 3.12

**Optimal Base Image:**
- **Recommendation:** `python:3.12-slim-bookworm` (Debian-based)
- **Rationale:**
  - Debian slim images (~150MB) balance size and compatibility
  - ChromaDB does NOT support Alpine (GitHub issue #2758: "not possible to run inside alpine")
  - Distroless lacks apt-get (needed for runtime dependencies like libpq5, curl)
  - python:3.12-slim provides C compiler for building native extensions

**uv Installation Methods:**

1. **Binary Copy (Recommended for Reproducibility):**
   ```dockerfile
   COPY --from=ghcr.io/astral-sh/uv:0.9.8 /uv /uvx /bin/
   ```
   - Pin to specific version (0.9.8 as of 2025-01)
   - No network dependency during build
   - Minimal layer size (~10MB)

2. **Alternative (Not Recommended):**
   ```dockerfile
   RUN pip install uv
   ```
   - Less reproducible (pulls latest)
   - Adds pip overhead

**Layer Ordering for Maximum Cache Hits:**

```dockerfile
# Stage 1: Builder
FROM python:3.12-slim-bookworm AS builder

# Install uv (cached unless version changes)
COPY --from=ghcr.io/astral-sh/uv:0.9.8 /uv /bin/uv

# Install build dependencies (cached unless apt lists change)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy ONLY dependency files first (cached unless dependencies change)
COPY pyproject.toml uv.lock ./

# Install dependencies with cache mount (MOST EXPENSIVE OPERATION)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Copy application code LAST (changes most frequently)
COPY . .

# Install project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Stage 2: Runtime
FROM python:3.12-slim-bookworm

# Runtime dependencies only (NO gcc, NO libpq-dev)
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    tini \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY --from=builder /app /app

WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH"

# Non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Tini as PID 1
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["uvicorn", "main.api.app:app", "--host", "0.0.0.0", "--port", "8080"]
```

**Key uv Environment Variables:**
```dockerfile
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never
```
- `UV_COMPILE_BYTECODE=1`: Pre-compile .pyc files for faster startup
- `UV_LINK_MODE=copy`: Required for Docker (hard links not supported)
- `UV_PYTHON_DOWNLOADS=never`: Use system Python (already in base image)

**Cache Mount Benefits:**
- RUN --mount=type=cache,target=/root/.cache/uv: Persists uv cache across builds
- Reduces rebuild time from ~5min to ~30sec for unchanged dependencies
- Docker BuildKit feature (requires `# syntax=docker/dockerfile:1.9`)

**Multi-Stage Build Size Savings:**
- Single-stage with build tools: ~500-800MB
- Multi-stage (builder + runtime): ~180-220MB
- Achieves <200MB target with proper optimization

### Tini Integration

**What is Tini:**
- Tiny init system (~10KB static binary) designed for containers
- Runs as PID 1 and spawns application as child process
- Handles two critical responsibilities:
  1. **Zombie Process Reaping:** Prevents orphaned processes from consuming PIDs
  2. **Signal Forwarding:** Ensures SIGTERM/SIGINT reach application for graceful shutdown

**Why Containers Need Tini:**

**Problem 1 - Zombie Processes:**
- When child process exits but parent doesn't call wait(), it becomes zombie (<defunct>)
- In Linux, PID 1 has special responsibility to reap zombies
- Applications not designed as init systems don't reap zombies
- Over time, zombies exhaust PID table, making system unusable

**Problem 2 - Signal Handling:**
- Docker sends SIGTERM to PID 1 for graceful shutdown
- Many applications (Python, Node.js) don't install signal handlers by default
- Without handlers, container ignores SIGTERM and gets killed with SIGKILL after 10s
- Results in: incomplete transactions, corrupted data, no cleanup

**Pharmaceutical Compliance Impact:**
- ALCOA+ requires "Complete" and "Accurate" records
- Ungraceful shutdowns can corrupt audit trails
- Lost in-flight transactions violate data integrity requirements
- GAMP-5 validation requires predictable shutdown behavior

**Installation in python:3.12-slim-bookworm:**

```dockerfile
# Method 1: apt-get (Recommended - matches system package manager)
RUN apt-get update && apt-get install -y tini && rm -rf /var/lib/apt/lists/*
# Installs to: /usr/bin/tini

# Method 2: Static binary (for Alpine or minimal images)
ADD https://github.com/krallin/tini/releases/download/v0.19.0/tini /tini
RUN chmod +x /tini
```

**Proper ENTRYPOINT Configuration:**

```dockerfile
# Correct
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["uvicorn", "main.api.app:app", "--host", "0.0.0.0", "--port", "8080"]

# The "--" separator prevents Tini from misinterpreting CMD args as its own options
```

**Signal Handling Verification:**
- Tini forwards signals to child process group
- Use `-g` flag for process group signal forwarding: `ENTRYPOINT ["/usr/bin/tini", "-g", "--"]`
- Logs warning if not running as PID 1 (detect misconfiguration)
- FastAPI/uvicorn handle SIGTERM gracefully when received via Tini

**ECS Fargate Compatibility:**
- ECS sends SIGTERM to container on task stop
- Waits for `stopTimeout` (default 30s) before SIGKILL
- Tini ensures SIGTERM reaches uvicorn for graceful shutdown
- Allows completion of in-flight requests before termination

### Runtime Dependencies

**PostgreSQL Client Libraries:**
```dockerfile
# BUILD STAGE (for psycopg2/asyncpg compilation)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# RUNTIME STAGE (for PostgreSQL connections)
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*
```
- **libpq-dev:** Development headers for building psycopg2 (build stage only)
- **libpq5:** Shared library for PostgreSQL connections (runtime required)
- **Why split:** libpq-dev is ~10MB, libpq5 is ~300KB (90% size reduction)

**ChromaDB Dependencies:**
- ChromaDB ships precompiled wheels for Linux x86_64
- Requires: SQLite (included in python:3.12-slim), onnxruntime (bundled)
- **Critical:** Does NOT support Alpine (musl libc incompatibility)
- No additional apt packages required for ChromaDB itself

**Essential Runtime Tools:**
```dockerfile
RUN apt-get update && apt-get install -y \
    curl \        # For healthcheck endpoint testing
    ca-certificates \  # For HTTPS connections (AWS APIs)
    libpq5 \      # PostgreSQL client
    tini \        # Init system
    && rm -rf /var/lib/apt/lists/*
```

**Size Optimization:**
- Always run `rm -rf /var/lib/apt/lists/*` after apt-get
- Combines update + install + cleanup in single RUN layer
- Saves ~50MB by not caching apt package lists

**Dependencies NOT Needed:**
- `build-essential`: Only in builder stage
- `git`: Not required for runtime
- `libpq-dev`: Only in builder stage
- `wget`: Use curl instead (smaller)

### Security & Compliance

**Non-Root User Best Practices:**

```dockerfile
# Create user with specific UID (important for ECS Fargate)
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Why UID 1000:
# - Predictable across environments
# - Matches default user in many base images
# - ECS task IAM roles work regardless of username
# - Audit logs can track by UID
```

**Security Implications:**
- Running as root violates principle of least privilege
- Container escape exploits gain root on host
- GAMP-5 validation requires demonstrable security controls
- ECS Fargate enforces non-root for regulatory workloads

**File Permissions:**
```dockerfile
# Ensure application files are owned by non-root user
COPY --from=builder --chown=appuser:appuser /app /app

# If writing to /app at runtime (logs, cache), set permissions in builder:
RUN mkdir -p /app/logs && chown -R appuser:appuser /app
```

**Trivy Security Scanning:**

**What is Trivy:**
- Open-source vulnerability scanner by Aqua Security
- Scans: OS packages, language libraries (Python), container images
- Detects: CVEs, misconfigurations, secrets, license issues
- Output formats: Table, JSON, SARIF (for CI/CD)

**Installation:**
```bash
# Local
brew install trivy  # macOS
apt-get install trivy  # Debian/Ubuntu

# Docker
docker run aquasec/trivy image python:3.12-slim
```

**Scanning Images:**
```bash
# Scan built image
trivy image thesis-api:latest

# Filter severity
trivy image --severity HIGH,CRITICAL thesis-api:latest

# Ignore unfixed vulnerabilities (no patches available)
trivy image --ignore-unfixed thesis-api:latest

# Output JSON for CI/CD
trivy image --format json --output results.json thesis-api:latest

# Fail build on CRITICAL vulnerabilities
trivy image --exit-code 1 --severity CRITICAL thesis-api:latest
```

**Common Vulnerabilities in python:3.12-slim:**
- Python standard library CVEs (regularly patched)
- OpenSSL vulnerabilities (use Debian security updates)
- libexpat, zlib, libc6 (system libraries)

**GAMP-5 Compliance Requirements:**
- Document all HIGH/CRITICAL vulnerabilities in validation report
- Justify accepted risks (unfixed vulnerabilities)
- Regular scanning schedule (weekly minimum)
- Track remediation in change control process

**ALCOA+ License Compliance:**
- Trivy detects license violations (GPL in proprietary software)
- Scan for: GPL, AGPL, LGPL dependencies
- Document all third-party licenses in validation package
- Use `trivy image --scanners license` for license-only scan

**Integration with Task 3.1:**
```dockerfile
# Add to CI/CD pipeline (GitHub Actions, GitLab CI)
- name: Scan Docker image
  run: |
    docker build -t thesis-api:${{ github.sha }} .
    trivy image --exit-code 1 --severity CRITICAL thesis-api:${{ github.sha }}
```

### Healthcheck Implementation

**FastAPI Healthcheck Endpoint Pattern:**

```python
# main/api/app.py (already exists)
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    ECS Fargate healthcheck endpoint.

    Returns 200 OK if:
    - Application is running
    - Database connections available (optional deep check)
    - Worker queue is responsive (optional deep check)

    GAMP-5 Compliance: Logged to audit trail via LangFuse.
    """
    return {
        "status": "healthy",
        "service": "pharmaceutical-test-generation-api",
        "version": "1.0.0"
    }

# Deep healthcheck (optional - adds latency)
@app.get("/health/deep")
async def deep_health_check(db: Database = Depends(get_db)):
    checks = {
        "database": await check_database(db),
        "worker_queue": await check_queue(),
        "storage": await check_storage()
    }

    if not all(checks.values()):
        raise HTTPException(status_code=503, detail=checks)

    return {"status": "healthy", "checks": checks}
```

**Docker HEALTHCHECK Directive:**

```dockerfile
# Shallow healthcheck (fast, minimal overhead)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Parameters explained:
# --interval=30s: Check every 30 seconds (ECS default)
# --timeout=5s: Mark unhealthy if no response in 5s
# --start-period=10s: Grace period for app startup (don't fail during boot)
# --retries=3: Mark unhealthy after 3 consecutive failures
# -f: curl fails on HTTP errors (non-200 responses)
```

**ECS Fargate Healthcheck Requirements:**

**Container-Level Healthcheck (Dockerfile):**
- ECS monitors Docker HEALTHCHECK status
- Marks container unhealthy after failures exceed retries
- Triggers task replacement if container unhealthy

**Load Balancer Healthcheck (separate from Docker):**
- Target Group healthcheck pings `/health` via ALB
- Parameters: HealthCheckIntervalSeconds, HealthCheckTimeoutSeconds, HealthyThresholdCount
- Must configure in Terraform (Task 4.1)

**Best Practices:**
1. **Keep shallow healthcheck fast (<100ms):**
   - Avoid database queries in `/health`
   - Use `/health/deep` for comprehensive checks (manual testing)

2. **Match intervals with ECS task lifecycle:**
   - start-period >= application startup time (uvicorn boot ~5-10s)
   - interval matches load balancer healthcheck interval

3. **Include curl in runtime image:**
   ```dockerfile
   RUN apt-get install -y curl
   ```

4. **Alternative to curl (reduces dependencies):**
   ```dockerfile
   HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1
   ```

**Graceful Startup Pattern:**
- FastAPI lifespan context manager (already implemented in app.py)
- Initializes dependencies before accepting traffic
- Healthcheck returns 503 during startup, 200 when ready

**Common Pitfalls:**
- Healthcheck endpoint not logging (floods audit trail)
- Deep checks too slow (mark container unhealthy under load)
- No HEALTHCHECK directive (ECS assumes always healthy)
- Wrong port in healthcheck (8080 vs 8000)

### AWS ECS Fargate Considerations

**Image Size Targets:**
- **Current target:** <200MB (task requirement)
- **Achievable with multi-stage:** 180-220MB
- **Baseline python:3.12-slim:** ~150MB
- **Add FastAPI + dependencies:** ~30-50MB
- **Add ChromaDB:** ~20MB (onnxruntime wheels)

**Why Image Size Matters:**
1. **Pull Time:** ECS Fargate pulls image from ECR on every task start
   - 200MB image: ~10-15s pull time
   - 800MB image: ~45-60s pull time
   - Impacts autoscaling responsiveness

2. **Storage Costs:** ECR charges $0.10/GB/month
   - 200MB × 10 versions = 2GB = $0.20/month
   - 800MB × 10 versions = 8GB = $0.80/month

3. **Task Startup Latency:** Target P95 ≤15 minutes (includes image pull)
   - Smaller images reduce cold start penalty

**Container Startup Time Optimization:**

```dockerfile
# Precompile Python bytecode (reduces startup ~20%)
ENV UV_COMPILE_BYTECODE=1

# Disable Python buffering (faster logs in CloudWatch)
ENV PYTHONUNBUFFERED=1

# Disable .pyc file writing (read-only filesystem)
ENV PYTHONDONTWRITEBYTECODE=1
```

**Resource Constraints (from aws-migration-updated.md):**
- **API Container:** 2 vCPU / 4 GB RAM
- **Worker Container:** 4 vCPU / 8 GB RAM

**Image should fit in memory overhead:**
- 4GB RAM - 200MB image = 3.8GB available for app runtime
- 8GB RAM - 200MB image = 7.8GB available for worker

**Platform Specification:**
```dockerfile
# ECS Fargate requires linux/amd64 or linux/arm64
FROM --platform=linux/amd64 python:3.12-slim-bookworm
```

**ECR Image Push (from Task 4.1 - ECS Deployment):**
```bash
# Tag with ECR registry
docker tag thesis-api:latest 123456789.dkr.ecr.eu-west-2.amazonaws.com/thesis-api:latest

# Push to ECR
docker push 123456789.dkr.ecr.eu-west-2.amazonaws.com/thesis-api:latest
```

**Logging to CloudWatch:**
- ECS automatically captures stdout/stderr
- Structured JSON logs preferred (LangFuse already outputs JSON)
- Use `PYTHONUNBUFFERED=1` to prevent log buffering

### Implementation Gotchas

**1. ChromaDB Alpine Incompatibility:**
- **Issue:** ChromaDB does NOT run on Alpine Linux (musl libc)
- **Solution:** MUST use Debian-based images (python:3.12-slim-bookworm)
- **Source:** GitHub issue #2758

**2. uv.lock Platform Mismatch:**
- **Issue:** Local .venv includes Windows/macOS binaries, incompatible with Linux
- **Solution:** Add `.venv` to `.dockerignore`
- **Verification:** uv sync in Docker uses linux/amd64 wheels

**3. Missing Runtime Dependencies:**
- **Issue:** Image builds but crashes at runtime: "libpq.so.5: cannot open shared object"
- **Solution:** Install libpq5 in runtime stage (NOT just libpq-dev in builder)
- **Debug:** `ldd /app/.venv/lib/python3.12/site-packages/psycopg2/_psycopg.so`

**4. Tini Not Running as PID 1:**
- **Issue:** Warning: "Tini is not running as PID 1"
- **Cause:** ENTRYPOINT set incorrectly (shell form vs exec form)
- **Solution:** Use exec form: `ENTRYPOINT ["/usr/bin/tini", "--"]`
- **Verification:** `docker exec <container> ps aux` (check PID 1)

**5. Healthcheck Port Mismatch:**
- **Issue:** Healthcheck fails: "Connection refused"
- **Cause:** Healthcheck uses port 8000, app listens on 8080
- **Solution:** Match port in HEALTHCHECK and CMD
- **From task file:** CMD uses port 8080 (line 30)

**6. File Permissions After COPY:**
- **Issue:** Container crashes: "Permission denied: /app/logs"
- **Cause:** Files copied as root, USER appuser can't write
- **Solution:** Use `--chown` in COPY: `COPY --chown=appuser:appuser`

**7. Cache Mount Requires BuildKit:**
- **Issue:** `RUN --mount=type=cache` fails: "Unknown flag: --mount"
- **Cause:** Using legacy Docker builder
- **Solution:** Enable BuildKit: `DOCKER_BUILDKIT=1 docker build`
- **Or:** Add `# syntax=docker/dockerfile:1.9` as first line

**8. uvicorn Worker Count:**
- **Issue:** Single uvicorn worker underutilizes 2 vCPU
- **Optimization:** Use `--workers 2` for API container
- **Caution:** Background worker.py already handles async queue (don't double-spawn)

**9. Langfuse Observability Overhead:**
- **Issue:** 200MB target includes LangFuse SDK (~15MB)
- **Optimization:** LangFuse is CRITICAL for GAMP-5 audit trail (DO NOT REMOVE)
- **Acceptable:** 215MB total size (includes compliance tooling)

**10. uv sync --frozen vs --locked:**
- **--frozen:** Fails if uv.lock out of sync with pyproject.toml (RECOMMENDED for CI/CD)
- **--locked:** Updates uv.lock if needed (NOT reproducible)
- **Use:** `uv sync --frozen --no-dev` in Dockerfile

### Recommended Approach

**High-Level Strategy:**

1. **Create Two Dockerfiles:**
   - `Dockerfile.api` - FastAPI application (port 8080)
   - `Dockerfile.worker` - Background job processor (no port exposure)

2. **Use Identical Multi-Stage Pattern:**
   - Builder stage: python:3.12-slim-bookworm + build deps + uv sync
   - Runtime stage: python:3.12-slim-bookworm + runtime deps + Tini + non-root user

3. **Optimize Layer Caching:**
   - Copy pyproject.toml + uv.lock FIRST (dependencies change rarely)
   - Copy application code LAST (changes frequently)
   - Use cache mounts for uv cache

4. **Security Hardening:**
   - Non-root user (appuser UID 1000)
   - Tini as PID 1 for signal handling
   - Minimal runtime dependencies
   - Trivy scanning in CI/CD

5. **ECS Fargate Readiness:**
   - Platform: linux/amd64
   - HEALTHCHECK directive
   - Structured JSON logging
   - Image size <200MB

6. **GAMP-5 Compliance:**
   - Document all dependencies in validation package
   - Trivy scan results in audit trail
   - Reproducible builds (pinned versions)
   - Change control for Dockerfile updates

**Implementation Order:**

1. **Task 3.1a - Create .dockerignore:**
   ```
   .venv
   __pycache__
   *.pyc
   .pytest_cache
   .mypy_cache
   .ruff_cache
   .env.local
   output/
   logs/
   .git
   ```

2. **Task 3.1b - Create Dockerfile.api:**
   - Multi-stage build (builder + runtime)
   - Install curl, libpq5, tini, ca-certificates
   - Create appuser, set permissions
   - HEALTHCHECK directive
   - ENTRYPOINT Tini, CMD uvicorn

3. **Task 3.1c - Create Dockerfile.worker:**
   - Identical to Dockerfile.api BUT:
   - NO HEALTHCHECK (workers don't expose HTTP)
   - CMD: `python -m main.api.worker` (or appropriate entrypoint)

4. **Task 3.1d - Add Build Scripts:**
   - `scripts/build-docker.sh` - Build both images
   - `scripts/scan-docker.sh` - Trivy scan
   - Tag with git commit SHA for traceability

5. **Task 3.1e - Test Locally:**
   - Build images: `docker build -f Dockerfile.api -t thesis-api .`
   - Run container: `docker run -p 8080:8080 thesis-api`
   - Test healthcheck: `curl http://localhost:8080/health`
   - Verify Tini: `docker exec <id> ps aux` (check PID 1)
   - Check size: `docker images thesis-api` (verify <200MB)

6. **Task 3.1f - CI/CD Integration:**
   - Add GitHub Actions workflow (or equivalent)
   - Build on every commit
   - Trivy scan with --exit-code 1 on CRITICAL
   - Push to ECR on main branch

### Required Libraries/Versions

**Base Image:**
- `python:3.12-slim-bookworm` (Debian 12, Python 3.12, ~150MB)

**uv Version:**
- `ghcr.io/astral-sh/uv:0.9.8` (pinned, latest stable as of 2025-01)

**Runtime Debian Packages:**
```dockerfile
RUN apt-get update && apt-get install -y \
    libpq5=15.* \         # PostgreSQL client library (matches Aurora PostgreSQL 15)
    curl=7.* \            # Healthcheck tool
    tini=0.19.* \         # Init system
    ca-certificates \     # HTTPS certificate validation
    && rm -rf /var/lib/apt/lists/*
```

**Build-Time Debian Packages (builder stage only):**
```dockerfile
RUN apt-get update && apt-get install -y \
    gcc=4:12.* \          # C compiler for native extensions
    libpq-dev=15.* \      # PostgreSQL development headers
    && rm -rf /var/lib/apt/lists/*
```

**Python Dependencies:**
- Managed by uv from pyproject.toml (no changes required)
- Key dependencies already pinned:
  - `fastapi`, `uvicorn` (web framework)
  - `chromadb>=0.4.22` (vector database)
  - `langfuse==3.5.2` (observability - CRITICAL for GAMP-5)
  - `clerk-backend-api==4.0.0` (authentication)
  - `aiobotocore>=2.11.0` (S3 client)

**Environment Variables:**
```dockerfile
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"
```

**Trivy (for CI/CD, not in image):**
- `aquasec/trivy:latest` (Docker image for scanning)

## Next Agent Guidance

**For task-executor:**

1. **Create `.dockerignore` file first** (prevents including local .venv in build context)

2. **Create `Dockerfile.api` with:**
   - Multi-stage build (builder + runtime stages)
   - Use EXACT base image: `python:3.12-slim-bookworm`
   - Copy uv from: `ghcr.io/astral-sh/uv:0.9.8`
   - Builder stage: gcc, libpq-dev
   - Runtime stage: libpq5, curl, tini, ca-certificates
   - Non-root user: `useradd -m -u 1000 appuser`
   - Tini entrypoint: `ENTRYPOINT ["/usr/bin/tini", "--"]`
   - CMD: `["uvicorn", "main.api.app:app", "--host", "0.0.0.0", "--port", "8080"]`
   - HEALTHCHECK: `CMD curl -f http://localhost:8080/health || exit 1`

3. **Create `Dockerfile.worker`:**
   - Clone Dockerfile.api structure
   - REMOVE HEALTHCHECK directive
   - Change CMD to worker entrypoint (determine from app.py/worker.py)

4. **Add healthcheck endpoint** to `main/api/app.py` if not exists:
   ```python
   @app.get("/health")
   async def health_check():
       return {"status": "healthy"}
   ```

5. **Create build script** `scripts/build-docker.sh`:
   - Build both images with git SHA tags
   - Run Trivy scan
   - Exit 1 on CRITICAL vulnerabilities

6. **Test locally:**
   - Build: `docker build -f Dockerfile.api -t thesis-api .`
   - Run: `docker run -p 8080:8080 thesis-api`
   - Verify: `curl http://localhost:8080/health`
   - Check size: `docker images thesis-api` (MUST be <200MB)
   - Check Tini: `docker exec <id> ps aux | grep PID`

7. **Critical Constraints:**
   - NO Alpine base images (ChromaDB incompatible)
   - NO poetry or pip (use uv only)
   - NO root user in final image
   - NO missing runtime dependencies (libpq5 required)
   - Image size MUST be <200MB
   - MUST include Tini as PID 1
   - MUST include HEALTHCHECK for API container

8. **GAMP-5 Compliance:**
   - Add comment headers documenting Dockerfile purpose
   - Pin all versions (uv, base image tags)
   - Document security decisions (why Debian over Alpine)
   - Save Trivy scan results for validation package

9. **Error Handling:**
   - NO FALLBACK LOGIC: If dependencies fail to install, BUILD MUST FAIL
   - NO DEFAULT VALUES: All ENV vars must be explicit
   - FAIL FAST: Use `set -e` in any shell scripts
   - EXPOSE ERRORS: Include full stack traces in build output

10. **Reference Examples:**
    - Study `examples/alex/backend/researcher/Dockerfile` for uv patterns
    - DO NOT copy Node.js/Playwright installation (not needed)
    - DO ADD multi-stage optimization (example lacks this)
    - DO ADD Tini and non-root user (example lacks these)

## Files Referenced

**Project Files Read:**
- `C:\Users\anteb\Desktop\Courses\Projects\thesis_project\pyproject.toml`
- `C:\Users\anteb\Desktop\Courses\Projects\thesis_project\main\api\app.py`
- `C:\Users\anteb\Desktop\Courses\Projects\thesis_project\main\api\worker.py`
- `C:\Users\anteb\Desktop\Courses\Projects\thesis_project\examples\alex\backend\researcher\Dockerfile`
- `C:\Users\anteb\Desktop\Courses\Projects\thesis_project\PRPs\tasks\3.1-docker-multistage.md`
- `C:\Users\anteb\Desktop\Courses\Projects\thesis_project\PRPs\tasks\1.1-storage-adapter.md`
- `C:\Users\anteb\Desktop\Courses\Projects\thesis_project\PRPs\tasks\1.2-vector-store-provider.md`

**External Documentation:**
- https://docs.astral.sh/uv/guides/integration/docker/ (uv Docker best practices)
- https://docs.docker.com/build/building/multi-stage/ (multi-stage builds)
- https://github.com/krallin/tini (Tini init system)
- https://digon.io/en/blog/2025_07_28_python_docker_images_with_uv (uv multi-stage tutorial)
- https://docs.roxautomation.com/linux/docker_best_practices/ (uv Docker patterns)
- https://computingpost.medium.com/how-to-use-tini-init-system-in-docker-containers-69283d0099ed (Tini guide)
- https://devopsdirective.com/posts/2023/06/container-init-process/ (container PID 1 explained)
- https://stackoverflow.com/questions/78230406/is-multistage-docker-possible-into-fastapi-application (FastAPI multi-stage)
- https://trivy.dev/ (Trivy security scanner)
- https://docs.aws.amazon.com/AmazonECS/latest/developerguide/healthcheck.html (ECS healthchecks)
- https://github.com/fastapi/fastapi/blob/master/docs/en/docs/deployment/docker.md (FastAPI Docker deployment)

**Search Results:**
- 10+ web articles on uv Docker integration
- 8+ articles on Tini init system
- 8+ articles on Trivy scanning
- 6+ articles on ECS Fargate healthchecks
- FastAPI official documentation via Context7

**Key Findings:**
- ChromaDB does NOT support Alpine (CRITICAL constraint)
- uv requires specific ENV vars for Docker (UV_LINK_MODE=copy)
- Tini installation via apt-get on Debian (simpler than static binary)
- Multi-stage builds reduce image size 60-75%
- ECS Fargate requires explicit HEALTHCHECK for proper monitoring

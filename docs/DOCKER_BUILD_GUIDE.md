# Docker Multi-Stage Build Guide

**GAMP-5 Compliant Container Deployment for Pharmaceutical Test Generation**

---

## Overview

This guide covers building, testing, and deploying Docker containers for the pharmaceutical test generation system with AWS ECS Fargate deployment.

### Architecture

- **API Container** (`Dockerfile.api`): FastAPI application with job submission endpoints
- **Worker Container** (`Dockerfile.worker`): Background job processor for test generation workflows
- **Base Image**: `python:3.12-slim-bookworm` (Debian 12, ~150MB)
- **Target Size**: <200MB per container
- **Platform**: `linux/amd64` (AWS ECS Fargate requirement)

### Compliance Requirements

**GAMP-5:**
- Reproducible builds via pinned versions
- Non-root user execution (security control)
- Tini init system for graceful shutdown (data integrity)
- Healthcheck for system monitoring (audit trail)

**ALCOA+:**
- Attributable: Non-root user UID 1000 (`appuser`)
- Contemporaneous: Tini ensures graceful shutdown preserves in-flight transactions
- Complete: Healthcheck prevents incomplete system startup
- Accurate: Image tagged with git SHA for traceability

---

## Prerequisites

### Required Tools

1. **Docker Desktop** (with BuildKit enabled)
   ```bash
   # Verify Docker version
   docker --version  # Requires Docker 20.10+ for BuildKit
   ```

2. **Git** (for commit SHA tagging)
   ```bash
   git --version
   ```

3. **Trivy** (security scanning - optional but recommended)
   ```bash
   # macOS
   brew install trivy

   # Linux (Debian/Ubuntu)
   apt-get install trivy

   # Windows (via Docker)
   docker run aquasec/trivy --version
   ```

### Environment Setup

Ensure `.env.local` exists in project root with required credentials:
```bash
# LangFuse observability
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com

# Clerk authentication
CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...

# OpenRouter API (DeepSeek V3)
OPENROUTER_API_KEY=sk-or-...
```

**Note:** Environment variables are NOT baked into images (security). Pass at runtime via ECS task definition.

---

## Building Images

### Quick Start

```bash
# Build both containers
./scripts/build-docker.sh

# Images created:
# - thesis-api:latest, thesis-api:<git-sha>
# - thesis-worker:latest, thesis-worker:<git-sha>
```

### Manual Build

```bash
# Enable BuildKit (required for cache mounts)
export DOCKER_BUILDKIT=1

# Build API container
docker build \
  --platform=linux/amd64 \
  -f Dockerfile.api \
  -t thesis-api:latest \
  .

# Build worker container
docker build \
  --platform=linux/amd64 \
  -f Dockerfile.worker \
  -t thesis-worker:latest \
  .
```

### Build Performance

**Layer Caching Strategy:**
1. `pyproject.toml` + `uv.lock` → Install dependencies (cached unless dependencies change)
2. Application code → Copy code (invalidates on every change)

**Cache Mount Benefits:**
- First build: ~5 minutes (download all dependencies)
- Incremental rebuild (code change only): ~30 seconds
- Incremental rebuild (dependency change): ~2 minutes

**Size Optimization:**
- Multi-stage build reduces image size 60-75%
- Single-stage: ~500-800MB
- Multi-stage: ~180-220MB

---

## Testing Containers

### Local Testing (API Container)

```bash
# Run API container
docker run -d \
  --name thesis-api-test \
  -p 8080:8080 \
  --env-file .env.local \
  thesis-api:latest

# Test healthcheck endpoint
curl http://localhost:8080/health

# Expected response:
# {"status":"healthy","service":"pharmaceutical-test-generation-api","version":"1.0.0"}

# Test root endpoint
curl http://localhost:8080/

# Check logs
docker logs thesis-api-test

# Verify Tini is PID 1 (proper init system)
docker exec thesis-api-test ps aux | head -2

# Expected:
# USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
# appuser      1  0.0  0.0   2304   752 ?        Ss   00:00   0:00 /usr/bin/tini -- ...

# Stop and remove container
docker stop thesis-api-test
docker rm thesis-api-test
```

### Local Testing (Worker Container)

```bash
# Run worker container
docker run -d \
  --name thesis-worker-test \
  --env-file .env.local \
  thesis-worker:latest

# Check worker logs (should show "Background job worker started")
docker logs thesis-worker-test

# Verify Tini is PID 1
docker exec thesis-worker-test ps aux | head -2

# Stop and remove container
docker stop thesis-worker-test
docker rm thesis-worker-test
```

### Image Size Verification

```bash
# Check image sizes
docker images | grep thesis

# Expected output:
# thesis-api      latest   <image-id>   2 minutes ago   180-220MB
# thesis-worker   latest   <image-id>   1 minute ago    180-220MB
```

**If images exceed 200MB:**
1. Check for unnecessary files in `.dockerignore`
2. Verify `rm -rf /var/lib/apt/lists/*` runs after `apt-get`
3. Ensure `--no-install-recommends` used with `apt-get install`
4. Verify dev dependencies excluded (`uv sync --no-dev`)

---

## Security Scanning

### Trivy Scan (Recommended)

```bash
# Scan for vulnerabilities
./scripts/scan-docker.sh

# Scan with CI/CD mode (fail on CRITICAL)
./scripts/scan-docker.sh --fail-on-critical
```

**Scan reports saved to:**
- `logs/trivy/api-scan-<timestamp>.json`
- `logs/trivy/worker-scan-<timestamp>.json`

### Interpreting Scan Results

**CRITICAL Vulnerabilities:**
- **Action:** Remediate before deployment (update base image or dependencies)
- **Documentation:** Record in GAMP-5 validation package if no patch available

**HIGH Vulnerabilities:**
- **Action:** Assess risk and document justification if deployment required
- **Timeline:** Remediate in next release cycle

**Unfixed Vulnerabilities:**
```bash
# Show only vulnerabilities with patches available
trivy image --ignore-unfixed thesis-api:latest
```

### License Compliance (ALCOA+)

```bash
# Scan for license issues
trivy image --scanners license thesis-api:latest

# Check for GPL/AGPL dependencies (not allowed in proprietary systems)
trivy image --scanners license --severity HIGH,CRITICAL thesis-api:latest
```

**Required Documentation:**
- List all third-party licenses in validation package
- Verify no GPL/AGPL dependencies in production code
- Document acceptable licenses (MIT, Apache 2.0, BSD)

---

## Deployment to AWS ECR

### Prerequisites

1. **AWS CLI configured:**
   ```bash
   aws configure
   # OR use environment variables:
   export AWS_ACCESS_KEY_ID=...
   export AWS_SECRET_ACCESS_KEY=...
   export AWS_DEFAULT_REGION=eu-west-2
   ```

2. **ECR repositories created** (Task 4.1):
   ```bash
   aws ecr describe-repositories --repository-names thesis-api thesis-worker
   ```

### Push to ECR

```bash
# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.eu-west-2.amazonaws.com"

# Authenticate Docker to ECR
aws ecr get-login-password --region eu-west-2 | \
  docker login --username AWS --password-stdin ${ECR_REGISTRY}

# Tag images for ECR
GIT_SHA=$(git rev-parse --short HEAD)
docker tag thesis-api:latest ${ECR_REGISTRY}/thesis-api:latest
docker tag thesis-api:latest ${ECR_REGISTRY}/thesis-api:${GIT_SHA}
docker tag thesis-worker:latest ${ECR_REGISTRY}/thesis-worker:latest
docker tag thesis-worker:latest ${ECR_REGISTRY}/thesis-worker:${GIT_SHA}

# Push to ECR
docker push ${ECR_REGISTRY}/thesis-api:latest
docker push ${ECR_REGISTRY}/thesis-api:${GIT_SHA}
docker push ${ECR_REGISTRY}/thesis-worker:latest
docker push ${ECR_REGISTRY}/thesis-worker:${GIT_SHA}
```

### Verify ECR Upload

```bash
# List images in ECR
aws ecr describe-images --repository-name thesis-api
aws ecr describe-images --repository-name thesis-worker

# Check image size in ECR
aws ecr describe-images \
  --repository-name thesis-api \
  --image-ids imageTag=latest \
  --query 'imageDetails[0].imageSizeInBytes' \
  --output text | awk '{print $1/1024/1024 " MB"}'
```

---

## ECS Fargate Configuration

### Task Definition (Terraform - Task 4.1)

**API Container:**
```hcl
resource "aws_ecs_task_definition" "api" {
  family                   = "thesis-api"
  requires_compatibilities = ["FARGATE"]
  network_mode            = "awsvpc"
  cpu                     = 2048  # 2 vCPU
  memory                  = 4096  # 4 GB

  container_definitions = jsonencode([{
    name  = "api"
    image = "${aws_ecr_repository.api.repository_url}:latest"

    portMappings = [{
      containerPort = 8080
      protocol      = "tcp"
    }]

    environment = []  # No secrets in plain text

    secrets = [
      { name = "LANGFUSE_PUBLIC_KEY", valueFrom = "${aws_secretsmanager_secret.langfuse.arn}:public_key::" },
      { name = "LANGFUSE_SECRET_KEY", valueFrom = "${aws_secretsmanager_secret.langfuse.arn}:secret_key::" },
      # ... other secrets
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = "/ecs/thesis-api"
        "awslogs-region"        = "eu-west-2"
        "awslogs-stream-prefix" = "api"
      }
    }

    healthCheck = {
      command     = ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 10
    }
  }])
}
```

**Worker Container:**
```hcl
resource "aws_ecs_task_definition" "worker" {
  family                   = "thesis-worker"
  requires_compatibilities = ["FARGATE"]
  network_mode            = "awsvpc"
  cpu                     = 4096  # 4 vCPU
  memory                  = 8192  # 8 GB

  container_definitions = jsonencode([{
    name  = "worker"
    image = "${aws_ecr_repository.worker.repository_url}:latest"

    # No port mappings (worker doesn't expose HTTP)

    environment = []
    secrets     = [/* same as API */]

    logConfiguration = {/* same as API */}

    # No healthCheck for workers
  }])
}
```

### Key Differences API vs Worker

| Configuration | API | Worker |
|--------------|-----|--------|
| CPU | 2 vCPU | 4 vCPU |
| Memory | 4 GB | 8 GB |
| Port | 8080 | None |
| Healthcheck | ✅ Yes | ❌ No |
| Load Balancer | ✅ Yes | ❌ No |

---

## Troubleshooting

### Image Build Fails

**Error:** `unknown flag: --mount`
- **Cause:** BuildKit not enabled
- **Solution:** `export DOCKER_BUILDKIT=1`

**Error:** `libpq.so.5: cannot open shared object`
- **Cause:** Missing runtime dependency `libpq5`
- **Solution:** Verify `libpq5` in runtime stage `apt-get install`

**Error:** `ChromaDB incompatible with Alpine`
- **Cause:** Using Alpine base image
- **Solution:** Use `python:3.12-slim-bookworm` (Debian-based)

### Healthcheck Fails

**Error:** `Connection refused`
- **Cause:** Port mismatch (healthcheck vs CMD)
- **Solution:** Both must use port 8080

**Error:** `curl: command not found`
- **Cause:** `curl` not installed in runtime stage
- **Solution:** Add `curl` to `apt-get install`

### Container Crashes on Startup

**Check logs:**
```bash
docker logs <container-id>
```

**Common causes:**
- Missing environment variables (`.env.local` not passed)
- Permission denied (user `appuser` can't write to `/app`)
- Module import errors (dependency missing from `pyproject.toml`)

**Fix permissions:**
```dockerfile
COPY --from=builder --chown=appuser:appuser /app /app
```

### Tini Not Running as PID 1

**Verify:**
```bash
docker exec <container> ps aux | grep PID
```

**Expected:** Tini is PID 1, application is child process

**If shell script is PID 1:**
- Use exec form: `ENTRYPOINT ["/usr/bin/tini", "--"]`
- NOT shell form: `ENTRYPOINT /usr/bin/tini --`

---

## Best Practices

### Development Workflow

1. **Local iteration:**
   ```bash
   # Rebuild after code changes
   docker build -f Dockerfile.api -t thesis-api:dev .
   docker run -p 8080:8080 --env-file .env.local thesis-api:dev
   ```

2. **Tag with git SHA:**
   ```bash
   GIT_SHA=$(git rev-parse --short HEAD)
   docker build -f Dockerfile.api -t thesis-api:${GIT_SHA} .
   ```

3. **Test before push:**
   ```bash
   ./scripts/scan-docker.sh --fail-on-critical
   ```

### CI/CD Integration (GitHub Actions)

```yaml
name: Docker Build and Scan

on:
  push:
    branches: [main, backend]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Build API image
        run: |
          docker build \
            --platform=linux/amd64 \
            -f Dockerfile.api \
            -t thesis-api:${{ github.sha }} \
            .

      - name: Build worker image
        run: |
          docker build \
            --platform=linux/amd64 \
            -f Dockerfile.worker \
            -t thesis-worker:${{ github.sha }} \
            .

      - name: Run Trivy scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: thesis-api:${{ github.sha }}
          severity: CRITICAL,HIGH
          exit-code: 1  # Fail on CRITICAL

      - name: Push to ECR (if main branch)
        if: github.ref == 'refs/heads/main'
        run: |
          # ECR push commands here
```

### GAMP-5 Validation Checklist

- [ ] Image tagged with git commit SHA
- [ ] Trivy scan results saved to `logs/trivy/`
- [ ] No CRITICAL vulnerabilities (or documented exceptions)
- [ ] License compliance verified (no GPL/AGPL)
- [ ] Image size <200MB
- [ ] Non-root user execution verified
- [ ] Tini running as PID 1
- [ ] Healthcheck endpoint tested
- [ ] ECR image URI recorded in change control

---

## References

### Official Documentation
- [Docker Multi-Stage Builds](https://docs.docker.com/build/building/multi-stage/)
- [uv Docker Integration](https://docs.astral.sh/uv/guides/integration/docker/)
- [Tini Init System](https://github.com/krallin/tini)
- [Trivy Security Scanner](https://trivy.dev/)
- [AWS ECS Fargate](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html)

### Project-Specific
- [AWS Migration PRP](../PRPs/aws-migration-updated.md)
- [Quick Start Guide](./guides/QUICK_START_GUIDE.md)
- [Task 4.1 - ECS Deployment](../PRPs/tasks/4.1-ecs-deployment.md)

---

**Last Updated:** 2025-01-11
**Version:** 1.0
**Task:** P3.1 - Optimize Docker Multi-Stage Build

# Docker Build Optimization Guide

Strategies for faster builds, smaller images, and efficient layer caching.

## Table of Contents

1. [Layer Caching Strategies](#layer-caching-strategies)
2. [Multi-Stage Builds](#multi-stage-builds)
3. [.dockerignore Optimization](#dockerignore-optimization)
4. [Image Size Reduction](#image-size-reduction)
5. [Build Performance](#build-performance)
6. [Advanced Techniques](#advanced-techniques)

---

## Layer Caching Strategies

### How Layer Caching Works

Docker caches each layer (instruction in Dockerfile). If a layer and everything before it haven't changed, Docker reuses the cached layer.

**Cache Invalidation**: Any change invalidates that layer and all subsequent layers.

```dockerfile
# Bad: Changes frequently, invalidates all subsequent layers
COPY . /app
RUN pip install -r requirements.txt

# Good: Stable dependencies cached, code changes don't invalidate dependency layer
COPY requirements.txt /app/
RUN pip install -r requirements.txt
COPY . /app
```

### Principle: Order by Change Frequency

**Least frequently changing → Most frequently changing**

```dockerfile
FROM python:3.12-slim

# 1. System packages (rarely change)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 2. Application dependencies (change occasionally)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Application code (changes frequently)
COPY . /app/

# 4. Runtime configuration (may change)
CMD ["python", "app.py"]
```

### Dependency Management

**Python**:
```dockerfile
# Install dependencies before copying code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Then copy code
COPY . .
```

**Node.js**:
```dockerfile
# Install dependencies before copying code
COPY package.json package-lock.json ./
RUN npm ci --only=production

# Then copy code
COPY . .
```

**Go**:
```dockerfile
# Download modules before copying code
COPY go.mod go.sum ./
RUN go mod download

# Then copy code
COPY . .
```

### Cache Mounts (BuildKit)

**Advanced**: Mount cache directories across builds

```dockerfile
# Enable BuildKit
# DOCKER_BUILDKIT=1 docker build -t image .

FROM python:3.12

# Cache pip packages across builds
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Cache apt packages across builds
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && apt-get install -y package
```

---

## Multi-Stage Builds

### Concept

Use multiple `FROM` statements to separate build and runtime environments, keeping only necessary artifacts in final image.

### Basic Multi-Stage Build

```dockerfile
# Stage 1: Build (includes build tools, source code)
FROM python:3.12 AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt
COPY . .

# Stage 2: Runtime (minimal, production-ready)
FROM python:3.12-slim
WORKDIR /app

# Copy only built artifacts
COPY --from=builder /root/.local /root/.local
COPY --from=builder /app /app

# Update PATH
ENV PATH=/root/.local/bin:$PATH

CMD ["python", "app.py"]
```

**Benefits**:
- Final image: **500 MB** (slim base + dependencies)
- Without multi-stage: **1.2 GB** (full base + build tools)

### Advanced Multi-Stage Patterns

**Pattern 1: Separate Build and Test Stages**

```dockerfile
# Build stage
FROM python:3.12 AS builder
COPY requirements.txt .
RUN pip install --user -r requirements.txt
COPY . .

# Test stage (not included in final image)
FROM builder AS tester
RUN pip install --user pytest
RUN pytest tests/

# Production stage
FROM python:3.12-slim
COPY --from=builder /root/.local /root/.local
COPY --from=builder /app /app
CMD ["python", "app.py"]
```

```bash
# Build with testing
docker build --target tester -t image:test .

# Build production (skips test stage)
docker build -t image:prod .
```

**Pattern 2: Multi-Platform Builds**

```dockerfile
# Use build platform for compilation (fast)
FROM --platform=${BUILDPLATFORM} node:18 AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Use target platform for runtime
FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/dist ./dist
CMD ["node", "dist/server.js"]
```

**Pattern 3: Shared Dependencies**

```dockerfile
# Base dependencies
FROM python:3.12 AS base
RUN pip install --user common-package

# Development build
FROM base AS development
RUN pip install --user dev-packages
COPY . .
CMD ["python", "dev_server.py"]

# Production build
FROM base AS production
RUN pip install --user prod-packages
COPY --from=development /app /app
CMD ["python", "prod_server.py"]
```

---

## .dockerignore Optimization

### Purpose

Exclude unnecessary files from build context to:
- Reduce context upload time
- Prevent accidental inclusion of secrets
- Improve cache efficiency

### Essential .dockerignore Template

```gitignore
# Version control
.git
.gitignore
.gitattributes

# CI/CD
.github
.gitlab-ci.yml
Jenkinsfile

# Documentation
*.md
README.md
docs/
CHANGELOG

# Python
__pycache__/
*.py[cod]
*$py.class
.Python
.venv
venv/
ENV/
env/
.pytest_cache/
.coverage
htmlcov/
*.egg-info/
dist/
build/

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Environment
.env
.env.*
*.local

# Docker
Dockerfile*
docker-compose*.yml
.dockerignore

# Build artifacts
*.log
*.tmp
temp/
tmp/

# Data files (if large)
data/
datasets/
*.csv
*.db
*.sqlite

# Test files (if not needed in image)
tests/
test_*.py

# Large binaries
*.tar
*.zip
*.gz
```

### Performance Impact

```bash
# Without .dockerignore
Sending build context to Docker daemon  2.5GB
Build time: 180 seconds

# With .dockerignore
Sending build context to Docker daemon  45MB
Build time: 30 seconds

# 6x faster context upload
# 6x faster build
```

---

## Image Size Reduction

### Technique 1: Use Minimal Base Images

```dockerfile
# Large: 1.1 GB
FROM python:3.12

# Medium: 450 MB
FROM python:3.12-slim

# Small: 150 MB (Python + Alpine)
FROM python:3.12-alpine

# Smallest: 50 MB (distroless)
FROM gcr.io/distroless/python3:latest
```

**Trade-offs**:
- `full`: All tools, easy debugging
- `slim`: Minimal GNU tools, good balance
- `alpine`: Smallest, musl libc (may cause compatibility issues)
- `distroless`: No shell, maximum security, hardest to debug

### Technique 2: Combine RUN Commands

```dockerfile
# Bad: Each RUN creates a layer
RUN apt-get update
RUN apt-get install -y package1
RUN apt-get install -y package2
RUN apt-get clean
# 4 layers

# Good: Single RUN command
RUN apt-get update && \
    apt-get install -y \
      package1 \
      package2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
# 1 layer
```

### Technique 3: Remove Build Dependencies

```dockerfile
# Install build deps, compile, remove build deps in same layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      gcc \
      && pip install package \
    && apt-get purge -y \
      build-essential \
      gcc \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*
```

### Technique 4: Use --no-cache-dir

```dockerfile
# Python: Don't cache pip packages in image
RUN pip install --no-cache-dir -r requirements.txt

# Node.js: Don't cache npm packages
RUN npm ci --only=production && npm cache clean --force

# apt: Clean up after install
RUN apt-get update && \
    apt-get install -y package && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
```

### Image Size Comparison

```dockerfile
# Example: Python FastAPI application

# Approach 1: Naive (1.2 GB)
FROM python:3.12
COPY . .
RUN pip install -r requirements.txt
CMD ["uvicorn", "main:app"]

# Approach 2: Optimized single-stage (450 MB)
FROM python:3.12-slim
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app"]

# Approach 3: Multi-stage (200 MB)
FROM python:3.12 AS builder
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.12-slim
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["uvicorn", "main:app"]

# Approach 4: Distroless (150 MB, most secure)
FROM python:3.12 AS builder
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM gcr.io/distroless/python3
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PYTHONPATH=/root/.local/lib/python3.12/site-packages
CMD ["main.py"]
```

---

## Build Performance

### Technique 1: Parallel Builds with BuildKit

```bash
# Enable BuildKit (parallel stage execution)
export DOCKER_BUILDKIT=1
docker build -t image:tag .

# Or inline
DOCKER_BUILDKIT=1 docker build -t image:tag .
```

**Benefits**:
- Parallel stage execution
- Improved caching
- Build secrets support
- SSH forwarding

### Technique 2: Build Cache

```bash
# Build with inline cache
docker build --cache-from image:latest -t image:new .

# Push with cache
docker build --cache-from image:latest -t image:new --push .

# BuildKit cache backend
docker buildx build \
  --cache-from type=registry,ref=user/image:cache \
  --cache-to type=registry,ref=user/image:cache,mode=max \
  -t user/image:latest \
  .
```

### Technique 3: Resource Limits

```bash
# Increase build resources
docker build --memory 4g --cpu-shares 1024 -t image:tag .
```

### Build Time Optimization Checklist

- [ ] Use multi-stage builds
- [ ] Order Dockerfile by change frequency
- [ ] Copy only necessary files with .dockerignore
- [ ] Combine RUN commands to reduce layers
- [ ] Use --no-cache-dir for package managers
- [ ] Enable BuildKit for parallel execution
- [ ] Use cache-from for CI/CD pipelines
- [ ] Build on native platform (avoid emulation)

---

## Advanced Techniques

### Technique 1: Build Secrets

```dockerfile
# Avoid committing secrets
# Use build secrets (BuildKit)

# In Dockerfile
RUN --mount=type=secret,id=mysecret \
    SECRET=$(cat /run/secrets/mysecret) && \
    curl -H "Authorization: Bearer $SECRET" https://api.example.com/data
```

```bash
# Build with secret
docker build --secret id=mysecret,src=./secret.txt -t image:tag .

# Secret is not in final image
```

### Technique 2: SSH Agent Forwarding

```dockerfile
# Use SSH keys during build without including them in image
RUN --mount=type=ssh \
    git clone git@github.com:user/private-repo.git
```

```bash
# Build with SSH
docker build --ssh default -t image:tag .
```

### Technique 3: Build Context from Git

```bash
# Build directly from Git (no local clone needed)
docker build -t image:tag https://github.com/user/repo.git#branch

# Build from tarball
docker build -t image:tag https://example.com/context.tar.gz
```

### Technique 4: Heredoc Syntax (BuildKit)

```dockerfile
# Create multiple files in single RUN
RUN <<EOF
cat > /etc/config.conf
key1=value1
key2=value2
EOF

RUN <<EOF
#!/bin/bash
apt-get update
apt-get install -y package
apt-get clean
EOF
```

---

## Optimization Metrics

### Measuring Build Performance

```bash
# Measure build time
time docker build -t image:tag .

# Show layer sizes
docker history image:tag

# Show total image size
docker images image:tag

# Show detailed size breakdown
docker history --no-trunc --human image:tag
```

### Target Metrics

| Metric | Target | Notes |
|--------|--------|-------|
| Build time | < 5 min | For active development |
| Image size | < 500 MB | For typical web apps |
| Layers | < 20 | Fewer layers = better caching |
| Context size | < 100 MB | Faster uploads |

---

## Complete Optimized Dockerfile Example

```dockerfile
# syntax=docker/dockerfile:1

# ===== Build Stage =====
FROM python:3.12 AS builder

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --user --no-cache-dir -r requirements.txt

# ===== Test Stage (optional) =====
FROM builder AS tester
COPY . .
RUN pip install --user pytest && pytest tests/

# ===== Production Stage =====
FROM python:3.12-slim

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser

# Copy dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
WORKDIR /app
COPY --chown=appuser:appuser . .

# Set environment
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Results**:
- Build time: 2 minutes (with cache: 10 seconds)
- Image size: 250 MB
- Layers: 12
- Security: Non-root user, minimal base, no build tools

---

**Key Takeaways**:
- Order Dockerfile by change frequency (dependencies before code)
- Use multi-stage builds to separate build and runtime
- Use .dockerignore to reduce context size
- Combine RUN commands to reduce layers
- Use slim or distroless base images
- Enable BuildKit for parallel execution
- Cache dependencies separately from code
- Build on native platform when possible

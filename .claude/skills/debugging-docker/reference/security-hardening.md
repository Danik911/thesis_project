# Docker Security Hardening Guide

Best practices for secure Docker container deployment with focus on pharmaceutical compliance contexts.

## Table of Contents

1. [Non-Root User Execution](#non-root-user-execution)
2. [Secret Management](#secret-management)
3. [Base Image Security](#base-image-security)
4. [Resource Limits](#resource-limits)
5. [Network Security](#network-security)
6. [Volume Security](#volume-security)
7. [Compliance & Auditing](#compliance--auditing)

---

## Non-Root User Execution

### Why Run as Non-Root?

**Risk**: Root user in container = root access to host if container escapes

**Best Practice**: Always create and use a dedicated non-root user

### Method 1: Create User in Dockerfile

```dockerfile
# Create non-root user
FROM python:3.12-slim

# Create user with specific UID/GID
RUN groupadd -r appuser -g 1000 && \
    useradd -r -u 1000 -g appuser appuser

# Create app directory with correct ownership
RUN mkdir -p /app && chown -R appuser:appuser /app

WORKDIR /app

# Install dependencies as root (if needed)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code with correct ownership
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

CMD ["python", "app.py"]
```

### Method 2: Minimal User Creation

```dockerfile
FROM python:3.12-slim

# Create minimal user (no home directory)
RUN adduser --disabled-password --gecos '' --no-create-home appuser

WORKDIR /app
COPY --chown=appuser:appuser . .

USER appuser
CMD ["python", "app.py"]
```

### Method 3: Alpine Linux

```dockerfile
FROM python:3.12-alpine

# Alpine uses adduser (different syntax)
RUN adduser -D -u 1000 appuser

WORKDIR /app
COPY --chown=appuser:appuser . .

USER appuser
CMD ["python", "app.py"]
```

### Running with User Override

```bash
# Run with specific user at runtime
docker run --user 1000:1000 image:tag

# Run with current user (Linux/WSL2)
docker run --user $(id -u):$(id -g) image:tag
```

### Permission Issues with Non-Root

**Problem**: Non-root user can't write to volumes

**Solution 1: Match host user ID**
```dockerfile
# Create user with same UID as host
RUN adduser -u 1000 -D appuser
USER appuser
```

```bash
# Run with host user
docker run --user $(id -u):$(id -g) -v /host/data:/app/data image:tag
```

**Solution 2: Fix volume permissions**
```bash
# On host, set correct ownership
sudo chown -R 1000:1000 /host/data

# Or make writable by all (not recommended)
sudo chmod -R 777 /host/data
```

---

## Secret Management

### Never Include Secrets in Images

**Bad Practices**:
```dockerfile
# NEVER do this
ENV API_KEY=secret123
COPY .env /app/.env
RUN echo "password=secret" > /app/config
```

**Why Bad**: Secrets remain in image layers even if deleted later

### Method 1: Environment Variables (Runtime)

```bash
# Pass secrets at runtime
docker run -e API_KEY=secret123 image:tag

# From file
docker run --env-file .env image:tag

# From host environment
docker run -e API_KEY=$API_KEY image:tag
```

**.env file**:
```
API_KEY=secret123
DB_PASSWORD=password456
```

### Method 2: Docker Secrets (Swarm/Compose)

```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    image: app:latest
    secrets:
      - api_key
      - db_password
    environment:
      API_KEY_FILE: /run/secrets/api_key
      DB_PASSWORD_FILE: /run/secrets/db_password

secrets:
  api_key:
    file: ./secrets/api_key.txt
  db_password:
    file: ./secrets/db_password.txt
```

**In application**:
```python
# Read secret from file
with open(os.getenv('API_KEY_FILE'), 'r') as f:
    api_key = f.read().strip()
```

### Method 3: Build Secrets (BuildKit)

```dockerfile
# Use secret during build without including in image
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc \
    npm install private-package

RUN --mount=type=secret,id=pip_config,target=/etc/pip.conf \
    pip install private-package
```

```bash
# Build with secret
docker build --secret id=npmrc,src=$HOME/.npmrc -t image:tag .

# Secret is not in final image layers
```

### Method 4: Multi-Stage with Secrets

```dockerfile
# Build stage: Use secrets
FROM node:18 AS builder
ARG NPM_TOKEN
RUN echo "//registry.npmjs.org/:_authToken=${NPM_TOKEN}" > .npmrc
RUN npm install private-package
RUN rm .npmrc  # Remove secret

# Production stage: No secrets
FROM node:18-slim
COPY --from=builder /app /app
CMD ["node", "server.js"]
```

```bash
# Pass secret as build arg (still risky - use BuildKit secrets instead)
docker build --build-arg NPM_TOKEN=$NPM_TOKEN -t image:tag .
```

### Scanning for Leaked Secrets

```bash
# Scan image for secrets
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image image:tag

# Check image history for secrets
docker history --no-trunc image:tag | grep -i password
```

---

## Base Image Security

### Choose Trusted Base Images

**Recommended**:
- Official images: `python`, `node`, `nginx`
- Verified publishers: `alpine`, `debian`
- Distroless: `gcr.io/distroless/*`

**Avoid**:
- Unknown publishers
- Unmaintained images
- Images with `latest` tag only

### Pin Specific Versions

```dockerfile
# Bad: Version can change
FROM python:3

# Bad: Latest can change
FROM python:latest

# Good: Specific version
FROM python:3.12.1-slim

# Best: Specific digest (immutable)
FROM python:3.12.1-slim@sha256:abc123...
```

### Minimal Base Images

```dockerfile
# Largest: Full Debian base
FROM python:3.12  # 1.1 GB

# Medium: Minimal Debian
FROM python:3.12-slim  # 450 MB

# Small: Alpine Linux
FROM python:3.12-alpine  # 150 MB

# Smallest: Distroless (no shell, most secure)
FROM gcr.io/distroless/python3  # 120 MB
```

**Security Ranking**: Distroless > Alpine > Slim > Full

### Scan for Vulnerabilities

```bash
# Docker scan (requires Docker Desktop or CLI plugin)
docker scan image:tag

# Trivy (open source)
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image image:tag

# Scan with severity filter
docker scan --severity high image:tag
```

### Update Base Images Regularly

```dockerfile
# Rebuild periodically to get security updates
FROM python:3.12-slim

# Update packages in image
RUN apt-get update && \
    apt-get upgrade -y && \
    rm -rf /var/lib/apt/lists/*
```

---

## Resource Limits

### Why Resource Limits?

**Risk**: Container can consume all host resources (CPU, memory, disk)

**Solution**: Set limits to prevent resource exhaustion

### Memory Limits

```bash
# Limit memory to 512 MB
docker run -m 512m image:tag

# Memory + swap limit
docker run -m 512m --memory-swap 1g image:tag

# No swap (memory-swap = memory)
docker run -m 512m --memory-swap 512m image:tag

# Memory reservation (soft limit)
docker run --memory-reservation 256m -m 512m image:tag
```

### CPU Limits

```bash
# Limit to 1.5 CPUs
docker run --cpus 1.5 image:tag

# CPU shares (relative weight)
docker run --cpu-shares 512 image:tag

# CPU quota (microseconds per period)
docker run --cpu-quota 50000 --cpu-period 100000 image:tag  # 50% of 1 CPU
```

### Disk I/O Limits

```bash
# Limit read/write IOPS
docker run --device-read-iops /dev/sda:1000 image:tag
docker run --device-write-iops /dev/sda:1000 image:tag

# Limit read/write bandwidth
docker run --device-read-bps /dev/sda:10mb image:tag
docker run --device-write-bps /dev/sda:10mb image:tag
```

### Process Limits

```bash
# Limit number of processes (prevents fork bombs)
docker run --pids-limit 100 image:tag
```

### Docker Compose Resource Limits

```yaml
version: '3.8'
services:
  app:
    image: app:latest
    deploy:
      resources:
        limits:
          cpus: '1.5'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
    pids_limit: 100
```

---

## Network Security

### Network Isolation

```bash
# Create isolated network
docker network create --driver bridge app-network

# Run containers on isolated network
docker run --network app-network image:tag

# Containers on different networks can't communicate
```

### Disable Inter-Container Communication

```bash
# Create network with ICC disabled
docker network create --driver bridge --opt com.docker.network.bridge.enable_icc=false secure-network
```

### Publish Only Required Ports

```dockerfile
# Expose in Dockerfile (documentation only)
EXPOSE 8000

# Publish at runtime (actually binds port)
docker run -p 127.0.0.1:8000:8000 image:tag  # Localhost only
docker run -p 8000:8000 image:tag  # All interfaces (less secure)
```

### Use Host Network Sparingly

```bash
# Host network: Container uses host's network stack
docker run --network host image:tag

# Security Risk: Container can access all host ports
# Only use when absolutely necessary
```

### DNS Security

```bash
# Use custom DNS servers
docker run --dns 8.8.8.8 --dns 8.8.4.4 image:tag

# Disable DNS lookups
docker run --dns-opt ndots:0 image:tag
```

---

## Volume Security

### Read-Only Volumes

```bash
# Mount volume as read-only
docker run -v /host/config:/app/config:ro image:tag

# Read-only root filesystem
docker run --read-only image:tag

# Read-only with tmpfs for /tmp
docker run --read-only --tmpfs /tmp image:tag
```

### Volume Permissions

```bash
# Verify volume permissions
ls -la /host/volume/path

# Run with specific user
docker run --user 1000:1000 -v /host/data:/app/data image:tag

# Set correct ownership on host
sudo chown -R 1000:1000 /host/data
```

### Named Volumes vs Bind Mounts

```bash
# Named volume (managed by Docker, more secure)
docker volume create app-data
docker run -v app-data:/app/data image:tag

# Bind mount (direct host access, less secure)
docker run -v /host/path:/container/path image:tag

# Prefer named volumes for production
```

---

## Compliance & Auditing

### GAMP-5 Considerations

For pharmaceutical systems requiring GAMP-5 compliance:

**Immutable Images**:
```bash
# Use specific digest (immutable)
FROM python:3.12-slim@sha256:abc123...

# Tag with immutable version
docker tag image:tag image:v1.0.0-$(date +%Y%m%d)

# Push with digest
docker push user/image:v1.0.0
```

**Audit Logging**:
```bash
# Enable Docker daemon logging
# /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3",
    "labels": "production,gamp5"
  }
}

# Container-level logging
docker run --log-driver json-file \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  image:tag
```

**Container Provenance**:
```bash
# Record build metadata
docker build \
  --label version=1.0.0 \
  --label build-date=$(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --label git-commit=$(git rev-parse HEAD) \
  --label gamp5=category4 \
  -t image:v1.0.0 \
  .

# Inspect metadata
docker inspect image:v1.0.0 | jq '.[0].Config.Labels'
```

### Runtime Security

```bash
# Drop all capabilities, add only required
docker run --cap-drop ALL --cap-add NET_BIND_SERVICE image:tag

# Prevent privilege escalation
docker run --security-opt no-new-privileges image:tag

# AppArmor profile (Linux)
docker run --security-opt apparmor=docker-default image:tag

# Seccomp profile
docker run --security-opt seccomp=default.json image:tag
```

### Security Scanning Pipeline

```bash
# In CI/CD pipeline
#!/bin/bash

# Build image
docker build -t app:$VERSION .

# Scan for vulnerabilities
trivy image --severity HIGH,CRITICAL --exit-code 1 app:$VERSION

# If scan passes, tag and push
docker tag app:$VERSION app:latest
docker push app:$VERSION
docker push app:latest
```

---

## Security Checklist

- [ ] **Non-root user**: Container runs as dedicated user (not root)
- [ ] **No secrets in image**: Secrets passed via env vars or secrets management
- [ ] **Trusted base image**: Official, verified, or distroless base image
- [ ] **Pinned versions**: Specific version/digest, not `latest`
- [ ] **Vulnerability scanning**: Images scanned before deployment
- [ ] **Resource limits**: Memory, CPU, and process limits set
- [ ] **Network isolation**: Containers on isolated networks
- [ ] **Minimal ports**: Only required ports published
- [ ] **Read-only volumes**: Config mounted read-only where possible
- [ ] **Read-only root filesystem**: Container filesystem read-only (if possible)
- [ ] **Dropped capabilities**: Unnecessary capabilities dropped
- [ ] **No privilege escalation**: `no-new-privileges` security option set
- [ ] **Audit logging**: Container logs captured and retained
- [ ] **Immutable tags**: Production images tagged with immutable versions
- [ ] **Minimal attack surface**: Smallest base image, minimal packages

---

## Complete Secure Dockerfile Example

```dockerfile
# Use specific version with digest
FROM python:3.12-slim@sha256:abc123...

# Metadata for compliance
LABEL version="1.0.0" \
      build-date="2024-01-15T12:00:00Z" \
      gamp5-category="category-4" \
      maintainer="team@example.com"

# Update packages and install minimal dependencies
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
      curl \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser -g 1000 && \
    useradd -r -u 1000 -g appuser appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

# Install dependencies as root
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application with correct ownership
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Expose port (documentation)
EXPOSE 8000

# Run application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Deployment with security options**:
```bash
docker run -d \
  --name app \
  --user 1000:1000 \
  --read-only \
  --tmpfs /tmp \
  -m 512m \
  --cpus 1.0 \
  --pids-limit 100 \
  -p 127.0.0.1:8000:8000 \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --log-driver json-file \
  --log-opt max-size=10m \
  -v app-data:/app/data \
  app:v1.0.0
```

---

**Key Takeaways**:
- Always run containers as non-root user
- Never include secrets in images (use runtime env vars or secrets management)
- Use minimal, trusted base images with pinned versions
- Set resource limits to prevent exhaustion attacks
- Isolate container networks and minimize port exposure
- Mount sensitive volumes as read-only
- Enable comprehensive audit logging for compliance
- Scan images for vulnerabilities before deployment
- Follow principle of least privilege (drop unnecessary capabilities)

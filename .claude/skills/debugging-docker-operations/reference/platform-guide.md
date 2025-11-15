# Platform-Specific Docker Guide

Comprehensive guide for multi-platform Docker operations across ARM64, AMD64, and WSL2 environments.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [ARM64 (Apple Silicon, Qualcomm Oryon)](#arm64-apple-silicon-qualcomm-oryon)
3. [AMD64/x86_64 (Intel/AMD)](#amd64x86_64-intelamd)
4. [WSL2 (Windows Subsystem for Linux)](#wsl2-windows-subsystem-for-linux)
5. [Multi-Platform Builds](#multi-platform-builds)
6. [Performance Optimization](#performance-optimization)

---

## Architecture Overview

### Platform Identifiers

| Platform | Architecture | Common Names | Typical Use Cases |
|----------|-------------|--------------|-------------------|
| ARM64 | aarch64, arm64 | Apple Silicon (M1/M2/M3), Qualcomm Oryon, AWS Graviton | MacBook, Windows ARM, Cloud ARM instances |
| AMD64 | x86_64, amd64 | Intel, AMD processors | Traditional servers, most cloud instances (EC2, ECS) |
| ARMv7 | armhf, armv7l | Raspberry Pi | IoT devices, embedded systems |

### Docker Platform Detection

```bash
# Check host architecture
uname -m
# Output: x86_64 (AMD64) or aarch64/arm64 (ARM64)

# Check Docker platform
docker info | grep -i architecture
# Output: Architecture: x86_64 or Architecture: aarch64

# Check container platform
docker inspect image:tag | jq '.[0].Architecture'
# Output: "amd64" or "arm64"

# Test architecture in container
docker run --rm alpine uname -m
```

---

## ARM64 (Apple Silicon, Qualcomm Oryon)

### Overview

ARM64 is increasingly popular for local development (MacBook M-series, Windows ARM devices) but production often requires AMD64.

### Native ARM64 Development

**Advantages**:
- **10-15x faster builds** compared to emulating AMD64
- Lower power consumption
- Native performance

**Best Practices**:
```bash
# Build for native ARM64
docker build --platform=linux/arm64 -t image:arm64-dev .

# Use ARM64 base images
FROM --platform=linux/arm64 python:3.12-slim
```

### ARM64 to AMD64 Cross-Compilation

**Use Case**: Developing on ARM64 Mac/Windows but deploying to AMD64 cloud

**Strategy 1: Emulation (Simple, Slower)**
```bash
# Build AMD64 on ARM64 (uses QEMU emulation)
docker build --platform=linux/amd64 -t image:amd64-prod .

# Expect slower build times (5-10x slower)
# Good for occasional production builds
```

**Strategy 2: Separate Builds (Recommended)**
```bash
# Development: Native ARM64 for speed
docker build --platform=linux/arm64 -f Dockerfile -t image:dev .

# Production: AMD64 when ready to deploy
docker build --platform=linux/amd64 -f Dockerfile -t image:prod .

# Or use CI/CD on AMD64 runners for production builds
```

**Strategy 3: Multi-Stage with Platform Separation**
```dockerfile
# Build stage can be ARM64 (fast)
FROM --platform=${BUILDPLATFORM} python:3.12 AS builder
RUN pip install --user package

# Runtime stage for target platform
FROM python:3.12-slim
COPY --from=builder /root/.local /root/.local
```

```bash
# Build using buildx
docker buildx build --platform=linux/amd64 -t image:prod .
```

### ARM64-Specific Issues

#### Issue 1: Base Image Not Available for ARM64

**Symptom**:
```
ERROR: no matching manifest for linux/arm64 in the manifest list
```

**Solution**:
```dockerfile
# Option 1: Find ARM64-compatible alternative
FROM python:3.12-slim  # Official images support multi-arch

# Option 2: Use multi-arch base images explicitly
FROM --platform=linux/arm64 python:3.12-slim

# Option 3: Switch to different base
# Instead of: FROM node:14 (if not ARM64)
# Use: FROM arm64v8/node:14
```

#### Issue 2: Binary Dependencies Not Available

**Symptom**:
```
ERROR: Could not find a version that satisfies the requirement <package>
  (no matching distribution found for ARM64)
```

**Solution**:
```dockerfile
# Install build tools to compile from source
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    && pip install --no-cache-dir <package>

# Or use --no-binary to force source compilation
RUN pip install --no-binary :all: <package>
```

---

## AMD64/x86_64 (Intel/AMD)

### Overview

Most common architecture for production deployments (AWS ECS, traditional data centers).

### Running on Native AMD64

**Best Practices**:
```bash
# Build for AMD64
docker build --platform=linux/amd64 -t image:amd64 .

# Use AMD64 base images
FROM --platform=linux/amd64 python:3.12-slim
```

### AMD64 on ARM64 Hosts (Emulation)

**Performance Impact**:
- 5-10x slower build times
- Acceptable for testing, problematic for active development

**When Emulation is Necessary**:
```bash
# Testing AMD64 images before production deployment
docker build --platform=linux/amd64 -t image:test-amd64 .
docker run --platform=linux/amd64 image:test-amd64

# Final verification before pushing to registry
```

**Optimization Tips**:
```bash
# Minimize emulated work by using multi-stage builds
# Build dependencies on native platform where possible
FROM --platform=${BUILDPLATFORM} python:3.12 AS builder
RUN pip install --user package

# Only runtime needs target platform
FROM --platform=linux/amd64 python:3.12-slim
COPY --from=builder /root/.local /root/.local
```

---

## WSL2 (Windows Subsystem for Linux)

### Overview

WSL2 enables Docker Desktop on Windows with Linux container support. Special considerations for file system performance and integration.

### WSL2 Setup

**Verify WSL2**:
```bash
# In PowerShell
wsl --list --verbose
# Look for VERSION 2

# Check Docker integration
docker info | grep -i "Operating System"
```

**Enable WSL2 Integration**:
1. Docker Desktop → Settings → Resources → WSL Integration
2. Enable integration for your distro (Ubuntu, Debian, etc.)

### File System Performance

**Critical**: File location dramatically affects performance

**Fast (WSL2 Filesystem)**:
```bash
# Store projects in WSL2 filesystem
/home/username/projects/

# Access in Windows Explorer via
\\wsl$\Ubuntu\home\username\projects\
```

**Slow (Windows Filesystem)**:
```bash
# Avoid storing projects here
/mnt/c/Users/username/projects/

# 10-100x slower for file operations
# Especially bad for node_modules, Python virtual envs
```

**Performance Comparison**:
```bash
# Test file performance
time docker build -t test .

# WSL2 filesystem: 30 seconds
# Windows filesystem (/mnt/c/): 300 seconds (10x slower)
```

### WSL2-Specific Issues

#### Issue 1: Docker Desktop Not Starting

**Symptoms**:
- "Docker Desktop starting..." indefinitely
- "Cannot connect to Docker daemon"

**Solutions**:
```bash
# 1. Restart WSL
wsl --shutdown
# Then restart Docker Desktop

# 2. Check WSL2 version
wsl --update

# 3. Reinstall Docker Desktop integration
# Docker Desktop → Settings → Resources → WSL Integration → Toggle off/on

# 4. Check Windows Hyper-V
# Control Panel → Programs → Turn Windows features on/off
# Enable: Virtual Machine Platform, Windows Subsystem for Linux
```

#### Issue 2: File Permission Issues

**Symptom**:
```
Permission denied: /app/file.txt
```

**Cause**: Windows vs Linux permission mismatch

**Solution**:
```bash
# Option 1: Use WSL2 filesystem (recommended)
mv /mnt/c/project /home/user/project

# Option 2: Fix permissions in Dockerfile
COPY --chown=user:user . /app

# Option 3: Use named volumes instead of bind mounts
docker run -v myvolume:/app/data image:tag
```

#### Issue 3: Network Issues

**Symptom**:
- Cannot access container from Windows browser
- DNS resolution fails in containers

**Solution**:
```bash
# Access containers via localhost from Windows
docker run -p 8080:8080 image:tag
# Access: http://localhost:8080 (not 127.0.0.1)

# For DNS issues, configure Docker daemon
# C:\Users\<user>\.docker\daemon.json
{
  "dns": ["8.8.8.8", "8.8.4.4"]
}
```

### WSL2 + ARM64 (Windows on Qualcomm)

**Special Case**: Windows ARM devices (Qualcomm Oryon processors) with WSL2

**Platform Stack**:
1. Windows ARM64 (host OS)
2. WSL2 ARM64 (Linux subsystem)
3. Docker Desktop ARM64
4. Containers: ARM64 native or AMD64 emulated

**Best Practices**:
```bash
# Check WSL2 architecture
wsl uname -m
# Output: aarch64 (ARM64)

# Native ARM64 builds (fast)
docker build --platform=linux/arm64 -t image:dev .

# AMD64 builds (slower, for production)
docker build --platform=linux/amd64 -t image:prod .

# Use WSL2 filesystem for best performance
/home/user/projects/  # Not /mnt/c/
```

---

## Multi-Platform Builds

### Using Docker Buildx

**Setup**:
```bash
# Create buildx builder
docker buildx create --name multiplatform --use

# Verify builder
docker buildx inspect --bootstrap
```

**Build for Multiple Platforms**:
```bash
# Build for both ARM64 and AMD64
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t username/image:multi \
  .

# Build and push to registry
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t username/image:multi \
  --push \
  .

# Build and load locally (single platform only)
docker buildx build \
  --platform linux/arm64 \
  -t image:arm64 \
  --load \
  .
```

### Platform-Aware Dockerfiles

**Using BUILDPLATFORM and TARGETPLATFORM**:
```dockerfile
# Use build platform for build stage (faster)
FROM --platform=${BUILDPLATFORM} python:3.12 AS builder
ARG TARGETPLATFORM
ARG BUILDPLATFORM
RUN echo "Building on ${BUILDPLATFORM} for ${TARGETPLATFORM}"

RUN pip install --user package

# Use target platform for runtime
FROM python:3.12-slim
COPY --from=builder /root/.local /root/.local
```

**Conditional Logic Based on Platform**:
```dockerfile
FROM python:3.12

ARG TARGETPLATFORM
RUN case "${TARGETPLATFORM}" in \
      "linux/amd64") echo "Building for AMD64" ;; \
      "linux/arm64") echo "Building for ARM64" ;; \
      *) echo "Unknown platform: ${TARGETPLATFORM}" ;; \
    esac

# Platform-specific package installation
RUN if [ "${TARGETPLATFORM}" = "linux/arm64" ]; then \
      apt-get install -y arm-specific-package; \
    fi
```

---

## Performance Optimization

### Build Time Comparison

| Scenario | Build Time | Notes |
|----------|------------|-------|
| ARM64 host → ARM64 image | 1x (baseline) | Native, fastest |
| AMD64 host → AMD64 image | 1x (baseline) | Native, fastest |
| ARM64 host → AMD64 image | 5-10x slower | QEMU emulation overhead |
| AMD64 host → ARM64 image | 5-10x slower | QEMU emulation overhead |
| WSL2 (Windows FS) | 10-100x slower | File system overhead |
| WSL2 (WSL2 FS) | ~1x | Near-native performance |

### Optimization Strategies

#### Strategy 1: Platform-Specific Workflows

```bash
# Development (fast feedback)
docker build --platform=linux/arm64 -t image:dev .

# CI/CD (production platform)
# Run on AMD64 runner
docker build --platform=linux/amd64 -t image:prod .

# Don't cross-compile during active development
```

#### Strategy 2: Multi-Stage with Platform Separation

```dockerfile
# Fast: Build stage uses host platform
FROM --platform=${BUILDPLATFORM} node:18 AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Target platform only for runtime
FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/dist ./dist
CMD ["node", "dist/server.js"]
```

```bash
# Builds fast on ARM64, produces AMD64 image
docker buildx build --platform=linux/amd64 -t image:prod .
```

#### Strategy 3: Layer Caching Optimization

```dockerfile
# Cache dependencies separately from code
FROM python:3.12

# Dependencies (change infrequently)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code (changes frequently)
COPY . .

# Leverage cache for cross-platform builds
```

### WSL2-Specific Optimizations

```bash
# 1. Use WSL2 filesystem
cd /home/user/projects  # Not /mnt/c/

# 2. Use .dockerignore aggressively
echo "node_modules" >> .dockerignore
echo ".git" >> .dockerignore

# 3. Use named volumes for data
docker run -v db-data:/var/lib/postgresql/data postgres

# 4. Allocate more resources to WSL2
# .wslconfig (C:\Users\<user>\.wslconfig)
[wsl2]
memory=8GB
processors=4
```

---

## Platform Decision Matrix

| Scenario | Recommended Approach |
|----------|---------------------|
| **Dev on ARM64, Deploy on AMD64** | ARM64 for dev, AMD64 final build in CI/CD |
| **Dev on AMD64, Deploy on AMD64** | AMD64 for everything |
| **Dev on Windows (WSL2)** | Use WSL2 filesystem, native platform for dev |
| **Multi-cloud deployment** | Use buildx for multi-platform images |
| **Active development** | Always use native platform for speed |
| **Final verification** | Build for target platform before deployment |
| **Package not available for ARM64** | Build from source or use AMD64 + emulation |

---

## Quick Reference Commands

```bash
# Detect current platform
uname -m

# Build for specific platform
docker build --platform=linux/amd64 -t image:amd64 .
docker build --platform=linux/arm64 -t image:arm64 .

# Multi-platform build
docker buildx build --platform linux/amd64,linux/arm64 -t image:multi .

# Test platform in container
docker run --rm alpine uname -m

# Check image platform
docker inspect image:tag | jq '.[0].Architecture'

# WSL2: Move to fast filesystem
mv /mnt/c/project /home/user/project

# Check Docker platform
docker info | grep -i architecture
```

---

**Key Takeaways**:
- Always use native platform for active development (5-10x faster)
- Use target platform only for final builds and verification
- WSL2: **Always** use WSL2 filesystem, not Windows filesystem
- Multi-platform: Use `buildx` for simultaneous builds
- ARM64 → AMD64: Build in CI/CD on AMD64 runners when possible
- Test target platform before production deployment

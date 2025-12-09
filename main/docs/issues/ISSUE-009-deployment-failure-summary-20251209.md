# ISSUE-009: Deployment Failure Summary - 2025-12-09

**Date**: 2025-12-09
**Status**: Active - Blocking Deployment
**Severity**: Critical

## Executive Summary

Deployment of pharma-test-gen to AWS ECS/Fargate failed due to Docker build issues on ARM64 development machine. The API image build repeatedly fails with "context canceled" error during pip install phase.

## Failures Encountered

### 1. API Image Build - Context Canceled (CRITICAL)

**Error Message:**
```
#12 CANCELED
ERROR: failed to build: failed to solve: Canceled: context canceled
```

**Timing:** Occurs after ~10 minutes (586 seconds) during pip install phase
**Frequency:** Reproducible - happened on every attempt
**Impact:** API image not pushed to ECR, deployment cannot proceed

**Details:**
- Build reaches step `#12 [builder 6/10] RUN pip install --no-cache-dir -r requirements-prod.txt`
- All 200+ packages download successfully
- 7 packages build wheels successfully (feedfinder2, html2text, jieba3k, pypika, sgmllib3k, spider-client, tinysegmenter)
- Package installation begins (`Installing collected packages: ...`)
- Context gets canceled before installation completes

### 2. Cross-Platform Build Slowness (Contributing Factor)

**Issue:** ISSUE-007
**Impact:** 5-10x slower builds due to ARM64 to AMD64 QEMU emulation
**Duration:** 15-20 minutes per image instead of 3-5 minutes

### 3. Deploy Script Continues Despite Failure (Bug)

**Observation:** The deploy.py script continues to build Worker image after API fails
**Impact:**
- Wastes build time on subsequent images
- Could result in partial deployment state
- Terraform would fail anyway due to missing API image

## Timeline of Events

| Time | Event |
|------|-------|
| T+0 | Deploy script started |
| T+66s | API context transfer complete (710KB) |
| T+366s | Build dependencies for source packages complete |
| T+535s | Wheel building started |
| T+569s | All wheels built successfully |
| T+586s | Package installation started |
| T+~600s | **FAILURE: Context canceled** |
| T+601s | Deploy script moved to Worker image (should have stopped) |

## Root Cause Analysis

### Primary Cause: Resource Exhaustion During QEMU Emulation

The ARM64 to AMD64 cross-compilation via QEMU consumes significant resources:
- High memory usage during pip install (200+ packages)
- CPU emulation overhead
- Buildx container likely runs out of resources or hits timeout

### Secondary Cause: No Build Timeout Configuration

The deploy script and buildx don't have explicit timeout handling:
- Default buildx timeouts may be too aggressive
- No retry logic for transient failures
- No resource monitoring

## Affected Files

| File | Role |
|------|------|
| `Dockerfile.api.pip` | API service Dockerfile |
| `Dockerfile.worker.pip` | Worker service Dockerfile (also at risk) |
| `aws/scripts/deploy.py` | Deployment orchestration |
| `requirements-prod.txt` | 200+ Python packages |

## Recommended Solutions

### Immediate Workarounds

#### Option A: Build on AMD64 Machine (Recommended)
```bash
# Use AWS CodeBuild, GitHub Actions, or cloud VM
# Native build eliminates QEMU overhead
```

#### Option B: Increase WSL Resources
```ini
# ~/.wslconfig
[wsl2]
memory=16GB
swap=8GB
processors=8
```

#### Option C: Build Images Separately with Extended Timeout
```bash
# Build API with no timeout
cd /mnt/c/Users/anteb/Desktop/Courses/Projects/thesis_project
DOCKER_BUILDKIT=1 docker buildx build \
  --platform linux/amd64 \
  --progress=plain \
  --no-cache \
  -f Dockerfile.api.pip \
  -t pharma-test-gen-api:manual \
  . 2>&1 | tee api-build.log
```

### Long-term Fixes

1. **Add proper error handling to deploy.py** - Stop on first build failure
2. **Implement CI/CD pipeline** - Use GitHub Actions with AMD64 runners
3. **Add build caching** - Use Docker layer caching more effectively
4. **Split requirements** - Separate heavy packages into pre-built base image

## Current State

| Component | ECR Image | Status |
|-----------|-----------|--------|
| API | staging-20251208-100719 (old) | **FAILED TO UPDATE** |
| Worker | staging-20251208-100719 (old) | Not attempted |
| Frontend | staging-20251208-100719 (old) | Not attempted |
| ECS Services | Not deployed | Terraform not run |

## Related Issues

- ISSUE-007: Slow ARM to AMD64 Docker Cross-Platform Builds
- ISSUE-008: Docker Build Context Canceled During pip install

## Next Steps

1. [ ] Try Option B: Increase WSL resources and retry
2. [ ] If fails, use Option C: Manual build with extended timeout
3. [ ] If continues to fail, use Option A: Build on cloud AMD64 machine
4. [ ] Fix deploy.py to fail fast on build errors
5. [ ] Consider implementing GitHub Actions CI/CD

## Notes

This is a development environment limitation, not a code bug. Production CI/CD on native AMD64 runners would not have this issue.

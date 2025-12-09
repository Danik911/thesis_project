# ISSUE-008: Docker Build Context Canceled During pip install

**Date**: 2025-12-09
**Status**: Active - Investigating
**Severity**: High (blocks deployment)

## Symptom

Docker buildx build for API image fails with "context canceled" error after pip install completes but before the build finishes.

## Error Message

```
#12 586.5 Installing collected packages: tinysegmenter, striprtf, sortedcontainers, ...
#12 CANCELED
ERROR: failed to build: failed to solve: Canceled: context canceled
```

## Context

- Build was at step `#12 [builder 6/10] RUN pip install --no-cache-dir -r requirements-prod.txt`
- All 200+ packages were downloaded and installed successfully
- Error occurred after ~10 minutes of pip install (586.5 seconds)
- Cross-platform build: ARM64 to AMD64 via QEMU emulation (see ISSUE-007)

## Potential Causes

1. **Docker buildx timeout** - Long-running builds may exceed default context timeout
2. **WSL memory pressure** - Cross-platform emulation consumes significant memory
3. **Docker daemon instability** - WSL Docker may have resource limits
4. **Buildx container crash** - The multiplatform-builder container may have run out of resources

## Workarounds

### 1. Retry the Deployment
The deploy script may continue and subsequent builds could succeed with cached layers:
```bash
python aws/scripts/deploy.py
```

### 2. Increase Docker Resources
In WSL, increase Docker memory allocation:
```bash
# ~/.wslconfig
[wsl2]
memory=8GB
swap=4GB
```

### 3. Build Images Individually
Build each image separately to isolate failures:
```bash
cd /mnt/c/Users/anteb/Desktop/Courses/Projects/thesis_project
docker buildx build --platform linux/amd64 -f Dockerfile.api.pip -t api:test .
```

### 4. Use Native AMD64 Build Environment
Use AWS CodeBuild or GitHub Actions with x86_64 runners (see ISSUE-007)

## Affected Components

| Component | Status | Notes |
|-----------|--------|-------|
| API Image | FAILED | Context canceled after pip install |
| Worker Image | Building | Started after API failure |
| Frontend Image | Pending | Depends on API URL |

## Files Involved

- `Dockerfile.api.pip` - API service Dockerfile
- `aws/scripts/deploy.py` - Deployment script (continues despite API failure?)
- `requirements-prod.txt` - 200+ Python packages

## Related Issues

- ISSUE-007: Slow ARM to AMD64 Docker Cross-Platform Builds (contributing factor)

## Investigation Notes

- The deploy script appears to continue building other images despite API failure
- This may result in partial deployment (Worker builds but API doesn't push)
- Need to verify ECR has all three images before running Terraform

## Resolution

**Status: UNRESOLVED - Blocking deployment**

### Root Cause Confirmed
The error is caused by resource exhaustion during ARM64 to AMD64 cross-compilation via QEMU emulation. The buildx container runs out of resources or hits an internal timeout during the resource-intensive pip install phase.

### Attempted Solutions
1. Retried deployment - Same failure at same point
2. Waited for build to complete - Context canceled consistently at ~586s

### Required Actions
See ISSUE-009 for comprehensive deployment failure summary and recommended next steps:
1. Increase WSL resources (memory/swap)
2. Manual build with extended timeout
3. Use native AMD64 build environment (AWS CodeBuild / GitHub Actions)

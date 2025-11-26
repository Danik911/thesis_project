---
name: debugging-docker
description: Debugs Docker build failures, container runtime errors, platform architecture issues (ARM64/AMD64/WSL2), and optimizes Docker workflows. Use when encountering Docker build errors, container crashes, performance problems, platform compatibility issues, networking failures, volume permission errors, or when working with multi-platform Docker images.
---

# Debugging Docker Operations

## Overview

This skill provides systematic troubleshooting workflows for Docker build failures, runtime errors, platform-specific issues, and performance optimization. Designed for multi-platform environments (ARM64/AMD64/WSL2) with focus on pharmaceutical compliance contexts requiring GAMP-5 validation.

## When to Use

- **Build Failures**: Package installation errors, COPY failures, layer caching issues, dependency conflicts
- **Runtime Errors**: Container crashes, exit codes, DNS resolution, port conflicts
- **Platform Issues**: ARM64 vs AMD64 emulation, WSL2 Docker Desktop integration, cross-platform builds
- **Performance Problems**: Slow builds, large images, inefficient layer caching
- **Networking**: Container communication, port binding, DNS configuration
- **Volumes**: Permission errors, mount failures, data persistence issues
- **Security**: Non-root execution, rootless mode, secret management

## Core Workflow

### Phase 1: Symptom Diagnosis

**Objective**: Identify the problem category and gather initial diagnostic information

1. **Identify Problem Type**
   ```bash
   # For build failures
   docker build 2>&1 | tee build.log

   # For runtime errors
   docker logs <container-name>
   docker inspect <container-name>

   # For platform issues
   bash .claude/skills/debugging-docker-operations/scripts/check-platform.sh
   ```

2. **Categorize the Issue**
   - Build Failure (exit during `docker build`)
   - Runtime Error (container exits or crashes)
   - Platform/Architecture Issue (ARM64/AMD64 mismatch)
   - Performance Problem (slow or inefficient)
   - Networking Issue (connectivity, DNS, ports)
   - Volume/Permission Issue (access denied, mount failures)

3. **Collect Context**
   - Docker version: `docker version`
   - System info: `docker info`
   - Platform: `uname -m` (x86_64, aarch64, arm64)
   - Available images: `docker images`
   - Running containers: `docker ps -a`

**Quality Gate**: Problem type identified, initial logs collected

---

### Phase 2: Root Cause Analysis

**Objective**: Diagnose the specific root cause using problem-specific investigation

#### Build Failures

1. **Analyze Build Log**
   ```bash
   # Run analysis script
   bash .claude/skills/debugging-docker-operations/scripts/analyze-build-failure.sh build.log

   # Common patterns to look for:
   # - "ERROR [stage X/Y]" - which stage failed
   # - "returned a non-zero code" - command failure
   # - "COPY failed" - file not found in build context
   # - Package installation errors
   ```

2. **Check Build Context**
   ```bash
   # Verify files exist in context
   ls -la <path-to-file>

   # Check .dockerignore
   cat .dockerignore

   # Verify Dockerfile COPY paths
   grep COPY Dockerfile
   ```

3. **Inspect Layer Caching**
   ```bash
   # Build with no cache to verify
   docker build --no-cache -f Dockerfile -t test:debug .

   # Check layer history
   docker history <image-name>
   ```

**Common Build Failure Causes**:
- Missing files in build context (COPY errors)
- Package manager issues (apt, pip, npm failures)
- Permission denied (user/group mismatches)
- Platform architecture mismatch
- Network connectivity during package downloads
- Layer cache invalidation

See `reference/common-errors.md` for complete error matrix.

#### Runtime Errors

1. **Check Container Status**
   ```bash
   # Get exit code and status
   docker ps -a | grep <container-name>

   # Inspect full container details
   docker inspect <container-name> | jq '.[0].State'
   ```

2. **Examine Logs**
   ```bash
   # Full logs
   docker logs <container-name>

   # Last 100 lines
   docker logs --tail 100 <container-name>

   # Follow logs in real-time
   docker logs -f <container-name>
   ```

3. **Deep Inspection**
   ```bash
   # Use inspection script
   bash .claude/skills/debugging-docker-operations/scripts/inspect-container.sh <container-name>

   # Check resource limits
   docker stats <container-name>
   ```

**Common Runtime Error Exit Codes**:
- `Exit 0`: Normal exit
- `Exit 1`: Application error
- `Exit 126`: Command invoked cannot execute (permission)
- `Exit 127`: Command not found
- `Exit 137`: Container killed by OOM or SIGKILL
- `Exit 139`: Segmentation fault
- `Exit 143`: Terminated by SIGTERM

#### Platform/Architecture Issues

1. **Verify Platform Configuration**
   ```bash
   # Check Docker platform
   docker info | grep -i architecture

   # Check if running emulation
   docker run --rm alpine uname -m

   # Check platform in image
   docker inspect <image-name> | jq '.[0].Architecture'
   ```

2. **Diagnose Emulation Problems**
   - **Symptom**: Very slow builds on ARM64 when using AMD64 images
   - **Cause**: QEMU emulation overhead
   - **Solution**: Use native ARM64 base images or build separately

3. **WSL2 Specific Issues**
   - **Docker Desktop not starting**: Check WSL2 integration settings
   - **File performance**: Avoid mounting Windows filesystem, use WSL2 filesystem
   - **Network issues**: Check WSL2 NAT configuration

See `reference/platform-guide.md` for complete platform guidance.

**Quality Gate**: Root cause identified, specific error patterns documented

---

### Phase 3: Solution & Validation

**Objective**: Apply fix and verify successful resolution

#### Solution Application Workflow

1. **Apply Specific Fix**

   **For Build Failures**:
   ```dockerfile
   # Fix missing file in context
   # Before: COPY app/main.py /app/
   # After: Verify file exists and fix path
   COPY main.py /app/

   # Fix package installation
   # Add explicit error handling
   RUN pip install --no-cache-dir -r requirements.txt || \
       (pip install --no-cache-dir pip --upgrade && pip install --no-cache-dir -r requirements.txt)

   # Fix platform issues
   # Add explicit platform flag
   # docker build --platform=linux/amd64 -f Dockerfile -t image:tag .
   ```

   **For Runtime Errors**:
   ```bash
   # Fix permission issues
   docker run --user $(id -u):$(id -g) image:tag

   # Fix port conflicts
   docker run -p 8081:8080 image:tag  # Change host port

   # Fix volume permissions
   docker run -v $(pwd)/data:/app/data:rw image:tag
   ```

   **For Performance**:
   - Optimize layer ordering (dependencies first, code last)
   - Use multi-stage builds
   - Leverage .dockerignore
   - See `reference/build-optimization.md`

2. **Validate Fix**
   ```bash
   # Rebuild with verbose output
   docker build --progress=plain -f Dockerfile -t image:test .

   # Test container startup
   docker run --rm image:test

   # Verify functionality
   docker run -it image:test /bin/sh -c "command-to-test"
   ```

3. **Document Resolution**
   - Record the error pattern
   - Document the root cause
   - Save the solution for future reference
   - Update Dockerfile comments if needed

**Quality Gate**: Fix applied successfully, container builds and runs without errors

---

## Best Practices

### Build Optimization
- **Layer ordering**: Place frequently changing files (app code) after stable layers (dependencies)
- **Multi-stage builds**: Separate build and runtime environments
- **Cache efficiency**: Group related RUN commands, use --mount=type=cache
- **Minimize layers**: Combine RUN commands with && where appropriate

### Security
- **Non-root user**: Create and use non-root user in Dockerfile
  ```dockerfile
  RUN adduser -D appuser
  USER appuser
  ```
- **Secrets management**: Use --secret flag or multi-stage builds, never COPY secrets
- **Base image selection**: Use official images, verify signatures
- **Scan for vulnerabilities**: `docker scan <image-name>`

### Platform Handling
- **Explicit platform**: Always specify --platform for production builds
  ```bash
  # For AWS/cloud deployment (Intel)
  docker build --platform=linux/amd64 -f Dockerfile -t image:prod .

  # For local ARM64 development
  docker build --platform=linux/arm64 -f Dockerfile -t image:dev .
  ```
- **Multi-platform images**: Use buildx for simultaneous builds
  ```bash
  docker buildx build --platform linux/amd64,linux/arm64 -t image:multi .
  ```

### Debugging Techniques
- **Incremental testing**: Comment out Dockerfile sections to isolate failures
- **Interactive debugging**: `docker run -it --entrypoint /bin/sh image:tag`
- **Build stages**: Test individual stages in multi-stage builds
  ```bash
  docker build --target builder -t image:builder .
  ```

---

## Common Pitfalls

### Don't: Use relative paths in COPY without verification
```dockerfile
# WRONG: May fail if build context is incorrect
COPY ../app/file.py /app/

# RIGHT: Use paths relative to build context root
COPY app/file.py /app/
```

### Do: Verify build context location
```bash
# Show what Docker sees in build context
docker build --no-cache --progress=plain -f Dockerfile -t test . 2>&1 | grep "COPY"
```

### Don't: Run containers as root in production
```dockerfile
# WRONG: Security risk
FROM python:3.12

# RIGHT: Create and use non-root user
FROM python:3.12
RUN adduser -D appuser
USER appuser
```

### Do: Use explicit platform flags for production
```bash
# WRONG: Platform inferred from host (may differ from production)
docker build -t api:latest .

# RIGHT: Explicit platform for consistent deployment
docker build --platform=linux/amd64 -t api:latest .
```

### Don't: Ignore .dockerignore
```dockerfile
# Build context size can explode without .dockerignore
# Create .dockerignore with:
__pycache__
*.pyc
.git
node_modules
.env
```

---

## Quality Checklist

- [ ] Problem type identified (build/runtime/platform/network/volume)
- [ ] Diagnostic logs collected and analyzed
- [ ] Root cause determined with specific error patterns
- [ ] Solution applied with appropriate fix
- [ ] Build succeeds without errors
- [ ] Container starts and runs successfully
- [ ] Functionality validated (application works as expected)
- [ ] Platform architecture verified (matches deployment target)
- [ ] Security checked (non-root user, no exposed secrets)
- [ ] Performance acceptable (build time, image size)
- [ ] Documentation updated (comments, notes)

---

## Examples

### Example 1: Python Package Installation Failure

**Symptom**:
```
ERROR [stage 2/5] RUN pip install -r requirements.txt
failed to solve: process "/bin/sh -c pip install -r requirements.txt" did not complete successfully: exit code: 1
```

**Diagnosis**:
```bash
# Check build log for specific package failure
grep -A 10 "ERROR" build.log

# Found: "Could not find a version that satisfies the requirement package-name"
```

**Root Cause**: Package version incompatibility or platform-specific binary not available

**Solution**:
```dockerfile
# Add explicit error handling and upgrade pip
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt || \
    (cat requirements.txt | cut -f1 -d= | xargs pip install --no-binary :all:)
```

**Validation**:
```bash
docker build --progress=plain -f Dockerfile -t test:debug .
# Success - no errors
```

---

### Example 2: ARM64 Platform Emulation Slowness

**Symptom**:
```bash
# Build takes 45 minutes on ARM64 Mac/Windows ARM
docker build -f Dockerfile.api -t api:test .
```

**Diagnosis**:
```bash
bash .claude/skills/debugging-docker-operations/scripts/check-platform.sh
# Output: Running on arm64, building for amd64 (emulation active)
```

**Root Cause**: Building AMD64 images on ARM64 host requires QEMU emulation

**Solution**:
```bash
# Strategy 1: Build ARM64 for local development
docker build --platform=linux/arm64 -f Dockerfile.api -t api:dev .

# Strategy 2: Build AMD64 only when needed for deployment
docker build --platform=linux/amd64 -f Dockerfile.api -t api:prod .

# Strategy 3: Use multi-stage build with platform-specific base
```

**Validation**:
```bash
# ARM64 build completes in 3 minutes (15x faster)
docker build --platform=linux/arm64 -f Dockerfile.api -t api:dev .
```

---

### Example 3: Container Exit 137 (OOM Killed)

**Symptom**:
```bash
docker ps -a
# Shows: Exited (137)
```

**Diagnosis**:
```bash
docker inspect container-name | jq '.[0].State'
# OOMKilled: true

docker logs container-name
# Shows application logs, then sudden termination
```

**Root Cause**: Container exceeded memory limit and was killed by OOM killer

**Solution**:
```bash
# Increase memory limit
docker run -m 2g --memory-swap 2g image:tag

# Or fix application memory leak
# Or optimize application memory usage
```

**Validation**:
```bash
# Monitor memory usage
docker stats container-name
# Memory usage stays below limit
```

---

## Advanced Features & References

### Detailed References
- **Docker Command Reference**: `reference/docker-commands.md`
- **Common Error Matrix**: `reference/common-errors.md` (20+ error patterns)
- **Platform-Specific Guide**: `reference/platform-guide.md` (ARM64/AMD64/WSL2)
- **Build Optimization**: `reference/build-optimization.md` (layer caching, multi-stage)
- **Security Hardening**: `reference/security-hardening.md` (non-root, rootless, secrets)

### Diagnostic Scripts
- **Build Failure Analysis**: `scripts/analyze-build-failure.sh <log-file>`
- **Container Inspection**: `scripts/inspect-container.sh <container-name>`
- **Platform Check**: `scripts/check-platform.sh`

### When to Escalate
- Persistent failures after applying documented solutions
- Security vulnerabilities requiring specialized tools
- Complex networking issues requiring tcpdump/wireshark analysis
- Performance issues requiring detailed profiling

---

## Troubleshooting Quick Reference

| Problem | Quick Check | Common Fix |
|---------|-------------|------------|
| Build fails at COPY | `ls -la <file>` in context | Fix path or add to build context |
| Package install fails | Check network, package name | Update package manager, verify name |
| Container exits immediately | `docker logs <container>` | Fix CMD/ENTRYPOINT, check permissions |
| Exit 137 (OOM) | `docker inspect` OOMKilled | Increase memory limit (-m flag) |
| Port already in use | `docker ps`, `netstat -tlnp` | Change host port or stop conflicting process |
| Permission denied | Check user in Dockerfile | Add USER directive, fix volume permissions |
| Slow build on ARM64 | Check `--platform` flag | Use `--platform=linux/arm64` for dev |
| Cannot connect to daemon | `docker info` | Start Docker Desktop, check WSL2 integration |
| Volume mount not working | Check container sees host files | `docker-compose down && up -d` to apply mount changes |
| Code changes not reflected | Volume mount disabled/stale | Re-enable mounts in docker-compose.yml, restart stack |

---

### Volume Mount Development Issues

**Problem**: Code changes on host not reflected in running container despite volume mounts configured

**Common Causes**:
1. **Volume mounts commented out**: Check `docker-compose.yml` for commented volume directives
2. **Container running with old configuration**: Volume changes require recreating containers
3. **Cached Python bytecode**: `.pyc` files from image build taking precedence over mounted source

**Diagnosis**:
```bash
# Check if container can see host files
docker exec <container-name> ls -la /app/main/

# Check if specific code changes are visible
docker exec <container-name> grep "new code marker" /app/main/path/to/file.py

# Inspect actual mounts
docker inspect <container-name> | jq '.[0].Mounts'
```

**Solution**:
```bash
# 1. Enable volume mounts in docker-compose.yml
# Uncomment or add:
#   volumes:
#     - ./main:/app/main:ro

# 2. Recreate containers (down/up applies configuration changes)
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml up -d

# 3. Verify mounts work
docker exec <container-name> grep "test marker" /app/main/file.py

# 4. For future code changes: just restart (no rebuild needed!)
docker-compose -f docker-compose.dev.yml restart api
```

**Development Workflow with Volume Mounts**:
```bash
# Make code changes on host → Edit files normally

# Restart container to reload Python modules (5 seconds)
docker-compose restart api

# Test immediately → No rebuild needed!
```

**When Volume Mounts Don't Work**:
- ❌ Changed `pyproject.toml` dependencies → Must rebuild
- ❌ Changed `Dockerfile` → Must rebuild
- ❌ Changed system packages → Must rebuild
- ✅ Changed Python code → Just restart container
- ✅ Changed config files → Just restart container

**Quality Gate**: Container sees host file changes immediately after restart, no rebuild required

---

**Remember**: Docker issues are systematic and diagnosable. Follow the three-phase workflow (Symptom → Root Cause → Solution), use the diagnostic scripts, and reference the detailed guides for complex scenarios. Always validate fixes before considering the issue resolved. For development speed, always use volume mounts for code - only rebuild when dependencies or system packages change.

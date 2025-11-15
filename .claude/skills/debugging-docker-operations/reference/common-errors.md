# Common Docker Errors Matrix

Comprehensive catalog of Docker errors with symptoms, causes, and solutions.

## Table of Contents

1. [Build Errors](#build-errors)
2. [Runtime Errors](#runtime-errors)
3. [Networking Errors](#networking-errors)
4. [Volume & Permission Errors](#volume--permission-errors)
5. [Platform & Architecture Errors](#platform--architecture-errors)
6. [Resource Errors](#resource-errors)

---

## Build Errors

### Error 1: COPY failed - file not found

**Symptom**:
```
ERROR [stage 2/5] COPY app/main.py /app/
failed to compute cache key: "/app/main.py" not found
```

**Cause**: File doesn't exist in build context or path is incorrect

**Diagnostic Steps**:
```bash
# Check build context location
ls -la app/main.py

# Verify Dockerfile location
pwd

# Check .dockerignore isn't excluding file
cat .dockerignore | grep main.py
```

**Solution**:
```dockerfile
# Fix path relative to build context root
COPY app/main.py /app/

# Or copy entire directory
COPY app/ /app/

# Or use wildcard
COPY app/*.py /app/
```

---

### Error 2: Package installation failed

**Symptom**:
```
ERROR [stage 3/5] RUN pip install -r requirements.txt
ERROR: Could not find a version that satisfies the requirement package-name
```

**Cause**: Package not available, version incompatible, or network issues

**Diagnostic Steps**:
```bash
# Test package availability
docker run --rm python:3.12 pip search package-name

# Check requirements.txt syntax
cat requirements.txt

# Test with verbose output
docker build --progress=plain -t test .
```

**Solution**:
```dockerfile
# Add error handling and upgrade pip
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Or install with platform-specific wheels
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

# Or install without binary (compile from source)
RUN pip install --no-cache-dir --no-binary :all: -r requirements.txt
```

---

### Error 3: apt-get update failed

**Symptom**:
```
ERROR [stage 2/5] RUN apt-get update && apt-get install -y package
E: Failed to fetch http://deb.debian.org/debian/...
```

**Cause**: Network issues, stale package cache, or repository unavailable

**Diagnostic Steps**:
```bash
# Check base image
docker inspect base-image:tag | jq '.[0].Os'

# Test network in container
docker run --rm base-image ping -c 3 deb.debian.org
```

**Solution**:
```dockerfile
# Add retry logic and clean up
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends package && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Or use different mirror
RUN sed -i 's|http://deb.debian.org|http://mirror.example.com|g' /etc/apt/sources.list && \
    apt-get update -y
```

---

### Error 4: Layer caching causing stale builds

**Symptom**:
```
# Code changes not reflected in image
# Old dependencies being used
```

**Cause**: Docker reusing cached layers despite changes

**Diagnostic Steps**:
```bash
# Build with no cache to verify
docker build --no-cache -t test .

# Check layer history
docker history image-name:tag
```

**Solution**:
```bash
# Build without cache
docker build --no-cache -t image:tag .

# Or invalidate cache at specific point
# Add a build arg that changes
docker build --build-arg CACHEBUST=$(date +%s) -t image:tag .
```

```dockerfile
# In Dockerfile, add before the layer
ARG CACHEBUST=1
RUN echo "Cache bust: ${CACHEBUST}"
```

---

### Error 5: Multi-stage build target not found

**Symptom**:
```
ERROR: failed to solve: failed to find stage builder
```

**Cause**: Stage name referenced doesn't exist in Dockerfile

**Diagnostic Steps**:
```bash
# Check Dockerfile for stage names
grep "FROM.*AS" Dockerfile

# Verify build command
echo "docker build --target builder ..."
```

**Solution**:
```dockerfile
# Ensure stage names match
FROM python:3.12 AS builder
RUN pip install --user package

FROM python:3.12-slim AS runtime
COPY --from=builder /root/.local /root/.local
```

```bash
# Build specific stage
docker build --target builder -t image:builder .
```

---

### Error 6: Context too large / slow upload

**Symptom**:
```
# Build hangs at "Sending build context to Docker daemon"
Sending build context to Docker daemon  2.5GB
```

**Cause**: Large files in build context (node_modules, .git, data files)

**Diagnostic Steps**:
```bash
# Check context size
du -sh .

# Find large files
find . -type f -size +10M

# Check .dockerignore
cat .dockerignore
```

**Solution**:
```
# Create/update .dockerignore
node_modules
.git
*.log
*.md
.env
.venv
__pycache__
*.pyc
.pytest_cache
.coverage
*.db
*.sqlite
data/
output/
```

---

## Runtime Errors

### Error 7: Container exits immediately (Exit 0)

**Symptom**:
```bash
docker ps -a
# Shows: Exited (0) few seconds ago
```

**Cause**: No foreground process, CMD/ENTRYPOINT completes immediately

**Diagnostic Steps**:
```bash
# Check logs
docker logs container-name

# Inspect CMD/ENTRYPOINT
docker inspect image:tag | jq '.[0].Config.Cmd'
```

**Solution**:
```dockerfile
# Ensure CMD runs foreground process
CMD ["python", "app.py"]  # Not CMD ["python", "app.py", "&"]

# Or use exec form
CMD exec python app.py

# For debugging, override entrypoint
docker run -it --entrypoint /bin/sh image:tag
```

---

### Error 8: Container exit code 137 (OOM Killed)

**Symptom**:
```bash
docker ps -a
# Shows: Exited (137)

docker inspect container | jq '.[0].State.OOMKilled'
# Returns: true
```

**Cause**: Container exceeded memory limit and was killed by OOM killer

**Diagnostic Steps**:
```bash
# Check memory limit
docker inspect container | jq '.[0].HostConfig.Memory'

# Monitor memory usage
docker stats container-name
```

**Solution**:
```bash
# Increase memory limit
docker run -m 2g --memory-swap 2g image:tag

# Or set no limit (use with caution)
docker run -m 0 image:tag

# Or optimize application memory usage
# Fix memory leaks, reduce memory footprint
```

---

### Error 9: Container exit code 127 (Command not found)

**Symptom**:
```bash
docker ps -a
# Shows: Exited (127)

docker logs container
# OCI runtime exec failed: executable file not found in $PATH
```

**Cause**: Command specified in CMD/ENTRYPOINT doesn't exist

**Diagnostic Steps**:
```bash
# Check what command failed
docker logs container-name

# Verify command exists in image
docker run --rm -it --entrypoint /bin/sh image:tag
which command-name
```

**Solution**:
```dockerfile
# Ensure command is installed
RUN apt-get update && apt-get install -y command-package

# Or fix path
ENV PATH="/usr/local/bin:${PATH}"

# Or use absolute path
CMD ["/usr/local/bin/python", "app.py"]
```

---

### Error 10: Permission denied errors

**Symptom**:
```
python: can't open file 'app.py': [Errno 13] Permission denied
```

**Cause**: File permissions incorrect or running as wrong user

**Diagnostic Steps**:
```bash
# Check file permissions
docker run --rm -it --entrypoint /bin/sh image:tag
ls -la /app/

# Check user
docker run --rm image:tag whoami
```

**Solution**:
```dockerfile
# Fix permissions during build
COPY --chown=appuser:appuser app.py /app/

# Or change ownership after copy
COPY app.py /app/
RUN chown -R appuser:appuser /app

# Or run as root (not recommended for production)
USER root
```

---

## Networking Errors

### Error 11: Port already in use

**Symptom**:
```
Error starting userland proxy: listen tcp 0.0.0.0:8080: bind: address already in use
```

**Cause**: Another process using the same host port

**Diagnostic Steps**:
```bash
# Check what's using the port
netstat -tlnp | grep 8080
# or
lsof -i :8080

# Check running containers
docker ps --format 'table {{.Names}}\t{{.Ports}}'
```

**Solution**:
```bash
# Use different host port
docker run -p 8081:8080 image:tag

# Or stop conflicting process
docker stop conflicting-container

# Or use host network mode
docker run --network host image:tag
```

---

### Error 12: Cannot connect to Docker daemon

**Symptom**:
```
Cannot connect to the Docker daemon at unix:///var/run/docker.sock
Is the docker daemon running?
```

**Cause**: Docker Desktop not running or permissions issue

**Diagnostic Steps**:
```bash
# Check Docker service status
docker info

# Check if daemon socket exists
ls -la /var/run/docker.sock

# Check user groups (Linux)
groups
```

**Solution**:
```bash
# Start Docker Desktop (Windows/Mac)
# Or start Docker service (Linux)
sudo systemctl start docker

# Add user to docker group (Linux)
sudo usermod -aG docker $USER
newgrp docker

# Or use sudo (temporary)
sudo docker ps
```

---

### Error 13: DNS resolution failed

**Symptom**:
```
docker logs container
# Could not resolve host: example.com
```

**Cause**: DNS configuration issues or network isolation

**Diagnostic Steps**:
```bash
# Test DNS in container
docker exec container nslookup google.com

# Check Docker DNS settings
docker inspect container | jq '.[0].HostConfig.Dns'
```

**Solution**:
```bash
# Use custom DNS
docker run --dns 8.8.8.8 --dns 8.8.4.4 image:tag

# Or use host network
docker run --network host image:tag

# Or configure Docker daemon
# Edit /etc/docker/daemon.json
{
  "dns": ["8.8.8.8", "8.8.4.4"]
}
```

---

## Volume & Permission Errors

### Error 14: Volume mount permission denied

**Symptom**:
```
docker logs container
# Permission denied: '/data/file.txt'
```

**Cause**: User in container doesn't have permissions for mounted volume

**Diagnostic Steps**:
```bash
# Check mount permissions
ls -la /host/mounted/path

# Check container user
docker exec container id
```

**Solution**:
```bash
# Run with same user as host
docker run --user $(id -u):$(id -g) -v /host/path:/container/path image:tag

# Or fix permissions on host
chmod -R 777 /host/path  # Not recommended for production

# Or change ownership on host
sudo chown -R 1000:1000 /host/path
```

```dockerfile
# In Dockerfile, match host user ID
RUN adduser -u 1000 -D appuser
USER appuser
```

---

### Error 15: Named volume not found

**Symptom**:
```
Error response from daemon: create volume-name: volume not found
```

**Cause**: Volume doesn't exist

**Diagnostic Steps**:
```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect volume-name
```

**Solution**:
```bash
# Create volume
docker volume create volume-name

# Or use Docker Compose
# docker-compose.yml
volumes:
  volume-name:
```

---

## Platform & Architecture Errors

### Error 16: Platform mismatch warning

**Symptom**:
```
WARNING: The requested image's platform (linux/amd64) does not match the detected host platform (linux/arm64/v8)
```

**Cause**: Building/running AMD64 image on ARM64 host (or vice versa)

**Diagnostic Steps**:
```bash
# Check host architecture
uname -m

# Check image architecture
docker inspect image:tag | jq '.[0].Architecture'

# Check if emulation is running
docker run --rm alpine uname -m
```

**Solution**:
```bash
# Build for native platform
docker build --platform=linux/arm64 -t image:arm64 .

# Or explicitly use emulation
docker build --platform=linux/amd64 -t image:amd64 .

# Or build multi-platform
docker buildx build --platform linux/amd64,linux/arm64 -t image:multi .
```

---

### Error 17: Exec format error

**Symptom**:
```
standard_init_linux.go:228: exec user process caused: exec format error
```

**Cause**: Binary architecture doesn't match container platform

**Diagnostic Steps**:
```bash
# Check binary architecture
file /path/to/binary

# Check container platform
docker inspect container | jq '.[0].Platform'
```

**Solution**:
```dockerfile
# Ensure correct base image for platform
FROM --platform=linux/amd64 python:3.12

# Or compile binary for correct architecture
RUN apt-get update && \
    apt-get install -y build-essential && \
    gcc -o app app.c
```

---

### Error 18: WSL2 slow file performance

**Symptom**:
```
# Extremely slow file operations
# Docker build takes 10x longer than expected
```

**Cause**: Accessing Windows filesystem from WSL2

**Diagnostic Steps**:
```bash
# Check if in WSL2 filesystem
pwd
# /mnt/c/... = Windows filesystem (slow)
# /home/... = WSL2 filesystem (fast)
```

**Solution**:
```bash
# Move project to WSL2 filesystem
mv /mnt/c/projects/app /home/user/projects/app
cd /home/user/projects/app

# Or use named volumes instead of bind mounts
docker run -v myvolume:/app/data image:tag
```

---

## Resource Errors

### Error 19: No space left on device

**Symptom**:
```
ERROR: failed to solve: failed to export image: failed to create image: write ... no space left on device
```

**Cause**: Docker disk usage exceeded available space

**Diagnostic Steps**:
```bash
# Check Docker disk usage
docker system df

# Check host disk space
df -h
```

**Solution**:
```bash
# Clean up Docker resources
docker system prune -a --volumes

# Remove specific items
docker container prune
docker image prune -a
docker volume prune
docker network prune

# Increase Docker Desktop disk limit (Settings > Resources > Disk)
```

---

### Error 20: Build timeout

**Symptom**:
```
# Build hangs indefinitely
# Or times out after long period
```

**Cause**: Long-running operations, network issues, or deadlock

**Diagnostic Steps**:
```bash
# Build with verbose output
docker build --progress=plain -t image:tag . 2>&1 | tee build.log

# Check network connectivity
docker run --rm alpine ping -c 3 google.com
```

**Solution**:
```dockerfile
# Add timeouts to long operations
RUN timeout 300 pip install -r requirements.txt

# Or split into smaller operations
RUN pip install package1
RUN pip install package2

# Or use --no-cache
docker build --no-cache -t image:tag .
```

---

## Exit Code Reference

| Exit Code | Meaning | Common Causes |
|-----------|---------|---------------|
| 0 | Success | Normal exit, but container stopped |
| 1 | Application error | Runtime error, exception, failed command |
| 2 | Misuse of shell command | Syntax error, missing semicolon |
| 126 | Command cannot execute | Permission denied, not executable |
| 127 | Command not found | Typo, binary not in PATH, not installed |
| 128 | Invalid exit argument | Exit code out of range |
| 130 | Terminated by Ctrl+C | SIGINT (manual interruption) |
| 137 | Killed by SIGKILL | OOM killed, resource limit exceeded |
| 139 | Segmentation fault | SIGSEGV, memory access violation |
| 143 | Terminated by SIGTERM | Graceful shutdown request |
| 255 | Exit status out of range | Invalid exit code used |

---

## Quick Diagnostic Commands

```bash
# Complete error diagnosis workflow

# 1. Check Docker daemon
docker info

# 2. View build logs
docker build --progress=plain -t test . 2>&1 | tee build.log

# 3. Check container status
docker ps -a

# 4. Inspect container
docker inspect container | jq '.[0].State'

# 5. View logs with timestamps
docker logs -t --tail 100 container

# 6. Check resource usage
docker stats --no-stream

# 7. Test interactively
docker run -it --entrypoint /bin/sh image:tag

# 8. Check disk usage
docker system df -v

# 9. Verify platform
docker inspect image | jq '.[0].Architecture'
```

---

**Pro Tips**:
- Always check logs first: `docker logs container-name`
- Use `--progress=plain` for verbose build output
- Use `docker inspect` with `jq` for structured data
- Test with `--rm` flag to auto-cleanup failed containers
- Use `docker exec -it` for interactive debugging
- Keep `docker system df` output handy for disk issues
- Document solutions for recurring errors in team knowledge base

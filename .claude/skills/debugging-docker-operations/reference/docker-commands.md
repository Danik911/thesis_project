# Docker Commands Reference

Quick reference for essential Docker commands used in debugging and operations.

## Table of Contents

1. [Build Commands](#build-commands)
2. [Container Management](#container-management)
3. [Image Management](#image-management)
4. [Inspection & Diagnostics](#inspection--diagnostics)
5. [Logs & Debugging](#logs--debugging)
6. [Network Commands](#network-commands)
7. [Volume Commands](#volume-commands)
8. [System Commands](#system-commands)

---

## Build Commands

### Basic Build
```bash
# Build image from Dockerfile
docker build -t image-name:tag .

# Build with specific Dockerfile
docker build -f Dockerfile.dev -t image-name:dev .

# Build with platform specification
docker build --platform=linux/amd64 -t image-name:amd64 .

# Build with no cache (clean build)
docker build --no-cache -t image-name:tag .

# Build with verbose output
docker build --progress=plain -t image-name:tag .
```

### Advanced Build Options
```bash
# Build specific stage in multi-stage Dockerfile
docker build --target builder -t image-name:builder .

# Build with build arguments
docker build --build-arg VERSION=1.0 -t image-name:tag .

# Build with resource limits
docker build --memory 2g --cpu-shares 512 -t image-name:tag .

# Build and tag multiple times
docker build -t image-name:latest -t image-name:v1.0 .

# Build with secret (for auth, keys)
docker build --secret id=mysecret,src=./secret.txt -t image-name:tag .
```

### Buildx (Multi-Platform)
```bash
# Create buildx builder
docker buildx create --name multiplatform --use

# Build for multiple platforms
docker buildx build --platform linux/amd64,linux/arm64 -t image-name:multi .

# Build and push multi-platform
docker buildx build --platform linux/amd64,linux/arm64 -t user/image:tag --push .
```

---

## Container Management

### Run Containers
```bash
# Run container (foreground)
docker run image-name:tag

# Run container (detached)
docker run -d image-name:tag

# Run with name
docker run --name my-container -d image-name:tag

# Run with port mapping
docker run -p 8080:80 image-name:tag

# Run with environment variables
docker run -e VAR1=value1 -e VAR2=value2 image-name:tag

# Run with volume mount
docker run -v /host/path:/container/path image-name:tag

# Run with resource limits
docker run -m 512m --cpus 1.5 image-name:tag

# Run interactively with shell
docker run -it image-name:tag /bin/sh

# Run with custom entrypoint
docker run --entrypoint /bin/bash image-name:tag

# Run as specific user
docker run --user 1000:1000 image-name:tag

# Run with network mode
docker run --network host image-name:tag
```

### Container Lifecycle
```bash
# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# Start stopped container
docker start container-name

# Stop running container
docker stop container-name

# Restart container
docker restart container-name

# Pause container
docker pause container-name

# Unpause container
docker unpause container-name

# Kill container (force stop)
docker kill container-name

# Remove container
docker rm container-name

# Remove running container (force)
docker rm -f container-name

# Remove all stopped containers
docker container prune
```

### Execute Commands in Containers
```bash
# Execute command in running container
docker exec container-name command

# Execute interactive shell
docker exec -it container-name /bin/sh

# Execute as specific user
docker exec -u root container-name command

# Execute with environment variable
docker exec -e VAR=value container-name command
```

---

## Image Management

### List & Remove Images
```bash
# List images
docker images

# List images with digests
docker images --digests

# List image IDs only
docker images -q

# Remove image
docker rmi image-name:tag

# Remove image by ID
docker rmi image-id

# Force remove image
docker rmi -f image-name:tag

# Remove all unused images
docker image prune

# Remove all images
docker image prune -a
```

### Image Operations
```bash
# Tag image
docker tag source-image:tag target-image:tag

# Pull image
docker pull image-name:tag

# Push image
docker push image-name:tag

# Save image to tar
docker save -o image.tar image-name:tag

# Load image from tar
docker load -i image.tar

# Export container as tar
docker export container-name > container.tar

# Import tar as image
docker import container.tar image-name:tag
```

---

## Inspection & Diagnostics

### Inspect Resources
```bash
# Inspect container (full JSON)
docker inspect container-name

# Inspect image
docker inspect image-name:tag

# Inspect specific field
docker inspect --format='{{.State.Status}}' container-name

# Inspect network configuration
docker inspect --format='{{.NetworkSettings.IPAddress}}' container-name

# Inspect using jq for better formatting
docker inspect container-name | jq '.[0].State'
```

### Resource Usage
```bash
# Show container resource usage (live)
docker stats

# Show stats for specific container
docker stats container-name

# Show stats once (no streaming)
docker stats --no-stream

# Show disk usage
docker system df

# Show detailed disk usage
docker system df -v
```

### Image History
```bash
# Show image layer history
docker history image-name:tag

# Show layer sizes
docker history --no-trunc image-name:tag

# Show human-readable sizes
docker history -H image-name:tag
```

---

## Logs & Debugging

### View Logs
```bash
# View container logs
docker logs container-name

# Follow logs (stream)
docker logs -f container-name

# Show last N lines
docker logs --tail 100 container-name

# Show logs with timestamps
docker logs -t container-name

# Show logs since timestamp
docker logs --since 2024-01-01T00:00:00 container-name

# Show logs until timestamp
docker logs --until 2024-01-02T00:00:00 container-name
```

### Debug Container
```bash
# Attach to running container
docker attach container-name

# Copy files from container
docker cp container-name:/path/to/file ./local/path

# Copy files to container
docker cp ./local/file container-name:/path/to/destination

# Show container processes
docker top container-name

# Show container changes
docker diff container-name

# Show container port mappings
docker port container-name
```

---

## Network Commands

### Network Management
```bash
# List networks
docker network ls

# Create network
docker network create network-name

# Remove network
docker network rm network-name

# Inspect network
docker network inspect network-name

# Connect container to network
docker network connect network-name container-name

# Disconnect container from network
docker network disconnect network-name container-name
```

### Network Diagnostics
```bash
# Run container with network mode
docker run --network=host image-name:tag

# Run container on specific network
docker run --network=network-name image-name:tag

# Publish all exposed ports
docker run -P image-name:tag

# Check DNS resolution in container
docker exec container-name nslookup hostname
```

---

## Volume Commands

### Volume Management
```bash
# List volumes
docker volume ls

# Create volume
docker volume create volume-name

# Remove volume
docker volume rm volume-name

# Inspect volume
docker volume inspect volume-name

# Remove all unused volumes
docker volume prune
```

### Volume Usage
```bash
# Mount named volume
docker run -v volume-name:/container/path image-name:tag

# Mount host directory (bind mount)
docker run -v /host/path:/container/path image-name:tag

# Mount as read-only
docker run -v volume-name:/container/path:ro image-name:tag

# Mount with specific driver
docker run --mount source=volume-name,target=/container/path image-name:tag
```

---

## System Commands

### System Information
```bash
# Show Docker version
docker version

# Show system information
docker info

# Show system events (live)
docker events

# Show events with filters
docker events --filter 'type=container'
```

### System Cleanup
```bash
# Remove all unused data
docker system prune

# Remove all unused data (including volumes)
docker system prune --volumes

# Remove all unused data (force, no prompt)
docker system prune -f

# Remove all unused images (not just dangling)
docker system prune -a
```

### Docker Context
```bash
# List contexts
docker context ls

# Use specific context
docker context use context-name

# Create new context
docker context create context-name --docker "host=ssh://user@remote"
```

---

## Advanced Diagnostic Commands

### Build Debugging
```bash
# Build with inline cache
docker build --cache-from image-name:latest -t image-name:new .

# Build with build kit
DOCKER_BUILDKIT=1 docker build -t image-name:tag .

# Show build dependencies
docker buildx imagetools inspect image-name:tag
```

### Container Debugging
```bash
# Run with healthcheck override
docker run --health-cmd='curl -f http://localhost/ || exit 1' image-name:tag

# Show live container logs during startup
docker run -d --name test image:tag && docker logs -f test

# Create container without starting
docker create --name test image:tag

# Commit running container to image (for debugging)
docker commit container-name debug-image:tag
```

### Security Scanning
```bash
# Scan image for vulnerabilities (Docker Desktop)
docker scan image-name:tag

# Scan with specific severity
docker scan --severity high image-name:tag
```

---

## Quick Diagnostic Workflow

```bash
# Complete diagnostic sequence for troubleshooting

# 1. Check Docker is running
docker info

# 2. List all containers
docker ps -a

# 3. Check specific container status
docker inspect container-name | jq '.[0].State'

# 4. View logs
docker logs --tail 100 container-name

# 5. Check resource usage
docker stats --no-stream container-name

# 6. Execute shell for interactive debugging
docker exec -it container-name /bin/sh

# 7. Check network connectivity
docker exec container-name ping google.com

# 8. Verify process running
docker top container-name
```

---

**Pro Tips**:
- Use `docker inspect` with `jq` for better JSON parsing
- Use `docker stats` to monitor resource usage in real-time
- Use `docker logs -f` to stream logs during troubleshooting
- Use `docker exec -it` for interactive debugging inside containers
- Use `docker system df` to check disk usage before cleanup
- Always specify `--platform` for production builds to avoid architecture mismatches

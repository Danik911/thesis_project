#!/bin/bash
#
# Docker build script for pharmaceutical test generation system
#
# GAMP-5 Compliance:
# - Tags images with git commit SHA for traceability
# - Builds both API and worker containers
# - Validates image size (<200MB target)
# - Enables BuildKit for cache mounts
#
# Usage:
#   ./scripts/build-docker.sh
#

set -e  # Exit on error (NO FALLBACK LOGIC)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "Docker Build - Pharmaceutical Test Gen"
echo "========================================="

# Enable BuildKit (required for cache mounts in Dockerfile)
export DOCKER_BUILDKIT=1

# Allow overriding build platform (defaults to linux/amd64 for ECS)
TARGET_PLATFORM="${TARGET_PLATFORM:-linux/amd64}"
echo "Target platform: ${TARGET_PLATFORM}"

# Get git commit SHA for image tagging (GAMP-5 traceability)
GIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
echo -e "${GREEN}Git SHA: ${GIT_SHA}${NC}"

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo ""
echo "Building API container..."
docker build \
    --platform="${TARGET_PLATFORM}" \
    -f Dockerfile.api \
    -t thesis-api:latest \
    -t thesis-api:${GIT_SHA} \
    .

echo ""
echo "Building worker container..."
docker build \
    --platform="${TARGET_PLATFORM}" \
    -f Dockerfile.worker \
    -t thesis-worker:latest \
    -t thesis-worker:${GIT_SHA} \
    .

echo ""
echo "========================================="
echo "Build Summary"
echo "========================================="

# Get image sizes
API_SIZE=$(docker images thesis-api:latest --format "{{.Size}}")
WORKER_SIZE=$(docker images thesis-worker:latest --format "{{.Size}}")

echo -e "API image size:    ${API_SIZE}"
echo -e "Worker image size: ${WORKER_SIZE}"

# Check if images exceed target size (200MB)
API_SIZE_MB=$(docker images thesis-api:latest --format "{{.Size}}" | sed 's/MB//' | awk '{print int($1)}')
WORKER_SIZE_MB=$(docker images thesis-worker:latest --format "{{.Size}}" | sed 's/MB//' | awk '{print int($1)}')

echo ""
if [ "$API_SIZE_MB" -gt 200 ]; then
    echo -e "${YELLOW}WARNING: API image (${API_SIZE}) exceeds 200MB target${NC}"
else
    echo -e "${GREEN}✓ API image size within target (<200MB)${NC}"
fi

if [ "$WORKER_SIZE_MB" -gt 200 ]; then
    echo -e "${YELLOW}WARNING: Worker image (${WORKER_SIZE}) exceeds 200MB target${NC}"
else
    echo -e "${GREEN}✓ Worker image size within target (<200MB)${NC}"
fi

echo ""
echo "Build complete! Images tagged:"
echo "  - thesis-api:latest, thesis-api:${GIT_SHA}"
echo "  - thesis-worker:latest, thesis-worker:${GIT_SHA}"
echo ""
echo "Next steps:"
echo "  1. Run: docker run -p 8080:8080 thesis-api:latest"
echo "  2. Test: curl http://localhost:8080/health"
echo "  3. Scan: ./scripts/scan-docker.sh"

#!/usr/bin/env bash

# check-platform.sh
# Checks Docker platform and architecture configuration

set -euo pipefail

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Docker Platform & Architecture Check ===${NC}\n"

# Helper function to print section headers
section() {
    echo -e "\n${BLUE}--- $1 ---${NC}"
}

# Helper function to print status
status() {
    echo -e "${GREEN}[OK]${NC} $1"
}

# Helper function to print warnings
warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Helper function to print errors
error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 1. Host platform detection
section "Host Platform"
HOST_ARCH=$(uname -m)
HOST_OS=$(uname -s)

echo "Architecture: $HOST_ARCH"
echo "Operating System: $HOST_OS"

case $HOST_ARCH in
    x86_64|amd64)
        echo "Platform: AMD64 (Intel/AMD 64-bit)"
        HOST_PLATFORM="amd64"
        ;;
    aarch64|arm64)
        echo "Platform: ARM64 (Apple Silicon, Qualcomm Oryon, AWS Graviton)"
        HOST_PLATFORM="arm64"
        ;;
    armv7l)
        echo "Platform: ARMv7 (Raspberry Pi)"
        HOST_PLATFORM="armv7"
        ;;
    *)
        echo "Platform: Unknown ($HOST_ARCH)"
        HOST_PLATFORM="unknown"
        ;;
esac

# 2. Docker platform configuration
section "Docker Configuration"
if command -v docker >/dev/null 2>&1; then
    status "Docker is installed"

    DOCKER_VERSION=$(docker version --format '{{.Server.Version}}' 2>/dev/null || echo "unknown")
    echo "Docker version: $DOCKER_VERSION"

    DOCKER_ARCH=$(docker info --format '{{.Architecture}}' 2>/dev/null || echo "unknown")
    echo "Docker architecture: $DOCKER_ARCH"

    DOCKER_OS=$(docker info --format '{{.OSType}}' 2>/dev/null || echo "unknown")
    echo "Docker OS: $DOCKER_OS"
else
    error "Docker is not installed or not running"
    exit 1
fi

# 3. Platform matching check
section "Platform Matching"
if [ "$HOST_ARCH" == "x86_64" ] && [ "$DOCKER_ARCH" == "x86_64" ]; then
    status "Host and Docker platforms match (AMD64)"
elif [ "$HOST_ARCH" == "aarch64" ] && [ "$DOCKER_ARCH" == "aarch64" ]; then
    status "Host and Docker platforms match (ARM64)"
elif [ "$HOST_ARCH" == "arm64" ] && [ "$DOCKER_ARCH" == "aarch64" ]; then
    status "Host and Docker platforms match (ARM64)"
else
    warn "Host architecture ($HOST_ARCH) may not match Docker ($DOCKER_ARCH)"
fi

# 4. Test container platform
section "Container Platform Test"
echo "Testing platform in container..."
CONTAINER_ARCH=$(docker run --rm alpine uname -m 2>/dev/null || echo "failed")

if [ "$CONTAINER_ARCH" == "failed" ]; then
    error "Could not test container platform"
else
    echo "Container reports architecture: $CONTAINER_ARCH"

    if [ "$CONTAINER_ARCH" == "$HOST_ARCH" ] || \
       ([ "$CONTAINER_ARCH" == "aarch64" ] && [ "$HOST_ARCH" == "arm64" ]) || \
       ([ "$CONTAINER_ARCH" == "arm64" ] && [ "$HOST_ARCH" == "aarch64" ]); then
        status "Container running on native platform (no emulation)"
    else
        warn "Container architecture ($CONTAINER_ARCH) differs from host ($HOST_ARCH)"
        echo "QEMU emulation may be active (expect slower performance)"
    fi
fi

# 5. Emulation detection
section "Emulation Detection"
if [ "$HOST_PLATFORM" == "arm64" ]; then
    echo "Testing AMD64 emulation capability..."
    if docker run --platform=linux/amd64 --rm alpine echo "AMD64 works" >/dev/null 2>&1; then
        status "AMD64 emulation available (QEMU)"
        warn "AMD64 builds will be 5-10x slower due to emulation"
        echo "Recommendation: Use --platform=linux/arm64 for development"
    else
        error "AMD64 emulation not available"
    fi
elif [ "$HOST_PLATFORM" == "amd64" ]; then
    echo "Testing ARM64 emulation capability..."
    if docker run --platform=linux/arm64 --rm alpine echo "ARM64 works" >/dev/null 2>&1; then
        status "ARM64 emulation available (QEMU)"
        warn "ARM64 builds will be 5-10x slower due to emulation"
    else
        error "ARM64 emulation not available"
    fi
fi

# 6. WSL2 detection (Windows only)
section "WSL2 Detection"
if grep -qi microsoft /proc/version 2>/dev/null; then
    status "Running in WSL2"

    WSL_DISTRO=${WSL_DISTRO_NAME:-"Unknown"}
    echo "WSL Distribution: $WSL_DISTRO"

    # Check if in WSL2 filesystem or Windows filesystem
    CWD=$(pwd)
    if [[ "$CWD" == /mnt/* ]]; then
        warn "Current directory is on Windows filesystem: $CWD"
        echo "File operations will be significantly slower"
        echo "Recommendation: Move project to WSL2 filesystem (/home/...)"
    else
        status "Current directory is on WSL2 filesystem: $CWD"
    fi
else
    echo "Not running in WSL2"
fi

# 7. BuildKit support
section "BuildKit Support"
if docker buildx version >/dev/null 2>&1; then
    status "BuildKit (buildx) is available"
    BUILDX_VERSION=$(docker buildx version 2>/dev/null || echo "unknown")
    echo "BuildX version: $BUILDX_VERSION"

    # List builders
    echo
    echo "Available builders:"
    docker buildx ls 2>/dev/null || echo "Could not list builders"
else
    warn "BuildKit (buildx) not available"
    echo "Install buildx for multi-platform builds"
fi

# 8. Platform-specific recommendations
section "Recommendations"
echo

if [ "$HOST_PLATFORM" == "arm64" ]; then
    echo -e "${GREEN}ARM64 Platform Detected${NC}"
    echo
    echo "For fastest builds (local development):"
    echo "  docker build --platform=linux/arm64 -t image:dev ."
    echo
    echo "For production (if targeting AMD64 cloud):"
    echo "  docker build --platform=linux/amd64 -t image:prod ."
    echo "  (Expect 5-10x slower due to emulation)"
    echo
    echo "Optimal strategy:"
    echo "  - Use ARM64 for active development (fast)"
    echo "  - Build AMD64 only for final deployment (in CI/CD if possible)"
    echo
elif [ "$HOST_PLATFORM" == "amd64" ]; then
    echo -e "${GREEN}AMD64 Platform Detected${NC}"
    echo
    echo "For production builds (most common):"
    echo "  docker build --platform=linux/amd64 -t image:prod ."
    echo
    echo "Native builds are fast on this platform"
    echo
fi

if grep -qi microsoft /proc/version 2>/dev/null; then
    echo -e "${YELLOW}WSL2 Optimization Tips:${NC}"
    echo "  - Store projects in WSL2 filesystem (/home/...) not Windows (/mnt/c/)"
    echo "  - Use named volumes instead of bind mounts when possible"
    echo "  - Allocate more resources to WSL2 in .wslconfig if needed"
    echo
fi

# 9. Quick test build
section "Platform Build Test"
read -p "Run quick platform build test? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Testing native platform build..."

    TMP_DIR=$(mktemp -d)
    cat > "$TMP_DIR/Dockerfile" <<EOF
FROM alpine:latest
RUN echo "Platform test successful"
EOF

    echo "Building for native platform..."
    BUILD_START=$(date +%s)
    if docker build -q -t platform-test:native "$TMP_DIR" >/dev/null 2>&1; then
        BUILD_END=$(date +%s)
        BUILD_TIME=$((BUILD_END - BUILD_START))
        status "Native build completed in ${BUILD_TIME}s"
    else
        error "Native build failed"
    fi

    # Test cross-platform if on ARM64
    if [ "$HOST_PLATFORM" == "arm64" ]; then
        echo
        echo "Testing AMD64 emulation build..."
        BUILD_START=$(date +%s)
        if docker build --platform=linux/amd64 -q -t platform-test:amd64 "$TMP_DIR" >/dev/null 2>&1; then
            BUILD_END=$(date +%s)
            BUILD_TIME=$((BUILD_END - BUILD_START))
            warn "AMD64 build completed in ${BUILD_TIME}s (emulated)"
            echo "Emulation overhead: ~${BUILD_TIME}x slower than native"
        else
            error "AMD64 build failed"
        fi
    fi

    # Cleanup
    docker rmi -f platform-test:native platform-test:amd64 >/dev/null 2>&1 || true
    rm -rf "$TMP_DIR"
fi

# 10. Summary
section "Summary"
echo
echo "Platform: $HOST_PLATFORM ($HOST_ARCH)"
echo "Docker: $DOCKER_ARCH"
echo "Status: $([ "$CONTAINER_ARCH" == "$HOST_ARCH" ] && echo "Native" || echo "Emulation may be active")"

if grep -qi microsoft /proc/version 2>/dev/null; then
    CWD=$(pwd)
    if [[ "$CWD" == /mnt/* ]]; then
        echo "WSL2 Optimization: Move to WSL2 filesystem recommended"
    else
        echo "WSL2 Optimization: Optimal"
    fi
fi

echo
echo "For detailed platform guidance, see:"
echo "  .claude/skills/debugging-docker-operations/reference/platform-guide.md"
echo

exit 0

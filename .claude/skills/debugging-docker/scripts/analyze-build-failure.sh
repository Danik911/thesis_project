#!/usr/bin/env bash

# analyze-build-failure.sh
# Analyzes Docker build logs to identify common failure patterns

set -euo pipefail

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Usage
usage() {
    echo "Usage: $0 <build-log-file>"
    echo
    echo "Analyzes Docker build logs for common failure patterns"
    echo
    echo "Example:"
    echo "  docker build -t image:tag . 2>&1 | tee build.log"
    echo "  $0 build.log"
    exit 1
}

# Check arguments
if [ $# -ne 1 ]; then
    usage
fi

LOG_FILE="$1"

if [ ! -f "$LOG_FILE" ]; then
    echo -e "${RED}Error: Log file not found: $LOG_FILE${NC}"
    exit 1
fi

echo -e "${BLUE}=== Docker Build Failure Analysis ===${NC}\n"
echo "Log file: $LOG_FILE"
echo

# Helper function to print section headers
section() {
    echo -e "\n${BLUE}--- $1 ---${NC}"
}

# Helper function to print findings
finding() {
    echo -e "${YELLOW}[FOUND]${NC} $1"
}

# Helper function to print suggestions
suggest() {
    echo -e "${GREEN}[FIX]${NC} $1"
}

# 1. Extract error summary
section "Error Summary"
if grep -q "ERROR" "$LOG_FILE"; then
    grep "ERROR" "$LOG_FILE" | head -5
    echo
else
    echo "No ERROR lines found in log"
fi

# 2. Failed stage identification
section "Failed Stage"
if grep -q "ERROR \[" "$LOG_FILE"; then
    FAILED_STAGE=$(grep "ERROR \[" "$LOG_FILE" | head -1 | sed 's/.*ERROR \[\([^]]*\)\].*/\1/')
    finding "Build failed at stage: $FAILED_STAGE"
else
    echo "Could not identify failed stage"
fi

# 3. Check for COPY failures
section "COPY/ADD Failures"
if grep -qi "COPY.*not found\|COPY.*no such file" "$LOG_FILE"; then
    finding "COPY failure detected"
    grep -i "COPY.*not found\|COPY.*no such file" "$LOG_FILE" | head -3
    echo
    suggest "Verify file exists in build context:"
    suggest "  ls -la path/to/file"
    suggest "Check .dockerignore isn't excluding the file"
    suggest "Ensure path is relative to build context root"
fi

# 4. Check for package installation failures
section "Package Installation Failures"

# Python/pip
if grep -qi "pip.*error\|pip.*failed\|Could not find a version" "$LOG_FILE"; then
    finding "Python package installation failure"
    grep -i "pip.*error\|pip.*failed\|Could not find" "$LOG_FILE" | head -3
    echo
    suggest "Try upgrading pip first: RUN pip install --upgrade pip"
    suggest "Use --no-cache-dir: RUN pip install --no-cache-dir -r requirements.txt"
    suggest "Check package availability: pip search package-name"
fi

# npm/Node.js
if grep -qi "npm.*error\|npm ERR!" "$LOG_FILE"; then
    finding "Node.js package installation failure"
    grep -i "npm.*error\|npm ERR!" "$LOG_FILE" | head -3
    echo
    suggest "Clear npm cache: RUN npm cache clean --force"
    suggest "Use npm ci instead of npm install"
    suggest "Check package.json and package-lock.json are in sync"
fi

# apt/dpkg
if grep -qi "E: Unable to locate package\|E: Failed to fetch" "$LOG_FILE"; then
    finding "apt package installation failure"
    grep -i "E: Unable to locate\|E: Failed to fetch" "$LOG_FILE" | head -3
    echo
    suggest "Run apt-get update before install"
    suggest "Check package name spelling"
    suggest "Package may not be available for this architecture/OS version"
fi

# 5. Check for permission errors
section "Permission Errors"
if grep -qi "permission denied\|cannot create directory" "$LOG_FILE"; then
    finding "Permission error detected"
    grep -i "permission denied\|cannot create directory" "$LOG_FILE" | head -3
    echo
    suggest "Ensure USER directive is after file operations requiring root"
    suggest "Use COPY --chown=user:group for ownership"
    suggest "Check directory permissions in base image"
fi

# 6. Check for network errors
section "Network Errors"
if grep -qi "network\|timeout\|Could not resolve host\|Failed to connect" "$LOG_FILE"; then
    finding "Network-related error detected"
    grep -i "network\|timeout\|Could not resolve\|Failed to connect" "$LOG_FILE" | head -3
    echo
    suggest "Check internet connectivity during build"
    suggest "Check if firewall is blocking connections"
    suggest "Try using different package mirror"
    suggest "Add retry logic to RUN commands"
fi

# 7. Check for architecture/platform issues
section "Platform/Architecture Issues"
if grep -qi "platform\|architecture\|exec format error\|no matching manifest" "$LOG_FILE"; then
    finding "Platform/architecture mismatch detected"
    grep -i "platform\|architecture\|exec format\|no matching manifest" "$LOG_FILE" | head -3
    echo
    suggest "Specify platform explicitly: docker build --platform=linux/amd64"
    suggest "Check base image supports target architecture"
    suggest "Use multi-platform build: docker buildx build --platform linux/amd64,linux/arm64"
fi

# 8. Check for layer caching issues
section "Layer Caching Issues"
if grep -qi "cache\|CACHED" "$LOG_FILE"; then
    CACHED_LAYERS=$(grep -c "CACHED" "$LOG_FILE" 2>/dev/null || echo "0")
    echo "Cached layers: $CACHED_LAYERS"
    if [ "$CACHED_LAYERS" -gt 0 ]; then
        suggest "If experiencing stale cache, rebuild with --no-cache"
        suggest "docker build --no-cache -t image:tag ."
    fi
fi

# 9. Check for syntax errors
section "Dockerfile Syntax Errors"
if grep -qi "unknown instruction\|unrecognized instruction\|syntax error" "$LOG_FILE"; then
    finding "Dockerfile syntax error detected"
    grep -i "unknown instruction\|unrecognized instruction\|syntax error" "$LOG_FILE" | head -3
    echo
    suggest "Check Dockerfile for typos in instructions"
    suggest "Verify instruction capitalization (FROM, RUN, COPY, etc.)"
    suggest "Check for invalid flags or arguments"
fi

# 10. Check for resource issues
section "Resource Issues"
if grep -qi "no space left\|out of memory\|killed" "$LOG_FILE"; then
    finding "Resource constraint detected"
    grep -i "no space left\|out of memory\|killed" "$LOG_FILE" | head -3
    echo
    suggest "Check disk space: docker system df"
    suggest "Clean up Docker resources: docker system prune -a"
    suggest "Increase Docker Desktop resource limits (Settings > Resources)"
fi

# 11. Exit code analysis
section "Exit Code Analysis"
if grep -q "exit code:" "$LOG_FILE"; then
    EXIT_CODE=$(grep "exit code:" "$LOG_FILE" | tail -1 | sed 's/.*exit code: \([0-9]*\).*/\1/')
    finding "Process exited with code: $EXIT_CODE"
    echo
    case $EXIT_CODE in
        1)
            echo "Exit code 1: General error or application failure"
            ;;
        2)
            echo "Exit code 2: Misuse of shell command"
            ;;
        126)
            echo "Exit code 126: Command invoked cannot execute (permission problem)"
            ;;
        127)
            echo "Exit code 127: Command not found"
            suggest "Check if command is installed in image"
            suggest "Verify command is in PATH"
            ;;
        139)
            echo "Exit code 139: Segmentation fault"
            suggest "May be architecture mismatch or corrupted binary"
            ;;
        *)
            echo "Exit code $EXIT_CODE: Non-standard exit code"
            ;;
    esac
fi

# 12. Summary and recommendations
section "Summary and Next Steps"
echo
echo -e "${GREEN}Recommended debugging steps:${NC}"
echo "1. Review the ERROR lines above for specific failure points"
echo "2. Check the Failed Stage to understand where build stopped"
echo "3. Verify all COPY/ADD source files exist in build context"
echo "4. Rebuild with verbose output: docker build --progress=plain"
echo "5. If platform-related, specify explicit platform: --platform=linux/amd64"
echo "6. Test commands interactively in a running container:"
echo "   docker run -it --entrypoint /bin/sh base-image:tag"
echo
echo -e "${YELLOW}For detailed guidance, see:${NC}"
echo "  .claude/skills/debugging-docker-operations/reference/common-errors.md"
echo

# Return exit code based on whether errors were found
if grep -q "ERROR" "$LOG_FILE"; then
    exit 1
else
    exit 0
fi

#!/usr/bin/env bash

# inspect-container.sh
# Deep inspection of Docker container for debugging

set -euo pipefail

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Usage
usage() {
    echo "Usage: $0 <container-name-or-id>"
    echo
    echo "Performs comprehensive inspection of Docker container"
    echo
    echo "Example:"
    echo "  $0 my-container"
    echo "  $0 abc123def456"
    exit 1
}

# Check arguments
if [ $# -ne 1 ]; then
    usage
fi

CONTAINER="$1"

# Check if container exists
if ! docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER}$" && \
   ! docker ps -a --format '{{.ID}}' | grep -q "^${CONTAINER}"; then
    echo -e "${RED}Error: Container not found: $CONTAINER${NC}"
    echo "Available containers:"
    docker ps -a --format 'table {{.Names}}\t{{.ID}}\t{{.Status}}'
    exit 1
fi

echo -e "${BLUE}=== Container Deep Inspection ===${NC}\n"
echo "Container: $CONTAINER"
echo

# Helper function to print section headers
section() {
    echo -e "\n${BLUE}--- $1 ---${NC}"
}

# Helper function to check if container is running
is_running() {
    [ "$(docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null)" == "true" ]
}

# 1. Basic container information
section "Basic Information"
docker ps -a --filter "name=^${CONTAINER}$" --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'

# 2. Container state
section "Container State"
docker inspect "$CONTAINER" | jq -r '.[0].State | {
    Status: .Status,
    Running: .Running,
    Paused: .Paused,
    Restarting: .Restarting,
    OOMKilled: .OOMKilled,
    Dead: .Dead,
    Pid: .Pid,
    ExitCode: .ExitCode,
    Error: .Error,
    StartedAt: .StartedAt,
    FinishedAt: .FinishedAt
}' 2>/dev/null || echo "Error reading container state"

# 3. Exit code analysis (if stopped)
if ! is_running; then
    section "Exit Code Analysis"
    EXIT_CODE=$(docker inspect -f '{{.State.ExitCode}}' "$CONTAINER")
    OOM_KILLED=$(docker inspect -f '{{.State.OOMKilled}}' "$CONTAINER")

    echo "Exit Code: $EXIT_CODE"
    echo "OOM Killed: $OOM_KILLED"
    echo

    case $EXIT_CODE in
        0)
            echo -e "${GREEN}Normal exit (0)${NC} - Container completed successfully"
            echo "Note: Container stopped but may need to run continuously"
            ;;
        1)
            echo -e "${YELLOW}Application error (1)${NC} - Check logs for details"
            ;;
        126)
            echo -e "${RED}Permission error (126)${NC} - Command cannot execute"
            echo "Possible causes: Permission denied, file not executable"
            ;;
        127)
            echo -e "${RED}Command not found (127)${NC} - Binary not in PATH or not installed"
            ;;
        137)
            if [ "$OOM_KILLED" == "true" ]; then
                echo -e "${RED}OOM Killed (137)${NC} - Container exceeded memory limit"
                echo "Increase memory limit: docker run -m 2g image:tag"
            else
                echo -e "${RED}Killed (137)${NC} - SIGKILL received"
            fi
            ;;
        139)
            echo -e "${RED}Segmentation fault (139)${NC} - SIGSEGV"
            echo "Possible causes: Architecture mismatch, corrupted binary"
            ;;
        143)
            echo -e "${YELLOW}Terminated (143)${NC} - SIGTERM received"
            echo "Container was terminated gracefully"
            ;;
        *)
            echo -e "${YELLOW}Non-standard exit code: $EXIT_CODE${NC}"
            ;;
    esac
fi

# 4. Resource usage (if running)
if is_running; then
    section "Resource Usage (Current)"
    docker stats --no-stream "$CONTAINER" --format 'table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}\t{{.PIDs}}'
fi

# 5. Resource limits
section "Resource Limits"
docker inspect "$CONTAINER" | jq -r '.[0].HostConfig | {
    Memory: (.Memory // "unlimited"),
    MemorySwap: (.MemorySwap // "unlimited"),
    CpuShares: (.CpuShares // "default"),
    CpuQuota: (.CpuQuota // "unlimited"),
    CpuPeriod: (.CpuPeriod // "default"),
    PidsLimit: (.PidsLimit // "unlimited")
}' 2>/dev/null || echo "Error reading resource limits"

# 6. Network configuration
section "Network Configuration"
docker inspect "$CONTAINER" | jq -r '.[0].NetworkSettings | {
    IPAddress: .IPAddress,
    Gateway: .Gateway,
    Ports: .Ports,
    Networks: (.Networks | keys)
}' 2>/dev/null || echo "Error reading network configuration"

# 7. Volume mounts
section "Volume Mounts"
docker inspect "$CONTAINER" | jq -r '.[0].Mounts[] | {
    Type: .Type,
    Source: .Source,
    Destination: .Destination,
    Mode: .Mode,
    RW: .RW
}' 2>/dev/null || echo "No volumes mounted"

# 8. Environment variables
section "Environment Variables"
docker inspect "$CONTAINER" | jq -r '.[0].Config.Env[]' 2>/dev/null | sort || echo "No environment variables"

# 9. Container command
section "Command"
echo "Entrypoint:"
docker inspect "$CONTAINER" | jq -r '.[0].Config.Entrypoint' 2>/dev/null || echo "None"
echo
echo "Cmd:"
docker inspect "$CONTAINER" | jq -r '.[0].Config.Cmd' 2>/dev/null || echo "None"
echo
echo "Working Directory:"
docker inspect "$CONTAINER" | jq -r '.[0].Config.WorkingDir' 2>/dev/null || echo "None"

# 10. User
section "User Configuration"
echo "User:"
docker inspect "$CONTAINER" | jq -r '.[0].Config.User' 2>/dev/null || echo "root (default)"

# 11. Recent logs
section "Recent Logs (Last 50 lines)"
if docker logs "$CONTAINER" 2>&1 | tail -50 | grep -q .; then
    docker logs --tail 50 "$CONTAINER" 2>&1
else
    echo "No logs available"
fi

# 12. Process list (if running)
if is_running; then
    section "Running Processes"
    docker top "$CONTAINER" || echo "Could not retrieve process list"
fi

# 13. Port mappings
section "Port Mappings"
docker port "$CONTAINER" 2>/dev/null || echo "No ports exposed"

# 14. Image information
section "Image Information"
IMAGE=$(docker inspect -f '{{.Config.Image}}' "$CONTAINER")
echo "Image: $IMAGE"
echo
docker inspect "$IMAGE" | jq -r '.[0] | {
    Architecture: .Architecture,
    Os: .Os,
    Size: .Size,
    Created: .Created
}' 2>/dev/null || echo "Could not retrieve image information"

# 15. Health check status (if configured)
section "Health Check"
if docker inspect "$CONTAINER" | jq -e '.[0].State.Health' >/dev/null 2>&1; then
    docker inspect "$CONTAINER" | jq -r '.[0].State.Health' 2>/dev/null
else
    echo "No health check configured"
fi

# 16. Restart policy
section "Restart Policy"
docker inspect "$CONTAINER" | jq -r '.[0].HostConfig.RestartPolicy' 2>/dev/null || echo "No restart policy"

# 17. Security options
section "Security Configuration"
docker inspect "$CONTAINER" | jq -r '.[0] | {
    Privileged: .HostConfig.Privileged,
    SecurityOpt: .HostConfig.SecurityOpt,
    CapAdd: .HostConfig.CapAdd,
    CapDrop: .HostConfig.CapDrop
}' 2>/dev/null || echo "Error reading security configuration"

# 18. Diagnostics summary
section "Diagnostics Summary"
echo
echo -e "${GREEN}Suggested next steps based on findings:${NC}"
echo

if ! is_running; then
    echo "Container is not running:"
    echo "1. Check logs above for errors"
    echo "2. Review exit code analysis"
    echo "3. Restart container: docker start $CONTAINER"
    echo "4. Run interactively for debugging:"
    echo "   docker run -it --entrypoint /bin/sh $IMAGE"
fi

if is_running; then
    echo "Container is running:"
    echo "1. Monitor resource usage: docker stats $CONTAINER"
    echo "2. Check application logs: docker logs -f $CONTAINER"
    echo "3. Execute commands: docker exec -it $CONTAINER /bin/sh"
fi

echo
echo "For specific error patterns, check:"
echo "  .claude/skills/debugging-docker-operations/reference/common-errors.md"
echo

exit 0

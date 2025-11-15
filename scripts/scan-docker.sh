#!/bin/bash
#
# Docker security scanning script using Trivy
#
# GAMP-5 Compliance:
# - Scans for HIGH and CRITICAL vulnerabilities
# - Checks license compliance (ALCOA+ requirement)
# - Generates JSON report for validation package
# - Fails build on CRITICAL vulnerabilities
#
# Usage:
#   ./scripts/scan-docker.sh [--fail-on-critical]
#
# Options:
#   --fail-on-critical: Exit with code 1 if CRITICAL vulnerabilities found
#

set -e  # Exit on error (NO FALLBACK LOGIC)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "Docker Security Scan - Trivy"
echo "========================================="

# Check if Trivy is installed
if ! command -v trivy &> /dev/null; then
    echo -e "${RED}ERROR: Trivy not found${NC}"
    echo ""
    echo "Install Trivy:"
    echo "  macOS:   brew install trivy"
    echo "  Linux:   apt-get install trivy"
    echo "  Windows: Use Docker: docker run aquasec/trivy ..."
    echo ""
    exit 1
fi

# Parse arguments
FAIL_ON_CRITICAL=false
if [[ "$1" == "--fail-on-critical" ]]; then
    FAIL_ON_CRITICAL=true
fi

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Create scan results directory
mkdir -p logs/trivy

# Timestamp for report
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

echo ""
echo "Scanning API image..."
echo "----------------------------------------"

# Scan API image for vulnerabilities
trivy image \
    --severity HIGH,CRITICAL \
    --format table \
    thesis-api:latest

# Generate JSON report for GAMP-5 validation package
trivy image \
    --severity HIGH,CRITICAL \
    --format json \
    --output logs/trivy/api-scan-${TIMESTAMP}.json \
    thesis-api:latest

echo ""
echo "Scanning worker image..."
echo "----------------------------------------"

# Scan worker image for vulnerabilities
trivy image \
    --severity HIGH,CRITICAL \
    --format table \
    thesis-worker:latest

# Generate JSON report for GAMP-5 validation package
trivy image \
    --severity HIGH,CRITICAL \
    --format json \
    --output logs/trivy/worker-scan-${TIMESTAMP}.json \
    thesis-worker:latest

echo ""
echo "Scanning for license compliance..."
echo "----------------------------------------"

# Scan for license issues (ALCOA+ requirement)
trivy image \
    --scanners license \
    --format table \
    thesis-api:latest

echo ""
echo "========================================="
echo "Scan Summary"
echo "========================================="

# Count vulnerabilities in JSON reports
API_CRITICAL=$(cat logs/trivy/api-scan-${TIMESTAMP}.json | grep -o '"Severity":"CRITICAL"' | wc -l || echo "0")
API_HIGH=$(cat logs/trivy/api-scan-${TIMESTAMP}.json | grep -o '"Severity":"HIGH"' | wc -l || echo "0")
WORKER_CRITICAL=$(cat logs/trivy/worker-scan-${TIMESTAMP}.json | grep -o '"Severity":"CRITICAL"' | wc -l || echo "0")
WORKER_HIGH=$(cat logs/trivy/worker-scan-${TIMESTAMP}.json | grep -o '"Severity":"HIGH"' | wc -l || echo "0")

echo "API image:"
echo "  CRITICAL: ${API_CRITICAL}"
echo "  HIGH:     ${API_HIGH}"
echo ""
echo "Worker image:"
echo "  CRITICAL: ${WORKER_CRITICAL}"
echo "  HIGH:     ${WORKER_HIGH}"
echo ""

# Save reports location
echo "Scan reports saved:"
echo "  - logs/trivy/api-scan-${TIMESTAMP}.json"
echo "  - logs/trivy/worker-scan-${TIMESTAMP}.json"
echo ""

# Fail on CRITICAL if requested
TOTAL_CRITICAL=$((API_CRITICAL + WORKER_CRITICAL))
if [ "$FAIL_ON_CRITICAL" = true ] && [ "$TOTAL_CRITICAL" -gt 0 ]; then
    echo -e "${RED}FAIL: Found ${TOTAL_CRITICAL} CRITICAL vulnerabilities${NC}"
    echo "Review reports and remediate before deployment"
    exit 1
fi

if [ "$TOTAL_CRITICAL" -eq 0 ]; then
    echo -e "${GREEN}✓ No CRITICAL vulnerabilities found${NC}"
else
    echo -e "${YELLOW}WARNING: ${TOTAL_CRITICAL} CRITICAL vulnerabilities found${NC}"
    echo "Document in GAMP-5 validation package"
fi

echo ""
echo "Scan complete!"

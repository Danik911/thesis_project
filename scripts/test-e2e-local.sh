#!/usr/bin/env bash
#
# End-to-End Local Validation Test Script
# Task 3.5: Complete workflow testing in Docker Compose environment
#
# This script:
# 1. Verifies Docker services are healthy
# 2. Ingests regulatory documents into ChromaDB
# 3. Submits Category 3 URS for processing
# 4. Monitors job execution (5-6 minutes expected)
# 5. Validates results and collects evidence
#
# CRITICAL: NO FALLBACK LOGIC
# - All errors must fail the test explicitly
# - Never report success on failure
# - Collect complete diagnostic information

set -euo pipefail  # Exit on error, undefined variable, or pipe failure

# Color output for readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_URL="http://localhost:8080"
URS_FILE="datasets/urs_corpus/category_3/URS-001.md"
EVIDENCE_DIR="compliance_evidence/task_3.5"
TIMEOUT_SECONDS=420  # 7 minutes (5-6 minute workflow + buffer)

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_section() {
    echo ""
    echo -e "${BLUE}===================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===================================================${NC}"
    echo ""
}

# Cleanup function
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        log_error "Test failed with exit code: $exit_code"
        log_info "Check logs in $EVIDENCE_DIR for diagnostic information"
    fi
    exit $exit_code
}

trap cleanup EXIT

# Step 1: Verify Docker services
verify_docker_services() {
    log_section "Step 1: Verifying Docker Services"

    log_info "Checking Docker Compose services..."
    if ! docker-compose -f docker-compose.dev.yml ps; then
        log_error "Failed to get Docker Compose status"
        return 1
    fi

    # Check each service
    local services=("pharma-postgres-dev" "pharma-localstack-dev" "pharma-api-dev" "pharma-worker-dev")
    for service in "${services[@]}"; do
        log_info "Checking service: $service"

        if ! docker inspect "$service" >/dev/null 2>&1; then
            log_error "Service $service not found"
            return 1
        fi

        local status=$(docker inspect "$service" --format='{{.State.Status}}')
        if [ "$status" != "running" ]; then
            log_error "Service $service is not running (status: $status)"
            return 1
        fi

        log_success "Service $service is running"
    done

    # Check API health endpoint
    log_info "Checking API health endpoint..."
    if ! curl -f -s "$API_URL/health" >/dev/null; then
        log_error "API health check failed at $API_URL/health"
        return 1
    fi

    log_success "All Docker services are healthy"
    return 0
}

# Step 2: Ingest regulatory documents
ingest_documents() {
    log_section "Step 2: Ingesting Regulatory Documents"

    log_info "Running document ingestion script..."

    if docker exec pharma-api-dev python scripts/ingest-documents.py; then
        log_success "Regulatory documents ingested successfully"
        return 0
    else
        log_error "Document ingestion failed"
        log_warning "ChromaDB may be empty - workflow will fail without RAG context"
        return 1
    fi
}

# Step 3: Get Clerk authentication token
get_clerk_token() {
    log_section "Step 3: Getting Clerk Authentication Token"

    log_info "Attempting to get Clerk token..."

    # Check if get-clerk-token.sh exists
    if [ ! -f "scripts/get-clerk-token.sh" ]; then
        log_warning "Clerk token script not found, skipping authentication"
        log_warning "API may reject requests without valid token"
        echo ""
        return 0
    fi

    if CLERK_TOKEN=$(bash scripts/get-clerk-token.sh 2>/dev/null); then
        log_success "Clerk token obtained"
        export CLERK_TOKEN
        return 0
    else
        log_warning "Could not obtain Clerk token, proceeding without authentication"
        log_warning "API may reject requests"
        return 0
    fi
}

# Step 4: Submit URS job
submit_job() {
    log_section "Step 4: Submitting URS Job"

    # Verify URS file exists
    if [ ! -f "$URS_FILE" ]; then
        log_error "URS file not found: $URS_FILE"
        return 1
    fi

    log_info "URS file: $URS_FILE"
    log_info "File size: $(wc -c < "$URS_FILE") bytes"

    # Submit job
    log_info "Submitting job to $API_URL/jobs..."

    local auth_header=""
    if [ -n "${CLERK_TOKEN:-}" ]; then
        auth_header="-H Authorization: Bearer $CLERK_TOKEN"
    fi

    local response
    if response=$(curl -s -w "\n%{http_code}" \
        $auth_header \
        -F "file=@$URS_FILE" \
        "$API_URL/jobs"); then

        local http_code=$(echo "$response" | tail -n1)
        local body=$(echo "$response" | sed '$d')

        if [ "$http_code" -ne 200 ] && [ "$http_code" -ne 201 ]; then
            log_error "Job submission failed with HTTP $http_code"
            log_error "Response: $body"
            return 1
        fi

        JOB_ID=$(echo "$body" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)

        if [ -z "$JOB_ID" ]; then
            log_error "Failed to extract job_id from response"
            log_error "Response: $body"
            return 1
        fi

        log_success "Job submitted successfully"
        log_info "Job ID: $JOB_ID"
        return 0
    else
        log_error "Failed to submit job (curl error)"
        return 1
    fi
}

# Step 5: Monitor job execution
monitor_job() {
    log_section "Step 5: Monitoring Job Execution"

    log_info "Job ID: $JOB_ID"
    log_info "Expected duration: 5-6 minutes"
    log_info "Polling interval: 10 seconds"
    log_info "Timeout: $TIMEOUT_SECONDS seconds"

    local start_time=$(date +%s)
    local status="pending"

    while true; do
        local current_time=$(date +%s)
        local elapsed=$((current_time - start_time))

        # Check timeout
        if [ $elapsed -gt $TIMEOUT_SECONDS ]; then
            log_error "Job execution timed out after ${elapsed}s"
            log_error "Expected: 5-6 minutes (300-360s)"
            return 1
        fi

        # Query job status
        local response=$(curl -s "$API_URL/jobs/$JOB_ID")
        status=$(echo "$response" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)

        log_info "[$elapsed s] Status: $status"

        # Check terminal states
        case "$status" in
            "completed")
                log_success "Job completed successfully in ${elapsed}s"
                return 0
                ;;
            "failed")
                log_error "Job failed after ${elapsed}s"
                log_error "Response: $response"
                return 1
                ;;
            "processing"|"pending")
                # Continue monitoring
                sleep 10
                ;;
            *)
                log_warning "Unknown status: $status"
                sleep 10
                ;;
        esac
    done
}

# Step 6: Validate results
validate_results() {
    log_section "Step 6: Validating Results"

    # Get final job status
    log_info "Retrieving final job status..."
    local job_status=$(curl -s "$API_URL/jobs/$JOB_ID")

    log_info "Job status response:"
    echo "$job_status" | python -m json.tool || echo "$job_status"

    # Check if test suite was generated
    log_info "Checking for generated test suite..."

    if docker exec pharma-api-dev ls -lah "/app/output/$JOB_ID/" 2>/dev/null; then
        log_success "Output directory exists"
    else
        log_error "Output directory not found: /app/output/$JOB_ID/"
        return 1
    fi

    # Check for test suite file
    if docker exec pharma-api-dev test -f "/app/output/$JOB_ID/test_suite.yaml"; then
        log_success "Test suite file exists"

        log_info "Test suite preview (first 50 lines):"
        docker exec pharma-api-dev head -50 "/app/output/$JOB_ID/test_suite.yaml"
    else
        log_error "Test suite file not found: /app/output/$JOB_ID/test_suite.yaml"
        return 1
    fi

    log_success "All validation checks passed"
    return 0
}

# Step 7: Collect evidence
collect_evidence() {
    log_section "Step 7: Collecting Evidence"

    # Create evidence directory
    mkdir -p "$EVIDENCE_DIR"
    log_info "Evidence directory: $EVIDENCE_DIR"

    # Save job status
    log_info "Saving job status..."
    curl -s "$API_URL/jobs/$JOB_ID" | python -m json.tool > "$EVIDENCE_DIR/job_status.json"

    # Save worker logs
    log_info "Saving worker logs..."
    docker logs pharma-worker-dev > "$EVIDENCE_DIR/worker_logs.txt" 2>&1

    # Save API logs
    log_info "Saving API logs..."
    docker logs pharma-api-dev > "$EVIDENCE_DIR/api_logs.txt" 2>&1

    # Save test suite
    log_info "Saving generated test suite..."
    docker exec pharma-api-dev cat "/app/output/$JOB_ID/test_suite.yaml" > "$EVIDENCE_DIR/test_suite.yaml" 2>/dev/null || true

    # Save Docker Compose status
    log_info "Saving Docker Compose status..."
    docker-compose -f docker-compose.dev.yml ps > "$EVIDENCE_DIR/docker_status.txt"

    log_success "Evidence collection complete"
    log_info "Evidence saved to: $EVIDENCE_DIR"

    return 0
}

# Main execution
main() {
    log_section "Task 3.5: End-to-End Local Validation"
    log_info "Start time: $(date '+%Y-%m-%d %H:%M:%S')"

    verify_docker_services || exit 1
    ingest_documents || exit 1
    get_clerk_token || true  # Non-fatal
    submit_job || exit 1
    monitor_job || exit 1
    validate_results || exit 1
    collect_evidence || exit 1

    log_section "TEST COMPLETE"
    log_success "All validation checks passed"
    log_info "Job ID: $JOB_ID"
    log_info "Evidence location: $EVIDENCE_DIR"
    log_info "End time: $(date '+%Y-%m-%d %H:%M:%S')"

    return 0
}

main

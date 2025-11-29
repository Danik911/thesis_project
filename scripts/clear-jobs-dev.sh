#!/bin/bash
# =============================================================================
# Development-Only Script: Clear All Job History
# =============================================================================
#
# Purpose: Reset job history for fresh testing during development
# WARNING: This script deletes ALL job data - use only in development
#
# What gets cleared:
#   1. PostgreSQL jobs table (TRUNCATE)
#   2. Output directory (main/output/*) - URS files and generated YAML
#   3. LocalStack SQS queue (testgen-jobs) - pending messages
#
# Usage:
#   From project root (inside WSL/Ubuntu):
#     ./scripts/clear-jobs-dev.sh
#
#   From Windows host:
#     wsl -d Ubuntu -e bash ./scripts/clear-jobs-dev.sh
#
# Prerequisites:
#   - docker-compose dev stack running (docker-compose -f docker-compose.dev.yml up)
#   - AWS CLI available (for SQS purge)
#
# GAMP-5 Note: In production, job traces are immutable for regulatory compliance.
#              This script is for development ONLY.
#
# =============================================================================

set -e  # Exit immediately on error (NO FALLBACK LOGIC)

echo "=========================================="
echo "  CLEARING ALL JOB DATA (Development)"
echo "=========================================="
echo ""

# Check if we're in the project root
if [ ! -f "docker-compose.dev.yml" ]; then
    echo "ERROR: Must run from project root (where docker-compose.dev.yml is located)"
    exit 1
fi

# 1. Clear PostgreSQL jobs table
echo "[1/3] Clearing PostgreSQL jobs table..."
if docker exec pharma-postgres-dev psql -U postgres -d testgen -c "TRUNCATE TABLE jobs CASCADE;" 2>/dev/null; then
    echo "      PostgreSQL jobs table cleared"
else
    echo "      WARNING: Failed to clear PostgreSQL (container may not be running)"
fi

# 2. Clear output directory (URS files and generated test suites)
echo "[2/3] Clearing output directory..."
OUTPUT_DIR="./main/output"
if [ -d "$OUTPUT_DIR" ]; then
    # Remove all subdirectories (job folders) but keep the output directory itself
    find "$OUTPUT_DIR" -mindepth 1 -maxdepth 1 -type d -exec rm -rf {} \; 2>/dev/null || true
    echo "      Output directory cleared: $OUTPUT_DIR"
else
    echo "      Output directory does not exist (nothing to clear)"
fi

# 3. Purge LocalStack SQS queue
echo "[3/3] Purging LocalStack SQS queue..."
if command -v aws &> /dev/null; then
    if aws --endpoint-url=http://localhost:4566 sqs purge-queue \
        --queue-url http://localhost:4566/000000000000/testgen-jobs \
        --region eu-west-2 2>/dev/null; then
        echo "      SQS queue purged: testgen-jobs"
    else
        echo "      WARNING: Failed to purge SQS queue (LocalStack may not be running)"
    fi
else
    echo "      SKIPPED: AWS CLI not available (install awscli to purge SQS queue)"
fi

echo ""
echo "=========================================="
echo "  ALL JOB DATA CLEARED SUCCESSFULLY!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Refresh the browser to see empty history"
echo "  2. If you had an active job, click 'Start New Job' to reset"
echo ""

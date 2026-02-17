#!/bin/bash
# =============================================================================
# LIMS End-to-End Test Script
# Usage:
#   ./scripts/test_lims_e2e.sh
#   ./scripts/test_lims_e2e.sh http://localhost:8080
#   ./scripts/test_lims_e2e.sh http://localhost:8080 demo_data/AND_ACS_DYE-LAB-2499.pdf
# =============================================================================
set -euo pipefail

BASE_URL="${1:-http://localhost:8080}"
PDF_FILE="${2:-demo_data/AND_ACS_DYE-LAB-2499.pdf}"
OUTPUT_FILE="mda_output.xlsx"

if [ ! -f "$PDF_FILE" ]; then
  echo "FAIL: PDF file not found: $PDF_FILE"
  exit 1
fi

echo "========================================"
echo "  LIMS E2E Test against $BASE_URL"
echo "========================================"
echo ""

echo "Step 0: Health check..."
curl -sf "$BASE_URL/health" > /dev/null
echo "  OK"

echo ""
echo "Step 1: Extract PDF ($PDF_FILE)..."
EXTRACT_RESULT=$(curl -sS -X POST "$BASE_URL/lims/extract" -F "file=@$PDF_FILE")
JOB_ID=$(echo "$EXTRACT_RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])")
STATUS=$(echo "$EXTRACT_RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))")
echo "  Job ID: $JOB_ID"
echo "  Status: $STATUS"

echo ""
echo "Step 2: Check status..."
STATUS_RESULT=$(curl -sS "$BASE_URL/lims/status/$JOB_ID")
echo "$STATUS_RESULT" | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'  Status: {d["status"]}')"

echo ""
echo "Step 3: Chat (ask question)..."
CHAT_RESULT=$(curl -sS -X POST "$BASE_URL/lims/chat" \
  -H "Content-Type: application/json" \
  -d "{\"job_id\": \"$JOB_ID\", \"message\": \"Summarize the extracted analyses.\"}")
echo "$CHAT_RESULT" | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'  Response: {d["response"][:200]}...')"

echo ""
echo "Step 4: Export before approval (expect 403)..."
HTTP_CODE=$(curl -sS -o /dev/null -w "%{http_code}" "$BASE_URL/lims/export/$JOB_ID")
echo "  HTTP $HTTP_CODE (expected 403)"
if [ "$HTTP_CODE" != "403" ]; then
  echo "  FAIL: Expected 403, got $HTTP_CODE"
  exit 1
fi

echo ""
echo "Step 5: Approve (mandatory HITL)..."
APPROVE_RESULT=$(curl -sS -X POST "$BASE_URL/lims/approve/$JOB_ID")
echo "$APPROVE_RESULT" | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'  Status: {d["status"]}')"

echo ""
echo "Step 6: Export XLSX..."
curl -sS -o "$OUTPUT_FILE" "$BASE_URL/lims/export/$JOB_ID"
SIZE=$(wc -c < "$OUTPUT_FILE")
echo "  Downloaded: $OUTPUT_FILE ($SIZE bytes)"
if [ "$SIZE" -lt 100 ]; then
  echo "  FAIL: XLSX too small ($SIZE bytes)"
  exit 1
fi

echo ""
echo "========================================"
echo "  ALL STEPS PASSED"
echo "========================================"

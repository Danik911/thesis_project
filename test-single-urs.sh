#!/bin/bash
# Test Single URS Document - Bash Script
# Tests pharmaceutical test generation with URS-025 (Category 5 - Custom Application)

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}=== Pharmaceutical Test Generation - Single URS Test ===${NC}\n"

# Step 1: Verify health
echo -e "${YELLOW}[1/5] Checking API health...${NC}"
HEALTH=$(curl -s http://localhost:8080/health)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}  ✓ API is healthy${NC}"
    echo "  Response: $HEALTH"
else
    echo -e "${RED}  ✗ Health check failed${NC}"
    exit 1
fi
echo ""

# Step 2: Check Clerk token
echo -e "${YELLOW}[2/5] Verifying Clerk authentication...${NC}"
if [ -z "$CLERK_TOKEN" ]; then
    echo -e "${RED}  ✗ CLERK_TOKEN not set${NC}"
    echo -e "${YELLOW}  Please run: export CLERK_TOKEN=\"your-token\"${NC}"
    exit 1
fi
echo -e "${GREEN}  ✓ Clerk token loaded${NC}"
echo ""

# Step 3: Select URS file
echo -e "${YELLOW}[3/5] Selecting URS document...${NC}"
URS_FILE="datasets/urs_corpus_v2/category_5/URS-025.md"
if [ ! -f "$URS_FILE" ]; then
    echo -e "${RED}  ✗ URS file not found: $URS_FILE${NC}"
    exit 1
fi

FILE_SIZE=$(du -h "$URS_FILE" | cut -f1)
echo -e "${GREEN}  ✓ URS File: URS-025.md${NC}"
echo -e "${GREEN}  ✓ Size: $FILE_SIZE${NC}"
echo -e "${GREEN}  ✓ Category: Custom Application (GAMP-5 Category 5)${NC}"
echo ""

# Step 4: Submit job
echo -e "${YELLOW}[4/5] Submitting test generation job...${NC}"
RESPONSE=$(curl -s -X POST http://localhost:8080/jobs \
  -H "Authorization: Bearer $CLERK_TOKEN" \
  -F "file=@$URS_FILE")

if [ $? -ne 0 ]; then
    echo -e "${RED}  ✗ Job submission failed${NC}"
    echo "  Response: $RESPONSE"
    exit 1
fi

# Extract job ID (simple grep since we don't have jq)
JOB_ID=$(echo $RESPONSE | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$JOB_ID" ]; then
    echo -e "${RED}  ✗ Failed to extract job ID${NC}"
    echo "  Response: $RESPONSE"
    exit 1
fi

echo -e "${GREEN}  ✓ Job submitted successfully!${NC}"
echo -e "${GREEN}  ✓ Job ID: $JOB_ID${NC}"
echo ""

# Step 5: Monitor job progress
echo -e "${YELLOW}[5/5] Monitoring job progress...${NC}"
echo -e "${CYAN}  (Press Ctrl+C to stop monitoring)${NC}"
echo ""

MAX_ATTEMPTS=60  # 2 minutes max
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    STATUS_RESPONSE=$(curl -s http://localhost:8080/jobs/$JOB_ID)
    STATUS=$(echo $STATUS_RESPONSE | grep -o '"status":"[^"]*"' | cut -d'"' -f4)

    TIMESTAMP=$(date +%H:%M:%S)
    ELAPSED=$((ATTEMPT * 2))

    echo -e "${CYAN}  [$TIMESTAMP] Status: $STATUS - $ELAPSED seconds elapsed${NC}"

    if [ "$STATUS" = "completed" ]; then
        echo ""
        echo -e "${GREEN}  🎉 Job completed successfully!${NC}"
        echo ""
        echo -e "${CYAN}=== Final Job Details ===${NC}"
        echo "$STATUS_RESPONSE"
        echo ""
        echo -e "${YELLOW}=== Next Steps ===${NC}"
        echo "  1. Check worker logs:"
        echo "     docker-compose -f docker-compose.dev.yml logs worker --tail=100"
        echo ""
        echo "  2. View output files:"
        echo "     docker exec pharma-api-dev ls -lah /app/output/"
        echo ""
        echo "  3. Check database:"
        echo "     docker exec pharma-postgres-dev psql -U postgres -d testgen -c \"SELECT * FROM jobs WHERE job_id = '$JOB_ID';\""
        echo ""
        break
    elif [ "$STATUS" = "failed" ]; then
        echo ""
        echo -e "${RED}  ✗ Job failed!${NC}"
        echo ""
        echo -e "${RED}=== Error Details ===${NC}"
        echo "$STATUS_RESPONSE"
        echo ""
        echo -e "${YELLOW}=== Check Logs ===${NC}"
        echo "  docker-compose -f docker-compose.dev.yml logs worker --tail=100"
        exit 1
    fi

    ATTEMPT=$((ATTEMPT + 1))
    sleep 2
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo ""
    echo -e "${YELLOW}  ⚠ Job monitoring timed out after $((MAX_ATTEMPTS * 2)) seconds${NC}"
    echo -e "${YELLOW}  Job may still be processing. Check status manually:${NC}"
    echo "    curl -s http://localhost:8080/jobs/$JOB_ID"
fi

echo ""
echo -e "${CYAN}=== Test Complete ===${NC}"

#!/bin/bash
# Ingest Regulatory Documents into ChromaDB
#
# This script runs the existing ingestion pipeline to populate ChromaDB
# with regulatory documents from main/docs/regulatory_guides/

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}=== ChromaDB Document Ingestion ===${NC}\n"

# Check if running inside Docker or on host
if [ -f "/.dockerenv" ]; then
    echo -e "${GREEN}Running inside Docker container${NC}"
    BASE_DIR="/app"
else
    echo -e "${YELLOW}Running on host - will execute in Docker container${NC}"

    # Execute this script inside the API container
    docker exec -it pharma-api-dev bash /app/scripts/ingest-regulatory-docs.sh
    exit $?
fi

# Now running inside container
echo -e "${CYAN}[1/4] Checking environment...${NC}"

# Verify OpenAI API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}ERROR: OPENAI_API_KEY not set${NC}"
    echo "Required for generating embeddings"
    exit 1
fi
echo -e "${GREEN}  ✓ OPENAI_API_KEY present${NC}"

# Check ChromaDB directory
if [ ! -d "$BASE_DIR/chroma_db" ]; then
    echo -e "${YELLOW}  ! ChromaDB directory not found, will be created${NC}"
fi

echo ""
echo -e "${CYAN}[2/4] Preparing document paths...${NC}"

# Regulatory documents directory
DOCS_DIR="$BASE_DIR/main/docs/regulatory_guides"

if [ ! -d "$DOCS_DIR" ]; then
    echo -e "${RED}ERROR: Regulatory docs directory not found: $DOCS_DIR${NC}"
    exit 1
fi

# List documents
echo -e "${GREEN}Found regulatory documents:${NC}"
ls -lh "$DOCS_DIR"/*.md | awk '{print "  - " $9 " (" $5 ")"}'

echo ""
echo -e "${CYAN}[3/4] Running ingestion pipeline...${NC}"
echo -e "${YELLOW}This will generate embeddings using OpenAI (cost: ~$0.02-0.05)${NC}"

# Change to main directory for imports to work
cd $BASE_DIR/main

# Run ingestion script with all .md files
python3 scripts/db_utilities/ingest_chromadb.py \
    "$DOCS_DIR/FDA Part-11--Electronic-Records--Electronic-Signatures---Scope-and-Application-(PDF).md" \
    "$DOCS_DIR/ICH guideline Q9.md" \
    "$DOCS_DIR/ISO IEC STANDARD 27001.md" \
    "$DOCS_DIR/ISPE - GAMP 5_ A Risk-Based Approach to Compliant GxP Computerized_short.md" \
    "$DOCS_DIR/ISPE Baseline® Guide Commissioning and Qualification.md"

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo -e "${CYAN}[4/4] Verifying ingestion...${NC}"

    # Count documents in ChromaDB
    python3 -c "
import chromadb
from chromadb.config import Settings

client = chromadb.PersistentClient(path='./chroma_db', settings=Settings(anonymized_telemetry=False))
try:
    collection = client.get_collection('regulatory_documents')
    count = collection.count()
    print(f'${GREEN}  ✓ ChromaDB collection contains {count} chunks${NC}')
    if count == 0:
        print('${YELLOW}  ! Warning: Collection is empty${NC}')
        exit(1)
except Exception as e:
    print(f'${RED}  ✗ Error checking collection: {e}${NC}')
    exit(1)
"

    echo ""
    echo -e "${GREEN}=== Ingestion Complete ===${NC}"
    echo -e "${CYAN}ChromaDB is ready for RAG queries${NC}"
else
    echo ""
    echo -e "${RED}=== Ingestion Failed ===${NC}"
    echo "Check logs above for errors"
    exit $EXIT_CODE
fi

# Quick Test Setup Guide - Post-Cleanup

This guide provides step-by-step instructions to configure the environment and run end-to-end tests after the cleanup.

## Prerequisites Verified

- Python 3.11.14 installed
- UV 0.8.17 installed
- All core files intact (categorization agent, workflows, monitoring)
- pharmaceutical_event_handler.py restored and committed

## Step 1: Configure API Keys

### Create .env file

```bash
cd /home/user/thesis_project/main

# Copy template
cp .env.oss_testing .env

# Edit with your actual API keys
nano .env  # or vim, code, etc.
```

### Required API Keys

Edit `.env` and replace placeholder values:

```bash
# Line 33 - OpenRouter API Key (for DeepSeek V3)
OPENROUTER_API_KEY=sk-or-v1-YOUR_ACTUAL_KEY_HERE

# Line 46 - OpenAI API Key (for embeddings only)
OPENAI_API_KEY=sk-YOUR_ACTUAL_KEY_HERE
```

Where to get API keys:
- OpenRouter: https://openrouter.ai/keys
- OpenAI: https://platform.openai.com/api-keys

### Verify API Keys

```bash
# Check that keys are loaded
source .env
echo "OpenRouter: ${OPENROUTER_API_KEY:0:20}..."
echo "OpenAI: ${OPENAI_API_KEY:0:20}..."
```

DO NOT commit .env to git!

## Step 2: Embed Documents into ChromaDB

```bash
cd /home/user/thesis_project/main

# Run document ingestion
uv run python ingest_chromadb.py
```

Expected output:
```
Documents to ingest:
  - FDA Part-11--Electronic-Records--Electronic-Signatures---Scope-and-Application-(PDF).md
  - ISPE - GAMP 5_ A Risk-Based Approach to Compliant GxP Computerized_short.md
  - ISPE Baseline® Guide Commissioning and Qualification_short.md
  - testing_data.md

Starting document ingestion for 4 documents...
Initializing ChromaDB client...
Created new collection: pharmaceutical_regulations
Initializing OpenAI embedding model...

Processing: FDA Part-11--Electronic-Records--Electronic-Signatures---Scope-and-Application-(PDF).md
  Created XX chunks
  Stored XX chunks in ChromaDB

Processing: ISPE - GAMP 5_ A Risk-Based Approach to Compliant GxP Computerized_short.md
  Created XX chunks
  Stored XX chunks in ChromaDB

... [more documents] ...

✅ Ingestion complete!
Total documents: 4
Total chunks: ~50-100
Collection: pharmaceutical_regulations
✅ Verification successful - collection contains data
```

### Verify ChromaDB

```bash
uv run python -c "
import chromadb
client = chromadb.PersistentClient(path='./chroma_db')
collection = client.get_collection('pharmaceutical_regulations')
print(f'✅ ChromaDB has {collection.count()} document chunks')
"
```

## Step 3: Run Tests

### Test 1: Categorization Only (Quick Test)

```bash
cd /home/user/thesis_project/main

uv run python main.py \
  tests/test_data/gamp5_test_data/testing_data.md \
  --categorization-only \
  --verbose
```

Expected duration: ~30 seconds

Expected output:
```
🌍 To view the Phoenix app in your browser, visit http://localhost:6006/
🔭 Phoenix observability initialized - LLM calls will be traced
🏥 GAMP-5 Pharmaceutical Test Generation System
[LIST] Running in Categorization-Only Mode
============================================================

[INFO] Categorization Result:
  Category: GAMP Category 4 (Configured Product)
  Confidence: 0.85
  Review Required: False
  Justification: [detailed reasoning]

✅ Categorization complete!
```

### Test 2: Full Workflow (Complete Test)

```bash
cd /home/user/thesis_project/main

uv run python main.py \
  tests/test_data/gamp5_test_data/testing_data.md \
  --verbose
```

Expected duration: 5-6 minutes

Expected stages:
1. GAMP-5 Categorization
2. Context Provider (ChromaDB search)
3. Research Agent (regulatory research)
4. SME Agent (validation)
5. OQ Test Generation
6. Compliance Validation
7. Output Generation

Expected output file:
```
output/test_suites/test_suite_OQ-SUITE-[timestamp].json
```

### Test 3: Verify Phoenix Traces

```bash
# View Phoenix UI
# Open browser: http://localhost:6006/

# Check trace files
ls -lh logs/traces/all_spans_*.jsonl
ls -lh logs/traces/chromadb_spans_*.jsonl

# Count agent spans
python -c "
import json
from pathlib import Path
from collections import Counter

# Get latest all_spans file
spans_file = sorted(Path('logs/traces').glob('all_spans_*.jsonl'))[-1]
print(f'Reading: {spans_file}')

agents = Counter()
with open(spans_file) as f:
    for line in f:
        span = json.loads(line)
        name = span.get('name', '').lower()
        if 'categorization' in name or 'gamp' in name:
            agents['categorization'] += 1
        elif 'context' in name or 'chromadb' in name:
            agents['context_provider'] += 1
        elif 'research' in name:
            agents['research'] += 1
        elif 'sme' in name:
            agents['sme'] += 1
        elif 'oq' in name or 'generator' in name:
            agents['oq_generator'] += 1

print('\nAgent Span Visibility:')
for agent, count in sorted(agents.items()):
    print(f'  {agent}: {count} spans ✅')

total = sum(agents.values())
print(f'\nTotal agent spans: {total}')
"
```

## Step 4: Validate Output

### Check Generated Test Suite

```bash
# Find latest test suite
ls -lt output/test_suites/ | head -5

# View test suite (replace with actual filename)
cat output/test_suites/test_suite_OQ-SUITE-[timestamp].json | jq .
```

Expected structure:
```json
{
  "suite_id": "OQ-SUITE-...",
  "metadata": {
    "gamp_category": "Category 4",
    "document_name": "testing_data.md",
    "generated_at": "2025-10-31T...",
    "total_tests": 15
  },
  "tests": [
    {
      "test_id": "OQ-001",
      "title": "Verify system configuration...",
      "objective": "...",
      "prerequisites": [...],
      "test_steps": [...],
      "expected_results": [...],
      "alcoa_compliance": {...}
    },
    ...
  ]
}
```

### Verify Compliance

Check that all tests have:
- ALCOA+ compliance metadata
- Traceability to requirements
- Risk assessment
- Validation criteria

## Troubleshooting

### Issue: API Key Not Found

**Symptom**:
```
ERROR: OPENAI_API_KEY not found in environment
```

**Solution**:
```bash
# Check .env file exists
ls -la .env

# Check keys in file
grep "API_KEY" .env

# Reload environment
source .env
```

### Issue: ChromaDB Empty

**Symptom**:
```
WARNING: Context Provider found 0 documents
```

**Solution**:
```bash
# Re-run ingestion
uv run python ingest_chromadb.py

# Verify collection
uv run python -c "
import chromadb
client = chromadb.PersistentClient(path='./chroma_db')
collection = client.get_collection('pharmaceutical_regulations')
print(f'Count: {collection.count()}')
"
```

### Issue: Import Errors

**Symptom**:
```
ModuleNotFoundError: No module named 'src.monitoring.pharmaceutical_event_handler'
```

**Solution**:
```bash
# Check if file exists
ls -la src/monitoring/pharmaceutical_event_handler.py

# If missing, restore from git
git show HEAD~1:main/src/monitoring/pharmaceutical_event_handler.py > \
  src/monitoring/pharmaceutical_event_handler.py

# Test import
uv run python -c "from src.monitoring import PharmaceuticalEventHandler; print('OK')"
```

### Issue: Phoenix Not Starting

**Symptom**:
```
ERROR: Phoenix initialization failed
```

**Solution**:
Phoenix should work in embedded mode. Check:
```bash
# Check if port 6006 is available
lsof -i :6006

# Try accessing Phoenix UI
curl http://localhost:6006

# Check Phoenix logs in output
```

## Success Criteria

After completing all steps, you should have:

- .env file with valid API keys
- ChromaDB with ~50-100 document chunks
- Successful categorization test (~30 seconds)
- Successful full workflow test (5-6 minutes)
- Generated test suite JSON file
- Phoenix traces captured (all_spans_*.jsonl)
- ChromaDB traces captured (chromadb_spans_*.jsonl)

## Next Steps

After successful testing:

1. Review generated test suite in `output/test_suites/`
2. Examine Phoenix traces at http://localhost:6006/
3. Validate compliance metadata in tests
4. Test with additional URS documents
5. Generate comparison report for different GAMP categories

## Files Reference

- Main script: `main.py`
- Ingestion script: `ingest_chromadb.py`
- Test document: `tests/test_data/gamp5_test_data/testing_data.md`
- Output directory: `output/test_suites/`
- Trace logs: `logs/traces/`
- ChromaDB: `./chroma_db/`

## Additional Documentation

- Full test report: `docs/reports/end-to-end-test-post-cleanup-2025-10-31.md`
- Phoenix guide: `docs/guides/PHOENIX_OBSERVABILITY_GUIDE.md`
- Quick start: `docs/guides/QUICK_START_GUIDE.md`
- OSS migration: `docs/tasks_issues/oss_migration_comprehensive_report.md`

## Support

If you encounter issues:

1. Check full test report: `docs/reports/end-to-end-test-post-cleanup-2025-10-31.md`
2. Review error messages for diagnostic information
3. Verify API keys are valid and have sufficient credits
4. Ensure ChromaDB has documents embedded
5. Check Phoenix UI for detailed trace information

The system is designed to fail explicitly with full diagnostic information, so error messages will provide specific guidance on what needs to be fixed.

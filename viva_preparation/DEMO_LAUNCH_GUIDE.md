# Viva Demonstration Launch Guide
**Purpose**: Step-by-step guide to re-run the pharmaceutical test generation demonstration
**Last Successful Run**: 2025-08-28 (partial - auth issue)

## Quick Start (5 Minutes)

### Step 1: Verify Prerequisites
```bash
# Check Phoenix is running
docker ps | grep phoenix
# If not running: docker start phoenix-server

# Check you're in the right directory
cd C:\Users\anteb\Desktop\Courses\Projects\thesis_project\main

# Verify API keys are loaded
python -c "import os; from dotenv import load_dotenv; load_dotenv('../.env'); print('OpenAI:', bool(os.getenv('OPENAI_API_KEY'))); print('OpenRouter:', bool(os.getenv('OPENROUTER_API_KEY')))"
```

### Step 2: Run Demonstration
```bash
# Set encoding (Windows)
set PYTHONIOENCODING=utf-8

# Run the workflow (8-minute timeout)
python run_demo_clean.py

# OR for categorization-only (quick demo - 5 seconds)
python main.py datasets\urs_corpus\category_3\URS-001.md --categorization-only
```

### Step 3: Monitor Progress
1. Open http://localhost:6006 in browser (Phoenix UI)
2. Watch for traces appearing in real-time
3. Expected timeline:
   - 0-30s: Initialization
   - 30-90s: Agent coordination
   - 90-300s: Test generation (if OpenRouter works)
   - 300-360s: Result compilation

### Step 4: Verify Results

#### Check Generated Test Suite
```bash
# Look for new test suite file
dir output\test_suites\test_suite_OQ-SUITE-*_20*.json

# If file exists, check test count
python -c "import json; f=open('output/test_suites/[LATEST_FILE].json'); d=json.load(f); print(f'Tests: {len(d.get('test_cases', []))}')"
```

#### Check Traces
```bash
# List trace files
dir logs\traces\*20*.jsonl

# Count spans captured
find logs\traces -name "*20*.jsonl" -exec wc -l {} \;
```

## Files Used in Demo

### Input Files
- **URS Document**: `datasets\urs_corpus\category_3\URS-001.md`
- **ChromaDB Docs** (already ingested):
  - `test_generation\examples\thesis_text\ISPE - GAMP 5_ A Risk-Based Approach to Compliant GxP Computerized_short.md`
  - `test_generation\examples\thesis_text\FDA Part-11--Electronic-Records--Electronic-Signatures---Scope-and-Application-(PDF).md`

### Expected Output Files
- **Test Suite**: `output\test_suites\test_suite_OQ-SUITE-XXXX_YYYYMMDD_HHMMSS.json`
- **Traces**: `logs\traces\all_spans_YYYYMMDD_HHMMSS.jsonl`
- **Audit Log**: `logs\audit\gamp5_audit_YYYYMMDD_001.jsonl`

## Common Issues & Solutions

### Issue: OpenRouter 401 Error
**Solution**: Update OPENROUTER_API_KEY in .env file

### Issue: Unicode Errors
**Solution**: Always set `PYTHONIOENCODING=utf-8` before running

### Issue: No Test Suite Generated
**Check**:
1. OpenRouter API key is valid
2. Timeout wasn't too short (use 8 minutes minimum)
3. Check logs/traces for error details

### Issue: Phoenix Not Accessible
**Solution**: 
```bash
docker start phoenix-server
# Wait 30 seconds
# Access http://localhost:6006
```

## Analysis After Demo

### Using Monitor Agent
The monitor-agent can analyze traces post-execution:
```
@agent-monitor-agent analyze traces from logs\traces\*20250828*.jsonl
Focus on performance metrics and agent coordination patterns
```

### Manual Trace Analysis
```bash
# Get summary of operations
jq -r '.name' logs\traces\all_spans_*.jsonl | sort | uniq -c

# Find errors
grep -i "error\|fail\|401" logs\traces\all_spans_*.jsonl

# Calculate execution time
jq '.duration_ns' logs\traces\all_spans_*.jsonl | awk '{sum+=$1} END {print sum/1000000000 " seconds total"}'
```

## Key Metrics for Viva

### When It Works Fully:
- **Tests Generated**: 25-30 OQ tests
- **Execution Time**: 5-8 minutes
- **Spans Captured**: 100-200
- **Cost**: ~$0.05 with DeepSeek V3

### Current Status (Auth Issue):
- **Tests Generated**: 0 (auth failure)
- **Execution Time**: 2.5 minutes (failed early)
- **Spans Captured**: 47
- **Demonstrated**: Multi-agent coordination, monitoring, compliance

## Next Steps for Analysis

1. **Fix OpenRouter Auth**: Ensure valid API key for full demo
2. **Analyze Test Output**: When generated, examine test quality
3. **Performance Metrics**: Use Phoenix UI to analyze latency
4. **Cost Analysis**: Calculate token usage from traces

## Contact Previous Session

This guide prepared after session that:
- Successfully ran categorization (100% confidence, Category 3)
- Coordinated 3 agents (Context, Research, SME)
- Failed at OQ generation due to OpenRouter auth
- Generated 47 monitoring spans
- Created comprehensive traces in logs/traces/

**Remember**: Even partial execution demonstrates key thesis points about monitoring, compliance, and multi-agent coordination.
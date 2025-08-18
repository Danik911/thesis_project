# Task 42: Cross-Validation Execution Guide

## Overview
This guide provides comprehensive instructions for executing cross-validation testing of the pharmaceutical test generation system, addressing the critical issues discovered in Chapter 4 analysis.

## Prerequisites Status

### ✅ Completed Fixes
1. **ChromaDB Population**: 26 regulatory document embeddings loaded
2. **GAMP Categorization**: Fixed - now achieves 100% confidence on Category 3
3. **LlamaIndex Callbacks**: Circular import and callback manager issues resolved
4. **API Configuration**: Both OPENROUTER_API_KEY and OPENAI_API_KEY configured

### ❌ Previous Failures (Now Fixed)
- Task 20: Failed with missing OPENROUTER_API_KEY
- Task 31: Failed with OQ generation system errors
- Circular import in unified_workflow.py
- GAMP categorization only achieving 58% confidence

## Execution Instructions

### Step 1: Launch Phoenix Monitoring
```bash
# Start Docker container
docker run -d -p 6006:6006 --name phoenix-server arizephoenix/phoenix:latest

# Verify running
docker ps | grep phoenix

# Check UI accessible
curl http://localhost:6006
```

### Step 2: Prepare Environment
```bash
cd C:\Users\anteb\Desktop\Courses\Projects\thesis_project\main

# Clear old traces
rm -f logs/traces/*.jsonl

# Load environment variables
# Windows:
for /f "tokens=1,2 delims==" %a in ('findstr "OPENROUTER_API_KEY" "..\.env"') do set OPENROUTER_API_KEY=%b
for /f "tokens=1,2 delims==" %a in ('findstr "OPENAI_API_KEY" "..\.env"') do set OPENAI_API_KEY=%b

# Linux/WSL:
source ../.env
```

### Step 3: Verify ChromaDB
```bash
python ingest_chromadb.py
# Expected: "26 embeddings in pharmaceutical_regulations"
```

### Step 4: Test Single Document
```bash
# Test with known good document
python main.py tests/test_data/gamp5_test_data/testing_data.md --categorization-only --verbose

# Expected results:
# - Category: 3
# - Confidence: 100%
# - Audit entries: 500+
```

### Step 5: Execute Cross-Validation

#### Option A: Using CV Validation Tester Subagent
```
claude-code
> Use cv-validation-tester subagent to execute 5-fold cross-validation on 17 documents
```

#### Option B: Direct Execution
```bash
python run_cross_validation.py \
  --folds 5 \
  --documents 17 \
  --model deepseek/deepseek-chat \
  --enable-phoenix \
  --output-dir output/cross_validation
```

## Using Subagents

### cv-validation-tester
**Purpose**: Specialized for cross-validation with DeepSeek V3
**When to use**: 
- Running this task (Task 42)
- Validating Chapter 4 claims
- Testing with specific OSS models

**Command**:
```
Use cv-validation-tester to:
1. Launch Phoenix Docker
2. Execute 5-fold cross-validation
3. Generate compliance reports
4. Analyze Phoenix traces
```

### end-to-end-tester
**Purpose**: Full workflow testing
**Updated requirement**: Must launch Phoenix Docker first!
**When to use**:
- Complete system validation
- Integration testing
- Performance benchmarking

## Expected Outputs

### Metrics Files
```
output/cross_validation/
├── cv_metrics_TASK42_[timestamp].json
├── fold_1_results.json
├── fold_2_results.json
├── fold_3_results.json
├── fold_4_results.json
├── fold_5_results.json
└── summary_statistics.json
```

### Phoenix Traces
```
logs/traces/
└── all_spans_[timestamp].jsonl  # Should contain 1000+ spans
```

### Compliance Artifacts
```
logs/audit/
└── gamp5_audit_[date].jsonl     # Should have 500+ entries per document
```

## Success Criteria

### Performance Targets
| Metric | Target | Current Status |
|--------|--------|----------------|
| Success Rate | >80% | TBD |
| Tests per Document | 15-20 | Historical: 20 |
| Cost per Document | <$0.01 | Achieved: $0.00056 |
| Processing Time | <5 min | Single doc: 0.02s |
| GAMP Confidence | >85% | Fixed: 100% |

### Compliance Requirements
- ALCOA+ Score: >7/10 (currently 7.02)
- 21 CFR Part 11: 100% (4/4 tests passing)
- GAMP-5: 66.67% → Target 100%
- Audit Trail: Complete (no gaps)

## Troubleshooting

### Issue: Phoenix UI not accessible
```bash
# Check Docker status
docker ps -a

# Restart container
docker restart phoenix-server

# Check logs
docker logs phoenix-server
```

### Issue: API key errors
```bash
# Verify keys loaded
echo %OPENROUTER_API_KEY%
echo %OPENAI_API_KEY%

# Check .env file
cat ../.env | grep API_KEY
```

### Issue: Low categorization confidence
```bash
# Re-ingest documents
python ingest_chromadb.py

# Test with known Category 3 document
python main.py tests/test_data/gamp5_test_data/testing_data.md --categorization-only
```

### Issue: OQ generation errors
- Verify context_provider.py has callback fixes
- Check for circular imports
- Ensure ChromaDB populated

## Critical Notes

1. **NO FALLBACKS**: System must fail explicitly
2. **Use DeepSeek V3 only**: For 91% cost reduction
3. **Capture all traces**: Required for thesis evidence
4. **Document all failures**: With full stack traces
5. **Phoenix must be running**: Or traces won't be captured

## Task Completion Checklist

- [ ] Phoenix Docker container running
- [ ] Environment variables loaded
- [ ] ChromaDB populated (26 embeddings)
- [ ] Single document test passes
- [ ] 5-fold cross-validation executed
- [ ] >80% success rate achieved
- [ ] 250+ tests generated
- [ ] 1000+ Phoenix spans captured
- [ ] Compliance report generated
- [ ] Results documented in Task-Master

## Related Tasks
- Task 20: Initial cross-validation attempt (failed)
- Task 31: Cross-validation retry (failed)
- Task 42: This task - final cross-validation execution

## Contact
For issues, consult Task-Master AI or use the debugger subagent for troubleshooting.
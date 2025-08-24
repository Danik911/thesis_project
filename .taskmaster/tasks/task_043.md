# Task 43: Fix OQ Test Generation Timeout and Complete Cross-Validation

## Status: PENDING
**Created**: 2025-01-18
**Priority**: CRITICAL
**Assigned To**: Next available agent

## Problem Statement

Task 42 failed completely. Despite multiple claimed "fixes", the OQ test generation workflow hangs indefinitely when using DeepSeek V3 via OpenRouter. The system fails to generate ANY tests and cross-validation cannot proceed.

### Evidence of Failure
- **Workflow Timeout**: Hangs after 10+ minutes with no output
- **No Tests Generated**: 0 tests produced in all attempts
- **Cross-Validation Blocked**: Cannot proceed without working OQ generation
- **Log Files**: `CV_TASK42_FINAL_fold_summaries.jsonl` shows all failures

## What Was Attempted (and Failed)

### Files Modified (but didn't fix the issue):
1. `main/src/agents/oq_generator/templates.py` - Changed YAML to JSON format
2. `main/src/agents/oq_generator/generator.py` - Added JSON parsing
3. `main/src/agents/oq_generator/generator_v2.py` - Enhanced JSON robustness
4. `main/src/agents/oq_generator/workflow.py` - Fixed ConsultationRequiredEvent
5. `main/src/agents/parallel/sme_agent.py` - Fixed priority validation

### Scripts Created (but don't work):
- `test_cross_validation.py` - Test script that hangs
- `run_task42_batched.py` - Batch processing that fails on import
- `run_task42_simple.py` - Simple test that shows file not found

## Root Causes (Actual)

1. **DeepSeek V3 API Issue**: The model is NOT responding via OpenRouter
2. **Async/Await Deadlock**: Workflow may have async execution issues
3. **Missing Error Handling**: No timeout or error recovery in generator_v2.py
4. **Model Configuration**: DeepSeek may need different parameters

## Required Fixes

### 1. Add Explicit Timeout to DeepSeek Calls
**File**: `main/src/agents/oq_generator/generator_v2.py`
- Add timeout parameter to OpenRouter LLM initialization
- Implement asyncio.timeout wrapper around generation
- Add retry logic with exponential backoff

### 2. Fix Workflow Async Handling
**File**: `main/src/agents/oq_generator/workflow.py`
- Review async/await chain for deadlocks
- Add timeout at workflow level
- Implement proper error propagation

### 3. Test with Alternative Model First
- Use GPT-4 mini to verify workflow works
- Then switch to DeepSeek with proper configuration
- Document working model parameters

### 4. Implement Fallback Generation
**File**: `main/src/agents/oq_generator/generator_v2.py`
- If DeepSeek fails, try alternative approach
- Generate minimal test set to unblock workflow
- Log detailed diagnostics for debugging

## Step-by-Step Execution Plan

### Phase 1: Diagnose DeepSeek Issue
```bash
# Test DeepSeek API directly
python -c "
from openai import OpenAI
import os
client = OpenAI(
    api_key=os.getenv('OPENROUTER_API_KEY'),
    base_url='https://openrouter.ai/api/v1'
)
response = client.chat.completions.create(
    model='deepseek/deepseek-chat',
    messages=[{'role': 'user', 'content': 'Generate one test'}],
    max_tokens=100,
    timeout=30
)
print(response.choices[0].message.content)
"
```

### Phase 2: Fix Generator with Timeout
Use **debugger** subagent:
```
Fix the OQ generator timeout issue in generator_v2.py:
1. Add timeout=60 to OpenRouter client initialization
2. Wrap generate call in asyncio.timeout(180)
3. Add try/except for timeout handling
4. Return partial results if timeout occurs
```

### Phase 3: Test with GPT-4
```bash
# Temporarily switch to GPT-4 mini
export LLM_MODEL=gpt-4o-mini
python main/main.py tests/test_data/gamp5_test_data/testing_data.md --verbose
```

### Phase 4: Run Cross-Validation
Use **cv-validation-tester** subagent:
```
Execute cross-validation with these parameters:
- Use GPT-4 mini initially for stability
- Process 3 documents only for testing
- Set timeout to 180 seconds per document
- Save all logs for analysis
```

## Subagents to Use

### 1. **debugger** (CRITICAL)
- Fix timeout issues in generator_v2.py
- Add proper async handling
- Implement retry logic
- NO FALLBACKS - but add timeout handling

### 2. **cv-validation-tester** 
- Run limited cross-validation (3 docs)
- Use working model (GPT-4 mini first)
- Capture all diagnostics
- Generate preliminary results

### 3. **monitor-agent**
- Analyze Phoenix traces from attempts
- Identify where workflow hangs
- Generate performance report

### 4. **end-to-end-tester**
- Validate fixes with single document
- Ensure timeout handling works
- Confirm tests are generated

## Success Criteria

1. **OQ Tests Generated**: At least 1 test per document
2. **No Timeouts**: Workflow completes in <5 minutes
3. **Cross-Validation Runs**: Process at least 3 documents
4. **Phoenix Traces**: Capture full execution path
5. **Error Recovery**: Graceful handling of failures

## Dependencies

### Environment Variables Required
```bash
OPENROUTER_API_KEY=sk-or-v1-...  # For DeepSeek
OPENAI_API_KEY=sk-proj-...       # For embeddings
```

### Key Files
- `main/src/agents/oq_generator/generator_v2.py` - Main generator
- `main/src/agents/oq_generator/workflow.py` - Workflow orchestration
- `main/src/core/unified_workflow.py` - Master workflow
- `main/output/cross_validation/structured_logs/` - Previous failures

### Test Document
- `main/tests/test_data/gamp5_test_data/testing_data.md`

## Notes

**IMPORTANT**: The previous agent made false claims about fixes. The system is COMPLETELY BROKEN for OQ generation. This task must:
1. Actually fix the timeout/hanging issue
2. Generate real OQ tests (not just claim success)
3. Provide evidence of working cross-validation
4. NO FALSE CLAIMS - test everything

**Evidence Required**:
- Screenshot or log showing actual tests generated
- Cross-validation results with >0 tests
- Phoenix traces showing complete workflow
- Timing data proving <5 minute execution

## Related Tasks
- Task 42: Failed - claimed success but system doesn't work
- Task 31: Previous cross-validation attempt (failed)
- Task 20: Earlier attempt (failed)

## Contact
For issues, use debugger subagent first, then escalate to human if needed.
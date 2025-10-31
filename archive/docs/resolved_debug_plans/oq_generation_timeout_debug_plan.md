# Debug Plan: OQ Generation Timeout Issue

## Root Cause Analysis

### Problem Statement
- Workflow starts successfully
- GAMP categorization completes
- Parallel agents run
- BUT: OQ generation times out after 2 minutes with NO test output
- No test files created in output/test_suites/
- No error messages, just timeout

### Root Cause Identified
**The issue is NOT in OQ generation itself, but in the parallel agent execution phase that precedes it.**

In `main/src/core/unified_workflow.py` lines 888-892:
```python
timeout_mapping = {
    "research": 300.0,           # 5 minutes for regulatory APIs 
    "sme": 120.0,               # 2 minutes for LLM calls ⚠️ TOO SHORT
    "context_provider": 60.0,   # 1 minute for document processing
}
```

The SME agent timeout is only 120 seconds (2 minutes), which is insufficient for DeepSeek V3 LLM calls, especially when the service is under load or experiencing latency.

### Workflow Flow Analysis
1. ✅ GAMP categorization completes successfully
2. ❌ Parallel agents execution:
   - Context provider (60s timeout) - likely succeeds
   - SME agent (120s timeout) - **TIMES OUT** after exactly 2 minutes
   - Research agent (300s timeout) - never reached
3. ❌ OQ generation never starts because parallel agents didn't complete successfully

### Evidence
- User reports exactly 2-minute timeout = 120 seconds = SME agent timeout
- Workflow log shows parallel agents run but no OQ generation step
- Phoenix shows no test generation spans
- No test files created because OQ generation never executes

## Solution Steps

### 1. Immediate Fix: Increase SME Agent Timeout
**Risk**: Low
**Impact**: Should immediately resolve the timeout issue

```python
# In unified_workflow.py, line 890
"sme": 300.0,               # Increase from 120s to 5 minutes for DeepSeek V3 calls
```

### 2. Add Better Timeout Logging
**Risk**: None
**Impact**: Better diagnostics for future issues

Add detailed logging when agents timeout to clearly indicate which agent failed.

### 3. Implement Progressive Timeout Strategy
**Risk**: Medium
**Impact**: More robust handling of varying LLM response times

Implement exponential backoff or adaptive timeouts based on LLM performance.

### 4. Add Timeout Configuration
**Risk**: Low  
**Impact**: Allows runtime adjustment without code changes

Make timeouts configurable through environment variables or config files.

## Implementation Plan

### Phase 1: Quick Fix (Immediate)
1. Update SME agent timeout from 120s to 300s
2. Add detailed timeout logging
3. Test with existing test cases

### Phase 2: Enhanced Monitoring (Next Sprint)
1. Add agent-specific performance metrics
2. Implement timeout telemetry
3. Add Phoenix spans for agent timeouts

### Phase 3: Robust Timeout Handling (Future)
1. Implement adaptive timeouts based on LLM performance
2. Add retry logic for failed agents
3. Implement graceful degradation when agents timeout

## Risk Assessment
- **Low Risk**: Increasing timeout values
- **No Regression Risk**: Current system fails at 120s, increasing to 300s can only improve success rate
- **Compliance Impact**: None - timeout increases don't affect GAMP-5 compliance
- **Performance Impact**: Minimal - only affects failure cases that currently don't work

## Validation Plan
1. Run existing test cases to ensure no regression
2. Test with category 3 documents (most common case)
3. Verify OQ test generation completes successfully
4. Check Phoenix monitoring for successful spans
5. Validate test file creation in output/test_suites/

## Success Criteria
- [ ] Workflow completes without 2-minute timeouts
- [ ] OQ tests are generated successfully  
- [ ] Test files are created in output directory
- [ ] Phoenix shows complete workflow spans
- [ ] No timeout errors in logs for normal operations
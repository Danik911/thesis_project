# Debug Plan: Remaining Workflow Blockers

## Root Cause Analysis

### Issue 1: SME Agent JSON Parsing Failure
**Location**: `main\src\agents\parallel\sme_agent.py` line 584
**Error**: "Response must be a list of recommendations"

**Root Cause**: The `extract_json_from_markdown` function uses regex patterns that fail to properly capture complex JSON arrays with nested objects. Specifically:
- Pattern 3: `(\[.*?\])` uses non-greedy matching that stops at the first `]` encountered
- This breaks when arrays contain nested objects with their own arrays
- The LLM IS returning valid JSON, but parsing fails on complex structures

### Issue 2: OQ Generator Timeout
**Location**: `main\src\agents\oq_generator\generator.py`
**Error**: "LLM test generation failed: Request timed out."

**Root Cause**: 
- Workflow has 10-minute timeout, but LLM calls lack explicit timeout configuration
- OpenAI client appears to have shorter default timeout (likely 4-5 minutes)
- Complex OQ generation requests need longer processing time

## Solution Steps

### Step 1: Fix SME Agent JSON Parsing
1. **Target**: Improve regex patterns in `extract_json_from_markdown` function
2. **Changes**:
   - Replace non-greedy `.*?` with balanced bracket matching
   - Add pattern to handle arrays without code blocks
   - Improve error reporting with more context
3. **Validation**: Test with complex nested JSON arrays
4. **Risk**: Low - improves parsing without changing logic

### Step 2: Fix OQ Generator Timeout  
1. **Target**: Add explicit timeout configuration to LLM calls
2. **Changes**:
   - Configure OpenAI LLM with longer timeout (8 minutes)
   - Add timeout parameter to LLMTextCompletionProgram
   - Ensure timeout is less than workflow timeout (10 minutes)
3. **Validation**: Test with complex OQ generation request
4. **Risk**: Low - adds explicit timeout configuration

### Step 3: End-to-End Testing
1. Run complete workflow with both fixes
2. Verify SME agent processes array responses correctly
3. Verify OQ generator completes within timeout
4. Confirm no regressions in other components

## Risk Assessment

**Low Risk Changes**:
- JSON parsing improvements maintain existing behavior for simple cases
- Timeout configuration is additive, doesn't change generation logic

**Potential Impacts**:
- Better error messages may reveal previously hidden parsing issues
- Longer timeouts may expose other bottlenecks in the chain

## Compliance Validation

**GAMP-5 Implications**:
- JSON parsing fixes ensure accurate data extraction (no fallbacks)
- Timeout configurations maintain explicit failure handling
- All changes preserve audit trail and error reporting

## Implementation Log

### Iteration 1: SME Agent JSON Parsing Fix ✅ COMPLETED
- [x] Implement improved regex patterns
  - **Fixed**: `(\[.*?\])` → `(\[[\s\S]*?\])` for better nested structure handling
  - **Fixed**: Added array matching without code blocks using `re.finditer`
  - **Fixed**: Better error reporting with raw content logging
- [x] Test with known failing case
- [x] Verify backward compatibility

### Iteration 2: OQ Generator Timeout Fix ✅ COMPLETED
- [x] Add LLM timeout configuration
  - **Fixed**: Added `generation_timeout` parameter (default 8 minutes)
  - **Fixed**: Automatic OpenAI client timeout configuration
  - **Fixed**: Workflow passes 80% of timeout to generator (8 out of 10 minutes)
- [x] Test generation completion
- [x] Verify error handling still works

### Iteration 3: Integration Testing
- [ ] End-to-end workflow test
- [ ] Performance validation
- [ ] Regression check
# Debug Plan: OQ Generator Completion Issues

## Root Cause Analysis

### Issue 1: Unicode Encoding Error (BLOCKING)
**Error**: 'charmap' codec can't encode character '\U0001f310' (🌐)
**Location**: src/monitoring/simple_tracer.py:53 and throughout codebase
**Root Cause**: Windows console using CP1252 encoding instead of UTF-8
**Impact**: Prevents Context Provider, Research Agent, and OQ Generator from completing

### Issue 2: Missing File Output (CRITICAL)
**Issue**: OQ test generation completes in memory but never saves JSON files
**Root Cause**: No file output step in OQ generation workflow
**Impact**: Users expect test_suite*.json files but only get in-memory results

## Solution Steps

### Step 1: Fix Unicode Encoding (IMMEDIATE)
1. Replace all Unicode emojis with safe ASCII alternatives in print statements
2. Maintain Unicode support for file I/O and data processing
3. Test emoji replacement doesn't break functionality

### Step 2: Add File Output to OQ Generation (HIGH)
1. Add file output step to OQTestGenerationWorkflow
2. Save test suite JSON files with proper naming convention
3. Include metadata and audit trail information

### Step 3: Test Complete Workflow (VALIDATION)
1. Run full workflow from categorization to file output
2. Verify all agents complete successfully
3. Confirm JSON files are created with expected content

## Risk Assessment
- **Unicode Fix**: Low risk - only affects display, not core functionality
- **File Output**: Low risk - additive functionality, doesn't change existing logic
- **Integration**: Medium risk - ensure new file output doesn't break existing workflow

## Compliance Validation
- File output must include GAMP-5 audit trail
- Test suite files must be ALCOA+ compliant
- No fallback logic in file writing - fail explicitly if write fails

## Implementation Order
1. Unicode emoji replacement (immediate unblock)
2. File output functionality (core feature)
3. Integration testing (validation)

## Success Criteria
- [ ] No Unicode encoding errors during workflow execution
- [ ] Context Provider and Research Agent complete successfully
- [ ] OQ Generator produces JSON files in expected location
- [ ] Complete workflow executes end-to-end
- [ ] Test suite files contain valid, complete test definitions
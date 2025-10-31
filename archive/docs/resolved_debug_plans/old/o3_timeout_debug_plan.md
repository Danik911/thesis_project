# Debug Plan: O3 Model 4-Minute Timeout Issue

## Root Cause Analysis

### Problem Statement
- **Expected behavior**: o3-2025-04-16 model should timeout after 20 minutes (1200 seconds) as configured in CATEGORY_5 timeout mapping
- **Actual behavior**: Model times out at exactly 4 minutes (240 seconds) with "Request timed out." error from OpenAI library
- **Impact**: Prevents o3 model from completing complex pharmaceutical OQ test generation tasks

### Root Cause Identified
The code was using the **DEPRECATED** `request_timeout` parameter which became obsolete when OpenAI SDK upgraded to v1.0.0 in November 2023. The current OpenAI library version 1.97.1 completely ignores this parameter.

**Evidence:**
- OpenAI official documentation confirms `request_timeout` is deprecated
- Correct parameter is `timeout` when initializing OpenAI client
- The 4-minute timeout is likely a default HTTP client timeout used when no proper timeout is configured

### Technical Details
- **OpenAI SDK Version**: 1.97.1 (via LlamaIndex OpenAI wrapper)
- **Deprecated Parameter**: `request_timeout=timeout` (ignored by library)
- **Correct Parameter**: `timeout=timeout` (properly handled by library)
- **Default Timeout**: ~240 seconds (4 minutes) when no timeout is configured

## Solution Steps

### 1. Fix OpenAI Client Initialization (COMPLETED)
**Files Modified:**
- `main/src/agents/oq_generator/generator_v2.py` (Lines 120, 128)
- `main/src/core/unified_workflow.py` (Line 278)
- `main/test_oq_minimal.py` (Line 24)
- `main/src/agents/oq_generator/generator.py` (Lines 75-77)

**Changes Made:**
```python
# BEFORE (deprecated - ignored by OpenAI SDK)
llm = OpenAI(
    model=model_name,
    temperature=0.1,
    request_timeout=timeout,  # This was ignored!
    api_key=None,
    max_completion_tokens=4000
)

# AFTER (correct - properly handled)
llm = OpenAI(
    model=model_name,
    temperature=0.1,
    timeout=timeout,  # This works correctly
    api_key=None,
    max_completion_tokens=4000
)
```

### 2. Verification Steps
1. **Static Analysis**: Confirmed no remaining instances of `request_timeout` in active code
2. **Configuration Validation**: Timeout mapping correctly shows CATEGORY_5: 1200 seconds
3. **Library Compatibility**: OpenAI SDK 1.97.1 uses `timeout` parameter properly

### 3. Testing Validation
**Test Commands:**
```bash
# Test o3 model with Category 5 (20-minute timeout)
cd main
python -m pytest tests/test_oq_generator_v2.py::test_o3_timeout -v

# Monitor timeout behavior
python test_oq_minimal.py  # Should now respect 10-minute timeout
```

## Risk Assessment

### Low Risk Changes
- Simple parameter rename from deprecated to current API
- No functional logic changes
- Backward compatible (old parameter was ignored anyway)

### Validation Required
- Confirm 20-minute timeout is now properly applied to o3 models
- Verify other model timeouts still work correctly
- Test under real pharmaceutical workload conditions

### Rollback Plan
If issues arise, can revert individual file changes:
```bash
git checkout HEAD~1 -- main/src/agents/oq_generator/generator_v2.py
```

## Compliance Validation

### GAMP-5 Implications
- **Positive Impact**: Proper timeout handling ensures models can complete complex pharmaceutical validation tasks
- **No Compliance Risk**: Change only affects technical timeout parameter, not validation logic
- **Audit Trail**: All changes documented with clear rationale

### FDA 21 CFR Part 11 Considerations
- **Data Integrity**: No impact on ALCOA+ principles
- **Electronic Records**: Timeout changes don't affect record generation or validation
- **System Validation**: Enhanced reliability for pharmaceutical test generation

## Iteration Log

### Iteration 1: Root Cause Analysis (COMPLETED)
- **Finding**: Identified deprecated `request_timeout` parameter as root cause
- **Evidence**: OpenAI SDK documentation confirmed parameter obsolescence
- **Impact**: 4-minute default timeout instead of configured 20-minute timeout

### Iteration 2: Systematic Fix Implementation (COMPLETED)
- **Action**: Updated all instances of `request_timeout` to `timeout` across codebase
- **Scope**: 4 files modified with consistent parameter updates
- **Validation**: No remaining deprecated parameters in active code paths

### Iteration 3: Testing and Validation (PENDING)
- **Next Steps**: Execute test suite with o3 model to confirm 20-minute timeout
- **Success Criteria**: o3 model runs for full duration without premature timeout
- **Monitoring**: Verify timeout behavior under real pharmaceutical workloads

## Expected Outcomes

### Immediate Results
- o3-2025-04-16 model should now respect 20-minute timeout configuration
- All other model timeouts should continue working as configured
- No impact on existing functionality or compliance requirements

### Long-term Benefits
- Improved reliability for complex pharmaceutical OQ test generation
- Proper timeout handling for future OpenAI model integrations
- Enhanced system stability for GAMP-5 compliant operations

## Completion Criteria

- [ ] All deprecated `request_timeout` parameters replaced with `timeout`
- [ ] o3 model successfully runs for 20 minutes without timeout error
- [ ] Other model timeouts remain functional (Category 1: 2min, Category 3: 3min, Category 4: 5min)
- [ ] No regressions in pharmaceutical test generation workflows
- [ ] Documentation updated to reflect correct timeout parameter usage

**Status**: Fix implemented, pending user validation testing
**Next Action**: User should test o3 model generation to confirm 20-minute timeout works correctly
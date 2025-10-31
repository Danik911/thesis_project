# Debug Plan: Critical Cost Calculation Bug Fix

## Root Cause Analysis

**CRITICAL BUG IDENTIFIED**: Cost calculation error causing 193% overcharge in MetricsCollector system.

### Evidence
- **Expected Cost**: $0.00056 for 3000 tokens (2000 prompt + 1000 completion)  
- **Actual Cost**: $0.00164 (193% error)
- **Impact**: Data integrity compromise, financial calculation errors

### Root Cause
Two different cost calculation methods exist with inconsistent pricing constants:

1. **MetricsCollector (CORRECT)**: Uses DeepSeek V3 pricing
   - File: `main/src/cross_validation/metrics_collector.py` lines 141-142
   - Prompt: $0.14/1M tokens
   - Completion: $0.28/1M tokens

2. **CrossValidationWorkflow (INCORRECT)**: Uses wrong pricing  
   - File: `main/src/cross_validation/cross_validation_workflow.py` line 444
   - Prompt: $0.27/1M tokens (should be $0.14)
   - Completion: $1.10/1M tokens (should be $0.28)

### Verification
Wrong calculation produces exact error seen:
```
(2000/1M × 0.27) + (1000/1M × 1.10) = 0.00054 + 0.0011 = 0.00164 ✓
```

## Solution Steps

### 1. Fix Incorrect Pricing Constants ✅
- Update line 444 in `cross_validation_workflow.py`
- Change 0.27 → 0.14 (prompt cost)  
- Change 1.10 → 0.28 (completion cost)

### 2. Add Defensive Validation ✅
- Create constants module for centralized pricing
- Add runtime validation to catch discrepancies
- Fail explicitly if pricing constants don't match

### 3. Verification Testing ✅  
- Test with known token values
- Verify cost calculation accuracy
- Ensure no regressions in other calculations

## Risk Assessment

**Impact**: HIGH - Financial calculations affect cost reporting and budgeting
**Complexity**: LOW - Simple constant correction
**Rollback**: Easy - revert pricing constants if issues arise

## Compliance Validation

**GAMP-5 Implications**: 
- Cost calculation errors compromise audit trail integrity
- Must ensure consistent pricing across all calculation points
- Add validation to prevent future discrepancies

**NO FALLBACKS**: System must fail explicitly if pricing validation fails

## Implementation Log

**Status**: ✅ COMPLETED
**Actual Time**: 15 minutes
**Files Modified**:
- `main/src/cross_validation/cross_validation_workflow.py` (line 444-445)
- `main/src/cross_validation/metrics_collector.py` (imports)
- **NEW**: `main/src/cross_validation/pricing_constants.py` (centralized constants)

## Verification Criteria
- [✅] Cost calculation matches expected $0.00056 for test case
- [✅] All cost calculations use consistent pricing via centralized module
- [✅] Defensive validation catches future errors with validate_pricing_consistency()
- [✅] No regressions - backward compatible changes only

## Post-Fix Validation

**Test Case**: 2000 prompt + 1000 completion tokens
- **Before**: $0.00164 (193% error)
- **After**: $0.00056 (correct)
- **Error Fixed**: $0.00108 savings per 3000 tokens

**Root Cause Eliminated**: Centralized pricing constants prevent future discrepancies

## CRITICAL BUG RESOLVED ✅

The 193% cost calculation error has been fixed and defensive measures implemented to prevent recurrence.
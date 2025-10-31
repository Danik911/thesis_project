# Debug Plan: Human Consultation Bypass Fix

## Root Cause Analysis
**Issue**: When categorization initially fails with low confidence (20%), SME consultation recovers to high confidence (90%). The `check_consultation_required` step incorrectly uses the NEW 90% confidence instead of ORIGINAL 20% to decide if human consultation is needed.

**Location**: `main/src/core/unified_workflow.py` - Method: `check_consultation_required` (lines 1357-1360)

**Previous Logic Flaw**:
```python
requires_consultation = (
    ev.confidence_score < bypass_threshold or  # Used CURRENT confidence (90% from SME)
    "consultation_required" in ev.risk_assessment.get("flags", [])
)
```

**Root Cause**: The system checked the recovered confidence (90%) instead of the original failure confidence (20%), bypassing required human consultation.

## Solution Implementation

### Fix Applied
Modified `check_consultation_required` method in `unified_workflow.py` (lines 1341-1360):

1. **Extract risk assessment** and check for SME recovery indicators
2. **Preserve original confidence** when SME consultation occurred
3. **Use original confidence** for consultation decision logic
4. **Enhanced audit trail** with transparent logging

### Key Changes
```python
# NEW: Check for SME consultation recovery
risk_assessment = ev.risk_assessment or {}
confidence_for_consultation = ev.confidence_score

if "original_confidence" in risk_assessment:
    confidence_for_consultation = risk_assessment["original_confidence"]
    # Audit log for transparency
    
requires_consultation = (
    confidence_for_consultation < bypass_threshold or  # Uses CORRECT confidence
    "consultation_required" in risk_assessment.get("flags", [])
)
```

### Enhanced Context Information
Updated consultation event creation to include:
- Both original and recovered confidence scores
- Clear indication of SME recovery in reason text
- Full audit trail for regulatory compliance

## Risk Assessment
**Impact**: CRITICAL - Addresses compliance violation where required human consultation was bypassed
**Rollback**: Simple - revert unified_workflow.py changes if issues arise
**Dependencies**: None - isolated fix in single method

## Compliance Validation
- ✅ Preserves full audit trail of original failure and SME recovery
- ✅ Ensures human consultation triggered when required per GAMP-5
- ✅ Maintains transparency for regulatory inspection
- ✅ No fallback logic - explicit failure handling maintained

## Testing Validation Required
1. **Low initial confidence (20%) → SME recovery (90%) → Consultation REQUIRED**
2. **High initial confidence (85%) → No SME involvement → No consultation needed**
3. **SME recovery failure → Explicit failure handling preserved**

## Expected Behavior Post-Fix
When categorization initially fails with 20% confidence:
1. SME consultation recovers to 90% confidence
2. System detects original_confidence in risk_assessment
3. Uses 20% (not 90%) for consultation decision
4. Since 20% < 70% threshold, human consultation is triggered
5. Audit logs show both original and recovered confidence

## Files Modified
- `C:\Users\anteb\Desktop\Courses\Projects\thesis_project\main\src\core\unified_workflow.py` - Lines 1341-1382

## Next Steps for Validation
1. Create test case simulating SME recovery scenario
2. Verify consultation is properly triggered
3. Confirm audit trail includes both confidence scores
4. Test normal high-confidence path still works
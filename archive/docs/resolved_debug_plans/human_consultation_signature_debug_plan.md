# Debug Plan: Human Consultation Data Not Captured in Digital Signature Manifest

## Root Cause Analysis

**CONFIRMED BUG**: Human consultation data is not being properly captured in digital signature manifest, causing 21 CFR Part 11 compliance violation.

### Issue Breakdown:
1. **Human consultation works correctly**: ConsultationEventHandler properly captures all human data (name, ID, role, justification) in HumanResponseEvent
2. **Workflow stores consultation result**: `handle_consultation` method stores comprehensive consultation data in context at `consultation_result`
3. **Signature creation ignores human data**: `handle_categorization` method uses config defaults instead of checking for human consultation data

### Technical Details:
- **Location**: `main/src/core/unified_workflow.py` lines 883-884
- **Current Code**: Always uses `getattr(config, "user_name", "System")` for signatures
- **Missing Logic**: No check for stored `consultation_result` context data
- **Impact**: Signature manifest shows "System" instead of actual human operator

## Solution Steps

### Step 1: Modify Signature Creation Logic
**File**: `main/src/core/unified_workflow.py` (lines 874-890)
**Action**: Add consultation data check before signature creation

1. Retrieve `consultation_result` from context if available
2. If consultation occurred, extract human operator data
3. Use human data for signature instead of config defaults
4. Enhance `additional_context` with consultation details

### Step 2: Context Data Retrieval
**Implementation**:
```python
# Check for human consultation data in context
consultation_result = await safe_context_get(ctx, "consultation_result", None)

if consultation_result:
    # Use human operator data
    signer_name = f"{consultation_result['operator_name']} ({consultation_result['operator_role']})"
    signer_id = consultation_result['operator_name']
    additional_context = {
        "workflow_session": self._workflow_session_id,
        "risk_assessment": categorization_event.risk_assessment,
        "consultation_required": True,
        "employee_id": consultation_result.get('digital_signature', '').split('_')[1] if '_' in consultation_result.get('digital_signature', '') else 'unknown',
        "operator_role": consultation_result['operator_role'],
        "decision_justification": consultation_result['decision_rationale'],
        "original_ai_confidence": consultation_result['original_confidence'],
        "human_selected_category": consultation_result['approved_category']
    }
else:
    # Use system defaults for automated decisions
    signer_name = getattr(config, "user_name", "System")
    signer_id = getattr(config, "user_id", "system")
    additional_context = {
        "workflow_session": self._workflow_session_id,
        "risk_assessment": categorization_event.risk_assessment,
        "consultation_required": False
    }
```

### Step 3: Employee ID Extraction
**Challenge**: Extract employee ID from digital signature format `"Name_ID_Timestamp"`
**Solution**: Parse digital signature string to extract individual components

### Step 4: Testing Validation
1. Test automated categorization (no consultation) - should use System defaults
2. Test human consultation - should use human operator data
3. Verify signature manifest contains correct human information
4. Check additional_context includes consultation details

## Risk Assessment

### Low Risk Changes:
- Adding context retrieval logic
- Conditional signature data selection
- Enhanced additional_context

### Medium Risk:
- Digital signature parsing (needs error handling)
- Backward compatibility with existing signatures

### Mitigation:
- Comprehensive error handling for context retrieval
- Fallback to existing logic if consultation data malformed
- Preserve existing behavior for automated decisions

## Compliance Validation

### 21 CFR Part 11 Requirements:
- ✅ Authentic: Real human operator name and ID captured
- ✅ Attributable: Clear operator identification with role
- ✅ Legible: Human-readable justification included
- ✅ Contemporaneous: Timestamp preserved from consultation
- ✅ Original: Full consultation context preserved
- ✅ Accurate: No fallback values masking real decisions

### GAMP-5 Implications:
- Maintains complete audit trail of human decisions
- Preserves original AI confidence that triggered consultation
- Documents human override with full justification
- Supports regulatory inspection requirements

## Implementation Priority
**CRITICAL**: This is a regulatory compliance bug that must be fixed immediately
**Impact**: All human consultations since deployment have incorrect audit trail
**Timeline**: Fix within current session to prevent further compliance violations

## Expected Outcome

### Before Fix:
```json
{
  "signer_id": "system",
  "signer_name": "System",
  "additional_context": {
    "workflow_session": "session_id",
    "risk_assessment": {...}
  }
}
```

### After Fix:
```json
{
  "signer_id": "Daniil Vladimirov", 
  "signer_name": "Daniil Vladimirov (Quality Assurance)",
  "signature_meaning": "reviewed",
  "additional_context": {
    "workflow_session": "session_id",
    "risk_assessment": {...},
    "consultation_required": true,
    "employee_id": "459933", 
    "operator_role": "quality_assurance",
    "decision_justification": "I know because I'm smart",
    "original_ai_confidence": 0.20,
    "human_selected_category": 4
  }
}
```

## Iteration Log
- **Analysis Complete**: Root cause identified in signature creation logic
- **Ready for Implementation**: All necessary changes mapped out
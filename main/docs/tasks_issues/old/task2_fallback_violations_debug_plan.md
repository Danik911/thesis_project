# Debug Plan: Task 2 Production-Blocking Issues

## Root Cause Analysis Summary

### Issue #1: FALLBACK VIOLATIONS (Priority 1) ✅ IDENTIFIED
**Root Cause**: `error_handler.py` contains fallback logic that creates artificial Category 5 classifications instead of failing explicitly with diagnostic information.

**Specific Violations**:
- Line 619: `return 5` in `_extract_sme_category_recommendation()` method
- Method `_request_sme_consultation()` (lines 443-577) has fallback behavior to Category 5
- Violates NO FALLBACKS policy required for pharmaceutical compliance
- Creates misleading `recovery_strategy: "fallback_to_category_5"` audit log entries

**Evidence**: End-to-end testing found audit logs showing artificial Category 5 fallbacks instead of explicit failures.

### Issue #2: PHOENIX OBSERVABILITY FAILURE (Priority 2) 🔍 UNDER INVESTIGATION  
**Root Cause**: Phoenix GraphQL backend completely broken - "Something went wrong" errors prevent trace access.

**Specific Symptoms**:
- Phoenix server responds but cannot load traces or projects
- GraphQL backend returns generic error messages
- Zero audit trail visibility for GAMP-5 compliance
- Instrumentation present but traces not accessible

**Evidence**: Monitor-agent found complete Phoenix observability failure preventing regulatory compliance monitoring.

## Solution Steps

### Phase 1: Eliminate Fallback Violations (Priority 1)

#### Step 1.1: Identify All Fallback Logic ✅ COMPLETED
- **File**: `main/src/agents/categorization/error_handler.py`
- **Lines**: 619, 571-576, throughout `_request_sme_consultation()` method
- **Action**: Located specific fallback implementations

#### Step 1.2: Replace with Explicit Failures ✅ COMPLETED
- **Target**: `_extract_sme_category_recommendation()` method (line 619)
- **Change**: ✅ Replaced `return 5` with explicit RuntimeError containing full diagnostic information
- **Target**: `_request_sme_consultation()` method (lines 571-576)  
- **Change**: ✅ Updated all log messages and comments to eliminate fallback references
- **Additional**: ✅ Updated module docstring, method docstrings, and dataclass defaults
- **Files Modified**: `main/src/agents/categorization/error_handler.py`

#### Step 1.3: Validate Compliance ⏳ PENDING
- **Action**: Test that all errors now fail explicitly with full diagnostic information
- **Requirement**: No artificial categorizations created under any failure condition
- **Verification**: End-to-end testing confirms no fallback audit log entries

### Phase 2: Fix Phoenix Observability (Priority 2)

#### Step 2.1: Infrastructure Diagnosis ✅ COMPLETED
- **Action**: ✅ Created comprehensive Phoenix diagnostic tool
- **File**: `main/debug_phoenix_observability.py`
- **Capability**: Tests HTTP connectivity, GraphQL endpoint, trace access, and OTLP ingestion
- **Output**: Provides specific recommendations based on failure patterns

#### Step 2.2: GraphQL Backend Investigation ⏳ READY FOR EXECUTION
- **Action**: Run diagnostic tool to identify root cause  
- **Command**: `python main/debug_phoenix_observability.py`
- **Expected**: Tool will identify specific GraphQL backend failure pattern
- **Method**: Systematic testing of Phoenix infrastructure components

#### Step 2.3: Apply Diagnostic Recommendations ⏳ PENDING
- **Action**: Execute recommendations from diagnostic tool
- **Requirement**: Restore full Phoenix observability functionality
- **Validation**: Confirm trace access and GraphQL backend operational

## Risk Assessment  

### Priority 1 - Fallback Violations
- **Regulatory Impact**: HIGH - Violates pharmaceutical compliance requirements
- **Audit Risk**: CRITICAL - Creates misleading audit trails
- **System Risk**: MEDIUM - Does not prevent system operation but violates policy

### Priority 2 - Phoenix Observability
- **Regulatory Impact**: HIGH - Prevents audit trail visibility required for GAMP-5
- **Operational Risk**: MEDIUM - System functions but lacks monitoring
- **Compliance Risk**: HIGH - Cannot validate system behavior for regulatory audit

## Compliance Validation

### GAMP-5 Requirements
- [❌] **Explicit Error Handling**: All failures must be documented with complete diagnostic information
- [❌] **Audit Trail Completeness**: All system decisions must be traceable and verifiable
- [❌] **No Misleading Information**: System must not create artificial data that masks real behavior

### ALCOA+ Principles  
- [❌] **Accuracy**: Fallbacks create inaccurate categorization data
- [❌] **Completeness**: Missing error information in current fallback approach
- [❌] **Consistency**: Inconsistent error handling between success and failure paths

## Implementation Log

### Iteration 1: Fallback Logic Removal ⏳ IN PROGRESS
- **Status**: Analyzing specific code changes required
- **Target**: Complete removal of all fallback categorization logic
- **Expected Outcome**: All categorization failures result in explicit exceptions with full diagnostics

### Iteration 2: Phoenix Diagnostics ⏳ PENDING
- **Status**: Preparing infrastructure investigation
- **Target**: Restore Phoenix trace access functionality
- **Expected Outcome**: Full observability restored for regulatory compliance

### Iteration 3: End-to-End Validation ⏳ PENDING
- **Status**: Awaiting completion of fixes
- **Target**: Comprehensive system validation
- **Expected Outcome**: Both issues resolved with full compliance validation

## Escalation Criteria

- **After 3 iterations**: If fallback violations persist, recommend architectural changes
- **After 5 iterations**: If Phoenix issues unresolved, recommend alternative observability solution
- **Immediate escalation**: If regulatory compliance cannot be achieved with current approach

## Next Actions

1. **Immediate**: Fix fallback violations in error_handler.py
2. **Next**: Diagnose Phoenix server infrastructure
3. **Then**: Validate complete solution with end-to-end testing
4. **Finally**: Document fixes for future reference and compliance audit
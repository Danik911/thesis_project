# Debug Plan: Cross-Validation Timeout Issues

## Root Cause Analysis

**Sequential Thinking Analysis Results:**
The cross-validation system was failing due to insufficient timeout settings and parallel processing conflicts:

1. **Primary Issue**: Timeout values set too low (60-180 seconds vs required 600 seconds)
2. **Secondary Issue**: Batch processing with batch_size > 1 causing resource conflicts
3. **Evidence**: Single document succeeds in 4.36 minutes, requiring ~300-600 second timeout per document
4. **Impact**: 0% success rate on 17-document cross-validation vs 100% on single document

## Solution Steps

### 1. Fixed Main Cross-Validation Script ✅
**File**: `main/run_cv_task42.py`
- **Change**: `batch_size: int = 3` → `batch_size: int = 1`
- **Reason**: Sequential processing prevents resource conflicts and timeouts
- **Status**: COMPLETED

### 2. Fixed Test Script ✅  
**File**: `main/test_cv_single.py`
- **Change**: `timeout_per_doc=60` → `timeout_per_doc=600`
- **Reason**: Match successful end-to-end test timeout (4.36 min per doc)
- **Status**: COMPLETED

### 3. Fixed Alternative Batched Script ✅
**File**: `run_task42_batched.py`
- **Changes**: 
  - `batch_size = 2` → `batch_size = 1`
  - `timeout_per_doc = 180` → `timeout_per_doc = 600`
  - Function signature: `batch_size: int = 2, timeout_per_doc: int = 300` → `batch_size: int = 1, timeout_per_doc: int = 600`
- **Reason**: Align with proven successful configuration
- **Status**: COMPLETED

### 4. Final Verification ✅
**Confirmed Settings Across All Scripts**:
- ✅ `main/run_cv_task42.py`: batch_size=1, timeout_per_doc=600
- ✅ `main/test_cv_single.py`: batch_size=1, timeout_per_doc=600  
- ✅ `run_task42_batched.py`: batch_size=1, timeout_per_doc=600
- ✅ `main/src/cross_validation/batch_executor.py`: Default timeout_per_doc=600 (correct)

## Risk Assessment

**LOW RISK CHANGES**:
- All timeout increases reduce failure probability
- Sequential processing (batch_size=1) eliminates race conditions
- Changes align with proven successful configuration
- No functional logic changes, only timeout/concurrency parameters

**Rollback Plan**: 
- If issues arise, revert batch_size and timeout_per_doc to original values
- Original values preserved in git history

## Compliance Validation

**GAMP-5 Implications**:
- ✅ No functional changes to test generation logic
- ✅ Improved reliability supports consistent validation
- ✅ Sequential processing provides deterministic execution order
- ✅ Extended timeouts prevent premature failures in regulatory validation

**Audit Requirements**:
- All changes documented in this debug plan
- Configuration changes clearly logged
- No fallback logic introduced (maintains explicit error handling)

## Expected Results

**Performance Expectations**:
- 17 documents × 4.36 minutes = ~74 minutes total execution time
- With 600-second timeout per document: maximum possible time = 17 × 10 minutes = 170 minutes
- Sequential processing ensures stable resource utilization
- Phoenix monitoring should capture ~2,200 spans (130 × 17 documents)

**Success Criteria**:
- All 17 documents process successfully without timeout
- Cross-validation generates complete test suites for each document
- Phoenix traces captured for full thesis evidence
- No timeout errors in execution logs

## Next Steps

1. **Test Single Document**: Run `main/test_cv_single.py` to verify fix
2. **Run Full Cross-Validation**: Execute `main/run_cv_task42.py` for all 17 documents  
3. **Monitor Progress**: Check Phoenix traces and execution logs
4. **Collect Evidence**: Verify complete thesis evidence package generation

## Implementation Notes

**Critical Configuration Values**:
- `timeout_per_doc = 600` (10 minutes per document)
- `batch_size = 1` (sequential processing)
- `enable_monitoring = True` (Phoenix tracing enabled)

**No Fallbacks Implemented**:
- System will fail explicitly if timeout exceeded
- All errors logged with full diagnostic information
- No artificial confidence scores or masked failures
- Complete transparency for regulatory compliance
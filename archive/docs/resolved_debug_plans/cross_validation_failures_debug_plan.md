# Debug Plan: Cross-Validation Failures in Pharmaceutical Test Generation System

## Root Cause Analysis

### Issue 1: LlamaIndex Callback Error
**Error**: `AttributeError: 'function' object has no attribute 'event_starts_to_ignore'`
**Location**: context_provider.py, line 542 (embed_model.get_text_embedding() call)
**Root Cause**: Callback manager conflict in cross-validation mode where multiple instances try to modify the same embedding model's callback manager

### Issue 2: GAMP Categorization Misclassification
**Document**: URS-001 (Environmental Monitoring System)
**Expected**: Category 3 (Standard Software)
**Actual**: Category 1 (Infrastructure) with 58% confidence
**Root Cause**: Pattern matching fails to detect obvious Category 3 indicators like "vendor-supplied software without modification"

### Issue 3: Phoenix UI Not Accessible
**Expected**: http://localhost:6006 accessible
**Actual**: Connection refused
**Root Cause**: Phoenix server not running in Docker

## Solution Steps

### 1. Fix LlamaIndex Callback Manager Conflict
- Remove conflicting callback manager logic in lines 614-617
- Ensure consistent callback manager handling across all embedding operations
- Add thread-safety for cross-validation parallel execution

### 2. Improve GAMP Categorization Pattern Matching
- Debug why Category 3 indicators are not being detected
- Review scoring logic for Category 3 vs Category 1 classification
- Add logging to trace categorization decision process

### 3. Launch Phoenix Server
- Start Phoenix Docker container with correct port mapping
- Verify accessibility and provide troubleshooting commands

## Risk Assessment
- **Impact**: Complete cross-validation failure affecting pharmaceutical compliance testing
- **Severity**: High - blocks regulatory validation workflows
- **Rollback Plan**: Revert to single document mode if fixes cause regressions

## Compliance Validation
- **GAMP-5 Implications**: Categorization accuracy critical for validation rigor
- **Audit Requirements**: All fixes must maintain full audit trail integrity
- **Regulatory Standards**: Must preserve 21 CFR Part 11 compliance

## Iteration Log
- **Iteration 1**: Systematic root cause analysis and targeted fixes
- **Expected Outcome**: Successful cross-validation with correct categorization
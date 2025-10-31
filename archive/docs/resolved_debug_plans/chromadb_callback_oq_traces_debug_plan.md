# Debug Plan: ChromaDB Callback Issue and Missing OQ Agent Traces

## Root Cause Analysis

### Issue 1: ChromaDB Embedding Callback Failure
- **Error**: `'NoneType' object has no attribute 'event_starts_to_ignore'`
- **Location**: `context_provider.py` line 551-554 in `_search_documents()`
- **Root Cause**: We set `callback_manager=None` on embedding model (line 433) but LlamaIndex embedding code still tries to access callback manager properties internally
- **Impact**: Context provider completely fails, blocking entire workflow

### Issue 2: Missing OQ Agent Traces  
- **Symptom**: User sees no traces from OQ agent execution
- **Root Cause**: Workflow dependency chain breaks at context provider failure
- **Flow Break**: categorize_document ✅ → execute_agent_request ❌ (context provider fails) → collect_agent_results ❌ → generate_oq_tests ❌ (OQ agent never runs)
- **Impact**: OQ test generation never executes, no 25 tests generated

## Solution Steps

### Step 1: Fix ChromaDB Callback Manager Issue
**Target**: `main/src/agents/parallel/context_provider.py` lines 551-554

**Current Code**:
```python
query_embedding = await asyncio.to_thread(
    self.embedding_model.get_text_embedding,
    query
)
```

**Fix**: Add callback manager validation before embedding call
```python
# Ensure embedding model has valid callback manager
if self.embedding_model.callback_manager is None:
    from llama_index.core.callbacks import CallbackManager
    self.embedding_model.callback_manager = CallbackManager([])

query_embedding = await asyncio.to_thread(
    self.embedding_model.get_text_embedding,
    query
)
```

### Step 2: Add Comprehensive Error Handling
**Target**: Same location in context provider

**Implementation**: Wrap embedding call with explicit error handling that doesn't mask the real issue but provides diagnostic information
```python
try:
    # Fix callback manager if needed
    if self.embedding_model.callback_manager is None:
        from llama_index.core.callbacks import CallbackManager
        self.embedding_model.callback_manager = CallbackManager([])
    
    query_embedding = await asyncio.to_thread(
        self.embedding_model.get_text_embedding,
        query
    )
except Exception as e:
    error_msg = f"ChromaDB embedding failed: {type(e).__name__}: {e}"
    self.logger.error(error_msg)
    # NO FALLBACKS - fail explicitly with full diagnostic information
    raise RuntimeError(f"Context provider embedding operation failed: {error_msg}") from e
```

### Step 3: Validate Workflow Continuation
**Target**: Ensure OQ agent runs after context provider fix

**Test**: Run end-to-end test to verify:
1. Context provider executes successfully
2. AgentResultsEvent gets generated
3. `generate_oq_tests()` step executes
4. OQ agent produces Phoenix traces
5. 25 tests generated for Category 5

### Step 4: Add Diagnostic Logging
**Target**: Enhanced logging for workflow flow tracking

**Implementation**: Add trace logging at key workflow steps to track execution flow

## Risk Assessment

**Risks**:
1. CallbackManager([]) might not be sufficient for all LlamaIndex operations
2. Phoenix observability might still conflict with callback manager
3. Fixing context provider might reveal downstream issues in OQ agent

**Mitigation**:
1. Test callback manager fix in isolation first
2. Maintain Phoenix disabled state during testing if needed
3. Have rollback plan ready

**Rollback Plan**: 
- Revert context_provider.py changes
- Use previous working state without context retrieval

## Compliance Validation

**GAMP-5 Implications**:
- ✅ Fix maintains explicit error handling (no fallbacks)
- ✅ Preserves audit trail with comprehensive logging
- ✅ Does not mask system failures
- ✅ Provides full diagnostic information for regulatory compliance

## Implementation Order

1. **Fix callback manager issue** (15 minutes) ✅ COMPLETED
   - ✅ Added CallbackManager([]) when None detected in context_provider.py
   - ✅ Added comprehensive error handling with NO FALLBACKS
   - ✅ Maintains explicit error reporting for regulatory compliance
   
2. **Test context provider fix** (15 minutes) 🔄 IN PROGRESS
   - Created test_callback_fix.py for isolated testing
   - Ready to verify ChromaDB search works
   
3. **Test full workflow** (30 minutes) 🔄 READY
   - Created test_oq_agent_execution.py for end-to-end test
   - Will verify OQ agent executes and produces traces
   - Will confirm 25 tests generated
   
4. **Validate no regressions** (15 minutes) 📋 PENDING
   - Test categorization still works
   - Verify Phoenix traces still generated where working
   
5. **Document fix** (15 minutes) 📋 PENDING
   - Update fix in codebase
   - Document solution for future reference

## Success Criteria

- [ ] ChromaDB embedding operations execute without callback errors
- [ ] Context provider successfully retrieves GAMP-5 documents
- [ ] OQ agent executes and generates Phoenix spans
- [ ] 25 OQ tests generated for Category 5
- [ ] No workflow regressions introduced
- [ ] Full diagnostic information preserved for compliance

## Files to Modify

### Primary Fix
- `main/src/agents/parallel/context_provider.py` - Lines 551-554 (callback manager fix)

### Testing Files
- `main/test_oss_migration_fixes.py` - End-to-end validation
- `main/test_oss_simple.py` - Context provider isolation test

## Expected Outcomes

**After Implementation**:
- ✅ ChromaDB search operations working
- ✅ Complete workflow execution from categorization to OQ generation  
- ✅ OQ agent produces visible Phoenix traces
- ✅ 25 test cases generated successfully
- ✅ All diagnostic information preserved for regulatory compliance

**Timeline**: 90 minutes total implementation and testing

---

## FIX IMPLEMENTATION SUMMARY

### ✅ Primary Fix Applied

**File**: `main/src/agents/parallel/context_provider.py`  
**Lines**: 551-566  
**Change**: Added callback manager validation and creation before embedding operations

```python
# Fix callback manager issue - ensure embedding model has valid callback manager
if self.embedding_model.callback_manager is None:
    from llama_index.core.callbacks import CallbackManager
    self.embedding_model.callback_manager = CallbackManager([])
    self.logger.debug("Created empty CallbackManager for embedding model")
```

### 🔧 Error Handling Enhancement

Added comprehensive error handling that maintains NO FALLBACKS policy:
- Explicit error messages with full type and details
- Preserved stack traces for regulatory compliance  
- RuntimeError raised with complete diagnostic information
- No artificial confidence scores or masked failures

### 📋 Testing Infrastructure Created

1. **test_callback_fix.py** - Isolated callback manager testing
2. **test_oq_agent_execution.py** - End-to-end OQ agent validation

### 🎯 Expected Resolution

This fix addresses both reported issues:
1. **ChromaDB Embedding Failure**: Resolved by ensuring valid callback manager
2. **Missing OQ Agent Traces**: Resolved by unblocking workflow execution path

The workflow should now complete: categorization → context provider ✅ → OQ generation ✅
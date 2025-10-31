# Debug Plan: Research Agent Resource Leak

## Root Cause Analysis
Through systematic analysis using sequential thinking methodology, the root cause has been identified:

**Primary Issue**: Research Agent creates unclosed requests.Session objects that accumulate across workflow runs
- Location: `src/agents/parallel/regulatory_data_sources.py:133`  
- Pattern: New FDAAPIClient created each workflow run (unified_workflow.py:984)
- Impact: Subsequent runs hang due to resource exhaustion/connection limits
- Evidence: "Starting research agent with 300.0s timeout" followed by hang

**Resource Leak Chain**:
1. `unified_workflow.py:984` - Creates new research agent every call (no caching)
2. `research_agent.py:119` - Creates new FDAAPIClient via create_fda_client()
3. `regulatory_data_sources.py:133` - Creates new requests.Session()
4. No cleanup mechanism - sessions accumulate

**Why First Run Works, Subsequent Fail**:
- First run: Clean system, single session works fine
- Subsequent runs: Multiple unclosed sessions compete for resources

## Solution Steps

### 1. Add Session Cleanup to FDAAPIClient
**File**: `src/agents/parallel/regulatory_data_sources.py`
- Add `close()` method to properly close session
- Add `__enter__/__exit__` for context manager support
- Add `__del__` method for cleanup safety

### 2. Implement Agent Caching in Unified Workflow  
**File**: `src/core/unified_workflow.py`
- Cache research agent instance instead of creating new ones
- Add proper cleanup on workflow destruction
- Ensure agent reuse between workflow runs

### 3. Add Resource Tracking and Diagnostics
**Files**: Both research agent and regulatory data sources
- Add session tracking counters
- Log resource creation/cleanup
- Add heartbeat during long operations
- Track memory usage during agent execution

### 4. Improve Error Propagation
**File**: `src/agents/parallel/research_agent.py`
- Add explicit timeouts for individual FDA API calls
- Improve async exception handling
- Add resource cleanup in exception handlers

## Risk Assessment  
**Low Risk**: Changes focus on resource management without altering core functionality
- Resource cleanup is defensive programming
- Agent caching improves performance
- No changes to API contracts or GAMP-5 compliance logic

**Rollback Plan**: Revert to creating new agents (current broken behavior) if caching introduces issues

## Compliance Validation
**GAMP-5 Implications**: 
- Resource management improves system reliability
- Better error visibility supports audit requirements
- No impact on validation data integrity
- Maintains explicit error handling (no fallbacks)

## Iteration Log

### Iteration 1: Add Session Cleanup
- Target: Fix immediate resource leak
- Change: Add close() method to FDAAPIClient
- Validation: Test multiple workflow runs

### Iteration 2: Implement Agent Caching
- Target: Prevent creating multiple agent instances
- Change: Cache research agent in unified workflow
- Validation: Confirm single agent reuse

### Iteration 3: Add Resource Diagnostics
- Target: Enable future debugging
- Change: Add resource tracking and heartbeat logging
- Validation: Monitor resource usage patterns

### Iteration 4: Timeout Improvements
- Target: Better async error handling
- Change: Add granular timeouts for FDA API calls
- Validation: Test timeout scenarios

### Iteration 5: Final Validation
- Target: Confirm reliable operation
- Change: End-to-end workflow testing
- Validation: Multiple consecutive successful runs

## Success Criteria
- [ ] `python test_direct_oq.py` runs successfully multiple times in a row
- [ ] `python main.py` workflow completes reliably on repeated execution
- [ ] Resource usage remains stable across multiple runs
- [ ] No hanging at "Starting research agent with 300.0s timeout"
- [ ] Error messages are clear when failures occur
- [ ] Phoenix monitoring shows consistent span patterns
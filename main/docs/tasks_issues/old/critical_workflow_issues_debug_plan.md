# Critical Workflow Issues Debug Plan

**Date**: 2025-07-29
**Debugger**: Advanced Debugging Agent
**Status**: In Progress

## Executive Summary

The pharmaceutical test generation workflow has 4 critical issues preventing production deployment:
1. Confidence scoring returns 0.0% despite successful categorization
2. Event logging captures 0 events despite workflow activity
3. Phoenix observability fails to capture traces
4. FunctionAgent.chat() attribute error in planning workflow

## Root Cause Analysis

### Issue 1: Confidence Scoring Broken (0.0%)

**Root Cause**: Exception handling in `confidence_tool_with_error_handling` returns 0.0 on ANY error
- File: `/home/anteb/thesis_project/main/src/agents/categorization/agent.py`
- Line 371: `return 0.0  # Return zero confidence on error`
- The LLM agent might be passing incorrect data structure to the confidence tool
- Any exception (parsing, validation, calculation) results in 0.0 confidence

**Evidence**:
- Test report shows "Confidence: 0.0%" despite successful Category 5 categorization
- Categorization works but confidence calculation fails silently
- Error is swallowed and returns 0.0 instead of proper error handling

### Issue 2: Event Logging Failure (0 events)

**Root Cause**: Task 15 solution implemented but not properly integrated
- Solution exists in `run_workflow_with_event_logging()` 
- Main workflow uses it (line 186 in main.py)
- But event filtering might be too restrictive or events not properly emitted

**Evidence**:
- Task 15 solution shows fix working in isolation
- End-to-end test shows 0 events captured
- Event handler statistics show 0 events processed

### Issue 3: Phoenix Observability Failure

**Root Cause**: Phoenix API endpoint misconfiguration
- Phoenix UI serves static content at port 6006
- OTLP trace endpoint expects `/v1/traces` but returns HTML
- Phoenix might not be properly initialized or instrumented

**Evidence**:
- Test report: "Traces Captured: 0"
- API endpoint returns HTML instead of accepting trace data
- Phoenix UI accessible but no trace data collection

### Issue 4: FunctionAgent.chat Attribute Error

**Root Cause**: Incorrect method call on FunctionAgent
- File: `/home/anteb/thesis_project/main/src/agents/planner/agent.py`
- Line 365: `response = self.function_agent.chat(prompt)`
- FunctionAgent uses `run()` method, not `chat()`

**Evidence**:
- Error message: "'FunctionAgent' object has no attribute 'chat'"
- LLM enhancement fails and falls back to original strategy

## Solution Implementation Plan

### Fix 1: Confidence Scoring

1. **Add detailed logging** to identify what data the confidence tool receives
2. **Fix data flow** between LLM agent and confidence tool
3. **Improve error handling** to log errors instead of returning 0.0
4. **Add validation** for tool input/output

### Fix 2: Event Logging

1. **Verify event emission** in workflows using `ctx.write_event_to_stream()`
2. **Check event filtering** configuration in EventStreamConfig
3. **Add debug logging** to trace event flow
4. **Ensure proper integration** with run_workflow_with_event_logging

### Fix 3: Phoenix Observability

1. **Verify Phoenix container** is running with proper ports
2. **Check OTLP endpoint** configuration
3. **Add instrumentation** to workflows if missing
4. **Test trace export** with minimal example

### Fix 4: FunctionAgent Method

1. **Replace** `self.function_agent.chat(prompt)` 
2. **With** `await self.function_agent.run(user_msg=prompt)`
3. **Update** error handling for async operation

## Implementation Order

1. **Fix FunctionAgent.chat** - Quick fix, immediate impact
2. **Fix Confidence Scoring** - Critical for GAMP-5 compliance
3. **Fix Event Logging** - Required for audit trail
4. **Fix Phoenix Observability** - Important for monitoring

## Risk Assessment

- **High Risk**: Confidence scoring affects GAMP-5 categorization decisions
- **Medium Risk**: Event logging affects compliance audit trails
- **Low Risk**: Phoenix observability is monitoring, not core functionality
- **Low Risk**: FunctionAgent fix is isolated to planning enhancement

## Validation Plan

After each fix:
1. Run unit tests for the specific component
2. Run integration test for the workflow
3. Verify fix in end-to-end test
4. Document results

## Rollback Strategy

If fixes cause new issues:
1. Revert individual changes using git
2. Re-run tests to confirm system stability
3. Document failed approach for future reference
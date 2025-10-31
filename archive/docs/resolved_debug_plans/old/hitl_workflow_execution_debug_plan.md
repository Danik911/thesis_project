# Debug Plan: HITL Workflow Execution Issue

## Root Cause Analysis

**Issue:** HITL consultation system reaches handle_consultation_required step but immediately terminates instead of waiting for human input.

**Root Cause Identified:** The workflow execution system lacks a mechanism to capture user input during workflow execution and convert it to HumanResponseEvent objects that the consultation system expects.

**Technical Details:**
1. The consultation system is designed to work with `ctx.wait_for_event(HumanResponseEvent)`
2. The main execution flow in `run_workflow_with_event_logging` only passively listens to workflow events
3. When user types "this is category 3" in CLI, there's no code to capture this input and convert it to a HumanResponseEvent
4. The workflow times out waiting for an event that never gets sent

## Solution Steps

### Step 1: Create HITL Input Handler
Create a function to handle human consultation input during workflow execution:
- Detect ConsultationRequiredEvent in event stream
- Prompt user for appropriate input based on consultation type  
- Convert user input to HumanResponseEvent
- Send event to workflow context

### Step 2: Modify Event Stream Processing
Update `run_workflow_with_event_logging` to:
- Monitor for ConsultationRequiredEvent in the event stream
- Call HITL input handler when consultation is required
- Inject HumanResponseEvent back into workflow

### Step 3: Test Integration
Validate that:
- User can provide input when consultation is required
- Input is properly converted to HumanResponseEvent
- Workflow continues with human decision
- All existing tests continue to pass

## Risk Assessment

**Low Risk:** Changes are isolated to workflow execution layer and don't modify core consultation logic.

**Rollback Plan:** If issues arise, revert changes to `event_logging_integration.py` and test with existing HITL test files.

## Compliance Validation

**GAMP-5 Implications:** 
- Human consultation functionality is critical for regulatory compliance
- Must maintain full audit trail of human decisions
- Conservative defaults must still apply on timeout

**Audit Requirements:**
- All human inputs must be logged with timestamps
- Decision rationale must be captured
- Timeout behavior must remain unchanged

## Implementation Details

Files to modify:
1. `/home/anteb/thesis_project/main/src/shared/event_logging_integration.py` - Add HITL handler
2. Test with existing workflow execution

## Iteration Log

**Iteration 1 (Planned):** Implement basic HITL input handler and test with categorization consultation
# Task 15 Event Logging System Debug Plan

**Date**: 2025-07-28  
**Issue**: Event logging system captures 0 real LlamaIndex workflow events  
**Status**: 🔧 DEBUGGING IN PROGRESS  

## 🎯 Problem Summary

The Task 15 event logging system shows "0 events processed" during real workflow execution because:
1. The `EventStreamHandler._simulate_event_stream()` generates fake events instead of reading real ones
2. The integration pattern is architecturally incorrect - trying to read events from inside the workflow
3. The test script uses `workflow.run()` instead of `workflow.run_stream()` to capture events

## 🔍 Root Cause Analysis

### Current (Incorrect) Architecture
```
Workflow → ctx.write_event_to_stream() → ??? (events lost)
         ↓
EventStreamHandler (inside workflow) → Simulates fake events
         ↓
Test Script uses workflow.run() → Gets result only, no events
```

### Correct Architecture (LlamaIndex Pattern)
```
Workflow → ctx.write_event_to_stream() → Event Stream
                                              ↓
Test Script uses workflow.run_stream() → async for event in stream
                                              ↓
                                    EventStreamHandler processes events
```

## 🛠️ Solution Plan

### Step 1: Fix the Test Script Integration
**File**: `/home/anteb/thesis_project/test_real_workflow_with_logging.py`

Change from:
```python
result = await workflow.run(
    document_content=document_content,
    document_name=test_document.name
)
```

To:
```python
# Collect events and result
events = []
result = None

async for event in workflow.run_stream(
    document_content=document_content,
    document_name=test_document.name
):
    # Process each event through the event handler
    if event_handler:
        await event_handler.process_workflow_event(event)
    events.append(event)
    
    # Check if this is the final result
    if isinstance(event, StopEvent):
        result = event.result
```

### Step 2: Create Real Event Processing Method
**File**: `/home/anteb/thesis_project/main/src/shared/event_logging.py`

Add new method to EventStreamHandler:
```python
async def process_workflow_event(self, event: Any) -> dict[str, Any] | None:
    """
    Process a real LlamaIndex workflow event.
    
    Args:
        event: LlamaIndex workflow event
        
    Returns:
        Processed event data or None if filtered
    """
    # Convert LlamaIndex event to our event format
    event_data = {
        "event_type": event.__class__.__name__,
        "event_id": str(uuid4()),
        "timestamp": datetime.now(UTC).isoformat(),
        "workflow_context": {
            "step": getattr(event, "step", "unknown"),
            "agent_id": getattr(event, "agent_id", "unknown"),
            "correlation_id": getattr(event, "correlation_id", str(uuid4()))
        },
        "payload": {}
    }
    
    # Extract event-specific data
    if hasattr(event, "__dict__"):
        for key, value in event.__dict__.items():
            if not key.startswith("_"):
                event_data["payload"][key] = str(value) if not isinstance(value, (str, int, float, bool, dict, list)) else value
    
    # Process through existing pipeline
    return await self._process_event(event_data)
```

### Step 3: Remove Simulated Event Stream
**File**: `/home/anteb/thesis_project/main/src/shared/event_logging.py`

Remove or deprecate the `_simulate_event_stream` method and update `stream_events` to handle real events properly.

### Step 4: Update EventLoggingMixin Integration
**File**: `/home/anteb/thesis_project/main/src/shared/event_logging_integration.py`

The EventLoggingMixin should focus on writing events, not reading them:
- Keep `ctx.write_event_to_stream()` for writing events
- Remove any attempts to read events from inside the workflow
- Events should be consumed externally via `run_stream()`

### Step 5: Create Proper Integration Helper
**File**: `/home/anteb/thesis_project/main/src/shared/event_logging_integration.py`

Add helper function:
```python
async def run_workflow_with_event_logging(
    workflow: Workflow,
    event_handler: EventStreamHandler,
    **kwargs
) -> tuple[Any, list[dict[str, Any]]]:
    """
    Run a workflow and capture all events through the event logging system.
    
    Returns:
        Tuple of (result, processed_events)
    """
    processed_events = []
    result = None
    
    async for event in workflow.run_stream(**kwargs):
        # Process event through handler
        processed_event = await event_handler.process_workflow_event(event)
        if processed_event:
            processed_events.append(processed_event)
        
        # Extract result from StopEvent
        if hasattr(event, "result"):
            result = event.result
    
    return result, processed_events
```

## 📊 Expected Outcomes

After implementing these fixes:
1. Real workflow events (URSIngestionEvent, GAMPCategorizationEvent, etc.) will be captured
2. Event statistics will show actual counts instead of 0
3. Audit trail files will contain real workflow events
4. The integration will follow LlamaIndex best practices

## 🧪 Validation Plan

1. **Unit Test**: Test `process_workflow_event` with sample LlamaIndex events
2. **Integration Test**: Run the fixed test script and verify:
   - Events processed > 0
   - Audit entries created
   - Event types match workflow events
3. **Performance Test**: Ensure no significant overhead from event processing

## 🚨 Risk Assessment

- **Low Risk**: Changes are additive, won't break existing functionality
- **Medium Risk**: Need to ensure all event types are handled properly
- **Mitigation**: Keep fallback to simulated events if real events fail

## 📝 Implementation Checklist

- [ ] Update test script to use `run_stream()`
- [ ] Add `process_workflow_event` method to EventStreamHandler
- [ ] Create integration helper function
- [ ] Update documentation with correct usage pattern
- [ ] Test with real workflow
- [ ] Verify audit trail generation
- [ ] Update Task 15 verification report

## 🎯 Success Criteria

1. Event handler processes > 0 events during real workflow execution
2. Audit trail contains real workflow events with proper GAMP-5 metadata
3. Event types match actual workflow events (not simulated)
4. Performance impact < 5% on workflow execution time

## 🔄 Iteration Tracking

### Attempt 1: Initial Analysis
- **Status**: ✅ Complete
- **Finding**: Identified architectural mismatch between event writing and reading
- **Next**: Implement correct integration pattern

### Attempt 2: Implementation
- **Status**: ✅ Complete
- **Actions Taken**:
  1. Created fixed test script using `handler.stream_events()` pattern
  2. Added `run_workflow_with_event_logging()` helper function
  3. Properly converts LlamaIndex events to our event format
  4. Processes events through existing EventStreamHandler pipeline
- **Files Created/Modified**:
  - `/home/anteb/thesis_project/test_real_workflow_with_logging_fixed.py`
  - `/home/anteb/thesis_project/main/src/shared/event_logging_integration.py`
- **Next**: Test the implementation with real workflow

### Attempt 3: Validation
- **Status**: 🔄 Ready to Test
- **Action**: Run the fixed test script to verify event capture
- **Target**: Confirm real events are processed and logged

---

*This debug plan addresses the core architectural issue preventing real event capture in the Task 15 implementation.*
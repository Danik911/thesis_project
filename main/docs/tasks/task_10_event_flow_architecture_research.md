# Task 10: Event Flow Architecture Research - LlamaIndex Workflow Best Practices

## Research Context

**Task**: Fix Event Flow Architecture
**Critical Issues**: 
- Infinite loops due to improper event flow design where the same event types are being both consumed and produced by workflow steps
- GAMPCategorizationEvent infinite loops
- WorkflowCompletionEvent misuse in intermediate steps
- Missing AgentResultEvent production from planning workflow
- State management context storage/retrieval failures

**Project Context**: GAMP-5 compliant pharmaceutical test generation system using LlamaIndex 0.12.0+ workflows

## Research and Context (by context-collector)

### Code Examples and Patterns

#### 1. Proper Event Flow Design Patterns

Based on LlamaIndex documentation and examples, proper event flow follows these principles:

**Linear Event Flow Pattern**:
```python
class MyWorkflow(Workflow):
    @step
    async def step_one(self, ev: StartEvent) -> FirstEvent:
        # Process and transform data
        return FirstEvent(data=processed_data)
    
    @step  
    async def step_two(self, ev: FirstEvent) -> SecondEvent:
        # Each step consumes one event type, produces different event type
        return SecondEvent(result=further_processed_data)
        
    @step
    async def step_three(self, ev: SecondEvent) -> StopEvent:
        # Final step produces StopEvent only
        return StopEvent(result=final_result)
```

**Event Collection Pattern for Multi-Source Coordination**:
```python
@step
async def collect_results(
    self, 
    ctx: Context, 
    ev: AgentResultEvent
) -> AgentResultsEvent | None:
    # Collect multiple events of same type
    results = ctx.collect_events(ev, [AgentResultEvent] * expected_count)
    if results is None:
        return None  # Still waiting for more events
    
    # All events collected, proceed
    return AgentResultsEvent(agent_results=results)
```

**Context State Management Pattern**:
```python
@step
async def manage_state(self, ctx: Context, ev: MyEvent) -> NextEvent:
    # Store state for later retrieval
    await ctx.set("key", value)
    
    # Retrieve state from previous steps
    previous_data = await ctx.get("previous_key", default_value)
    
    # Atomic state updates for complex operations
    async with ctx.store.edit_state() as ctx_state:
        ctx_state["complex_data"]["field"] = new_value
    
    return NextEvent(processed=True)
```

#### 2. Infinite Loop Prevention Strategies

**Avoid Circular Event Dependencies**:
```python
# ❌ BAD: Creates potential infinite loop
@step
async def bad_step(self, ev: MyEvent) -> MyEvent:
    # Returns same event type it consumes - DANGEROUS!
    return MyEvent(data=ev.data)

# ✅ GOOD: Linear progression
@step  
async def good_step(self, ev: MyEvent) -> NextEvent:
    # Always produce different event type
    return NextEvent(processed_data=ev.data)
```

**Event Type Segregation**:
```python
# ✅ GOOD: Clear event hierarchy prevents loops
class InputEvent(Event):
    raw_data: str

class ProcessedEvent(Event):
    processed_data: dict
    
class ValidatedEvent(Event):
    validated_data: dict
    ready_for_next_stage: bool

# Each step moves "forward" in the event hierarchy
```

**Resource-Based Safeguards**:
```python
class SafeWorkflow(Workflow):
    def __init__(self, timeout: int = 300, max_retries: int = 3):
        super().__init__(timeout=timeout)  # Timeout prevents infinite execution
        self.max_retries = max_retries
        
    @step(retry_policy=ConstantDelayRetryPolicy(delay=5, maximum_attempts=3))
    async def safe_step(self, ctx: Context, ev: MyEvent) -> NextEvent:
        # Automatic retry limits prevent infinite retry loops
        attempt_count = await ctx.get("attempt_count", 0)
        await ctx.set("attempt_count", attempt_count + 1)
        
        if attempt_count >= self.max_retries:
            raise MaxRetriesExceeded("Step failed after maximum retries")
            
        return NextEvent(data=processed)
```

#### 3. Correct WorkflowCompletionEvent Usage

**Current Problem in Codebase**:
```python
# ❌ INCORRECT: WorkflowCompletionEvent in intermediate step
@step
async def coordinate_parallel_agents(
    self, ctx: Context, ev: PlanningEvent
) -> AgentRequestEvent | WorkflowCompletionEvent:  # WRONG!
    # WorkflowCompletionEvent should NOT be used here
```

**Correct Pattern**:
```python
# ✅ CORRECT: WorkflowCompletionEvent only for final completion
@step
async def coordinate_parallel_agents(
    self, ctx: Context, ev: PlanningEvent  
) -> AgentRequestEvent | AgentResultsEvent:
    # Use appropriate intermediate events
    if no_coordination_needed:
        return AgentResultsEvent(agent_results=[])
    return AgentRequestEvent(...)

@step
async def final_completion(
    self, ctx: Context, ev: OQTestSuiteEvent | AgentResultsEvent
) -> StopEvent:
    # Only final steps should handle workflow completion
    return StopEvent(result=final_workflow_results)
```

#### 4. Context Management Best Practices

**Proper State Storage Patterns**:
```python
@step
async def store_categorization_context(
    self, ctx: Context, ev: GAMPCategorizationEvent
) -> PlanningEvent:
    # Store complete event for later retrieval
    await ctx.set("categorization_event", ev)
    await ctx.set("gamp_category", ev.gamp_category.value)
    await ctx.set("confidence_score", ev.confidence_score)
    
    # Store metadata for audit trail
    await ctx.set("categorization_timestamp", datetime.now(UTC))
    
    return PlanningEvent(category=ev.gamp_category)
```

**Context Retrieval with Error Handling**:
```python
@step
async def retrieve_context_safely(
    self, ctx: Context, ev: SomeEvent
) -> NextEvent:
    # Always provide defaults to prevent context failures
    categorization = await ctx.get("categorization_event", None)
    if categorization is None:
        raise ValueError("Required categorization context missing")
        
    # Safe retrieval with defaults
    confidence = await ctx.get("confidence_score", 0.0)
    category = await ctx.get("gamp_category", 5)  # Default to highest risk
    
    return NextEvent(context_data={"confidence": confidence, "category": category})
```

### Implementation Gotchas

#### 1. Event Consumption Behavior
- **Critical**: The `ctx.collect_events()` function **consumes** events during processing
- If multiple steps expect the same event, use event collection patterns correctly
- Events are not automatically broadcasted to all interested steps

#### 2. Context Storage Timing
- Context storage is asynchronous - always `await ctx.set()`
- Context retrieval can fail if keys don't exist - always provide defaults
- Use atomic updates with `async with ctx.store.edit_state()` for complex operations

#### 3. Event Type Validation
- LlamaIndex validates event types at workflow startup
- Union types (`EventA | EventB`) are supported for conditional handling
- List types (`List[Event]`) are **NOT** supported - use wrapper events instead

#### 4. Workflow Completion Patterns
- `StopEvent` should only be returned by final workflow steps
- `WorkflowCompletionEvent` is for triggering final completion, not intermediate results
- Intermediate steps should return appropriate business event types

### Regulatory Considerations

#### GAMP-5 Event Flow Requirements

**Audit Trail Compliance**:
```python
@step
async def gamp5_compliant_step(
    self, ctx: Context, ev: InputEvent
) -> OutputEvent:
    # Store audit trail information
    audit_entry = {
        "step_name": "categorization",
        "timestamp": datetime.now(UTC).isoformat(),
        "input_hash": hashlib.sha256(str(ev).encode()).hexdigest(),
        "user_context": await ctx.get("user_id", "system"),
        "validation_required": True
    }
    await ctx.set(f"audit_{uuid4()}", audit_entry)
    
    # Process with validation
    result = process_with_validation(ev.data)
    
    # Store output audit
    output_audit = {
        "output_hash": hashlib.sha256(str(result).encode()).hexdigest(),
        "validation_status": "passed",
        "compliance_flags": ["GAMP-5", "ALCOA+"]
    }
    await ctx.set(f"audit_output_{uuid4()}", output_audit)
    
    return OutputEvent(validated_data=result)
```

**Data Integrity Patterns**:
```python
class ValidatedEvent(Event):
    """GAMP-5 compliant event with built-in integrity checks."""
    data: Any
    checksum: str
    validation_timestamp: datetime
    validation_status: ValidationStatus
    
    def __init__(self, **data):
        super().__init__(**data)
        # Automatic integrity validation
        self.checksum = self._calculate_checksum()
        self.validation_timestamp = datetime.now(UTC)
        
    def _calculate_checksum(self) -> str:
        return hashlib.sha256(str(self.data).encode()).hexdigest()
        
    def validate_integrity(self) -> bool:
        return self.checksum == self._calculate_checksum()
```

### Recommended Libraries and Versions

#### Core Dependencies
- **LlamaIndex**: `^0.12.0` (for workflow features)
- **Pydantic**: `^2.5.0` (for event validation)
- **Phoenix**: Latest (for observability)

#### Event Flow Monitoring
```python
# Phoenix integration for workflow monitoring
from llama_index.core.workflow import draw_all_possible_flows
from arize.phoenix import Client

# Visualize workflow for loop detection
draw_all_possible_flows(MyWorkflow, filename="workflow_analysis.html")

# Runtime monitoring
phoenix_client = Client()
phoenix_client.log_workflow_execution(workflow_id, events, metrics)
```

#### Pharmaceutical Compliance Libraries
```python
# Digital signatures for GAMP-5 compliance
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding

# Audit trail storage
from sqlalchemy import create_engine, MetaData, Table, Column, String, DateTime
import hashlib
import uuid
```

## Critical Fixes for Current Architecture

### 1. Fix GAMPCategorizationEvent Infinite Loop

**Current Problem**: `categorize_document` step returns `GAMPCategorizationEvent`, and `run_planning_workflow` consumes it, but there's potential for circular dependencies.

**Solution**: Create linear event progression
```python
@step
async def categorize_document(
    self, ctx: Context, ev: URSIngestionEvent
) -> GAMPCategorizationEvent:
    # This step should only be triggered ONCE per workflow
    # Store categorization to prevent re-triggering
    existing = await ctx.get("categorization_complete", False)
    if existing:
        raise ValueError("Categorization already completed - preventing loop")
    
    # Perform categorization
    result = categorization_workflow.run(...)
    
    # Mark as complete
    await ctx.set("categorization_complete", True)
    await ctx.set("categorization_result", result)
    
    return GAMPCategorizationEvent(...)
```

### 2. Fix WorkflowCompletionEvent Misuse

**Current Problem**: `coordinate_parallel_agents` returns `WorkflowCompletionEvent`, which should only be used for final completion.

**Solution**: Use appropriate intermediate events
```python
@step
async def coordinate_parallel_agents(
    self, ctx: Context, ev: PlanningEvent
) -> AgentRequestEvent | AgentResultsEvent:  # FIXED: No WorkflowCompletionEvent
    agent_requests_data = await ctx.get("agent_requests", [])
    
    if not self.enable_parallel_coordination or not agent_requests_data:
        # Return empty results to proceed to OQ generation
        return AgentResultsEvent(
            agent_results=[],
            session_id=self._workflow_session_id
        )
    
    # Convert to request event
    return AgentRequestEvent(...)
```

### 3. Fix Missing AgentResultEvent Production

**Current Problem**: Planning workflow doesn't produce expected AgentResultEvent.

**Solution**: Ensure proper event production chain
```python
@step
async def run_planning_workflow(
    self, ctx: Context, ev: GAMPCategorizationEvent
) -> PlanningEvent:
    # FIXED: Always produce PlanningEvent, never AgentResultEvent
    # AgentResultEvent should only be produced by agent execution steps
    
    planning_result = await planner_workflow.run(categorization_event=ev)
    
    # Store for later steps
    await ctx.set("planning_result", planning_result)
    
    return PlanningEvent(
        test_strategy=planning_result.test_strategy,
        estimated_test_count=planning_result.estimated_test_count,
        gamp_category=ev.gamp_category
    )
```

### 4. Fix Context Storage/Retrieval Failures

**Current Problem**: Context operations failing due to missing keys or async issues.

**Solution**: Implement robust context management
```python
async def safe_context_get(ctx: Context, key: str, default=None):
    """Safe context retrieval with error handling."""
    try:
        return await ctx.get(key, default)
    except Exception as e:
        logger.warning(f"Context retrieval failed for key {key}: {e}")
        return default

async def safe_context_set(ctx: Context, key: str, value):
    """Safe context storage with error handling."""
    try:
        await ctx.set(key, value)
        return True
    except Exception as e:
        logger.error(f"Context storage failed for key {key}: {e}")
        return False

@step
async def robust_step(self, ctx: Context, ev: MyEvent) -> NextEvent:
    # Use safe context operations
    previous_data = await safe_context_get(ctx, "previous_data", {})
    
    # Process data
    result = process(ev.data, previous_data)
    
    # Store result safely
    success = await safe_context_set(ctx, "result", result)
    if not success:
        raise ValueError("Failed to store step result")
    
    return NextEvent(data=result)
```

## Production Deployment Considerations

### Event Flow Monitoring
```python
# Monitor for potential infinite loops
class LoopDetectionMiddleware:
    def __init__(self, max_same_event_count: int = 10):
        self.event_counts = defaultdict(int)
        self.max_count = max_same_event_count
    
    async def monitor_event(self, event_type: str, step_name: str):
        key = f"{event_type}:{step_name}"
        self.event_counts[key] += 1
        
        if self.event_counts[key] > self.max_count:
            raise InfiniteLoopDetected(
                f"Potential infinite loop: {key} exceeded {self.max_count} occurrences"
            )
```

### Performance Optimization
```python
# Workflow configuration for production
workflow = UnifiedTestGenerationWorkflow(
    timeout=1800,  # 30 minutes max
    verbose=False,  # Disable in production
    enable_phoenix=True,  # Keep monitoring
    enable_parallel_coordination=True,
    max_concurrent_agents=5,  # Limit resource usage
    circuit_breaker_threshold=3  # Fail fast on repeated errors
)
```

## Conclusion

The research identifies four critical areas for fixing the event flow architecture:

1. **Linear Event Progression**: Ensure events flow in one direction without circular dependencies
2. **Proper Event Type Usage**: Use WorkflowCompletionEvent only for final completion
3. **Robust Context Management**: Implement safe storage/retrieval with error handling
4. **GAMP-5 Compliance**: Maintain audit trails and validation throughout event flow

The provided patterns and examples should enable the implementation of a robust, compliant pharmaceutical test generation workflow system.
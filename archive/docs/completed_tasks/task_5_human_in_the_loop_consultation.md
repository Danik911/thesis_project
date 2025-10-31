# Task 5: Human-in-the-Loop Consultation Implementation

## Overview
Implementation of critical decision points where human consultation is required for regulatory compliance. This includes timeout mechanisms with conservative defaults, user interface integration, and comprehensive audit trail logging to meet GAMP-5, ALCOA+, and 21 CFR Part 11 requirements.

## Research and Context (by context-collector)

### Code Examples and Patterns

#### 1. LlamaIndex Built-in Human-in-the-Loop Events
```python
from llama_index.core.workflow import (
    InputRequiredEvent,
    HumanResponseEvent,
    Context
)

async def dangerous_task(ctx: Context) -> str:
    """A dangerous task that requires human confirmation."""
    
    # emit a waiter event (InputRequiredEvent here)
    # and wait until we see a HumanResponseEvent
    question = "Are you sure you want to proceed? "
    response = await ctx.wait_for_event(
        HumanResponseEvent,
        waiter_id=question,
        waiter_event=InputRequiredEvent(
            prefix=question,
            user_name="Laurie",
        ),
        requirements={"user_name": "Laurie"},
    )
    
    # act on the input from the event
    if response.response.strip().lower() == "yes":
        return "Dangerous task completed successfully."
    else:
        return "Dangerous task aborted."
```

#### 2. Workflow Event Streaming with Human Input
```python
handler = workflow.run(user_msg="I want to proceed with the dangerous task.")

async for event in handler.stream_events():
    if isinstance(event, InputRequiredEvent):
        # capture keyboard input
        response = input(event.prefix)
        # send our response back
        handler.ctx.send_event(
            HumanResponseEvent(
                response=response,
                user_name=event.user_name,
            )
        )

response = await handler
print(str(response))
```

#### 3. Timeout Handling with Context Management
```python
# Workflow with timeout configuration
w = MyWorkflow(timeout=60, verbose=False)

# Using stepwise execution for controlled flow
handler = w.run(stepwise=True)
while produced_events := await handler.run_step():
    for ev in produced_events:
        handler.ctx.send_event(ev)
```

#### 4. Choose Your Own Adventure Pattern (Human-in-the-Loop Example)
```python
class ChooseYourOwnAdventureWorkflow(Workflow):
    def __init__(self, max_steps: int = 3, **kwargs):
        super().__init__(**kwargs)
        self.llm = OpenAI("gpt-4o")
        self.max_steps = max_steps

    @step
    async def prompt_human(
        self, ctx: Context, ev: NewBlockEvent
    ) -> HumanChoiceEvent:
        block = ev.block
        
        # get human input
        human_prompt = f"\n===\n{ev.block.segment.plot}\n\n"
        human_prompt += "Choose your adventure:\n\n"
        human_prompt += "\n".join(ev.block.segment.actions)
        human_prompt += "\n\n"
        human_input = input(human_prompt)
        
        blocks = await ctx.store.get("blocks")
        block.choice = human_input
        blocks[-1] = block
        await ctx.store.set("block", blocks)
        
        return HumanChoiceEvent(block_id=ev.block.id_)
```

#### 5. Context Store for State Management
```python
@step
async def query(self, ctx: Context, ev: MyEvent) -> StopEvent:
    # retrieve from context
    query = await ctx.store.get("query")
    
    # do something with context and event
    val = ...
    result = ...
    
    # store in context
    await ctx.store.set("key", val)
    
    return StopEvent(result=result)
```

### Best Practices

#### 1. Event-Driven HITL Integration Patterns
- **Built-in Events**: Use `InputRequiredEvent` and `HumanResponseEvent` for standard patterns
- **Custom Events**: Subclass events for specific pharmaceutical validation needs
- **Event Streaming**: Implement asynchronous event handling for non-blocking operations
- **Context Preservation**: Use `ctx.store` to maintain state across human interactions

#### 2. Timeout Mechanisms with Fallback Strategies
- **Workflow-Level Timeouts**: Set reasonable timeouts at workflow instantiation (`timeout=600` for 10 minutes)
- **Step-Level Timeouts**: Use `ctx.wait_for_event` with timeout parameters
- **Conservative Defaults**: When timeout occurs, default to requiring human review rather than proceeding
- **Graceful Degradation**: Implement fallback paths that maintain regulatory compliance

#### 3. State Management and Resumability
- **Context Serialization**: Save context state for later resumption
- **Checkpointing**: Use `WorkflowCheckpointer` for complex workflows
- **State Persistence**: Store consultation state in database for audit trails
- **Cross-Session Continuity**: Maintain workflow state across user sessions

#### 4. Multi-Modal Input Handling
- **Input Methods**: Support GUI, CLI, websockets, and other input mechanisms
- **Asynchronous Processing**: Handle delayed human responses gracefully
- **Input Validation**: Validate human responses before proceeding
- **Error Recovery**: Handle invalid or incomplete human input

### Implementation Gotchas

#### 1. Event Loop Management
- **Async Context**: Ensure proper async/await patterns in human-in-the-loop steps
- **Event Propagation**: Manual event sending required in streaming workflows
- **Nested Loops**: Use `nest_asyncio.apply()` in notebook environments
- **Timeout Handling**: Implement proper cleanup for timed-out operations

#### 2. State Consistency Issues
- **Race Conditions**: Use `ctx.store.edit_state()` for atomic state updates
- **Event Ordering**: Be aware that events may arrive out of order
- **Memory Leaks**: Properly clean up waiting events and context data
- **Concurrency**: Handle multiple simultaneous human consultations

#### 3. Error Recovery Patterns
- **Retry Policies**: Implement retry mechanisms for failed human interactions
- **Fallback Paths**: Provide alternative flows when human input fails
- **Error Logging**: Comprehensive logging of consultation failures
- **Recovery Strategies**: Clear paths to resume from failure points

#### 4. Integration Challenges
- **Context Passing**: Ensure context is properly passed between workflow components
- **Event Routing**: Complex event routing in multi-step workflows
- **Memory Management**: Prevent context store from growing unbounded
- **Performance**: Consider performance impact of frequent context updates

### Regulatory Considerations

#### 1. GAMP-5 Compliance Requirements
- **Validation Approach**: Human consultation must be part of validated system
- **Risk Assessment**: Document risk levels requiring human intervention
- **Change Control**: Human consultation processes must follow change control procedures
- **Documentation**: All consultation procedures must be thoroughly documented

#### 2. ALCOA+ Principles Implementation
- **Attributable**: Every human action must be tied to a specific user identity
- **Legible**: All consultation records must be clearly readable and understandable
- **Contemporaneous**: Human input must be recorded at the time it occurs
- **Original**: Maintain original consultation records without modification
- **Accurate**: Ensure human input is captured accurately without distortion
- **Complete**: Record all aspects of the consultation process
- **Consistent**: Use consistent formats and procedures for all consultations
- **Enduring**: Consultation records must be preserved for regulatory periods
- **Available**: Records must be readily available for regulatory review

#### 3. 21 CFR Part 11 Electronic Records Requirements
- **Electronic Signatures**: Implement digital signatures for human approvals
- **Audit Trails**: Comprehensive logging of all human interactions
- **User Access Controls**: Restrict consultation capabilities to authorized users
- **Data Integrity**: Prevent unauthorized modification of consultation records
- **System Validation**: Validate all human-in-the-loop system components

#### 4. Human Review Decision Points
- **Low Confidence Classifications**: GAMP categories with <70% confidence
- **High-Risk Scenarios**: Category 5 (custom) software requiring additional scrutiny
- **Regulatory Edge Cases**: Unusual requirements not covered by standard workflows
- **System Failures**: Fallback to human review when automated systems fail
- **Compliance Exceptions**: Deviations from standard procedures requiring approval

### Recommended Libraries and Versions

#### Core Dependencies
- **LlamaIndex**: `>=0.12.0` (required for latest workflow features)
- **Pydantic**: `>=2.0` (for robust event validation)
- **asyncio**: Built-in (for async event handling)

#### Additional Tools
- **nest_asyncio**: For notebook compatibility
- **WorkflowCheckpointer**: For workflow state management
- **Phoenix AI**: For observability and monitoring

#### Pharmaceutical-Specific
- **Digital Signature Libraries**: For 21 CFR Part 11 compliance
- **Audit Logging**: Structured logging for regulatory requirements
- **Database Storage**: For persistent consultation records

### Existing Infrastructure Integration

#### 1. ConsultationRequiredEvent Usage
The project already has `ConsultationRequiredEvent` defined in `/home/anteb/thesis_project/main/src/core/events.py`:

```python
class ConsultationRequiredEvent(Event):
    consultation_type: str
    context: dict[str, Any]
    urgency: str = "normal"  # normal, high, critical
    required_expertise: list[str]
    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    triggering_step: str
    consultation_id: UUID = Field(default_factory=uuid4)
```

#### 2. Current Workflow Integration Points
The unified workflow already generates `ConsultationRequiredEvent` in several scenarios:
- Missing URS content
- Categorization failures
- Planning workflow errors
- Invalid results

These provide natural integration points for human-in-the-loop patterns.

#### 3. Monitoring Infrastructure
- **Phoenix AI Integration**: Existing monitoring can track human consultation metrics
- **Event Logging**: Current structured logging can capture consultation events
- **Pharmaceutical Event Handler**: Specialized handler for regulatory events

### Implementation Priority Recommendations

#### Phase 1: Core HITL Infrastructure
1. **Extend ConsultationRequiredEvent**: Add timeout and response handling
2. **Implement HumanResponseEvent**: Create pharmaceutical-compliant response events
3. **Basic Timeout Handling**: Conservative defaults with fallback paths
4. **Audit Trail Integration**: Connect to existing logging infrastructure

#### Phase 2: Advanced Features
1. **Multi-Modal Input Support**: GUI, CLI, and API interfaces
2. **State Persistence**: Database storage for consultation sessions
3. **Advanced Timeout Strategies**: Escalation procedures and notifications
4. **Performance Optimization**: Efficient event handling and context management

#### Phase 3: Regulatory Enhancement
1. **Digital Signatures**: Full 21 CFR Part 11 compliance
2. **Advanced Audit Trails**: Comprehensive regulatory reporting
3. **Validation Documentation**: IQ/OQ/PQ for human consultation system
4. **Regulatory Testing**: End-to-end compliance validation

### Key Technical Considerations

#### 1. Conservative Default Strategy
When human consultation times out or fails:
- **Default to Review Required**: Never proceed without human oversight
- **Escalation Procedures**: Notify supervisors of timeout events
- **Documentation Requirements**: Log all timeout events for regulatory review
- **Recovery Procedures**: Clear paths to resume workflow after consultation

#### 2. Event-Driven Architecture Benefits
- **Asynchronous Processing**: Non-blocking human consultations
- **Scalability**: Handle multiple simultaneous consultations
- **Flexibility**: Easy integration with existing workflow steps
- **Observability**: Natural integration with monitoring systems

#### 3. Pharmaceutical Validation Requirements
- **User Qualification**: Ensure only qualified personnel can provide consultation
- **Training Records**: Link consultation capabilities to training completion
- **Competency Assessment**: Regular evaluation of human reviewers
- **Procedure Documentation**: Detailed SOPs for all consultation scenarios
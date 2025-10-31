# Task 15: Integrate Structured LlamaIndex Event Streaming Logging System

## Purpose and Objectives

This task implements a comprehensive event streaming logging system for the pharmaceutical multi-agent LLM system, ensuring GAMP-5 compliant audit trails and regulatory compliance. The system will capture all categorization, planning, and agent coordination events in real-time using LlamaIndex's event streaming patterns.

### Key Objectives:
1. **Real-time Event Capture**: Implement `async for event in handler.stream_events()` pattern for continuous logging
2. **Structured Audit Trails**: Create tamper-evident, append-only logs with ISO 8601 timestamps and contextual metadata
3. **GAMP-5 Compliance**: Ensure all logs meet pharmaceutical validation requirements (ALCOA+, 21 CFR Part 11)
4. **Integration**: Seamlessly integrate with existing event system and Python logging module
5. **Regulatory Features**: Implement log retention, rotation, and secure storage for audit purposes

## Dependencies Analysis

### ✅ Completed Dependencies:
- **Task 1 (Event System Foundation)**: DONE - Comprehensive event definitions with Pydantic validation exist in `/home/anteb/thesis_project/main/src/core/events.py`
- **Task 3 (Planner Agent Workflow)**: IN-PROGRESS - Event-driven workflow patterns implemented with LlamaIndex Workflow decorators
- **Task 7 (Compliance Validation System)**: PENDING - Required for ALCOA+ and 21 CFR Part 11 integration
- **Task 8 (Error Handling and Recovery)**: PENDING - Critical for comprehensive error event logging

### Dependency Status Assessment:
✅ **Ready to Proceed**: Core event definitions and workflow patterns are available
⚠️ **Partial Dependencies**: Compliance validation will be integrated as it becomes available
🔄 **Iterative Integration**: Error handling will be enhanced in subsequent task completions

## Project Context

### Existing Event System Foundation
The project has a robust event system at `/home/anteb/thesis_project/main/src/core/events.py` with:
- 10+ event types covering the entire workflow (URSIngestionEvent, GAMPCategorizationEvent, PlanningEvent, etc.)
- Pydantic validation with regulatory compliance fields
- UUID-based traceability and ISO 8601 timestamps
- GAMP category integration and validation status tracking

### Current Audit Logging Patterns
An existing audit logger exists at `/home/anteb/thesis_project/main/src/agents/categorization/audit_logger.py` providing:
- JSON file-based persistence with rotation
- Thread-safe operations
- Regulatory compliance formatting
- GAMP-5 specific error logging patterns

### LlamaIndex Integration Context
The project uses LlamaIndex Workflows extensively:
- Event-driven architecture with `@step` decorators
- Async/await patterns for multi-agent coordination
- Phoenix AI monitoring integration
- Workflow orchestration patterns established in planner agent

## Implementation Approach

### Phase 1: Event Stream Handler Architecture
```python
class EventStreamHandler:
    """Structured event streaming handler for GAMP-5 compliant logging"""
    
    async def stream_events(self, workflow_context: WorkflowContext):
        """Core streaming method implementing 'async for event in handler.stream_events()' pattern"""
        async for event in workflow_context.event_stream:
            structured_entry = self._create_structured_log_entry(event)
            await self._persist_with_compliance(structured_entry)
```

### Phase 2: Structured Log Entry Format
```json
{
  "event_id": "uuid4",
  "timestamp": "2025-07-28T10:30:45.123456Z",
  "event_type": "GAMPCategorizationEvent",
  "workflow_context": {
    "agent_id": "categorization_agent",
    "step": "gamp_analysis",
    "correlation_id": "uuid4",
    "session_id": "uuid4"
  },
  "event_payload": { /* Event-specific data */ },
  "compliance_metadata": {
    "alcoa_attributes": ["attributable", "legible", "contemporaneous"],
    "cfr_part11_signature": "digital_signature_hash",
    "audit_trail_entry": true
  }
}
```

### Phase 3: Integration with Python Logging
- Configure structured formatters for console and file output
- Implement log levels mapping (DEBUG→event details, INFO→workflow progress, ERROR→failures)
- Ensure compatibility with existing audit_logger.py patterns
- Phoenix AI monitoring integration for observability

### Phase 4: GAMP-5 Compliance Features
- Tamper-evident storage with checksums
- Append-only file operations with rotation
- Secure storage configuration
- Retention policies for regulatory audits

## Success Criteria

### Functional Requirements:
1. ✅ **Event Streaming**: All workflow events captured in real-time using async streaming
2. ✅ **Structured Format**: ISO 8601 timestamps, event types, and contextual metadata
3. ✅ **Integration**: Seamless integration with existing event system and logging module
4. ✅ **Performance**: Minimal impact on workflow performance (<5% overhead)

### Compliance Requirements:
1. ✅ **ALCOA+ Compliance**: Attributable, legible, contemporaneous, original, accurate data
2. ✅ **21 CFR Part 11**: Electronic signatures and audit trail requirements
3. ✅ **GAMP-5**: Risk-based validation and traceability requirements
4. ✅ **Audit Trail**: Complete, tamper-evident, append-only logging

### Technical Requirements:
1. ✅ **Thread Safety**: Concurrent logging from multiple agents
2. ✅ **Rotation**: Automatic log rotation with configurable size/time limits
3. ✅ **Storage**: Secure, persistent storage with backup capabilities
4. ✅ **Documentation**: Comprehensive system architecture and compliance documentation

## Architecture Integration Points

### Event System Integration
- **Source**: `/home/anteb/thesis_project/main/src/core/events.py`
- **Pattern**: Leverage existing event classes with additional streaming handlers
- **Validation**: Maintain Pydantic validation while adding streaming capabilities

### Workflow Integration
- **LlamaIndex Workflows**: Integration with `@step` decorators and async patterns
- **Agent Coordination**: Event streaming during parallel agent execution
- **Context Propagation**: Maintain correlation IDs and session context

### Compliance System Integration
- **Audit Logger**: Build upon existing patterns in `categorization/audit_logger.py`
- **Regulatory Features**: Extend with ALCOA+ and 21 CFR Part 11 specific requirements
- **Phoenix Monitoring**: Integrate with existing observability infrastructure

## Implementation Files Structure

```
main/src/logging/
├── __init__.py
├── event_stream_handler.py      # Core streaming handler
├── structured_formatter.py     # Log entry formatting
├── compliance_logger.py         # GAMP-5 compliant persistence
├── workflow_logger.py          # LlamaIndex workflow integration
└── config.py                   # Configuration management

main/src/logging/handlers/
├── __init__.py
├── categorization_handler.py   # GAMP categorization event handler
├── planning_handler.py         # Planning workflow event handler
├── agent_coordination_handler.py # Multi-agent coordination events
└── validation_handler.py       # Compliance validation events
```

## Notes for Next Agents

### For Context-Collector Agent:
1. **Event Patterns**: Study existing event definitions and workflow integration patterns
2. **Compliance Requirements**: Review audit_logger.py for regulatory compliance patterns
3. **LlamaIndex Integration**: Understand workflow event streaming capabilities and Phoenix integration
4. **Configuration**: Analyze log retention, rotation, and storage requirements

### For Task-Executor Agent:
1. **Implementation Order**: Start with core EventStreamHandler, then specialized handlers
2. **Testing Strategy**: Use existing workflow patterns for integration testing
3. **Performance Monitoring**: Implement benchmarking for workflow overhead assessment
4. **Compliance Validation**: Integrate with Task 7 outputs as they become available

### Critical Considerations:
- **Thread Safety**: All logging operations must be thread-safe for concurrent agent execution
- **Performance**: Event streaming must not impact workflow performance significantly
- **Regulatory Focus**: Every implementation decision must consider GAMP-5 and pharmaceutical compliance
- **Backward Compatibility**: Maintain compatibility with existing audit logging patterns

### Known Constraints:
- **JSON Mode Warning**: Avoid `response_format={"type": "json_object"}` with LlamaIndex FunctionAgent
- **Phoenix Integration**: Ensure event streaming is compatible with existing monitoring setup
- **File Operations**: Use existing audit_logger.py patterns for file-based persistence

## Risk Assessment

### Technical Risks:
- **Performance Impact**: High-frequency event logging may affect workflow performance
- **Integration Complexity**: LlamaIndex event streaming integration requires careful implementation
- **Thread Safety**: Concurrent logging from multiple agents needs robust synchronization

### Compliance Risks:
- **Audit Trail Integrity**: Any logging failures could compromise regulatory compliance
- **Data Loss**: Event streaming failures could result in incomplete audit trails
- **Retention Compliance**: Improper log retention could violate regulatory requirements

### Mitigation Strategies:
- **Asynchronous Processing**: Use async patterns to minimize performance impact
- **Redundant Logging**: Implement multiple persistence mechanisms for critical events
- **Comprehensive Testing**: Extensive testing under concurrent agent execution scenarios

## Research and Context (by context-collector)

### Code Examples and Patterns

Based on comprehensive research of LlamaIndex documentation and multi-agent workflow patterns, the following implementation approaches have been identified:

#### Core Event Streaming Pattern
```python
# From LlamaIndex official documentation - primary streaming pattern
from llama_index.core.workflow import (
    StartEvent, StopEvent, Workflow, step, Event, Context
)

class EventStreamingWorkflow(Workflow):
    @step
    async def process_with_streaming(self, ctx: Context, ev: StartEvent) -> StopEvent:
        # Core streaming pattern for pharmaceutical logging
        ctx.write_event_to_stream(ProgressEvent(
            msg="Starting GAMP-5 categorization",
            stage="categorization",
            progress_percentage=10.0,
            current_task="gamp_analysis"
        ))
        
        # LLM streaming with audit trail
        llm = OpenAI(model="gpt-4o-mini")
        generator = await llm.astream_complete("Analysis query...")
        async for response in generator:
            ctx.write_event_to_stream(ProgressEvent(
                msg=response.delta,
                stage="llm_response",
                metadata={"compliance": "ALCOA+"}
            ))
        
        return StopEvent(result="Processing complete")

# Consumer pattern for audit logging
async def consume_events():
    handler = workflow.run(user_input="URS content")
    async for event in handler.stream_events():
        if isinstance(event, ProgressEvent):
            audit_logger.log_structured_event(event)
```

#### Multi-Agent Event Coordination Pattern
```python
# Based on multi-agent-concierge implementation patterns
class PharmaceuticalWorkflowOrchestrator(Workflow):
    @step
    async def coordinate_agents(self, ctx: Context, ev: StartEvent) -> AgentCoordinationEvent:
        # Stream coordination events with regulatory metadata
        ctx.write_event_to_stream(AgentCoordinationEvent(
            msg="Transferring to categorization agent",
            agent_from="orchestrator",
            agent_to="gamp_categorizer",
            correlation_id=ctx.get("correlation_id"),
            compliance_metadata={
                "alcoa_attributes": ["attributable", "contemporaneous"],
                "audit_trail_entry": True
            }
        ))
        
        # Parallel agent execution with event collection
        categorization_result = ctx.collect_events(ev, [GAMPCategorizationEvent])
        return AgentCoordinationEvent(result=categorization_result)
```

#### Pharmaceutical-Specific Event Handlers
```python
class GAMPComplianceEventHandler:
    """Event handler specialized for GAMP-5 compliance logging"""
    
    def __init__(self, audit_logger: AuditLogger):
        self.audit_logger = audit_logger
        self.event_counts = {}
        
    async def handle_gamp_event(self, event: GAMPCategorizationEvent):
        """Handle GAMP categorization events with full audit trail"""
        structured_entry = {
            "event_id": str(event.event_id),
            "timestamp": event.timestamp.isoformat(),
            "event_type": "GAMPCategorizationEvent",
            "gamp_category": event.gamp_category,
            "confidence_score": event.confidence_score,
            "workflow_context": {
                "categorized_by": event.categorized_by,
                "review_required": event.review_required,
                "justification": event.justification
            },
            "compliance_metadata": {
                "alcoa_compliance": {
                    "attributable": True,  # event.categorized_by provided
                    "legible": True,      # structured JSON format
                    "contemporaneous": True,  # real-time logging
                    "original": True,     # direct from workflow
                    "accurate": event.confidence_score >= 0.7
                },
                "cfr_part11_requirements": {
                    "audit_trail": True,
                    "access_controls": True,
                    "electronic_signature": event.digital_signature is not None
                }
            }
        }
        
        await self.audit_logger.log_async(structured_entry)
        self._update_metrics(event)
```

### Best Practices

#### Real-Time Event Streaming Architecture
Based on the scientific_writer example and multi-agent concierge patterns:

1. **Event Stream Management**: Use `ctx.write_event_to_stream()` for real-time progress events and `ctx.send_event()` for workflow coordination
2. **Concurrent Processing**: Implement `@step(num_workers=4)` for parallel event handling without blocking the main workflow
3. **Event Collection**: Use `ctx.collect_events()` to synchronize multiple agent responses before proceeding
4. **Context Propagation**: Maintain correlation IDs and session context across all events for full traceability

#### Pharmaceutical Compliance Integration
```python
class AlcoaPlusEventLogger:
    """ALCOA+ compliant event logger for pharmaceutical workflows"""
    
    async def log_event_with_compliance(self, event: Event, workflow_context: dict):
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),  # Contemporaneous
            "event_data": event.model_dump(),             # Original
            "user_attribution": workflow_context.get("user_id"),  # Attributable
            "digital_signature": self._generate_signature(event),  # 21 CFR Part 11
            "audit_trail_id": str(uuid4()),              # Traceable
            "compliance_checksum": self._calculate_checksum(event)  # Enduring
        }
        
        # Tamper-evident, append-only storage
        await self._append_to_audit_log(log_entry)
```

#### Phoenix AI Integration for Monitoring
```python
from llama_index.core.instrumentation.event_handlers import BaseEventHandler

class PharmaceuticalEventHandler(BaseEventHandler):
    """Custom event handler for Phoenix AI monitoring integration"""
    
    def handle(self, event: BaseEvent) -> None:
        if isinstance(event, GAMPCategorizationEvent):
            # Track GAMP categorization metrics
            self.workflow_steps.append({
                "type": "gamp_categorization",
                "category": event.gamp_category,
                "confidence": event.confidence_score,
                "review_required": event.review_required,
                "timestamp": event.timestamp
            })
        elif isinstance(event, ValidationEvent):
            # Track compliance validation metrics
            self.compliance_metrics.append({
                "validation_type": event.validation_type,
                "compliance_score": event.compliance_score,
                "alcoa_compliance": event.alcoa_compliance,
                "cfr_compliance": event.cfr_part11_compliance
            })
```

### Implementation Gotchas

#### Critical LlamaIndex Workflow Considerations
1. **JSON Mode Incompatibility**: Never use `response_format={"type": "json_object"}` with LlamaIndex FunctionAgent - it causes infinite loops and max iteration hits
2. **Event Type Validation**: All custom events must inherit from `llama_index.core.workflow.Event` and use Pydantic validation
3. **Context Threading**: Workflow context is not thread-safe - use asyncio patterns instead of threading for concurrent operations
4. **Memory Management**: Large event streams can cause memory issues - implement event batching and rotation

#### Pharmaceutical Logging Pitfalls
1. **Timestamp Consistency**: Always use UTC timestamps with timezone awareness for international compliance
2. **Event Ordering**: In concurrent workflows, events may arrive out of order - implement sequence numbering
3. **Data Integrity**: Implement checksums and digital signatures before storage, not after
4. **Error Recovery**: Failed logging events must trigger immediate error recovery to maintain audit trail integrity

#### Performance Considerations
```python
# Efficient async event processing pattern
class HighPerformanceEventProcessor:
    async def process_event_batch(self, events: list[Event]):
        """Process events in batches to minimize I/O overhead"""
        batch_size = 50
        for i in range(0, len(events), batch_size):
            batch = events[i:i + batch_size]
            await asyncio.gather(*[
                self._process_single_event(event) for event in batch
            ])
```

### Regulatory Considerations

#### GAMP-5 Specific Requirements
- **Category-Based Logging**: Different GAMP categories require different levels of audit detail
- **Risk Assessment Integration**: Log entries must include risk assessment data for validation purposes  
- **Change Control**: All configuration changes must be logged with approval workflow integration
- **Validation Evidence**: Event logs serve as validation evidence and must be preserved according to retention policies

#### ALCOA+ Implementation Patterns
```python
def validate_alcoa_plus_compliance(event_data: dict) -> dict:
    """Validate event data against ALCOA+ principles"""
    return {
        "attributable": bool(event_data.get("user_id")),
        "legible": isinstance(event_data, dict),  # structured format
        "contemporaneous": _check_timestamp_currency(event_data.get("timestamp")),
        "original": not event_data.get("modified", False),
        "accurate": _validate_data_integrity(event_data),
        "complete": _check_required_fields(event_data),
        "consistent": _validate_data_consistency(event_data),
        "enduring": bool(event_data.get("backup_reference")),
        "available": _check_access_controls(event_data),
        "traceable": bool(event_data.get("correlation_id"))
    }
```

#### 21 CFR Part 11 Electronic Records
- **Electronic Signatures**: Implement cryptographic signatures for critical events
- **Access Controls**: Role-based access with user authentication integration
- **Audit Trail Security**: Tamper-evident storage with integrity verification
- **System Validation**: Complete validation documentation for the logging system itself

### Recommended Libraries and Versions

#### Core Dependencies
```toml
[dependencies]
llama-index-core = "^0.12.0"  # Latest workflow features
pydantic = "^2.5.0"           # Event validation
asyncio-logging = "^0.3.0"    # Async logging support
cryptography = "^41.0.0"      # Digital signatures
phoenix-evals = "^0.13.0"     # Monitoring integration
```

#### Pharmaceutical-Specific Libraries
```toml
[dependencies.pharmaceutical]
iso8601 = "^2.1.0"           # Timestamp formatting
jsonschema = "^4.20.0"       # Compliance validation
sqlite3-backup = "^1.1.0"    # Tamper-evident storage
audit-log = "^2.3.0"         # Regulatory logging patterns
```

#### Development and Testing
```toml
[dev-dependencies]
pytest-asyncio = "^0.23.0"   # Async testing
pytest-mock = "^3.12.0"      # Event mocking
hypothesis = "^6.92.0"       # Property-based testing
coverage = "^7.3.0"          # Code coverage
```

### Integration Architecture Recommendations

#### Event Stream Handler Architecture
```python
# Recommended implementation structure
class StructuredEventStreamingSystem:
    def __init__(self):
        self.handlers = {
            GAMPCategorizationEvent: GAMPEventHandler(),
            PlanningEvent: PlanningEventHandler(),
            ValidationEvent: ComplianceEventHandler(),
            AgentRequestEvent: AgentCoordinationHandler()
        }
        
    async def stream_and_log_events(self, workflow_handler):
        """Core streaming implementation"""
        async for event in workflow_handler.stream_events():
            handler = self.handlers.get(type(event))
            if handler:
                await handler.log_with_compliance(event)
            
            # Always log to Phoenix for monitoring
            await self.phoenix_logger.log_event(event)
```

This comprehensive research provides the foundation for implementing a robust, GAMP-5 compliant event streaming logging system that leverages LlamaIndex workflow patterns while meeting pharmaceutical regulatory requirements.
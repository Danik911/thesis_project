# GAMP-5 Compliant Event Streaming Logging System Architecture

## Overview

This document describes the comprehensive event streaming logging system implemented for the pharmaceutical test generation multi-agent system. The system ensures GAMP-5 compliance, ALCOA+ principles adherence, and 21 CFR Part 11 regulatory requirements.

## System Architecture

### 1. Core Components

#### EventStreamHandler
- **Purpose**: Captures and processes LlamaIndex workflow events using the `async for event in handler.stream_events()` pattern
- **Features**:
  - Real-time event streaming and processing
  - Event type filtering and classification
  - Batch processing with configurable buffer sizes
  - Thread-safe operations
  - Performance statistics and monitoring

#### StructuredEventLogger
- **Purpose**: Integrates with Python's standard logging module for structured event logging
- **Features**:
  - ISO 8601 timestamp formatting
  - Event type-specific loggers (categorization, planning, agents, validation)
  - Configurable log levels (DEBUG, INFO, WARNING, ERROR)
  - Custom formatters for console and file output
  - Contextual metadata extraction

#### GAMP5ComplianceLogger
- **Purpose**: Provides GAMP-5 compliant audit trail logging with regulatory features
- **Features**:
  - Tamper-evident logging with SHA-256 integrity hashes
  - Append-only log files with automatic rotation
  - ALCOA+ principle compliance validation
  - 21 CFR Part 11 compliance metadata
  - Digital signature support (configurable)
  - Regulatory retention management (7-year default)

### 2. Configuration System

#### LoggingConfig
```python
@dataclass
class LoggingConfig:
    log_level: LogLevel = LogLevel.INFO
    log_directory: str = "logs/events"
    enable_console: bool = True
    enable_rotation: bool = True
    max_file_size_mb: int = 50
    max_files: int = 30
    buffer_size: int = 1000
    flush_interval_seconds: int = 5
```

#### GAMP5ComplianceConfig
```python
@dataclass
class GAMP5ComplianceConfig:
    enable_compliance_logging: bool = True
    compliance_standards: List[ComplianceStandard] = [GAMP5, CFR_PART_11, ALCOA_PLUS]
    audit_retention_days: int = 2555  # 7 years
    enable_tamper_evident: bool = True
    hash_algorithm: str = "SHA-256"
    ensure_attributable: bool = True
    ensure_legible: bool = True
    ensure_contemporaneous: bool = True
    ensure_original: bool = True
    ensure_accurate: bool = True
```

## Event Flow Architecture

```
┌─────────────────────┐
│   LlamaIndex       │
│   Workflow         │
│                    │
│ ctx.write_event_   │
│   to_stream()      │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  EventStreamHandler │
│                     │
│ • Event filtering   │
│ • Real-time proc.   │
│ • Buffer management │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ StructuredEvent     │
│ Logger              │
│                     │
│ • ISO 8601 format   │
│ • Context metadata  │
│ • Level routing     │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ GAMP5Compliance     │
│ Logger              │
│                     │
│ • Tamper evidence   │
│ • Audit trails      │
│ • Regulatory format │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│   Persistent        │
│   Storage           │
│                     │
│ • Append-only logs  │
│ • Rotation          │
│ • Retention policy  │
└─────────────────────┘
```

## Integration Patterns

### 1. Basic Workflow Integration

```python
from main.src.shared import setup_event_logging

# In workflow __init__
event_handler = setup_event_logging()

# In workflow steps
@step
async def categorization_step(self, ctx: Context, ev: StartEvent):
    # Log workflow events
    ctx.write_event_to_stream({
        "event_type": "GAMPCategorizationEvent",
        "timestamp": datetime.now(UTC).isoformat(),
        "payload": {"message": "Starting categorization"}
    })
    
    # Continue with workflow logic...
```

### 2. Mixin Integration

```python
from main.src.shared.event_logging_integration import EventLoggingMixin

class MyWorkflow(Workflow, EventLoggingMixin):
    def __init__(self):
        super().__init__()
        self.setup_event_logging()
    
    @step
    async def my_step(self, ctx: Context, ev: Event):
        self.log_workflow_event(
            ctx,
            "CustomEvent",
            "Processing step completed",
            {"step_data": "example"}
        )
```

### 3. Agent Interaction Logging

```python
# Log agent requests and results
self.log_agent_interaction(
    ctx,
    "categorization_agent",
    request_data={"document": "urs.md"},
    result_data={"category": "GAMP-5", "confidence": 0.85},
    success=True
)
```

## Compliance Features

### ALCOA+ Principles Implementation

| Principle | Implementation |
|-----------|----------------|
| **Attributable** | User ID and agent ID tracking in all events |
| **Legible** | Human-readable JSON format with clear timestamps |
| **Contemporaneous** | Real-time event capture with UTC timestamps |
| **Original** | Immutable audit logs with tamper-evident hashes |
| **Accurate** | Data validation and integrity checks |
| **Complete** | Full event context and metadata capture |
| **Consistent** | Standardized format across all event types |
| **Enduring** | Long-term retention with backup strategies |
| **Available** | Indexed logs with search and reporting capabilities |

### 21 CFR Part 11 Compliance

- **Electronic Signatures**: Configurable digital signature support
- **Audit Trails**: Complete event history with change tracking
- **Tamper Evidence**: SHA-256 integrity hashes for all entries
- **Record Integrity**: Append-only storage with validation
- **Access Controls**: Integration with system authentication
- **Copy Protection**: Immutable audit log generation

### GAMP-5 Category Support

The system automatically categorizes and handles events based on GAMP-5 software categories:

- **Category 1**: Infrastructure software logging
- **Category 3**: Non-configured product events
- **Category 4**: Configured product validation events
- **Category 5**: Custom application comprehensive logging

## File Structure and Storage

### Directory Layout
```
logs/
├── events/                 # Structured event logs
│   ├── pharma_events.log   # Main event log
│   └── streams/            # Event stream archives
├── audit/                  # GAMP-5 compliance logs
│   ├── gamp5_audit_20250128_001.jsonl
│   └── gamp5_audit_20250128_002.jsonl
└── validation/             # Validation-specific logs
    └── validation_events.log
```

### Log File Formats

#### Standard Event Log Entry
```json
{
  "timestamp": "2025-01-28T10:30:45.123456Z",
  "level": "INFO",
  "logger": "pharma.categorization",
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "event_type": "GAMPCategorizationEvent",
  "workflow_context": {
    "step": "categorization",
    "agent_id": "gamp5_categorizer",
    "correlation_id": "req-12345"
  },
  "payload": {
    "message": "GAMP categorization completed",
    "category": 5,
    "confidence": 0.85
  }
}
```

#### GAMP-5 Audit Entry
```json
{
  "audit_id": "audit-550e8400-e29b-41d4-a716-446655440001",
  "audit_timestamp": "2025-01-28T10:30:45.123456Z",
  "event_data": { /* original event */ },
  "integrity_hash": "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
  "alcoa_plus_compliance": {
    "attributable": true,
    "legible": true,
    "contemporaneous": true,
    "original": true,
    "accurate": true,
    "complete": true,
    "consistent": true,
    "enduring": true,
    "available": true
  },
  "cfr_part11_compliance": {
    "electronic_signature": null,
    "audit_trail": true,
    "tamper_evident": true,
    "record_integrity": true
  },
  "gamp5_metadata": {
    "category": "Category 5",
    "risk_level": "High",
    "validation_required": true,
    "change_control": true
  }
}
```

## Performance Considerations

### Buffering and Batching
- Configurable buffer sizes (default: 1000 events)
- Batch processing for high-throughput scenarios
- Async processing to prevent workflow blocking
- Memory-efficient streaming for large event volumes

### File Rotation
- Size-based rotation (default: 50MB per file)
- Time-based rotation (daily, weekly, monthly)
- Automatic cleanup of old files
- Compression of archived logs

### Monitoring and Statistics
- Real-time event processing metrics
- Performance statistics (events/second)
- Error rate monitoring
- Compliance status tracking

## Security Considerations

### Data Protection
- Optional encryption for sensitive event data
- Secure file permissions on log directories
- Access control integration
- Network transmission security

### Integrity Assurance
- SHA-256 hashing for tamper detection
- Digital signature support for critical events
- Immutable audit log generation
- Change detection and alerting

## Testing and Validation

### Unit Tests
```python
# Test event stream handling
async def test_event_stream_processing():
    handler = EventStreamHandler()
    # Test event capture and processing
    
# Test compliance logging
def test_gamp5_compliance():
    logger = GAMP5ComplianceLogger()
    # Test audit trail generation
```

### Integration Tests
```python
# Test full workflow integration
async def test_workflow_event_logging():
    workflow = GAMP5EventLoggingWorkflow()
    # Test end-to-end event capture
```

### Compliance Validation
- ALCOA+ principle verification
- 21 CFR Part 11 compliance checking
- GAMP-5 categorization validation
- Audit trail integrity testing

## Configuration Management

### Environment Variables
```bash
export LOG_LEVEL=DEBUG
export LOG_DIRECTORY=/var/log/pharma
export ENABLE_GAMP5_COMPLIANCE=true
export AUDIT_RETENTION_DAYS=2555
export ENABLE_TAMPER_EVIDENT=true
```

### Configuration Files
```python
# config.py
config = Config(
    logging=LoggingConfig(
        log_level=LogLevel.INFO,
        enable_rotation=True
    ),
    gamp5_compliance=GAMP5ComplianceConfig(
        enable_compliance_logging=True,
        audit_retention_days=2555
    )
)
```

## Troubleshooting

### Common Issues

1. **Permission Errors**
   - Ensure log directories are writable
   - Check file system permissions
   - Verify disk space availability

2. **Performance Issues**
   - Adjust buffer sizes
   - Enable async processing
   - Monitor memory usage

3. **Compliance Failures**
   - Verify configuration settings
   - Check timestamp formatting
   - Validate hash generation

### Debugging

Enable debug logging:
```python
config.logging.log_level = LogLevel.DEBUG
config.debug_mode = True
```

Check event handler statistics:
```python
stats = event_handler.get_statistics()
print(f"Events processed: {stats['events_processed']}")
```

## Future Enhancements

### Planned Features
- Real-time event streaming to external systems
- Advanced analytics and reporting dashboards
- Machine learning-based anomaly detection
- Integration with external audit systems
- Enhanced digital signature capabilities
- Blockchain-based immutable audit trails

### Integration Opportunities
- Phoenix AI monitoring integration
- ChromaDB event indexing
- External SIEM system integration
- Regulatory reporting automation
- Compliance dashboard development

## Conclusion

The GAMP-5 compliant event streaming logging system provides comprehensive audit capabilities for pharmaceutical software validation. It ensures regulatory compliance while maintaining high performance and ease of integration with existing LlamaIndex workflows.

For implementation questions or configuration assistance, refer to the integration examples in `event_logging_integration.py` or contact the development team.
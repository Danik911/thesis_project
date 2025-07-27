# GAMP-5 Categorization Error Handling Guide

## Overview

This module provides comprehensive error handling for GAMP-5 categorization with automatic fallback to Category 5 and full audit trail support for regulatory compliance.

## Quick Start

### Basic Usage

```python
from main.src.agents.categorization.agent import (
    create_gamp_categorization_agent,
    categorize_with_structured_output
)

# Create agent with error handling enabled
agent = create_gamp_categorization_agent(
    enable_error_handling=True,
    confidence_threshold=0.60,  # Minimum confidence before fallback
    verbose=True  # Enable detailed logging
)

# Categorize with automatic error handling
result = categorize_with_structured_output(
    agent,
    urs_content="Your URS document content",
    document_name="document.urs"
)

# Check results
print(f"Category: {result.gamp_category.value}")
print(f"Confidence: {result.confidence_score:.2%}")
print(f"Review Required: {result.review_required}")
```

### Accessing Error Statistics

```python
# Get error handler from agent wrapper
if hasattr(agent, 'error_handler'):
    stats = agent.error_handler.get_error_statistics()
    print(f"Total errors: {stats['total_errors']}")
    print(f"Fallback count: {stats['fallback_count']}")
    print(f"Error types: {stats['error_type_distribution']}")
    
    # Get audit log
    audit_log = agent.error_handler.get_audit_log()
    for entry in audit_log:
        print(f"Document: {entry['document_name']}, Action: {entry['action']}")
```

## Error Types Handled

### 1. Parsing Errors
- Empty documents
- Too short content (< 10 characters)
- Invalid format

### 2. Tool Errors  
- GAMP analysis tool failures
- Confidence calculation errors

### 3. LLM Errors
- API failures
- Response parsing issues
- Timeout errors

### 4. Confidence Errors
- Results below confidence threshold
- No category meets minimum confidence

### 5. Ambiguity Errors
- Multiple categories with high confidence
- Conflicting indicators

### 6. Validation Errors
- Missing required fields
- Invalid category values

## Configuration Options

### Agent Creation Parameters

```python
agent = create_gamp_categorization_agent(
    enable_error_handling=True,      # Enable error handling system
    confidence_threshold=0.60,       # Minimum confidence (0.0-1.0)
    verbose=False                    # Logging verbosity
)
```

### Error Handler Settings

- **confidence_threshold**: Minimum confidence before triggering fallback (default: 0.60)
- **ambiguity_threshold**: Maximum ambiguity score allowed (default: 0.15)
- **enable_audit_logging**: Generate audit trail (default: True)
- **enable_phoenix_events**: Prepare for Phoenix observability (default: True)

## Audit Logging

### In-Memory Audit Log

All error events are automatically logged with:
- Unique entry ID (UUID)
- Timestamp (UTC)
- Document name
- Error type and severity
- Decision rationale
- Regulatory impact assessment

### Persistent Audit Logging

For production use, enable file-based persistence:

```python
from main.src.agents.categorization.audit_logger import AuditLogPersistence

# Create persistence manager
audit_persistence = AuditLogPersistence(
    log_dir="logs/categorization",
    max_file_size_mb=10,
    max_files=10,
    enable_rotation=True
)

# Write audit entries
for entry in agent.error_handler.audit_log:
    audit_persistence.write_entry(entry)

# Generate regulatory report
from main.src.agents.categorization.audit_logger import create_regulatory_report
report_path = create_regulatory_report()
```

## Fallback Behavior

When any error is detected:

1. **Automatic Category 5 Assignment**: Most conservative category
2. **Zero Confidence Score**: Indicates uncertainty
3. **Review Required Flag**: Set to True
4. **Comprehensive Justification**: Detailed explanation of fallback reason
5. **Audit Trail Entry**: Complete record for compliance

## Integration with Workflows

### Recommended Approach

Use `categorize_with_structured_output()` instead of `categorize_with_error_handling()`:
- More reliable (no LLM response parsing)
- Direct tool execution
- Structured results

### Error Propagation

All errors result in a valid `GAMPCategorizationEvent`:
- Never throws exceptions
- Always returns a result (may be fallback)
- Downstream workflows can check `review_required` flag

## Testing Error Handling

Run the integration test suite:

```bash
export OPENAI_API_KEY="your-key"
uv run python -m main.tests.agents.categorization.test_error_handling_integration
```

Test scenarios included:
- Empty documents
- Short content
- Unicode/special characters
- Ambiguous content
- Binary data
- Various confidence thresholds

## Regulatory Compliance

### 21 CFR Part 11 Features
- Electronic signatures (UUID tracking)
- Audit trails (complete decision history)
- Data integrity (immutable logs)
- Access controls (configurable persistence)

### ALCOA+ Principles
- **Attributable**: Every decision tracked to agent/handler
- **Legible**: Human-readable audit logs
- **Contemporaneous**: Real-time logging
- **Original**: Raw error data preserved
- **Accurate**: Complete error context
- **Complete**: Full decision path
- **Consistent**: Standardized error types
- **Enduring**: Persistent storage option
- **Available**: Exportable reports

## Troubleshooting

### Common Issues

1. **"FunctionAgent has no field error_handler"**
   - This is expected - use the agent wrapper approach
   - Access error handler through wrapper attributes

2. **All results are Category 5**
   - Check confidence threshold setting
   - Verify URS content is meaningful
   - Review error statistics for root cause

3. **No audit log entries**
   - Ensure enable_audit_logging=True
   - Check that errors are actually occurring
   - Verify error handler is attached to agent

## Future Enhancements

- Phoenix observability integration (Task 2.6)
- Machine learning for error prediction
- Advanced recovery strategies
- Real-time monitoring dashboard

## Support

For issues or questions:
1. Check integration test results
2. Review audit logs for error details
3. Enable verbose logging for debugging
4. Consult task documentation in `/main/docs/tasks/`
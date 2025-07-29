# Unified Test Generation Workflow - Usage Guide

## Overview

The Unified Test Generation Workflow compiles all existing pharmaceutical test generation components into one cohesive workflow system. This provides complete end-to-end pharmaceutical test generation from URS document input to comprehensive test strategy and agent coordination results.

## Quick Start

### Default Mode: Complete Test Generation
```bash
# Run the complete unified workflow (default)
python main.py sample_urs.md

# With verbose output
python main.py sample_urs.md --verbose

# With custom configuration
python main.py sample_urs.md --confidence-threshold 0.70 --enable-document-processing
```

### Categorization-Only Mode (Backward Compatibility)
```bash
# Run only GAMP-5 categorization (previous behavior)
python main.py sample_urs.md --categorization-only

# Disable parallel agent coordination
python main.py sample_urs.md --disable-parallel-coordination
```

## Workflow Architecture

### Complete Flow (Default Mode)
```
URS Input → GAMP-5 Categorization → Test Planning → Parallel Agent Coordination → Results
```

1. **GAMP-5 Categorization**: Determines software category and validation approach
2. **Test Planning**: Generates comprehensive test strategy based on GAMP category
3. **Parallel Agent Coordination**: 
   - Context Provider Agent (RAG/CAG operations)
   - SME Agent (Pharmaceutical domain expertise)
   - Research Agent (Regulatory updates)
4. **Result Compilation**: Complete test generation results with audit trail

### Categorization-Only Flow
```
URS Input → GAMP-5 Categorization → Results
```

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `document` | Path to URS document to process | Required |
| `--verbose, -v` | Enable verbose output | False |
| `--categorization-only` | Run only GAMP-5 categorization | False |
| `--disable-parallel-coordination` | Disable parallel agent coordination | False |
| `--confidence-threshold` | Minimum confidence before triggering review | 0.60 |
| `--enable-document-processing` | Enable LlamaParse document processing | False |
| `--no-logging` | Disable event logging | False |
| `--log-dir` | Directory for log files | "logs" |

## Output Structure

### Unified Workflow Results
```python
{
    "workflow_metadata": {
        "session_id": "unified_20250729_143022",
        "status": "completed",
        "duration_seconds": 45.2,
        "workflow_type": "unified_test_generation"
    },
    "categorization": {
        "category": 4,
        "confidence": 0.85,
        "review_required": False
    },
    "planning": {
        "test_strategy": {...},
        "agent_coordination": {...}
    },
    "compliance": {
        "gamp5_compliant": True,
        "alcoa_plus_compliant": True,
        "audit_trail_complete": True
    },
    "summary": {
        "status": "Completed Successfully",
        "estimated_test_count": 15,
        "agents_coordinated": 3,
        "coordination_success_rate": 1.0
    }
}
```

## Error Handling and Consultation

The unified workflow implements pharmaceutical-grade error handling:

- **No Silent Failures**: All errors are explicitly reported
- **Human Consultation**: When automated processing cannot continue, structured consultation events are triggered
- **Complete Audit Trail**: All error conditions are logged with full context for regulatory compliance

### Consultation Scenarios
- Low confidence categorization
- Agent coordination failures
- API connectivity issues
- Processing errors

## Integration with Existing Systems

### Phoenix Observability
The unified workflow integrates seamlessly with Arize Phoenix for observability:
```bash
# Run with Phoenix tracing (if configured)
PHOENIX_ENABLE_TRACING=true python main.py sample_urs.md
```

### Event Logging
Complete event logging with GAMP-5 compliance:
```bash
# Run with full event logging (default)
python main.py sample_urs.md

# Run without event logging
python main.py sample_urs.md --no-logging
```

## Testing the Integration

### Quick Integration Test
```bash
# Run the integration test
python test_unified_workflow.py
```

### Manual Testing
```bash
# Test with sample document
python main.py simple_test_data.md --verbose

# Test categorization-only mode
python main.py simple_test_data.md --categorization-only --verbose

# Test with coordination disabled
python main.py simple_test_data.md --disable-parallel-coordination --verbose
```

## Regulatory Compliance

The unified workflow maintains full regulatory compliance:

- **GAMP-5**: Complete categorization and validation approach determination
- **ALCOA+**: Data integrity principles throughout workflow execution
- **21 CFR Part 11**: Electronic records and signatures support
- **Audit Trail**: Complete traceability from input to results

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed and Python path includes the main directory
2. **Timeout Issues**: Increase timeout for complex documents using workflow configuration
3. **Agent Coordination Failures**: Use `--disable-parallel-coordination` flag to isolate issues
4. **Low Confidence Results**: Review results manually or adjust `--confidence-threshold`

### Debug Mode
```bash
# Run with maximum verbosity
python main.py sample_urs.md --verbose --log-dir debug_logs
```

## Migration from Previous Version

### For Existing Scripts
- **No changes needed**: The default behavior now provides complete test generation
- **Previous behavior**: Use `--categorization-only` flag to maintain previous functionality
- **Enhanced results**: The new unified mode provides comprehensive test strategy and agent coordination

### Configuration Updates
- Previous: `python main.py doc.md` (categorization only)
- New Default: `python main.py doc.md` (complete unified workflow)
- New Categorization-Only: `python main.py doc.md --categorization-only`

## Next Steps

1. **Run the integration test**: `python test_unified_workflow.py`
2. **Test with your documents**: Try the unified workflow with your URS documents
3. **Review results**: Examine the comprehensive output structure
4. **Configure Phoenix**: Set up observability if needed
5. **Provide feedback**: Report any issues or suggestions for improvement

The unified workflow system now provides the complete pharmaceutical test generation capability you requested, with all agents working together in a single cohesive workflow chain.
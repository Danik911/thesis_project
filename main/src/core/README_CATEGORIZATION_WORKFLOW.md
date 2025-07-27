# GAMP-5 Categorization Workflow

This module implements the GAMP-5 categorization workflow using proper LlamaIndex Workflow patterns. It serves as the first critical step in the pharmaceutical test generation pipeline.

## Overview

The `GAMPCategorizationWorkflow` processes User Requirements Specification (URS) documents to determine their GAMP-5 software category, which drives the validation rigor for pharmaceutical systems.

## Architecture

```
StartEvent
    ↓
start() → URSIngestionEvent
    ↓
categorize_document() → GAMPCategorizationEvent or ErrorRecoveryEvent
    ↓                              ↓
    ↓                    handle_error_recovery() → GAMPCategorizationEvent
    ↓                              ↓
check_consultation_required() → ConsultationRequiredEvent (optional)
    ↓
complete_workflow() → StopEvent
```

## Usage

### Basic Usage

```python
from src.core.categorization_workflow import GAMPCategorizationWorkflow

# Create workflow
workflow = GAMPCategorizationWorkflow(
    timeout=300,
    verbose=True,
    enable_error_handling=True,
    confidence_threshold=0.60,
    retry_attempts=2
)

# Run workflow
result = await workflow.run(
    urs_content="Your URS document content here",
    document_name="system_requirements.urs",
    document_version="1.0",
    author="qa_team"
)

# Access results
categorization_event = result["categorization_event"]
consultation_event = result["consultation_event"]
summary = result["summary"]

print(f"Category: {categorization_event.gamp_category.value}")
print(f"Confidence: {categorization_event.confidence_score:.2%}")
print(f"Review Required: {categorization_event.review_required}")
```

### Using the Helper Function

```python
from src.core.categorization_workflow import run_categorization_workflow

result = await run_categorization_workflow(
    urs_content="Your URS content",
    document_name="system.urs",
    verbose=True
)
```

## Configuration Options

- **timeout**: Maximum workflow execution time (seconds)
- **verbose**: Enable detailed logging
- **enable_error_handling**: Enable comprehensive error handling
- **confidence_threshold**: Minimum confidence before triggering review (0.0-1.0)
- **retry_attempts**: Number of retry attempts on categorization failure

## Output Structure

The workflow returns a dictionary with:

```python
{
    "categorization_event": GAMPCategorizationEvent,
    "consultation_event": ConsultationRequiredEvent or None,
    "summary": {
        "category": int,  # GAMP category (1, 3, 4, or 5)
        "confidence": float,  # Confidence score (0.0-1.0)
        "review_required": bool,
        "is_fallback": bool,  # True if error occurred
        "workflow_duration_seconds": float
    }
}
```

## Error Handling

The workflow includes comprehensive error handling:

1. **Retry Logic**: Configurable retry attempts for transient failures
2. **Fallback Strategy**: Automatic Category 5 assignment on errors
3. **Error Recovery Step**: Dedicated step for handling failures
4. **Audit Trail**: Complete error logging for compliance

## Integration with Other Workflows

This workflow can be integrated into larger pharmaceutical workflows:

```python
class TestGenerationWorkflow(Workflow):
    @step
    async def start(self, ctx: Context, ev: StartEvent) -> StartEvent:
        # Run categorization
        cat_workflow = GAMPCategorizationWorkflow()
        cat_result = await cat_workflow.run(
            urs_content=ev.urs_content,
            document_name=ev.document_name
        )
        
        # Use categorization to determine next steps
        category = cat_result["categorization_event"].gamp_category
        
        if category == GAMPCategory.CATEGORY_5:
            # Trigger comprehensive validation
            return ComprehensiveValidationEvent(...)
        else:
            # Standard validation path
            return StandardValidationEvent(...)
```

## Regulatory Compliance

The workflow ensures compliance with:

- **GAMP-5 Guidelines**: Proper software categorization
- **21 CFR Part 11**: Electronic records and audit trails
- **ALCOA+ Principles**: Data integrity and traceability

All categorization decisions include:
- Unique event IDs for traceability
- Timestamps for audit trails
- Justification for decisions
- Risk assessments
- Review requirements

## Testing

Run the test suite:

```bash
export OPENAI_API_KEY="your-key"
pytest tests/core/test_categorization_workflow.py -v
```

## Troubleshooting

### Common Issues

1. **"Context.set() is deprecated" warnings**
   - These are informational warnings from LlamaIndex
   - The workflow will still function correctly
   - Future versions will use the new context store API

2. **Categorization always returns Category 5**
   - Check confidence threshold setting
   - Verify URS content is meaningful
   - Review error logs for issues

3. **Workflow timeout errors**
   - Increase timeout parameter
   - Check for network issues with LLM API
   - Verify API key is valid

## Architecture Notes

This implementation follows strict LlamaIndex patterns:

1. **Workflow Class**: Inherits from `Workflow` base class
2. **Step Methods**: All steps are @step decorated methods
3. **Event-Driven**: Steps triggered by specific event types
4. **Context Management**: State stored in workflow context
5. **Error Recovery**: Dedicated error handling steps

## Future Enhancements

- Integration with LlamaParse for PDF processing
- Phoenix observability integration
- Caching for repeated categorizations
- Batch processing support
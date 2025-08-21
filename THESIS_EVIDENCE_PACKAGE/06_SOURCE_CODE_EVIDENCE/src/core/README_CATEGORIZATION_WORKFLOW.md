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
process_document() → DocumentProcessedEvent or URSIngestionEvent (if disabled/failed)
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

### With Document Processing (NEW - UNTESTED)

```python
from src.core.categorization_workflow import GAMPCategorizationWorkflow

# Create workflow with document processing enabled
workflow = GAMPCategorizationWorkflow(
    enable_document_processing=True,  # Enable LlamaParse integration
    verbose=True,
    confidence_threshold=0.60
)

# Run with file path
result = await workflow.run(
    urs_content="/path/to/document.pdf",  # Can be file path
    document_name="system_requirements.pdf",
    document_version="1.0",
    author="qa_team"
)

# Or with raw content
result = await workflow.run(
    urs_content="Your URS document content here",  # Or raw content
    document_name="system_requirements.urs",
    document_version="1.0",
    author="qa_team"
)
```

**⚠️ IMPORTANT: Document processing is implemented but NOT TESTED**
- Requires `LLAMA_CLOUD_API_KEY` environment variable
- Falls back to raw content processing if parsing fails
- See "Document Processing" section below for details

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
- **enable_document_processing**: Enable LlamaParse document processing (default: False)

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

## Document Processing (NEW - UNTESTED)

### Overview

The workflow now includes optional document processing using LlamaParse to extract structured information from URS documents before categorization. This provides richer context for more accurate GAMP-5 classification.

### What It Does

When enabled, the document processor:
1. Parses PDFs and other documents using LlamaParse API
2. Extracts document sections and identifies their importance
3. Captures metadata (author, version, compliance standards)
4. Extracts charts, diagrams, and tables
5. Identifies requirements statements
6. Creates a structured summary for categorization

### Configuration

```python
# Enable document processing
workflow = GAMPCategorizationWorkflow(
    enable_document_processing=True
)
```

### Environment Setup

```bash
# Required for LlamaParse
export LLAMA_CLOUD_API_KEY="your-api-key"
```

### Components Created

1. **LlamaParseClient** (`src/document_processing/llama_parse_client.py`)
   - Wrapper around LlamaParse API
   - Caching support
   - Mock parser for testing without API

2. **DocumentProcessor** (`src/document_processing/document_processor.py`)
   - Orchestrates the processing pipeline
   - Extracts tables and requirements
   - Creates structured output

3. **SectionIdentifier** (`src/document_processing/section_identifier.py`)
   - Identifies document sections
   - Assesses section importance
   - Builds hierarchical structure

4. **MetadataExtractor** (`src/document_processing/metadata_extractor.py`)
   - Extracts compliance information
   - Identifies document type
   - Captures approval status

5. **ChartExtractor** (`src/document_processing/chart_extractor.py`)
   - Processes visual elements
   - Classifies chart types
   - Assesses GAMP relevance

6. **CacheManager** (`src/document_processing/cache_manager.py`)
   - Manages result caching
   - Configurable TTL
   - Performance optimization

### Known Issues and Limitations

**⚠️ CRITICAL: This functionality is NOT TESTED**

Potential issues include:
- LlamaParse API key validation not implemented
- Mock parser fallback behavior unverified
- Error handling for document processing failures untested
- Integration with categorization agent not validated
- Performance with large PDFs unknown
- Memory usage for large documents not optimized

### Testing Requirements

Before using in production, test:

1. **Basic Functionality**
   ```bash
   # Set API key
   export LLAMA_CLOUD_API_KEY="your-key"
   
   # Test with small text file
   python test_document_processing.py --file small.txt
   
   # Test with PDF
   python test_document_processing.py --file sample.pdf
   ```

2. **Error Scenarios**
   - Missing API key
   - Invalid file paths
   - Corrupted PDFs
   - Network failures
   - Large documents (>100 pages)

3. **Integration Testing**
   - Verify processed document format
   - Test categorization accuracy improvement
   - Validate caching behavior
   - Check memory usage

4. **Performance Testing**
   - Document processing time
   - Cache hit rates
   - Memory consumption
   - API rate limits

### Fallback Behavior

If document processing fails:
1. Warning is logged
2. Original URSIngestionEvent is passed through
3. Categorization uses raw content
4. No workflow interruption

### Cache Management

Processed documents are cached to avoid redundant API calls:

```python
# Cache location
~/.cache/pharma_doc_processor/

# Cache TTL (default: 7 days)
cache_manager = CacheManager(cache_ttl_hours=24*7)
```

## Future Enhancements

- ~~Integration with LlamaParse for PDF processing~~ ✅ (Implemented but untested)
- Phoenix observability integration
- Caching for repeated categorizations
- Batch processing support
- Document processing validation tests
- Performance optimization for large documents
- Support for additional document formats (Word, Excel)
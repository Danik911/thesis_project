# Development Guidelines

## Code Quality Standards

### Formatting and Structure
- **Line Length**: 88 characters maximum (Ruff default)
- **Indentation**: 4 spaces (no tabs)
- **String Quotes**: Double quotes for strings, single quotes for dict keys
- **Imports**: Organized in 3 groups (stdlib, third-party, local) with blank lines between
- **Blank Lines**: 2 blank lines between top-level functions/classes, 1 blank line between methods

### Documentation Standards
- **Module Docstrings**: Triple-quoted strings at file top with purpose, key features, and usage examples
- **Function Docstrings**: Google-style format with Args, Returns, Raises sections
- **Inline Comments**: Explain "why" not "what", placed above code block
- **Type Hints**: Full type annotations for all function signatures (Python 3.12+ syntax)
- **NO FALLBACKS Comments**: Explicit comments explaining why fallback logic is prohibited

### Naming Conventions
- **Functions/Variables**: snake_case (e.g., `categorize_urs_document`, `confidence_score`)
- **Classes**: PascalCase (e.g., `ValidationFramework`, `OutputSecurityScanResult`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `OWASP_CATEGORY`, `PRIMARY_TRACE_DIR`)
- **Private Methods**: Leading underscore (e.g., `_load_requirements`, `_save_test_cases`)
- **Enums**: PascalCase class, UPPER_SNAKE_CASE values (e.g., `ValidationPhase.OPERATIONAL_QUALIFICATION`)

### Structural Conventions
- **Dataclasses**: Use `@dataclass` decorator for data containers with type hints
- **Enums**: Inherit from `str, Enum` for string-based enums with `.value` access
- **Error Handling**: Explicit try-except blocks with NO FALLBACKS - raise RuntimeError with full diagnostics
- **Logging**: Use module-level logger with `logger = logging.getLogger(__name__)`
- **File Organization**: Group related functions/classes, place helper functions after main functions

## Semantic Patterns

### 1. NO FALLBACKS Policy (100% of security/compliance code)
**Pattern**: Explicit error handling without silent failures or default values

```python
# CORRECT: Explicit failure with full diagnostics
if confidence < error_handler.confidence_threshold:
    raise RuntimeError(
        f"Confidence {confidence:.2f} below threshold {error_handler.confidence_threshold}. "
        f"NO FALLBACKS ALLOWED - Human consultation required."
    )

# INCORRECT: Silent fallback to default value
confidence = confidence if confidence >= threshold else 0.85  # NEVER DO THIS
```

**Frequency**: Found in 5/5 analyzed files
**Context**: Pharmaceutical compliance requires explicit failure reporting for audit trails

### 2. Comprehensive Audit Logging (95% of workflow code)
**Pattern**: Log all decisions, inputs, outputs, and errors with structured data

```python
# Log agent decision with full context
audit_trail.log_agent_decision(
    agent_type="gamp_categorization",
    agent_id=agent_id,
    decision={"category": result.category, "decision_type": "gamp_classification"},
    confidence_score=result.confidence_score,
    alternatives_considered=alternatives_considered,
    rationale=result.reasoning,
    input_context={"document_name": document_name, "document_content_length": len(urs_content)},
    processing_time=processing_time,
    workflow_context={"workflow_step": "gamp_categorization", "regulatory_standards": ["GAMP-5", "21_CFR_Part_11"]}
)
```

**Frequency**: Found in 4/5 analyzed files
**Context**: 21 CFR Part 11 requires complete audit trails for regulatory compliance

### 3. Pydantic Models for Data Validation (90% of data structures)
**Pattern**: Use Pydantic BaseModel for structured data with automatic validation

```python
from pydantic import BaseModel, Field

class GAMPCategorizationResult(BaseModel):
    category: int = Field(..., ge=1, le=5, description="GAMP category (1, 3, 4, or 5)")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    reasoning: str = Field(..., min_length=10, description="Categorization reasoning")
    has_ambiguity_signals: bool = Field(default=False)
    ambiguity_details: str | None = Field(default=None)
    requires_human_review: bool = Field(default=False)
    alternative_categories: list[int] | None = Field(default=None)
```

**Frequency**: Found in 3/5 analyzed files
**Context**: Ensures data integrity and automatic validation for pharmaceutical systems

### 4. LangFuse @observe Decorators (85% of workflow functions)
**Pattern**: Decorate workflow functions with @observe for automatic trace capture

```python
from langfuse import observe

@observe(name="gamp5-categorization-agent", as_type="span")
def categorize_with_pydantic_structured_output(
    llm: LLM,
    urs_content: str,
    document_name: str = "Unknown",
    error_handler: CategorizationErrorHandler | None = None
) -> GAMPCategorizationEvent:
    # Function implementation with automatic LangFuse tracing
    pass
```

**Frequency**: Found in 2/5 analyzed files
**Context**: Production-grade observability with EU-compliant cloud platform

### 5. Enum-Based State Management (80% of state variables)
**Pattern**: Use string-based Enums for all state/status values

```python
class ValidationStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    DEVIATIONS_FOUND = "deviations_found"
    APPROVED = "approved"
    REJECTED = "rejected"

# Usage
requirement.validation_status = ValidationStatus.COMPLETED
```

**Frequency**: Found in 4/5 analyzed files
**Context**: Type-safe state management with IDE autocomplete support

### 6. Regex Pattern Compilation (75% of pattern matching)
**Pattern**: Pre-compile regex patterns at module/class level for performance

```python
class PharmaceuticalOutputScanner:
    def _initialize_pharmaceutical_patterns(self) -> None:
        self._pharma_patterns = {
            "clinical_trial_id": re.compile(
                r"\b(?:trial|study)[_\s-]?(?:id|number)[:\s]*([A-Za-z0-9-]{6,20})\b",
                re.IGNORECASE
            ),
            "drug_product_code": re.compile(
                r"\b(?:product|drug)[_\s-]?code[:\s]*([A-Za-z0-9-]{4,15})\b",
                re.IGNORECASE
            ),
        }
```

**Frequency**: Found in 2/5 analyzed files
**Context**: Performance optimization for repeated pattern matching

### 7. Dataclass with to_dict/from_dict Methods (70% of data classes)
**Pattern**: Implement serialization methods for persistence and API responses

```python
class ValidationRequirement:
    def to_dict(self) -> dict[str, Any]:
        return {
            "requirement_id": self.requirement_id,
            "title": self.title,
            "description": self.description,
            "requirement_type": self.requirement_type.value,
            "validation_status": self.validation_status.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ValidationRequirement":
        req = cls(
            requirement_id=data["requirement_id"],
            title=data["title"],
            description=data["description"],
            requirement_type=RequirementType(data["requirement_type"]),
        )
        req.validation_status = ValidationStatus(data.get("validation_status", "not_started"))
        return req
```

**Frequency**: Found in 2/5 analyzed files
**Context**: Enables JSON persistence and API serialization

### 8. UUID-Based Identifiers (65% of entity IDs)
**Pattern**: Use UUID4 for unique identifiers with timestamp correlation

```python
from uuid import uuid4
from datetime import UTC, datetime

# Generate unique IDs
scan_id = uuid4()
agent_id = f"gamp_categorization_{document_name}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
```

**Frequency**: Found in 3/5 analyzed files
**Context**: Ensures globally unique identifiers for distributed systems

### 9. Pathlib for File Operations (60% of file handling)
**Pattern**: Use pathlib.Path instead of os.path for modern file operations

```python
from pathlib import Path

class ValidationFramework:
    def __init__(self, validation_dir: str = "compliance/validation"):
        self.validation_dir = Path(validation_dir)
        self.validation_dir.mkdir(parents=True, exist_ok=True)
        
        self.requirements_file = self.validation_dir / "requirements.json"
        self.test_cases_file = self.validation_dir / "test_cases.json"
```

**Frequency**: Found in 2/5 analyzed files
**Context**: Modern, cross-platform file path handling

### 10. Structured Logging with Context (55% of log statements)
**Pattern**: Include structured context in log messages for debugging

```python
logger.info(
    f"[{scan_id}] Output security scan complete: "
    f"secure={is_secure}, threats={len(all_threats)}, "
    f"confidence={max_confidence:.3f}"
)

logger.error(
    f"[VALIDATION] Test case execution failed: {e}\n"
    f"Test Case: {test_case_id}\n"
    f"Executed By: {executed_by}\n"
    f"Error Type: {type(e).__name__}"
)
```

**Frequency**: Found in 5/5 analyzed files
**Context**: Enables efficient debugging and audit trail analysis

## Internal API Usage Patterns

### 1. LlamaIndex Workflow Integration
```python
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.tools import FunctionTool

# Create function tools with proper descriptions
gamp_analysis_tool = FunctionTool.from_defaults(
    fn=gamp_analysis_tool_with_error_handling,
    name="gamp_analysis_tool",
    description="Analyze URS content to determine GAMP category. Input: URS content string. Returns: dictionary with predicted_category, evidence, and analysis."
)

# Create agent with tools and system prompt
agent = FunctionAgent(
    tools=[gamp_analysis_tool, confidence_tool],
    llm=llm,
    verbose=verbose,
    max_iterations=15,
    system_prompt=system_prompt
)
```

### 2. LangFuse Cloud Observability
```python
from langfuse import observe

# Decorate workflow functions for automatic tracing
@observe(name="gamp5-categorization-agent", as_type="span")
def categorize_with_pydantic_structured_output(llm, urs_content, document_name):
    # LangFuse automatically captures:
    # - Function inputs/outputs
    # - Execution time
    # - Token usage
    # - Error traces
    pass
```

### 3. Pydantic Validation
```python
from pydantic import BaseModel, Field, ValidationError

class GAMPCategorizationResult(BaseModel):
    category: int = Field(..., ge=1, le=5)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    
    def validate_category(self) -> None:
        if self.category not in [1, 3, 4, 5]:
            raise ValueError(f"Invalid GAMP category: {self.category}")

# Usage with error handling
try:
    result = GAMPCategorizationResult(**data)
    result.validate_category()
except ValidationError as e:
    raise RuntimeError(f"Validation failed: {e}")
```

### 4. Async/Await Patterns
```python
async def categorize_with_error_handling(
    agent: FunctionAgent,
    urs_content: str,
    document_name: str = "Unknown",
    max_retries: int = 1
) -> GAMPCategorizationEvent:
    retry_count = 0
    while retry_count <= max_retries:
        try:
            response = await agent.run(user_msg=f"Analyze this URS document: {urs_content}")
            return create_categorization_event(response)
        except Exception as e:
            retry_count += 1
            if retry_count > max_retries:
                raise RuntimeError(f"Failed after {max_retries} retries: {e}")
```

### 5. ChromaDB Integration
```python
from chromadb import PersistentClient

# Initialize ChromaDB client
client = PersistentClient(path="/app/chroma_db")
collection = client.get_or_create_collection(
    name="gamp5_docs",
    metadata={"description": "GAMP-5 regulatory documents"}
)

# Query with filters
results = collection.query(
    query_texts=["GAMP category 5 validation"],
    n_results=10,
    where={"compliance_level": {"$in": ["regulatory", "mandatory"]}}
)
```

## Frequently Used Code Idioms

### 1. Dictionary Comprehension for Serialization
```python
# Convert dict of objects to dict of dicts
data = {
    req_id: req.to_dict()
    for req_id, req in self.requirements.items()
}
```

### 2. List Comprehension with Filtering
```python
# Filter and transform in one line
regulatory_requirements = [
    req for req in self.requirements.values()
    if req.requirement_type == RequirementType.REGULATORY
]
```

### 3. Context Managers for File Operations
```python
# Atomic file writes with error handling
try:
    with open(self.requirements_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
except Exception as e:
    raise RuntimeError(f"Failed to save requirements: {e}") from e
```

### 4. F-String Formatting with Precision
```python
# Consistent numeric formatting
logger.info(f"Confidence: {confidence:.2f}, Coverage: {coverage:.1%}")
```

### 5. Ternary Expressions for Defaults
```python
# Provide defaults without fallback logic
evidence = evidence or {}
comments = comments if comments else None
```

### 6. Type Union with None (Optional)
```python
# Modern Python 3.10+ optional syntax
def process_data(
    data: dict[str, Any],
    context: str | None = None,
    error_handler: ErrorHandler | None = None
) -> Result:
    pass
```

### 7. Datetime with UTC Timezone
```python
from datetime import UTC, datetime

# Always use UTC for timestamps
timestamp = datetime.now(UTC)
iso_timestamp = timestamp.isoformat()
```

### 8. JSON Lines (JSONL) for Audit Logs
```python
# Append-only audit log format
with open(self.audit_log_file, "a", encoding="utf-8") as f:
    json.dump(event, f, separators=(",", ":"))
    f.write("\n")
```

### 9. Pathlib Glob for File Discovery
```python
# Find all trace files recursively
trace_files = []
for search_path in cls.get_trace_search_paths():
    if search_path.exists():
        trace_files.extend(search_path.glob("*.jsonl"))
return sorted(trace_files)
```

### 10. Enum Value Access
```python
# Access enum values consistently
status_value = requirement.validation_status.value  # "completed"
status_enum = ValidationStatus(data.get("status", "not_started"))
```

## Popular Annotations

### 1. Type Hints for Collections
```python
from typing import Any

# Modern Python 3.9+ syntax (no typing.Dict/List)
def process_results(
    results: list[dict[str, Any]],
    filters: dict[str, list[str]]
) -> dict[str, int]:
    pass
```

### 2. Dataclass Decorators
```python
from dataclasses import dataclass

@dataclass
class OutputSecurityScanResult:
    is_secure: bool
    threat_level: SecurityThreatLevel
    confidence_score: float
    detected_threats: list[str]
    scan_id: UUID
    timestamp: datetime
    error_message: str | None = None
```

### 3. LangFuse Observability
```python
from langfuse import observe

@observe(name="workflow-step-name", as_type="span")
def workflow_function(input_data: str) -> Result:
    # Automatic trace capture to LangFuse Cloud
    pass
```

### 4. Pydantic Field Validators
```python
from pydantic import BaseModel, Field

class ValidationModel(BaseModel):
    category: int = Field(..., ge=1, le=5, description="GAMP category")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    reasoning: str = Field(..., min_length=10, description="Reasoning text")
```

### 5. Enum String Inheritance
```python
from enum import Enum

class ValidationStatus(str, Enum):
    """String-based enum for validation status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
```

### 6. Classmethod Constructors
```python
class ValidationRequirement:
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ValidationRequirement":
        """Create requirement from dictionary."""
        return cls(
            requirement_id=data["requirement_id"],
            title=data["title"],
            description=data["description"]
        )
```

### 7. Property Decorators
```python
class ValidationFramework:
    @property
    def is_compliant(self) -> bool:
        """Check if system is regulatory compliant."""
        return self.regulatory_compliance_rate >= 100
```

### 8. Context Manager Protocol
```python
class AuditLogger:
    def __enter__(self):
        self.start_time = datetime.now(UTC)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.log_completion(datetime.now(UTC) - self.start_time)
```

## Testing Patterns

### 1. Pytest Fixtures
```python
import pytest

@pytest.fixture
def validation_framework():
    """Create validation framework for testing."""
    return ValidationFramework(validation_dir="tests/fixtures/validation")

def test_requirement_creation(validation_framework):
    req = validation_framework.requirements["REQ-PART11-001"]
    assert req.requirement_type == RequirementType.REGULATORY
```

### 2. Mock External Dependencies
```python
from unittest.mock import Mock, patch

@patch("src.agents.categorization.agent.LLMConfig.get_secure_llm")
def test_categorization(mock_llm):
    mock_llm.return_value = Mock(complete=Mock(return_value=Mock(text='{"category": 5}')))
    result = categorize_urs_document("test content")
    assert result.gamp_category == GAMPCategory.CATEGORY_5
```

### 3. Parametrized Tests
```python
@pytest.mark.parametrize("category,expected_tests", [
    (3, 10),
    (4, 20),
    (5, 30),
])
def test_test_count_by_category(category, expected_tests):
    result = generate_tests(category)
    assert len(result) == expected_tests
```

## Error Handling Philosophy

### 1. NO FALLBACKS - Explicit Failures
```python
# CORRECT: Explicit error with full context
if not urs_content or not isinstance(urs_content, str):
    raise ValueError(
        f"Invalid URS content: must be non-empty string, got {type(urs_content)}. "
        f"NO FALLBACKS ALLOWED - Human consultation required."
    )

# INCORRECT: Silent fallback
urs_content = urs_content or "default content"  # NEVER DO THIS
```

### 2. Chained Exceptions
```python
try:
    result = process_data(data)
except Exception as e:
    raise RuntimeError(f"Processing failed: {e}") from e
```

### 3. Comprehensive Error Context
```python
except Exception as e:
    logger.error(
        f"Validation failed: {e}\n"
        f"Input: {input_data[:200]}...\n"
        f"Error Type: {type(e).__name__}\n"
        f"Stack Trace: {traceback.format_exc()}"
    )
    raise RuntimeError(f"Validation failed with full diagnostics: {e}") from e
```

## Performance Optimization

### 1. Pre-compile Regex Patterns
```python
# Module-level compilation
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")

# Use in functions
def scan_for_emails(text: str) -> list[str]:
    return EMAIL_PATTERN.findall(text)
```

### 2. Use Generators for Large Datasets
```python
def process_large_file(file_path: Path):
    with open(file_path) as f:
        for line in f:  # Generator, not list
            yield process_line(line)
```

### 3. Batch Operations
```python
# Batch database operations
for i in range(0, len(items), batch_size):
    batch = items[i:i+batch_size]
    process_batch(batch)
```

## Security Best Practices

### 1. Input Validation
```python
def validate_input(data: str) -> None:
    if not data or not isinstance(data, str):
        raise ValueError("Invalid input: must be non-empty string")
    if len(data) > MAX_INPUT_SIZE:
        raise ValueError(f"Input too large: {len(data)} > {MAX_INPUT_SIZE}")
```

### 2. Secrets Detection
```python
# Never log sensitive data
logger.info(f"Processing document: {document_name}")  # OK
logger.debug(f"API Key: {api_key}")  # NEVER DO THIS
```

### 3. Output Sanitization Prohibition
```python
# NO SANITIZATION in pharmaceutical systems
def sanitize_output(output: str) -> str:
    raise RuntimeError(
        "Output sanitization is PROHIBITED in pharmaceutical systems. "
        "ALCOA+ data integrity requires original output preservation."
    )
```

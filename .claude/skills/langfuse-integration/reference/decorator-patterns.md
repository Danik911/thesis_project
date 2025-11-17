# Langfuse Decorator Patterns Reference

**Purpose**: Comprehensive guide to using `@observe` decorators for pharmaceutical test generation workflows.

---

## Table of Contents

1. [Basic Function Decoration](#basic-function-decoration)
2. [Async Function Patterns](#async-function-patterns)
3. [LLM Generation Tracing](#llm-generation-tracing)
4. [Nested Span Creation](#nested-span-creation)
5. [Compliance Attribute Injection](#compliance-attribute-injection)
6. [Error Handling](#error-handling)
7. [LlamaIndex Workflow Integration](#llamaindex-workflow-integration)

---

## Basic Function Decoration

### Pattern 1: Simple Function Tracing

```python
from langfuse import observe

@observe()
def parse_urs_document(file_path: str) -> dict:
    """
    Parse URS document and extract requirements.

    The @observe decorator automatically:
    - Captures function name as span name
    - Records input parameters
    - Records output/return value
    - Measures execution time
    """
    with open(file_path, 'r') as f:
        content = f.read()

    requirements = extract_requirements(content)

    return {
        "file": file_path,
        "requirement_count": len(requirements),
        "requirements": requirements
    }
```

**Trace Structure**:
```
parse_urs_document (span)
├── input: {"file_path": "examples/urs_001.md"}
├── output: {"file": "...", "requirement_count": 15, "requirements": [...]}
└── duration: 142ms
```

### Pattern 2: Custom Span Name

```python
@observe(name="urs-document-parser")
def parse_urs_document(file_path: str) -> dict:
    """Use custom name instead of function name."""
    ...
```

**Best Practice**: Use custom names for:
- More readable dashboard views
- Consistent naming across refactors
- Grouping related operations

---

## Async Function Patterns

### Pattern 3: Async Function Decoration

```python
from langfuse import observe

@observe()
async def generate_oq_tests(requirements: list[str]) -> list[dict]:
    """
    Async functions work identically to sync functions.

    Langfuse handles async contexts automatically.
    """
    tasks = [generate_test(req) for req in requirements]
    tests = await asyncio.gather(*tasks)

    return tests
```

**Critical**: No special async handling needed - `@observe` works transparently.

### Pattern 4: Async Context Manager Pattern

```python
@observe()
async def batch_categorization(urs_files: list[str]) -> list[dict]:
    """Process multiple URS files in parallel."""
    async with aiofiles.open(config_file) as f:
        config = await f.read()

    results = await asyncio.gather(*[
        categorize_single_urs(file) for file in urs_files
    ])

    return results
```

---

## LLM Generation Tracing

### Pattern 5: LLM Call Tracing with Token Metrics

```python
from langfuse import observe, get_current_observation

@observe(name="llm-categorization", as_type="generation")
async def call_llm_for_category(urs_content: str) -> dict:
    """
    Trace LLM calls with token usage and costs.

    as_type="generation" signals this is an LLM call.
    Langfuse automatically tracks tokens if using OpenAI/Anthropic.
    """
    response = await openrouter_client.complete(
        model="deepseek/deepseek-chat",
        prompt=f"Categorize this URS per GAMP-5:\n{urs_content}"
    )

    # For DeepSeek via OpenRouter, manually update token usage
    obs = get_current_observation()
    if obs and hasattr(response, 'usage'):
        obs.update(usage={
            "input": response.usage.prompt_tokens,
            "output": response.usage.completion_tokens,
            "total": response.usage.total_tokens,
            "unit": "TOKENS"
        })

    return parse_category_response(response.text)
```

**Trace Structure**:
```
llm-categorization (generation)
├── model: "deepseek/deepseek-chat"
├── input: "Categorize this URS per GAMP-5:\n..."
├── output: {"category": 5, "confidence": 0.95}
├── usage:
│   ├── input_tokens: 1234
│   ├── output_tokens: 56
│   ├── total_tokens: 1290
│   └── cost: $0.0023 (if configured)
└── duration: 3421ms
```

### Pattern 6: Streaming LLM Responses

```python
@observe(as_type="generation")
async def stream_test_generation(requirements: str):
    """Track streaming LLM responses."""
    obs = get_current_observation()

    full_response = ""
    async for chunk in llm.astream(requirements):
        full_response += chunk.text

        # Optionally update observation with intermediate state
        if obs:
            obs.update(metadata={"chunks_received": len(full_response)})

    # Final update with complete response
    if obs:
        obs.update(output={"generated_tests": full_response})

    return parse_tests(full_response)
```

---

## Nested Span Creation

### Pattern 7: Automatic Nested Spans

```python
@observe(name="test-suite-generation")
async def generate_test_suite(urs_file: str) -> dict:
    """
    Parent function creates root span.
    All called functions with @observe create child spans automatically.
    """
    # Child span 1
    category_result = await categorize_urs(urs_file)  # Has @observe

    # Child span 2
    if category_result["category"] == 5:
        requirements = await extract_requirements(urs_file)  # Has @observe

        # Child span 3
        tests = await generate_oq_tests(requirements)  # Has @observe
    else:
        tests = []

    return {"category": category_result, "tests": tests}


@observe()
async def categorize_urs(urs_file: str) -> dict:
    """Automatically becomes child span of generate_test_suite."""
    ...


@observe()
async def extract_requirements(urs_file: str) -> list:
    """Automatically becomes child span of generate_test_suite."""
    ...


@observe()
async def generate_oq_tests(requirements: list) -> list:
    """Automatically becomes child span of generate_test_suite."""
    ...
```

**Trace Structure**:
```
test-suite-generation (root span)
├── categorize_urs (child span)
│   └── duration: 3.2s
├── extract_requirements (child span)
│   └── duration: 0.8s
└── generate_oq_tests (child span)
    └── duration: 12.4s
```

**Best Practice**: Use nested decorators liberally - Langfuse handles context propagation automatically.

### Pattern 8: Manual Nested Span Control

```python
from langfuse import observe, get_client

@observe()
def complex_workflow():
    """Manual control for non-decorated functions."""
    langfuse = get_client()

    # Automatic child span (decorated)
    result1 = decorated_function()

    # Manual child span for legacy code
    with langfuse.start_as_current_span(
        name="legacy-processing",
        as_type="span"
    ) as span:
        span.update(input={"mode": "legacy"})
        result2 = legacy_function_without_decorator()
        span.update(output=result2)

    return result1, result2
```

---

## Compliance Attribute Injection

### Pattern 9: GAMP-5 Category Metadata

```python
from langfuse import observe, get_current_observation

@observe(name="gamp5-categorization")
async def categorize_for_gamp5(urs_content: str) -> dict:
    """Inject GAMP-5 compliance metadata."""
    # Existing categorization logic
    category = await classify_software(urs_content)
    confidence = calculate_confidence(category)

    # Inject compliance metadata
    obs = get_current_observation()
    if obs:
        obs.update(metadata={
            "compliance.gamp5.applicable": True,
            "compliance.gamp5.category": category,  # 1-5
            "compliance.gamp5.confidence": confidence,
            "compliance.standard": "GAMP-5",
            "compliance.timestamp": datetime.now(timezone.utc).isoformat()
        })

    return {
        "category": category,
        "confidence": confidence,
        "rationale": get_rationale(category)
    }
```

### Pattern 10: ALCOA+ Attribute Propagation

```python
@observe()
async def generate_compliant_test_suite(
    user_id: str,
    urs_file: str,
    job_id: str
) -> dict:
    """
    Set ALCOA+ attributes at trace root.
    All child spans inherit automatically.
    """
    from langfuse import get_current_trace

    # Set trace-level attributes
    trace = get_current_trace()
    if trace:
        trace.update(
            user_id=user_id,  # Attributable
            session_id=job_id,  # Traceable
            tags=["pharmaceutical", "gamp5", "alcoa-plus"],
            metadata={
                "compliance.alcoa_plus.attributable": True,
                "compliance.alcoa_plus.contemporaneous": True,
                "compliance.alcoa_plus.original": True,
                "user.clerk_id": user_id,
                "job.id": job_id,
                "job.timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

    # All child operations inherit these attributes
    result = await unified_workflow.run(urs_file)

    return result
```

### Pattern 11: Multi-Tenant Organization Attribution

```python
@observe()
async def org_attributed_workflow(
    org_id: str,
    user_id: str,
    urs_file: str
) -> dict:
    """Track pharmaceutical organization for audit purposes."""
    trace = get_current_trace()
    if trace:
        trace.update(
            user_id=user_id,
            tags=[f"org:{org_id}", "gamp5", "pharmaceutical"],
            metadata={
                "organization.id": org_id,
                "organization.name": get_org_name(org_id),
                "organization.country": "EU",
                "compliance.data_residency": "EU",
                "compliance.gdpr_applicable": True
            }
        )

    # Organization context propagates to all child spans
    result = await process_urs(urs_file)

    return result
```

---

## Error Handling

### Pattern 12: Explicit Error Capture (NO FALLBACKS)

```python
@observe()
async def parse_urs_with_validation(urs_file: str) -> dict:
    """
    CRITICAL: Errors must propagate - no fallback logic.

    Langfuse automatically captures exceptions.
    """
    try:
        content = await read_file(urs_file)

        # Validation - must fail if invalid
        if not validate_urs_schema(content):
            raise ValueError(f"Invalid URS schema in {urs_file}")

        requirements = extract_requirements(content)

        # Another validation - no fallbacks
        if len(requirements) == 0:
            raise ValueError(f"No requirements found in {urs_file}")

        return {
            "file": urs_file,
            "requirements": requirements,
            "valid": True
        }

    except FileNotFoundError as e:
        # Log error details in observation
        obs = get_current_observation()
        if obs:
            obs.update(metadata={
                "error.type": "FileNotFoundError",
                "error.file": urs_file,
                "error.message": str(e)
            })

        # RE-RAISE - do not mask errors
        raise

    except ValueError as e:
        obs = get_current_observation()
        if obs:
            obs.update(metadata={
                "error.type": "ValidationError",
                "error.message": str(e)
            })

        # RE-RAISE - validation failures must propagate
        raise
```

**Trace Structure on Error**:
```
parse_urs_with_validation (span)
├── input: {"urs_file": "invalid.md"}
├── status: ERROR
├── error:
│   ├── type: "ValueError"
│   ├── message: "Invalid URS schema in invalid.md"
│   └── stack_trace: "..."
└── metadata:
    ├── error.type: "ValidationError"
    └── error.message: "Invalid URS schema in invalid.md"
```

**Best Practice**:
- ✅ Capture error metadata for debugging
- ✅ Always re-raise exceptions
- ❌ NEVER return default values on errors
- ❌ NEVER mask errors with fallback logic

### Pattern 13: Retry Logic with Trace Visibility

```python
@observe()
async def call_llm_with_retry(prompt: str, max_retries: int = 3) -> str:
    """
    Retry logic with explicit trace visibility.
    Each retry creates metadata - no hidden failures.
    """
    obs = get_current_observation()

    for attempt in range(max_retries):
        try:
            response = await llm.acomplete(prompt)

            # Log successful attempt
            if obs:
                obs.update(metadata={
                    "retry.attempt": attempt + 1,
                    "retry.success": True
                })

            return response.text

        except RateLimitError as e:
            # Log retry metadata
            if obs:
                obs.update(metadata={
                    f"retry.attempt_{attempt + 1}.error": "RateLimitError",
                    f"retry.attempt_{attempt + 1}.message": str(e)
                })

            if attempt == max_retries - 1:
                # Final attempt failed - re-raise
                raise

            # Exponential backoff
            await asyncio.sleep(2 ** attempt)

    # Should never reach here
    raise RuntimeError("Retry logic failed unexpectedly")
```

---

## LlamaIndex Workflow Integration

### Pattern 14: LlamaIndex Callback Handler

```python
# main/src/monitoring/langfuse_config.py
from langfuse.llama_index import LlamaIndexCallbackHandler
import os

def get_langfuse_callback_handler() -> LlamaIndexCallbackHandler:
    """
    Create Langfuse callback handler for LlamaIndex workflows.

    This handler automatically instruments:
    - Workflow events (StartEvent, StopEvent, custom events)
    - LLM calls
    - Retrieval operations
    - Tool calls
    """
    return LlamaIndexCallbackHandler(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),

        # Optional: Configure behavior
        flush_interval=5,  # Flush every 5 seconds
        flush_at=50,       # Or after 50 events
    )
```

### Pattern 15: Workflow Entry Point Decoration

```python
# main/src/core/unified_workflow.py
from llama_index.core.workflow import Workflow, StartEvent, StopEvent, Context
from langfuse import observe

class UnifiedWorkflow(Workflow):
    """Main pharmaceutical test generation workflow."""

    @observe(name="unified-workflow-run", as_type="span")
    async def run(
        self,
        ctx: Context,
        ev: StartEvent
    ) -> StopEvent:
        """
        Root workflow span.

        The @observe decorator creates a root span.
        LlamaIndex callback handler creates child spans for events.
        """
        # Set trace-level attributes
        from langfuse import get_current_trace
        trace = get_current_trace()
        if trace:
            trace.update(
                user_id=ev.user_id,
                session_id=ev.job_id,
                tags=["pharmaceutical", "gamp5"],
                metadata={
                    "workflow.version": "1.0.0",
                    "workflow.type": "unified",
                    "compliance.gamp5.enabled": True
                }
            )

        # Workflow executes - callback handler instruments automatically
        result = await super().run(ctx, ev)

        return result
```

### Pattern 16: Registering Callback with Workflow

```python
# main/main.py
from main.src.core.unified_workflow import UnifiedWorkflow
from main.src.monitoring.langfuse_config import get_langfuse_callback_handler

async def main():
    """Initialize workflow with Langfuse instrumentation."""

    # Create callback handler
    langfuse_handler = get_langfuse_callback_handler()

    # Register with workflow
    workflow = UnifiedWorkflow(
        callbacks=[langfuse_handler],
        timeout=600,
        verbose=True
    )

    # Run workflow - automatically traced
    result = await workflow.run(
        user_id="user_35KgiAcvIC0tdtFvJUN1vDkrNYc",
        urs_file="examples/urs_001.md",
        job_id="job_12345"
    )

    # CRITICAL: Flush before exit
    langfuse_handler.flush()

    return result
```

**Trace Structure**:
```
unified-workflow-run (root span from @observe)
├── StartEvent (from LlamaIndex callback)
│   └── input: {"user_id": "...", "urs_file": "..."}
├── categorization-event (from callback)
│   ├── llm-call (from callback)
│   │   ├── model: "deepseek/deepseek-chat"
│   │   └── tokens: {...}
│   └── output: {"category": 5}
├── requirement-extraction-event (from callback)
│   └── ...
└── StopEvent (from callback)
    └── output: {"tests": [...]}
```

**Best Practice**: Combine `@observe` decorators with LlamaIndex callback handler for complete visibility:
- Decorators trace custom functions
- Callback handler traces LlamaIndex internals
- Both share same trace context automatically

---

## Configuration Templates

### Complete Langfuse Configuration Module

```python
# main/src/monitoring/langfuse_config.py
from langfuse import Langfuse
from langfuse.llama_index import LlamaIndexCallbackHandler
import os
from typing import Optional

# Singleton instance
_langfuse_client: Optional[Langfuse] = None


def setup_langfuse() -> Langfuse:
    """
    Initialize Langfuse client for EU cloud.

    Environment variables required:
    - LANGFUSE_PUBLIC_KEY
    - LANGFUSE_SECRET_KEY
    - LANGFUSE_HOST (optional, defaults to EU cloud)
    """
    global _langfuse_client

    if _langfuse_client is not None:
        return _langfuse_client

    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")

    if not public_key or not secret_key:
        raise ValueError(
            "Langfuse API keys not configured. "
            "Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY environment variables."
        )

    _langfuse_client = Langfuse(
        public_key=public_key,
        secret_key=secret_key,
        host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),

        # Performance tuning
        flush_interval=5,
        flush_at=50,

        # Enable debug logging (disable in production)
        debug=os.getenv("LANGFUSE_DEBUG", "false").lower() == "true"
    )

    return _langfuse_client


def get_langfuse_client() -> Langfuse:
    """Get existing client or create new one."""
    if _langfuse_client is None:
        return setup_langfuse()
    return _langfuse_client


def get_langfuse_callback_handler() -> LlamaIndexCallbackHandler:
    """Create callback handler for LlamaIndex workflows."""
    return LlamaIndexCallbackHandler(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        flush_interval=5,
        flush_at=50
    )


def add_compliance_attributes(
    category: int,
    user_id: str,
    job_id: str
) -> dict:
    """
    Generate standard GAMP-5 + ALCOA+ compliance attributes.

    Use with trace.update(metadata=add_compliance_attributes(...))
    """
    from datetime import datetime, timezone

    return {
        # GAMP-5
        "compliance.gamp5.applicable": True,
        "compliance.gamp5.category": category,
        "compliance.standard": "GAMP-5",

        # ALCOA+
        "compliance.alcoa_plus.attributable": True,
        "compliance.alcoa_plus.contemporaneous": True,
        "compliance.alcoa_plus.original": True,
        "compliance.alcoa_plus.accurate": True,

        # User attribution
        "user.clerk_id": user_id,
        "job.id": job_id,

        # Timestamps
        "compliance.timestamp": datetime.now(timezone.utc).isoformat(),

        # Regulatory
        "compliance.21cfr_part11.applicable": True,
        "compliance.data_residency": "EU",
        "compliance.gdpr_compliant": True
    }


def flush_langfuse():
    """
    Flush all pending events to Langfuse Cloud.

    CRITICAL: Call before application shutdown.
    """
    if _langfuse_client:
        _langfuse_client.flush()
```

---

## Decorator Pattern Decision Tree

```
Does the function make LLM calls?
├─ Yes → Use @observe(as_type="generation")
│        + Manually track token usage for DeepSeek
└─ No  → Use @observe() or @observe(name="custom-name")

Does the function need GAMP-5 metadata?
├─ Yes → Call get_current_observation() inside function
│        + Update metadata with compliance attributes
└─ No  → Basic @observe() sufficient

Is this the workflow entry point?
├─ Yes → Call get_current_trace() to set user_id, session_id
│        + Add tags for filtering
└─ No  → Attributes propagate from parent automatically

Is this a complex multi-step function?
├─ Yes → Break into smaller functions with separate @observe
│        + Better trace granularity
└─ No  → Single @observe sufficient

Does the function have retry logic?
├─ Yes → Log retry attempts in metadata
│        + Re-raise final failure
└─ No  → Standard error handling with re-raise
```

---

## Performance Considerations

### Decorator Overhead

- **Typical overhead**: 0.1-0.5ms per decorated function
- **Network latency**: 10-50ms per batch flush (amortized)
- **Recommendation**: Decorate liberally - overhead is negligible compared to LLM calls (3-10 seconds)

### Flush Strategy

```python
# Option 1: Manual flush at end (synchronous)
@observe()
def main():
    result = workflow.run()

    from langfuse import get_client
    client = get_client()
    client.flush()  # Blocks until all events sent

    return result


# Option 2: Async flush (non-blocking)
@observe()
async def main():
    result = await workflow.run()

    from langfuse import get_client
    client = get_client()
    client.flush_async()  # Returns immediately, sends in background

    return result


# Option 3: Automatic flush (context manager)
with get_client() as langfuse:
    result = workflow.run()
    # Automatic flush on context exit
```

---

## Troubleshooting Decorator Issues

### Issue: Decorators Not Creating Spans

**Symptom**: Functions run but no spans in dashboard.

**Diagnosis**:
1. Check if Langfuse client initialized
2. Check if API keys set
3. Check if flush() called before exit

**Solution**:
```python
# Add debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

from langfuse import observe, get_client

@observe()
def test_function():
    return "test"

test_function()

client = get_client()
client.flush()  # CRITICAL
```

### Issue: Nested Spans Not Appearing

**Symptom**: Only root span visible, child spans missing.

**Diagnosis**: Context propagation failure.

**Solution**: Verify all child functions have `@observe`:
```python
@observe()  # Parent
def parent():
    child()  # Must also have @observe

@observe()  # Child - DO NOT FORGET
def child():
    pass
```

### Issue: Metadata Not Appearing

**Symptom**: Spans appear but metadata missing.

**Solution**: Ensure `get_current_observation()` called inside decorated function:
```python
@observe()
def my_function():
    obs = get_current_observation()  # Must be inside function
    if obs:  # Check not None
        obs.update(metadata={"key": "value"})
```

---

**Reference Version**: 1.0.0
**Last Updated**: 2025-01-17
**Compatibility**: Langfuse SDK 3.0+, Python 3.12+
**EU Data Residency**: cloud.langfuse.com

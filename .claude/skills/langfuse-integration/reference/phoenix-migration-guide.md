# Phoenix → Langfuse Migration Guide

**Purpose**: Step-by-step guide for replacing Phoenix observability with Langfuse Cloud (EU).

---

## Migration Strategy: Complete Replacement

**Approach**: Remove Phoenix entirely, replace with Langfuse.

**Rationale**:
- Production requires persistent storage (Phoenix is ephemeral)
- Langfuse Cloud provides analytics, dashboards, audit trails
- EU data residency compliance
- Cost-effective cloud solution
- No need for dual observability complexity

**Migration Timeline**: 1-2 hours for typical pharmaceutical test generation codebase.

---

## API Equivalence Table

| Phoenix | Langfuse | Notes |
|---------|----------|-------|
| `from phoenix.otel import register` | `from langfuse import Langfuse` | Setup |
| `tracer_provider = register()` | `client = Langfuse(...)` | Client init |
| `from opentelemetry import trace` | `from langfuse import observe` | Instrumentation |
| `@tracer.start_as_current_span("name")` | `@observe(name="name")` | Decorator |
| `span.set_attribute("key", value)` | `obs.update(metadata={"key": value})` | Attributes |
| `span.add_event("event")` | `obs.event(name="event")` | Events |
| OpenTelemetry LlamaIndex callback | `LlamaIndexCallbackHandler` | Workflow tracing |
| `phoenix serve` (local UI) | `cloud.langfuse.com` (cloud UI) | Dashboard |
| No persistent storage | PostgreSQL-backed cloud | Data retention |
| Local-only traces | Multi-user cloud access | Collaboration |

---

## Step-by-Step Migration

### Step 1: Identify Phoenix Code

Search for all Phoenix-related code:

```bash
# Find Phoenix imports
grep -r "from phoenix" main/src/ --include="*.py"
grep -r "import phoenix" main/src/ --include="*.py"

# Find Phoenix configuration
find main/src/ -name "*phoenix*" -type f

# Find OpenTelemetry usage (may be Phoenix-specific)
grep -r "from opentelemetry" main/src/ --include="*.py"
grep -r "tracer" main/src/ --include="*.py"
```

**Expected files** (from existing thesis project):
- `main/src/monitoring/phoenix_config.py` - Configuration module
- `main/src/core/unified_workflow.py` - Workflow with Phoenix callbacks
- `main/main.py` - Phoenix server startup (if applicable)

### Step 2: Create Langfuse Configuration

**Create**: `main/src/monitoring/langfuse_config.py`

```python
from langfuse import Langfuse
from langfuse.llama_index import LlamaIndexCallbackHandler
import os
from typing import Optional

_langfuse_client: Optional[Langfuse] = None


def setup_langfuse() -> Langfuse:
    """Initialize Langfuse client for EU cloud."""
    global _langfuse_client

    if _langfuse_client is not None:
        return _langfuse_client

    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")

    if not public_key or not secret_key:
        raise ValueError(
            "Langfuse API keys not configured. "
            "Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY."
        )

    _langfuse_client = Langfuse(
        public_key=public_key,
        secret_key=secret_key,
        host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        flush_interval=5,
        flush_at=50
    )

    return _langfuse_client


def get_langfuse_client() -> Langfuse:
    """Get singleton client."""
    if _langfuse_client is None:
        return setup_langfuse()
    return _langfuse_client


def get_langfuse_callback_handler() -> LlamaIndexCallbackHandler:
    """Create LlamaIndex callback handler."""
    return LlamaIndexCallbackHandler(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    )
```

### Step 3: Replace Workflow Callbacks

**Before (Phoenix)**:
```python
# main/src/core/unified_workflow.py
from phoenix.otel import register
from opentelemetry import trace

# Setup Phoenix
tracer_provider = register(
    project_name="pharmaceutical_test_generation",
    endpoint="http://localhost:6006"
)

# Use with workflow
workflow = UnifiedWorkflow(timeout=600)
```

**After (Langfuse)**:
```python
# main/src/core/unified_workflow.py
from langfuse import observe
from langfuse.llama_index import LlamaIndexCallbackHandler
import os

# Get callback handler
langfuse_handler = LlamaIndexCallbackHandler(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
)

# Use with workflow
workflow = UnifiedWorkflow(
    callbacks=[langfuse_handler],
    timeout=600
)
```

### Step 4: Replace Manual Spans

**Before (Phoenix/OpenTelemetry)**:
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

def categorize_urs(urs_content: str) -> dict:
    with tracer.start_as_current_span("gamp5-categorization") as span:
        span.set_attribute("compliance.gamp5", True)

        result = classify(urs_content)

        span.set_attribute("category", result["category"])

        return result
```

**After (Langfuse)**:
```python
from langfuse import observe, get_current_observation

@observe(name="gamp5-categorization")
def categorize_urs(urs_content: str) -> dict:
    obs = get_current_observation()
    if obs:
        obs.update(metadata={"compliance.gamp5": True})

    result = classify(urs_content)

    if obs:
        obs.update(metadata={"category": result["category"]})

    return result
```

**Key differences**:
- Decorator instead of context manager (cleaner code)
- `metadata={}` instead of `set_attribute()`
- `get_current_observation()` instead of span parameter

### Step 5: Remove Phoenix Configuration File

```bash
# Backup (optional)
cp main/src/monitoring/phoenix_config.py main/src/monitoring/phoenix_config.py.bak

# Remove
rm main/src/monitoring/phoenix_config.py

# Update __init__.py
# Edit main/src/monitoring/__init__.py
```

**Before**:
```python
# main/src/monitoring/__init__.py
from .phoenix_config import setup_phoenix, PhoenixManager

__all__ = ["setup_phoenix", "PhoenixManager"]
```

**After**:
```python
# main/src/monitoring/__init__.py
from .langfuse_config import (
    setup_langfuse,
    get_langfuse_client,
    get_langfuse_callback_handler
)

__all__ = [
    "setup_langfuse",
    "get_langfuse_client",
    "get_langfuse_callback_handler"
]
```

### Step 6: Update Dependencies

```bash
# Remove Phoenix
uv remove arize-phoenix arize-phoenix-otel

# Add Langfuse
uv add langfuse llama-index-instrumentation-langfuse

# Sync environment
uv sync
```

### Step 7: Update Environment Variables

**Before (.env)**:
```bash
# Phoenix (local)
PHOENIX_PROJECT_NAME=pharmaceutical_test_generation
PHOENIX_ENDPOINT=http://localhost:6006
```

**After (.env)**:
```bash
# Langfuse Cloud (EU)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

**Update .env.example**:
```bash
# Add to .env.example
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key
LANGFUSE_HOST=https://cloud.langfuse.com
```

### Step 8: Update Main Entry Point

**Before**:
```python
# main/main.py
from phoenix.otel import register

def main():
    # Setup Phoenix
    tracer_provider = register()

    # Run workflow
    result = workflow.run()

    return result
```

**After**:
```python
# main/main.py
from main.src.monitoring.langfuse_config import (
    setup_langfuse,
    get_langfuse_callback_handler
)

def main():
    # Setup Langfuse
    langfuse = setup_langfuse()
    handler = get_langfuse_callback_handler()

    # Run workflow with handler
    workflow = UnifiedWorkflow(callbacks=[handler])
    result = workflow.run()

    # CRITICAL: Flush before exit
    langfuse.flush()

    return result
```

### Step 9: Remove Phoenix Server Commands

Check for Phoenix server startup:

```bash
# Search for phoenix serve commands
grep -r "phoenix serve" . --include="*.sh" --include="*.py" --include="*.md"
```

**Remove**:
- Shell scripts starting Phoenix server
- Documentation references to `phoenix serve`
- README instructions for Phoenix UI access

**Replace with**:
- Langfuse Cloud dashboard URL
- Instructions for accessing cloud.langfuse.com
- API key setup instructions

### Step 10: Validate Migration

Run validation checks:

```bash
# 1. Check imports
python -c "from main.src.monitoring import setup_langfuse; print('✅ Import successful')"

# 2. Check API keys
python -c "import os; print('✅ Keys set' if os.getenv('LANGFUSE_PUBLIC_KEY') else '❌ Keys missing')"

# 3. Run tests
pytest main/tests/ -v

# 4. Check for Phoenix references
grep -r "phoenix" main/src/ --include="*.py"
# Should return 0 results

# 5. Run end-to-end workflow
uv run python main/main.py
```

---

## Span Structure Comparison

### Phoenix Span Structure

```
Root Trace
├── unified-workflow-run (manual span)
│   ├── gamp5-categorization (manual span)
│   │   └── llm-call (OpenTelemetry auto-instrumentation)
│   ├── requirement-extraction (manual span)
│   └── test-generation (manual span)
│       └── llm-call (OpenTelemetry auto-instrumentation)
```

**Characteristics**:
- Manual span creation with context managers
- OpenTelemetry auto-instrumentation for LLM calls
- Local-only storage
- Ephemeral (lost on restart)

### Langfuse Span Structure

```
Root Trace
├── unified-workflow-run (@observe decorator)
│   ├── gamp5-categorization (@observe decorator)
│   │   └── llm-call (LlamaIndex callback handler)
│   ├── requirement-extraction (@observe decorator)
│   └── test-generation (@observe decorator)
│       └── llm-call (LlamaIndex callback handler)
```

**Characteristics**:
- Decorator-based instrumentation (cleaner code)
- LlamaIndex callback handler for workflow events
- Cloud storage with persistence
- Analytics, dashboards, sharing

**Trace parity**: Should maintain ~131 spans per workflow.

---

## Common Migration Issues

### Issue 1: Import Errors After Removal

**Symptom**:
```python
ModuleNotFoundError: No module named 'phoenix'
```

**Cause**: Missed Phoenix import in file.

**Solution**:
```bash
# Find all Phoenix references
grep -r "phoenix" main/ --include="*.py"

# Replace with Langfuse equivalents
```

### Issue 2: Missing Traces in Dashboard

**Symptom**: Workflow runs but no traces in Langfuse Cloud.

**Cause**: Missing `flush()` call.

**Solution**:
```python
from langfuse import get_client

def main():
    result = workflow.run()

    # CRITICAL
    client = get_client()
    client.flush()

    return result
```

### Issue 3: Span Count Mismatch

**Symptom**: Langfuse shows fewer spans than Phoenix.

**Cause**: Missing `@observe` decorators on functions.

**Solution**:
```bash
# Compare Phoenix baseline
# Phoenix: 131 spans/workflow (baseline)

# Count Langfuse decorators
grep -r "@observe" main/src/ --include="*.py" | wc -l

# Should match number of instrumented functions
```

### Issue 4: Compliance Attributes Missing

**Symptom**: Traces appear but GAMP-5 metadata absent.

**Cause**: Metadata not propagated correctly.

**Solution**:
```python
from langfuse import get_current_trace

# Set at trace root
trace = get_current_trace()
if trace:
    trace.update(metadata={
        "compliance.gamp5.applicable": True,
        "compliance.gamp5.category": 5
    })
```

---

## Feature Comparison

| Feature | Phoenix | Langfuse | Winner |
|---------|---------|----------|--------|
| **Setup complexity** | Low (local) | Medium (API keys) | Phoenix |
| **Data persistence** | None (ephemeral) | PostgreSQL-backed | **Langfuse** |
| **Multi-user access** | ❌ | ✅ | **Langfuse** |
| **Analytics** | Basic | Advanced (dashboards, metrics) | **Langfuse** |
| **Cost tracking** | ❌ | ✅ (token usage, $) | **Langfuse** |
| **Data residency** | Local only | EU/US/Custom | **Langfuse** |
| **API access** | Limited | Full REST API | **Langfuse** |
| **Audit trails** | ❌ | ✅ (ALCOA+ compliant) | **Langfuse** |
| **Latency** | ~0ms (local) | ~10-50ms (cloud) | Phoenix |
| **Production-ready** | ❌ | ✅ | **Langfuse** |
| **Compliance** | ❌ | ✅ (GAMP-5, GDPR) | **Langfuse** |

**Verdict**: Langfuse wins for production pharmaceutical applications requiring compliance, persistence, and audit trails.

---

## Rollback Procedure (If Needed)

If migration fails and rollback required:

### Step 1: Restore Phoenix Configuration

```bash
# Restore backup
cp main/src/monitoring/phoenix_config.py.bak main/src/monitoring/phoenix_config.py

# Reinstall Phoenix
uv add arize-phoenix arize-phoenix-otel
```

### Step 2: Restore Imports

```python
# main/src/monitoring/__init__.py
from .phoenix_config import setup_phoenix, PhoenixManager

__all__ = ["setup_phoenix", "PhoenixManager"]
```

### Step 3: Remove Langfuse Decorators

```bash
# Find all @observe decorators
grep -r "@observe" main/src/ --include="*.py"

# Replace with Phoenix equivalents (manual)
```

### Step 4: Restore Workflow Callbacks

```python
# main/src/core/unified_workflow.py
from phoenix.otel import register

tracer_provider = register()
workflow = UnifiedWorkflow(timeout=600)
```

### Step 5: Restore Environment

```bash
# Remove Langfuse keys
unset LANGFUSE_PUBLIC_KEY
unset LANGFUSE_SECRET_KEY

# Add Phoenix config
export PHOENIX_PROJECT_NAME=pharmaceutical_test_generation
```

**Rollback time**: ~30 minutes.

---

## Post-Migration Validation Checklist

After migration, verify:

- [ ] All Phoenix imports removed
- [ ] Phoenix packages uninstalled
- [ ] Langfuse SDK installed
- [ ] API keys configured
- [ ] `@observe` decorators added to all critical functions
- [ ] LlamaIndex callback handler registered
- [ ] End-to-end workflow runs successfully
- [ ] Traces visible in Langfuse Cloud dashboard
- [ ] Span count matches Phoenix baseline (±10%)
- [ ] User ID propagated correctly
- [ ] Session ID propagated correctly
- [ ] GAMP-5 compliance attributes present
- [ ] ALCOA+ attributes present
- [ ] Tags include "pharmaceutical", "gamp5"
- [ ] Tests pass (pytest)
- [ ] Type checking passes (mypy)
- [ ] Linting passes (ruff)
- [ ] Documentation updated
- [ ] Changes committed to Git

---

## Timeline and Effort

**Estimated migration time**: 1-2 hours

**Breakdown**:
- Assessment: 10 minutes
- Configuration setup: 15 minutes
- Code changes: 30-60 minutes
- Testing and validation: 20-30 minutes
- Documentation: 10 minutes

**Complexity**: Medium

**Risk**: Low (rollback procedure available)

**Impact**: High (enables production deployment)

---

**Guide Version**: 1.0.0
**Last Updated**: 2025-01-17
**Compatibility**: Phoenix 4.x → Langfuse 3.0+
**Target Platform**: Langfuse Cloud (EU)

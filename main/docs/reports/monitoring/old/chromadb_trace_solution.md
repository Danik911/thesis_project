# ChromaDB Trace Export Solution

## Problem Statement
ChromaDB traces were visible in the Phoenix UI but not being exported in the JSONL files downloaded from Phoenix. This severely limited observability for vector database operations in our pharmaceutical multi-agent system.

## Root Cause Analysis
After investigation, we discovered:
1. Phoenix UI displays traces from in-memory/temporary storage
2. Only certain span types (mainly LLM/Chain spans) are persisted to the SQLite database
3. Instrumentation spans like ChromaDB operations are not persisted for long-term storage
4. The "OpenAI Fine-Tuning JSONL" export format only includes persisted spans from the database

## Solution Implemented

### 1. Custom Span Exporter
Created `src/monitoring/custom_span_exporter.py` that implements a custom OpenTelemetry SpanProcessor:

```python
class LocalFileSpanExporter(SpanProcessor):
    """
    Custom span processor that exports ALL spans to local JSONL files.
    """
```

Key features:
- Captures ALL spans including ChromaDB operations
- Saves to `logs/traces/all_spans_*.jsonl`
- Separate file for ChromaDB spans: `chromadb_spans_*.jsonl`
- Preserves full span context including attributes, events, and timing

### 2. Phoenix Configuration Update
Modified `src/monitoring/phoenix_config.py` to automatically add the custom exporter:

```python
# Add local file exporter to capture ALL spans including ChromaDB
if add_local_span_exporter:
    add_local_span_exporter(self.tracer_provider)
```

### 3. Monitor Agent Update
Updated `.claude/agents/monitor-agent.md` to:
- Look for custom span export files in `logs/traces/`
- Parse the new span format with ChromaDB operations
- Provide comprehensive analysis of vector database usage

## Verification
Created `scripts/test_custom_span_export.py` that confirms:
- ✅ ChromaDB operations are captured (add, query, delete)
- ✅ Performance metrics are recorded (duration, result counts)
- ✅ Compliance attributes are preserved
- ✅ Full trace context is maintained

## Benefits
1. **Complete Observability**: All operations including vector database access are now traceable
2. **Performance Analysis**: Can analyze ChromaDB query performance and optimization opportunities
3. **Compliance**: GAMP-5 compliance attributes on vector operations are captured
4. **Debugging**: Full context for troubleshooting retrieval issues

## Usage
The custom span exporter runs automatically when Phoenix is initialized. Trace files are saved to:
- `main/logs/traces/all_spans_YYYYMMDD_HHMMSS.jsonl` - All spans
- `main/logs/traces/chromadb_spans_YYYYMMDD_HHMMSS.jsonl` - ChromaDB-specific spans

The monitor-agent can now analyze these files for comprehensive workflow observability.
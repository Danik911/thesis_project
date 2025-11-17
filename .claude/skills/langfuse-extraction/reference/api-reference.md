# Langfuse API Reference

## Authentication

```python
from langfuse import Langfuse

langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
)
```

## Trace Operations

### List Traces
```python
traces = langfuse.api.trace.list(
    from_timestamp="2025-01-01T00:00:00Z",  # Optional
    to_timestamp="2025-01-31T23:59:59Z",    # Optional
    user_id="user_xxx",                      # Optional
    session_id="job_yyy",                    # Optional
    tags=["pharmaceutical", "gamp5"],        # Optional
    limit=100                                 # Default: 50, Max: 1000
)

for trace in traces.data:
    print(f"{trace.id}: {trace.timestamp}")
```

### Get Single Trace
```python
trace = langfuse.api.trace.get("trace_id_here")

# Access properties
print(f"Duration: {trace.duration}ms")
print(f"User: {trace.user_id}")
print(f"Cost: ${trace.total_cost}")

# Iterate observations
for obs in trace.observations:
    print(f"  {obs.name}: {obs.latency}ms")
```

## Observation Properties

```python
obs.id              # Unique observation ID
obs.type            # "SPAN", "GENERATION", "EVENT"
obs.name            # Human-readable name
obs.input           # Input data (dict/string)
obs.output          # Output data (dict/string)
obs.latency         # Duration in milliseconds
obs.usage.input     # Input tokens
obs.usage.output    # Output tokens
obs.calculated_total_cost  # Cost in USD
obs.metadata        # Custom metadata dict
obs.status_message  # Error message if failed
```

## Rate Limits

- Free tier: 100 requests/minute
- Pro tier: 1000 requests/minute
- Implement exponential backoff for 429 errors

## Common Queries

**Last 24 hours of pharmaceutical traces:**
```python
from datetime import datetime, timedelta
traces = langfuse.api.trace.list(
    from_timestamp=(datetime.now() - timedelta(hours=24)).isoformat(),
    tags=["pharmaceutical", "gamp5"]
)
```

**All traces for user session:**
```python
traces = langfuse.api.trace.list(
    user_id="user_35KgiAcvIC0tdtFvJUN1vDkrNYc",
    session_id="job_12345"
)
```

**High-cost traces:**
```python
all_traces = langfuse.api.trace.list(limit=1000)
high_cost = [t for t in all_traces.data if (t.total_cost or 0) > 0.10]
```

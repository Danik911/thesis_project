# ISSUE-003: Langfuse trace_id Always "unknown"

## Date
2025-12-06 (Updated: 2025-12-07)

## Symptom
After job completion, the Langfuse trace button showed "Langfuse trace unavailable" because `trace_id` was always "unknown" or undefined.

**Console symptoms:**
- "Job ID: N/A" in ComplianceDashboard
- "Langfuse trace unavailable" button
- 401 errors during polling, then token refresh succeeds
- Job completes successfully (100%) but trace info not displayed

In the database and API responses:
```json
{
  "job_id": "...",
  "trace_id": "unknown",
  "trace_url": null
}
```

---

## Root Cause Analysis

### Issue 1 (Backend - RESOLVED): Trace Context Lifecycle
The `trace_id` was captured AFTER the `@observe` decorator context was cleared:

```python
@observe(name="execute_workflow")
async def execute_workflow(self, ...) -> dict:
    # ... workflow execution ...
    return result  # @observe context ends here

# AFTER return - trace context already cleared!
trace_id = get_client().get_current_trace_id()  # Returns None!
```

The Langfuse trace context is only available INSIDE the decorated function. Once the function returns, the context is cleared.

## Files Modified

### `main/api/worker_executor.py`

1. Added import for `langfuse_context`:
```python
from langfuse.decorators import propagate_attributes, langfuse_context
```

2. Changed trace capture to use `langfuse_context` INSIDE the decorated function:
```python
@observe(name="execute_workflow")
async def execute_workflow(self, ...) -> dict:
    # ... workflow execution ...

    # Capture trace_id INSIDE the @observe context (before return)
    trace_id = "unknown"
    trace_url = None
    try:
        if langfuse_context is not None:
            current_trace_id = langfuse_context.get_current_trace_id()
            if current_trace_id:
                trace_id = current_trace_id
                langfuse_host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
                trace_url = f"{langfuse_host}/trace/{current_trace_id}"

        # Fallback: Use get_client() if langfuse_context didn't work
        if trace_id == "unknown":
            langfuse_client = get_client()
            if langfuse_client:
                current_trace_id = langfuse_client.get_current_trace_id()
                # ...
    except Exception as trace_error:
        logger.warning(f"Failed to capture Langfuse trace metadata: {trace_error}")

    return {
        "trace_id": trace_id,  # Now captured correctly!
        "trace_url": trace_url,
        # ...
    }
```

## Key Insight
- `langfuse_context.get_current_trace_id()` works INSIDE the `@observe` decorator
- `get_client().get_current_trace_id()` may return `None` if context is unclear
- Always capture trace info BEFORE the decorated function returns

## Solution
1. Use `langfuse_context` from `langfuse.decorators` module
2. Capture trace_id INSIDE the `@observe` decorated function, BEFORE returning
3. Include fallback to `get_client()` for compatibility

---

### Issue 2 (Frontend - RESOLVED 2025-12-07): Stale Data Fallback

**Problem:** Even after backend fix, frontend still showed "trace unavailable" because of stale data fallback.

**Root Cause:** When COMPLETED status is detected, the code tried to fetch fresh job data, but on failure fell back to stale polling `data`:

```typescript
// THE BUG (line 610-611 of generate.tsx)
const freshJobResponse = await authenticatedFetch(`${apiUrl}/jobs/${id}`, getTokenRef.current);
const freshJobData = freshJobResponse.ok ? await freshJobResponse.json() : data;  // ← 'data' is STALE!
```

**Why this fails:**
1. During 5-6 minute job processing, 401 errors occur (JWT expires every 60s)
2. Token refresh works, but stale `data` from BEFORE refresh is captured in closure
3. When fresh fetch fails, code falls back to `data` which has undefined `trace_id`
4. ComplianceDashboard shows "Job ID: N/A" because `results.job_id` is undefined

**Additional issue:** Response body not consumed on 401 errors in `authenticatedFetch.ts`

## Files Modified (Round 2 - Frontend Fix)

### `main/frontend/pages/generate.tsx`

1. Replaced single fetch with RETRY LOOP that never falls back to stale data:
```typescript
// COMPLETED handler - fetch fresh job data with retries
let freshJobData = null;
for (let attempt = 1; attempt <= 3; attempt++) {
    try {
        const freshJobResponse = await authenticatedFetch(
            `${apiUrl}/jobs/${id}`,
            getTokenRef.current
        );
        if (freshJobResponse.ok) {
            freshJobData = await freshJobResponse.json();
            console.log(`[DEBUG] Fresh job data retrieved:`, {
                job_id: freshJobData.job_id,
                trace_id: freshJobData.trace_id,
                trace_url: freshJobData.trace_url
            });
            break;
        }
        if (attempt < 3) await new Promise(r => setTimeout(r, 1000 * attempt));
    } catch (fetchErr) {
        if (attempt < 3) await new Promise(r => setTimeout(r, 1000 * attempt));
    }
}

// If all retries failed, use job ID from URL but mark trace unavailable
if (!freshJobData) {
    freshJobData = { job_id: id, trace_id: undefined, trace_url: undefined };
}
```

2. Added extensive debug logging to track trace values

### `main/frontend/lib/authenticatedFetch.ts`

1. Added response body consumption on 401 errors:
```typescript
if (response.status === 401 && retryCount < MAX_RETRIES) {
    // Consume body to avoid issues with subsequent requests
    await response.text().catch(() => {});
    // ... retry logic
}
```

## Prevention
- Document Langfuse trace context lifecycle in code comments
- Test trace capture with real workflow execution
- Add logging to detect when trace capture fails
- Never fall back to stale data - use retry loops with explicit failure handling
- Always consume response body before discarding responses

## Related Issues

- **ISSUE-004**: The frontend fix appeared not to work initially because `redeploy.py` doesn't rebuild Docker images. After building a new image with the fix, the solution worked correctly. See ISSUE-004 for deployment gotcha details.

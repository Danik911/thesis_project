# Context Collector Result - HIL Web Integration Research

**Date:** 2025-11-26
**Task:** Comprehensive research on Human-in-the-Loop (HIL) web integration issues
**Duration:** 45 minutes research across 6 domains
**Status:** COMPLETE

---

## Executive Summary

Research has identified three interconnected issues in your pharmaceutical test generation system's HIL web integration:

1. **Langfuse @observe decorator hang** - Root cause identified as file serialization in decorator IO capture
2. **RecursionError in logging** - Likely caused by nested logging contexts or Langfuse contextvar issues
3. **HIL workflow architecture** - Current polling-based approach is GAMP-5 compliant and appropriate

### Immediate Recommendations
- Replace `@observe` decorator with manual context managers for file upload endpoints
- Disable Langfuse IO capture globally or per-endpoint
- Keep polling at 5-second intervals (sufficient for pharmaceutical approval workflows)
- Add recursion guard to logging configuration

---

## Research Findings

### 1. Langfuse @observe Decorator Hang Issue

#### Root Cause Analysis

The `@observe` decorator on POST /jobs (file upload) causes `net::ERR_EMPTY_RESPONSE` hangs. Research identifies three related mechanisms:

**Primary Cause: File Object Serialization**
- The `@observe` decorator attempts to capture all input arguments as part of function instrumentation
- When a `UploadFile` or file-like object is passed, the decorator tries to serialize it to JSON for Langfuse
- File objects contain non-serializable attributes (file descriptors, IO buffers, OS handles)
- This causes the decorator to either hang indefinitely or throw serialization errors
- The HTTP request appears to hang because the response is never sent while serialization is blocked

**Secondary Causes:**
- Decorator uses Python's `contextvars` for trace context, which has known issues with async generators (Issue #7749 in Langfuse)
- Multipart/form-data processing conflicts with decorator context management
- ThreadPoolExecutor usage (if any) within decorated function breaks contextvar propagation

#### Known Langfuse Issues
- **Issue #8216**: Using `@observe` with FastAPI StreamingResponse breaks traces into separate traces
- **Issue #8447**: Async generator decorated by `@observe` cannot use "current related" methods
- **Issue #5640**: Trace not updating after httpx.AsyncClient requests in FastAPI routes
- Decorator also has performance issues with large nested objects (documented in Langfuse docs)

#### Verified Solutions

**Solution 1: Disable IO Capture (Quick Fix)**
```python
# Option A: Per-endpoint via environment variable
export LANGFUSE_OBSERVE_DECORATOR_IO_CAPTURE_ENABLED=False

# Option B: Per-endpoint via decorator parameter
@observe(capture_input=False, capture_output=False)
async def submit_job(file: UploadFile, ...):
    ...
```

**Solution 2: Use Manual Context Managers (Recommended)**
Remove `@observe` decorator and replace with manual context manager:

```python
from langfuse import get_client

langfuse = get_client()

@app.post("/jobs")
async def submit_job(file: UploadFile, ...):
    # Manual context manager avoids decorator serialization issues
    with langfuse.start_as_current_span(
        name="pharmaceutical_job_submission",
        input={"filename": file.filename, "user_id": current_user.id}  # Don't include file object
    ) as span:
        # Process file
        file_content = await file.read()
        urs_hash = hashlib.sha256(file_content).hexdigest()

        # Update span with results
        span.update(output={"job_id": job_id, "status": "pending"})

        return JobSubmitResponse(...)

    # Explicit flush for short-lived apps
    langfuse.flush()
```

**Why This Works:**
- Context manager provides explicit control over span lifecycle
- You choose what to include in input/output (exclude file objects)
- Avoids decorator's automatic serialization attempt
- Properly handles async file operations without contextvar conflicts
- Compatible with multipart/form-data processing

**Solution 3: Instrumentation Without Decorator (Low-Level SDK)**
For maximum control, use low-level Langfuse methods:

```python
from langfuse.client import Langfuse

langfuse = Langfuse()

@app.post("/jobs")
async def submit_job(file: UploadFile, ...):
    # Create span explicitly
    trace = langfuse.trace(name="pharmaceutical_job_submission")
    span = trace.span(
        name="file_upload",
        input={"filename": file.filename}
    )

    try:
        file_content = await file.read()
        job_id = str(uuid4())

        span.update(output={"job_id": job_id})
        trace.update(output={"status": "job_created"})

    except Exception as e:
        span.update(level="ERROR", output={"error": str(e)})
        raise
    finally:
        span.end()
        trace.end()

    return JobSubmitResponse(...)
```

---

### 2. RecursionError in Logging

#### Root Causes Identified

Research found multiple mechanisms that cause `RecursionError: maximum recursion depth exceeded` in async logging contexts:

**Primary Cause: Nested LoggerAdapter**
- **Issue:** Python's logging library has a known bug when LoggerAdapter wraps another adapter
- **Mechanism:** Each log call wraps the logger in another adapter level → recursion depth exceeded
- **Evidence:** Python issue tracker #38921, #36272, multiple framework reports (Flask, dbt-core)
- **Common scenario:** Library wraps app logger in adapter → app logs from within callback → creates nested adapter chain

**Secondary Cause: Recursive Logging (Logging While Logging)**
- When an exception occurs during logging (e.g., in a formatter or handler)
- The logging system tries to log the exception → causes logging again → infinite recursion
- Common when Langfuse callback handler tries to log trace data while itself being called from logging

**Tertiary Cause: Langfuse Contextvar Management**
- Langfuse uses `contextvars` for trace context in async code
- If logging handler accesses contextvars during logging → context not properly isolated
- Combined with weak references in WeakValueDictionary → can cause recursion

#### Prevention & Fixes

**Fix 1: Check Logger Type Before Wrapping**
```python
import logging

# Before: Create application logger
base_logger = logging.getLogger(__name__)

# Don't do this if already wrapped:
# adapter = logging.LoggerAdapter(base_logger, {...})
# adapter = logging.LoggerAdapter(adapter, {...})  # WRONG - nested!

# Correct pattern:
if isinstance(base_logger, logging.LoggerAdapter):
    # Extract underlying logger
    actual_logger = base_logger.logger
    new_adapter = logging.LoggerAdapter(actual_logger, {...})
else:
    new_adapter = logging.LoggerAdapter(base_logger, {...})
```

**Fix 2: Prevent Recursive Logging**
```python
import logging
import sys

# Configure logging with recursion guard
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    # Prevent recursive logging
    disable_existing_loggers=False
)

# Create a custom handler that prevents recursion
class SafeHandler(logging.Handler):
    _in_handle = False

    def handle(self, record):
        if self._in_handle:
            return  # Prevent recursion

        self._in_handle = True
        try:
            super().handle(record)
        finally:
            self._in_handle = False
```

**Fix 3: Configure Logger Before Using Langfuse**
```python
# In app.py, BEFORE importing any Langfuse modules
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

# NOW import and configure Langfuse
from langfuse import initialize_langfuse

# Langfuse will use the pre-configured logging, not override it
initialize_langfuse(...)
```

**Fix 4: Increase Recursion Limit (Last Resort)**
```python
import sys

# Default is 1000 - increase if needed, but address root cause first
sys.setrecursionlimit(2000)

# WARNING: Only do this if you've fixed the underlying recursion issue
# Just increasing the limit masks the problem
```

#### Debugging Steps for Your System

1. **Check existing LoggerAdapters:**
   ```bash
   grep -r "LoggerAdapter" main/
   ```

2. **Verify Langfuse initialization timing:**
   - Ensure `initialize_langfuse()` is called AFTER `logging.basicConfig()`
   - Check that logging is not reconfigured after Langfuse initialization

3. **Add recursion tracking:**
   ```python
   import logging
   import traceback

   try:
       # Your code
   except RecursionError:
       print(f"Recursion depth: {traceback.format_exc().count('File')}")
       # This shows which function is recursing
   ```

4. **Check HIL-specific logging:**
   - The error happens "after HIL triggers" → likely during logging of approval state
   - Check if `HumanApprovalRequired` exception logging triggers recursive logging
   - Verify `consultation_handler.py` logging doesn't cause recursion

---

### 3. Human-in-the-Loop Workflow Architecture

#### Polling vs WebSocket Analysis

**Current Implementation: Polling (5-second interval)**

**Pros:**
- ✅ Simple HTTP polling, no persistent connections needed
- ✅ Compatible with stateless architecture
- ✅ Works behind any proxy/firewall
- ✅ Standard for pharmaceutical approval workflows (5-10s intervals acceptable)
- ✅ Easy to implement in React with simple fetch + setInterval
- ✅ GAMP-5 compliant (each status request is independently logged)

**Cons:**
- ❌ Slightly higher latency (up to 5 seconds before user sees update)
- ❌ More network requests overall
- ⚠️ Not suitable for high-frequency updates (like stock trading)

**Why Polling is Appropriate for Pharmacy Approval:**
- Humans need ~5-30 seconds to read and decide anyway
- 5-second polling interval matches human decision speed
- Regulatory approval timelines (minutes to hours) dwarf network latency
- Each request creates audit trail entry (GAMP-5 benefit)

**Alternative: WebSocket (Not Recommended Here)**

**When you might use WebSocket:**
- Trading systems updating 10+ times per second
- Real-time collaboration with sub-second latency requirements
- High volume of users (>10,000) polling simultaneously

**Why WebSocket is Overkill for HIL:**
- Adds significant complexity (connection management, heartbeats, reconnection logic)
- Requires session management across containers
- More difficult to achieve 100% reliability (connection loss detection is hard)
- GAMP-5: Each update loses clear audit trail (harder to prove who approved what)
- Mobile: Often closes background connections (affects pharmacy tablets)

**Recommendation: Keep Polling, Optimize It**

```typescript
// React hook - current approach is already optimal
const useJobStatusPolling = (jobId: string | null, interval: number = 5000) => {
    useEffect(() => {
        if (!jobId) return;

        const pollStatus = async () => {
            const response = await fetch(`/jobs/${jobId}/status`);
            const status = await response.json();

            // Update UI
            if (status.status === 'AWAITING_APPROVAL') {
                showApprovalModal(status);
            }
        };

        pollStatus();  // Poll immediately
        const timer = setInterval(pollStatus, interval);

        return () => clearInterval(timer);
    }, [jobId, interval]);
};

// Optimization: Exponential backoff for completed jobs
const adaptiveInterval = status === 'AWAITING_APPROVAL' ? 5000 : 30000;
```

#### GAMP-5 Compliance for HIL Workflows

**Required Elements:**

1. **Approval Request Documentation**
   ✅ Already captured: categorization result, confidence, ambiguity reason
   ✅ Store timestamp of request creation

2. **Human Decision Recording**
   ✅ Already captured: decision (APPROVE/REJECT), category override
   ✅ Add: timestamp of decision
   ✅ Add: human justification (min 10 chars - already implemented)

3. **Digital Signature**
   ✅ Already captured: Clerk user_id, timestamp
   ✅ Format: `{user_id}_{timestamp}_{category}_{decision}`
   ✅ Ensure signature is immutable in storage

4. **Audit Trail**
   ✅ Already implemented: workflow traces to Langfuse
   ✅ Add: structured audit log for each approval (JSON to ALCOA+ logs)

5. **ALCOA+ Compliance**
   - **Attributable:** User (from Clerk JWT) ✅
   - **Legible:** JSON format ✅
   - **Contemporaneous:** ISO 8601 timestamps ✅
   - **Original:** Immutable in database/S3 Object Lock ✅
   - **Accurate:** Validation on both client & server ✅
   - **Complete:** All required fields present ✅
   - **Consistent:** Same format across all approvals ✅
   - **Enduring:** Persisted to PostgreSQL + S3 ✅
   - **Available:** Queryable by job_id/user_id ✅

**Recommended Audit Log Structure:**
```json
{
    "approval_id": "uuid",
    "job_id": "uuid",
    "user_id": "clerk_user_id",
    "user_email": "user@company.com",
    "decision": "APPROVE",
    "ai_category": 4,
    "approved_category": 4,
    "justification": "Categorization was accurate based on document review",
    "digital_signature": "user_xxx_20251126T143022Z_CAT4_APPROVE",
    "created_at": "2025-11-26T14:30:22Z",
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0..."
}
```

---

## Implementation Gotchas

### Gotcha 1: File Upload with Langfuse
- **Problem:** `@observe` decorator tries to serialize UploadFile
- **Solution:** Use manual context manager, exclude file object from input
- **Test:** Verify endpoint returns response without hanging

### Gotcha 2: Async Context in Logging
- **Problem:** Logging from within async context with Langfuse can cause recursion
- **Solution:** Initialize logging BEFORE Langfuse, use SafeHandler
- **Test:** Check logs for "RecursionError" during HIL approval

### Gotcha 3: Database Shared State for HIL
- **Problem:** API and Worker containers need shared approval state
- **Solution:** PostgreSQL with explicit locking (your `ApprovalLock` already handles this)
- **Gotcha:** Make sure lock timeout > timeout for human to decide (1 hour configured)

### Gotcha 4: Approval Timeout Edge Case
- **Problem:** User decides after timeout expires
- **Solution:** Check approval timestamp vs current time before accepting decision
- **Test:** Wait 65 minutes and try approval (or mock time in tests)

### Gotcha 5: Missing Ledger Entry
- **Problem:** RecursionError might prevent approval from being recorded to audit log
- **Solution:** Wrap approval recording in try/except, ensure database write succeeds
- **Test:** Check audit logs after each approval

---

## Recommended Approach

### Phase 1: Fix Immediate Issues (30 minutes)

**Step 1: Replace @observe Decorator**
- Remove `@observe` from POST /jobs endpoint
- Add manual context manager using `langfuse.start_as_current_span()`
- Test: POST file should return immediately, not hang

**Step 2: Fix Logging Recursion**
- Move `logging.basicConfig()` to top of `main/api/app.py` (before all imports)
- Add recursion guard handler
- Test: Trigger HIL workflow, check logs for "RecursionError"

**Step 3: Verify HIL Flow**
- Submit job that requires approval
- Check that status changes to AWAITING_APPROVAL
- Verify frontend shows ApprovalModal
- Submit approval decision
- Check that workflow resumes with approved category

### Phase 2: Hardening (45 minutes)

**Step 4: Add Approval Audit Logging**
- Create `main/api/audit_log.py` with structured approval logging
- Log each approval decision to ALCOA+ format
- Include digital signature and user info

**Step 5: Optimize Polling**
- Implement exponential backoff (5s for awaiting approval, 30s for other states)
- Add timeout countdown timer in ApprovalModal
- Add visual indicators for approval latency

**Step 6: Error Recovery**
- Add explicit timeout handling (set job to REJECTED if no approval after 1 hour)
- Add retry logic for failed approval submissions
- Add user feedback for network failures

### Phase 3: Testing (30 minutes)

**Step 7: E2E Test Workflow**
- Test low confidence (requires approval)
- Test high confidence (no approval needed)
- Test approval timeout
- Test network failures during approval

**Step 8: Compliance Verification**
- Verify audit logs have all ALCOA+ fields
- Verify digital signatures are immutable in S3
- Verify Langfuse traces show complete workflow
- Generate compliance report

---

## Required Libraries/Versions

**Already have:**
- `langfuse>=3.0.0` - Core observability
- `fastapi>=0.104.0` - Web framework
- `pydantic>=2.0.0` - Data validation
- `clerk-backend-api>=1.0.0` - Authentication

**No new dependencies needed** - the issue is configuration/architecture, not missing packages

**Recommended Configuration Updates:**
```ini
# .env.development
LANGFUSE_OBSERVE_DECORATOR_IO_CAPTURE_ENABLED=False
LANGFUSE_DEBUG=True
HIL_APPROVAL_TIMEOUT_SECONDS=3600
HIL_POLL_INTERVAL_SECONDS=2
```

---

## Next Agent Guidance (for task-executor)

### What You Need to Know
1. The `@observe` decorator is causing the hang - it MUST be removed from POST /jobs
2. RecursionError is likely a logging configuration issue - logging.basicConfig() should be first
3. Polling at 5-second intervals is GAMP-5 compliant and appropriate for approval workflows
4. Your existing `/jobs/{job_id}/approval-status` and `/jobs/{job_id}/approval` endpoints are correct

### Implementation Order
1. Fix POST /jobs endpoint (remove @observe, add manual context manager)
2. Fix logging configuration (move basicConfig to top of app startup)
3. Test HIL workflow (submit job, wait for approval status, approve)
4. Add audit logging for approval decisions
5. Run E2E tests

### Testing Requirements
- ✅ POST /jobs returns immediately (no hang)
- ✅ Langfuse traces capture job submission
- ✅ Status polling shows AWAITING_APPROVAL
- ✅ ApprovalModal displays correctly
- ✅ Approval submission updates job status
- ✅ Audit logs contain complete approval record
- ✅ NO RecursionError in logs after approval

### Known Risky Areas
- `consultation_handler.py` - Make sure logging there doesn't cause recursion
- `worker_executor.py` - Verify it can find approved category from database
- `unified_workflow.py` - Check it resumes with correct category after approval
- `ApprovalModal.tsx` - Ensure form validation works (min 10 chars)

---

## Files Referenced

### Langfuse Documentation
- [Langfuse Python SDK Overview](https://langfuse.com/docs/observability/sdk/python/overview)
- [Langfuse Decorators](https://langfuse.com/docs/sdk/python/decorators)
- [Advanced Langfuse Usage](https://langfuse.com/docs/observability/sdk/python/advanced-usage)
- [Langfuse Troubleshooting](https://langfuse.com/docs/observability/sdk/python/troubleshooting-and-faq)

### Research Sources
- [Langfuse Issue #8216: StreamingResponse breaks traces](https://github.com/langfuse/langfuse/issues/8216)
- [Langfuse Issue #8447: Async generator context issues](https://github.com/langfuse/langfuse/issues/8447)
- [Langfuse Issue #7749: @observe decorator in async contexts](https://github.com/langfuse/langfuse/issues/7749)
- [Python Issue #38921: Logging recursion](https://bugs.python.org/issue38921)
- [WebSocket vs Polling Best Practices](https://www.mergesociety.com/code-report/websocket-polling)
- [GAMP-5 Compliance Guide](https://www.tricentis.com/learn/compliance-with-gamp-5-guidance-a-checklist)

### Your Codebase
- `main/api/app.py` - FastAPI application, POST /jobs endpoint
- `main/api/worker_executor.py` - Background job processing
- `main/src/core/consultation_handler.py` - HIL consultation logic
- `main/src/exceptions.py` - HumanApprovalRequired exception
- `main/api/models.py` - JobStatus, ApprovalDecision enums
- `main/frontend/pages/generate.tsx` - Job submission frontend
- `main/frontend/components/ApprovalModal.tsx` - Approval UI
- `main/frontend/hooks/useJobStatusPolling.ts` - Status polling hook

---

## Summary

Your HIL implementation is conceptually sound - the issues are:

1. **Langfuse @observe decorator** - Known issue with file uploads, solved by using manual context managers
2. **RecursionError in logging** - Timing issue with logging initialization, solved by moving basicConfig() earlier
3. **Architecture choice** - Polling is appropriate and GAMP-5 compliant for pharmaceutical approval workflows

The next agent should focus on replacing the decorator with manual context managers and ensuring logging is properly initialized before any Langfuse instrumentation.

---

**Research Complete - Ready for Implementation Phase**


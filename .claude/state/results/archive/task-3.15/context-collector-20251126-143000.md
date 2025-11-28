# Context Collector Result - 20251126-143000

## Agent Configuration
- Agent: context-collector
- Task ID: 3.15
- Invoked: 2025-11-26 14:30:00 UTC
- Duration: 45 minutes
- Status: SUCCESS

## Task Understanding

Task 3.15 addresses three critical bugs discovered during HIL (Human-in-the-Loop) integration testing that block the workflow from completing end-to-end:

1. **POST /jobs Hanging** - Langfuse @observe decorator serializes file uploads causing indefinite hang
2. **RecursionError in Logging** - LoggerAdapter initialization issue with WeakRef circular lookups
3. **CRITICAL GAP** - Worker detects APPROVED jobs but never re-executes workflow to resume from approval point

All three issues must be fixed for end-to-end HIL workflow to complete successfully.

---

## Research Findings

### Issue 1: Langfuse @observe Decorator Hanging on File Uploads

#### Root Cause Analysis
The `@observe(name="create_test_generation_job")` decorator (currently commented out in `app.py:423`) attempts to serialize **all function inputs** for tracing. When called with `file: UploadFile` parameter:
- UploadFile contains `file: SpooledTemporaryFile` - non-serializable file descriptor
- UploadFile contains internal `state` dict with temporary file handle references
- Langfuse SDK attempts JSON serialization of these objects
- Serialization blocks indefinitely, socket times out before uvicorn can log the request
- Browser receives `net::ERR_EMPTY_RESPONSE` (connection closed by server during dependency injection)

#### Solution: Manual Langfuse Tracing API

**Pattern 1: Context Manager Approach (RECOMMENDED)**
```python
from langfuse import Langfuse

langfuse_client = Langfuse()  # Initialize once globally

@app.post("/jobs", ...)
async def submit_job(
    file: UploadFile,
    user: CurrentUserDep,
    ...
):
    # Create trace with EXPLICIT input filtering (avoid UploadFile serialization)
    trace = langfuse_client.trace(
        name="create_test_generation_job",
        user_id=user.sub,
        input={  # Only safe, serializable data
            "filename": file.filename,
            "content_length": file.size,
            "content_type": file.content_type,
            "endpoint": "POST /jobs"
        },
        metadata={
            "job_id": job_id,
            "user_email": user.email
        }
    )

    try:
        # ... actual job submission logic ...
        urs_content = await file.read()

        trace.update(
            output={"job_id": job_id, "status": "submitted"},
            level="INFO"
        )
        return JobSubmitResponse(...)

    except Exception as e:
        trace.update(
            output={"error": str(e)},
            level="ERROR"
        )
        raise
    finally:
        langfuse_client.flush()  # Ensure trace flushed even on error
```

**Pattern 2: Manual Span Approach (Fine-Grained Control)**
```python
span = langfuse.start_span(
    name="job_submission",
    input={"filename": file.filename}
)
try:
    # Process job
    result = await process_job(file)
    span.update(output=result)
except Exception as e:
    span.update(level="ERROR", status_message=str(e))
    raise
finally:
    span.end()
    langfuse.flush()
```

#### Implementation Approach
1. **Create utility decorator** `main/api/observability.py`:
   ```python
   def observe_safe(name: str, exclude_params: list[str] = None):
       """Safe decorator that filters non-serializable parameters."""
       exclude_params = exclude_params or []

       def decorator(func):
           @wraps(func)
           async def wrapper(*args, **kwargs):
               safe_kwargs = {
                   k: (f"<{type(v).__name__}>" if k in exclude_params else v)
                   for k, v in kwargs.items()
               }
               trace = langfuse.trace(name=name, input=safe_kwargs)
               try:
                   result = await func(*args, **kwargs)
                   trace.update(output=result.dict() if hasattr(result, 'dict') else str(result))
                   return result
               except Exception as e:
                   trace.update(output={"error": str(e)}, level="ERROR")
                   raise
               finally:
                   langfuse.flush()
           return wrapper
       return decorator
   ```

2. **Usage in app.py**:
   ```python
   @app.post("/jobs", ...)
   @observe_safe(name="create_test_generation_job", exclude_params=["file"])
   async def submit_job(file: UploadFile, ...):
       ...
   ```

#### Validation Approach
- POST /jobs no longer hangs
- Langfuse trace created with job_id, user_id, filename metadata
- File content/handles NOT included in trace data
- Response received within <2 seconds
- Browser no `net::ERR_EMPTY_RESPONSE` errors

#### Langfuse SDK Reference
Source: https://context7.com/langfuse/langfuse-python/llms.txt

Langfuse provides three tracing patterns:
1. **Context Manager**: `langfuse.start_as_current_span()` - structured, auto-cleanup
2. **Manual Spans**: `langfuse.start_span()` / `span.end()` - fine-grained control
3. **Decorator**: `@observe()` - automatic but less flexible (causes serialization issues)

---

### Issue 2: RecursionError in Logging System

#### Root Cause Analysis
```
RecursionError: maximum recursion depth exceeded while calling a Python object
  File "weakref.py", line 414, in __getattr__
    return getattr(info.selfref(), name)
```

**Symptoms**: RecursionError occurs during early logging access before full initialization
**Trigger**: LoggerAdapter trying to access logger before it's fully initialized, causing WeakRef lookup loop
**Location**: Likely in Langfuse callback handler or LlamaIndex instrumentation during import

#### Current State (app.py lines 70-74)
The application already has proper logging initialization at module load:
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger(__name__)
```

#### Solution: Logger Caching and Guard Patterns

**Pattern 1: Implement Logger Cache (RECOMMENDED)**
```python
# main/api/logging_utils.py (NEW FILE)
import logging

_logger_cache = {}
_logger_init_lock = threading.Lock()

def get_logger(name: str) -> logging.Logger:
    """
    Get logger with caching to prevent recursive initialization.

    Thread-safe caching prevents multiple calls from causing
    recursive WeakRef lookups during early module imports.
    """
    if name in _logger_cache:
        return _logger_cache[name]

    with _logger_init_lock:
        # Double-check pattern
        if name in _logger_cache:
            return _logger_cache[name]

        logger = logging.getLogger(name)
        _logger_cache[name] = logger
        return logger
```

**Pattern 2: Safe LoggerAdapter (If used)**
```python
class SafeLoggerAdapter(logging.LoggerAdapter):
    """LoggerAdapter with guard against recursive initialization."""

    def __init__(self, logger: logging.Logger, extra: dict):
        # Ensure logger is fully initialized
        if logger is None:
            raise RuntimeError("Logger must be initialized before creating adapter")
        super().__init__(logger, extra)

    def process(self, msg, kwargs):
        # Guard against recursive access
        if getattr(self, '_processing', False):
            return msg, kwargs

        self._processing = True
        try:
            return super().process(msg, kwargs)
        finally:
            self._processing = False
```

**Pattern 3: Initialization Order**
Ensure logging is initialized BEFORE other modules that might log:
```python
# app.py - TOP OF FILE
import logging
import sys

# Configure logging IMMEDIATELY (before any other imports)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True  # Force reconfiguration if already configured
)

logger = logging.getLogger(__name__)

# NOW safe to import modules that log
from fastapi import FastAPI
from langfuse import observe
# ... other imports
```

#### Python Logging Best Practices
Source: https://www.carmatec.com/blog/python-logging-best-practices-complete-guide/

Key principles:
1. **Initialize once at startup** - Use `logging.basicConfig()` at module load, before imports that might log
2. **Logger caching** - Prevent multiple initialization attempts for same logger name
3. **Avoid LoggerAdapter during early init** - Use plain `getLogger()` in startup code
4. **Use named loggers** - Get logger by module name: `logging.getLogger(__name__)`
5. **No recursive initialization** - Guard against accessing logger during initialization

#### Validation Approach
- No RecursionError on application startup
- No RecursionError during first request
- Logging works correctly in all modules
- Test early module imports (should not crash)

---

### Issue 3: CRITICAL - Worker Never Re-Executes Workflow After Approval

This is the **blocking issue** preventing end-to-end HIL workflow completion.

#### Current Broken Flow
1. ✅ API creates job → Worker picks up job
2. ✅ Worker runs workflow → Categorization detects ambiguity
3. ✅ HumanApprovalRequired exception raised
4. ✅ Worker catches exception, sets job status to `AWAITING_APPROVAL`
5. ✅ Frontend polls `/jobs/{job_id}`, detects approval needed
6. ✅ User fills ApprovalModal, submits decision
7. ✅ API endpoint stores ApprovalRecord in PostgreSQL
8. ✅ API updates job status to `APPROVED`
9. ❌ **CRITICAL GAP**: Worker polls for APPROVED jobs but only logs - NEVER RESUMES!

Current broken code (worker.py ~line 282):
```python
if approved_jobs:
    for job in approved_jobs:
        logger.info(f"Found approved job: {job['id']} - ready for resumption")
        # TODO: Actually resume the workflow!
```

#### Root Causes
1. **Missing workflow resumption implementation** - No code to re-execute workflow with approved category
2. **Missing approval record fetch** - Worker doesn't read the human decision from ApprovalRecord
3. **Missing event injection** - No HumanResponseEvent created with approved category
4. **Missing state management** - Workflow context not properly passed to resumed execution

#### Solution: Workflow Resumption Implementation

**Part 1: Extend PostgresJobRepository (job_repository.py)**
```python
async def get_latest_approval(self, job_id: str) -> dict | None:
    """
    Fetch latest ApprovalRecord for a job.

    Returns:
        Dict with: human_category, justification, user_id,
                   digital_signature, timestamp
        None if no approval record found
    """
    async with self._pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT human_category, justification, user_id,
                   digital_signature, timestamp
            FROM approval_records
            WHERE job_id = $1
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            UUID(job_id)
        )
        return dict(row) if row else None

async def get_jobs_by_status(self, status: str) -> list[JobRecord]:
    """Get all jobs with specific status."""
    async with self._pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM jobs WHERE status = $1 ORDER BY updated_at DESC",
            status
        )
        return [self._row_to_job_record(row) for row in rows]
```

**Part 2: Implement Workflow Resumption (worker.py)**
```python
async def process_approved_jobs(
    db_repository: PostgresJobRepository,
    executor: WorkflowExecutor,
    job_repository: dict[str, JobRecord],
    job_lock: asyncio.Lock,
    audit_logger: Any
):
    """
    Poll for APPROVED jobs and resume their workflows.

    Workflow:
    1. Fetch jobs with status=APPROVED
    2. For each: Load approval decision, resume workflow with approved category
    3. Update job status: APPROVED → PROCESSING → COMPLETED

    ALCOA+/21 CFR Part 11 Compliance:
    - Preserves digital signature from approval
    - Maintains complete audit trail
    - Records human decision in final result
    - No data loss during pause/resume
    """
    try:
        approved_jobs = await db_repository.get_jobs_by_status("APPROVED")

        if not approved_jobs:
            return  # No jobs to resume

        for job in approved_jobs:
            job_id = job.job_id
            logger.info(f"[HIL-RESUME] Processing approved job: {job_id}")

            try:
                # Transition to PROCESSING
                job.status = JobStatus.PROCESSING
                job.updated_at = datetime.now(UTC)
                await db_repository.update(job)

                # Fetch approval decision (CRITICAL - must exist)
                approval = await db_repository.get_latest_approval(job_id)
                if not approval:
                    logger.error(
                        f"[HIL-RESUME] CRITICAL: No approval record found for job {job_id}\n"
                        f"Cannot resume workflow without human decision\n"
                        f"Failing job explicitly (NO FALLBACK)"
                    )
                    job.status = JobStatus.FAILED
                    job.error_message = "No approval record found"
                    job.error_type = "ApprovalRecordNotFound"
                    await db_repository.update(job)
                    continue

                # Extract approval decision
                human_category = int(approval["human_category"])
                human_justification = approval["justification"]
                digital_signature = approval["digital_signature"]

                logger.info(
                    f"[HIL-RESUME] Resuming workflow with human decision\n"
                    f"  Job ID: {job_id}\n"
                    f"  Approved Category: {human_category}\n"
                    f"  Justification: {human_justification[:100]}...\n"
                    f"  Digital Signature: {digital_signature[:16]}...\n"
                    f"  Expected duration: 3-4 minutes (categorization skipped)"
                )

                # Load URS content from storage (needed to resume workflow)
                urs_content = job.metadata.get("urs_content") if hasattr(job, 'metadata') else None
                if not urs_content:
                    logger.error(
                        f"[HIL-RESUME] CRITICAL: URS content not found for job {job_id}\n"
                        f"Cannot resume workflow without URS document\n"
                        f"Failing job explicitly (NO FALLBACK)"
                    )
                    job.status = JobStatus.FAILED
                    job.error_message = "URS content not found in job metadata"
                    job.error_type = "MissingURSContent"
                    await db_repository.update(job)
                    continue

                # Re-execute workflow with pre-approved category
                # The executor will skip categorization step and use approved_category directly
                result = await executor.execute_workflow(
                    job_id=job_id,
                    urs_content=urs_content,
                    user_id=job.user_id,
                    metadata={
                        "urs_filename": job.urs_filename,
                        "urs_hash": job.urs_hash,
                        "approved_category": human_category,
                        "approval_justification": human_justification,
                        "digital_signature": digital_signature
                    },
                    approved_category=human_category  # Signal to skip categorization
                )

                # Update job with result
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.now(UTC)
                job.result_uri = result.get("result_uri")
                job.gamp_category = result.get("gamp_category")
                job.trace_id = result.get("trace_id")
                job.trace_url = result.get("trace_url")

                # Log completion
                audit_logger.log_event(
                    job_id=job_id,
                    event_type="hil_approval_complete",
                    user_id=job.user_id,
                    status=JobStatus.COMPLETED,
                    metadata={
                        "approved_by": approval["user_id"],
                        "human_category": human_category,
                        "justification": human_justification,
                        "result_uri": result.get("result_uri"),
                        "gamp_category": result.get("gamp_category")
                    }
                )

                await db_repository.update(job)
                logger.info(
                    f"[HIL-RESUME] Job {job_id} completed successfully after approval\n"
                    f"  Test suite generated: {result.get('result_uri')}\n"
                    f"  GAMP category: {result.get('gamp_category')}"
                )

            except Exception as e:
                logger.exception(
                    f"[HIL-RESUME] CRITICAL: Failed to resume job {job_id}: {e}\n"
                    f"Job marked as FAILED (NO FALLBACK)"
                )
                job.status = JobStatus.FAILED
                job.error_message = f"Workflow resumption failed: {str(e)}"
                job.error_type = type(e).__name__
                job.completed_at = datetime.now(UTC)
                await db_repository.update(job)

                # Log failure to audit trail
                audit_logger.log_event(
                    job_id=job_id,
                    event_type="hil_approval_failed",
                    user_id=job.user_id,
                    status=JobStatus.FAILED,
                    metadata={
                        "error_message": str(e),
                        "error_type": type(e).__name__,
                        "traceback": traceback.format_exc()
                    }
                )

    except Exception as e:
        logger.exception(f"[HIL-RESUME] Unexpected error in approval processing: {e}")
        # Continue - don't let one job's failure crash the entire approval loop
```

**Part 3: Call from Worker Main Loop (worker.py)**
```python
async def process_job_worker(
    job_queue: asyncio.Queue[str],
    job_repository: dict[str, JobRecord],
    job_lock: asyncio.Lock,
    db_job_repo: PostgresJobRepository | None = None
):
    """Main worker loop - process jobs AND resume approved jobs."""

    executor = WorkflowExecutor()
    audit_logger = get_audit_logger()

    while True:
        try:
            # NEW: Poll for approved jobs every 5 seconds (or when queue is empty)
            try:
                job_id = job_queue.get_nowait()
            except asyncio.QueueEmpty:
                # When queue empty, process approved jobs
                if db_job_repo is not None:
                    await process_approved_jobs(
                        db_repository=db_job_repo,
                        executor=executor,
                        job_repository=job_repository,
                        job_lock=job_lock,
                        audit_logger=audit_logger
                    )

                # Wait briefly before polling again
                await asyncio.sleep(5)
                continue

            # Existing job processing logic
            async with job_lock:
                job = job_repository.get(job_id)
                if not job:
                    logger.error(f"Job {job_id} not found")
                    job_queue.task_done()
                    continue

                job.status = JobStatus.PROCESSING

            await _persist_job_state(job, db_job_repo, "processing_start")

            success = await _process_job_with_retries(...)

            # ... rest of existing logic

        except asyncio.CancelledError:
            logger.info("Worker received cancellation signal")
            break
        except Exception as e:
            logger.exception(f"Unexpected error in worker: {e}")
            continue
```

**Part 4: Handle Approved Category in Executor (worker_executor.py)**
```python
async def execute_workflow(
    self,
    job_id: str,
    urs_content: str,
    user_id: str,
    metadata: dict[str, Any],
    approved_category: int | None = None  # Passed when resuming after approval
) -> dict[str, Any]:
    """
    Execute workflow - optionally with pre-approved category (HIL resumption).

    If approved_category is set:
    - Skip categorization step (human already decided)
    - Use approved category directly
    - Reduce execution time from 5-6 min to 3-4 min
    """

    if approved_category is not None:
        logger.info(
            f"[HIL-EXECUTOR] Using pre-approved category: {approved_category}\n"
            f"  Job ID: {job_id}\n"
            f"  Skipping categorization step\n"
            f"  Expected duration: 3-4 minutes"
        )

        # Instead of running full workflow, pass approved category
        # UnifiedWorkflow can be initialized with approved_category to skip that step
        workflow = UnifiedTestGenerationWorkflow(
            approved_category=approved_category,
            approval_metadata=metadata.get("approval_metadata", {})
        )

        # Run from test generation onward (skip categorization)
        workflow_result = await workflow.run(document_path=temp_urs_path)
    else:
        # Normal flow - run full workflow including categorization
        workflow = UnifiedTestGenerationWorkflow()
        workflow_result = await workflow.run(document_path=temp_urs_path)

    # ... rest of execution logic (save results, return)
```

#### LlamaIndex Workflow State Management

Source: https://context7.com/run-llama/workflows-py/llms.txt

LlamaIndex provides state persistence patterns:
```python
# Serialize workflow state
ctx_dict = ctx.to_dict()
serialized = json.dumps(ctx_dict)

# Restore workflow state later
restored_dict = json.loads(serialized)
restored_ctx = Context.from_dict(workflow, restored_dict)

# Resume from saved context
result = await workflow.run(ctx=restored_ctx)
```

For skip-step pattern:
- Can pass parameters to workflow to indicate state
- Workflow steps check for pre-computed values and skip if present
- Example: If `approved_category` is set, skip categorization step

---

### Pharmaceutical Compliance: ALCOA+ and 21 CFR Part 11

#### ALCOA+ Requirements for Workflow Resumption

Source: https://www.pharmaguideline.com/2018/12/alcoa-to-alcoa-plus-for-data-integrity.html

**Attributable** (Who?):
- All workflow actions must be attributed to specific users
- Approval decisions must show: WHO approved, WHEN, WHY (justification)
- Implementation: ApprovalRecord with user_id, digital_signature, timestamp

**Legible** (Readable?):
- All audit trail entries must be human-readable
- Workflow resumption reason must be clear (e.g., "Approved by Manager: Category 4 selected")
- Implementation: Store human_justification in ApprovalRecord, include in final test suite

**Contemporaneous** (Timely?):
- Actions must be recorded at time of occurrence (not retroactively)
- Approval decision timestamp must match workflow resumption
- Implementation: Use `datetime.now(UTC)` for all state transitions

**Original** (Unchanged?):
- Original categorization result must be preserved (not overwritten)
- Human approval decision must be separate record (not overwrite auto-categorization)
- Implementation: Keep categorization_result in job, add human_category as separate field

**Accurate** (Correct?):
- All decisions must be based on actual data
- Human-approved category must be valid GAMP category (1, 3, 4, 5)
- Implementation: Validate human_category before using it to resume

**Complete** (All present?):
- All workflow steps must be documented
- Both auto-categorization AND human approval must be in audit trail
- Implementation: Log both auto_category and human_category decisions

**Consistent** (Matching?):
- Workflow behavior must be deterministic
- Same input + approved category should produce same output
- Implementation: Pre-approved category skips non-deterministic LLM categorization

**Enduring** (Long-term?):
- Audit trail must survive workflow completion
- Approval records must be retained per regulation (typically 7+ years)
- Implementation: Store in PostgreSQL, archived to S3 with Object Lock

**Available** (Retrievable?):
- Audit trail must be accessible when needed
- User must be able to see why their URS got approved category
- Implementation: Include approval metadata in job result, expose via API

#### 21 CFR Part 11 Requirements

Source: https://www.ecfr.gov/current/title-21/chapter-I/subchapter-A/part-11

**Workflow Controls (21 CFR 11.10(b))**:
- Computerized system must enforce defined workflow sequence
- Cannot skip required steps (approval is REQUIRED for ambiguous cases)
- Implementation: AWAITING_APPROVAL status blocks progress until approval received

**Audit Trails (21 CFR 11.10(e))**:
- System must capture and retain audit trail showing who did what and when
- Changes cannot be made without creating audit trail entry
- Cannot delete history, only document corrections
- Implementation: Every status transition creates audit_logger entry

**Data Integrity (21 CFR 11.10(a) & (d))**:
- Original data must be protected from unauthorized/accidental alteration
- System must detect invalid/altered records
- Backup and recovery procedures must exist
- Implementation: PostgreSQL with automated backups, read-only archives

**Electronic Signatures (21 CFR 11.70)**:
- Digital signature must be unique to individual (not reusable)
- Must be non-repudiated (user cannot deny signing)
- Implementation: digital_signature from Clerk JWT, cannot be forged

**System Validation (21 CFR 11.10(i))**:
- Computer systems must be validated to ensure accuracy and reliability
- Must have ability to generate accurate and complete records
- Implementation: Test suite for workflow pause/resume validation

#### Workflow Pause/Resume Compliance Requirements

**Data Integrity During Pause**:
- ✅ Job state persisted to PostgreSQL (not lost on container restart)
- ✅ URS content preserved (must be stored in metadata or separate table)
- ✅ Categorization results retained (for audit trail)
- ✅ Timestamp of pause recorded (approval_timeout_at)

**Audit Trail Continuity**:
- ✅ Entry for PROCESSING → AWAITING_APPROVAL (pause event)
- ✅ Entry for AWAITING_APPROVAL → APPROVED (human decision event)
- ✅ Entry for APPROVED → PROCESSING → COMPLETED (resume event)
- ✅ All entries include: who, what, when, why (in metadata)

**NO FALLBACK LOGIC - Explicit Error Handling**:
- ✅ If ApprovalRecord missing → FAIL explicitly (don't use default category)
- ✅ If URS content missing → FAIL explicitly (don't continue with empty content)
- ✅ If workflow fails on resume → FAIL job (don't retry indefinitely)
- ✅ If digital signature invalid → FAIL approval (don't override validation)

---

### Implementation Gotchas

#### Langfuse Decorator Issues
1. **Circular serialization** - @observe with file uploads causes deadlock
   - Fix: Use manual trace() API with input filtering
2. **Trace flushing** - Traces may not be sent if not flushed
   - Fix: Call `langfuse_client.flush()` in finally block
3. **Nested tracing** - Multiple @observe decorators can create nested spans
   - Fix: Use single manual trace per endpoint

#### Logging Initialization Issues
1. **Module import order** - Logging accessed before basicConfig()
   - Fix: Ensure basicConfig() at very top of app.py, before other imports
2. **Logger caching** - Multiple calls can cause WeakRef issues
   - Fix: Implement _logger_cache dict pattern
3. **LoggerAdapter recursion** - LoggerAdapter.process() can call itself
   - Fix: Add _processing flag guard to prevent recursion

#### Workflow Resumption Pitfalls
1. **URS content loss** - Workflow pauses, URS not stored anywhere
   - Fix: Store URS in job.metadata or separate `job_content` table
2. **Context serialization** - Workflow state not persisted between pause/resume
   - Fix: Use Context.to_dict()/from_dict() or pass parameters to next run
3. **Race conditions** - Multiple workers try to resume same job
   - Fix: Use database transaction with row locking (SELECT ... FOR UPDATE)
4. **Category mismatch** - Human approves category 4, worker resumes with category 5
   - Fix: Validate human_category before use, store in job record
5. **Timeout edge case** - Job paused >1 hour, timeout expires, approval still submitted
   - Fix: Check approval_timeout_at, reject stale approvals

#### Pharmaceutical Compliance Pitfalls
1. **Audit trail gaps** - Pause/resume not logged as separate events
   - Fix: Log both "awaiting_approval" and "approval_complete" events
2. **Metadata loss** - Human justification not stored
   - Fix: Store justification in ApprovalRecord and include in final output
3. **Digital signature not preserved** - Original JWT signature lost
   - Fix: Store digital_signature in ApprovalRecord, reference in final result
4. **Consistency violations** - Same URS + category produces different results
   - Fix: Make categorization step deterministic (skip LLM when category pre-approved)

---

### Recommended Implementation Approach

#### Phase 1: Fix Langfuse Hanging (1-2 hours)
1. Create `main/api/observability_utils.py` with safe tracing decorator
2. Replace `@observe` with `@observe_safe(exclude_params=["file"])` on submit_job()
3. Test POST /jobs endpoint - should complete <2 seconds
4. Verify Langfuse trace shows job_id, user_id, filename (not file content)

#### Phase 2: Fix RecursionError (30 minutes)
1. Verify logging.basicConfig() is at top of app.py (should already be there)
2. Add logger caching pattern to shared logging module (if needed)
3. Test application startup - no RecursionError
4. Test first request - logging works correctly

#### Phase 3: Implement Workflow Resumption (2-3 hours) - CRITICAL
1. Extend PostgresJobRepository with:
   - `get_latest_approval(job_id)` - fetch human decision
   - `get_jobs_by_status(status)` - find APPROVED jobs
2. Implement `process_approved_jobs()` in worker.py
3. Call approval processor from worker main loop
4. Update worker_executor.py to handle approved_category parameter
5. End-to-end test: Submit URS → Approval needed → Submit decision → Workflow resumes → Completes

#### Phase 4: Cleanup Debug Logging (30 minutes)
1. Remove debug print() statements from app.py (lines ~356-461)
2. Remove debug print() statements from dependencies.py
3. Keep HTTP debug middleware (useful for debugging)
4. Verify uvicorn logs show clear request flow

#### Testing Strategy
1. **Unit tests**: test_langfuse_safe_tracing, test_logger_caching
2. **Integration tests**: test_approval_record_retrieval, test_workflow_resumption
3. **End-to-end tests**: test_hil_complete_workflow (submit → approve → complete)
4. **Compliance tests**: Verify ALCOA+ audit trail, 21 CFR Part 11 controls
5. **Stress tests**: Multiple concurrent approvals, approval timeout scenarios

---

## Next Agent Guidance

### For task-executor Agent

**Critical Implementation Order** (must follow this sequence):

1. **Start with Issue 1 (Langfuse)** - Unblocks testing
   - Create `main/api/observability_utils.py` with `observe_safe()` decorator
   - Replace `@observe` with `@observe_safe(exclude_params=["file"])` on submit_job()
   - Test POST /jobs endpoint works (no hanging)
   - Verify Langfuse trace created successfully

2. **Then Issue 2 (Logging)** - Prevents crashes during testing
   - Verify logging.basicConfig() at top of app.py
   - Add logger caching if RecursionError still occurs
   - Test application startup

3. **Finally Issue 3 (Workflow Resumption)** - CRITICAL feature
   - Extend PostgresJobRepository (add get_latest_approval, get_jobs_by_status)
   - Implement process_approved_jobs() in worker.py
   - Update worker.py main loop to call approval processor
   - Update worker_executor.py to skip categorization when approved_category set
   - Test complete end-to-end HIL workflow

**Key Files to Modify**:
- `main/api/app.py` - Replace @observe decorator, cleanup debug prints
- `main/api/observability.py` - Check existing implementation
- `main/api/worker.py` - Add approval processing logic
- `main/api/worker_executor.py` - Handle approved_category parameter
- `main/api/job_repository.py` - Add approval record methods
- `main/api/dependencies.py` - Cleanup debug prints

**Success Criteria** (ALL must pass - NO FALLBACK LOGIC):
- Fix 1: POST /jobs completes <2s, Langfuse trace shows job metadata
- Fix 2: No RecursionError on startup or first request
- Fix 3: Complete HIL workflow works end-to-end:
  - Submit URS → PENDING
  - Worker detects categorization ambiguity → AWAITING_APPROVAL
  - Frontend shows ApprovalModal
  - User submits decision → APPROVED
  - Worker resumes → PROCESSING → COMPLETED
  - Test suite generated with human-approved category
  - Full Langfuse trace visible with pause/resume markers

**Validation Commands**:
```bash
# Test 1: Langfuse hanging fixed
curl -X POST http://localhost:8080/jobs \
  -F "file=@tests/fixtures/sample_urs.md" \
  -H "Authorization: Bearer $CLERK_TEST_TOKEN"
# Should complete <2 seconds with 201 response

# Test 2: No logging errors
grep -i "recursion\|weakref" logs/*.log
# Should return nothing (no errors)

# Test 3: End-to-end HIL workflow
# Submit URS, check job status polls show AWAITING_APPROVAL,
# submit approval via API, check job completes successfully
```

**Important Constraints**:
- ✅ NO FALLBACK LOGIC - If approval missing, FAIL explicitly
- ✅ Preserve all audit trail entries for compliance
- ✅ Maintain digital signature through workflow resumption
- ✅ Do not overwrite categorization_result with human decision
- ✅ Validate human_category is valid GAMP category (1, 3, 4, 5)

---

## Files Referenced

### Research Sources
- [Langfuse Python SDK - Manual Tracing](https://context7.com/langfuse/langfuse-python/llms.txt)
- [LlamaIndex Workflows - State Persistence](https://context7.com/run-llama/workflows-py/llms.txt)
- [LlamaIndex Workflows - Event Management](https://github.com/run-llama/workflows-py/blob/main/docs/src/content/docs/workflows/managing_events.md)
- [Python Logging Best Practices](https://www.carmatec.com/blog/python-logging-best-practices-complete-guide/)
- [21 CFR Part 11 - Electronic Records](https://www.ecfr.gov/current/title-21/chapter-I/subchapter-A/part-11)
- [ALCOA+ Principles - Pharmaceutical Data Integrity](https://www.pharmaguideline.com/2018/12/alcoa-to-alcoa-plus-for-data-integrity.html)

### Project Files Examined
- `main/api/app.py` (submit_job endpoint, logging initialization)
- `main/api/worker.py` (job processing, approval polling)
- `main/api/worker_executor.py` (workflow execution, HIL support)
- `main/api/job_repository.py` (database operations)
- `main/api/observability.py` (Langfuse configuration)
- `main/api/models.py` (JobRecord, JobStatus, ApprovalRecord)
- `main/src/exceptions.py` (HumanApprovalRequired exception)
- `main/src/events.py` (Event definitions)
- `main/src/core/unified_workflow.py` (Main workflow)
- `PRPs/tasks/3.15-hil-integration-fixes.md` (Task specification)

---

**Research Status: COMPLETE**
All three issues thoroughly researched with implementation patterns, code examples, and pharmaceutical compliance requirements documented.

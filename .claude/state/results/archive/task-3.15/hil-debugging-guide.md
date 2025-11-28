# HIL Workflow - Debugging & Troubleshooting Guide

**Purpose:** Step-by-step debugging procedures for common HIL issues
**Date:** 2025-11-26

---

## Issue #1: 404 "Job Not Found" on Approval Endpoint

### Symptom
```
POST /jobs/{job_id}/approval → 404 Not Found
GET /jobs/{job_id} → 404 Not Found
But job exists in worker traces
```

### Root Cause Analysis

#### Step 1: Verify Database Connectivity
```bash
# Check if DATABASE_URL is set
echo $DATABASE_URL

# Test direct PostgreSQL connection
psql postgresql://user:pass@localhost/testdb \
  -c "SELECT COUNT(*) FROM jobs;"

# Expected: Returns count > 0
```

#### Step 2: Check Connection Pool Status
```python
# Add to app.py lifespan:
@asynccontextmanager
async def lifespan(app: FastAPI):
    db_job_repo = await initialize_database_repository(database_url)

    # Log pool status
    pool_info = {
        "size": db_job_repo._pool.get_size(),
        "idle": db_job_repo._pool.get_idle_size(),
        "max_size": db_job_repo._pool.get_max_size(),
        "min_size": db_job_repo._pool.get_min_size(),
    }
    logger.info(f"Connection pool initialized: {pool_info}")

    yield

    # Check final pool state
    logger.info(f"Final pool state: {db_job_repo._pool.get_size()}")
```

**Expected Output:**
```
Connection pool initialized: {'size': 2, 'idle': 2, 'max_size': 10, 'min_size': 2}
```

**If seeing PoolEmptyError:**
```
RuntimeError: Pool is empty. Maximum pool size reached.
```

**Fix:** Increase max_size:
```python
pool = await asyncpg.create_pool(
    database_url,
    min_size=2,
    max_size=20,  # Increase from 10
    command_timeout=60
)
```

#### Step 3: Debug Job Query Directly
```python
# In GET /jobs/{job_id}:
async def get_job_status(job_id: str, db_job_repo: DbJobRepositoryDep):
    logger.info(f"[DEBUG] Query job: id={job_id}, type={type(job_id)}")

    # Try database
    try:
        job = await db_job_repo.get(job_id)
        logger.info(f"[DEBUG] Database result: {job}")

        if job is None:
            # Log what jobs DO exist
            all_jobs = await db_job_repo.get_jobs_by_user("*")
            logger.info(f"[DEBUG] Jobs in database: {[j.job_id for j in all_jobs]}")

            raise HTTPException(status_code=404, detail="Job not found")

        return job

    except Exception as e:
        logger.exception(f"[DEBUG] Database query failed: {e}")
        raise
```

#### Step 4: Check UUID vs String Consistency
```python
# In job creation:
job_id = str(uuid.uuid4())  # ✅ Always string
logger.info(f"Created job_id: {job_id}, type: {type(job_id)}")

# In database query:
row = await conn.fetchrow(
    "SELECT * FROM jobs WHERE job_id = $1",
    UUID(job_id)  # ✅ Convert string to UUID for query
)

# In response:
return JobRecord(job_id=str(row['job_id']))  # ✅ Convert back to string
```

#### Step 5: Verify Database Transactions
```python
# Check if update actually commits
async def set_approval_status(job_id: str, status: str, pool: asyncpg.Pool):
    logger.info(f"[BEFORE] Updating job {job_id} to {status}")

    async with pool.acquire() as conn:
        async with conn.transaction():
            # Check before update
            before = await conn.fetchrow(
                "SELECT status FROM jobs WHERE job_id = $1",
                UUID(job_id)
            )
            logger.info(f"[DEBUG] Before update: status={before['status']}")

            # Update
            await conn.execute(
                "UPDATE jobs SET status = $2, updated_at = NOW() WHERE job_id = $1",
                UUID(job_id), status
            )

            # Check after update (within same transaction)
            after = await conn.fetchrow(
                "SELECT status FROM jobs WHERE job_id = $1",
                UUID(job_id)
            )
            logger.info(f"[DEBUG] After update: status={after['status']}")

    # Check after transaction commits
    async with pool.acquire() as conn:
        final = await conn.fetchrow(
            "SELECT status FROM jobs WHERE job_id = $1",
            UUID(job_id)
        )
        logger.info(f"[AFTER] Final status in database: {final['status']}")
```

### Solution Checklist
- [ ] DATABASE_URL environment variable is set
- [ ] PostgreSQL service is running and accessible
- [ ] Connection pool not exhausted (idle_size > 0)
- [ ] Job ID type is consistent (always string in API, convert to UUID for queries)
- [ ] Database transactions commit successfully
- [ ] Job created in database (not just in-memory dict)

---

## Issue #2: Multiple Langfuse Traces per Workflow

### Symptom
```
Same job_id appears as 3-4 separate traces in Langfuse dashboard
Expected: 1 trace with nested spans
Actual: Multiple root traces
```

### Debug Steps

#### Step 1: Verify Parent Span Creation
```python
# In worker.py _process_job_with_retries:
trace_id = f"job_{job.job_id}"
logger.info(f"[TRACE] Creating parent span with trace_id={trace_id}")

parent_span = langfuse.start_span(
    name="process_job_with_retries",
    trace_id=trace_id,  # ✅ Same trace_id for all steps
)
```

#### Step 2: Check Child Spans Nesting
```python
# ❌ WRONG: Each span creates new trace
span1 = langfuse.start_span(name="categorize", trace_id=f"job_{job_id}")
span1.end()

span2 = langfuse.start_span(name="hil_approval", trace_id=f"job_{job_id}")
span2.end()

# ✅ CORRECT: Child spans nest under parent
parent = langfuse.start_span(name="process_job", trace_id=f"job_{job_id}")

child1 = parent.start_child_span(name="categorize")
child1.end()

child2 = parent.start_child_span(name="hil_approval")
child2.end()

parent.end()
```

#### Step 3: Check Flush Frequency
```python
# ❌ WRONG: Flush after each span
span = langfuse.start_span(name="step1")
span.end()
langfuse.flush()  # ← Causes separate trace

# ✅ CORRECT: Flush once at end
parent = langfuse.start_span(name="workflow")
child1 = parent.start_child_span(name="step1")
child1.end()
child2 = parent.start_child_span(name="step2")
child2.end()
parent.end()
langfuse.flush()  # ← Single flush at end
```

#### Step 4: Enable Langfuse Debug Logging
```python
import logging
logging.getLogger("langfuse").setLevel(logging.DEBUG)

# Run workflow
result = await _process_job_with_retries(job, ...)

# Should see:
# DEBUG: Creating span with trace_id=job_abc123
# DEBUG: Creating child span categorize
# DEBUG: Flushing trace job_abc123
```

#### Step 5: Verify Span Output Serialization
```python
# ❌ WRONG: Output with non-serializable objects
span.update(output={
    "file": file_handle,  # ❌ Non-serializable
    "connection": db_conn
})

# ✅ CORRECT: Only serializable output
span.update(output={
    "filename": "test.yaml",
    "gamp_category": 4,
    "test_count": 42
})
```

### Solution Checklist
- [ ] All spans have same trace_id for given job
- [ ] Child spans created with `parent.start_child_span()` not `langfuse.start_span()`
- [ ] Single `langfuse.flush()` call at end of workflow, not after each span
- [ ] Span output contains only JSON-serializable data
- [ ] No duplicate `trace_id` assignments within single workflow
- [ ] Check Langfuse dashboard for span hierarchy

---

## Issue #3: Worker Doesn't Resume After Approval

### Symptom
```
Job approved via POST /jobs/{job_id}/approval → 200 OK
Worker logs show AWAITING_APPROVAL but never move to approved
Expected: Job completed with human category
Actual: Job stays in AWAITING_APPROVAL or APPROVED state indefinitely
```

### Debug Steps

#### Step 1: Verify Approval Persisted to Database
```python
# After POST /jobs/{job_id}/approval returns 200:
# Check database directly

SELECT job_id, status, human_category, approval_timeout_at, updated_at
FROM jobs
WHERE job_id = '{job_id}';

-- Expected output:
-- job_id         | status   | human_category | approval_timeout_at | updated_at
-- abc123...      | approved | 4              | NULL                | 2025-11-26 ...
```

#### Step 2: Check Worker is Polling
```python
# In worker.py logs, look for:
logger.info(f"[HIL] Starting approval polling for job {job_id}")
logger.info(f"[HIL] Job {job_id} still awaiting approval (poll #{poll_count}, ...)")

# If not seeing "approval polling" message:
# → Worker never called _wait_for_hil_approval()
# → Check if categorization result marked review_required=True
```

#### Step 3: Verify Polling Mode
```python
# Worker should log which polling mode:
logger.info(f"[HIL] Starting approval polling for job {job_id}")
logger.info(f"  Mode: PostgreSQL (docker-compose)")  # ✅ Correct

# If seeing:
logger.info(f"  Mode: in-memory (local)")  # ❌ Wrong - HIL won't work in docker-compose
```

**Fix:** Ensure `db_job_repo` passed to worker:
```python
# In app.py lifespan:
worker_task = asyncio.create_task(
    process_job_worker(
        job_queue=job_queue,
        job_repository=job_repository,
        job_lock=job_lock,
        db_job_repo=db_job_repo  # ← Must be passed!
    )
)
```

#### Step 4: Check Polling Loop Logic
```python
# In worker.py _wait_for_hil_approval:
# Add detailed logging:

poll_count = 0
while datetime.now(UTC) < timeout_at:
    poll_count += 1
    await asyncio.sleep(poll_interval_seconds)

    logger.info(f"[HIL-POLL] Poll #{poll_count} for job {job_id}")

    # Get job from database
    current_job = await db_job_repo.get(job_id)
    logger.info(f"[HIL-POLL] Status: {current_job.status}, Category: {current_job.human_category}")

    if current_job.status == JobStatus.APPROVED:
        logger.info(f"[HIL-APPROVED] Returning True")
        return True

    # Continue polling
    if poll_count % 5 == 0:
        logger.info(f"[HIL-POLL] Still awaiting (poll #{poll_count})")
```

**Expected log output:**
```
[HIL] Starting approval polling for job abc123
  Poll interval: 2s
  Timeout: 3600s
  Mode: PostgreSQL (docker-compose)

[HIL-POLL] Poll #1 for job abc123
[HIL-POLL] Status: awaiting_approval, Category: None

[HIL-POLL] Poll #2 for job abc123
[HIL-POLL] Status: approved, Category: 4
[HIL-APPROVED] Returning True
```

#### Step 5: Check Timeout Logic
```python
# Worker should auto-reject on timeout:
logger.warning(f"[HIL] Job {job_id} approval TIMEOUT after {poll_count} polls")

# Check if timeout was actually reached
# or if worker crashed before timeout logic
```

#### Step 6: Test End-to-End with Logging
```bash
# Terminal 1: Run API
export DATABASE_URL="postgresql://user:pass@localhost/testdb"
uvicorn main.api.app:app --reload

# Terminal 2: Monitor API logs
tail -f app.log | grep -E "\[HIL\]|\[DB\]|CRITICAL"

# Terminal 3: Submit job
curl -X POST http://localhost:8000/jobs \
  -H "Authorization: Bearer <token>" \
  -F "file=@test.urs"

# Copy job_id from response
JOB_ID="..."

# Wait for AWAITING_APPROVAL status
curl http://localhost:8000/jobs/$JOB_ID \
  -H "Authorization: Bearer <token>"

# Monitor worker logs for polling
tail -f worker.log | grep -E "\[HIL\]"

# Terminal 4: Approve job
curl -X POST http://localhost:8000/jobs/$JOB_ID/approval \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "approval_decision": "approve",
    "human_category": 4,
    "justification": "Test approval"
  }'

# Monitor worker logs for resume
tail -f worker.log | grep -E "\[HIL-APPROVED\]|completed"
```

### Solution Checklist
- [ ] Job status updated to APPROVED in database
- [ ] Worker receives db_job_repo in lifespan
- [ ] Worker logs show "PostgreSQL (docker-compose)" polling mode
- [ ] Worker logs show polling continuing after approval
- [ ] Polling detects status change and returns True
- [ ] Workflow resumes with human_category

---

## Issue #4: Async Event Loop Blocking

### Symptom
```
Worker stops processing jobs
API requests hang or timeout
Langfuse traces never complete
```

### Root Cause
Synchronous blocking operations on async event loop

### Debug Steps

#### Step 1: Check for Blocking Operations
```python
# ❌ WRONG: Blocking I/O on event loop
def slow_operation():
    time.sleep(5)  # ← Blocks entire event loop!

result = slow_operation()  # Other tasks frozen for 5 seconds

# ✅ CORRECT: Use async sleep
await asyncio.sleep(5)  # Other tasks can run

# ✅ CORRECT: Use run_in_threadpool for sync ops
result = await run_in_threadpool(slow_operation)
```

#### Step 2: Check Event Loop Health
```python
# Add event loop monitoring:
import asyncio

async def log_event_loop_stats():
    while True:
        await asyncio.sleep(10)

        loop = asyncio.get_event_loop()
        logger.info(f"Event loop health:")
        logger.info(f"  Running tasks: {len(asyncio.all_tasks())}")
        logger.info(f"  Pending tasks: {len([t for t in asyncio.all_tasks() if not t.done()])}")

# In app.py lifespan:
asyncio.create_task(log_event_loop_stats())
```

**Expected output (healthy):**
```
Event loop health:
  Running tasks: 2
  Pending tasks: 1
```

**Unhealthy signs:**
```
Event loop health:
  Running tasks: 100+
  Pending tasks: 50+
```

#### Step 3: Profile Worker Task Duration
```python
# Wrap workflow execution with timing:
import time

start = time.time()
result = await executor.execute_workflow(
    job_id=job.job_id,
    urs_content=urs_content,
    user_id=job.user_id,
    approved_category=approved_category
)
duration = time.time() - start

logger.info(f"Workflow execution: {duration:.1f}s")

# If duration > 10 seconds consistently:
# → Check for blocking calls in workflow
# → Profile with cProfile
```

#### Step 4: Check Connection Pool Blocking
```python
# Connection pool queries can block if misconfigured
async with pool.acquire() as conn:
    # This should be <100ms
    start = time.time()
    row = await conn.fetchrow("SELECT * FROM jobs WHERE job_id = $1", job_id)
    duration = time.time() - start

    if duration > 1.0:
        logger.warning(f"Slow database query: {duration:.3f}s")
```

### Solution Checklist
- [ ] All I/O operations are async (await asyncio.sleep, await db.query)
- [ ] No time.sleep() calls in async functions
- [ ] Database queries <100ms
- [ ] Workflow execution <10 minutes
- [ ] Event loop task count stable (not growing)

---

## Issue #5: Langfuse Never Receives Traces

### Symptom
```
No traces in Langfuse dashboard
Worker/API logs show span.end() called
Expected: Traces visible in Langfuse
Actual: Dashboard empty
```

### Debug Steps

#### Step 1: Check Langfuse Credentials
```python
# Verify environment variables:
import os

print(f"LANGFUSE_PUBLIC_KEY: {os.getenv('LANGFUSE_PUBLIC_KEY', 'NOT SET')}")
print(f"LANGFUSE_SECRET_KEY: {os.getenv('LANGFUSE_SECRET_KEY', 'NOT SET')}")
print(f"LANGFUSE_HOST: {os.getenv('LANGFUSE_HOST', 'https://cloud.langfuse.com')}")

# Check for any typos or empty strings
```

#### Step 2: Enable Langfuse Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("langfuse").setLevel(logging.DEBUG)
logging.getLogger("httpx").setLevel(logging.DEBUG)

# Run a simple span
langfuse = Langfuse()
span = langfuse.start_span(name="test")
span.update(output={"result": "success"})
span.end()
langfuse.flush()

# Should see:
# DEBUG:httpx: POST https://cloud.langfuse.com/api/public/traces
# DEBUG:langfuse: Trace sent successfully
```

#### Step 3: Check Network Connectivity
```bash
# Test direct connection to Langfuse
curl -v https://cloud.langfuse.com/api/public/traces \
  -H "Authorization: Bearer <PUBLIC_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"trace_id": "test123"}'

# Should return 200/400 (not timeout or connection error)
```

#### Step 4: Verify Flush Happens
```python
# Langfuse buffers traces, only sends on flush()
span = langfuse.start_span(name="test")
span.end()

# Traces NOT sent yet - only buffered
logger.info("Span ended, flushing...")

langfuse.flush()  # ← This actually sends to Langfuse

logger.info("Flush completed")

# If flush() doesn't complete:
# → Check network timeout
# → Check Langfuse credentials
# → Check rate limiting
```

#### Step 5: Check for Exceptions in Span Operations
```python
# Wrap span operations with try-catch:
try:
    span = langfuse.start_span(name="test", trace_id="test123")
    span.update(output={"result": "success"})
    span.end()
    langfuse.flush()
    logger.info("Span sent successfully")
except Exception as e:
    logger.exception(f"Langfuse error: {e}")
```

### Solution Checklist
- [ ] LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY set correctly
- [ ] LANGFUSE_HOST points to correct server (not typo)
- [ ] Network connectivity to Langfuse endpoint works
- [ ] langfuse.flush() called and completes
- [ ] No exceptions in span operations
- [ ] Span trace_id format is valid (32 lowercase hex chars)

---

## Quick Reference: Common Fixes

| Issue | Quick Fix | Verify |
|-------|-----------|--------|
| 404 on approval | Check DATABASE_URL set, pool not exhausted | `SELECT * FROM jobs WHERE job_id = '...'` |
| Multiple traces | Nest spans with `parent.start_child_span()` | Single trace in Langfuse with nested children |
| Worker not resuming | Pass `db_job_repo` to worker in lifespan | Worker logs: "PostgreSQL (docker-compose)" |
| Approval not persisted | Check transaction commits | Check database directly before polling |
| Langfuse empty | Call `langfuse.flush()` | Check DEBUG logs for HTTP POST |
| Event loop hung | Check for `time.sleep()`, use `await asyncio.sleep()` | Event loop task count stable |

---

## Emergency Debugging: Full Trace

If all else fails, enable everything:

```python
# In app.py:
import logging
import sys

# Maximum verbosity
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)

# Enable all module logging
logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger("asyncio").setLevel(logging.DEBUG)
logging.getLogger("asyncpg").setLevel(logging.DEBUG)
logging.getLogger("langfuse").setLevel(logging.DEBUG)
logging.getLogger("httpx").setLevel(logging.DEBUG)

# Run workflow with maximum diagnostics
```

This will show:
- Every database query (asyncpg logs)
- Every HTTP request (httpx logs)
- Every trace operation (langfuse logs)
- Every async operation (asyncio logs)

**Warning:** This generates ~1MB logs per request. Use only for debugging specific jobs.

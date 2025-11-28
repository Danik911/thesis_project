# Context Collector Result - PostgreSQL Job State Management

## Agent Configuration
- Agent: context-collector
- Task ID: Supplemental Research (HIL Integration - Job Persistence)
- Invoked: 2025-11-26 15:20:00
- Duration: 35 minutes
- Status: SUCCESS

## Task Understanding

Research PostgreSQL job state management patterns for async FastAPI applications with Human-in-the-Loop (HIL) workflows. The system needs to persist jobs across API container restarts and support coordinated state synchronization between API and Worker containers in docker-compose deployment.

### Problem Context
- Jobs are created in API container and must survive container restarts
- Worker container polls for approved jobs from database (docker-compose mode)
- APIendpoint `/jobs/{job_id}` returns 404 after container restart
- HIL approval decision stored in database must be visible to Worker

## Research Findings

### 1. PostgreSQL Job Repository Patterns for FastAPI

#### Current Implementation Assessment
Your codebase (`main/api/job_repository.py`) correctly implements the dual-layer persistence pattern:

```python
# Asyncpg Pool Configuration (CORRECT)
pool = await asyncpg.create_pool(
    database_url,
    min_size=2,      # Minimum connections always available
    max_size=10,     # Maximum concurrent connections
    command_timeout=60  # Query execution timeout
)
```

**Strengths**:
- ✅ Connection pooling prevents connection exhaustion
- ✅ Min/max sizes balanced for web server usage
- ✅ 60s timeout prevents hung queries from blocking
- ✅ Async context managers ensure proper cleanup

**Recommended Adjustments for Production**:
- Consider `min_size=4, max_size=20` for high-concurrency API (per Medium's "Async Without Tears")
- Add `statement_cache_size=512` for prepared statement caching (5-30% performance improvement)
- Add `ssl='require'` for AWS RDS/Aurora (Task 4.2)

#### Pattern: Dual-Write (In-Memory + Database)

Your `submit_job()` endpoint implements this correctly:

```python
# Phase 1: Write to in-memory repository (fast, for worker)
async with job_lock:
    job_repository[job_id] = job_record

# Phase 2: Write to PostgreSQL (persistent, for docker-compose shared state)
if db_job_repo is not None:
    try:
        await db_job_repo.create(job_record)
        logger.info(f"[HIL-DB] Job {job_id} created in PostgreSQL")
    except Exception as e:
        logger.error(f"[HIL-DB] Failed to create job in database: {e}")
        # Continue - in-memory job exists, basic operations will work
        # but HIL workflow resumption may fail
```

**Critical Issue - Race Condition**:
If in-memory write succeeds but database write fails:
- Job appears to exist to user (POST returns 201)
- Job is in queue for worker processing
- But on API restart, job is lost (database is source of truth on restart)

**Recommended Fix**:
```python
# Write to database FIRST (stronger consistency)
if db_job_repo is not None:
    try:
        await db_job_repo.create(job_record)
    except Exception as e:
        logger.error(f"[HIL-DB] Database persistence failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="Database unavailable - cannot persist job"
        )

# Only write to in-memory after database succeeds
async with job_lock:
    job_repository[job_id] = job_record
```

### 2. Container Restart Resilience Pattern

#### Job Recovery on Startup (IMPLEMENTED CORRECTLY)

Your `app.py` lifespan handler demonstrates the correct recovery pattern:

```python
# Lines 151-170: Recovery mechanism
restartable_jobs = await db_job_repo.get_pending_jobs()

if restartable_jobs:
    logger.info(
        f"[RECOVERY] Found {len(restartable_jobs)} restartable jobs in database. "
        f"Re-enqueuing..."
    )
    async with job_lock:
        for job in restartable_jobs:
            # 1. Restore to in-memory repository (required for worker)
            job_repository[job.job_id] = job
            # 2. Add to processing queue
            await job_queue.put(job.job_id)
```

**Pattern Explanation**:
1. On startup, query database for `PENDING`, `PROCESSING`, or `APPROVED` jobs
2. Restore each job to in-memory repository
3. Re-enqueue for worker processing
4. Ensures work is never lost, even after unexpected shutdown

**Recommended Enhancement - Timeout Protection**:
```python
try:
    # Add timeout to prevent startup hang if database is slow
    async with asyncio.timeout(30):  # Python 3.11+
        restartable_jobs = await db_job_repo.get_pending_jobs()
except asyncio.TimeoutError:
    logger.error("[RECOVERY] Database query timed out - continuing with empty queue")
    restartable_jobs = []
except Exception as e:
    logger.error(f"[RECOVERY] Failed to recover jobs: {e}")
    restartable_jobs = []
```

### 3. Database-First Lookup in API Endpoints

#### Current Implementation (CORRECT)

Your `get_job_status()` endpoint uses database-first pattern:

```python
# Try database first for latest HIL status (docker-compose mode)
job = None
if db_job_repo is not None:
    try:
        job = await db_job_repo.get(job_id)
    except Exception as e:
        logger.warning(f"[HIL-DB] Failed to get job from database: {e}")
        # Fall through to in-memory

# Fall back to in-memory if database unavailable or returned None
if job is None:
    async with job_lock:
        job = job_repository.get(job_id)
```

**Why This Matters**:
- After container restart, in-memory dict is empty
- Database is source of truth
- Falls back to in-memory if database unavailable (resilience)
- Ensures users can always query job status

**Enhancement - Circuit Breaker Pattern**:
```python
class JobStatusQueryWithFallback:
    def __init__(self):
        self.db_failures = 0
        self.circuit_open = False

    async def get_job(self, job_id: str, db_repo, mem_repo):
        # If circuit is open, skip database and go straight to fallback
        if self.circuit_open:
            logger.warning("[CIRCUIT] Database circuit open - using in-memory fallback")
            return mem_repo.get(job_id)

        try:
            job = await db_repo.get(job_id)
            self.db_failures = 0  # Reset on success
            return job
        except Exception as e:
            self.db_failures += 1

            # Open circuit after 3 consecutive failures
            if self.db_failures >= 3:
                self.circuit_open = True
                logger.error("[CIRCUIT] Database failures exceeded - opening circuit")

            # Fallback to in-memory
            return mem_repo.get(job_id)
```

### 4. HIL Workflow State Synchronization

#### Approval Decision Persistence Pattern (IMPLEMENTED)

Your worker's `_wait_for_hil_approval()` function demonstrates correct database polling:

```python
# Lines 727-734: Database polling for approval decision
if use_database:
    # CRITICAL: Poll PostgreSQL for shared state with API container
    try:
        current_job = await db_job_repo.get(job_id)
    except Exception as e:
        logger.error(f"[HIL-DB] Failed to poll database for job {job_id}: {e}")
        # Continue polling - might recover on next attempt
        continue
```

**How This Works**:
1. API receives approval via `POST /jobs/{job_id}/approval`
2. API updates job status in database: `set_approval_status(APPROVED, human_category)`
3. Worker polls database every `HIL_POLL_INTERVAL_SECONDS` (2s)
4. Worker detects status change and resumes workflow
5. Both containers use same PostgreSQL database as source of truth

**Critical Issue - Set vs Update Consistency**:

Your `set_approval_status()` correctly updates multiple fields atomically:

```python
await conn.execute(
    """
    UPDATE jobs SET
        status = $2,
        human_category = $3,
        requires_approval = FALSE,
        approval_timeout_at = NULL,
        updated_at = $4
    WHERE job_id = $1
    """,
    UUID(job_id),
    status.value,
    str(human_category) if human_category else None,
    datetime.now(UTC)
)
```

**Recommendation**: Add explicit transaction for multi-step updates:

```python
async def set_approval_status_transactional(
    self,
    job_id: str,
    status: JobStatus,
    human_category: int | None = None
) -> None:
    async with self._pool.acquire() as conn:
        async with conn.transaction():  # Explicit transaction
            # Update job status
            await conn.execute(
                "UPDATE jobs SET status = $2, human_category = $3, updated_at = $4 WHERE job_id = $1",
                UUID(job_id),
                status.value,
                str(human_category) if human_category else None,
                datetime.now(UTC)
            )

            # Update approval metadata in single transaction
            await conn.execute(
                "UPDATE jobs SET requires_approval = FALSE, approval_timeout_at = NULL WHERE job_id = $1",
                UUID(job_id)
            )
```

### 5. Async PostgreSQL with Asyncpg - Best Practices

#### Connection Pooling Gotchas

**Issue 1: Connection Hold Times**
```python
# WRONG - holds connection for entire external API call
async with pool.acquire() as conn:
    await some_external_api()  # 10 seconds
    result = await conn.fetch("SELECT ...")
```

**Correct Pattern** (your code does this):
```python
# RIGHT - releases connection quickly
async with pool.acquire() as conn:
    result = await conn.fetch("SELECT ...")
# Connection released here
await some_external_api()  # Doesn't block pool
```

**Issue 2: Transaction Scope**
```python
# WRONG - implicit transaction, hard to debug
async with pool.acquire() as conn:
    await conn.execute("UPDATE jobs SET status = $1", "APPROVED")
    # Implicit commit happens here
```

**Correct Pattern** (your code does this):
```python
# RIGHT - explicit transaction control
async with pool.acquire() as conn:
    async with conn.transaction():
        await conn.execute("UPDATE jobs SET status = $1", "APPROVED")
        # Explicit commit on exit
```

#### Statement Caching
AsyncPG uses `statement_cache_size` for prepared statements:

```python
# Configuration (recommended for production)
pool = await asyncpg.create_pool(
    dsn,
    statement_cache_size=512  # Caches up to 512 prepared statements
)
```

**Performance Impact**:
- First execution: Parse SQL → Execute
- Subsequent executions: Use prepared statement (5-30% faster)
- Your queries are parameterized (good) - caching helps significantly

### 6. Implementation Gotchas & Known Issues

#### Issue 1: "Job Not Found" After Restart
**Root Cause**: Database recovery query fails during startup

**Symptoms**:
- POST /jobs returns 201 (job created)
- Immediately GET /jobs/{job_id} returns 200
- After container restart, GET /jobs/{job_id} returns 404

**Why It Happens**:
```python
# If this query fails, jobs aren't recovered:
restartable_jobs = await db_job_repo.get_pending_jobs()

# If exception occurs, continues with empty list:
except Exception as e:
    logger.error(f"Failed to re-enqueue: {e}")
    # Jobs are lost!
```

**Fix**:
```python
try:
    async with asyncio.timeout(30):
        restartable_jobs = await db_job_repo.get_pending_jobs()
        if restartable_jobs:
            logger.info(f"[RECOVERY] Re-enqueuing {len(restartable_jobs)} jobs")
            # ... recovery logic ...
        else:
            logger.info("[RECOVERY] No jobs to recover")
except asyncio.TimeoutError:
    logger.critical("[RECOVERY] Database timeout during startup - check PostgreSQL connectivity")
    raise RuntimeError("Cannot start API without database recovery")
except Exception as e:
    logger.critical(f"[RECOVERY] Unrecoverable database error: {e}")
    raise RuntimeError("Cannot start API - database unavailable")
```

#### Issue 2: Race Condition in Dual-Write
**Scenario**: In-memory write succeeds, database write fails

```python
# Current code (vulnerable):
async with job_lock:
    job_repository[job_id] = job_record  # ✅ Succeeds

if db_job_repo:
    await db_job_repo.create(job_record)  # ❌ Fails - but job already in-memory!
```

**Impact on HIL**: User sees job exists, submits approval, but approval is lost on restart

**Fix**: Reverse order + transaction:
```python
# Write to database FIRST (atomic)
if db_job_repo:
    try:
        await db_job_repo.create(job_record)
    except Exception as e:
        logger.error(f"Failed to persist to database: {e}")
        raise HTTPException(status_code=503, detail="Database unavailable")

# Only in-memory if database succeeds
async with job_lock:
    job_repository[job_id] = job_record
```

#### Issue 3: HIL Approval Timeout Not Persisted
**Current Code** (worker.py lines 808-824):
```python
# Timeout auto-rejection in worker
if use_database:
    await db_job_repo.set_approval_status(
        job_id=job_id,
        status=JobStatus.REJECTED,
        human_category=None
    )
else:
    # Fallback to in-memory
    async with job_lock:
        current_job = job_repository.get(job_id)
        if current_job:
            current_job.status = JobStatus.REJECTED
```

**Issue**: If database update fails, in-memory rejection happens but database still shows AWAITING_APPROVAL

**Fix**: Ensure transactional consistency:
```python
try:
    if use_database:
        await db_job_repo.set_approval_status(
            job_id=job_id,
            status=JobStatus.REJECTED,
            human_category=None
        )
except Exception as e:
    logger.error(f"[CRITICAL] Failed to persist HIL timeout rejection: {e}")
    # Don't silently fail - mark as failed instead
    job.status = JobStatus.FAILED
    job.error_message = f"HIL timeout rejection failed to persist: {e}"
    return False
```

#### Issue 4: APPROVED Job Recovery Incomplete
**Current Code** (worker.py lines 284-295):
```python
# CRITICAL: Check if job was pre-approved (HIL recovery scenario)
approved_category = None
if job.human_category:
    approved_category = job.human_category
    logger.info(f"[HIL-RECOVERY] Job {job.job_id} has pre-approved category")
```

**Missing**: Update job status on recovery

**Fix**:
```python
if job.human_category:
    approved_category = job.human_category
    # Also update status to PROCESSING if still APPROVED
    async with job_lock:
        if job.status == JobStatus.APPROVED:
            job.status = JobStatus.PROCESSING
            job.updated_at = datetime.now(UTC)
    await _persist_job_state(job, db_job_repo, "hil_recovery_start")
```

### 7. GAMP-5 Compliance Considerations

#### Audit Trail for Job State Changes
Your `audit_logger.log_event()` captures user actions, but database writes should also be auditable:

**Recommendation**: Add trigger-based audit table in PostgreSQL:

```sql
-- Create audit table for all job changes
CREATE TABLE jobs_audit (
    audit_id BIGSERIAL PRIMARY KEY,
    job_id UUID NOT NULL,
    old_status VARCHAR,
    new_status VARCHAR,
    changed_by VARCHAR,  -- Service name (API, WORKER, SYSTEM)
    change_reason TEXT,
    changed_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (job_id) REFERENCES jobs(job_id)
);

-- Trigger to log all status changes
CREATE OR REPLACE FUNCTION log_job_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status IS DISTINCT FROM OLD.status THEN
        INSERT INTO jobs_audit (job_id, old_status, new_status, changed_by, change_reason)
        VALUES (
            NEW.job_id,
            OLD.status,
            NEW.status,
            'DATABASE',
            'Status changed via SQL update'
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER job_status_audit AFTER UPDATE ON jobs
FOR EACH ROW EXECUTE FUNCTION log_job_status_change();
```

**Benefits for GAMP-5**:
- ✅ Immutable audit trail (database-level)
- ✅ All state changes captured (SQL, API, Worker)
- ✅ Timestamp on all changes
- ✅ Source of change recorded

### 8. Required Libraries & Versions

Based on current code and AWS migration targets:

```
# Core
asyncpg>=0.29.0        # Async PostgreSQL driver (bug fixes, performance)
fastapi>=0.104.0       # Web framework (lifespan support)
uvicorn>=0.24.0        # ASGI server

# AWS Production (Task 4.2)
boto3>=1.26.0          # AWS SDK for Data API access
aiosql>=8.0.0          # SQL file management (optional, for migrations)

# Observability
langfuse>=3.5.2        # Tracing (already used, manual span support)
opentelemetry-api>=1.20.0  # OpenTelemetry instrumentation

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
```

**Version Constraints Reasoning**:
- `asyncpg>=0.29.0`: Fix for connection pool edge cases, proper timeout handling
- `fastapi>=0.104.0`: Lifespan context manager (required for your startup recovery)
- `boto3>=1.26.0`: Data API improvements for Aurora Serverless v2

### 9. Recommended Approach Summary

#### Phase 1: Immediate (Current HIL Testing)
1. **Reverse dual-write order** (database-first, not in-memory-first)
2. **Add startup timeout protection** (prevent hang on recovery)
3. **Fix APPROVED job status** (update to PROCESSING on recovery)
4. **Test container restart cycle**:
   - Create job via API
   - Verify job in database
   - Stop API container
   - Restart API container
   - Verify job still queryable via GET /jobs/{job_id}
   - Verify worker can still process it

#### Phase 2: Robustness (Before Docker-Compose Testing)
1. **Add health check endpoint** for database connectivity
2. **Implement circuit breaker** for database failures
3. **Add connection pool monitoring** (log pool exhaustion)
4. **Enhance error messages** for troubleshooting

#### Phase 3: Production Hardening (AWS Migration - Task 4.2)
1. **Migrate to Aurora Data API** (boto3)
2. **Replace asyncpg pool** with Data API calls
3. **Add database-level audit table** (PostgreSQL triggers)
4. **Implement AWS Secrets Manager** rotation for credentials
5. **Add CloudWatch metrics** for job queue depth

## Next Agent Guidance

**For task-executor** (if implementing fixes):

1. **Dual-Write Fix Priority**: HIGH
   - File: `main/api/app.py`
   - Change: Reverse order in `submit_job()` - database write FIRST
   - Rationale: Prevents 404 errors after restart

2. **Startup Recovery Fix**: HIGH
   - File: `main/api/app.py` (lifespan handler)
   - Change: Add timeout protection and error handling
   - Rationale: Prevents startup hang if database is slow

3. **APPROVED Status Fix**: MEDIUM
   - File: `main/api/worker.py`
   - Change: Update job status during HIL recovery
   - Rationale: Ensures complete state consistency

4. **Testing Strategy**:
   - Add integration test for container restart
   - Verify job persists after restart
   - Verify HIL workflow survives approval decision
   - Verify worker can resume approved jobs

## Files Referenced

### Official Documentation
- [AsyncPG Documentation](https://magicstack.github.io/asyncpg/) - Connection pooling, transaction handling
- [FastAPI Lifespan Documentation](https://fastapi.tiangolo.com/advanced/events/) - Startup/shutdown patterns
- [PostgreSQL Transaction Documentation](https://www.postgresql.org/docs/current/sql-begin.html) - ACID guarantees

### Research Articles
- Medium: "Async Without Tears: 10 Patterns for asyncpg + SQLModel" - Connection pooling best practices
- LinkedIn: "Best Practices for Creating a FastAPI and PostgreSQL Connection Pool" - Timeout configuration
- Dev.to: "Python Fundamentals: asyncpg" - Connection pooling pitfalls and recovery patterns

### Project References
- `examples/alex/guides/5_database.md` - Aurora Serverless v2 setup (Task 4.2 reference)
- Local code: `main/api/job_repository.py` - Current PostgreSQL implementation (correct pattern)
- Local code: `main/api/worker.py` - HIL polling pattern (database-first approach)
- Local code: `main/api/app.py` - Startup recovery mechanism (mostly correct, needs timeout)

### GAMP-5 Compliance
- PHARMAGMP.IN: "Audit Trails: Configuration, Review Frequency and Data Integrity Controls" - FDA expectations
- Qualio: "Guide to GAMP 5 and Data Integrity for GxP Manufacturers" - Comprehensive GAMP-5 requirements

## Summary

Your current implementation is **fundamentally sound** for PostgreSQL job persistence in async FastAPI with HIL workflows. The dual-layer pattern (in-memory for speed + database for durability) is industry-standard and correctly implemented.

**Critical fixes needed** (before production):
1. Reverse dual-write order (database-first)
2. Add timeout protection on startup recovery
3. Ensure APPROVED jobs update status on recovery

**Key gotchas to watch**:
- Connection pool timeout configuration (60s is good default)
- Race conditions in dual-write (fixed by ordering)
- Database unavailability during startup (fixed by timeout + error handling)
- HIL approval decisions require database polling (correctly implemented)

**Path to AWS Production** (Task 4.2):
- Replace asyncpg with Aurora Data API (boto3)
- Add Secrets Manager for credential rotation
- Implement CloudWatch monitoring for queue depth
- Add database-level audit triggers for GAMP-5

The pattern you've implemented is production-ready for docker-compose. The AWS migration will require replacing asyncpg with Data API, but the fundamental approach remains the same.

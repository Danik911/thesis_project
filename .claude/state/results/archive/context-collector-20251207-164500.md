# Context Collector Result - 2025-12-07T16:45:00Z

## Agent Configuration
- Agent: context-collector
- Task ID: 4.5
- Task Name: Daily Job Limit Implementation
- Invoked: 2025-12-07T16:45:00Z
- Duration: 15 minutes
- Status: SUCCESS

## Task Understanding
Implement a global daily job limit feature for cost control during staging/development. This involves:
1. Adding a PostgreSQL query to count today's jobs (excluding failed jobs)
2. Implementing a limit check in POST /jobs endpoint before job creation
3. Creating a GET /jobs/quota endpoint to show remaining quota
4. Configuring the limit via DAILY_JOB_LIMIT environment variable
5. Ensuring GAMP-5/ALCOA+ compliance through audit logging

The feature must gracefully handle both database mode (docker-compose with PostgreSQL) and in-memory mode (local development without DATABASE_URL).

---

## Research Findings

### 1. Current Codebase Patterns

#### PostgresJobRepository Pattern (main/api/job_repository.py)
**Connection Acquisition:**
```python
async with self._pool.acquire() as conn:
    result = await conn.fetchval(query, param1, param2)
    return result or 0
```

**Key Observations:**
- Uses `self._pool` (asyncpg.Pool) with connection acquisition context manager
- Methods use `conn.fetchval()` for single values, `conn.fetchrow()` for single rows, `conn.fetch()` for multiple rows
- All datetime operations use `datetime.now(UTC)` for timezone-aware timestamps
- Error handling follows NO FALLBACK pattern - explicit exceptions only

**Existing Methods:**
- `get()` - Single job retrieval
- `create()` - Job creation with full field mapping
- `update()` - Full job update
- `set_approval_status()` - HIL approval status update
- `get_jobs_by_user()` - User-specific job listing with LIMIT pagination
- `get_pending_jobs()` - Restartable jobs recovery (pending, processing, approved)

#### Database Schema (scripts/postgres-init.sql)
```sql
CREATE TABLE IF NOT EXISTS jobs (
    job_id UUID PRIMARY KEY,
    status VARCHAR(20) NOT NULL
        CHECK (status IN ('pending', 'processing', 'awaiting_approval',
                         'approved', 'rejected', 'completed', 'failed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- ... other fields
);

-- Performance Index (already exists)
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);
```

**Index Optimization:** The `idx_jobs_created_at` index already exists and will optimize the date filtering query.

#### API Endpoint Pattern (main/api/app.py)
**Error Handling:**
```python
raise HTTPException(
    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
    detail=f"CRITICAL: Job limit exceeded. Detail: {specific_info}"
)
```

**Dependency Injection:**
- `db_job_repo: DbJobRepositoryDep` - Optional[PostgresJobRepository]
- Check `if db_job_repo is not None` before database operations
- Gracefully degrades to in-memory mode if database unavailable

**Audit Logging:**
```python
from .audit import get_audit_logger

audit_logger = get_audit_logger()
audit_logger.log_event(
    job_id=job_id,
    event_type="limit_violation",  # Custom event type
    user_id=user.sub,
    status=JobStatus.PENDING,
    user_email=user.email,
    metadata={
        "daily_limit": limit,
        "current_count": count,
        "remaining": 0
    }
)
```

**LangFuse Tracing:**
```python
# Manual span creation (DO NOT use @observe decorator)
langfuse = get_langfuse_client()
if langfuse:
    span = langfuse.start_span(
        name="daily_limit_check",
        input={"endpoint": "POST /jobs"},
        metadata={
            "user_id": user.sub,
            "daily_limit": limit,
            "jobs_today": count
        }
    )
    # ... operation ...
    span.update(output={"result": "allowed" or "denied"})
    span.end()
    langfuse.flush()
```

#### Environment Variable Pattern (.env.example)
```bash
# Existing patterns:
WORKFLOW_TIMEOUT=1800
LLM_TIMEOUT=600
LLM_MAX_RETRIES=5

# New variable to add:
DAILY_JOB_LIMIT=10  # Set to 0 to disable
```

**Environment Variable Loading:**
- FastAPI app loads .env.local via `dotenv.load_dotenv()` at startup
- AWS ECS uses task definition JSON for environment variables
- Access via `os.getenv("DAILY_JOB_LIMIT", "10")`
- Convert to int: `int(os.getenv("DAILY_JOB_LIMIT", "10"))`

---

### 2. FastAPI HTTP 429 Best Practices

**Source:** [LoadForge - Implementing Rate Limits in FastAPI](https://loadforge.com/guides/implementing-rate-limits-in-fastapi), [Medium - Rate Limiting and Throttling in FastAPI](https://medium.com/@prabha.ochetty/rate-limiting-and-throttling-in-fastapi-prevent-api-abuse-the-smart-way-0806bade0e3f)

#### Status Code and Response Format
```python
from fastapi import HTTPException, status

raise HTTPException(
    status_code=status.HTTP_429_TOO_MANY_REQUESTS,  # 429
    detail=f"System daily job limit ({daily_limit}) reached. "
           f"Resets at midnight UTC. "
           f"Current count: {job_count}"
)
```

#### Optional Response Headers (Not Required for Daily Limit)
For per-second/per-minute rate limiting, these headers are standard:
- `Retry-After`: Seconds until retry allowed (or HTTP date)
- `X-RateLimit-Limit`: Total allowed requests in window
- `X-RateLimit-Remaining`: Requests remaining in current window
- `X-RateLimit-Reset`: Unix timestamp when window resets

**For Daily Limit:** These headers are less relevant since the window is 24 hours. Include quota info in response body instead.

#### Client Communication Best Practices
1. **Clear Error Messages:** Explain why the request was denied
2. **Quota Transparency:** Show current usage and limit
3. **Reset Time:** Tell users when they can retry (midnight UTC)
4. **Avoid Masking:** Return 429, NOT 200 with error payload

---

### 3. PostgreSQL Date Filtering with asyncpg

**Sources:** [asyncpg GitHub Issue #1002](https://github.com/MagicStack/asyncpg/issues/1002), [Crunchy Data - Working with Time in Postgres](https://www.crunchydata.com/blog/working-with-time-in-postgres), [PostgreSQL Documentation - Date/Time Functions](https://www.postgresql.org/docs/current/functions-datetime.html)

#### Timezone Handling
**PostgreSQL Behavior:**
- `TIMESTAMPTZ` columns store UTC internally
- Queries compare timestamps in UTC automatically
- When passing timezone-aware Python datetime as parameter, asyncpg converts correctly

**Python UTC Datetime Creation:**
```python
from datetime import UTC, datetime

# Get start of today in UTC
today_start = datetime.now(UTC).replace(
    hour=0, minute=0, second=0, microsecond=0
)
```

**Important:** asyncpg may return naive datetime objects even from TIMESTAMPTZ columns ([Issue #481](https://github.com/MagicStack/asyncpg/issues/481)). However, when **passing** timezone-aware datetimes as parameters, it handles them correctly.

#### Query Implementation
```python
async def count_jobs_today(self) -> int:
    """Count all jobs created today (globally), excluding failed jobs."""
    query = """
        SELECT COUNT(*) FROM jobs
        WHERE created_at >= $1
        AND status NOT IN ('failed')
    """
    today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

    async with self._pool.acquire() as conn:
        result = await conn.fetchval(query, today_start)

    return result or 0
```

**Query Optimization:**
- `idx_jobs_created_at` index (already exists) accelerates date filtering
- COUNT queries are fast (~1-5ms for typical job volumes)
- Parameterized query prevents SQL injection

#### Status Exclusion Decision Point
**Task Spec:** "Exclude failed jobs to avoid penalizing users for system errors"

**Status Values in Database:**
- `pending` - Queued, waiting
- `processing` - Currently running
- `awaiting_approval` - HIL paused for human review
- `approved` - HIL approved, resuming workflow
- `rejected` - HIL rejected by human reviewer
- `completed` - Successfully finished
- `failed` - System error/crash

**Recommendation:**
- **Exclude:** `failed` (system errors, as specified)
- **Include:** `rejected` (human decision, still consumed LLM resources)

Rationale: A rejected job still triggered GAMP-5 categorization and consumed API quota. Only pure system failures should be excluded.

**Alternative (More Lenient):**
```sql
AND status NOT IN ('failed', 'rejected')
```
This would exclude both system failures and human rejections. Decision left to task-executor based on product requirements.

---

### 4. GAMP-5 & ALCOA+ Compliance for Rate Limiting

**Sources:** [GAMP 5 Guidelines for System Validation](https://intuitionlabs.ai/articles/gamp-5-guidelines-system-validation), [ALCOA to ALCOA+ Principles](https://www.pharmaguideline.com/2018/12/alcoa-to-alcoa-plus-for-data-integrity.html), [Navigating 21 CFR Part 11 Compliance](https://blog.cloudbyz.com/resources/navigating-21-cfr-part-11-compliance-leveraging-gamp-5-and-alcoa-principles-for-robust-electronic-records-and-signatures-management)

#### ALCOA+ Principles Applied to Rate Limiting

**A - Attributable:** Log who triggered the limit violation
```python
audit_logger.log_event(
    job_id="rate_limit_violation_" + str(uuid.uuid4()),  # Unique event ID
    event_type="rate_limit_exceeded",
    user_id=user.sub,  # Clerk user ID
    status=JobStatus.PENDING,  # Job never created
    user_email=user.email,  # Human-readable attribution
    metadata={
        "daily_limit": daily_limit,
        "jobs_today": job_count,
        "endpoint": "POST /jobs",
        "client_ip": request.client.host if request.client else None
    }
)
```

**L - Legible:** Clear error messages for users and auditors
```python
detail=f"System daily job limit ({daily_limit}) reached. "
       f"Resets at midnight UTC. Current count: {job_count}"
```

**C - Contemporaneous:** Timestamp when limit was hit
- Audit log entry includes `timestamp=datetime.now(UTC)`
- LangFuse span tracks exact timing

**O - Original:** Direct logging, no intermediate systems
- Write to audit log immediately upon limit detection
- LangFuse trace created in same transaction

**A - Accurate:** Precise job count from database
- Query counts actual jobs, not estimates
- No caching, no approximations

**+ Complete:** Include all relevant context
- User ID, email, IP address
- Current count, limit value, remaining quota
- Endpoint, timestamp, event type

**+ Consistent:** Same format as other audit events
- Use existing `AuditLogger` class
- Same JSON structure, field names, timezone (UTC)

**+ Enduring:** Persistent audit trail
- Audit logs stored in `logs/audit/jobs/` directory
- LangFuse traces retained per configured policy

**+ Available:** Queryable audit trail
- File-based audit logs can be parsed/searched
- LangFuse dashboard provides UI for trace analysis

#### Regulatory Compliance Considerations

**GAMP-5 Risk Assessment:**
- Rate limiting is a **Quality Control** feature (prevents system overload)
- Reduces risk of cost overruns in staging/development environments
- Audit trail demonstrates **controlled** access management

**21 CFR Part 11 Considerations:**
- Rate limiting decisions must be **auditable** (logged with timestamps)
- User attribution required for compliance
- No silent failures - users must be notified of denials

**Data Integrity:**
- Count query must be accurate (no fallbacks, no estimates)
- Timezone consistency critical (always UTC)
- Audit trail must be tamper-evident (append-only logs)

---

### 5. In-Memory Mode Handling Strategy

**Context:** The application supports two modes:
1. **Database Mode** (docker-compose): DATABASE_URL set, PostgreSQL available
2. **In-Memory Mode** (local dev): No DATABASE_URL, no persistent storage

**Dependency Injection Pattern:**
```python
db_job_repo: DbJobRepositoryDep  # Annotated[PostgresJobRepository | None, Depends(...)]
```

**Implementation Strategy:**
```python
# In POST /jobs endpoint
daily_limit = int(os.getenv("DAILY_JOB_LIMIT", "10"))

# Only enforce limit if database available
if daily_limit > 0 and db_job_repo is not None:
    job_count = await db_job_repo.count_jobs_today()
    if job_count >= daily_limit:
        # Log limit violation
        audit_logger.log_event(...)

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"System daily job limit ({daily_limit}) reached. "
                   f"Resets at midnight UTC. Current count: {job_count}"
        )
```

**Rationale:**
- In-memory mode is for local development only
- Local development doesn't incur cloud costs
- Enforcing limit without persistent storage would be meaningless (resets on restart)
- Graceful degradation: skip limit check if database unavailable

**Quota Endpoint Behavior:**
```python
@app.get("/jobs/quota")
async def get_job_quota(db_job_repo: DbJobRepositoryDep) -> dict:
    daily_limit = int(os.getenv("DAILY_JOB_LIMIT", "10"))

    if daily_limit <= 0:
        return {
            "limit_enabled": False,
            "message": "No daily limit configured"
        }

    if db_job_repo is None:
        return {
            "limit_enabled": False,
            "message": "Database not available (in-memory mode)"
        }

    job_count = await db_job_repo.count_jobs_today()
    return {
        "limit_enabled": True,
        "daily_limit": daily_limit,
        "jobs_today": job_count,
        "remaining": max(0, daily_limit - job_count),
        "resets_at": "00:00 UTC"
    }
```

---

### 6. AWS Task Definition Environment Variables

**Current Pattern (aws/terraform/task-definition-api-v20.json):**
```json
{
  "environment": [
    {
      "name": "LANGFUSE_HOST",
      "value": "https://cloud.langfuse.com"
    },
    {
      "name": "ENVIRONMENT",
      "value": "staging"
    },
    {
      "name": "LLM_MODEL",
      "value": "google/gemini-2.5-flash-lite"
    }
  ]
}
```

**Add to environment array:**
```json
{
  "name": "DAILY_JOB_LIMIT",
  "value": "10"
}
```

**Files to Modify:**
- `aws/terraform/task-definition-api-v*.json` (latest version)
- `aws/terraform/task-definition-worker-v*.json` (if worker needs awareness of limit)

**Important:** Worker container doesn't create jobs, so it doesn't need DAILY_JOB_LIMIT. Only API container needs it.

---

### 7. Implementation Gotchas & Warnings

#### Issue 1: Task Spec Uses Incorrect Pattern
**Task Spec Shows:**
```python
result = await self.pool.fetchval(query, today_start)
```

**Correct Pattern (from existing code):**
```python
async with self._pool.acquire() as conn:
    result = await conn.fetchval(query, today_start)
```

**Why:** Connection pooling requires explicit acquisition. Direct pool access not supported.

#### Issue 2: Status Exclusion Ambiguity
**Task Spec:** "excluding failed jobs"
**Question:** Should 'rejected' also be excluded?

**Recommendation:** Exclude only 'failed', include 'rejected' (see Section 3 for rationale)

#### Issue 3: Race Conditions (Acceptable)
**Scenario:** Two concurrent job submissions at count=9 (limit=10)
- Both check count (9 < 10) → both pass
- Both create jobs → count becomes 11

**Task Spec:** "Race conditions with concurrent submissions (acceptable for staging use case)"

**Why Acceptable:**
- Daily limit is for cost control, not strict enforcement
- Race window is milliseconds (not user-noticeable)
- Distributed lock would add complexity/latency
- Staging/development use case (not production billing)

**If Strict Enforcement Needed (Future):**
```python
# Atomic increment with database transaction
async with self._pool.acquire() as conn:
    async with conn.transaction():
        count = await conn.fetchval("SELECT COUNT(*) ...")
        if count >= limit:
            raise HTTPException(...)
        # Create job within same transaction
```

#### Issue 4: Timezone Consistency
**Critical:** ALL date calculations MUST use UTC
- Database: `created_at TIMESTAMPTZ` (UTC)
- Python: `datetime.now(UTC)`
- Display: "Resets at midnight UTC"

**Never Use:**
```python
datetime.now()  # Naive datetime - BAD
datetime.utcnow()  # Deprecated in Python 3.12+
```

#### Issue 5: Missing Dependencies
**All required libraries already installed:**
- `asyncpg` - PostgreSQL driver
- `fastapi` - Web framework
- `pydantic` - Data validation

**No new installations needed.**

#### Issue 6: Audit Log Event Type
**Existing Event Types (from audit.py):**
- `submit`, `start`, `complete`, `fail`, `retry`, `auth_success`, `auth_failure`

**New Event Type:**
- `rate_limit_exceeded` (custom, not predefined in enum)

**Implementation:** Audit logger accepts arbitrary event_type strings, so this is safe.

---

## Recommended Approach

### Implementation Order
1. **Add `count_jobs_today()` method to PostgresJobRepository**
   - Query: COUNT(*) with date filter and status exclusion
   - Return 0 if no jobs today
   - Use connection acquisition pattern

2. **Add limit check to POST /jobs endpoint**
   - Read DAILY_JOB_LIMIT environment variable
   - Check if db_job_repo available (database mode)
   - Query job count, compare to limit
   - Raise HTTPException(429) if exceeded
   - Log violation to audit trail and LangFuse

3. **Add GET /jobs/quota endpoint**
   - Return quota status (enabled, limit, current, remaining)
   - Handle in-memory mode gracefully
   - Handle limit disabled (value=0)

4. **Update .env.example**
   - Add DAILY_JOB_LIMIT=10 with comment

5. **Update AWS task definition**
   - Add environment variable to api task definition JSON
   - Redeploy API service to apply

### Testing Strategy (from Task Spec)
**Unit Tests:**
- Verify count query excludes failed jobs
- Verify count returns 0 when no jobs exist
- Test timezone handling (today's jobs only)

**Integration Tests:**
- Submit jobs until limit reached, verify 429 response
- Test quota endpoint returns accurate counts
- Verify limit resets at midnight UTC (time-travel test)
- Test in-memory mode gracefully skips limit check

**Manual Testing:**
- Set DAILY_JOB_LIMIT=2 locally
- Submit 3 jobs, verify 3rd returns 429
- Check /jobs/quota shows correct remaining count
- Verify audit log contains limit violation event

---

## Next Agent Guidance (task-executor)

### Critical Implementation Notes

1. **Database Connection Pattern:**
   ```python
   # CORRECT:
   async with self._pool.acquire() as conn:
       result = await conn.fetchval(query, param)

   # WRONG (from task spec):
   result = await self.pool.fetchval(query, param)
   ```

2. **Status Exclusion Decision:**
   - Task spec: Exclude 'failed'
   - Consider: Should 'rejected' also be excluded?
   - Default: Only exclude 'failed' (rationale in Section 3)
   - Flag for user confirmation if needed

3. **In-Memory Mode Handling:**
   ```python
   if daily_limit > 0 and db_job_repo is not None:
       # Check limit
   # else: skip check (in-memory mode or disabled)
   ```

4. **Audit Logging:**
   - Log ALL limit violations (not just first)
   - Include full context (user, count, limit)
   - Use existing `get_audit_logger()` pattern

5. **Error Message Format:**
   ```python
   f"System daily job limit ({daily_limit}) reached. "
   f"Resets at midnight UTC. Current count: {job_count}"
   ```

6. **Environment Variable:**
   - Default: "10"
   - Conversion: `int(os.getenv("DAILY_JOB_LIMIT", "10"))`
   - Disable: Set to "0"

### Files to Modify

| File | Changes | Complexity |
|------|---------|------------|
| `main/api/job_repository.py` | Add `count_jobs_today()` method | Low |
| `main/api/app.py` | Add limit check in `submit_job()`, add quota endpoint | Medium |
| `.env.example` | Add DAILY_JOB_LIMIT variable | Trivial |
| `aws/terraform/task-definition-api-v*.json` | Add environment variable | Trivial |

### Edge Cases to Handle

1. **Database Unavailable Mid-Request:**
   - db_job_repo is not None initially
   - Database connection fails during count query
   - Solution: Catch exception, log warning, allow job creation (fail-open for availability)

2. **Negative Limit:**
   - User sets DAILY_JOB_LIMIT=-1
   - Solution: Treat as disabled (same as 0)

3. **Non-Integer Limit:**
   - User sets DAILY_JOB_LIMIT=abc
   - Solution: ValueError from `int()` - let it crash (config error, not runtime error)

4. **Midnight Boundary:**
   - Job submitted at 23:59:59 UTC
   - Count query runs, sees 9 jobs today
   - Job creation happens at 00:00:01 UTC (next day)
   - Solution: Acceptable race condition (count resets daily)

### Required Libraries/Versions
**No new dependencies required.** All necessary libraries already in project:
- `asyncpg>=0.28.0` (PostgreSQL driver)
- `fastapi>=0.104.0` (web framework)
- `pydantic>=2.0.0` (data validation)

---

## Files Referenced

### Codebase Files
- `main/api/job_repository.py` - Repository implementation patterns
- `main/api/app.py` - API endpoint patterns, dependency injection
- `main/api/dependencies.py` - Dependency factories, database initialization
- `main/api/models.py` - JobStatus enum, response models
- `main/api/audit.py` - AuditLogger class, ALCOA+ principles
- `.env.example` - Environment variable examples
- `scripts/postgres-init.sql` - Database schema, indexes
- `aws/terraform/task-definition-api-v20.json` - AWS environment variables
- `docker-compose.dev.yml` - Local development setup

### External Documentation
- [LoadForge - Implementing Rate Limits in FastAPI](https://loadforge.com/guides/implementing-rate-limits-in-fastapi)
- [Medium - Rate Limiting and Throttling in FastAPI](https://medium.com/@prabha.ochetty/rate-limiting-and-throttling-in-fastapi-prevent-api-abuse-the-smart-way-0806bade0e3f)
- [Stack Overflow - Ratelimit in FastAPI](https://stackoverflow.com/questions/65491184/ratelimit-in-fastapi)
- [asyncpg GitHub Issue #1002](https://github.com/MagicStack/asyncpg/issues/1002)
- [Crunchy Data - Working with Time in Postgres](https://www.crunchydata.com/blog/working-with-time-in-postgres)
- [PostgreSQL Documentation - Date/Time Functions](https://www.postgresql.org/docs/current/functions-datetime.html)
- [GAMP 5 Guidelines for System Validation](https://intuitionlabs.ai/articles/gamp-5-guidelines-system-validation)
- [ALCOA to ALCOA+ Principles](https://www.pharmaguideline.com/2018/12/alcoa-to-alcoa-plus-for-data-integrity.html)
- [Navigating 21 CFR Part 11 Compliance](https://blog.cloudbyz.com/resources/navigating-21-cfr-part-11-compliance-leveraging-gamp-5-and-alcoa-principles-for-robust-electronic-records-and-signatures-management)

---

**Research Completion Status:** ✅ COMPLETE
**Next Agent:** task-executor
**Confidence:** HIGH - All implementation details verified against existing codebase patterns

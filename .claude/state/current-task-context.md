# Current Task Context: 4.5

## Task File
PRPs/tasks/4.5-daily-job-limit.md

## Task Content
# Task P4.5 – Daily Job Limit Implementation

## What to Do
- Implement global daily job limit to control costs during staging/development.
- Add PostgreSQL query to count today's jobs (excluding failed jobs).
- Add limit check in POST /jobs endpoint before job creation.
- Add GET /jobs/quota endpoint to show remaining quota.
- Configure limit via DAILY_JOB_LIMIT environment variable.

## Dependencies
- Requires PostgreSQL database (Task P4.2 or local docker-compose).
- Uses existing `jobs` table with `created_at` index.

## Implementation Details

### 1. Add Repository Method
File: `main/api/job_repository.py`

```python
async def count_jobs_today(self) -> int:
    """Count all jobs created today (globally), excluding failed jobs."""
    query = """
        SELECT COUNT(*) FROM jobs
        WHERE created_at >= $1
        AND status NOT IN ('failed')
    """
    today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    result = await self.pool.fetchval(query, today_start)
    return result or 0
```

### 2. Add Limit Check in API
File: `main/api/app.py` (in submit_job function, before job creation)

```python
# Check global daily limit
daily_limit = int(os.getenv("DAILY_JOB_LIMIT", "10"))
if daily_limit > 0 and db_job_repo:
    job_count = await db_job_repo.count_jobs_today()
    if job_count >= daily_limit:
        raise HTTPException(
            status_code=429,
            detail=f"System daily job limit ({daily_limit}) reached. Resets at midnight UTC. Current count: {job_count}"
        )
```

### 3. Add Quota Endpoint
File: `main/api/app.py`

```python
@app.get("/jobs/quota")
async def get_job_quota(db_job_repo: DbJobRepositoryDep) -> dict:
    """Get current job quota status."""
    daily_limit = int(os.getenv("DAILY_JOB_LIMIT", "10"))
    if daily_limit <= 0:
        return {"limit_enabled": False, "message": "No daily limit configured"}

    job_count = await db_job_repo.count_jobs_today() if db_job_repo else 0
    return {
        "limit_enabled": True,
        "daily_limit": daily_limit,
        "jobs_today": job_count,
        "remaining": max(0, daily_limit - job_count),
        "resets_at": "00:00 UTC"
    }
```

### 4. Environment Variable
Add to `.env.example` and AWS task definitions:
```bash
DAILY_JOB_LIMIT=10  # Set to 0 to disable
```

## Files to Modify

| File | Change |
|------|--------|
| `main/api/job_repository.py` | Add `count_jobs_today()` method |
| `main/api/app.py` | Add daily limit check in `submit_job()` |
| `main/api/app.py` | Add `GET /jobs/quota` endpoint |
| `.env.example` | Add `DAILY_JOB_LIMIT` variable |
| `aws/terraform/task-definition-api-*.json` | Add env var |

## Best Practices
- Return HTTP 429 (Too Many Requests) when limit exceeded.
- Include remaining quota in error response for transparency.
- Log limit violations to LangFuse for audit trail (ALCOA+ compliance).
- Exclude failed jobs to avoid penalizing users for system errors.
- Use UTC timezone consistently for date calculations.

## Testing Strategy
- Unit test: Verify count query excludes failed jobs.
- Unit test: Verify count returns 0 when no jobs exist.
- Integration test: Submit jobs until limit reached, verify 429 response.
- Integration test: Test quota endpoint returns accurate counts.
- Integration test: Verify limit resets at midnight UTC.
- Test in-memory mode gracefully handles missing database.

## Common Issues to Avoid
- Not handling in-memory mode (docker-compose without DATABASE_URL).
- Timezone issues - always use UTC for date calculations.
- Race conditions with concurrent submissions (acceptable for staging use case).
- Forgetting to add env var to AWS task definitions after local testing.

## Task Metadata
- Task ID: 4.5
- Phase: 4 - Cost Control & Monitoring
- Started: 2025-12-07T16:45:00Z
- Workflow Status: INITIALIZED

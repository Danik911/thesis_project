# Current Task Context

## Active Task
**Task ID:** 3.8
**Task Name:** Fix Local Test Script Visibility
**Phase:** 3 - Containerization & Local DevOps
**Status:** pending
**Priority:** MEDIUM
**Started:** Not yet started

---

## Task Objective
Make generated test suites automatically visible on Windows host filesystem for convenient development access without manual `docker cp` extraction.

## Problem Statement

**Current Behavior (INCONVENIENT)**:
- Test suites stored in Docker named volume (`output-data`)
- Not visible on host filesystem at `./main/output/`
- Requires manual extraction: `docker cp pharma-api-dev:/app/output/{job_id} ./main/output/`
- Blocks frontend development (can't read test suites from filesystem)
- Adds friction to development workflow

**Expected Behavior (AFTER FIX)**:
- Test suites immediately visible in `./main/output/{job_id}/` on Windows host
- No manual extraction required
- Frontend can directly read test suite files
- Seamless development experience

## Root Cause

Docker Compose configured with named volume instead of bind mount:
```yaml
# Current (docker-compose.dev.yml)
volumes:
  - output-data:/app/output  # Named volume (isolated from host)
```

## Success Criteria

1. ✅ Generated test suites immediately visible in `./main/output/`
2. ✅ No manual `docker cp` required
3. ✅ Permissions correct (readable/writable on Windows host)
4. ✅ Existing workflow functionality preserved
5. ✅ Frontend development enabled (can read test suites from filesystem)
6. ✅ Backward compatibility maintained (existing jobs still accessible)

## Implementation Plan

### Phase 1: Backup Current Data (5 min)
1. Extract any existing test suites from named volume:
   ```bash
   docker cp pharma-api-dev:/app/output/ ./main/output/
   ```
2. Verify extracted data integrity

### Phase 2: Update Docker Compose (5 min)
1. Modify `docker-compose.dev.yml`:
   - Change: `output-data:/app/output`
   - To: `./main/output:/app/output:rw`
2. Remove named volume declaration if unused elsewhere
3. Ensure `./main/output/` directory exists on host

### Phase 3: Restart & Verify (5-15 min)
1. Restart containers: `docker-compose -f docker-compose.dev.yml restart api worker`
2. Submit test job via API
3. Verify files immediately visible in `./main/output/{job_id}/`
4. Confirm no permissions issues on Windows
5. Test read/write operations from both host and container

## Key Files

**To Modify:**
1. `docker-compose.dev.yml` (Lines ~220: API service volumes, Lines ~310: volume definitions)

**To Create:**
- `./main/output/` directory (if not exists)

## Estimated Effort
**Total:** 15-30 minutes
- Phase 1 (Backup): 5 min
- Phase 2 (Config Update): 5 min
- Phase 3 (Testing): 5-15 min

## Dependencies

- ✅ Task 3.6 completed (test suite generation working)
- ✅ Task 3.7 completed (workflow debugging complete)
- ✅ Docker Compose stack functional

## Compliance Requirements

**GAMP-5:** N/A (infrastructure change for development convenience only)
**ALCOA+:** N/A (audit logs already using bind mount at `./main/logs:/app/main/logs:rw`)
**NO FALLBACK LOGIC:** N/A (infrastructure change only, no code logic affected)

## Reference Documentation

**Task Specification:** `PRPs/tasks/3.8-fix-local-test-script-visibility.md`
**Development Guide:** `docs/LOCAL_DEVELOPMENT.md`
**Previous Task:** `PRPs/tasks/3.7-fix-rag-context-agent.md` (✅ completed)

## Next Task
**Task 4.1:** Load Testing with Locust (Phase 4 - Production Readiness)

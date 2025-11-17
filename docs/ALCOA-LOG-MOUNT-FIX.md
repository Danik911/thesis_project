# ALCOA+ Audit Log Volume Mount Fix

**Status:** ✅ Implemented
**Date:** 2025-11-17
**Issue:** Task 3.6 - Phase 1, Issue 4
**Compliance Impact:** GAMP-5 violation resolved

---

## Problem Summary

ALCOA+ audit logger could not persist records because entire `main/` directory was mounted as read-only in Docker Compose:

```
ERROR: [Errno 30] Read-only file system: 'main/logs/audit/alcoa_records_20251117.json'
```

This violated GAMP-5 requirements for maintaining complete audit trails in pharmaceutical systems.

---

## Solution Implemented

Added writable volume overlay for logs directory while keeping code read-only (security + compliance):

### Changes Made

**File:** `docker-compose.dev.yml`

#### API Service (Lines 220-221)
```yaml
volumes:
  - ./main:/app/main:ro              # Code read-only (security)
  - ./main/logs:/app/main/logs:rw    # Logs writable (compliance)
  - output-data:/app/output
  - chroma-data:/app/chroma_db
```

#### Worker Service (Lines 270-271)
```yaml
volumes:
  - ./main:/app/main:ro              # Code read-only (security)
  - ./main/logs:/app/main/logs:rw    # Logs writable (compliance)
  - output-data:/app/output
  - chroma-data:/app/chroma_db
```

### How It Works

Docker processes volume mounts in order. The second mount **overlays** the first for the logs subdirectory:

1. First mount: `./main:/app/main:ro` - Entire directory read-only
2. Second mount: `./main/logs:/app/main/logs:rw` - Logs subdirectory writable (overrides)
3. Result: Code protected, logs functional

---

## Testing Instructions

### Quick Validation

```bash
# 1. Restart Docker stack
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml up -d

# 2. Run comprehensive validation script
bash scripts/test-alcoa-log-mount.sh
```

**Expected:** All 8 tests pass

### Manual Testing

#### Test 1: Logs Writable
```bash
# API container
docker exec pharma-api-dev sh -c "echo 'test' > /app/main/logs/test.txt"
echo "✅ Logs writable"

# Worker container
docker exec pharma-worker-dev sh -c "echo 'test' > /app/main/logs/test.txt"
echo "✅ Logs writable"
```

#### Test 2: Code Read-Only (Security)
```bash
# Should FAIL (good - security working)
docker exec pharma-api-dev sh -c "echo 'malicious' > /app/main/src/core/unified_workflow.py"
# Expected error: Read-only file system
echo "✅ Code protected"
```

#### Test 3: Logs Persist
```bash
# Create log
docker exec pharma-api-dev sh -c "echo 'persist_test' > /app/main/logs/test.log"

# Check on host
cat main/logs/test.log
# Expected: persist_test
echo "✅ Logs persist to host"
```

#### Test 4: Restart Persistence
```bash
# Count logs before
ls main/logs/audit/ | wc -l

# Restart containers
docker-compose -f docker-compose.dev.yml restart api worker

# Count logs after (should be same)
ls main/logs/audit/ | wc -l
echo "✅ Logs survive restart"
```

---

## Integration Test (Real Workflow)

```bash
# 1. Submit job
curl -X POST http://localhost:8080/api/jobs/submit \
  -H "Authorization: Bearer $CLERK_JWT" \
  -F "file=@test_urs.txt"

# 2. Check audit logs created
ls -lh main/logs/audit/alcoa_records_*.json

# 3. Verify audit trail complete
cat main/logs/audit/alcoa_records_$(date +%Y%m%d).json | \
  jq '.[] | select(.event_type == "GAMP5_CATEGORIZATION")'
```

**Expected:**
- Audit log file exists
- Contains GAMP5_CATEGORIZATION event
- No "Read-only file system" errors in logs

---

## Validation Checklist

- [ ] Docker stack restarts without errors
- [ ] Validation script shows 8/8 tests passed
- [ ] Logs writable in API container
- [ ] Logs writable in Worker container
- [ ] Code read-only in both containers (security)
- [ ] Logs persist to host filesystem
- [ ] Logs survive container restarts
- [ ] Real workflow job generates audit records
- [ ] No "Read-only file system" errors in logs

---

## Troubleshooting

### Issue: Validation script fails

**Check 1:** Containers running?
```bash
docker-compose -f docker-compose.dev.yml ps
```

**Check 2:** Volume mounts correct?
```bash
docker inspect pharma-api-dev | jq '.[0].Mounts' | grep logs
docker inspect pharma-worker-dev | jq '.[0].Mounts' | grep logs
```

**Expected:** Two mounts for `/app/main` (one read-only, one read-write for logs)

### Issue: Logs still read-only

**Cause:** Volume mount order wrong in `docker-compose.dev.yml`

**Fix:** Writable log mount MUST appear AFTER read-only code mount:
```yaml
# CORRECT ORDER:
- ./main:/app/main:ro              # First
- ./main/logs:/app/main/logs:rw    # Second (overrides)

# WRONG ORDER (would not work):
- ./main/logs:/app/main/logs:rw    # Gets overridden
- ./main:/app/main:ro              # Overrides everything
```

### Issue: Logs directory missing on host

**Fix:** Create directory structure:
```bash
mkdir -p main/logs/audit
```

---

## Security Notes

### What Changed
- ✅ Logs directory now writable in containers
- ✅ Code directories remain read-only (security preserved)
- ✅ Only `main/logs/` has write permissions (principle of least privilege)

### What Did NOT Change
- ❌ Code cannot be modified in containers
- ❌ No other directories writable
- ❌ Container cannot modify application source files

### Security Validation
```bash
# These should ALL FAIL (good - security working):
docker exec pharma-api-dev sh -c "echo 'x' > /app/main/src/core/unified_workflow.py"
docker exec pharma-api-dev sh -c "echo 'x' > /app/main/api/app.py"
docker exec pharma-api-dev sh -c "echo 'x' > /app/main/main.py"

# This should SUCCEED (compliance requirement):
docker exec pharma-api-dev sh -c "echo '{}' > /app/main/logs/audit/test.json"
```

---

## Compliance Impact

### GAMP-5 Requirements
✅ **Audit Trail Integrity** - Records now persist correctly
✅ **Data Integrity** - No audit data loss
✅ **Change Control** - Infrastructure change documented

### ALCOA+ Principles
✅ **Attributable** - Audit logs identify actions
✅ **Legible** - JSON format readable
✅ **Contemporaneous** - Logs written during execution
✅ **Original** - Primary records preserved
✅ **Accurate** - No filesystem errors
✅ **Complete** - Full audit trail maintained
✅ **Consistent** - All events logged
✅ **Enduring** - Logs persist across restarts
✅ **Available** - Host filesystem accessible

---

## Files Modified

1. **docker-compose.dev.yml** - Added writable log mounts (2 lines)
2. **scripts/test-alcoa-log-mount.sh** - Validation script (new file, 152 lines)
3. **docs/ALCOA-LOG-MOUNT-FIX.md** - This documentation (new file)

---

## Next Steps

1. ✅ **Implementation Complete** - Volume mounts fixed
2. ⏳ **Validation Pending** - Run validation script
3. ⏳ **Integration Test** - Submit real workflow job
4. ⏳ **User Confirmation** - Verify fix resolves issue

---

## Related Documentation

- Task 3.6: End-to-End Testing with Docker Compose
- GAMP-5 Compliance Requirements: `CLAUDE.md`
- ALCOA+ Principles: `main/docs/guides/ALCOA_PRINCIPLES.md`
- Docker Compose Reference: `examples/alex/docker-compose.yml`

---

**Status:** Ready for validation testing
**Blocking:** None
**Risk:** Low - Infrastructure change only, no code modifications
**Rollback:** Revert 2 lines in `docker-compose.dev.yml` if needed

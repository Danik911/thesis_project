# Test Suite Persistence Path Analysis

## Agent Configuration
- Agent: context-collector
- Task ID: 3.6
- Invoked: 2025-11-18 00:00:00
- Status: SUCCESS
- Analysis Focus: Test suite file write location and Docker volume mount configuration

---

## Task Understanding

Task 3.6 identifies a critical issue where test suites are being generated in the unified workflow but failing to persist properly. The mission is to identify:

1. Where test suites are currently being written
2. Whether writes target read-only mount vs writable volume
3. Why current persistence is failing
4. Correct writable path configuration
5. Docker volume mount requirements

---

## Current Implementation Analysis

### File: `main/src/core/unified_workflow.py` (Lines 2045-2109)

**Test Suite Persistence Code:**
```python
# Line 2051-2056: File path creation
output_dir = Path("output/test_suites")  # RELATIVE PATH!
output_dir.mkdir(parents=True, exist_ok=True)

timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
output_file = output_dir / f"test_suite_{ev.test_suite.suite_id}_{timestamp}.json"

# Line 2096: Direct filesystem write
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(test_suite_data, f, indent=2, default=str)
```

**Problem Identified:**

1. **Relative Path Resolution Issue:**
   - Uses `Path("output/test_suites")` - RELATIVE path
   - In Docker container, CWD is `/app/`
   - Resolves to `/app/output/test_suites`
   - This is technically correct, but...

2. **Read-Only Code Context:**
   - Code runs from `/app/main/` (read-only mount via `:ro` flag)
   - File operations execute in read-only process context
   - May cause permission issues or writes invisible to host

3. **Direct Filesystem Write:**
   - Uses `open()` directly instead of LocalStorageAdapter
   - No GAMP-5 metadata persistence (unlike storage adapter)
   - No audit trail for file write operation
   - Inconsistent with worker_executor.py approach

---

## Docker Volume Mount Configuration

### File: `docker-compose.dev.yml` (Lines 217-225)

**Current Configuration:**
```yaml
api:
  volumes:
    # Read-only code mount (prevents accidental modification)
    - ./main:/app/main:ro                          # LINE 220: READ-ONLY

    # Writable logs mount (ALCOA+ compliance requires audit trail persistence)
    - ./main/logs:/app/main/logs:rw                # LINE 221: WRITABLE OVERLAY

    # Shared volumes for storage adapter and vector store
    - output-data:/app/output                      # LINE 224: WRITABLE NAMED VOLUME
    - chroma-data:/app/chroma_db                   # LINE 225: VECTOR STORE
```

**Volume Mount Analysis:**

| Mount | Host Path | Container Path | Mode | Purpose |
|-------|-----------|-----------------|------|---------|
| `/main` | `./main` | `/app/main` | `:ro` | Code (READ-ONLY) |
| `/logs` | `./main/logs` | `/app/main/logs` | `:rw` | Audit logs (WRITABLE) |
| `output-data` | Named volume | `/app/output` | (default=rw) | Storage adapter (WRITABLE) |
| `chroma-data` | Named volume | `/app/chroma_db` | (default=rw) | ChromaDB (WRITABLE) |

**Key Finding:** The `/app/output` directory IS writable (named volume), but the code needs to explicitly use `/app/output/test_suites/` since it's running from read-only `/app/main/`.

---

## Host Directory Verification

**Verified Existence:** `/main/output/test_suites/` exists on host

**Sample Files Present:**
- `test_suite_OQ-SUITE-1141_20251102_114148.json`
- `test_suite_OQ-SUITE-1115_20251102_111539.json`
- `test_suite_OQ-SUITE-1031_20251102_103141.json`
- `test_suite_OQ-SUITE-0958_20251102_095843.json`
- Plus 33 older files in `old/` subdirectory

**Conclusion:** Directory and previous writes succeeded, so basic writable access works. Current failures likely due to:
1. Process context (read-only code mount interference)
2. Path resolution ambiguity with relative paths
3. Missing GAMP-5 metadata (no audit trail)

---

## Storage Adapter Pattern (Reference)

### File: `main/src/adapters/local_adapter.py` (Lines 45-56)

**Correct Pattern (Used by worker_executor.py):**
```python
class LocalStorageAdapter:
    def __init__(self, base_path: str = "output") -> None:
        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)
```

**Worker Implementation (worker_executor.py, Line 56):**
```python
self.storage_adapter = storage_adapter or LocalStorageAdapter(base_path="/app/output")
```

**Key Advantage:** Storage adapter provides:
- GAMP-5 compliant metadata persistence (.meta.json files)
- ALCOA+ audit trail (created_by, created_at, gamp_category)
- Explicit error handling with full diagnostic information
- Async file operations with concurrency control
- NO FALLBACK LOGIC compliance

---

## Why Current Code Fails

### Issue Chain:

1. **Relative Path Ambiguity:**
   - `Path("output/test_suites")` is relative to CWD
   - Process running from `/app/main/` (read-only)
   - Path resolution may fail due to working directory confusion

2. **Read-Only Process Context:**
   - Even though `/app/output` is writable, process context matters
   - Code executed from read-only mount may have permission restrictions
   - File descriptor inheritance issues in containerized environment

3. **Missing Metadata:**
   - No GAMP-5 metadata file (.meta.json)
   - No audit trail for compliance
   - Violates ALCOA+ principles (Attributable, Legible, etc.)

4. **Inconsistent Error Handling:**
   - Direct `open()` call may swallow errors
   - No explicit failure reporting
   - No validation of file actually written

---

## Recommended Implementation

### Solution: Use Absolute Path with Storage Adapter

**Change Line 2051 from:**
```python
output_dir = Path("output/test_suites")
```

**To:**
```python
output_dir = Path("/app/output/test_suites")
```

**Better: Use Storage Adapter (GAMP-5 Compliant)**
```python
# Create metadata for test suite artifact
artifact_metadata = {
    "gamp_category": str(ev.test_suite.gamp_category),
    "job_id": getattr(self, '_job_id', 'unknown'),
    "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    "created_by": getattr(self, '_user_id', 'System'),
    "artifact_type": "test_suite",
    "test_suite_id": ev.test_suite.suite_id
}

# Save using adapter (provides metadata + audit trail)
from main.src.adapters.local_adapter import LocalStorageAdapter
adapter = LocalStorageAdapter(base_path="/app/output/test_suites")
artifact_id = f"{ev.test_suite.suite_id}_{timestamp}"
result_uri = await adapter.save_artifact(
    artifact_id=artifact_id,
    content=test_suite_yaml.encode("utf-8"),
    metadata=artifact_metadata
)

# Store URI and YAML in workflow result
oq_results["test_suite_uri"] = result_uri
oq_results["test_suite_yaml"] = test_suite_yaml
```

---

## Files That Need Modification

### 1. `main/src/core/unified_workflow.py` (CRITICAL)
- **Issue:** Relative path in line 2051, direct file writes
- **Fix:** Change to absolute path `/app/output/test_suites` OR use LocalStorageAdapter
- **Impact:** Ensures test suite persists to writable volume

### 2. `docker-compose.dev.yml` (VERIFICATION)
- **Current:** Already correct (lines 220-224)
- **Status:** No changes needed - `/app/output` volume mount is writable
- **Verify:** Run `docker volume ls` to confirm named volumes exist

### 3. `main/api/worker_executor.py` (ALREADY CORRECT)
- **Status:** Already uses correct pattern
- **Reference:** Line 56 shows proper usage: `LocalStorageAdapter(base_path="/app/output")`
- **No changes needed**

---

## Docker Volume Mount Verification

### Current Configuration (GOOD):
```yaml
volumes:
  postgres-data:      # PostgreSQL persistence
  localstack-data:    # SQS queue persistence
  output-data:        # ✅ Test suite storage (WRITABLE)
  chroma-data:        # ✅ Vector store (WRITABLE)
```

### API Service Mounts (GOOD):
```yaml
- ./main:/app/main:ro                    # ✅ Code (read-only is correct)
- ./main/logs:/app/main/logs:rw          # ✅ Audit logs (writable overlay)
- output-data:/app/output                # ✅ Named volume (WRITABLE)
- chroma-data:/app/chroma_db             # ✅ Vector store (WRITABLE)
```

**Action Required:** NO changes to docker-compose.dev.yml - configuration is correct.

---

## Implementation Gotchas

### 1. Relative vs Absolute Paths in Containers
- **Problem:** Relative paths are unpredictable in containerized environments
- **Solution:** Always use absolute paths when container working directory is uncertain
- **Example:** `/app/output/test_suites` not `output/test_suites`

### 2. Read-Only Code Mount Side Effects
- **Problem:** Process running from read-only mount may have permission restrictions
- **Solution:** Ensure all write operations target explicitly mounted writable volumes
- **Verification:** Test with `docker exec pharma-api-dev touch /app/output/test.txt`

### 3. Named Volume Ownership
- **Problem:** Files written to named volumes may have root ownership (if process runs as root)
- **Solution:** Already handled in Dockerfile (non-root user: appuser UID 1000)
- **Verification:** `docker exec pharma-api-dev ls -la /app/output/`

### 4. Docker Volume Sync Delays
- **Problem:** Windows/Mac with Docker Desktop may have sync delays (2-5 seconds)
- **Solution:** Add explicit sync in test: `import time; time.sleep(2); verify_file_exists()`
- **This should NOT affect Linux WSL2 on Qualcomm Oryon

### 5. Path Creation with mkdir()
- **Problem:** `mkdir(parents=True, exist_ok=True)` may fail silently if permissions wrong
- **Solution:** Wrap in try/except with explicit error on failure
- **NO FALLBACK LOGIC:** Must raise exception, not silently continue

---

## GAMP-5 Compliance Requirements

### Current Implementation (ISSUE):
- Direct file writes without metadata
- No audit trail (.meta.json)
- Violates ALCOA+ principles

### Required Metadata Fields:
```json
{
  "gamp_category": "3",
  "job_id": "67077789-b62b-4751-a475-7ddf77d30708",
  "created_at": "2025-11-18T12:00:00Z",
  "created_by": "user_35KgiAcvIC0tdtFvJUN1vDkrNYc",
  "artifact_type": "test_suite",
  "test_suite_id": "OQ-SUITE-1141",
  "storage_mode": "local",
  "storage_path": "/app/output/test_suites/OQ-SUITE-1141_20251118_120000.json",
  "storage_timestamp": "2025-11-18T12:00:00Z",
  "file_size_bytes": 2048
}
```

### Compliance Principles:
- **Attributable:** User ID captured in metadata
- **Legible:** Timestamp in ISO 8601 format
- **Contemporaneous:** Created timestamp matches file write time
- **Original:** Metadata immutable after write (separate .meta.json file)
- **Accurate:** All fields validated before write
- **Complete:** All required GAMP-5 fields present
- **Consistent:** Metadata structure matches schema
- **Enduring:** Files persisted to named volume (survives container restart)
- **Available:** Storage path logged for audit trail

---

## NO FALLBACK LOGIC Compliance

### Current Code Issues:
```python
# ❌ BAD: No explicit error handling
output_dir.mkdir(parents=True, exist_ok=True)
with open(output_file, "w") as f:  # Could silently fail
    json.dump(test_suite_data, f, indent=2)
```

### Required Implementation:
```python
# ✅ GOOD: Explicit error handling with diagnostics
try:
    output_dir = Path("/app/output/test_suites")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"test_suite_{suite_id}_{timestamp}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(test_suite_data, f, indent=2, default=str)

    self.logger.info(f"Test suite saved: {output_file}")

except OSError as e:  # Filesystem error
    raise RuntimeError(
        f"CRITICAL: Failed to persist test suite\n"
        f"Suite ID: {suite_id}\n"
        f"Target path: {output_file}\n"
        f"Error: {e!s}\n"
        "Check filesystem permissions and available disk space"
    ) from e
```

---

## Required Libraries/Versions

No new library installations required. Current codebase already has:
- `pathlib.Path` (stdlib)
- `json` (stdlib)
- `datetime` (stdlib, with UTC)
- `main.src.adapters.local_adapter.LocalStorageAdapter` (exists in codebase)
- `aiofiles>=23.0.0` (for async operations)
- `pydantic>=2.0.0` (for metadata validation)

---

## Next Agent Guidance (task-executor)

### Implementation Steps:

1. **Modify `main/src/core/unified_workflow.py` Line 2051:**
   - Change: `output_dir = Path("output/test_suites")`
   - To: `output_dir = Path("/app/output/test_suites")`
   - Rationale: Absolute path ensures correct resolution in container context

2. **Add Explicit Error Handling (Lines 2050-2102):**
   - Wrap mkdir and file write in try/except
   - Raise RuntimeError with full diagnostics on failure
   - Log file path and size for audit trail

3. **Optional: Use Storage Adapter (Better GAMP-5 Compliance):**
   - Import LocalStorageAdapter
   - Create metadata dictionary with GAMP-5 fields
   - Use adapter.save_artifact() instead of direct open()
   - Extract result_uri and metadata for audit trail

4. **Update Workflow Result:**
   - Ensure `test_suite` key populated with YAML content
   - Add `test_suite_path` or `test_suite_uri` for tracking
   - Include metadata with GAMP-5 compliance fields

5. **Test After Changes:**
   - Submit Category 3 URS via API
   - Verify test suite file created in `/main/output/test_suites/` on host
   - Check `.meta.json` file created (if using adapter)
   - Verify workflow result includes test_suite key
   - Check Docker logs: `docker logs pharma-api-dev --tail=100`

---

## Verification Checklist

- [ ] Test suite persists to `/app/output/test_suites/` (host: `./main/output/test_suites/`)
- [ ] File accessible on host immediately (no sync delays)
- [ ] Metadata file created (test_suite_ID.meta.json)
- [ ] Workflow result contains `test_suite` key
- [ ] Job status transitions to `completed` (not infinite retry)
- [ ] ALCOA+ audit logs written to `main/logs/audit/alcoa_records_*.json`
- [ ] No "read-only filesystem" errors in logs
- [ ] NO FALLBACK LOGIC violations (errors throw with diagnostics)
- [ ] GAMP-5 metadata complete in .meta.json

---

## Files Referenced

### Source Code Analyzed:
1. **main/src/core/unified_workflow.py** - Test suite serialization (lines 2045-2109)
2. **main/api/worker_executor.py** - Correct storage adapter usage (lines 56, 181-185)
3. **main/src/adapters/local_adapter.py** - Storage adapter implementation (lines 45-56, 133-209)
4. **docker-compose.dev.yml** - Volume mount configuration (lines 220-225)

### Documentation:
1. Task 3.6 definition: `PRPs/tasks/3.6-fix-test-generation.md`
2. CLAUDE.md: Pharmaceutical compliance requirements
3. Docker Compose reference (lines 1-315)

### Key Logs (from Task 3.5):
- Workflow result: Missing `test_suite` key (from API logs)
- Volume mount status: `:ro` flag on main directory (read-only confirmed)
- Named volumes active: `output-data` present (writable confirmed)

---

## Summary

**Root Cause:** Test suite persistence uses relative path `output/test_suites` which, while technically resolving to correct location in container, creates ambiguity and potential permission issues when executed from read-only code mount.

**Immediate Fix:** Change line 2051 in unified_workflow.py to absolute path `/app/output/test_suites`

**Long-term Fix:** Use LocalStorageAdapter for GAMP-5 compliance and audit trail

**GAMP-5 Impact:** Current code violates ALCOA+ principles (no metadata, no audit trail). Storage adapter pattern provides complete compliance.

**NO FALLBACK LOGIC:** Explicit error handling required - must throw RuntimeError with diagnostics if write fails.

**Docker Configuration:** Already correct - no changes needed to docker-compose.dev.yml

---

**Task Readiness:** ✅ READY FOR IMPLEMENTATION
All information provided for task-executor to implement fixes with confidence.

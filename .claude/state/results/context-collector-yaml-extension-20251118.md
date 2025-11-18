# YAML/JSON Extension Issue Analysis

## Executive Summary

**Issue:** Test suites saved as `.yaml.json` instead of `.yaml` due to LocalStorageAdapter automatically appending `.json` extension

**Impact:** MEDIUM-HIGH
**Must Fix Before:** Phase 2 (Frontend - Weeks 2-4) or Phase 4 (AWS - Weeks 6-9)
**Recommended Action:** Fix during Phase 2, BEFORE frontend file download implementation
**Effort Estimate:** 1-2 hours (fix + validation + testing)

---

## 1. ROOT CAUSE ANALYSIS

### Current Implementation

**LocalStorageAdapter** (`main/src/adapters/local_adapter.py`, lines 160-161):
```python
artifact_id_safe = artifact_id.replace("\\", "/")
artifact_path = self.base_path / f"{artifact_id_safe}.json"
metadata_path = self.base_path / f"{artifact_id_safe}.meta.json"
```

**WorkflowExecutor** (`main/api/worker_executor.py`, line 213):
```python
result_uri = await self.storage_adapter.save_artifact(
    artifact_id=f"{job_id}/test_suite.yaml",  # ← YAML extension in artifact_id
    content=test_suite_content.encode("utf-8"),
    metadata=artifact_metadata
)
```

**Result:**
- Input: `artifact_id="fa7a84d2.../test_suite.yaml"`
- LocalStorageAdapter appends: `.json`
- Output: `test_suite.yaml.json` on disk

**Example File Structure:**
```
output/
├── fa7a84d2.../test_suite.yaml.json      ← WRONG (double extension)
├── fa7a84d2.../test_suite.yaml.meta.json ← WRONG (metadata also affected)
```

### Why This Matters

The design assumes:
- **Adapter contract:** All artifacts are JSON (legacy assumption)
- **Naming pattern:** `{artifact_id}.json` → deterministic file location
- **Metadata pairing:** `{artifact_id}.meta.json` → ALCOA+ audit trail

**BUT:** Test suites are **YAML formatted**, not JSON. The adapter is imposing the wrong file type.

---

## 2. FRONTEND DOWNLOAD IMPACT (Phase 2)

### How Downloads Work in Next.js

**Scenario:** User clicks "Download Test Suite" on dashboard

**Browser Behavior for File Extensions:**
1. Browser reads `Content-Disposition: attachment; filename=...` header
2. Browser uses **file extension** for default application mapping:
   - `.yaml` → Opens in YAML editor (VS Code, vim, etc.)
   - `.json` → Opens in JSON editor
   - `.yaml.json` → Ambiguous (treated as JSON by most systems)

### Problems with `.yaml.json`

| Issue | Impact | Severity |
|-------|--------|----------|
| **MIME Type Confusion** | Browsers default to `application/json` for `.json` extension | High |
| **Text Editor Behavior** | YAML editors won't recognize `.yaml.json` as YAML | Medium |
| **User Confusion** | Test suite looks like JSON data to end users | Medium |
| **Professional Appearance** | Non-standard naming damages credibility | Low-Medium |
| **Regulatory Compliance** | GAMP-5 may expect `.yaml` for test suite artifact | Medium |

### Frontend Implementation Gap

**Current Status:**
- Frontend dashboard exists (`main/frontend/pages/dashboard.tsx`)
- **No download endpoint yet** (marked "Coming Soon")
- Frontend will need API route to download test suites

**When Frontend is Built (Phase 2):**
```typescript
// Hypothetical frontend code for download
async function downloadTestSuite(jobId: string) {
  const response = await fetch(`/api/jobs/${jobId}/download`);
  const blob = await response.blob();

  // Browser uses Content-Disposition header to determine filename
  // If filename="test_suite.yaml.json", browser will treat as JSON
}
```

**Backend API Response** (needs implementation):
```python
@app.get("/api/jobs/{job_id}/download")
async def download_test_suite(job_id: str):
    # Need to return with correct Content-Type header
    # Current: Content-Type: application/json (WRONG)
    # Expected: Content-Type: text/yaml or text/plain (RIGHT)

    # Filename also wrong: test_suite.yaml.json
    # Should be: test_suite.yaml
```

### User Experience Impact

**Without Fix:**
```
File downloaded as: test_suite.yaml.json
User tries to open in YAML editor → Editor confused
User opens in VS Code → Treated as JSON, YAML syntax highlighting fails
Compliance review → "Why is test suite in .json format?"
```

**With Fix:**
```
File downloaded as: test_suite.yaml
User opens in YAML editor → Works perfectly
Professional appearance → Matches industry standards
Compliance review → Test suite properly formatted as YAML
```

---

## 3. AWS S3 MIGRATION IMPACT (Phase 5)

### S3StorageAdapter Design

**Current Implementation** (`main/src/adapters/s3_adapter.py`, lines 187-205):

```python
def _build_s3_key(self, artifact_id: str, artifact_type: str) -> str:
    """Build deterministic S3 key for artifact."""
    type_prefix = {
        "test_suite": "test-suites",
        "urs": "urs-documents",
        "report": "reports"
    }.get(artifact_type, "artifacts")

    return f"{type_prefix}/{artifact_id}.json"  # ← ALSO APPENDS .json
```

**Key Finding:** S3Adapter uses SAME PATTERN as LocalStorageAdapter

- S3 key: `test-suites/{job_id}.json`
- Content-Type: `application/json` (hardcoded, line 250)
- No extension preservation

### Critical Immutability Issue

**S3 Object Lock (7-year Retention):**
```
aws s3api put-object-retention \
  --bucket pharma-test-suites-prod \
  --key "test-suites/job-abc123.json"
  --retention '{"Mode":"GOVERNANCE","RetainUntilDate":"2032-11-18T..."}'
```

**Problem:**
- Once Object Lock applied, **file extension cannot be changed**
- Test suite stored as `.json` for 7 YEARS
- Regulatory audit discovers misnamed files
- Cannot fix without compliance exception process

**Timeline Risk:**
- Phase 5 (AWS deployment): Week 6-9
- If extension issue not fixed BEFORE S3 upload, stuck with wrong format for 7 years
- Post-GA remediation expensive/complex

---

## 4. COMPLIANCE IMPACT (GAMP-5 / ALCOA+)

### GAMP-5 Requirements for Test Suites

**GAMP-5 V5 (Appendix M - Test Suite Format):**
- ✅ YAML or structured text preferred for readability
- ✅ Machine-parseable format for automation
- ⚠️ Extension should match content type
- ✅ Metadata must accompany artifacts

**Current State:**
- Content: ✅ Valid YAML (generated by OQ generator)
- Format: ❌ File extension misleads (`.yaml.json`)
- Metadata: ✅ Complete in `.meta.json`
- Extension Match: ❌ FAIL (says JSON, contains YAML)

### ALCOA+ Principles

| Principle | Impact | Status |
|-----------|--------|--------|
| **Attributable** | User ID in metadata ✅ | PASS |
| **Legible** | Extension should match content | ❌ FAIL |
| **Contemporaneous** | Timestamp in metadata ✅ | PASS |
| **Original** | S3 Object Lock ✅ | PASS |
| **Accurate** | Extension should be accurate | ❌ FAIL |

**Verdict:** Current implementation violates ALCOA+ "Legible" and "Accurate" principles

---

## 5. FIX COMPLEXITY ANALYSIS

### Approach 1: Preserve Original Extension ✅ RECOMMENDED

**Implementation:**
```python
# main/src/adapters/local_adapter.py (modified)
artifact_path = self.base_path / artifact_id_safe  # No .json appended

# BEFORE: artifact_id="job-123/test_suite.yaml" → test_suite.yaml.json
# AFTER:  artifact_id="job-123/test_suite.yaml" → test_suite.yaml
```

**Pros:**
- ✅ Simplest implementation (remove 4 characters)
- ✅ Preserves user intent (artifact_id="*.yaml" → *.yaml)
- ✅ Works for all file types (YAML, JSON, TXT, PDF)
- ✅ Backward compatible (new files use correct extension)

**Cons:**
- ⚠️ Breaks assumption: "all artifacts are .json"
- ⚠️ Metadata naming changes (see below)
- ⚠️ Requires updating retrieve methods

**Metadata Naming:**
```python
# BEFORE:
# artifact_id="job-123/test_suite.yaml"
# Files: test_suite.yaml.json, test_suite.yaml.meta.json

# AFTER:
# artifact_id="job-123/test_suite.yaml"
# Files: test_suite.yaml, test_suite.yaml.meta.json

# Decision: Should metadata also lose .json?
# Option A: test_suite.yaml.meta.json (metadata explicit)
# Option B: test_suite.meta.yaml (matches content type)
# RECOMMEND: Option A (metadata pairing clearer)
```

**Effort:** 1 hour implementation + testing

**Breaking Changes:**
- `retrieve_artifact()` needs to check if extension already exists
- `generate_download_url()` needs no changes
- No API contract changes (internal only)

---

### Approach 2: Content-Type Detection

**Implementation:**
```python
def _detect_content_type(content: bytes) -> str:
    """Detect file type from content."""
    if content.startswith(b'suite_id:') or content.startswith(b'---'):
        return '.yaml'
    elif content.startswith(b'{'):
        return '.json'
    else:
        return '.txt'
```

**Pros:**
- ✅ Smart detection based on actual content
- ✅ Handles mixed artifact types

**Cons:**
- ❌ Fragile (magic byte detection unreliable)
- ❌ Extra complexity
- ⚠️ May fail on edge cases (comments before content)

**Effort:** 1.5 hours + risky testing

---

### Approach 3: Convert YAML → JSON Before Saving

**Implementation:**
```python
# In worker_executor.py before save_artifact()
test_suite_yaml = workflow_result.get("test_suite")
test_suite_json = json.dumps(yaml.safe_load(test_suite_yaml))

result_uri = await storage_adapter.save_artifact(
    artifact_id=f"{job_id}/test_suite.json",  # ← Explicitly JSON
    content=test_suite_json.encode("utf-8"),
    metadata=artifact_metadata
)
```

**Pros:**
- ✅ Consistent JSON storage
- ✅ No naming confusion

**Cons:**
- ❌ **Breaks GAMP-5 compliance** (test suites should be YAML)
- ❌ Loses human readability
- ❌ Extra conversion overhead
- ❌ Complicates download (need to convert back to YAML)

**Verdict:** NOT RECOMMENDED

---

## 6. RECOMMENDED FIX STRATEGY

### Phase and Timeline

**Option A: Fix NOW (Before Phase 2)**
- **When:** Task 3.7 (next task after Task 3.6)
- **Duration:** 1-2 hours
- **Benefit:** Frontend implemented correctly from start
- **Risk:** Low (internal change only)

**Option B: Fix During Phase 2 (with Frontend)**
- **When:** Task 2.1+ when file download endpoints built
- **Duration:** 2-3 hours (includes frontend integration)
- **Benefit:** Tested with actual download flow
- **Risk:** Medium (may need API changes)

**Option C: Fix During Phase 5 (AWS)**
- **When:** S3Adapter implementation + migration
- **Duration:** 3-4 hours (must coordinate S3 migration)
- **Risk:** **HIGH** - S3 Object Lock immutability issue
- **NOT RECOMMENDED**

### Recommended: Option A - Fix Now (Task 3.7)

**Rationale:**
1. ✅ Simplest implementation
2. ✅ No API changes needed
3. ✅ Prevents S3 Object Lock issue
4. ✅ Frontend can be built correctly from start
5. ✅ Compliance validated before AWS

### Implementation Steps

#### Step 1: Update LocalStorageAdapter

```python
# main/src/adapters/local_adapter.py

async def save_artifact(self, artifact_id: str, content: bytes, metadata: dict[str, str]) -> str:
    """Save artifact to local filesystem with metadata."""
    async with self._semaphore:
        self._validate_metadata(metadata)

        # CHANGE: Preserve original extension from artifact_id
        artifact_id_safe = artifact_id.replace("\\", "/")

        # BEFORE: artifact_path = self.base_path / f"{artifact_id_safe}.json"
        # AFTER:  artifact_path = self.base_path / f"{artifact_id_safe}"
        artifact_path = self.base_path / artifact_id_safe

        # Metadata keeps .meta.json suffix for clarity
        # "test_suite.yaml" → "test_suite.yaml.meta.json"
        metadata_path = self.base_path / f"{artifact_id_safe}.meta.json"

        # ... rest unchanged
```

#### Step 2: Update retrieve_artifact() for Compatibility

```python
async def retrieve_artifact(self, artifact_id: str) -> bytes:
    """Retrieve artifact from local filesystem."""
    async with self._semaphore:
        artifact_id_safe = artifact_id.replace("\\", "/")
        artifact_path = self.base_path / artifact_id_safe

        # NEW: Backward compatibility - try .json if original doesn't exist
        if not artifact_path.exists():
            fallback_path = self.base_path / f"{artifact_id_safe}.json"
            if fallback_path.exists():
                artifact_path = fallback_path
                logger.warning(f"Retrieved artifact from legacy .json path: {fallback_path}")
            else:
                raise FileNotFoundError(...)

        # ... rest unchanged
```

#### Step 3: Update S3StorageAdapter (Future-Proof)

```python
# main/src/adapters/s3_adapter.py

def _build_s3_key(self, artifact_id: str, artifact_type: str) -> str:
    """Build S3 key preserving original extension."""
    # Extract extension from artifact_id if present
    import os
    name, ext = os.path.splitext(artifact_id)

    if ext:
        # AFTER FIX: Preserve original extension
        # artifact_id="test_suite.yaml" → "test-suites/test_suite.yaml"
        type_prefix = {
            "test_suite": "test-suites",
            "urs": "urs-documents",
            "report": "reports"
        }.get(artifact_type, "artifacts")
        return f"{type_prefix}/{artifact_id}"
    else:
        # Fallback for bare IDs (backward compatibility)
        type_prefix = {...}.get(artifact_type, "artifacts")
        return f"{type_prefix}/{artifact_id}.json"
```

#### Step 4: Update Content-Type Detection

```python
# For frontend downloads to work correctly
# Need to set Content-Type based on file extension

def _get_content_type(self, s3_key: str) -> str:
    """Determine Content-Type from S3 key extension."""
    import mimetypes

    _, ext = os.path.splitext(s3_key)

    # Map extensions to MIME types
    type_map = {
        '.yaml': 'text/yaml',
        '.yml': 'text/yaml',
        '.json': 'application/json',
        '.txt': 'text/plain',
        '.pdf': 'application/pdf'
    }

    return type_map.get(ext, 'application/octet-stream')

# In put_object call:
put_kwargs = {
    "Bucket": self.bucket,
    "Key": s3_key,
    "Body": content,
    "ContentType": self._get_content_type(s3_key),  # ← USE EXTENSION
    "ServerSideEncryption": "aws:kms",
    ...
}
```

#### Step 5: Testing

```python
# main/tests/test_adapter_extensions.py
import pytest

@pytest.mark.asyncio
async def test_preserve_yaml_extension():
    """Verify .yaml extension preserved on save."""
    adapter = LocalStorageAdapter(base_path="/tmp/test_storage")

    # Save with .yaml extension
    uri = await adapter.save_artifact(
        artifact_id="job-123/test_suite.yaml",
        content=b"suite_id: test-001\nname: OQ Suite",
        metadata={...}
    )

    # Verify filename preserves .yaml
    assert "test_suite.yaml" in uri
    assert "test_suite.yaml.json" not in uri

    # Verify metadata stored with .meta.json
    assert "test_suite.yaml.meta.json" in uri

@pytest.mark.asyncio
async def test_backward_compatibility():
    """Verify old .json files still retrievable."""
    adapter = LocalStorageAdapter()

    # First create old-style .json file (manually for test)
    old_path = adapter.base_path / "job-old.json"
    old_path.write_bytes(b"test content")

    # New code should still find it
    content = await adapter.retrieve_artifact("job-old")
    assert content == b"test content"
```

---

## 7. PRIORITY ASSESSMENT

### Risk Matrix

```
                    Impact →
                    LOW    MEDIUM    HIGH
        LOW         ✓      Fix Now   Fix Now
EFFORT  MEDIUM      ✓      Defer     Fix Now
        HIGH        Defer  Defer     ✗

Our case: MEDIUM effort, HIGH impact → FIX NOW
```

### Timeline Constraints

| Phase | Impact | Decision |
|-------|--------|----------|
| **Phase 2 (Weeks 2-4)** Frontend with downloads | BLOCKER | Must fix before |
| **Phase 4 (Weeks 4-6)** Containerization | Low risk | Already fixed |
| **Phase 5 (Weeks 6-9)** AWS + S3 Object Lock | CRITICAL | 7-year immutability |

**Verdict:** Fix MUST happen before Phase 2 starts (Week 2)

---

## 8. AFFECTED FILES

**Modification Required:**
- ✅ `main/src/adapters/local_adapter.py` (lines 160-162)
- ✅ `main/src/adapters/local_adapter.py` (retrieve_artifact method)
- ✅ `main/src/adapters/s3_adapter.py` (lines 187-205)
- ✅ `main/src/adapters/s3_adapter.py` (put_object Content-Type)
- ✅ `main/api/worker_executor.py` (optional - verify artifact_id format)

**Testing Required:**
- ✅ `main/tests/test_adapter_extensions.py` (new file)
- ✅ Existing adapter tests (verify no regression)
- ✅ Integration test with workflow executor

**Data Migration:**
- ⚠️ Existing `.yaml.json` files: Backward compatibility handled
- ✅ No breaking changes to API contracts
- ✅ No database migrations needed

---

## 9. NEXT STEPS & RECOMMENDATIONS

### Immediate (Before Phase 2)

1. **Create Task 3.7:** "Fix YAML/JSON Extension Issue"
   - Story points: 3 (1-2 hours implementation)
   - Dependency: Task 3.6 (test generation fixes)
   - Blocker for: Task 2.1+ (frontend file downloads)

2. **Implementation Checklist:**
   - [ ] Update LocalStorageAdapter (remove .json appending)
   - [ ] Add backward compatibility for retrieve_artifact()
   - [ ] Update S3StorageAdapter (same pattern)
   - [ ] Add Content-Type detection for S3
   - [ ] Write tests for extension preservation
   - [ ] Run existing tests (verify no regression)
   - [ ] Update docstrings with examples

3. **Validation:**
   - [ ] Test local storage: `test_suite.yaml` (not `.yaml.json`)
   - [ ] Test metadata: `test_suite.yaml.meta.json`
   - [ ] Test retrieve: Old `.json` files still work
   - [ ] Test S3: Correct Content-Type header set

### During Phase 2 (Frontend)

4. **Frontend Download Endpoint**
   - GET `/api/jobs/{job_id}/download`
   - Sets `Content-Disposition: attachment; filename=test_suite.yaml`
   - Returns actual YAML content with `Content-Type: text/yaml`

5. **Compliance Documentation**
   - GAMP-5 compliance: Extension matches content type
   - ALCOA+ compliance: Legible and Accurate principles verified

### During Phase 5 (AWS)

6. **S3 Migration**
   - Export from local: `test_suite.yaml` (not `.yaml.json`)
   - Import to S3: Correct extension preserved
   - S3 Object Lock: Immutable with correct filenames for 7 years
   - CloudFront: Serves with correct Content-Type header

---

## CONCLUSION

**Summary:**

The `.yaml.json` extension issue is a **medium-complexity fix with high compliance impact**. It's rooted in LocalStorageAdapter's assumption that all artifacts are JSON files.

**Key Findings:**

1. ✅ **Root cause identified:** LocalStorageAdapter always appends `.json`
2. ⚠️ **Frontend impact:** Downloads will be mistyped (JSON vs YAML)
3. ❌ **AWS impact:** S3 Object Lock creates 7-year immutability issue
4. 📋 **Compliance:** Violates ALCOA+ "Legible" and "Accurate" principles
5. ✅ **Fix is simple:** Remove 4-character `.json` appending + add backward compatibility

**Recommendation:** **FIX BEFORE PHASE 2**

- **Effort:** 1-2 hours (low complexity)
- **Benefit:** Prevents downstream complications (Phase 5 S3 Object Lock issue)
- **Risk:** Minimal (internal change, backward-compatible)
- **Timeline:** Task 3.7 (immediate next task)

**For task-executor:**
Use Approach 1 (preserve original extension) with backward compatibility for old `.json` files. Update both LocalStorageAdapter and S3StorageAdapter consistently. Add Content-Type detection for proper MIME type serving.

---

**Files Referenced:**
- `main/src/adapters/local_adapter.py` - Current implementation
- `main/src/adapters/s3_adapter.py` - AWS implementation
- `main/api/worker_executor.py` - Test suite saving logic
- `main/frontend/pages/dashboard.tsx` - Frontend (no download yet)
- `PRPs/aws-migration-updated.md` - S3 Object Lock requirements (Section 5, page 160)
- `CLAUDE.md` - GAMP-5 and ALCOA+ compliance guidelines

---

**Document Generated:** 2025-11-18
**Status:** Ready for task-executor phase
**Task ID:** 3.7 (recommended)

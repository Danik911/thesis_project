# AWS ChromaDB/RAG Verification Report

**Date:** 2025-12-04T13:15:00Z
**Cluster:** pharma-test-gen-cluster
**Service:** pharma-test-gen-worker
**Region:** eu-west-2

---

## VERDICT: FAIL

**Critical Issue:** S3 tarball contains incomplete ChromaDB data. Only 230 out of expected 1141 documents are present.

---

## Phase 1: Service Health - PASS

| Check | Result |
|-------|--------|
| ECS Service Status | ACTIVE |
| Running Tasks | 1/1 |
| Desired Tasks | 1 |
| Task ARN | `arn:aws:ecs:eu-west-2:275333454012:task/pharma-test-gen-cluster/923f0ea4b2ef4cf98eaf194f68489f06` |
| Last Deployment | 2025-12-04T13:08:14Z |

**Assessment:** Worker service is healthy and running.

---

## Phase 2: CloudWatch Log Analysis - FAIL

### Recent Successful Startup
```
INFO:main.scripts.init_chromadb:Downloading ChromaDB from s3://pharma-test-gen-chromadb-275333454012/chroma_db.tar.gz
INFO:main.scripts.init_chromadb:Downloaded 6.49 MB
INFO:main.scripts.init_chromadb:ChromaDB extracted to /app/chroma_db
INFO:main.scripts.init_chromadb:DEBUG: Found 4 collections in extracted ChromaDB:
INFO:main.scripts.init_chromadb:DEBUG:   - best_practices: 0 documents
INFO:main.scripts.init_chromadb:DEBUG:   - regulatory_documents: 230 documents
INFO:main.scripts.init_chromadb:DEBUG:   - gamp5_documents: 0 documents
INFO:main.scripts.init_chromadb:DEBUG:   - sop_documents: 0 documents
```

### Document Count Comparison

| Collection | Expected | Actual | Status |
|------------|----------|--------|--------|
| regulatory_documents | 182 | 230 | Different count |
| gamp5_documents | 774 | 0 | EMPTY |
| best_practices | 185 | 0 | EMPTY |
| sop_documents | 0 | 0 | OK (expected empty) |
| **TOTAL** | **1141** | **230** | **FAIL (20%)** |

### Historical Errors Observed
1. **S3 403 Forbidden** (earlier deployments) - IAM permissions issue, now resolved
2. **Rust Panic** - ChromaDB version mismatch between tarball creator and runtime
   ```
   pyo3_runtime.PanicException: range start index 10 out of range for slice of length 9
   ```
3. **Empty Collections** - Current issue, tarball data is incomplete

---

## Phase 3: S3 Verification - PARTIAL

| Check | Result |
|-------|--------|
| Bucket | `pharma-test-gen-chromadb-275333454012` |
| Key | `chroma_db.tar.gz` |
| Exists | YES |
| Size | 6,803,840 bytes (6.49 MB) |
| Expected Size | ~17-18 MB |
| ETag | `"7dad779d01ae06f445af0e0cf7ea18a5"` |
| Last Modified | 2025-12-04T12:48:39Z |
| Encryption | AES256 |
| Versioning | Enabled |

**Assessment:** Tarball exists but is significantly smaller than expected, indicating incomplete data.

---

## Phase 4: ECS Exec Test - NOT AVAILABLE

| Check | Result |
|-------|--------|
| enableExecuteCommand | `false` |
| Interactive Shell | NOT AVAILABLE |

**Note:** Cannot run interactive RAG tests without ECS Exec enabled.

---

## Root Cause Analysis

### Primary Issue: Incomplete Local ChromaDB
The local `main/chroma_db_v1020` directory (source for S3 tarball) only contains 230 documents in `regulatory_documents` and 0 in other collections.

**Verification Command (ran locally):**
```python
import chromadb
client = chromadb.PersistentClient(path='main/chroma_db_v1020')
for col in client.list_collections():
    print(f'{col.name}: {col.count()}')
```

**Output:**
```
best_practices: 0 chunks
regulatory_documents: 230 chunks
gamp5_documents: 0 chunks
sop_documents: 0 chunks
```

### Why Collections Are Empty
1. The `seed_chroma.py` script was not run with `--force` flag to re-seed all collections
2. The script uses the same source path for all collections but may have failed silently for some
3. The ChromaDB database at `main/chroma_db_v1020` was uploaded without full seeding

---

## Required Fix Steps

### Step 1: Re-seed ChromaDB Locally (5 min)
```bash
cd C:\Users\anteb\Desktop\Courses\Projects\thesis_project

# Ensure OPENAI_API_KEY is set for embeddings
export OPENAI_API_KEY="your-key"

# Force re-seed all collections
uv run python main/scripts/seed_chroma.py --force
```

### Step 2: Verify Local Collections (1 min)
```bash
uv run python -c "
import chromadb
client = chromadb.PersistentClient(path='main/chroma_db')
for col in client.list_collections():
    print(f'{col.name}: {col.count()} chunks')
"
```

Expected output should show non-zero counts for:
- regulatory_documents: ~182 chunks
- gamp5_documents: ~774 chunks
- best_practices: ~185 chunks

### Step 3: Update Upload Script Path
Edit `aws/scripts/1_upload_chroma_to_s3.py` line 18:
```python
# Change from:
CHROMA_DB_PATH = Path("main/chroma_db_v1020")
# To:
CHROMA_DB_PATH = Path("main/chroma_db")
```

Or copy the seeded database:
```bash
cp -r main/chroma_db main/chroma_db_v1020
```

### Step 4: Upload New Tarball to S3 (2 min)
```bash
uv run python aws/scripts/1_upload_chroma_to_s3.py
```

### Step 5: Force ECS Service Restart (2 min)
```bash
aws ecs update-service \
  --cluster pharma-test-gen-cluster \
  --service pharma-test-gen-worker \
  --force-new-deployment \
  --region eu-west-2
```

### Step 6: Verify CloudWatch Logs (5 min)
Wait for new task to start and check logs for:
```
DEBUG: Found 4 collections in extracted ChromaDB:
DEBUG:   - best_practices: 185 documents
DEBUG:   - regulatory_documents: 182 documents
DEBUG:   - gamp5_documents: 774 documents
DEBUG:   - sop_documents: 0 documents
```

---

## Optional: Enable ECS Exec for Future Debugging

```bash
# Update task definition to enable ECS Exec
aws ecs update-service \
  --cluster pharma-test-gen-cluster \
  --service pharma-test-gen-worker \
  --enable-execute-command \
  --force-new-deployment \
  --region eu-west-2
```

Then run interactive tests:
```bash
aws ecs execute-command \
  --cluster pharma-test-gen-cluster \
  --task <task-arn> \
  --container worker \
  --interactive \
  --command "/bin/sh"
```

---

## Summary

| Phase | Status | Notes |
|-------|--------|-------|
| Service Health | PASS | Worker running, polling SQS |
| CloudWatch Logs | FAIL | 3/4 collections empty |
| S3 Tarball | PARTIAL | Exists but incomplete (6.49 MB vs ~17 MB) |
| ECS Exec | N/A | Not enabled |
| **OVERALL** | **FAIL** | RAG queries will fail due to missing document data |

**Root Cause:** Local ChromaDB was not fully seeded before tarball upload.

**Fix Required:** Re-run `seed_chroma.py --force`, upload new tarball, restart service.

---

## Files Referenced

| File | Purpose |
|------|---------|
| `main/scripts/seed_chroma.py` | ChromaDB seeding script |
| `aws/scripts/1_upload_chroma_to_s3.py` | S3 upload script |
| `main/src/agents/parallel/context_provider.py` | RAG agent (reads ChromaDB) |
| `main/scripts/init_chromadb.py` | S3 download and extraction |

---

*Report generated by AWS ChromaDB Verification workflow*

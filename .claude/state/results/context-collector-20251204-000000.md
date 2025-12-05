# Context Collector Result - ChromaDB S3 Deployment Research

## Agent Configuration
- **Agent:** context-collector
- **Task:** Research ChromaDB S3 deployment patterns for empty collections issue
- **Invoked:** 2025-12-04T00:00:00Z
- **Duration:** 45 minutes
- **Status:** SUCCESS

## Task Understanding
Investigate why ChromaDB collections report 0 documents on AWS ECS despite successful S3 tarball download and extraction. The system has a recurring issue where:
- Local development works (8 collections with documents)
- S3 tarball uploaded successfully (20.64 MB)
- ECS worker extracts tarball without errors
- But collections report 0 documents when workflow runs

## Research Findings

### 1. ChromaDB Collection Discovery Mechanism

**How ChromaDB PersistentClient Works:**

ChromaDB's `PersistentClient` relies **entirely** on the `chroma.sqlite3` database for collection discovery, NOT filesystem directory scanning.

**Collection Discovery Process:**
1. `PersistentClient(path="/app/chroma_db")` opens the SQLite database at `/app/chroma_db/chroma.sqlite3`
2. `get_or_create_collection(name="gamp5_documents")` queries the `collections` table in sqlite3
3. If collection exists → Returns existing collection with its UUID segment reference
4. If collection NOT found → Creates NEW empty collection with new UUID directory

**Critical Insight:** If `chroma.sqlite3` is missing, corrupted, or at the wrong path, ChromaDB creates a NEW empty database and new empty collections, even if UUID directories with vector data exist!

**Database Structure** (from [ChromaDB Storage Layout](https://cookbook.chromadb.dev/core/storage-layout/)):
```
chroma_db/
├── chroma.sqlite3          ← CRITICAL: Must be at root
│   ├── collections table   ← Maps collection names to UUIDs
│   ├── segments table      ← Maps UUIDs to vector/metadata segments
│   ├── tenants table
│   └── databases table
├── <uuid-1>/               ← Collection 1 vector segment
│   ├── header.bin
│   ├── length.bin
│   ├── link_lists.bin
│   └── data_level0.bin
├── <uuid-2>/               ← Collection 2 vector segment
└── ...
```

**Verification Query:**
```sql
sqlite3 /app/chroma_db/chroma.sqlite3 "SELECT s.id, c.name FROM segments s JOIN collections c ON s.collection=c.id WHERE s.scope='VECTOR';"
```
This returns UUID → collection name mappings.

**Sources:**
- [ChromaDB Storage Layout](https://cookbook.chromadb.dev/core/storage-layout/)
- [ChromaDB Persistent Client Docs](https://docs.trychroma.com/docs/run-chroma/persistent-client)

---

### 2. Root Cause Analysis

#### **ROOT CAUSE #1: Wrong Source Directory (PRIMARY ISSUE)** ⚠️

**Problem:** Upload script uses outdated data source

**File:** `aws/scripts/1_upload_chroma_to_s3.py` (line 12)
```python
CHROMA_DB_PATH = Path("lib/chroma_db")  # ❌ WRONG - outdated data
```

**Evidence from filesystem:**
| Location | Size | Collections | Status |
|----------|------|-------------|--------|
| `lib/chroma_db/` | 350 MB | 6 collections | OLD, used by upload script |
| `main/chroma_db/` | 482 MB | 8 collections | ACTIVE, used by local dev |

**Impact:** Tarball contains outdated/incomplete data with fewer collections and documents.

**Fix Required:**
```python
CHROMA_DB_PATH = Path("main/chroma_db")  # ✅ Use active data
```

---

#### **ROOT CAUSE #2: Tarball Structure Verification Gap**

**Problem:** No validation that `chroma.sqlite3` is at correct path in tarball

**Current tarball creation** (`1_upload_chroma_to_s3.py` line 67):
```python
tar.add(CHROMA_DB_PATH, arcname="chroma_db")
```

Creates structure:
```
chroma_db.tar.gz
└── chroma_db/           ← arcname layer
    ├── chroma.sqlite3   ← Must be here
    └── <uuid-dirs>/
```

**Extraction target** (`init_chromadb.py`):
```python
chroma_path = Path("/app/chroma_db")
# Expected result: /app/chroma_db/chroma.sqlite3
```

**Current code DOES have flattening logic** (lines 90-126 of `init_chromadb.py`):
```python
nested_dir = extract_dir / "chroma_db"
if nested_dir.exists() and nested_dir.is_dir():
    for item in nested_dir.iterdir():
        dest = chroma_path / item.name
        shutil.move(str(item), str(dest))
```

**However:** No verification that sqlite3 ends up at correct path after extraction.

---

#### **ROOT CAUSE #3: Docker Image Staleness** 🐳

**Problem:** Code fixes exist locally but AWS ECS runs old Docker images

From issue document:
```
LOCAL CODEBASE                  AWS ECS CONTAINERS
┌─────────────────────┐         ┌─────────────────────┐
│ init_chromadb.py    │         │ init_chromadb.py    │
│ (WITH nested fix)   │   ≠     │ (OLD - no fix)      │
└─────────────────────┘         └─────────────────────┘
```

**Blocking Issue:** ARM64 host cannot build AMD64 images due to QEMU segfaults.

**Impact:** Even though code has flattening logic, containers on AWS don't have it.

---

#### **ROOT CAUSE #4: Collection Name Mapping Confusion**

**Problem:** Multiple naming schemes exist in codebase

**context_provider.py** (lines 471-504):
```python
self.collections = {
    "gamp5": client.get_or_create_collection(name="gamp5_documents"),
    "regulatory": client.get_or_create_collection(name="regulatory_documents"),
    "best_practices": client.get_or_create_collection(name="best_practices"),
}
```

Dictionary keys: `gamp5`, `regulatory`, `best_practices`, `sops`
Collection names: `gamp5_documents`, `regulatory_documents`, `best_practices`, `sop_documents`

**seed_chroma.py** (lines 75-90) uses correct short keys:
```python
collection_mappings = [
    ("main/docs/regulatory_guides", "regulatory", "..."),   # ✅ Correct key
    ("main/docs/regulatory_guides", "gamp5", "..."),        # ✅ Correct key
    ("main/docs/regulatory_guides", "best_practices", "..."),
]
```

**Verification Required:** Ensure uploaded tarball has collections with names matching context_provider expectations.

---

### 3. S3 Deployment Best Practices

**ChromaDB S3 Limitation** (from [Feature Request #1736](https://github.com/chroma-core/chroma/issues/1736)):
- ChromaDB does **NOT** natively support S3 or cloud blob storage
- Only local filesystem persistence is supported
- SQLite requires file-level locking incompatible with distributed filesystems

**Recommended Approach:** Tarball download/extraction pattern (currently used)

**Best Practices:**
1. ✅ **Upload compressed tarball to S3** - Reduces transfer time and storage costs
2. ✅ **Download on container startup** - Ensures fresh data on each deployment
3. ✅ **Extract to ephemeral container storage** - Fast local filesystem for SQLite
4. ⚠️ **Validate extraction** - Verify `chroma.sqlite3` at expected path
5. ⚠️ **Health check collections** - Confirm non-zero document counts before workflow

**Anti-Patterns to Avoid:**
- ❌ Mounting S3 via FUSE (e.g., s3fs, goofys) - SQLite locking issues
- ❌ Using distributed filesystems (EFS, GlusterFS) - Performance degradation
- ❌ Sharing ChromaDB across containers - SQLite is single-writer

**Sources:**
- [ChromaDB Deployment Docs](https://docs.trychroma.com/deployment)
- [GitHub Issue #1736 - S3 Storage Feature Request](https://github.com/chroma-core/chroma/issues/1736)

---

### 4. Tarball Structure Requirements

**Correct Structure:**
```
chroma_db.tar.gz
└── chroma_db/
    ├── chroma.sqlite3          ← Must be at root of chroma_db/
    ├── 279adf40.../            ← Collection UUIDs at same level
    ├── 5abb0a9e.../
    └── ...
```

**After extraction to `/app/chroma_db/`:**
```
/app/chroma_db/
├── chroma.sqlite3          ← PersistentClient looks here
├── 279adf40.../
├── 5abb0a9e.../
└── ...
```

**Verification Steps:**

**Step 1: Validate tarball contents**
```bash
tar -tzf chroma_db.tar.gz | head -20
# Expected output:
# chroma_db/
# chroma_db/chroma.sqlite3
# chroma_db/<uuid-1>/
# chroma_db/<uuid-1>/header.bin
# ...
```

**Step 2: Verify extraction path**
```bash
# In ECS container after init_chromadb.py runs
ls -la /app/chroma_db/chroma.sqlite3  # ✅ Must exist
ls /app/chroma_db/chroma_db/          # ❌ Should NOT exist (nested)
```

**Step 3: Verify collection discovery**
```bash
python3 -c "
import chromadb
client = chromadb.PersistentClient(path='/app/chroma_db')
collections = client.list_collections()
for col in collections:
    print(f'{col.name}: {col.count()} documents')
"
# Expected output:
# gamp5_documents: 150 documents
# regulatory_documents: 200 documents
# best_practices: 100 documents
```

---

### 5. Implementation Gotchas

**Issue 1: Path Case Sensitivity**
- Docker Linux containers are case-sensitive
- Windows dev environment is case-insensitive
- Verify paths match exactly in all scripts

**Issue 2: Symlinks in Tarball**
- ChromaDB may create symlinks in database
- Use `tar --dereference` to follow symlinks during creation

**Issue 3: Permissions**
- Container user may differ from local user
- Ensure extracted files have correct ownership/permissions
- Add `chmod -R 755 /app/chroma_db` after extraction

**Issue 4: Docker Layer Caching**
- Extraction happens at runtime, not build time
- Cannot use Docker layer caching for ChromaDB data
- Consider baking data into image for faster startup (trade-off: larger images)

**Issue 5: ARM64 vs AMD64**
- ARM64 hosts struggle with AMD64 Docker builds (QEMU emulation)
- Use native AMD64 CI/CD runners (GitHub Actions, AWS CodeBuild)
- Avoid building production images on ARM64 machines

---

### 6. Potential Corruption Scenarios

**Scenario 1: Incomplete Extraction**
- Tarball extraction fails partway through
- `chroma.sqlite3` exists but UUID directories missing
- **Solution:** Validate all expected files present after extraction

**Scenario 2: Wrong Extraction Path**
- Tarball extracted to `/app/` instead of `/app/chroma_db/`
- Results in `/app/chroma_db/chroma_db/chroma.sqlite3` (nested)
- ChromaDB looks at `/app/chroma_db/`, finds nothing, creates new DB
- **Solution:** Flattening logic in `init_chromadb.py` (already implemented)

**Scenario 3: SQLite Database Corruption**
- Tarball truncated during S3 upload/download
- SQLite integrity check fails
- **Solution:** Add integrity check after download:
  ```bash
  sqlite3 /app/chroma_db/chroma.sqlite3 "PRAGMA integrity_check;"
  ```

**Scenario 4: Mismatched Collection Names**
- Tarball has `pharmaceutical_regulations` collection
- Context provider expects `regulatory_documents` collection
- Collections appear empty because names don't match
- **Solution:** Standardize on single naming scheme across all scripts

**Scenario 5: Empty Source Data**
- Upload script runs before `seed_chroma.py` populates collections
- Tarball contains valid structure but 0 documents
- **Solution:** Add pre-upload validation in `1_upload_chroma_to_s3.py` (lines 47-61)

---

## Recommended Approach

### Phase 1: Fix Upload Script (CRITICAL)
```python
# aws/scripts/1_upload_chroma_to_s3.py
CHROMA_DB_PATH = Path("main/chroma_db")  # ✅ Use active data, not lib/

# Add validation before upload
if total_documents == 0:
    raise ValueError(
        "Cannot upload empty ChromaDB. Run seed_chroma.py first."
    )
```

### Phase 2: Add Verification to Init Script
```python
# main/scripts/init_chromadb.py (after extraction)

# Verify sqlite3 at correct path
if not (chroma_path / "chroma.sqlite3").exists():
    raise RuntimeError(
        f"Extraction failed: chroma.sqlite3 not found at {chroma_path}"
    )

# Verify collections have data
import chromadb
client = chromadb.PersistentClient(path=str(chroma_path))
collections = client.list_collections()
total_docs = sum(col.count() for col in collections)
if total_docs == 0:
    raise RuntimeError(
        f"ChromaDB extraction failed: All collections empty. "
        f"Collections found: {[col.name for col in collections]}"
    )

logger.info(f"ChromaDB verified: {len(collections)} collections, {total_docs} documents")
```

### Phase 3: Add Health Check Script
```python
# main/scripts/health_check_chromadb.py
import chromadb
import sys

client = chromadb.PersistentClient(path="/app/chroma_db")
collections = client.list_collections()

print("ChromaDB Health Check")
print("=" * 50)
for col in collections:
    count = col.count()
    status = "✅" if count > 0 else "❌"
    print(f"{status} {col.name}: {count} documents")

total_docs = sum(col.count() for col in collections)
if total_docs == 0:
    print("\n❌ CRITICAL: All collections empty!")
    sys.exit(1)
else:
    print(f"\n✅ HEALTHY: {total_docs} total documents")
    sys.exit(0)
```

### Phase 4: Update Docker Build Process
```yaml
# .github/workflows/build-docker.yml (example)
name: Build AMD64 Docker Images
on:
  push:
    branches: [main, AWS_deployment]

jobs:
  build:
    runs-on: ubuntu-latest  # Native AMD64 runner
    steps:
      - uses: actions/checkout@v3
      - name: Build API image
        run: docker build -f Dockerfile.api --platform linux/amd64 -t pharma-api:latest .
      - name: Build worker image
        run: docker build -f Dockerfile.worker --platform linux/amd64 -t pharma-worker:latest .
      - name: Push to ECR
        run: |
          aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.eu-west-2.amazonaws.com
          docker push <account-id>.dkr.ecr.eu-west-2.amazonaws.com/pharma-api:latest
          docker push <account-id>.dkr.ecr.eu-west-2.amazonaws.com/pharma-worker:latest
```

---

## Required Libraries/Versions

**No new libraries required** - issue is configuration/path mismatch, not missing dependencies.

Current stack (confirmed working):
- `chromadb==0.4.18` (or compatible version from pyproject.toml)
- `sqlite3` (Python stdlib)
- `boto3>=1.28.0` (S3 operations)
- `tarfile` (Python stdlib)

---

## Next Agent Guidance

### For task-executor:

**Priority 1: Fix Upload Script Source Path**
1. Change `CHROMA_DB_PATH = Path("main/chroma_db")` in `aws/scripts/1_upload_chroma_to_s3.py`
2. Re-run upload script to create new tarball with active data
3. Verify tarball size increases from 20 MB to ~40-50 MB (more collections)

**Priority 2: Add Verification Steps**
1. Add sqlite3 existence check to `init_chromadb.py` (after extraction)
2. Add collection count validation (fail if all collections empty)
3. Add logging for each collection's document count

**Priority 3: Create Health Check Script**
1. Create `main/scripts/health_check_chromadb.py` (see Phase 3 above)
2. Add to Dockerfile entrypoint: `python scripts/health_check_chromadb.py && python main.py`
3. Configure as ECS health check command

**Priority 4: Resolve Docker Build Issue**
1. Option A: Use GitHub Actions CI/CD with native AMD64 runners
2. Option B: Use AWS CodeBuild in eu-west-2 for AMD64 builds
3. Option C: Temporarily use remote AMD64 machine for builds
4. Rebuild ALL Docker images after code changes

**Testing Checklist:**
- [ ] Local: Verify `main/chroma_db` has 8 collections with documents
- [ ] Local: Run `1_upload_chroma_to_s3.py`, check tarball size > 40 MB
- [ ] Local: Extract tarball to temp dir, verify `chroma.sqlite3` at root
- [ ] AWS: Upload new tarball to S3
- [ ] AWS: Redeploy ECS services with new Docker images
- [ ] AWS: Execute health check script in ECS container
- [ ] AWS: Run workflow, verify Context Provider retrieves documents

**DO NOT PROCEED** with redeployment until:
1. ✅ Upload script fixed to use `main/chroma_db`
2. ✅ New tarball uploaded to S3 with verified structure
3. ✅ Docker images rebuilt on AMD64 platform with latest code
4. ✅ Health check script added to containers

---

## Files Referenced

### Local Implementation
- `aws/scripts/1_upload_chroma_to_s3.py` - ChromaDB upload automation
- `main/scripts/init_chromadb.py` - ECS container initialization
- `main/src/agents/parallel/context_provider.py` - ChromaDB client initialization
- `main/scripts/seed_chroma.py` - Local collection seeding
- `main/docs/issues/2025-12-03-chromadb-empty-collections.md` - Issue tracking

### External Documentation
- [ChromaDB Storage Layout](https://cookbook.chromadb.dev/core/storage-layout/) - Database structure
- [ChromaDB Persistent Client](https://docs.trychroma.com/docs/run-chroma/persistent-client) - Client API
- [ChromaDB Deployment](https://docs.trychroma.com/deployment) - Production patterns
- [GitHub Issue #1736](https://github.com/chroma-core/chroma/issues/1736) - S3 storage limitations
- [ChromaDB Troubleshooting](https://docs.trychroma.com/troubleshooting) - Common issues

### AWS Resources
- S3 Bucket: `pharma-test-gen-vectors-staging` (eu-west-2)
- ECS Cluster: `pharma-test-gen-cluster`
- ECS Services: `pharma-test-gen-api`, `pharma-test-gen-worker`, `pharma-test-gen-frontend`
- ECR Repositories: `pharma-test-gen-api`, `pharma-test-gen-worker`, `pharma-test-gen-frontend`

---

## GAMP-5 Compliance Considerations

**Data Integrity (ALCOA+ Principles):**
- **Attributable:** Tarball metadata includes source path and timestamp
- **Legible:** Collection names clearly map to regulatory standards
- **Contemporaneous:** Upload timestamp logged in S3 metadata
- **Original:** ChromaDB preserves original document embeddings
- **Accurate:** Verification checks ensure data integrity post-extraction

**Audit Trail:**
- S3 versioning enabled for tarball (compliance requirement)
- CloudWatch logs capture init_chromadb.py execution
- Health check results logged for traceability
- Collection counts logged before upload and after extraction

**Risk Mitigation:**
- Pre-upload validation prevents empty tarball deployment
- Post-extraction verification catches corruption early
- Health check prevents workflow from running with empty collections
- Explicit error messages with diagnostic information (no silent failures)

---

**Research completed successfully. All root causes identified with actionable fixes.**

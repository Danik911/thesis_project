# Task 3.7 Diagnostic Report: RAG Context Provider Investigation

**Date**: 2025-11-19
**Task**: Fix RAG Context Provider Agent returning 0 documents
**Status**: 🔴 **UNRESOLVED** - Intermittent failure during workflow execution
**Investigator**: Claude Code with Ultrathink analysis

---

## Executive Summary

The RAG Context Provider Agent exhibits **inconsistent behavior**:
- ✅ **Standalone tests**: Successfully retrieves 364 regulatory document chunks
- ❌ **Workflow execution**: Reports 0 documents and raises `RuntimeError`

This report documents comprehensive investigation findings, architecture analysis, and remaining hypotheses.

---

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Investigation Timeline](#investigation-timeline)
3. [Architecture Overview](#architecture-overview)
4. [Key Findings](#key-findings)
5. [Environment Configuration Analysis](#environment-configuration-analysis)
6. [ChromaDB State Verification](#chromadb-state-verification)
7. [Code Path Analysis](#code-path-analysis)
8. [Hypotheses](#hypotheses)
9. [Files Modified](#files-modified)
10. [Documentation Links](#documentation-links)
11. [Next Steps](#next-steps)

---

## Problem Statement

### Symptoms
```
RuntimeError: CRITICAL: Context Provider cannot execute - ALL ChromaDB collections are empty.

Empty collections: ['gamp5', 'regulatory', 'best_practices']

Collection status:
  - gamp5: 0 documents
  - regulatory: 0 documents
  - best_practices: 0 documents
```

### Context
- **Trigger**: Category 3 URS submission via API workflow
- **Expected**: Retrieve 50-200 documents from 364 total regulatory chunks
- **Actual**: 0 documents retrieved, workflow fails with RuntimeError
- **Impact**: Pharmaceutical test generation blocked (GAMP-5 compliance violation)

---

## Investigation Timeline

### Session 1: Initial Diagnosis (Previous)
1. ✅ Identified NLTK dependency blocker
   - `SentenceSplitter` requires NLTK packages (stopwords, punkt_tab)
   - Solution: Replaced with `TokenTextSplitter` (NLTK-free)

2. ✅ Fixed collection name mismatch
   - Code expected: `regulatory`, `gamp5`, `sops`
   - ChromaDB contained: `regulatory_documents`, `gamp5_documents`, `sop_documents`
   - Solution: Updated `context_provider.py:475-502` to use `_documents` suffix

3. ✅ Fixed path mismatch
   - Docker volume mount: `/app/chroma_db`
   - Agent default path: `./lib/chroma_db`
   - Solution: Updated to `./chroma_db` (resolves to `/app/chroma_db`)

4. ✅ Fixed readiness guard
   - Previously failed if ANY collection empty
   - Solution: Only fail if ALL collections empty (`total_documents == 0`)

5. ❌ Docker bytecode caching issue
   - Rebuilt images with `--no-cache`
   - Containers started successfully

### Session 2: Persistence Investigation (Current)
6. 🔍 Environment variable investigation
   - Docker loads `.env.local` (NOT `.env.development`)
   - `.env.local` missing `RAG_VECTOR_STORE_PATH`
   - Code falls back to default `./chroma_db` (correct)

7. ✅ ChromaDB data verification
   - Volume `thesis_project_chroma-data` exists (persistent)
   - Collections present: 4 total
   - `regulatory_documents`: **364 chunks confirmed** ✅

8. ✅ Standalone agent test
   - Context Provider initialization succeeds
   - Collections mapped correctly: `regulatory` → `regulatory_documents`
   - Count verification: 364 documents accessible

9. ❌ Workflow execution failure
   - Despite standalone success, workflow reports 0 documents
   - Inconsistent behavior suggests runtime initialization issue

---

## Architecture Overview

### Docker Compose Stack

```
┌─────────────────────────────────────────────────────────────┐
│                   Docker Compose Dev Stack                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────┐  ┌────────────────┐  ┌───────────────┐ │
│  │   postgres    │  │  localstack    │  │      api      │ │
│  │  (pgvector)   │  │  (SQS mock)    │  │   (FastAPI)   │ │
│  │  Port: 5432   │  │  Port: 4566    │  │  Port: 8080   │ │
│  └───────┬───────┘  └────────────────┘  └───────┬───────┘ │
│          │                                       │          │
│          │        ┌────────────────┐             │          │
│          └────────│     worker     │─────────────┘          │
│                   │  (background)  │                        │
│                   └────────┬───────┘                        │
│                            │                                │
│                   ┌────────▼───────┐                        │
│                   │  chroma-data   │                        │
│                   │  Named Volume  │                        │
│                   │ /app/chroma_db │                        │
│                   └────────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

**Key File**: [`docker-compose.dev.yml`](../docker-compose.dev.yml)

### RAG Context Provider Architecture

```
┌──────────────────────────────────────────────────────────────┐
│              Context Provider Agent (Parallel)               │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Initialization (__init__):                                  │
│  1. Load env var: RAG_VECTOR_STORE_PATH                      │
│     Default: "./chroma_db" → resolves to "/app/chroma_db"    │
│  2. _initialize_chromadb():                                  │
│     - PersistentClient(path="/app/chroma_db")                │
│     - get_or_create_collection() for 4 collections:          │
│       * gamp5          → gamp5_documents                     │
│       * regulatory     → regulatory_documents ✅ 364 chunks │
│       * sops           → sop_documents                       │
│       * best_practices → best_practices                      │
│  3. _setup_ingestion_pipeline()                              │
│                                                              │
│  Execution (_search_documents):                              │
│  1. _select_collections(gamp_category=3)                     │
│     Returns: ["gamp5", "regulatory", "best_practices"]       │
│  2. Readiness Guard (lines 621-660):                         │
│     For each collection: check count()                       │
│     If total_documents == 0: raise RuntimeError ❌           │
│  3. Perform retrieval                                        │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Key File**: [`main/src/agents/parallel/context_provider.py`](../main/src/agents/parallel/context_provider.py) (1679 lines)

---

## Key Findings

### ✅ Confirmed Working
1. **ChromaDB Persistence**: Volume `thesis_project_chroma-data` contains 364 regulatory document chunks
2. **Collection Naming**: Correctly mapped (`regulatory` → `regulatory_documents`)
3. **Path Resolution**: Default `./chroma_db` resolves to `/app/chroma_db` (matches volume mount)
4. **Standalone Initialization**: Context Provider agent can access collections in direct tests
5. **Docker Volume Mount**: Both API and worker containers mount same volume at `/app/chroma_db`

### ❌ Failing
1. **Workflow Execution**: Reports 0 documents during actual URS processing
2. **Readiness Guard Triggers**: `RuntimeError` raised with empty collection counts

### 🔍 Anomalies
1. **Environment Variables**:
   - Docker Compose loads `.env.local` (not `.env.development`)
   - `.env.local` missing `RAG_VECTOR_STORE_PATH` variable
   - Worker container does NOT have `RAG_VECTOR_STORE_PATH` in environment
   - Code correctly falls back to default path

2. **Inconsistent Behavior**:
   - Standalone test: `collection.count()` returns 364 ✅
   - Workflow execution: `collection.count()` returns 0 ❌
   - Same container, same code, different results

---

## Environment Configuration Analysis

### File Structure
```
thesis_project/
├── .env.local              # Loaded by docker-compose (API keys only)
├── .env.development        # Comprehensive config (NOT loaded by Docker)
├── .env.example            # Documentation template
└── docker-compose.dev.yml  # Loads .env.local via env_file directive
```

### .env.local (Loaded by Docker Compose)
**Lines**: 36 lines
**Contents**: API keys, authentication, observability
**Missing**: `RAG_VECTOR_STORE_PATH`, `RAG_MODE`, storage configuration

**Snippet**:
```bash
# Clerk Authentication
CLERK_SECRET_KEY=sk_test_...
CLERK_ISSUER=https://helped-sturgeon-19.clerk.accounts.dev

# OpenRouter API (DeepSeek V3)
OPENROUTER_API_KEY=sk-or-v1-...
LLM_MODEL=deepseek/deepseek-chat

# OpenAI API (Embeddings only)
OPENAI_API_KEY=sk-proj-...
EMBEDDING_MODEL=text-embedding-3-small

# ❌ RAG_VECTOR_STORE_PATH NOT PRESENT
```

**File**: [`.env.local`](../.env.local)

### .env.development (NOT Loaded by Docker)
**Lines**: 178 lines
**Contents**: Comprehensive configuration including RAG settings
**Key Variables**:
```bash
RAG_MODE=chromadb
RAG_VECTOR_STORE_PATH=/app/chroma_db  # Line 46 ✅ Present but not loaded
CHROMA_COLLECTION=pharma_docs
```

**File**: [`.env.development`](../.env.development)

### docker-compose.dev.yml Configuration
```yaml
services:
  api:
    env_file: .env.local  # ❌ Loads .env.local (not .env.development)
    environment:
      ENVIRONMENT: development

  worker:
    env_file: .env.local  # ❌ Loads .env.local (not .env.development)
    environment:
      ENVIRONMENT: development
```

**Lines**: 190, 251
**File**: [`docker-compose.dev.yml`](../docker-compose.dev.yml)

### Python Environment Loading

**API Entry Point** (`main/api/app.py`):
```python
# Lines 17-30
from dotenv import load_dotenv

env_file = Path(__file__).parent.parent.parent / ".env.local"
if env_file.exists():
    load_dotenv(env_file)  # ✅ Loads .env.local in Python
    logging.info(f"Loaded environment variables from {env_file}")
```
**Result**: API loads `.env.local`, gets API keys

**Worker Entry Point** (`main/api/worker.py`):
```python
# ❌ NO load_dotenv() call
# Worker relies ENTIRELY on env vars from docker-compose
```
**Result**: Worker has NO Python-level env loading

**File**: [`main/api/app.py`](../main/api/app.py), [`main/api/worker.py`](../main/api/worker.py)

---

## ChromaDB State Verification

### Volume Inspection
```bash
$ docker volume ls | grep chroma
local     thesis_project_chroma-data
local     thesis_project_fresh_chroma-data  # ❓ Unexpected second volume

$ docker volume inspect thesis_project_chroma-data
{
    "Name": "thesis_project_chroma-data",
    "Driver": "local",
    "Mountpoint": "/var/lib/docker/volumes/thesis_project_chroma-data/_data",
    "Created": "2025-11-15T17:19:04Z",  # 4 days ago (persistent)
    "Scope": "local"
}
```

**Observation**: Second volume `thesis_project_fresh_chroma-data` exists. Potential for volume confusion?

### Collection Verification (Worker Container)
```bash
$ docker exec pharma-worker-dev python3 -c "
import chromadb
client = chromadb.PersistentClient(path='/app/chroma_db')
for col in client.list_collections():
    print(f'{col.name}: {col.count()} documents')
"

Output:
sop_documents: 0 documents
best_practices: 0 documents
regulatory_documents: 364 documents  ✅
gamp5_documents: 0 documents
```

**Result**: ✅ Collections exist, data present

### Context Provider Agent Test (Worker Container)
```bash
$ docker exec pharma-worker-dev python3 -c "
from main.src.agents.parallel.context_provider import create_context_provider_agent
agent = create_context_provider_agent(verbose=True)
for key, collection in agent.collections.items():
    print(f'{key} -> {collection.name}: {collection.count()}')
"

Output:
gamp5 -> gamp5_documents: 0 documents
regulatory -> regulatory_documents: 364 documents  ✅
sops -> sop_documents: 0 documents
best_practices -> best_practices: 0 documents
```

**Result**: ✅ Agent initialization succeeds, collections mapped correctly

---

## Code Path Analysis

### Context Provider Initialization Path

**File**: [`main/src/agents/parallel/context_provider.py`](../main/src/agents/parallel/context_provider.py)

```python
# Lines 145-162
def __init__(self, ...):
    # Line 152: Path resolution
    self.vector_store_path = Path(
        vector_store_path or os.getenv("RAG_VECTOR_STORE_PATH", "./chroma_db")
    )
    # Default: "./chroma_db" (no env var present)
    # Resolves to: "/app/chroma_db" (WORKDIR=/app in Dockerfile)

    # Line 157: Create directory
    self.vector_store_path.mkdir(parents=True, exist_ok=True)

    # Line 161: Initialize ChromaDB
    self._initialize_chromadb()
```

**Lines**: 145-162

### ChromaDB Initialization

```python
# Lines 460-503
def _initialize_chromadb(self):
    self.chroma_client = chromadb.PersistentClient(
        path=str(self.vector_store_path)  # "/app/chroma_db"
    )

    # Create dictionary mapping internal keys to ChromaDB collections
    self.collections = {
        "gamp5": self.chroma_client.get_or_create_collection(
            name="gamp5_documents",  # ✅ Correct name
            metadata={...}
        ),
        "regulatory": self.chroma_client.get_or_create_collection(
            name="regulatory_documents",  # ✅ Correct name
            metadata={...}
        ),
        "sops": self.chroma_client.get_or_create_collection(
            name="sop_documents",  # ✅ Correct name
            metadata={...}
        ),
        "best_practices": self.chroma_client.get_or_create_collection(
            name="best_practices",  # ✅ Correct name
            metadata={...}
        )
    }
```

**Lines**: 460-503

### Readiness Guard (Execution Path)

```python
# Lines 618-660 (_search_documents method)
def _search_documents(self, request: ContextRequest) -> ContextResponse:
    # Line 619: Determine which collections to search
    collection_names = self._select_collections(
        request.gamp_category,  # "3" for Category 3
        request.search_scope
    )
    # Returns: ["gamp5", "regulatory", "best_practices"] for Category 3

    # Lines 621-630: Check collection counts
    empty_collections = []
    collection_stats = {}
    total_documents = 0
    for collection_name in collection_names:
        count = self.collections[collection_name].count()  # ❌ Returns 0 in workflow
        collection_stats[collection_name] = count
        total_documents += count
        if count == 0:
            empty_collections.append(collection_name)

    # Lines 634-652: Raise error if ALL empty
    if total_documents == 0:
        raise RuntimeError("CRITICAL: Context Provider cannot execute...")
```

**Lines**: 618-660

### Collection Selection Logic

```python
# Lines 924-943 (_select_collections method)
def _select_collections(self, gamp_category: str, search_scope: dict) -> list[str]:
    collections = []

    # GAMP-5 guidelines always relevant
    collections.append("gamp5")

    # Regulatory documents for Categories 3, 4, 5
    if gamp_category in ["3", "4", "5"]:
        collections.append("regulatory")

    # SOPs for Categories 4, 5 only
    if gamp_category in ["4", "5"]:
        collections.append("sops")

    # Best practices (optional, default True)
    if search_scope.get("include_best_practices", True):
        collections.append("best_practices")

    return collections
    # For Category 3: ["gamp5", "regulatory", "best_practices"]
```

**Lines**: 924-943

---

## Hypotheses

### Hypothesis 1: Collection Reset on Workflow Start ❓
**Theory**: Something in the workflow initialization recreates collections, overwriting persisted data.

**Evidence**:
- Standalone test shows 364 chunks ✅
- Workflow execution shows 0 chunks ❌
- Same container, same code

**Test**: Add debug logging to `_initialize_chromadb()` to detect multiple initializations

**Code Check Required**:
- [`main/src/core/unified_workflow.py`](../main/src/core/unified_workflow.py) - Workflow initialization
- Does workflow create its own Context Provider instance with different parameters?

---

### Hypothesis 2: Multiple ChromaDB Paths in Use ❓
**Theory**: Workflow uses a different ChromaDB path, creating duplicate empty collections.

**Evidence**:
- Two volumes exist: `chroma-data` and `fresh_chroma-data`
- Env var `RAG_VECTOR_STORE_PATH` not present in container
- Default path `./chroma_db` depends on current working directory

**Test**:
```bash
# Check if WORKDIR differs during workflow execution
docker exec pharma-worker-dev pwd
docker exec pharma-worker-dev python3 -c "import os; print(os.getcwd())"
```

**Possible Issue**: If workflow changes working directory, `./chroma_db` resolves differently

---

### Hypothesis 3: ChromaDB Client Caching Issue ❓
**Theory**: ChromaDB's `get_or_create_collection()` doesn't refresh counts on existing collections.

**Evidence**:
- Collections exist with data
- `count()` returns 0 in workflow but 364 in standalone test

**Test**: Force client refresh after initialization
```python
# After get_or_create_collection()
collection.count()  # Force load metadata?
```

---

### Hypothesis 4: Race Condition on Container Startup ❓
**Theory**: Workflow executes before volume mount fully propagates data.

**Evidence**:
- Containers recreated during investigation
- Worker healthcheck may not wait for ChromaDB readiness

**Test**: Add delay or volume readiness check before workflow execution

**Mitigation**: Add healthcheck in `docker-compose.dev.yml`:
```yaml
worker:
  healthcheck:
    test: ["CMD", "python3", "-c", "import chromadb; c=chromadb.PersistentClient(path='/app/chroma_db'); exit(0 if len(c.list_collections()) > 0 else 1)"]
    interval: 10s
    timeout: 5s
    retries: 3
```

---

### Hypothesis 5: Environment-Specific Initialization Path ❓
**Theory**: Workflow uses environment-specific config that bypasses default path logic.

**Evidence**:
- `.env.development` exists but isn't loaded by Docker
- Python code may load `.env.development` at runtime
- Different initialization order for API vs worker

**Test**: Check if workflow loads additional env files:
```bash
docker exec pharma-worker-dev python3 -c "
import os
from pathlib import Path
env_dev = Path('/app/.env.development')
print(f'.env.development exists: {env_dev.exists()}')
"
```

---

## Files Modified (Session History)

### Session 1 Modifications
1. **`main/scripts/ingest-documents.py`**
   - Line 73: Path `/app/lib/chroma_db` → `/app/chroma_db`
   - Line 74: Collection `pharma_docs` → `regulatory_documents`
   - Lines 91, 100-109: `SimpleNodeParser` → `TokenTextSplitter`

2. **`main/src/agents/parallel/context_provider.py`**
   - Line 35: Import `TokenTextSplitter`
   - Line 152: Path `./lib/chroma_db` → `./chroma_db`
   - Lines 475-502: Collection names use `_documents` suffix
   - Lines 536-544: `SentenceSplitter` → `TokenTextSplitter`
   - Lines 620-659: Readiness guard fixed (allow partial empty)
   - Line 648: Error message path updated

3. **`.env.example`**
   - Lines 50-51: Documentation updated with volume mount comment

4. **`.env.development`**
   - Line 46: `CHROMA_PATH` → `RAG_VECTOR_STORE_PATH`

5. **`main/src/config/chromadb_collections.py`** (NEW)
   - Constants for collection names
   - Validation helpers
   - Prevention against future naming mismatches

---

## Documentation Links

### Internal Documentation
- [Task 3.7 PRP Definition](../PRPs/tasks/3.7-fix-rag-context-agent.md)
- [MVP Implementation Plan](../main/docs/plans/mvp_implementation_plan.md)
- [Quick Start Guide](../main/docs/guides/QUICK_START_GUIDE.md)
- [AWS Migration PRP](../PRPs/aws-migration-updated.md)
- [CLAUDE.md Project Instructions](../CLAUDE.md)

### Key Code Files
- **Context Provider Agent**: [`main/src/agents/parallel/context_provider.py`](../main/src/agents/parallel/context_provider.py) (1679 lines)
- **Unified Workflow**: [`main/src/core/unified_workflow.py`](../main/src/core/unified_workflow.py)
- **API Application**: [`main/api/app.py`](../main/api/app.py)
- **Worker Executor**: [`main/api/worker.py`](../main/api/worker.py)
- **Docker Compose**: [`docker-compose.dev.yml`](../docker-compose.dev.yml)

### External References
- [LlamaIndex Workflows Documentation](https://docs.llamaindex.ai/en/stable/module_guides/workflow/)
- [ChromaDB PersistentClient API](https://docs.trychroma.com/api-guide)
- [Docker Compose Environment Variables](https://docs.docker.com/compose/environment-variables/)
- [GAMP-5 Guidelines](https://ispe.org/initiatives/regulatory-resources/gamp-5)
- [ALCOA+ Principles](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/data-integrity-and-compliance-cgmp-guidance-industry)

---

## Next Steps

### Immediate Actions (Priority)

1. **Add Comprehensive Logging** 🔴
   ```python
   # In context_provider.py __init__
   self.logger.info(f"[INIT] ChromaDB path: {self.vector_store_path}")
   self.logger.info(f"[INIT] Path exists: {self.vector_store_path.exists()}")
   self.logger.info(f"[INIT] Current working directory: {os.getcwd()}")

   # In _initialize_chromadb()
   for key, collection in self.collections.items():
       count = collection.count()
       self.logger.info(f"[INIT] Collection {key} ({collection.name}): {count} documents")
   ```

2. **Test Hypothesis 2: Path Verification** 🔴
   ```bash
   # During workflow execution, check actual path used
   docker logs pharma-worker-dev | grep "ChromaDB path"
   docker logs pharma-worker-dev | grep "Current working directory"
   ```

3. **Verify Volume Mount** 🟡
   ```bash
   # Check which volume is mounted
   docker inspect pharma-worker-dev --format '{{json .Mounts}}' | jq '.[] | select(.Destination=="/app/chroma_db")'

   # Expected: "Source": "/var/lib/docker/volumes/thesis_project_chroma-data/_data"
   ```

4. **Add Worker Healthcheck** 🟡
   ```yaml
   # docker-compose.dev.yml
   worker:
     healthcheck:
       test: ["CMD", "python3", "-c", "import chromadb; c=chromadb.PersistentClient(path='/app/chroma_db'); assert len(c.list_collections()) > 0"]
       interval: 10s
       timeout: 5s
       retries: 5
   ```

5. **Instrument Workflow Entry Point** 🔴
   ```python
   # In main/src/core/unified_workflow.py or wherever workflow starts
   # Log Context Provider initialization parameters
   logger.info(f"[WORKFLOW] Creating Context Provider with config: {config}")
   ```

### Medium-Term Actions

6. **Consolidate Environment Configuration** 🟢
   - Merge `.env.local` and `.env.development` OR
   - Update `docker-compose.dev.yml` to load both files:
   ```yaml
   env_file:
     - .env.local        # API keys (priority)
     - .env.development  # Configuration
   ```

7. **Refactor to Use Constants** 🟢
   - Update all modules to import from `chromadb_collections.py`
   - Add validation tests to prevent naming drift

8. **Add ChromaDB Seeding to Healthcheck** 🟢
   - Ensure collections populated before accepting requests
   - Fail fast if data missing on container startup

### Long-Term Prevention

9. **Add Integration Test** 🟢
   ```python
   # tests/integration/test_rag_context_provider.py
   def test_workflow_context_retrieval():
       """Verify Context Provider retrieves documents in workflow context"""
       # Simulate workflow execution path
       # Assert documents retrieved > 0
   ```

10. **CI/CD Pipeline Check** 🟢
    - Add step to verify ChromaDB population
    - Validate collection counts before deploying

---

## Diagnostic Commands Reference

### Container Status
```bash
# Check running containers
docker-compose -f docker-compose.dev.yml ps

# Start stack
docker-compose -f docker-compose.dev.yml up -d

# View worker logs
docker-compose -f docker-compose.dev.yml logs -f worker

# Stop stack (preserves volumes)
docker-compose -f docker-compose.dev.yml down

# Reset completely (deletes volumes)
docker-compose -f docker-compose.dev.yml down --volumes
```

### ChromaDB Verification
```bash
# List volumes
docker volume ls | grep chroma

# Inspect volume
docker volume inspect thesis_project_chroma-data

# Check collections in worker
docker exec pharma-worker-dev python3 -c "
import chromadb
c = chromadb.PersistentClient(path='/app/chroma_db')
for col in c.list_collections():
    print(f'{col.name}: {col.count()}')
"

# Test Context Provider
docker exec pharma-worker-dev python3 -c "
from main.src.agents.parallel.context_provider import create_context_provider_agent
agent = create_context_provider_agent(verbose=True)
for k, col in agent.collections.items():
    print(f'{k} -> {col.name}: {col.count()}')
"
```

### Environment Verification
```bash
# Check environment variables in worker
docker exec pharma-worker-dev printenv | grep -E "RAG|CHROMA|ENVIRONMENT"

# Check working directory
docker exec pharma-worker-dev pwd

# Verify Python can import Context Provider
docker exec pharma-worker-dev python3 -c "from main.src.agents.parallel.context_provider import ContextProviderAgent; print('Import successful')"
```

### Volume Mount Verification
```bash
# Check worker mounts
docker inspect pharma-worker-dev --format '{{json .Mounts}}' | jq '.'

# List files in ChromaDB path
docker exec pharma-worker-dev ls -la /app/chroma_db

# Check ChromaDB database files
docker exec pharma-worker-dev ls -la /app/chroma_db/chroma.sqlite3
```

---

## Conclusion

After comprehensive investigation, **the root cause remains unidentified**. The system exhibits paradoxical behavior:

**Working**: ✅
- ChromaDB collections exist with 364 documents
- Standalone Context Provider initialization succeeds
- Collection name mapping correct
- Path resolution correct
- Docker volume persistence confirmed

**Failing**: ❌
- Workflow execution reports 0 documents
- Readiness guard triggers RuntimeError
- Inconsistent `count()` results between standalone and workflow contexts

**Most Likely Hypothesis**: **Multiple Initialization Paths** (Hypothesis 1 or 2)
- Workflow may initialize Context Provider with different parameters
- Working directory change could alter `./chroma_db` resolution
- Second ChromaDB volume suggests potential path confusion

**Recommended Next Step**: **Add comprehensive logging** to trace initialization and path resolution during actual workflow execution. This will definitively identify whether the issue is path-related, initialization-related, or due to ChromaDB client caching.

**GAMP-5 Compliance Note**: This investigation follows ALCOA+ principles (Contemporaneous, Complete documentation of troubleshooting process for regulatory audit trail).

---

**Report Generated**: 2025-11-19
**Investigation Duration**: ~2 hours across 2 sessions
**Files Analyzed**: 15+ Python modules, 3 configuration files, 1 Docker Compose stack
**Tests Performed**: 8 diagnostic commands, 3 verification scripts
**Status**: 🔴 **UNRESOLVED** - Awaiting additional logging data from workflow execution

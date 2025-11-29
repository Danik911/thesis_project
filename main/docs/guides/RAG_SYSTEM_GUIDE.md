# RAG System Guide - Pharmaceutical Test Generation

**Last Updated:** 2025-11-29
**Status:** Production Ready
**Observability:** LangFuse Cloud (Phoenix deprecated)

---

## Overview

The RAG (Retrieval-Augmented Generation) system provides contextual pharmaceutical regulatory knowledge to the test generation workflow. It uses ChromaDB as the vector store with OpenAI embeddings for semantic search.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         RAG System Architecture                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────┐  │
│  │   URS Document   │───▶│  Unified Workflow │───▶│   Context    │  │
│  │   (User Input)   │    │                  │    │   Provider   │  │
│  └──────────────────┘    └──────────────────┘    │    Agent     │  │
│                                                   └──────┬───────┘  │
│                                                          │          │
│                                                          ▼          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                      ChromaDB Vector Store                    │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐  │  │
│  │  │ regulatory_docs │  │  gamp5_docs     │  │ best_practices│  │  │
│  │  │   (182 chunks)  │  │  (auto-created) │  │ (auto-created)│  │  │
│  │  └─────────────────┘  └─────────────────┘  └──────────────┘  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                 │                                   │
│                                 ▼                                   │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    OpenAI Embeddings API                      │  │
│  │                   text-embedding-3-small                      │  │
│  │                     (1536 dimensions)                         │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Key Files

```
thesis_project/
├── main/
│   ├── src/
│   │   ├── agents/parallel/
│   │   │   └── context_provider.py      # RAG agent (query + retrieval)
│   │   ├── adapters/
│   │   │   └── chroma_adapter.py        # ChromaDB adapter (unused)
│   │   └── config/
│   │       └── chromadb_collections.py  # Collection definitions
│   ├── scripts/
│   │   ├── ingest-documents.py          # Primary ingestion script
│   │   └── seed_chroma.py               # Alternative seeding (has bugs)
│   └── docs/
│       └── regulatory_guides/           # Source documents (5 files)
│           ├── ISPE - GAMP 5_...md      # GAMP-5 guidelines
│           ├── FDA Part-11...md         # 21 CFR Part 11
│           ├── ICH guideline Q9.md      # Quality Risk Management
│           ├── ISO IEC 27001.md         # Information Security
│           └── ISPE Baseline...md       # Commissioning & Qualification
├── docker-compose.dev.yml               # Volume: chroma-data
└── scripts/
    └── seed_chroma.py                   # Root-level seeder (has bugs)
```

---

## Docker Volume Configuration

ChromaDB data is stored in a **Docker named volume**, not a bind mount:

```yaml
# docker-compose.dev.yml
volumes:
  - chroma-data:/app/chroma_db  # Named volume

volumes:
  chroma-data:
    driver: local
```

**Important:** The local `main/chroma_db/` directory is NOT used by Docker containers.

---

## Common Issues and Solutions

### Issue 1: "Could not connect to tenant default_tenant"

**Symptom:**
```
chromadb.errors.InternalError: Could not connect to tenant default_tenant. Are you sure it exists?
```

**Root Cause:**
- Docker volume is empty or corrupted
- Volume was deleted with `docker-compose down --volumes`
- Permission issues in the volume

**Solution:**
```bash
# 1. Fix permissions
docker exec -u root pharma-api-dev chown -R appuser:appuser /app/chroma_db

# 2. Re-ingest documents
docker exec -it pharma-api-dev python /app/main/scripts/ingest-documents.py
```

---

### Issue 2: "unable to open database file"

**Symptom:**
```
chromadb.errors.InternalError: error returned from database: (code: 14) unable to open database file
```

**Root Cause:**
- Volume directory owned by `root` but container runs as `appuser`
- Empty volume directory

**Diagnosis:**
```bash
# Check ownership
docker exec pharma-api-dev ls -la /app/chroma_db
# Should show: drwxr-xr-x appuser appuser (NOT root root)
```

**Solution:**
```bash
docker exec -u root pharma-api-dev chown -R appuser:appuser /app/chroma_db
```

---

### Issue 3: Embedding Dimension Mismatch

**Symptom:**
```
Error calculating similarity: shapes (1536,) and (3072,) not aligned
```

**Root Cause:**
- Database contains embeddings from different models
- `text-embedding-3-small` = 1536 dimensions
- `text-embedding-ada-002` = 3072 dimensions

**Solution:**
```bash
# Delete and re-ingest with consistent model
docker volume rm thesis_project_chroma-data
docker-compose -f docker-compose.dev.yml up -d
docker exec -it pharma-api-dev python /app/main/scripts/ingest-documents.py
```

---

### Issue 4: Empty Collections / Zero Documents Retrieved

**Symptom:**
- `documents_retrieved: 0` in Langfuse traces
- `context_quality: "poor"`
- Workflow continues with no RAG context

**Root Cause:**
- Collections never seeded after container rebuild
- Volume deleted without re-ingestion

**Solution:**
```bash
# Check collection status
docker exec pharma-worker-dev python3 -c "
import chromadb
c = chromadb.PersistentClient(path='/app/chroma_db')
for col in c.list_collections():
    print(f'{col.name}: {col.count()} documents')
"

# If empty, re-ingest
docker exec -it pharma-api-dev python /app/main/scripts/ingest-documents.py
```

---

### Issue 5: Rate Limit Exhaustion During Ingestion

**Symptom:**
- `RateLimitError` during document ingestion
- Ingestion stuck at 73% or similar

**Root Cause:**
- Too many embedding API calls
- LlamaIndex extractors defaulting to GPT-3.5-turbo

**Solution:**
- Use `TokenTextSplitter` instead of `SentenceSplitter` (NLTK-free)
- Batch embedding requests
- Use embedding cache for repeated documents

---

### Issue 6: GAMP Category Format Issues

**Symptom:**
- Wrong collections selected during search
- Missing regulatory context

**Root Cause:**
- GAMP category format mismatch: `"Category_5"` vs `"5"`

**Solution:**
- Standardize to simple format: `"5"`, `"4"`, `"3"`, `"1"`
- Already fixed in `context_provider.py` (uses `str(gamp_category)`)

---

## Health Check Commands

### Quick Status Check
```bash
docker exec pharma-worker-dev python3 -c "
import chromadb
c = chromadb.PersistentClient(path='/app/chroma_db')
print('=== ChromaDB Health ===')
cols = c.list_collections()
print(f'Collections: {len(cols)}')
for col in cols:
    print(f'  - {col.name}: {col.count()} docs')
"
```

### Test Query
```bash
docker exec pharma-worker-dev python3 -c "
import chromadb
c = chromadb.PersistentClient(path='/app/chroma_db')
col = c.get_collection('regulatory_documents')
results = col.query(query_texts=['GAMP-5 validation requirements'], n_results=3)
print('Query: GAMP-5 validation requirements')
print(f'Results: {len(results[\"ids\"][0])} documents')
for doc in results['documents'][0][:2]:
    print(f'  - {doc[:80]}...')
"
```

### Volume Inspection
```bash
# Check volume exists
docker volume ls | grep chroma

# Check volume contents
docker run --rm -v thesis_project_chroma-data:/data alpine ls -la /data

# Check volume size
docker system df -v | grep chroma
```

---

## Ingestion Workflow

### Standard Ingestion (Recommended)
```bash
# Uses ingest-documents.py - creates regulatory_documents collection
docker exec -it pharma-api-dev python /app/main/scripts/ingest-documents.py
```

**Output:**
```
=== ChromaDB Regulatory Document Ingestion ===
[Step 1/2] Validating regulatory documents...
  FOUND: ISPE - GAMP 5_... (61,779 bytes)
  FOUND: FDA Part-11... (27,766 bytes)
  ...
[Step 2/2] Ingesting documents into ChromaDB...
  Parsing nodes: 100% 5/5
  Generating embeddings: 100% 182/182
  Documents processed: 5
  Chunks created: 182
  Ingestion duration: 9.2s
=== INGESTION COMPLETE ===
```

### Full Reset
```bash
# Stop containers
docker-compose -f docker-compose.dev.yml down

# Delete volume
docker volume rm thesis_project_chroma-data

# Start containers (creates fresh volume)
docker-compose -f docker-compose.dev.yml up -d

# Fix permissions and ingest
docker exec -u root pharma-api-dev chown -R appuser:appuser /app/chroma_db
docker exec -it pharma-api-dev python /app/main/scripts/ingest-documents.py
```

---

## Configuration

### Environment Variables
```bash
# Required
OPENAI_API_KEY=sk-...              # For embeddings

# Optional (defaults shown)
RAG_VECTOR_STORE_PATH=/app/chroma_db
RAG_CACHE_DIR=/app/cache/rag
EMBEDDING_MODEL=text-embedding-3-small
RAG_CHUNK_SIZE=1024
RAG_CHUNK_OVERLAP=200
```

### Collections Structure

The Context Provider Agent expects these collections:
```python
collections = {
    "gamp5": "gamp5_documents",
    "regulatory": "regulatory_documents",  # Primary collection
    "sops": "sop_documents",
    "best_practices": "best_practices"
}
```

**Note:** Only `regulatory_documents` needs to be populated. The readiness guard allows workflow to proceed if at least one collection has documents.

---

## Troubleshooting Flowchart

```
RAG Not Working?
       │
       ▼
┌──────────────────┐
│ Check container  │
│ logs for errors  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐     Yes    ┌──────────────────┐
│ "tenant" or      │───────────▶│ Fix permissions  │
│ "database file"  │            │ and re-ingest    │
│ error?           │            └──────────────────┘
└────────┬─────────┘
         │ No
         ▼
┌──────────────────┐     Yes    ┌──────────────────┐
│ Collections      │───────────▶│ Run ingestion    │
│ empty?           │            │ script           │
└────────┬─────────┘            └──────────────────┘
         │ No
         ▼
┌──────────────────┐     Yes    ┌──────────────────┐
│ Dimension        │───────────▶│ Delete volume    │
│ mismatch?        │            │ and re-ingest    │
└────────┬─────────┘            └──────────────────┘
         │ No
         ▼
┌──────────────────┐
│ Check OPENAI_API │
│ _KEY is set      │
└──────────────────┘
```

---

## GAMP-5 Compliance Notes

### ALCOA+ Requirements for RAG
- **Attributable:** Document source tracked in metadata
- **Legible:** Human-readable collection names
- **Contemporaneous:** `ingested_at` timestamp in metadata
- **Original:** Source files preserved in `docs/regulatory_guides/`
- **Accurate:** Consistent embedding model (1536 dimensions)
- **Complete:** All 5 regulatory documents ingested
- **Consistent:** Deterministic chunking with `TokenTextSplitter`
- **Enduring:** Persistent Docker volume
- **Available:** Accessible to all workflow containers

### Audit Trail
All RAG operations are traced in LangFuse with:
- Query text
- Documents retrieved
- Confidence scores
- Processing time
- Collection searched

---

## Related Documentation

- [PRPs/tasks/3.7-fix-rag-context-agent.md](../../../PRPs/tasks/3.7-fix-rag-context-agent.md) - RAG fix task
- [archive/docs/old_issues/RAG_SYSTEM_ISSUES_UPDATED.md](../../../archive/docs/old_issues/RAG_SYSTEM_ISSUES_UPDATED.md) - Historical issues
- [QUICK_START_GUIDE.md](./QUICK_START_GUIDE.md) - Getting started

---

## Version History

| Date | Change | Author |
|------|--------|--------|
| 2025-11-29 | Added Docker volume permission fix, tenant error solution | Claude |
| 2025-11-19 | Task 3.7 RAG fix (commit 10485cb) | Daniil |
| 2025-07-30 | Phoenix observability validation | Daniil |

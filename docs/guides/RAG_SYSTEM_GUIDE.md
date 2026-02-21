# RAG System Guide - Pharmaceutical Test Generation

**Last Updated:** 2026-02-20
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

---

## AI4LIMS RAG System

The AI4LIMS PoC has its own independent RAG system using ChromaDB. It is entirely separate from the thesis RAG system above (different collections, different embeddings, different seeding pipeline).

---

### Collections

| Collection | Size | Source | Description |
|------------|------|--------|-------------|
| `mda_templates` | 325 chunks | 25 XLSX files (MDA templates) | Sheet-level markdown table chunks, 13 per XLSX |
| `lims_standards` | 154 chunks | SOPs / standards documents | Regulatory standards for MDA generation |
| `calculation_patterns` | (varies) | Calculation pattern docs | Reusable calculation templates |

**Embedding model:** ChromaDB default (sentence-transformers, local — no OpenAI key required).

---

### Sheet-Level Chunking Architecture

**File:** `main/src/lims/chunking.py`

Before this change, each XLSX file was ingested as a single monolithic text blob (25 blobs total). The new chunker splits each XLSX into one chunk per sheet plus a summary chunk, producing 13 chunks per file (12 sheets + 1 summary = 325 chunks total for 25 files).

Each chunk is stored with metadata:
- `file_name` — source XLSX filename
- `sheet_name` — worksheet name within the file
- `is_priority` — `True` for high-signal sheets (Analysis, Component, Calc Variable, Calculation)
- `chunk_type` — `"sheet"` or `"summary"`

Priority sheets are flagged so downstream queries can weight them higher.

**Configuration** (`main/src/lims/config.py`):
```bash
LIMS_RAG_CHUNK_MAX_SIZE=2000    # Max characters per chunk (default: 2000)
```

---

### Langfuse Tracing

All LIMS pipeline stages are traced end-to-end in Langfuse Cloud using `@observe` decorators from Langfuse v3 (`from langfuse import get_client, observe`).

**File:** `main/src/lims/langfuse_tracing.py` — LIMS-specific Langfuse client init, get, and flush helpers.

**Full trace tree:**

```
lims-two-layer-pipeline (parent trace)
├── lims-classify
├── lims-focused-extract
├── lims-augment
│   └── rag-standards-query (auto-nested)
├── lims-merge
└── lims-chat (when user interacts)
    └── rag-mda-templates-query (auto-nested)
```

**Tracing integration:**

| Location | Decorator | Span Name |
|----------|-----------|-----------|
| `pipeline.py` — `TwoLayerPipeline.run()` | `@observe` | `lims-two-layer-pipeline` (parent trace) |
| `classifier.py` — `TestTypeClassifier.classify()` | `@observe` | `lims-classify` |
| `focused_extractor.py` — `focused_extract()` | `@observe` | `lims-focused-extract` |
| `pipeline.py` — `_augment_gaps()` | `@observe` | `lims-augment` |
| `merger.py` — `merge_layers()` | `@observe` | `lims-merge` |
| `chat_agent.py` — `ChatSession.chat()` | `@observe` | `lims-chat` |
| `mda_generator.py` — `generate_mda()` | `@observe` | `lims-mda-generate` |
| `rag_loader.py` — `query_similar_templates()` | `@observe` | `rag-mda-templates-query` |
| `rag_loader.py` — `query_similar_templates_with_scores()` | `@observe` | `rag-mda-templates-query-scored` |
| `standards_loader.py` — `query_standards()` | `@observe` | `rag-standards-query` |

Child `@observe` decorators auto-nest under the parent `TwoLayerPipeline.run()` trace. The parent trace uses `capture_input=False, capture_output=False` to avoid serializing PDF bytes.

The API (`lims_router.py`) captures `trace_id` and `trace_url` after the pipeline completes and returns them in the `/lims/extract` response. Langfuse is flushed after each pipeline run.

Distance values (ChromaDB L2) are logged as span attributes and are visible in the Langfuse Cloud dashboard.

---

### RAG Evaluation Framework

**Files:**
- `main/src/lims/rag_evaluator.py` — Core evaluation logic (Hit Rate@k, MRR, Precision@k)
- `scripts/evaluate_rag.py` — CLI runner with parameter sweep support

**Metrics computed:**

| Metric | Description |
|--------|-------------|
| Hit Rate@k | Fraction of queries where the relevant document appears in top-k results |
| MRR | Mean Reciprocal Rank — rewards higher-ranked relevant results |
| Precision@k | Fraction of top-k results that are relevant |
| Mean Distance | Average ChromaDB L2 distance (lower = more similar) |

**Parameter sweep results** (collection: `mda_templates`, 11 evaluation queries):

| top_k | Hit Rate | MRR   | Precision@k | Mean Distance |
|-------|----------|-------|-------------|---------------|
| 1     | 0.909    | 0.909 | 0.909       | 1.2842        |
| 3     | 1.000    | 0.955 | 0.727       | 1.3426        |
| 5     | 1.000    | 0.955 | 0.527       | 1.3792        |
| 10    | 1.000    | 0.955 | 0.318       | 1.4259        |

**Selected default:** `top_k=3` — 100% Hit Rate with acceptable Precision.

---

### Configuration Parameters

Four new environment variables added to `main/src/lims/config.py`:

```bash
# LIMS RAG tuning
LIMS_RAG_MDA_TOP_K=3                  # top-k for mda_templates queries (default: 3)
LIMS_RAG_STANDARDS_TOP_K=5            # top-k for lims_standards queries (default: 5)
LIMS_RAG_CHUNK_MAX_SIZE=2000          # Max chars per chunk during seeding (default: 2000)
LIMS_RAG_SIMILARITY_THRESHOLD=0.0     # Min similarity threshold; 0.0 = no filter (range: 0.0–2.0 L2)
```

Note: ChromaDB uses L2 distance (lower = more similar, range ~0.0–2.0). A threshold of `0.0` disables filtering.

---

### Key Commands

**Seed collections from XLSX files:**
```bash
# Seeds mda_templates collection with sheet-level chunks
uv run python scripts/populate_lims_chroma.py
```

**Run RAG evaluation (single top_k):**
```bash
uv run python scripts/evaluate_rag.py --collection mda_templates --top-k 3
```

**Run parameter sweep (all top_k values):**
```bash
uv run python scripts/evaluate_rag.py --collection mda_templates --sweep
```

**Run with Langfuse tracing enabled:**
```bash
uv run python scripts/evaluate_rag.py --collection mda_templates --sweep --langfuse
```

**Run E2E pipeline test:**
```bash
uv run python scripts/test_e2e_pipeline.py
```

---

### Key Files

| File | Purpose |
|------|---------|
| `main/src/lims/chunking.py` | Sheet-level XLSX chunker; produces markdown table chunks per sheet |
| `main/src/lims/rag_evaluator.py` | Hit Rate@k, MRR, Precision@k evaluation metrics |
| `main/src/lims/langfuse_tracing.py` | LIMS Langfuse client init, get, flush |
| `main/src/lims/rag_loader.py` | `mda_templates` collection queries; `@observe` tracing; returns distances |
| `main/src/lims/standards_loader.py` | `lims_standards` collection queries; `@observe` tracing; returns distances |
| `main/src/lims/pipeline.py` | `_augment_gaps()` RAG + LLM with Langfuse spans |
| `main/src/lims/mda_generator.py` | `generate_mda()` RAG + LLM with Langfuse spans |
| `main/src/lims/config.py` | `LIMS_RAG_*` config fields |
| `scripts/evaluate_rag.py` | CLI evaluation runner with `--sweep`, `--langfuse` flags |
| `scripts/populate_lims_chroma.py` | Seeds ChromaDB from XLSX files using sheet-level chunks |
| `scripts/test_e2e_pipeline.py` | Standalone E2E pipeline test |
| `main/tests/lims/test_chunking.py` | 12 unit tests for chunking.py |
| `main/tests/lims/test_rag_evaluator.py` | 11 unit tests for rag_evaluator.py |

---

## Related Documentation

- [PRPs/tasks/3.7-fix-rag-context-agent.md](../../../PRPs/tasks/3.7-fix-rag-context-agent.md) - RAG fix task
- [archive/docs/old_issues/RAG_SYSTEM_ISSUES_UPDATED.md](../../../archive/docs/old_issues/RAG_SYSTEM_ISSUES_UPDATED.md) - Historical issues
- [QUICK_START_GUIDE.md](./QUICK_START_GUIDE.md) - Getting started

---

## Version History

| Date | Change | Author |
|------|--------|--------|
| 2026-02-20 | Added AI4LIMS RAG System section: sheet-level chunking (325 chunks), Langfuse tracing, RAG evaluation framework, parameter sweep results, config parameters | Claude |
| 2025-11-29 | Added Docker volume permission fix, tenant error solution | Claude |
| 2025-11-19 | Task 3.7 RAG fix (commit 10485cb) | Daniil |
| 2025-07-30 | Phoenix observability validation | Daniil |

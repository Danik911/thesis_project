# Current Task Context

## Active Task
**Task ID:** 3.7
**Task Name:** Fix RAG Context Provider Agent
**Phase:** 3 - Containerization & Local DevOps
**Status:** ready_to_start
**Priority:** HIGH
**Started:** Not yet started

---

## Task Objective
Fix Context Provider Agent to successfully retrieve RAG documents from ChromaDB, preventing the "poor" context quality that degrades downstream SME and OQ generation agents.

## Problem Statement

**Current Behavior (BROKEN)**:
- Context Provider Agent executes without error
- Returns `documents_retrieved: 0` for all collections (gamp5, regulatory, best_practices)
- ChromaDB collections empty (`document_count: 0`)
- Downstream agents operate without RAG context (`context_quality: "poor"`, `confidence_score: 0`)
- Silent failure - workflow continues despite missing critical context
- ALCOA+ violation - no audit trail for context retrieval failure

**Evidence**: Langfuse trace `76f363c24dc087450c73d473128d48ad` from successful Task 3.6 completion

## Root Causes

1. **Collections never seeded** - ChromaDB collections empty, never populated with corpus documents
2. **Strict metadata filters** - `_apply_metadata_filters` drops docs if metadata key absent
3. **Missing configuration** - No validation of OPENAI_API_KEY, RAG_VECTOR_STORE_PATH, RAG_CACHE_DIR
4. **No fallback / readiness guard** - Silent failure without explicit error

## Success Criteria

1. ChromaDB collections populated (>100 documents each for gamp5/regulatory, >50 for best_practices)
2. RAG retrieval functional (50-200 relevant chunks per query)
3. `context_quality`: "medium" or better
4. Readiness guard prevents silent failures
5. Metadata filtering hardened (handles missing keys)
6. Configuration validation at startup
7. End-to-end validation confirmed via Langfuse trace

## Implementation Phases

### Phase 1: Create Corpus Seeding Script
- File: `scripts/seed_chroma.py`
- Ingest documents from `datasets/corpus_3/` into ChromaDB collections
- Verify persistence in `lib/chroma_db/chroma.sqlite3`

### Phase 2: Add Readiness Guard
- File: `main/src/agents/parallel/context_provider.py`
- Location: Inside `_search_documents()` before retrieval loop
- Fail fast if collections empty with actionable error message

### Phase 3: Harden Metadata Filtering
- File: `main/src/agents/parallel/context_provider.py`
- Location: Inside `_apply_metadata_filters()` method
- Use `.get()` instead of direct access, handle missing keys gracefully

### Phase 4: Configuration Validation
- File: `main/src/agents/parallel/context_provider.py`
- Location: Inside `__init__()` method
- Validate required env vars at instantiation

### Phase 5: Fallback Context (Optional)
- File: `main/src/agents/parallel/context_provider.py`
- Location: Inside `_execute_context_retrieval()` method
- Load baseline markdown if RAG returns zero results
- Flag with `fallback_used: true`

## Key Files

**To Create:**
1. `scripts/seed_chroma.py` (~80 lines)
2. `datasets/baselines/category3_context.md` (~500 lines)
3. `docs/RAG_SEEDING_GUIDE.md` (~300 lines)

**To Modify:**
1. `main/src/agents/parallel/context_provider.py` (~60 lines total across 4 methods)
2. `.env.local` or `.env.development` (ensure RAG env vars present)
3. `docker-compose.dev.yml` (mount `./lib/chroma_db:/app/lib/chroma_db:rw`)

## Reference Documentation

**Analysis File:** `docs/context_agent_analysis.md`
**Task Specification:** `PRPs/tasks/3.7-fix-rag-context-agent.md`
**Previous Task:** `PRPs/tasks/3.6-fix-test-generation.md` (✅ completed)

## Dependencies

- ✅ Task 3.6 completed (workflow end-to-end functional)
- ✅ ChromaDB working (Task 1.2)
- ✅ OpenAI embeddings configured (Task 3.5)
- ⏸️ Corpus documents available in `datasets/corpus_3/` (assume present or create during execution)

## Estimated Effort
**Total:** 2.5 hours
- Phase 1 (Seeding): 30 min
- Phase 2 (Readiness Guard): 15 min
- Phase 3 (Metadata Hardening): 20 min
- Phase 4 (Config Validation): 15 min
- Phase 5 (Fallback Context): 30 min
- Testing & Validation: 45 min

## Compliance Requirements

**GAMP-5:** Category 5 (Custom Software - RAG infrastructure)
**ALCOA+:** All 9 principles enforced
**NO FALLBACK LOGIC:**
- ✅ Readiness guard fails explicitly if collections empty
- ✅ Configuration validation raises on missing env vars
- ✅ Fallback context flagged (not silent)
- ❌ NO silent continuation with zero RAG results

## Next Task
**Task 3.8:** Fix local test script visibility (change to bind mount)

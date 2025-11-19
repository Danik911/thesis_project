# Context Provider Agent Analysis

## Summary
- **Incident:** Context Provider Agent returned `documents_retrieved = 0`, leading to "poor" context and low confidence across the workflow.
- **Evidence Sources:**
  - Langfuse trace `main/logs/langfuse/trace-with-observations-76f363c24dc087450c73d473128d48ad.json` (IDs `context_provider.process_request`, `chromadb.search_collection.*`).
  - Code paths in `main/src/agents/parallel/context_provider.py` (Chroma initialization, retrieval, and ingestion routines).
- **Impact:** Downstream SME and research agents operated without RAG context, reducing OQ guidance quality and risking compliance findings.

## Observed Behavior
1. **Langfuse telemetry** showed `documents_retrieved: 0`, `context_quality: "poor"`, `confidence_score: 0`, and each `chromadb.search_collection.<collection>` span reported `collection.document_count: 0`.
2. `ContextProviderAgent._initialize_chromadb` creates collections automatically but does not ingest any documents; empty collections are therefore expected unless ingestion scripts run beforehand.
3. `_apply_metadata_filters` requires every filter key to exist in node metadata. When ingestion omits a key (e.g., `sections`) the filter removes all results even though raw nodes were retrieved.
4. Environment variables (`OPENAI_API_KEY`, `RAG_VECTOR_STORE_PATH`, `RAG_CACHE_DIR`) are mandatory; missing values surface as runtime `RuntimeError` during embedding or storage initialization.
5. No fallback content or readiness check exists, so the workflow proceeds despite missing context and only logs "poor" quality.

## Root Causes
| # | Cause | Evidence | Effect |
|---|-------|----------|--------|
| 1 | **Collections never seeded** | `collection.document_count: 0` across `gamp5`, `regulatory`, `best_practices` spans | Retrieval loop returns empty list despite successful execution |
| 2 | **Strict metadata filters** | `_apply_metadata_filters` drops docs if a metadata key is absent | Potential zero results even with actual matches |
| 3 | **Missing configuration** | `_initialize_chromadb` and `_search_documents` raise on missing API key or invalid vector-store path | Retrieval halts before producing context |
| 4 | **No fallback / readiness guard** | `_execute_context_retrieval` only logs "poor" quality | Downstream agents have no contextual grounding |

## Recommended Fixes
1. **Seed Chroma collections before running the workflow**
   ```python
   # scripts/seed_chroma.py
   import asyncio
   from src.agents.parallel.context_provider import create_context_provider_agent

   async def main():
       agent = create_context_provider_agent(verbose=True)
       await agent.ingest_documents("datasets/corpus_3/gamp5", "gamp5")
       await agent.ingest_documents("datasets/corpus_3/regulatory", "regulatory")
       await agent.ingest_documents("datasets/corpus_3/best_practices", "best_practices")

   if __name__ == "__main__":
       asyncio.run(main())
   ```
   ```powershell
   # Run once to populate ./lib/chroma_db
   & .venv/Scripts/python.exe scripts/seed_chroma.py
   ```

2. **Add readiness guard inside `_search_documents`**
   ```python
   empty = [name for name in collection_names if self.collections[name].count() == 0]
   if empty:
       raise RuntimeError(
           "Context provider cannot run: empty collections "
           f"{empty}. Ingest documents before executing the workflow."
       )
   ```
   This fails fast and surfaces the operational issue to the orchestrator.

3. **Harden metadata filtering**
   ```python
   value = metadata.get(key)
   if isinstance(value, str) and isinstance(filter_value, list):
       include = any(v.lower() in value.lower().split(",") for v in filter_value)
   elif isinstance(filter_value, list):
       include = value in filter_value
   ```
   Also ensure ingestion writes consistent `sections`, `test_types`, and `gamp_categories` values.

4. **Validate configuration at startup**
   - Ensure `OPENAI_API_KEY`, `RAG_VECTOR_STORE_PATH`, and `RAG_CACHE_DIR` are present in `.env.local` or container envs.
   - Mount `./lib/chroma_db` as a writable volume in Docker so ingested data persists across restarts.

5. **Provide fallback context when retrieval fails**
   - If `_search_documents` returns zero results after the guard, load baseline markdown (e.g., `datasets/baselines/category3_context.md`) to keep SME/research agents informed.
   - Flag the workflow output with `context_provider_fallback: true` so operators know RAG context was degraded.

## Validation Checklist
- [ ] Run `scripts/seed_chroma.py`; verify `lib/chroma_db/chroma.sqlite3` grows and Langfuse shows `document_count > 0` on the next run.
- [ ] Trigger a Category 3 URS flow; confirm Langfuse spans show non-zero `documents_retrieved` and `context_quality` ≥ `medium`.
- [ ] Exercise metadata filters by requesting specific sections and ensure results still include relevant nodes.
- [ ] Simulate missing env vars to confirm startup validation blocks execution with actionable errors.
- [ ] Confirm fallback context path by temporarily renaming `lib/chroma_db` and ensuring the workflow emits the degraded-context warning instead of silent failure.

# ChromaDB Empty Collections Debug Plan

## Objectives
- Confirm and document the precise failure path causing ChromaDB collections to appear empty on AWS ECS worker tasks.
- Correlate data flow from seeding → tarball upload → ECS extraction → runtime access.
- Implement a targeted fix (likely within `context_provider.py`) that eliminates silent fallbacks and enforces strict collection loading.
- Provide reproducible validation evidence and deployment guidance.

## Investigation & Fix Strategy

### Phase 0 – Prep
1. Verify current branch (`AWS_deployment`) status and note any uncommitted changes touching relevant files.
2. Capture current environment assumptions (Python 3.12, ChromaDB 1.0.20, ECS paths) for reference in diagnostics.

### Phase 1 – Context Gathering
1. Read `main/docs/issues/2025-12-03-chromadb-empty-collections.md` to understand prior attempts, log snippets, and hypotheses.
2. Review `main/src/agents/parallel/context_provider.py` with emphasis on collection initialization (lines ~476-492) and any logging/error-handling.
3. Inspect `main/scripts/init_chromadb.py` to confirm extraction target path, logging, and closure semantics.
4. Review seeding scripts (`main/scripts/seed_chroma.py`, `main/scripts/reseed_chroma.py` if present) to document exact collection names and metadata usage.
5. Review `aws/scripts/1_upload_chroma_to_s3.py` to ensure tarball creation path matches seeded data.
6. If necessary, skim Dockerfiles (API/worker) to confirm build context includes latest code.

### Phase 2 – Trace Data Flow
1. Map the full path chain (local seeding dir → tarball path → S3 key → ECS extraction dest → runtime client path).
2. Note any discrepancies between environment variables (`RAG_VECTOR_STORE_PATH`, etc.) and actual code usage.
3. Identify where collection keys (`gamp5`, `regulatory`) map to ChromaDB collection names (`gamp5_documents`, `regulatory_documents`).

### Phase 3 – Root Cause Isolation
1. Instrument or reason through `context_provider.py` to determine why `get_collection` fails (e.g., wrong path, metadata mismatch, silent exception handling).
2. Confirm whether exception handling currently masks errors by creating new collections. Capture exact code paths.
3. Evaluate whether metadata provided to `get_or_create_collection` differs between seeding and runtime, preventing matches.

### Phase 4 – Implement Fix
1. Modify `context_provider.py` (and any other necessary script) to:
   - Use `PersistentClient` against the verified path.
   - Attempt `get_collection` with strict error handling and verbose logging.
   - Remove fallback creation of empty collections.
   - (If needed) normalize metadata or collection naming to match seeded data.
2. Ensure logging clearly states path, collection names, and document counts.
3. Avoid touching unrelated modules or introducing fallback logic.

### Phase 5 – Validation
1. Run targeted tests:
   - `pytest main/tests -v -k chromadb`
   - `mypy main/src/agents/parallel/context_provider.py`
   - `ruff check main/src/agents/parallel/`
2. Manually instantiate a `PersistentClient` locally to list collection counts and confirm they match expectations.

### Phase 6 – Reporting & Deployment Guidance
1. Compile findings and fix details into `.claude/state/results/debugger-chromadb-<timestamp>.md` using required template.
2. Document Docker build command for worker image and ECS deployment command (per instructions).
3. Outline CloudWatch log entries to verify on AWS after redeploy.

## Risks & Mitigations
- **Risk:** Existing containers use outdated code → ensure instructions emphasize rebuilding worker image post-fix.
- **Risk:** Metadata mismatch persists → consider stripping dynamic metadata entirely.
- **Risk:** Path differences between local/dev/prod → log absolute paths during initialization to aid future debugging.

## Dependencies / Approvals Needed
- Await user approval of this plan before making code changes or running tests.

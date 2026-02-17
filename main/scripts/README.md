# Scripts Directory

Utility scripts for thesis project development, testing, and data management.

## Active Scripts

### Authentication & Testing
- `generate_test_token.py` — Generate Clerk JWT tokens for integration tests
- `create_clerk_session.py` — Manage Clerk session tokens
- `test_clerk_auth.py` — Test Clerk authentication workflows

### ChromaDB Management
- `init_chromadb.py` — Initialize ChromaDB collections
- `seed_chroma.py` — Seed ChromaDB with initial embeddings
- `embed_gamp5_docs.py` — Embed GAMP-5 regulatory documents into ChromaDB
- `db_utilities/ingest_chromadb.py` — Ingest documents into ChromaDB
- `db_utilities/populate_chromadb.py` — Populate ChromaDB with vectors
- `db_utilities/manual_db_clear.py` — Clear ChromaDB collections

### Monitoring & Validation
- `monitoring/monitor_workflow.py` — Monitor multi-agent workflow execution
- `validation/run_cross_validation.py` — Run cross-validation tests
- `analyze_test_suites.py` — Analyze test suite coverage and metrics

### Utilities
- `ingest-documents.py` — Document ingestion pipeline
- `consolidate_traces.py` — Consolidate execution traces
- `trace_analyzer.py` — Analyze LangFuse traces
- `generate_real_visualizations.py` — Generate data visualizations

## Historical/Outdated Scripts

> These scripts are kept for reference only. The system has migrated to LangFuse for observability.

### Phoenix Exports (Deprecated)
- `export_all_phoenix_traces.py` — ~~Export all Phoenix traces~~ (LangFuse now used)
- `export_phoenix_all_spans.py` — ~~Export Phoenix spans~~ (LangFuse now used)
- `export_phoenix_from_db.py` — ~~Export Phoenix from database~~ (LangFuse now used)
- `test_phoenix_*` — ~~Phoenix testing scripts~~ (LangFuse now used)

### Tracing & Migration (Completed)
- `check_chromadb_traces.py` — ~~Check ChromaDB tracing~~ (superseded by LangFuse)
- `test_chromadb_tracing.py` — ~~Test ChromaDB tracing~~ (superseded by LangFuse)
- `test_custom_span_export.py` — ~~Custom span export testing~~ (LangFuse now used)
- `migrate_chromadb_to_pgvector.py` — ~~Migration to PGVector~~ (not used in current architecture)
- `validate_oss_migration.py` — ~~Validate OSS migration~~ (completed)

## Usage

Most scripts can be run directly via `uv run`:

```bash
uv run main/scripts/generate_test_token.py
uv run main/scripts/init_chromadb.py
```

For database utilities, refer to `db_utilities/` subdirectory documentation.

## Last Updated
2026-02-17

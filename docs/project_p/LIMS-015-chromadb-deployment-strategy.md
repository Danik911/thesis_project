# LIMS-015: ChromaDB Deployment Strategy

**Date**: 2026-02-20
**Status**: Implemented (local + Docker); Planned (AWS Fargate)
**Related**: ISSUE-034 (seeding latency), LIMS-002 (RAG XLSX)

---

## Summary

ChromaDB for AI4LIMS uses bundled JSONL seed files instead of tracking binary HNSW index files in git. Collections auto-seed at startup when empty.

## Architecture

```
Source PDFs (demo_data/SOP/)
    |
    v
Data Prep Pipeline (data-prep-chunk-builder subagent)
    |
    v
JSONL Artifacts (output/prepared_l10l15/L13_rag/)
    |
    v  [copied to git-tracked location]
Bundled Seeds (main/src/lims/data/seeds/)
    |
    v  [upserted at startup if collection empty]
ChromaDB (chroma_db_lims/)
```

## Bundled Seed Files

| File | Collection | Chunks | Size |
|------|-----------|--------|------|
| `lims_standards_chunks.jsonl` | `lims_standards` | 154 | ~197 KB |
| `calculation_patterns_chunks.jsonl` | `calculation_patterns` | 401 | ~565 KB |
| **Total** | | **555** | **~762 KB** |

Location: `main/src/lims/data/seeds/`

## How Seeding Works

1. **App startup** (`main/api/app.py` lifespan):
   - Opens ChromaDB at `LIMS_CHROMADB_PATH` (default: `./chroma_db_lims`)
   - Checks `lims_standards.count()`
   - If 0: calls `seed_all_from_bundled()` which upserts both JSONL files
   - If non-zero: logs count, skips seeding

2. **Idempotent**: All seeding uses `collection.upsert()` -- safe to re-run at any time.

3. **Seed time**: ~30-60s for 555 chunks (embedding generation dominates).

## Environment Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LIMS_CHROMADB_PATH` | `./chroma_db_lims` | Path to ChromaDB persistent storage |

## Local Development

ChromaDB persists to `./chroma_db_lims/` (gitignored). First run auto-seeds from bundled JSONL. Subsequent runs skip seeding.

```bash
# Manual re-seed (e.g., after updating JSONL files)
python -c "
from main.src.lims.standards_loader import seed_all_from_bundled
print(seed_all_from_bundled())
"
```

## Docker (docker-compose.lims.yml)

- Volume mount: `./chroma_db_lims:/app/chroma_db_lims:rw`
- Env var: `LIMS_CHROMADB_PATH=/app/chroma_db_lims`
- JSONL files are in the image via `COPY main/ /app/main/` (Dockerfile.api)
- First container start auto-seeds; data persists across restarts via volume

## AWS Fargate (Planned)

### Current Strategy: Ephemeral Storage + Startup Seed

Fargate tasks have ephemeral storage (20 GB default). ChromaDB data is lost on task restart, but auto-seeds from bundled JSONL at startup.

**Trade-offs**:
- Cold start adds ~30-60s for 555 chunks (embedding generation)
- Acceptable for PoC; healthcheck `start_period` should be >= 90s
- No infrastructure cost (no EFS or EBS volumes needed)

### Task Definition Adjustments

```json
{
  "healthCheck": {
    "command": ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"],
    "interval": 30,
    "timeout": 5,
    "startPeriod": 90,
    "retries": 3
  }
}
```

### Future Option: EFS for Persistent ChromaDB

If cold start latency becomes unacceptable (e.g., more SOPs, larger corpus):

1. Create EFS filesystem in the same VPC
2. Mount as Fargate volume at `/app/chroma_db_lims`
3. ChromaDB persists across task restarts
4. First-ever deployment still auto-seeds; subsequent deployments are instant

**Cost**: ~$0.30/GB/month for EFS Standard. Current ChromaDB size is ~68 MB.

## Adding New SOP Documents

When new PDFs are added to the corpus:

1. Run data prep pipeline (or `data-prep-chunk-builder` subagent) to generate new JSONL
2. Copy updated JSONL to `main/src/lims/data/seeds/`
3. Commit the updated JSONL files (human-readable diffs show exactly what changed)
4. On next deployment/restart, `upsert()` adds new chunks without affecting existing ones

## Files Modified

| File | Change |
|------|--------|
| `.gitignore` | Added `chroma_db_lims/` |
| `main/src/lims/data/seeds/*.jsonl` | New bundled seed files (762 KB total) |
| `main/src/lims/standards_loader.py` | `add()` -> `upsert()`, added `seed_from_jsonl()` + `seed_all_from_bundled()` |
| `main/src/lims/rag_loader.py` | Removed `delete_collection()`, `add()` -> `upsert()` |
| `main/api/app.py` | Added auto-seed check in lifespan startup |
| `docker-compose.lims.yml` | Added ChromaDB volume mount + `LIMS_CHROMADB_PATH` env var |

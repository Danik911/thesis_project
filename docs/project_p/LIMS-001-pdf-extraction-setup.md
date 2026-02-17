# LIMS-001: PDF Upload + LlamaExtract Parsing

**Date:** 2026-02-17
**Status:** Complete (feasibility validated)
**Branch:** `prjoject_p_protatype`

---

## Summary

Implemented the first AI4LIMS building block: a `/lims` page where users upload pharmaceutical test method PDFs, which are extracted via LlamaExtract Cloud API into structured JSON matching the MDA (Method Definition and Analysis) schema.

## Files Created

| File | Purpose |
|------|---------|
| `main/src/lims/config.py` | LIMS configuration from env vars (`LIMS_LLAMAEXTRACT_API_KEY`, `LIMS_EXTRACTION_MODE`) |
| `main/src/lims/pdf_extractor.py` | LlamaExtract wrapper — SDK v0.6+ 2-step API: `create_agent` + `agent.extract` |
| `main/src/lims/extraction_schema.py` | Simplified Pydantic schema for LlamaExtract (no enums/validators) |
| `main/api/lims_router.py` | FastAPI `POST /lims/extract` — public, no auth, validates PDF |
| `main/frontend/pages/lims.tsx` | LIMS page with drag-and-drop PDF upload, emerald color scheme |

## Files Modified

| File | Change |
|------|--------|
| `main/api/app.py` | Mounted `lims_router` at `/lims` prefix (2 lines) |
| `main/frontend/components/Layout.tsx` | Added LIMS nav link + public page bypass (`isPublicPage`) |
| `pyproject.toml` | Added `llama-cloud-services>=0.1.0`, `llama-cloud>=0.1.0` |

## Test Result

```bash
curl -X POST http://localhost:8080/lims/extract \
  -F "file=@demo_data/AND_ACS_AQ126-LAB-2349.pdf"
```

Extraction returned structured data:
- **1 analysis**: AQ126 N — Suitability for Use Test for rhBMP-2/ACS Kit
- **3 components**: Wetted Appearance, Physical Integrity, Loading Capacity (%)
- **2 calc variables**: Volume Retained by ACS, Percent Volume Retained
- **1 calculation**: Loading Capacity formula

Pydantic validation against the full `MDATemplate` fails (expected) — LLM returns natural language values (`"yes/no"`) instead of LabWare codes (`"L"`). Raw extraction data is still valuable. Schema mapping will be a later refinement step.

---

## Issues Encountered

### 1. LlamaExtract SDK v0.6+ API Breaking Change

**Symptom:** `AttributeError: 'LlamaExtract' object has no attribute 'extract'`

**Root Cause:** SDK v0.6.54 uses a 2-step API pattern, not the single-call `extractor.extract()` from older docs.

**Fix:** Changed from:
```python
result = extractor.extract(MDATemplate, extract_config, tmp_path)
```
To:
```python
agent = extractor.create_agent(name=agent_name, data_schema=MDAExtractionSchema, config=extract_config)
run = agent.extract(tmp_path)
raw_data = run.data
```

### 2. LlamaExtract Schema Validation Error

**Symptom:** `ApiError: status_code: 400, schema_validation: incorrect type or null value provided at path (root)`

**Root Cause:** `MDATemplate` uses complex Pydantic features (enums like `AnalysisType`, `ResultType`, custom validators, model validators) that LlamaExtract cannot convert to its internal JSON schema format.

**Fix:** Created `extraction_schema.py` with a simplified `MDAExtractionSchema` — same fields but using plain `str/int/float/bool` types only. After extraction, the raw dict is validated against the full `MDATemplate` separately.

### 3. Docker Container Stale Environment Variables

**Symptom:** `LIMS_LLAMAEXTRACT_API_KEY not set` even though the key was in `.env.local`.

**Root Cause:** The running Docker container (`pharma-api-dev`) was created 2 months before the LIMS env vars were added to `.env.local`. `docker restart` does NOT reload `env_file` — it only restarts the process with the original environment.

**Fix:** Recreated the container:
```bash
docker compose -f docker-compose.dev.yml up -d api
```

**Lesson:** Always use `docker compose up -d` (recreate) instead of `docker restart` when env vars change.

### 4. Docker Compose v1 vs v2

**Symptom:** `KeyError: 'ContainerConfig'` when using `docker-compose` (v1).

**Fix:** Use `docker compose` (v2 plugin, no hyphen) instead of `docker-compose` (v1 standalone).

### 5. WSL Native Server Numpy ImportError

**Symptom:** `ImportError: Error importing numpy: you should not try to import numpy from its source directory` when running `uv run uvicorn` natively in WSL.

**Root Cause:** The `.venv` is on `/mnt/c/` (Windows filesystem via NTFS mount). Numpy doesn't work well from its source directory on mounted filesystems.

**Recommendation:** Use local server first for faster iteration (avoids Docker rebuild wait). If numpy import fails on `/mnt/c/`, consider creating a WSL-native venv or use Docker as fallback.

---

## Useful Commands

```bash
# Start API container (recreates if env vars changed)
docker compose -f docker-compose.dev.yml up -d api

# Stop all containers
docker compose -f docker-compose.dev.yml down

# Nuclear rebuild
docker compose -f docker-compose.dev.yml down -v --remove-orphans
docker compose -f docker-compose.dev.yml build --no-cache
docker compose -f docker-compose.dev.yml up -d

# Test LIMS extraction
curl -X POST http://localhost:8080/lims/extract \
  -F "file=@demo_data/AND_ACS_AQ126-LAB-2349.pdf"

# Check container logs
docker compose -f docker-compose.dev.yml logs -f api

# Check running containers
docker ps
```

---

## Next Steps

- Chat-based MDA refinement (map natural language values to LabWare codes)
- ChromaDB RAG for MDA templates
- XLSX export (4-sheet format)
- Frontend result viewer improvements

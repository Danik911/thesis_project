# LIMS-002: MDA Generation Pipeline (RAG + LLM + XLSX Export)

**Date:** 2026-02-17
**Status:** Complete
**Branch:** `prjoject_p_protatype`
**Task:** L4a (PRP Tasks Merged: L4.1, L4.2, L4.5)

---

## Summary

Implemented the MDA generation pipeline: raw PDF extraction results are enriched with RAG context from 25 demo LabWare XLSX templates stored in ChromaDB, then an LLM generates a complete preliminary MDA (Method Definition and Analysis) template, which can be exported to a 4-sheet XLSX matching LabWare import format.

## Files Created

| File | Purpose |
|------|---------|
| `main/src/lims/rag_loader.py` | Parse demo XLSX -> text, seed ChromaDB `mda_templates`, query interface (242 lines) |
| `main/src/lims/mda_generator.py` | LlamaIndex Workflow: raw extraction + RAG context -> LLM -> MDATemplate (154 lines) |
| `main/src/lims/xlsx_exporter.py` | openpyxl: MDATemplate -> 4-sheet XLSX (Analysis, Component, Calc Variable, Calculation) (298 lines) |
| `main/src/lims/prompts/__init__.py` | Package init |
| `main/src/lims/prompts/mda_generation_prompt.py` | System prompt with 12 sections of MDA domain knowledge |
| `scripts/populate_lims_chroma.py` | CLI script to seed ChromaDB from `demo_data/*.xlsx` |

## Files Modified

| File | Change |
|------|--------|
| `main/src/lims/config.py` | Added 5 fields: `openrouter_api_key`, `openrouter_model`, `chromadb_path`, `upload_dir`, `output_dir` with LIMS_* env var loading |

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| RAG Store | ChromaDB PersistentClient | 1.0.20 |
| Workflow | LlamaIndex Workflow (@step) | llama-index-core 0.13.3 |
| LLM | OpenRouter (OpenAI-compatible SDK) | openai 1.102.0 |
| XLSX | openpyxl | 3.1.0+ |
| Validation | Pydantic v2 (MDATemplate) | 2.x |

## Test Results

- ChromaDB seeding: **25 documents** from `demo_data/` (AND=8, FRE=9, TUA=8)
- XLSX roundtrip: 4 sheets with correct headers verified
- All module imports successful
- pytest: 84 passed, 2 skipped

## Manual E2E Result

```bash
curl -X POST http://localhost:8080/lims/extract -F "file=@demo_data/AND_ACS_DYE-LAB-2499.pdf"
```

LLM (`google/gemini-3-flash-preview`) generated:
- 3 analyses (AND_ACS_DYE, AND_ACS_DYE_CTL, AND_ACS_DYE_META)
- 10 components with result types (N, K, L, T)
- Populated calc_variables and calculations
- Pydantic validation passed (MDATemplate.model_validate)

---

## Issues Encountered

### 1. No-Fallback Violation in RAG Query (FIXED)

**Symptom:** Broad `except Exception` around ChromaDB RAG query silently caught all failures.
**Fix:** Changed to `except RuntimeError` (specific to empty collection). Added `rag_failure` field to StopEvent for transparency. Other exceptions propagate as unhandled.

### 2. typing.Sequence Deprecation (FIXED)

**Symptom:** Linter flagged `from typing import Sequence` as deprecated.
**Fix:** Changed to `from collections.abc import Sequence` in xlsx_exporter.py.

---

## Useful Commands

```bash
# Seed ChromaDB with demo templates
uv run python scripts/populate_lims_chroma.py ./demo_data

# Test MDA generation (requires LIMS_OPENROUTER_API_KEY)
uv run uvicorn main.api.app:app --port 8080
curl -X POST http://localhost:8080/lims/extract -F "file=@demo_data/AND_ACS_DYE-LAB-2499.pdf"

# Run LIMS tests
uv run pytest main/tests/lims/ -v
```

---

## Next Steps

- L4b: Chat agent + HITL state machine + router endpoints (DONE)
- L5: Backend E2E testing
- L6: Full HITL UI (ChatInterface, LIMSStepIndicator, lims.tsx rewrite)

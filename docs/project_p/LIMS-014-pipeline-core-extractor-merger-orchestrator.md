# LIMS-014 — L14 Pipeline Core: Focused Extractor, Merger & Orchestrator

**Date:** 2026-02-19
**Task:** L14 — Pipeline Core (Extractor + Merger + Orchestrator)
**Phase:** 8d (Two-Layer Pipeline — Full Orchestration)
**Branch:** `prjoject_p_protatype`

## Summary

Implemented the core of the two-layer pipeline: a focused extractor (PDF text via PyMuPDF + LlamaExtract wrapper), a merger with provenance tracking, and the `TwoLayerPipeline` orchestrator that sequences all 6 stages end-to-end. Also extended the API with `/classify` and `/template/{test_type}` endpoints and rewrote `/extract` to use the pipeline. Achieved **287 passed, 4 skipped, 0 failures** across the full LIMS test suite with 46 new tests added.

## Pipeline Architecture

The `TwoLayerPipeline` runs 6 sequential stages:

| Stage | Name | Description |
|-------|------|-------------|
| 1 | Classify | Calls `TestTypeClassifier` to identify test type from PDF |
| 2 | Template | Loads skeleton MDA from `TemplateLibrary` for the detected type |
| 3 | Extract | Runs full LlamaExtract extraction via `FocusedExtractor` |
| 4 | Augment | Enriches with standards data from ChromaDB RAG (skipped if no OpenRouter key) |
| 5 | Merge | Applies `MDAMerger` — template + extracted + augmented → final MDA with provenance |
| 6 | Review | Cross-sheet integrity validation; records `MergeConflict` list for SME review |

## Files Created

| File | Purpose |
|------|---------|
| `main/src/lims/focused_extractor.py` | PDF text extraction (PyMuPDF) + focused extraction wrapper around LlamaExtract |
| `main/src/lims/merger.py` | `MDAMerger` — merges template, extracted, and augmented data; tracks field provenance; records conflicts |
| `main/src/lims/pipeline.py` | `TwoLayerPipeline` orchestrator — sequences all 6 stages, returns `PipelineResult` with MDA + provenance + conflicts |
| `main/tests/lims/test_merger.py` | 21 tests for merge algorithm, provenance tracking, and conflict detection |
| `main/tests/lims/test_pipeline.py` | 10 tests for pipeline orchestration, stage sequencing, and OTHER fallback |

## Files Modified

| File | Change |
|------|--------|
| `main/src/lims/job_store.py` | Added `AUGMENTING` to valid transitions from `EXTRACTING` state |
| `main/api/lims_router.py` | Rewrote `POST /extract` to use `TwoLayerPipeline.run()`; added `POST /classify` and `GET /template/{test_type}` endpoints |
| `main/tests/lims/test_lims_router.py` | Updated extract test to mock `TwoLayerPipeline.run()`; added 9 new tests for classify and template endpoints |

## Key Design Decisions

1. **Full extraction, merger filters** — LlamaExtract runs against the full PDF; the merger then filters to variable fields only. No per-test-type schema narrowing is applied at extraction time.
2. **Augmentation is optional** — The augment stage is skipped silently when no OpenRouter key is configured. The pipeline does not fail if the key is absent.
3. **TestType.OTHER uses single-layer fallback** — When the classifier returns `OTHER`, the pipeline delegates to the original single-layer extraction path for backward compatibility.
4. **Merge priority order** — `Extracted > Template > Augmented > SME_REQUIRED`. Higher-priority sources win when multiple sources provide a value for the same field.
5. **Conflicts recorded, not auto-resolved** — When template and extraction disagree on a field value, a `MergeConflict` is recorded in the `PipelineResult` for SME review. No automatic resolution is attempted.
6. **Every non-null field has a provenance entry** — The provenance map is complete: every field in the final MDA that carries a value has a corresponding source annotation.

## Test Results

```
287 passed, 4 skipped, 0 failures (full LIMS test suite)
46 new tests added:
  - 21 tests: test_merger.py (merge algorithm + provenance + conflict detection)
  - 10 tests: test_pipeline.py (orchestration + stage sequencing + OTHER fallback)
  - 15 tests: test_lims_router.py (classify endpoint + template endpoint + updated extract)
```

## Gate Criteria Met

- `TwoLayerPipeline` produces an MDA with provenance for all known test types
- `TestType.OTHER` falls back to single-layer path (AND_ACS_DYE backward compat verified)
- `MergeConflict` objects are generated when template and extraction values disagree
- Cross-sheet integrity validation runs after merge (Stage 6)
- Every non-null field in the output MDA has a corresponding provenance entry
- `/classify` endpoint callable and returns test type + confidence
- `/template/{test_type}` endpoint callable and returns skeleton MDA
- `/extract` uses `TwoLayerPipeline` end-to-end
- All pre-existing LIMS tests still pass (no regressions)

## Issues Encountered

None. Implementation completed without errors or regressions.

## Useful Commands

```bash
# Run merger tests
wsl -e bash -lc "cd /mnt/c/Users/anteb/Desktop/Courses/Projects/thesis_project && uv run pytest main/tests/lims/test_merger.py -v"

# Run pipeline tests
wsl -e bash -lc "cd /mnt/c/Users/anteb/Desktop/Courses/Projects/thesis_project && uv run pytest main/tests/lims/test_pipeline.py -v"

# Run all LIMS tests
wsl -e bash -lc "cd /mnt/c/Users/anteb/Desktop/Courses/Projects/thesis_project && uv run pytest main/tests/lims/ -v"

# Test classify endpoint
curl -X POST http://localhost:8080/lims/classify \
  -F "file=@demo_data/AND_ACS_AQ126-LAB-2349.pdf"

# Test template endpoint
curl http://localhost:8080/lims/template/IDENTITY

# Test full pipeline via extract
curl -X POST http://localhost:8080/lims/extract \
  -F "file=@demo_data/AND_ACS_AQ126-LAB-2349.pdf"
```

## Next Steps

- **L15:** Frontend workflow UI (step indicator: Classify → Template → Extract → Augment → Merge → Review; conflict viewer; approve/export buttons)
- **L16:** End-to-end integration test with real PDFs through the full pipeline
- **Future:** Integrate LLM classification in `_classify_by_llm()` for low-confidence cases
- **Future:** SME conflict resolution UI (allow human to choose between conflicting field values)

# LIMS-005 — Task L7: Extraction Normalization & SDK Migration Decision Record

**Date:** 2026-02-18  
**Task:** `PRPs/tasks/L7-extraction-normalization-sdk-migration.md`  
**Branch:** `prjoject_p_protatype`

---

## Summary

Task L7 is implemented with additive, backward-compatible changes:

1. Added post-extraction normalization layer before strict Pydantic validation.
2. Added extraction API switch (`LIMS_EXTRACTION_API`) for controlled migration.
3. Pinned current extraction SDK stack for deterministic runtime compatibility.
4. Added normalization unit tests and extraction integration assertions.
5. Completed SDK/API research and captured empirical comparison data.

No thesis-system code paths were modified.

---

## Files Created

- `main/src/lims/data_normalizer.py`
- `main/tests/lims/test_data_normalizer.py`

---

## Files Modified

- `main/src/lims/pdf_extractor.py`
- `main/src/lims/config.py`
- `main/src/lims/extraction_schema.py`
- `main/tests/lims/test_extraction.py`
- `pyproject.toml`

---

## What Changed

### 1) Post-processing normalization layer

`normalize_extraction(raw_dict)` now runs after extraction and before `MDATemplate.model_validate(...)`.

Normalization operations include:

- Unicode symbol normalization (`µ/μ/°/≥/≤/±` etc. -> LIMS-safe forms)
- Component and analysis naming normalization
- Numeric string coercion for known numeric fields
- Boolean string coercion for known boolean fields
- LIMS defaults (`K` components get `auto_calc=True` if missing, `units=None` -> `""`)

`pdf_extractor` now returns both:

- `raw_extraction` (original API output)
- `normalized_extraction` (post-processed payload)

Validation is applied to `normalized_extraction`.

### 2) Extraction API switch

`LIMSConfig` now includes:

- `extraction_api: "llamaextract" | "llamaparse_v2"` (default: `llamaextract`)

Current runtime intentionally supports only `llamaextract`; selecting `llamaparse_v2` raises explicit `NotImplementedError` (fail-loud behavior, no fallback logic).

### 3) SDK version strategy (current stability)

Pinned runtime-compatible versions in `pyproject.toml`:

- `llama-cloud-services==0.6.93`
- `llama-cloud==0.1.46`

This preserves current functionality while documenting migration path.

---

## Research Findings

### LlamaParse v2 (from official docs/blog)

- Tier model: `fast`, `cost_effective`, `agentic`, `agentic_plus`
- Structured v2 API endpoints: `/api/v2/parse` and `/api/v2/parse/upload`
- Version pinning supported (e.g., date versions)
- Structured options include grouped `input_options`, `output_options`, `processing_options`
- New SDK direction is `llama-cloud` (`LlamaCloud` client)

### LlamaExtract status

- LlamaExtract remains beta-oriented in product messaging and roadmaps.
- Roadmap highlights include multimodal and HITL schema improvements.

---

## Empirical Comparison (Target file)

### Dataset

- `demo_data/AND_ACS_DYE-LAB-2499.pdf`
- Supporting converted markdown in `demo_data/parced/`

### Approach A — Current LlamaExtract path (`llama-cloud-services`)

Command executed via `uv run python` against current `extract_mda_from_pdf`.

Observed:

- Runtime: ~125.95s
- Output counts: analyses=1, components=3, calc_variables=3, calculations=3
- Validation: **failed** with 19 schema errors (enum semantic mismatch + missing structured fields)

Example failure classes:

- `analysis_type='Identity Test'` (expected enum IDs)
- `result_type='Qualitative'` (expected `N/K/L/T/D`)
- missing/invalid `calc_variables.reference_type/return_value/scope/function`

### Approach B — LlamaParse v2 (`/api/v2/parse/upload`, `cost_effective`)

Command executed via direct API polling.

Observed:

- Runtime: ~27.82s
- Status: `COMPLETED`
- Parsed pages: 20 markdown pages, 20 items pages
- Detected table items: 38

Interpretation:

- Parse v2 produces richer structural parsing artifacts quickly.
- Parse v2 alone does **not** replace schema-constrained extraction; it should feed a deterministic structuring step.

### Local parsed markdown normalization signal

Scanning provided artifacts:

- `demo_data/parced/AND_ACS_DYE-LAB-2499_pdf.md`: 37 symbol-normalization hits
- `demo_data/parced/AND_ACS_DYE-LAB-2499_xlsx.md`: 0 hits

This confirms practical value of normalization on your provided non-normalized data.

---

## Decision & Recommendation

### Immediate (implemented now)

- Keep `llamaextract` as default runtime path.
- Use normalization layer before validation to improve output consistency.
- Keep fail-loud behavior for unsupported API switch values.

### Near-term migration path

1. Add fully implemented `llamaparse_v2` pipeline:
   - Parse v2 -> deterministic structuring prompt/tool -> `MDATemplate` validation.
2. Keep `LIMS_EXTRACTION_API` switch for A/B execution.
3. Evaluate on 3+ PDFs with metrics:
   - validation pass rate
   - enum-field correctness
   - extraction latency
   - cost per document

---

## Validation Performed

### Targeted tests

`uv run pytest main/tests/lims/test_data_normalizer.py main/tests/lims/test_extraction.py -v`

- Result: **10 passed, 1 skipped**

### Full LIMS test suite

`uv run pytest main/tests/lims/ -v`

- Result: **95 passed, 4 skipped**

---

## Notes for Next Task (L8/L9 readiness)

- The remaining extraction-quality gap is primarily semantic mapping, not only symbol cleanup.
- Highest-impact next step is enum/value mapping and structured field completion for calc variables/calculations.
- Parse v2 results indicate a viable migration candidate once structuring logic is added.

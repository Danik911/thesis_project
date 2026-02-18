# ISSUE-031: LIMS LlamaExtract Semantic Enum Mismatch on Demo PDF

**Date:** 2026-02-18  
**Status:** Resolved  
**Consolidated Into:** `ISSUE-032`  
**Category:** API/Data Quality  
**Priority:** High

---

## Symptom

Baseline extraction on `demo_data/AND_ACS_DYE-LAB-2499.pdf` returns payload that fails strict `MDATemplate` validation even after normalization.

Observed result:

- Runtime: ~125.95s
- Output counts: analyses=1, components=3, calc_variables=3, calculations=3
- Validation: failed with 19 errors

---

## Error Pattern

Representative failures:

- `analysis_type='Identity Test'` (expected enum: `ID|ASY|IMP|PHYS|QC_SAMPLES`)
- `result_type='Qualitative'` (expected enum: `N|K|L|T|D`)
- `calc_variables.*.reference_type` missing
- `calc_variables.*.return_value/scope/function` semantic mismatch
- `calculations.*.calculation_type` invalid semantic values

---

## Root Cause

LlamaExtract returned human-language semantic labels and nullable fields where strict `MDATemplate` expects controlled enums and required typed fields. Existing normalization handled symbols/type coercion but not semantic alias mapping or cross-sheet reference alignment after name normalization.

---

## Files Modified

| File | Change |
|------|--------|
| `main/src/lims/data_normalizer.py` | Added semantic enum mapping for analysis/result/calc types, required-field coercion, and cross-sheet analysis/component reference normalization. |
| `main/tests/lims/test_data_normalizer.py` | Added regression test for semantic alias payload validating against `MDATemplate`. |

---

## Resolution

Implemented deterministic semantic normalization layer to convert extraction aliases into strict LabWare enum values and normalize cross-sheet identifiers before validation.

Fixed classes of failures:

- `analysis_type` aliases (e.g., `identity test` -> `ID`)
- `result_type` aliases (e.g., `visual inspection`, `color comparison` -> `L`)
- `calculation_type` aliases (e.g., `concentration calculation` -> `FORMULA`)
- `calc_variables` enum defaults/mapping (`reference_type`, `return_value`, `scope`, `function`)
- Missing required fields (`active`, `reported_name`, `common_name`, `order_number`) via deterministic normalization rules
- Cross-sheet `analysis` / `component` reference mismatches after name normalization

---

## Verification

- `uv run pytest main/tests/lims/test_data_normalizer.py main/tests/lims/test_extraction.py -v`
- `uv run pytest main/tests/lims/ -v`

---

## Proposed Fix Path

1. Add semantic normalization/mapping layer for enum aliases (e.g., `Identity Test` -> `ID`, `Qualitative` -> `L/T` depending on context).
2. Improve extraction schema instructions for calc variable/calculation semantics.
3. Evaluate Parse v2 + structuring as alternate extraction path via `LIMS_EXTRACTION_API=llamaparse_v2` implementation.

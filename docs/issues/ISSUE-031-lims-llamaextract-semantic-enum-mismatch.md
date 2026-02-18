# ISSUE-031: LIMS LlamaExtract Semantic Enum Mismatch on Demo PDF

**Date:** 2026-02-18  
**Status:** Open  
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

## Affected Files

- `main/src/lims/pdf_extractor.py`
- `main/src/lims/data_normalizer.py`
- `main/src/lims/extraction_schema.py`

---

## Proposed Fix Path

1. Add semantic normalization/mapping layer for enum aliases (e.g., `Identity Test` -> `ID`, `Qualitative` -> `L/T` depending on context).
2. Improve extraction schema instructions for calc variable/calculation semantics.
3. Evaluate Parse v2 + structuring as alternate extraction path via `LIMS_EXTRACTION_API=llamaparse_v2` implementation.

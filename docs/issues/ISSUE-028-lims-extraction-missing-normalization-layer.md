# ISSUE-028: LIMS Extraction Missing Post-Processing Normalization Layer

**Date:** 2026-02-18  
**Status:** Resolved  
**Consolidated Into:** `ISSUE-032`  
**Category:** API/Data Quality  
**Priority:** High

---

## Symptom

LIMS extraction output from pharmaceutical PDFs reaches strict `MDATemplate` validation without a normalization pass. This creates data-quality defects such as:

- Unicode symbol drift (e.g., µ/μ/°/≥/≤ variants)
- Inconsistent naming (`component_name`, analysis name formatting)
- Numeric and boolean values returned as strings
- Null/empty values not aligned with LIMS conventions

These defects reduce validation success and downstream template quality.

---

## Root Cause

`pdf_extractor.py` passed raw extraction payload directly to `MDATemplate.model_validate(...)` without preprocessing. Extraction outputs include Unicode variants, string-typed numeric/boolean values, and naming drift that degrade strict schema compatibility.

---

## Files Modified

| File | Change |
|------|--------|
| `main/src/lims/data_normalizer.py` | Added normalization module (symbols, names, coercion, defaults). |
| `main/src/lims/pdf_extractor.py` | Added normalization step before Pydantic validation; preserved raw output and added `normalized_extraction`. |
| `main/tests/lims/test_data_normalizer.py` | Added unit tests for normalization behavior. |
| `main/tests/lims/test_extraction.py` | Added assertions for normalized output and API switch behavior. |

---

## Resolution

Implemented Task L7 normalization layer and integrated it in extraction flow. Validation now runs against normalized payload while raw extraction remains available for audit/debug.

---

## Verification

- `uv run pytest main/tests/lims/test_data_normalizer.py main/tests/lims/test_extraction.py -v`
- `uv run pytest main/tests/lims/ -v`

# ISSUE-039: LIMS XLSX Export Fails — Null and Truncated Analysis References

**Date Created:** 2026-02-21
**Date Resolved:** 2026-02-21
**Status:** RESOLVED
**Category:** API/Data Quality
**Priority:** High
**Affected Component:** LIMS Pipeline Export

---

## Symptom

XLSX export of approved MDA templates fails with Pydantic validation errors. Two distinct failure modes observed:

### Failure Mode 1: Null `analysis` fields (25 validation errors)

```
XLSX export failed: ValidationError: 25 validation errors for MDATemplate
components.25.analysis
  Input should be a valid string [type=string_type, input_value=None, input_type=NoneType]
...
calculations.13.component
  Input should be a valid string [type=string_type, input_value=None, input_type=NoneType]
```

### Failure Mode 2: Truncated analysis name reference (1 validation error)

```
XLSX export failed: ValidationError: 1 validation error for MDATemplate
  Value error, Component 'Package: Double layered and sealed?' references analysis
  'SITE_IDENTITY' which does not exist. Valid analyses:
  ['DYE_BINDING_IDENTITY_TEST_FOR_ABSORBABLE_COLLAGEN_SPONGE_(ACS)',
   'SITE_IDENTITY_CTL', 'SITE_IDENTITY_META']
```

---

## Root Cause

### Failure Mode 1: Null analysis fields

LlamaExtract does not repeat the `analysis` name for every row in extracted tables. When a PDF has components grouped under an analysis header, only the first rows get the analysis name populated -- continuation rows have `analysis: None`. The `MDATemplate` schema requires `analysis: str` (non-Optional), so `MDATemplate.model_validate()` fails during export.

The `_normalize_analysis_refs()` function in `data_normalizer.py` skipped records with `analysis=None` instead of trying to infer the correct value.

### Failure Mode 2: Truncated analysis name

LlamaExtract sometimes returns abbreviated or truncated analysis names in component references (e.g., `SITE_IDENTITY` instead of `SITE_IDENTITY_CTL`). The normalizer's `_normalize_analysis_refs()` only performed exact-match lookup, so truncated names passed through unchanged. The MDATemplate cross-sheet validator then correctly rejected the reference.

### Contributing factor: Outdated SDK

The `llama-cloud` package (v0.1.18) had an `ExtractConfig` with only 3 fields. Parameters like `cite_sources`, `use_reasoning`, `confidence_scores` were silently dropped during API serialization. Updated to v0.1.46.

---

## Files Modified

| File | Change |
|------|--------|
| `main/src/lims/data_normalizer.py` | Added `_forward_fill_field()` with forward-fill, backward-fill, and single-value inference. Added `_resolve_analysis_name()` with cascading match: exact, prefix (single/multi), substring. Refactored `_normalize_analysis_refs()` to use resolver. |
| `main/api/lims_router.py` | Export endpoint now runs `_normalize_analysis_refs()` + `_forward_fill_field()` on stored data before `MDATemplate.model_validate()`. |
| `main/src/lims/pdf_extractor.py` | Added early validation: `cite_sources` and `confidence_scores` require MULTIMODAL/PREMIUM mode. |
| `main/src/lims/config.py` | No change (defaults were correct: `extraction_mode=multimodal`). |
| `.env.local` | Changed `LIMS_EXTRACTION_MODE=balanced` to `multimodal` (required for `cite_sources=True`). |
| `main/tests/lims/test_data_normalizer.py` | Added 8 new tests covering analysis name resolution and forward-fill scenarios. |

---

## Resolution Details

### 1. Forward-fill with backward-fill and inference (`_forward_fill_field`)

Handles three PDF layout patterns:
- **Forward-fill**: analysis name on first row, blank below (most common)
- **Backward-fill**: analysis name appears mid-table, leading rows blank
- **Single-value inference**: all rows blank but only one analysis exists in the extracted data

When multiple analyses exist and ALL component rows are blank, the function correctly refuses to guess (ambiguous case fails validation with clear error).

### 2. Cascading analysis name resolution (`_resolve_analysis_name`)

When exact match fails, tries in order:
1. **Prefix match (single)**: `SITE_IDENTITY` matches only `SITE_IDENTITY_CTL` -> use it
2. **Prefix match (multiple)**: `SITE_IDENTITY` matches `SITE_IDENTITY_CTL` and `SITE_IDENTITY_META` -> pick shortest (closest to the reference)
3. **Substring match (single)**: handles cases where the reference is embedded in a longer canonical name

No match -> returns None, validator catches it with a clear error.

### 3. SDK update

- `llama-cloud`: 0.1.18 -> 0.1.46 (ExtractConfig now has all 16 fields)
- `llama-cloud-services`: 0.6.12 -> 0.6.94

### 4. Config validation

Added pre-flight checks in `_get_extract_config()`:
- `cite_sources=True` + non-MULTIMODAL/PREMIUM -> clear ValueError with fix instructions
- `confidence_scores=True` + non-MULTIMODAL/PREMIUM -> same

---

## Test Coverage

16 tests in `test_data_normalizer.py`, all passing:

| Test | Scenario |
|------|----------|
| `test_exact_match` | Direct name lookup |
| `test_prefix_single_match` | `SITE_IDENTITY` -> `SITE_IDENTITY_CTL` |
| `test_prefix_multiple_matches_picks_shortest` | Multiple prefix matches, picks closest |
| `test_substring_single_match` | Substring containment |
| `test_no_match_returns_none` | Complete mismatch returns None |
| `test_case_insensitive_prefix_match` | Case insensitive |
| `test_truncated_site_identity_resolves_for_export` | Reproduces exact ISSUE-039 bug |
| `test_full_pipeline_with_truncated_ref_passes_validation` | End-to-end through MDATemplate |

---

## Prevention

- The normalizer now handles the three most common PDF extraction artifacts (null fields, truncated names, abbreviated references) before data reaches Pydantic validation.
- The export endpoint applies the same normalization to stored data, so existing jobs are also fixed.
- The MDATemplate cross-sheet validator is NOT weakened -- it still catches genuinely invalid references.
- SDK packages are updated to versions where ExtractConfig properly serializes all fields.

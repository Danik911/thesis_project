# LIMS-018: MDA Template Approval Validation Errors — Merger Analysis Matching and Ref Rewriting Fixes

**Date:** 2026-02-23
**Type:** Issue / Bug Fix
**Status:** Archived — superseded by [LIMS-020](../LIMS-020-template-locked-merge-quality-fix.md)

> This document is archived for audit traceability. The current reference for merger quality fixes is
> [LIMS-020-template-locked-merge-quality-fix.md](../LIMS-020-template-locked-merge-quality-fix.md).

---

## Summary

When processing `AND_ACS_DYE-LAB-2499.pdf` through the two-layer pipeline, the MDA template failed cross-sheet validation and blocked approval. The merged result contained 4 analyses instead of the expected 3 — the extraction's analysis entry was added alongside the template's instead of being merged into it. Component rows referenced truncated analysis names that matched nothing in the analysis sheet.

---

## Symptom

- Post-merge validation failure: cross-sheet `analysis` references in `components`, `calc_variables`, and `calculations` could not be resolved to any analysis row.
- Analysis sheet contained 4 rows instead of 3 (one duplicate created by failed matching).
- Approval gate blocked; job stuck in `PENDING_REVIEW` with `validated=False`.

---

## Root Cause: 4 Interrelated Problems

### Problem 1 — Analysis matching fails when extraction `analysis_type` is NULL

`data_normalizer.py`'s `_normalize_analysis_type()` returned `None` when the raw extraction value was `None`. The merger's `_match_analysis()` used the normalized type as a match criterion, so `NULL` type could never match the template's `"ID"` type. The extraction analysis was therefore treated as a new (unmatched) analysis and appended rather than merged.

### Problem 2 — Component analysis refs are truncated names

LlamaExtract returns shortened analysis names in component `analysis` fields (e.g., `"Dye-Binding Test"` instead of the full template name `"SITE_IDENTITY"`). The exact-match-only resolution introduced in LIMS-017 Phase 6 could not resolve these truncated refs, leaving components with dangling references.

### Problem 3 — Extraction overlay overwrites template analysis names (LIMS identifier corruption)

The `_overlay_extracted_items()` helper updated all fields from the extraction onto the matched template row, including `name`. This destroyed the LIMS system identifier (e.g., `"SITE_IDENTITY"` → `"DYE_BINDING_IDENTITY_TEST_FOR_..."`), breaking all downstream cross-sheet refs that depended on the canonical template name.

### Problem 4 — None-typed extraction lists crash merger

When Pydantic validation partially fails on raw extraction output, list fields (analyses, components, calc_variables, calculations) can be present in the dict with value `None` rather than absent. The pattern `.get(key, [])` returns `None` when the key exists with value `None`, causing `TypeError: 'NoneType' object is not iterable` in the merger loops.

---

## Fixes Applied

### Fix A — Type inference from analysis name (`data_normalizer.py`)

Added `_infer_analysis_type_from_name(name: str) -> Optional[str]`. When `_normalize_analysis_type()` receives a `None` value, it calls the inference function to derive a type from the analysis name using keyword matching:

| Name keyword | Inferred type |
|---|---|
| `identity`, `id test`, `id_test` | `"ID"` |
| `assay`, `purity`, `content` | `"ASSAY"` |
| `dissolution` | `"DISSOLUTION"` |
| `_ctl`, `control`, `qc` | `"QC_SAMPLES"` |
| `water`, `lod` | `"MOISTURE"` |
| `limit`, `impurity` | `"LIMIT_TEST"` |
| `clarity`, `appearance` | `"APPEARANCE"` |

This allows extraction analyses with `NULL` type to match template analyses of a known type.

### Fix B — Protected analysis names during overlay (`merger.py`)

Added `protected_keys: set[str]` parameter to `_overlay_extracted_items()`. When `"name"` is in `protected_keys`, the template analysis name is never overwritten by the extraction name. Name conflicts are recorded in `match_map_out` for SME review rather than silently applied.

`merge_layers()` now calls `_overlay_extracted_items(..., protected_keys={"name"})` for analysis overlay.

### Fix C — Extraction ref rewriting to template names (`merger.py`)

Added two new functions:

- `_build_extraction_to_template_map(analyses, rename_map) -> dict[str, str]`: Builds a mapping from extraction analysis names (including truncated variants) to canonical template names. Uses exact match first, then word-subset matching (minimum 3 tokens, unambiguous — exactly one template name must match to prevent over-matching).

- `_rewrite_extraction_refs(extracted_data, ref_map) -> dict`: Rewrites `analysis` fields in all component, calc_variable, and calculation rows of the extraction dict from extraction names to template names before the overlay step.

`merge_layers()` calls Fix C after building the rename map (Phase 2 from LIMS-017) and before the component/calc overlay steps.

### Fix D — Alias injection into normalizer ref map (`merger.py`)

After Fix C rewrites refs in `extracted_data`, `merge_layers()` also injects extraction→template aliases into the step 4b normalization alias map (used by `_normalize_analysis_refs()`). This serves as belt-and-suspenders coverage for any refs that Fix C did not reach (e.g., nested or dynamically added refs).

Word-subset matching applies here too, with the same minimum 3-token guard.

### Runtime Fix — None-safe extraction list access (`merger.py`)

Changed `.get(key, [])` to `.get(key) or []` in 3 locations in `merge_layers()` to correctly handle `None`-valued extraction list fields.

### Hardening — Deep-copy at merge entry (`merger.py`)

`merge_layers()` now deep-copies `extracted_data` at the entry point. This prevents the caller's extraction dict from being mutated by ref rewriting (Fix C), which would be a traceability violation (ALCOA+ attributable/original principles).

---

## Files Modified

| File | Changes |
|------|---------|
| `main/src/lims/data_normalizer.py` | Added `_infer_analysis_type_from_name()`; modified `_normalize_analysis_type()` to call inference when value is `None` |
| `main/src/lims/merger.py` | Added `protected_keys`/`match_map_out` params to `_overlay_extracted_items()`; added `_build_extraction_to_template_map()` and `_rewrite_extraction_refs()`; updated `merge_layers()` with deep-copy, None-safety (`.get() or []`), Fix C ref rewriting, Fix D alias injection |
| `main/tests/lims/test_data_normalizer.py` | 11 new tests covering type inference from name keywords |
| `main/tests/lims/test_merger.py` | 13 new tests: protected name overlay, ref rewriting, E2E merge with truncated refs, caller immutability, Fix D truncated ref resolution |

---

## Test Results

```
65 passed (29 normalizer + 36 merger), 0 failed
```

---

## Design Decisions

1. **Minimum 3-token guard on word-subset matching**: Prevents short or generic substrings (e.g., `"Test"`) from incorrectly matching unrelated template names. Both Fix C and Fix D enforce this guard.

2. **Protected keys do not silently discard extraction names**: Conflicts are recorded in `match_map_out` so the SME review UI can surface them. No information is destroyed.

3. **Deep-copy over in-place mutation**: Extraction dict rewriting (Fix C) operates on a deep copy. The caller's dict is never modified, preserving the original extraction artifact for audit trail purposes (ALCOA+ compliance).

4. **Inference as fallback only**: `_infer_analysis_type_from_name()` is called only when the extracted type is `None`. Explicit extraction values are never overridden by inference.

---

## Related Issues

- [LIMS-017: L18 Run Validation Remediation Task](../LIMS-017-l18-run-validation-remediation-task.md) — introduced the hard validation gate and deterministic exact-match analysis resolution that this issue extends.

---

## Useful Commands

```bash
# Run normalizer tests
uv run pytest main/tests/lims/test_data_normalizer.py -v

# Run merger tests
uv run pytest main/tests/lims/test_merger.py -v

# Run all LIMS tests
uv run pytest main/tests/lims/ -v
```

---

## Next Steps

- Monitor merged output for `AND_ACS_DYE-LAB-2499.pdf` — confirm 3 analyses, all component refs resolved.
- Review `match_map_out` conflict records surfaced during SME review to verify no spurious name conflicts are flagged.
- Consider extending `_infer_analysis_type_from_name()` keyword table as new document types are processed.

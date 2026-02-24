# LIMS-020: Template-Locked Merge Mode — MDA Generation Quality Fix

**Date:** 2026-02-24
**Type:** Bug Fix / Architecture Enhancement
**Status:** Implemented — pending E2E runtime validation
**Branch:** `prjoject_p_protatype`

---

## Summary

Introduced template-locked merge mode in `merger.py` to eliminate spurious entities admitted into the MDA output from PDF extraction noise. For known test types (any `TestType` value other than `TestType.OTHER`), the template defines the exact structure: unmatched extracted entities are logged at WARNING level and rejected rather than appended. This change fixes low-precision MDA output observed during L18 E2E validation.

This document consolidates the content of the now-archived LIMS-018 (merger analysis matching and ref rewriting fixes) and LIMS-019 (L18 strict rerun checklist and audit protocol) into a single current reference. Both predecessor documents are preserved for audit traceability under `docs/project_p/archived/`.

---

## Problem

When processing `AND_ACS_DYE-LAB-2499.pdf` through the two-layer pipeline, the merged MDA output had low quality:

| Metric | Observed | Target |
|--------|----------|--------|
| Analysis count | 4 | 3 |
| Component alias-aware precision | 0.521 (+23 extra components) | >= 0.90 |
| SME_REQUIRED placeholder calculations | 4 | 0 |
| Calculation alias-aware precision | 0.846 | >= 0.95 |

The spurious 4th analysis row originated from PDF description text that LlamaExtract interpreted as an analysis entity. Because `_overlay_extracted_items()` unconditionally appended unmatched extracted entities, noise from the extraction pass entered the merged output unfiltered.

---

## Root Cause

In `main/src/lims/merger.py`, `_overlay_extracted_items()` unconditionally appended all unmatched extracted entities to the template rows. In two-layer mode for known test types (e.g., IDENTITY), the template defines the exact structure. Unmatched items from extraction are noise, not additions.

This was the primary driver of:
- Extra analysis row count
- Inflated component count (precision collapse)
- Placeholder calculations from spuriously admitted analysis rows

---

## Fix Applied (Template-Locked Merge Mode)

### Change to `_overlay_extracted_items()`

Added a `template_locked: bool = False` parameter. When `True`:
- Unmatched extracted items are logged at `WARNING` level with the entity key.
- The item is rejected and not appended to the result list.
- A rejection counter is incremented.

When `False` (default, unlocked), behavior is identical to the pre-fix implementation (backward compatible).

### Change to `merge_layers()`

`merge_layers()` now computes the lock flag before all four overlay calls:

```python
template_locked = test_type is not None and test_type != TestType.OTHER
```

All four `_overlay_extracted_items()` calls in `merge_layers()` pass this flag:
- analyses overlay
- components overlay
- calc_variables overlay
- calculations overlay

### Rejection Tracking

Rejection count is accumulated across all four overlay calls and stored in:

```python
MergeResult.stats["TEMPLATE_LOCKED_REJECTED"]
```

This provides a per-run audit trail of how many extracted entities were rejected by the lock.

### Mode Behavior by Test Type

| Condition | Mode | Behavior |
|-----------|------|----------|
| `test_type is None` | Unlocked | Unmatched items appended (original behavior) |
| `test_type == TestType.OTHER` | Unlocked | Unmatched items appended (original behavior) |
| `test_type` is any other value | Locked | Unmatched items rejected with WARNING log |

---

## Expected Quality Impact

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| Analysis count | 4 | 3 | 3 |
| Component alias-aware precision | 0.521 | 1.0 | >= 0.90 |
| SME_REQUIRED placeholder calculations | 4 | 0 | 0 |
| Calculation alias-aware precision | 0.846 | 1.0 | >= 0.95 |

---

## Files Modified

| File | Changes |
|------|---------|
| `main/src/lims/merger.py` | Added `template_locked` param to `_overlay_extracted_items()`; updated all 4 overlay calls in `merge_layers()`; added rejection counting; tracks `MergeResult.stats["TEMPLATE_LOCKED_REJECTED"]` |
| `main/tests/lims/test_merger.py` | Added 7 new `TestTemplateLocked` tests; updated 1 existing test to use `TestType.OTHER` to retain unlocked behavior |

---

## Test Results

```
43/43 merger tests passed (including 7 new TestTemplateLocked tests)
217/219 full LIMS suite passed (2 pre-existing failures unrelated to this fix)
Zero regressions
```

---

## Background: Prior Fixes Incorporated (from LIMS-018)

The following fixes were implemented before this change and remain active. They address separate but related merger quality issues:

### Analysis Type Inference (`data_normalizer.py`)

When `_normalize_analysis_type()` receives `None`, it calls `_infer_analysis_type_from_name()` to derive a type from name keywords. This allows `NULL`-typed extraction analyses to match template analyses of a known type.

### Protected Analysis Names During Overlay (`merger.py`)

`_overlay_extracted_items()` accepts `protected_keys: set[str]`. When `"name"` is in `protected_keys`, the template analysis name is never overwritten by the extraction name. Name conflicts are recorded in `match_map_out` for SME review.

### Extraction Ref Rewriting to Template Names (`merger.py`)

`_build_extraction_to_template_map()` and `_rewrite_extraction_refs()` rewrite truncated or alternate analysis names in component, calc_variable, and calculation `analysis` fields to canonical template names before the overlay step. Uses exact match first, then word-subset matching (minimum 3 tokens, unambiguous).

### None-Safe Extraction List Access (`merger.py`)

`.get(key, [])` changed to `.get(key) or []` to handle `None`-valued extraction list fields without `TypeError`.

### Deep-Copy at Merge Entry (`merger.py`)

`merge_layers()` deep-copies `extracted_data` at entry. The caller's extraction dict is never mutated, preserving the original artifact for audit trail (ALCOA+ compliant).

---

## Rerun Protocol (from LIMS-019)

To execute a reproducible L18 validation run and produce a canonical evidence package:

### Preconditions

- API healthy: `curl http://localhost:8080/health` returns HTTP 200.
- Environment keys loaded: LlamaExtract, Langfuse, model keys.
- Source PDF exists: `demo_data/data/AND_ACS_DYE-LAB-2499.pdf`
- Ground-truth files exist:
  - `demo_data/testing_data_ground_truth/AND_ACS_DYE-LAB-2499_pdf.md`
  - `demo_data/testing_data_ground_truth/AND_ACS_DYE-LAB-2499_xlsx.md`
- No parallel L18 run writing to the same output directory.

### Canonical Execution Command

```bash
python scripts/compare_lims_extractions.py \
  --pdf demo_data/data/AND_ACS_DYE-LAB-2499.pdf \
  --base-url http://localhost:8080 \
  --out-dir demo_data/e2e_outputs \
  --llama-cloud-results-dir demo_data/llama_cloud_results \
  --langfuse-traces-dir demo_data/langfuse
```

### Mandatory Run Artifacts

All of the following must exist inside `demo_data/e2e_outputs/<run_id>/`:

- `direct_result.json`
- `app_result.json`
- `comparison.json`
- `evidence_manifest.json`
- `trace_snapshot.json`

### Quality Gates for Rerun Signoff

| Gate | Threshold |
|------|-----------|
| Analysis count | Exactly 3 (no extra rows) |
| Component alias-aware precision | >= 0.90 |
| Component alias-aware recall | >= 0.98 |
| Calc-variable alias-aware exact semantic | = 1.00 |
| Calculation alias-aware exact semantic | >= 0.95 |
| SME_REQUIRED placeholder count | 0 |
| TEMPLATE_LOCKED_REJECTED stat | Present in MergeResult.stats |

### Fast Failure Rules

Stop immediately and mark run failed if:
- API call fails or times out before artifact completion.
- Harness exits without `run_id`/`run_dir` output.
- Mandatory artifacts missing.
- `comparison.json` cannot be parsed.
- Traceability fields are absent with no documented reason.

---

## Design Decisions

1. **Template-locked is opt-in per call site**: The default is `template_locked=False` so existing call sites not yet updated retain the original behavior. All four overlay calls in `merge_layers()` explicitly pass the computed flag.

2. **Rejection is logged, not silently dropped**: Every rejected entity is logged at WARNING with its key. The `TEMPLATE_LOCKED_REJECTED` stat provides a numeric summary for monitoring.

3. **TestType.OTHER uses unlocked mode**: Documents that cannot be classified remain in unlocked mode, preserving the pipeline's ability to handle novel document types.

4. **Backward compatibility preserved**: The `template_locked` parameter defaults to `False`. Code paths outside `merge_layers()` that call `_overlay_extracted_items()` directly are unaffected unless they opt in.

---

## Related Documents

- [LIMS-017: L18 Run Validation Remediation Task](LIMS-017-l18-run-validation-remediation-task.md) — introduced hard validation gate and exact-match analysis resolution
- [ISSUE-040: L18 Extraction Quality Gate and Merge Admission Control](../../docs/issues/ISSUE-040-l18-extraction-quality-gate-and-merge-admission-control.md) — tracks the quality gate and merge admission control work; template-locked merge mode addresses the merge admission control part
- [L19 Task: L18 Reproducible Rerun and Signoff Readiness](../../PRPs/tasks/L19-l18-reproducible-rerun-signoff-readiness.md)
- Archived predecessor docs:
  - [`archived/LIMS-018-mda-merger-validation-analysis-matching-fixes.md`](archived/LIMS-018-mda-merger-validation-analysis-matching-fixes.md)
  - [`archived/LIMS-019-l18-rerun-checklist-and-audit-protocol.md`](archived/LIMS-019-l18-rerun-checklist-and-audit-protocol.md)

---

## Useful Commands

```bash
# Run merger tests only
uv run pytest main/tests/lims/test_merger.py -v

# Run all LIMS tests
uv run pytest main/tests/lims/ -v

# Run normalizer tests
uv run pytest main/tests/lims/test_data_normalizer.py -v

# Execute canonical L18 rerun
python scripts/compare_lims_extractions.py \
  --pdf demo_data/data/AND_ACS_DYE-LAB-2499.pdf \
  --base-url http://localhost:8080 \
  --out-dir demo_data/e2e_outputs \
  --llama-cloud-results-dir demo_data/llama_cloud_results \
  --langfuse-traces-dir demo_data/langfuse
```

---

## Next Steps

1. **E2E validation with real PDF**: Run the canonical harness against `AND_ACS_DYE-LAB-2499.pdf` to confirm analysis count drops to 3 and precision metrics meet targets.
2. **Verify TEMPLATE_LOCKED_REJECTED stat**: Confirm the stat is present and non-zero in `MergeResult.stats` for the IDENTITY test type run.
3. **Check rerun quality gates**: All gates in the table above must pass before L19 signoff is declared.
4. **Update ISSUE-040**: After a successful E2E run, update ISSUE-040 status to reflect full resolution of the merge admission control part.
5. **Extend keyword table if needed**: If new document types expose gaps in `_infer_analysis_type_from_name()`, extend the keyword-to-type mapping accordingly.

# ISSUE-040 — L18 Extraction Quality Gate and Merge Admission Control

**Date:** 2026-02-23
**Updated:** 2026-02-24
**Status:** PARTIALLY RESOLVED — extraction quality gate implemented; merge admission control (template-locked mode) implemented; pending E2E runtime validation
**Category:** API/Data Quality
**Priority:** High

---

## Symptom
L18 E2E validation shows high-recall but low-precision output quality:
- extraction validation fails (`validated=False`, 169 schema errors)
- merger admits many non-component extracted rows into component sheet
- unmatched new extracted components are defaulted with weak semantics (`result_type='T'`), increasing false positives

---

## Error / Evidence
- `demo_data/api_ui_local_output/api_output.txt`:
  - `Pydantic validation failed ... 169 validation errors for MDATemplate`
  - many auto-added components with defaulted `result_type='T'`
- `demo_data/e2e_outputs/L18-e2e-evaluation-report-2026-02-23.md`:
  - alias-mapped component precision 0.521
  - +23 extra components vs GT-equivalent semantic set

---

## Affected Files
- `main/src/lims/pipeline.py`
- `main/src/lims/pdf_extractor.py`
- `main/src/lims/merger.py`
- `main/src/lims/config.py`

---

## Root Cause (Initial)
1. Pipeline does not enforce hard extraction quality gates prior to augmentation/merge.
2. Merger allows unmatched extracted components without strong admissibility checks.
3. New unmatched extracted components are defaulted to text result type (`T`) instead of being rejected or explicitly reviewed.

---

## Planned Fix
- Add configurable extraction quality gate in pipeline:
  - require validated extraction
  - enforce max null-field ratio threshold
- Compute and persist extraction quality metrics from extractor.
- Tighten merger admission for unmatched new components:
  - reject if required semantic fields are missing (no fallback defaulting)
  - remove automatic default `result_type='T'` path

---

## Implementation Update (2026-02-23)

### Root Cause Confirmation
Confirmed from run evidence: extraction outputs with high null density were still merged, and unmatched extracted rows were auto-admitted with permissive defaults.

### Files Modified

| File | Change |
|---|---|
| `main/src/lims/config.py` | Added extraction quality gate settings (`LIMS_EXTRACTION_QUALITY_GATE_ENABLED`, `LIMS_REQUIRE_VALIDATED_EXTRACTION`, `LIMS_EXTRACTION_MAX_NULL_RATIO`) + validation/parsing |
| `main/src/lims/pdf_extractor.py` | Added deterministic extraction quality metrics (`fields_scanned`, `null_like_fields`, `null_ratio`) to extraction result |
| `main/src/lims/pipeline.py` | Added `_enforce_extraction_quality_gate()` and hard-fail behavior before augment/merge in both two-layer and single-layer paths |
| `main/src/lims/merger.py` | Added non-component row heuristic gate; removed permissive defaulting for unmatched new component `result_type`; reject non-admissible rows |
| `demo_data/e2e_outputs/L18-e2e-evaluation-report-2026-02-23.md` | Expanded P0→P2 matrix and marked implemented P0 items |

### Validation Notes
- Static diagnostics: no editor errors on modified runtime files.
- Syntax check passed with `python -m py_compile` for modified LIMS runtime modules.
- Full test execution blocked on local environment dependency issues (`.venv` invalid under `uv`; missing `openpyxl` in system python test run).

### Template-Locked Merge Mode (2026-02-24)

The merge admission control part of this issue has been addressed by implementing template-locked merge mode in `main/src/lims/merger.py`. When the test type is a known value (not `None` and not `TestType.OTHER`), `_overlay_extracted_items()` is called with `template_locked=True`. Unmatched extracted entities are logged at WARNING and rejected rather than admitted. Rejection counts are tracked in `MergeResult.stats["TEMPLATE_LOCKED_REJECTED"]`.

Expected quality impact:
- Analysis count: 4 -> 3 (spurious 4th row eliminated)
- Component precision: 0.521 -> 1.0 (no spuriously admitted components)
- Placeholder calculations: 4 -> 0
- Calculation precision: 0.846 -> 1.0

Files modified: `main/src/lims/merger.py`, `main/tests/lims/test_merger.py`
Test results: 43/43 merger tests passed (7 new TestTemplateLocked tests added)
Reference: [LIMS-020](../../docs/project_p/LIMS-020-template-locked-merge-quality-fix.md)

### Remaining Work
- Re-run targeted LIMS tests in a valid environment to confirm E2E metrics meet targets.
- Complete pending P0 item: alias-aware comparator integration in official L18 harness.
- Execute canonical L18 rerun per LIMS-020 rerun protocol and verify all quality gates pass.

---

## Prevention
- Keep quality gate enabled by default in local and CI-like validation runs.
- Maintain deterministic mismatch report package for each run.
- Treat non-admissible extracted entities as rejected with explicit logs (not silent conversion).

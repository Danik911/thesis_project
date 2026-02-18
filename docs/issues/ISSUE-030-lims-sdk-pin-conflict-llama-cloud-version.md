# ISSUE-030: LIMS SDK Pin Conflict (`llama-cloud-services==0.6.93` vs `llama-cloud>=1.4.0`)

**Date:** 2026-02-18  
**Status:** Resolved  
**Consolidated Into:** `ISSUE-032`  
**Category:** Dependencies/API  
**Priority:** High

---

## Symptom

Running `uv run pytest` failed dependency resolution:

- `llama-cloud-services==0.6.93` requires `llama-cloud==0.1.46`
- L7 migration pin attempt set `llama-cloud>=1.4.0`

This made the project requirements unsatisfiable.

---

## Root Cause

Current runtime extraction path still uses `llama-cloud-services` + `LlamaExtract`. That package version is tightly coupled to an older `llama-cloud` package version.

---

## Files Modified

| File | Change |
|------|--------|
| `pyproject.toml` | Set compatible pins: `llama-cloud-services==0.6.93`, `llama-cloud==0.1.46` |

---

## Resolution

Pinned compatible versions and reran tests successfully.

Verification:

- `uv run pytest main/tests/lims/test_data_normalizer.py main/tests/lims/test_extraction.py -v`
- `uv run pytest main/tests/lims/ -v`

---

## Prevention

1. For current `llamaextract` runtime path, keep SDK pins compatible.
2. Perform Parse v2 migration in a separate runtime path before upgrading to new `llama-cloud` major line.

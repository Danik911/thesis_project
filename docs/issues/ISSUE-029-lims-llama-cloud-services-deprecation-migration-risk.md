# ISSUE-029: LIMS `llama-cloud-services` Deprecation Migration Risk

**Date:** 2026-02-18  
**Status:** Resolved  
**Category:** Dependencies/API  
**Priority:** High

---

## Symptom

LIMS extraction currently depends on `llama-cloud-services` runtime usage in `pdf_extractor.py`. The package has a published deprecation track and introduces medium-term maintenance risk for reproducible extraction workflows.

---

## Risk

- SDK API surface may diverge from newer `llama-cloud` client interfaces.
- Future updates can break extraction or prevent leveraging new parse/extraction capabilities.
- Regulatory reproducibility requirements need explicit dependency/version strategy.

---

## Root Cause

The current runtime extraction implementation uses `llama_cloud_services.LlamaExtract` and cannot be switched to `llama-cloud` v1.4+ in-place without introducing a new Parse v2/structured extraction path.

---

## Files Modified

| File | Change |
|------|--------|
| `pyproject.toml` | Pinned stable compatible runtime versions (`llama-cloud-services==0.6.93`, `llama-cloud==0.1.46`). |
| `main/src/lims/config.py` | Added `extraction_api` switch for controlled migration path. |
| `main/src/lims/pdf_extractor.py` | Added explicit fail-loud guard for unsupported `llamaparse_v2` runtime path. |
| `docs/project_p/LIMS-005-l7-extraction-normalization-sdk-migration.md` | Added research findings, empirical comparison, and migration recommendation. |

---

## Resolution

Implemented a staged migration strategy:

1. Keep current runtime stable via compatible SDK pins.
2. Add API selection config for future A/B testing.
3. Document Parse v2 migration path and empirical comparison data.

---

## Follow-up

- Remaining semantic extraction quality gap is tracked in `ISSUE-031`.

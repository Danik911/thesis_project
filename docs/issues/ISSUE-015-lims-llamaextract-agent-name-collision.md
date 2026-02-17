# ISSUE-015: LIMS LlamaExtract Agent Name Collision

**Date:** 2026-02-17  
**Status:** Resolved  
**Category:** API  
**Priority:** High

---

## Symptom

Repeated calls to `POST /lims/extract` failed with HTTP 500 wrapping LlamaExtract HTTP 409:

`An extraction agent with the name 'mda-AND_ACS_DYE-LAB-2499' already exists in this project.`

## Affected Files

| File | Area |
|------|------|
| `main/src/lims/pdf_extractor.py` | LlamaExtract agent creation naming |

---

## Root Cause

Agent names were generated deterministically from the uploaded filename stem:

`mda-{Path(filename).stem[:30]}`

When the same PDF filename was uploaded again, the service attempted to create an already-existing agent name and returned HTTP 409.

---

## Resolution

Generate a unique agent name on every request by appending a short UUID suffix:

`mda-{Path(filename).stem[:20]}-{uuid4().hex[:8]}`

This preserves filename traceability while eliminating naming collisions.

---

## Files Modified

| File | Change |
|------|--------|
| `main/src/lims/pdf_extractor.py` | Added `uuid4` import and unique suffix in `agent_name` generation |

---

## Prevention Guidance

1. Avoid deterministic external resource names when providers enforce uniqueness.
2. Include a stable traceable prefix plus a random/unique suffix for repeatable operations.
3. Add regression verification by calling extraction endpoint multiple times with same filename.

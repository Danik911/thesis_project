# ISSUE-035: L15 Frontend Workflow Blocked by Incomplete L14 API Contracts

## Date
2026-02-19

## Status
RESOLVED (2026-02-19)

## Consolidation
Consolidated into `ISSUE-037-l15-frontend-delivery-and-local-e2e-consolidated.md`.

## Symptom
Task L15 frontend implementation required stable L14 payload contracts for pipeline stages, but backend contracts were initially in-progress. This blocked strict integration for:

- `/lims/classify` response schema
- `/lims/template/{test_type}` payload
- `/lims/extract` conflict/provenance/stage details payload
- `/lims/status/{job_id}` stage/provenance/conflict payload

## Root Cause
Frontend L15 scaffold was built before finalized L14 contracts were available, so provisional placeholder mappings were used in `lims.tsx`.

## Resolution Summary
After L14 completion, L15 frontend was migrated to strict contract-bound integration:

1. Added typed API contracts in `main/frontend/types/lims.ts`
2. Rewired workflow to use `/lims/classify` then `/lims/template/{test_type}` before `/lims/extract`
3. Mapped backend `provenance.fields` paths (e.g., `components[2].units`) to UI cell keys used by `MDAViewer`
4. Mapped backend `conflicts` and `stage_details` directly into Merge and Pipeline Reasoning UI panels
5. Updated classification UI to explicit Confirm/Override actions

## Files Modified

| File | Change |
|------|--------|
| `main/frontend/types/lims.ts` | Added strict TypeScript interfaces for classify/template/extract/status payloads |
| `main/frontend/pages/lims.tsx` | Replaced scaffold placeholders with finalized L14 endpoint and payload mapping |
| `main/frontend/components/ClassificationPanel.tsx` | Added explicit Confirm + Override buttons and test-type icon |
| `main/frontend/components/LIMSStepIndicator.tsx` | Added L14 runtime status mappings (`LOADING_TEMPLATE`, `AUGMENTING`, `PENDING_REVIEW`) |

## Validation
- Type/lint diagnostics: no errors in modified L15 files.
- Frontend lint command passes with only pre-existing warnings outside L15 scope.

## Prevention Guidance
For cross-task dependencies, publish OpenAPI snapshots or response-model stubs before frontend workflow rewrites begin.

# LIMS-017: L18 Run Validation Remediation Task

**Date:** 2026-02-21  
**Type:** Issue/Remediation Task  
**Status:** Implemented

## Context
This task captures the end-to-end evaluation of the L18 AI4LIMS run against provided ground truth artifacts and Langfuse traces.

### Evaluation Goal
- Identify all run inconsistencies.
- Identify architectural weak points causing those inconsistencies.
- Propose prioritized remediation steps.

### High-Level Findings
1. Analysis identity drift across merge created broken cross-sheet references.
2. Invalid merged output can still proceed to review flow (validation warning only).
3. Export path performs normalization/forward-fill mutations before final validation.
4. Extraction output includes noise entries (`EXT_None`) and namespace divergence from expected analysis IDs.
5. One expected extraction artifact file is empty despite trace evidence of extraction.
6. Review UI warning block has long-text overflow/readability issues.

## Remediation Tasks (Prioritized)

### P0 (Blockers)
1. Enforce hard gate on post-merge validation failure (no progression to review/export).
2. Implement atomic analysis rename propagation across dependent sheets:
   - `components.analysis`
   - `calc_variables.analysis`
   - `calculations.analysis`
   - `reference_analysis` fields where applicable
3. Remove export-time semantic mutation (keep export as pure serialization + strict validation).

### P1
4. Replace ambiguous prefix/substring analysis matching with deterministic resolution.
5. Add extraction noise filtering for revision-history/non-analysis rows before merge.
6. Align template analysis namespace contract with document/site naming expectations.

### P2
7. Improve UI rendering for large validator payloads (bounded container + safe wrapping/scrolling).

## File Index (All files referenced in investigation)

### Ground Truth / Artifacts
- [demo_data/parced/AND_ACS_DYE-LAB-2499_pdf.md](demo_data/parced/AND_ACS_DYE-LAB-2499_pdf.md)
- [demo_data/parced/AND_ACS_DYE-LAB-2499_xlsx.md](demo_data/parced/AND_ACS_DYE-LAB-2499_xlsx.md)
- [demo_data/llama_cloud_results/lims_extract_6dt2m07g.json](demo_data/llama_cloud_results/lims_extract_6dt2m07g.json)
- [demo_data/llama_cloud_results/lims_extract_6dt2m07g.pdf.json](demo_data/llama_cloud_results/lims_extract_6dt2m07g.pdf.json)
- [demo_data/llama_cloud_results/output_AND_ACS_DYE-LAB-2499_MDA.xlsx.md](demo_data/llama_cloud_results/output_AND_ACS_DYE-LAB-2499_MDA.xlsx.md)

### Backend / Pipeline / Schema
- [main/src/lims/pdf_extractor.py](main/src/lims/pdf_extractor.py)
- [main/src/lims/data_normalizer.py](main/src/lims/data_normalizer.py)
- [main/src/lims/merger.py](main/src/lims/merger.py)
- [main/src/lims/pipeline.py](main/src/lims/pipeline.py)
- [main/src/lims/mda_schema.py](main/src/lims/mda_schema.py)
- [main/src/lims/templates/identity.py](main/src/lims/templates/identity.py)
- [main/api/lims_router.py](main/api/lims_router.py)

### Frontend
- [main/frontend/pages/lims.tsx](main/frontend/pages/lims.tsx)

### Related Project Docs Referenced
- [CLAUDE.md](CLAUDE.md)
- [.github/copilot-instructions.md](.github/copilot-instructions.md)

## Implementation Summary (2026-02-21)

All 7 remediation items implemented across 7 phases:

### Phase 1: Extraction Noise Filter
- `merger.py`: `_sanitize_new_analysis()` returns `None` for phantom rows (name is None/empty/"None"/"unknown")
- `merger.py`: `_overlay_extracted_items()` skips items where sanitize_fn returns None

### Phase 2: Atomic Analysis Rename Propagation
- `merger.py`: `_match_analysis()` gains `exclude_indices` for exclusive matching
- `merger.py`: New `_propagate_analysis_renames()` updates dependent sheet refs
- `merger.py`: `merge_layers()` builds rename map + calls propagation before component overlay

### Phase 3: Move Normalization Pre-Review
- `merger.py`: `merge_layers()` calls `_normalize_analysis_refs()` + `_forward_fill_field()` before validation (not at export)

### Phase 4: Hard Validation Gate
- `job_store.py`: Added `validated: bool` and `validation_error: Optional[str]` to LIMSJob
- `pipeline.py`: Stores validation state on job record
- `lims_router.py`: Approve endpoint runs `MDATemplate.model_validate()` before allowing approval
- `lims_router.py`: Chat endpoint re-validates after edits, returns validation state
- `lims_router.py`: Status endpoint returns validated/validation_error
- `lims.tsx`: Approve button disabled when `!validated`, red blocked message shown
- `ChatInterface.tsx`: New `onValidationUpdate` callback propagates chat validation changes
- `types/lims.ts`: StatusResponse gains validated/validation_error fields

### Phase 5: Remove Export-Time Mutation
- `lims_router.py`: Export endpoint reduced to pure `MDATemplate.model_validate()` + `export_mda_to_xlsx()`

### Phase 6: Deterministic Analysis Matching
- `data_normalizer.py`: `_resolve_analysis_name()` stripped to exact-match only via alias map

### Phase 7: UI Overflow Fix
- `lims.tsx`: Validation error wrapped in `max-h-48 overflow-y-auto`
- `PipelineStageDetail.tsx`: Expanded panel gets `max-h-60 overflow-y-auto`, bullets get `break-words`
- `MergeConflictPanel.tsx`: Value divs get `max-h-24 overflow-y-auto break-words`

### Files Modified
| File | Phases |
|------|--------|
| `main/src/lims/merger.py` | 1, 2, 3 |
| `main/api/lims_router.py` | 4, 5 |
| `main/src/lims/pipeline.py` | 4 |
| `main/src/lims/job_store.py` | 4 |
| `main/src/lims/data_normalizer.py` | 6 |
| `main/frontend/pages/lims.tsx` | 4, 7 |
| `main/frontend/components/ChatInterface.tsx` | 4 |
| `main/frontend/components/PipelineStageDetail.tsx` | 7 |
| `main/frontend/components/MergeConflictPanel.tsx` | 7 |
| `main/frontend/types/lims.ts` | 4 |
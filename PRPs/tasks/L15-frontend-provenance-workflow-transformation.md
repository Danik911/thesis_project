# Task L15 — Frontend: Provenance Badges, Classification & Pipeline Workflow UI

**Phase:** 8f (Two-Layer Pipeline — Frontend) | **Dependencies:** L14 (Pipeline Core)
**Branch:** `prjoject_p_protatype`
**Estimated effort:** 4 days
**Status:** NOT STARTED (WAITING ON L14 API CONTRACTS — handoff updated 2026-02-19)

## Handoff Update (2026-02-19)

- **Implementation readiness:** Frontend can start component scaffolding, but full workflow integration depends on L14 endpoints and payloads.
- **Reference data for UI mocks:** `output/prepared_l10l15/per_document/` plus quality/provenance expectations from task specs.
- **Backend contract prerequisite:** `/lims/classify`, template preview payload, merge conflict payload, and stage detail payload from L14.
- **Known caveat:** Do not wire UI against legacy prepared artifacts from `output/prepared/`; use canonical `output/prepared_l10l15/`.
- **Next agent action:** Define strict TypeScript interfaces from L14 response models before implementing workflow rewrites.

---

## Objective

Transform the frontend from the current 5-state workflow to an 8-state pipeline with provenance visualization. SMEs see color-coded source attribution on every cell, a classification confirmation panel, template preview, merge conflict resolution, and expandable pipeline stage reasoning.

---

## Files to Create

| File | Purpose |
|------|---------|
| `main/frontend/components/ProvenanceBadge.tsx` | Color-coded source badge: green=Template, blue=Extracted, purple=Inferred, orange=SME Required, yellow=SME Modified |
| `main/frontend/components/ClassificationPanel.tsx` | Displays detected test type with confidence, allows SME to confirm or override |
| `main/frontend/components/TemplatePreview.tsx` | Shows template skeleton with fixed vs variable slot visualization |
| `main/frontend/components/MergeConflictPanel.tsx` | Side-by-side conflict resolution: template value vs extracted value |
| `main/frontend/components/PipelineStageDetail.tsx` | Expandable accordion showing AI reasoning per pipeline stage |

## Files to Modify

| File | Change | Risk |
|------|--------|------|
| `main/frontend/components/LIMSStepIndicator.tsx` | Update STAGES array to 6 stages: Classify, Template, Extract, Merge, Review, Export | LOW |
| `main/frontend/components/MDAViewer.tsx` | Add `provenanceMap` prop; render ProvenanceBadge per cell | LOW |
| `main/frontend/pages/lims.tsx` | Major rewrite: 5-state -> 8-state workflow with new view components | HIGH |

---

## Implementation Details

### 1. ProvenanceBadge.tsx

Small color-coded chip displayed next to each MDA cell value:
- Green badge: "Template" — from curated skeleton
- Blue badge: "Extracted" — from PDF with page citation
- Purple badge: "Inferred" — AI-filled from standards RAG
- Orange badge: "SME Required" — gap needing human input
- Yellow badge: "SME Modified" — changed by SME during review

```tsx
interface ProvenanceBadgeProps {
  source: 'TEMPLATE' | 'EXTRACTED' | 'INFERRED' | 'SME_REQUIRED' | 'SME_MODIFIED';
  confidence?: number;
  detail?: string;
}
```

### 2. ClassificationPanel.tsx

Shows after PDF upload:
- Detected test type with icon
- Confidence score bar
- Classification method (rules/LLM/hybrid)
- Evidence list (keywords found, etc.)
- "Confirm" and "Override" buttons

### 3. TemplatePreview.tsx

Shows the template skeleton before extraction:
- Fixed fields (green) — from template
- Variable slots (dashed border) — to be extracted
- Component count: "42 template + 18 variable"

### 4. MergeConflictPanel.tsx

Side-by-side comparison for each conflict:
- Left: Template value
- Right: Extracted value
- Radio buttons: "Use Template" / "Use Extracted" / "Enter Custom"
- Batch actions: "Accept All Template" / "Accept All Extracted"

### 5. PipelineStageDetail.tsx

Expandable accordion with one section per pipeline stage:
- Classify: method used, keywords matched, confidence
- Template: component counts, variable fields
- Extract: extraction duration, fields found
- Augment: standards cited, gaps filled
- Merge: conflicts found, auto-resolutions

### 6. LIMSStepIndicator.tsx — Updated Stages

```tsx
const STAGES = [
  { key: 'classify', label: 'Classify', icon: '...' },
  { key: 'template', label: 'Template', icon: '...' },
  { key: 'extract', label: 'Extract', icon: '...' },
  { key: 'merge', label: 'Merge', icon: '...' },
  { key: 'review', label: 'Review', icon: '...' },
  { key: 'export', label: 'Export', icon: '...' },
];
```

### 7. lims.tsx — Rewritten Workflow

New states: idle -> uploading -> classifying -> template_preview -> extracting -> merging -> review -> exporting -> done

---

## Testing Strategy

- Upload PDF -> classification panel appears with correct test type
- Template preview shows skeleton structure
- After extraction, MDA table shows provenance badges on every cell
- Conflict panel allows resolution
- Pipeline stages show reasoning details
- Chat refinement still works alongside new components
- Export produces XLSX with optional provenance sheet

---

## Gate Criteria

- [ ] ProvenanceBadge renders 5 distinct colors for 5 source types
- [ ] ClassificationPanel shows test type with confirm/override
- [ ] TemplatePreview differentiates fixed vs variable fields
- [ ] MergeConflictPanel allows individual and batch conflict resolution
- [ ] PipelineStageDetail shows reasoning for each pipeline stage
- [ ] LIMSStepIndicator shows 6 stages
- [ ] MDAViewer renders provenance badges per cell when provenanceMap provided
- [ ] Full 8-state workflow navigates correctly
- [ ] Existing chat functionality preserved

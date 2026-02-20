# Task L17 — Frontend: Brand-Led Platform Repositioning (LabAI) & AI Pillar Visibility

**Phase:** 8h (Positioning + UX Narrative Layer) | **Dependencies:** L15, L16
**Branch:** `prjoject_p_protatype`
**Estimated effort:** 2–3 days
**Status:** NOT STARTED

---

## Objective

Reframe the current LIMS UI as part of a holistic platform brand (`LabAI`) by making core differentiators immediately visible:

1. **Deterministic ML** (predictable classify/route/validate behavior)
2. **Agentic Orchestration** (staged pipeline execution)
3. **RAG Grounding** (standards-backed suggestions)
4. **Human-in-the-Loop (HITL)** (SME review and approval authority)

The UX must remain assistive: **copilot/helper, not human replacement**.

---

## Positioning to Implement in UI

### Category Statement

`LabAI` is a **deterministic AI copilot platform** for pharmaceutical test-method digitization.

### Messaging Principles

- **Platform first:** present existing thesis capabilities + LIMS as one coherent system.
- **Method-agnostic:** emphasize support for varied test method families via templates/workflows.
- **Human authority:** state clearly that AI proposes, humans approve.
- **Compliance confidence:** show provenance, stage reasoning, and auditability as first-class UX signals.

### Tagline Candidates (for hero/sub-hero testing)

- "LabAI — Deterministic Intelligence for Method Lifecycle"
- "LabAI — AI Copilot for Pharmaceutical Methods"
- "LabAI — Agentic Workflow, Human Authority"

---

## Files to Modify

| File | Change | Risk |
|------|--------|------|
| `main/frontend/pages/lims.tsx` | Add platform-level hero/header narrative, pillar cards, and helper-not-replacement messaging; keep workflow states unchanged | MEDIUM |
| `main/frontend/components/LIMSStepIndicator.tsx` | Update labels/microcopy to reflect deterministic flow and agentic orchestration semantics | LOW |
| `main/frontend/components/PipelineStageDetail.tsx` | Add explicit stage annotations for ML/RAG/HITL responsibilities | LOW |
| `main/frontend/components/ClassificationPanel.tsx` | Reword to "deterministic classification" and show confidence rationale clearly | LOW |
| `main/frontend/components/TemplatePreview.tsx` | Surface method-agnostic template concept and fixed/variable contract | LOW |
| `main/frontend/components/MergeConflictPanel.tsx` | Emphasize human decision ownership for conflicts | LOW |
| `main/frontend/components/ChatInterface.tsx` | Reframe assistant copy as copilot helper (suggestions + SME confirmation) | LOW |

---

## Optional New Files (if needed for cleanliness)

| File | Purpose |
|------|---------|
| `main/frontend/components/PlatformPillars.tsx` | Compact visual block for Deterministic ML / Agentic Orchestration / RAG / HITL |
| `main/frontend/components/TrustBanner.tsx` | One-line trust statement: "AI-assisted, human-approved, audit-ready" |

---

## Implementation Details

### 1. Brand Shell in `lims.tsx`

Add a top narrative block before upload controls:
- Product name: `LabAI Method Copilot` (under umbrella `LabAI`)
- Short value proposition (2 lines max)
- Four pillar chips/cards:
  - Deterministic ML
  - Agentic Orchestration
  - Standards RAG
  - Human-in-the-Loop

Keep existing extraction/review/export flow intact.

### 2. Make Key Features Visually Prominent

Use persistent summary indicators near step indicator or right rail:
- `ML`: Classifier method + confidence
- `RAG`: Standards context status (used/skipped)
- `HITL`: current approval gate state
- `Audit`: provenance available (yes/no)

Do not add new backend dependencies for this task; render from existing response payloads.

### 3. "Copilot, Not Replacement" Microcopy

Inject clear copy in 3 places:
- Hero/support text
- Review state panel
- Merge conflict resolution panel

Required wording pattern:
- "AI suggests" / "SME decides" / "Final approval is human-controlled"

### 4. Method-Agnostic Messaging

In template and classify views, add concise explanation:
- "This workflow adapts to multiple method types via template + extraction contracts."

Avoid claiming universal coverage; keep wording "method-agnostic architecture" and "extensible templates".

### 5. Keep UX Abstract but Catchy

- Reduce dense technical details in default view; keep details in expandable stage panels.
- Use short labels and outcome-centric text.
- Preserve existing dark theme tokens and current component system (no new custom design system).

---

## Acceptance Criteria

- [ ] UI presents a clear platform identity (`LabAI`) instead of only feature-level screens
- [ ] Four pillars (Deterministic ML, Agentic Orchestration, RAG, HITL) are visible without scrolling in desktop view
- [ ] Workflow remains functionally identical (no regression in upload → review → export)
- [ ] At least 3 visible statements reinforce "copilot/helper, not replacement"
- [ ] Method-agnostic positioning appears in classify/template-related UI
- [ ] Existing provenance/conflict/review components still render and behave correctly
- [ ] No hard-coded new design tokens outside existing Tailwind/theme patterns

---

## Testing Strategy

### Manual UX Verification

1. Load `/lims` and confirm hero + platform narrative appears.
2. Upload PDF and verify pillar visibility persists while workflow progresses.
3. Confirm classification panel shows deterministic framing and confidence evidence.
4. Confirm review/merge states show human-approval ownership language.
5. Export flow still works after review/approval path.

### Regression Checks

- `npm run lint` in `main/frontend`
- Run/verify key LIMS page interactions locally (upload, review, export)

---

## Gate Criteria

- [ ] Brand narrative is coherent across entry screen and review flow
- [ ] Core AI differentiators are immediately discoverable to stakeholders
- [ ] "Human in control" message is explicit and repeated in critical UX moments
- [ ] No backend contract changes required
- [ ] No regressions in existing L15 workflow behaviors

---

## Notes for Stakeholder Demo

Suggested one-liner for presenter notes:

> "LabAI combines deterministic ML, agentic orchestration, and standards-grounded RAG to accelerate method digitization — with humans retaining final authority at every critical decision point."

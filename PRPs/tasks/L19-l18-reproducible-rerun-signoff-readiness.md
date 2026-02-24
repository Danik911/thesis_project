# Task L19 — L18 Reproducible Rerun & Signoff Readiness Consolidation

**Phase:** 8i (Validation + Monitoring Readiness)  
**Dependencies:** L14, L15, L16, L17, L18  
**Branch:** `prjoject_p_protatype`  
**Estimated effort:** 1–2 days  
**Status:** IN PROGRESS — template-locked merge mode implemented (2026-02-24); pending canonical E2E rerun

---

## Objective

Create one **audit-clean, reproducible, single-run evidence package** for the LAB-2499 scenario and reconcile all L18 inconsistencies so signoff decisions are based on one canonical run only.

This task is the consolidation/finalization layer after L18 analysis work.

---

## Why this task exists

Current L18 evidence shows progress but still has cross-artifact inconsistencies (metric drift, mixed snapshots, and non-canonical trace export patterns). L19 closes that gap by enforcing a strict rerun protocol and one-source-of-truth reporting.

---

## Scope

### In Scope
1. Execute one controlled rerun with deterministic run_id artifacts.
2. Produce canonical evidence package (`comparison.json`, `evidence_manifest.json`, `trace_snapshot.json`, raw outputs).
3. Validate output quality against ground truth using strict + alias-aware comparisons.
4. Validate traceability package consistency (API trace IDs + stage spans + persisted references).
5. Publish final run report with explicit pass/fail against acceptance thresholds.
6. Reconcile previous inconsistency points (counts/placeholders/analysis cardinality/source-of-truth metrics).

### Out of Scope
- New feature development unrelated to L18 quality/traceability closure.
- Multi-method benchmark expansion (track separately unless explicitly requested).
- UI redesign work.

---

## Execution Protocol (Mandatory)

- Do not run ad hoc comparisons outside the canonical harness.
- Do not mix artifacts from different run_ids in the same report.
- If mandatory artifacts are missing, mark run invalid and stop.
- No fallback logic: fail loudly with diagnostics when gates fail.

---

## Essential Documents (single source map)

## A) Task and architecture anchors
- [L18 task spec](L18-e2e-ground-truth-comparison-and-traceability.md)
- [L16 pipeline validation prerequisite](L16-two-layer-pipeline-validation-e2e.md)
- [L14 pipeline core implementation](L14-pipeline-core-extractor-merger-orchestrator.md)
- [System architecture reference](../../docs/ARCHITECTURE.md)
- [Project structure reference](../../docs/PROJECT_STRUCTURE.md)

## B) Ground truth and run evidence inputs
- [Input ground truth (PDF parse)](../../demo_data/testing_data_ground_truth/AND_ACS_DYE-LAB-2499_pdf.md)
- [Output ground truth (MDA)](../../demo_data/testing_data_ground_truth/AND_ACS_DYE-LAB-2499_xlsx.md)
- [Current app/API runtime evidence log](../../demo_data/api_ui_local_output/api_output.txt)
- [Current app output snapshot](../../demo_data/e2e_outputs/output.md)
- [Prior L18 evaluation report](../../demo_data/e2e_outputs/L18-e2e-evaluation-report-2026-02-23.md)
- [Comprehensive inconsistency analysis](../../demo_data/e2e_outputs/L18-comprehensive-analysis-and-remediation-2026-02-23.md)

## C) Rerun protocol and implementation docs
- [Template-locked merge fix + rerun protocol (LIMS-020)](../../docs/project_p/LIMS-020-template-locked-merge-quality-fix.md) — consolidated reference; supersedes LIMS-018 and LIMS-019
- [L18 remediation doc](../../docs/project_p/LIMS-017-l18-run-validation-remediation-task.md)
- [Extraction optimization and LlamaCloud alignment](../../docs/project_p/LIMS-016-extraction-optimization-llamacloud-v2-alignment.md)
- Archived: [LIMS-018 merger fixes](../../docs/project_p/archived/LIMS-018-mda-merger-validation-analysis-matching-fixes.md)
- Archived: [LIMS-019 rerun checklist](../../docs/project_p/archived/LIMS-019-l18-rerun-checklist-and-audit-protocol.md)

## D) Issue tracking and risk controls
- [Issue 040 — extraction quality gate & merge admission control](../../docs/issues/ISSUE-040-l18-extraction-quality-gate-and-merge-admission-control.md)
- [Issue 038 — grounded chat/provenance context](../../docs/issues/ISSUE-038-lims-chat-missing-grounded-context-and-provenance.md)

## E) Tooling/harness source of truth
- [Comparator harness](../../scripts/compare_lims_extractions.py)

---

## Required Run Outputs (for this task to pass)

Inside one run directory under `demo_data/e2e_outputs/<run_id>/`:
- `direct_result.json`
- `app_result.json`
- `comparison.json`
- `evidence_manifest.json`
- `trace_snapshot.json`

And cross-folders:
- `demo_data/llama_cloud_results/<run_id>_direct_result.json`
- `demo_data/langfuse/<run_id>_trace_refs.json`

---

## Acceptance Criteria

- [ ] Canonical rerun executed via official harness only.
- [ ] All mandatory artifacts present for one run_id.
- [ ] Reported metrics are generated from that run’s `comparison.json` only.
- [ ] No stale/mixed metric contradictions remain (validation errors, placeholder count, analysis count).
- [ ] Traceability package contains API trace references and stage span coverage evidence.
- [ ] Explicit pass/fail decision documented against thresholds.
- [ ] Unresolved gaps listed with prioritized remediation actions.

### Implementation Progress (2026-02-24)

The following criteria are now closer to met due to the template-locked merge mode fix:

- [x] Merge admission control implemented: `_overlay_extracted_items(template_locked=True)` rejects unmatched extracted entities for known test types. Tracked in `MergeResult.stats["TEMPLATE_LOCKED_REJECTED"]`. See [LIMS-020](../../docs/project_p/LIMS-020-template-locked-merge-quality-fix.md).
- [x] Extra analysis row blocked: spurious 4th analysis from PDF description text is rejected.
- [x] Placeholder calculations expected to reach 0 (from 4) once E2E run confirms.
- [ ] Canonical E2E rerun not yet executed. Run per LIMS-020 rerun protocol to confirm quality gates.
- [ ] Evidence package not yet generated for this fix iteration.

---

## Quality Gates (minimum thresholds)

- Alias-aware component precision >= 0.90
- Alias-aware component recall >= 0.98
- Alias-aware calc-variable exact semantic = 1.00
- Alias-aware calculation exact semantic >= 0.95
- Placeholder calculations in final signoff output = 0
- Canonical evidence package completeness = 100%

---

## Work Plan

1. **Preflight validation**
   - Confirm API health, env readiness, and source files.
2. **Canonical rerun**
   - Execute comparator harness using LIMS-019 protocol.
3. **Artifact integrity checks**
   - Confirm required files and hashes/trace references.
4. **Quality + traceability scoring**
   - Evaluate strict/alias-aware output and span coverage.
5. **Consistency reconciliation**
   - Resolve all previously observed count/mismatch conflicts.
6. **Final signoff report**
   - Publish one run-scoped report with pass/fail and next actions.

---

## Deliverables

1. Canonical run artifact folder (`demo_data/e2e_outputs/<run_id>/...`).
2. Final L19 run report (single-run, no mixed evidence).
3. Updated issue note if unresolved blockers remain (reference run_id and manifest).

---

## Risk Notes

- If retrieval gate fails (e.g., method-family mismatch), augmentation may be skipped; report must explicitly state that RAG was functional but non-contributory for this run.
- If merge still introduces extra analysis family or placeholders, run cannot be signoff-ready.
- Mixed trace export schema/duplicate files must not be treated as canonical evidence without normalization.

---

## Definition of Done

L19 is complete only when one run_id has a complete, internally consistent, auditable evidence package and the final report can be reviewed independently without referring to conflicting prior snapshots.

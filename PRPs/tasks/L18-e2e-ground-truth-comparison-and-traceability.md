# Task L18 — E2E Ground-Truth Comparison & Full Traceability Validation

**Phase:** 8i (Validation + Monitoring Readiness) | **Dependencies:** L14, L15, L16, L17  
**Branch:** `prjoject_p_protatype`  
**Estimated effort:** 2–4 days  
**Status:** NOT STARTED

---

## Objective

Run a controlled end-to-end validation for AI4LIMS using real method artifacts and complete traceability:

1. Compare **input parsing quality** (app parse vs document ground truth)
2. Compare **output MDA quality** (app-generated MDA vs MDA ground truth)
3. Verify **full monitoring/tracing coverage** (Langfuse + API trace metadata + persisted artifacts)
4. Produce a reproducible debugging package for root-cause analysis

---

## Ground Truth Sources (Authoritative)

### Input Ground Truth (PDF content parse)
- `demo_data/testing_data_ground_truth/AND_ACS_DYE-LAB-2499_pdf.md`

### Output Ground Truth (Expected MDA from LabWare)
- `demo_data/testing_data_ground_truth/AND_ACS_DYE-LAB-2499_xlsx.md`

These are the canonical references for this task.

### Trace / Output Directories (current structure)
- Langfuse trace exports: `demo_data/langfuse/`
- LlamaCloud UI export results: `demo_data/llama_cloud_results/`
- App run outputs for E2E: `demo_data/e2e_outputs/`

---

## Context: What We Already Did

### Completed Technical Work

1. **Chat context/provenance grounding fix (root-cause addressed)**
   - `main/api/lims_router.py`
   - `main/src/lims/chat_agent.py`
   - `main/src/lims/prompts/chat_system_prompt.py`
   - Goal: stop generic chat responses and enforce source-attributed explanations.

2. **Extraction optimization wiring**
   - `main/src/lims/config.py`
   - `main/src/lims/pdf_extractor.py`
   - `main/src/lims/extraction_schema.py`
   - Goal: apply real `ExtractConfig` knobs (mode/model/context/metadata) instead of default config.

3. **E2E comparison harness added**
   - `scripts/compare_lims_extractions.py`
   - Compares direct top-model extraction vs `/lims/extract` output and records comparison artifacts.

4. **Documentation updates created**
   - `docs/project_p/LIMS-016-extraction-optimization-llamacloud-v2-alignment.md`
   - `docs/issues/ISSUE-038-lims-chat-missing-grounded-context-and-provenance.md`

### Known Constraint Found

- LlamaExtract provider constraint: `confidence_scores` is not supported with `openai-gpt-5` / `openai-gpt-5-mini` for extraction model.
- Action already taken: added preflight validation in extractor and updated recommended profile accordingly.

---

## Scope of This Task

### A) Input Parse Validation (Ground Truth vs App Parse)

- Use the real 20-page PDF (LAB-2499 source file) through app extraction pipeline.
- Compare parsed structure/content against `AND_ACS_DYE-LAB-2499_pdf.md`.
- Focus on:
  - section/header detection
  - critical equations/procedures
  - decision/criteria statements
  - table fidelity (rows/conditions)

### B) Output MDA Validation (Ground Truth vs App MDA)

- Compare app-generated MDA (analysis/components/calc variables/calculations) against `AND_ACS_DYE-LAB-2499_xlsx.md`.
- Focus on:
  - 3-analysis pattern (`AND_ACS_DYE`, `_CTL`, `_META`)
  - component result-type correctness (`N/K/L/T/D`)
  - calc variable references (`C` vs `A`, scope/function)
  - source code / calculation semantics

### C) Traceability & Monitoring Validation

- Confirm each major step is traceable:
  - extract/classify/augment/merge/review/chat
- Validate presence of:
  - `trace_id` / `trace_url` from API responses
  - extraction trace metadata (provider, run id, config used)
  - provenance payload for MDA fields
  - persisted comparison artifacts for audit/debug
- Confirm Langfuse flush and visibility of traces for run timeline debugging.

---

## Execution Protocol (Important)

- **Do not run comparisons automatically.**
- Run only when user explicitly signals readiness and confirms required source files are available.
- Use deterministic run labels and write artifacts per run to an isolated output directory.

---

## Suggested Run Plan

1. **Preflight**
   - health check API
   - verify env keys (`LIMS_LLAMAEXTRACT_API_KEY`, Langfuse keys)
   - verify ground-truth files exist

2. **Direct extraction baseline (top model profile)**
   - premium extraction profile
   - compatible metadata flags (no unsupported combinations)

3. **App pipeline extraction**
   - `/lims/extract` same PDF
   - capture `trace_id`, `trace_url`, `extraction_trace`, `mda_template`

4. **Compare artifacts**
   - input parse comparison against ground-truth input md
   - output MDA comparison against ground-truth xlsx md

5. **Publish evidence package**
   - raw outputs
   - comparison metrics
   - mismatch inventory
   - Langfuse trace links

---

## Deliverables

- Run folder with:
   - direct extraction result JSON (also copied to `demo_data/llama_cloud_results/`)
   - app extraction result JSON
  - comparison JSON/markdown report
  - mismatch tables (input + output)
   - trace references (Langfuse URLs, copied to `demo_data/langfuse/`)
- Final summary with:
  - pass/fail status by category
  - highest-impact mismatch root causes
  - prioritized remediation list

---

## Acceptance Criteria

- [ ] Input parse quality report generated against `AND_ACS_DYE-LAB-2499_pdf.md`
- [ ] Output MDA quality report generated against `AND_ACS_DYE-LAB-2499_xlsx.md`
- [ ] End-to-end traces visible and linkable for the run
- [ ] Provenance evidence present for MDA fields used in decisions
- [ ] Reproducible artifact bundle created for debugging/audit
- [ ] Explicit list of unresolved gaps with recommended fixes

---

## Risks / Notes

- Ground-truth markdown itself may contain parser artifacts (HTML fragments, mixed formatting); matching logic should normalize before scoring.
- Model/provider constraints (e.g., GPT-5 confidence-score limitation) must be respected in config profiles.
- This task is validation-oriented; no fallback logic allowed and no hidden assumptions in scoring.

# L18 Strict Rerun Checklist (2026-02-23)

**Status:** Archived — superseded by [LIMS-020](../LIMS-020-template-locked-merge-quality-fix.md)

> This document is archived for audit traceability. The current rerun protocol is consolidated in
> [LIMS-020-template-locked-merge-quality-fix.md](../LIMS-020-template-locked-merge-quality-fix.md),
> section "Rerun Protocol".

---

## Purpose
Run L18 end-to-end validation in a reproducible, audit-clean way and produce a canonical evidence package tied to one run only.

---

## 0) Preconditions (must be true before running)
- API is reachable and healthy.
- Required environment keys are loaded (LlamaExtract + Langfuse + model keys).
- Source PDF exists and is the intended test artifact.
- Ground-truth files exist:
  - demo_data/testing_data_ground_truth/AND_ACS_DYE-LAB-2499_pdf.md
  - demo_data/testing_data_ground_truth/AND_ACS_DYE-LAB-2499_xlsx.md
- No parallel L18 run writing to the same output directory.

---

## 1) Start services and verify health
Use your normal stack for AI4LIMS, then verify:

curl http://localhost:8080/health

Expected:
- HTTP 200
- service status healthy

If health check fails, stop and fix infra before proceeding.

---

## 2) Create isolated run workspace
Use this base output root (already used in project):
- demo_data/e2e_outputs

The compare harness creates a unique UTC run folder automatically (run_id format like YYYYMMDDTHHMMSSZ).

Rule:
- Do not reuse or overwrite a previous run folder.

---

## 3) Execute canonical compare harness (single command)
From repo root:

python scripts/compare_lims_extractions.py \
  --pdf demo_data/data/AND_ACS_DYE-LAB-2499.pdf \
  --base-url http://localhost:8080 \
  --out-dir demo_data/e2e_outputs \
  --llama-cloud-results-dir demo_data/llama_cloud_results \
  --langfuse-traces-dir demo_data/langfuse

Optional (only if a structured JSON GT file exists):

python scripts/compare_lims_extractions.py \
  --pdf demo_data/data/AND_ACS_DYE-LAB-2499.pdf \
  --base-url http://localhost:8080 \
  --out-dir demo_data/e2e_outputs \
  --llama-cloud-results-dir demo_data/llama_cloud_results \
  --langfuse-traces-dir demo_data/langfuse \
  --ground-truth-json <path-to-ground-truth-json>

Capture stdout JSON from this command; it includes run_id and run_dir.

---

## 4) Mandatory artifacts (run is invalid if any missing)
Inside demo_data/e2e_outputs/<run_id>/ all of the following must exist:
- direct_result.json
- app_result.json
- comparison.json
- evidence_manifest.json
- trace_snapshot.json

Also expected side artifacts:
- demo_data/llama_cloud_results/<run_id>_direct_result.json
- demo_data/langfuse/<run_id>_trace_refs.json

---

## 5) Traceability checks
From app_result.json and manifest:
- trace_id exists
- trace_url exists (or explicit null with explanation if unavailable in environment)
- extraction trace block exists with:
  - provider
  - run_id
  - run_status
  - duration_ms
  - extract_config

From Langfuse export evidence:
- pipeline span present
- stage spans present:
  - lims-classify
  - lims-focused-extract
  - lims-augment
  - rag-standards-query-metrics (or equivalent query span)
  - lims-merge

---

## 6) Output quality gates for this rerun
Treat rerun as FAIL if any condition below is not met:

### Structure gates
- Final MDA must not include uncontrolled extra analysis family rows for this profile.
- Placeholder calculations (SME_REQUIRED) in final output must be zero for sign-off target.

### Metric gates
- Components alias-aware precision >= 0.90
- Components alias-aware recall >= 0.98
- Calc variables alias-aware exact semantic = 1.00
- Calculations alias-aware exact semantic >= 0.95

### Reproducibility gates
- All mandatory artifacts present.
- Report metrics derived from this run's comparison.json only.
- No mixed metrics from old runs.

---

## 7) Consistency validation pass (prevent stale-metric contamination)
Before writing summary report, verify:
- Validation error count in report matches app_result/extraction payload for this run.
- Placeholder count in report matches output artifact for this run.
- Analysis count in report matches output artifact for this run.
- Any "implemented" claim is backed by present artifacts in this run.

If any mismatch is found: mark run as INVALID EVIDENCE PACKAGE.

---

## 8) Final report template (same-run only)
Create one report for this run with sections:
1. Run metadata (run_id, UTC timestamp, input hashes)
2. Input parse evaluation
3. Output MDA evaluation (strict + alias-aware)
4. Traceability verification
5. RAG effectiveness for this run (functional vs material impact)
6. Pass/fail table by acceptance criterion
7. Unresolved gaps + prioritized fixes

Mandatory references in report:
- run_dir path
- evidence_manifest.json path
- trace_snapshot.json path
- comparison.json path

---

## 9) Fast failure rules (do not continue if triggered)
Stop immediately and mark run failed if:
- API call fails or times out before artifact completion.
- Harness exits without run_id/run_dir output.
- Mandatory artifacts missing.
- comparison.json cannot be parsed.
- Traceability fields are absent and no explicit documented reason exists.

---

## 10) Recommended follow-up after rerun
- If rerun passes all gates: promote this run as canonical L18 validation evidence.
- If rerun fails: open/update issue doc with exact run_id, attach mismatch inventory from manifest, and prioritize P0 fixes before another full rerun.

---

## One-line operator checklist
- Health OK
- Single isolated run executed
- 5 mandatory run artifacts generated
- Traceability fields present
- Quality gates evaluated from same run
- Report generated from same run only
- Pass/fail declared with unresolved gaps

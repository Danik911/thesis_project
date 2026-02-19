# Task L11 — Template Library: HPLC, LOD, Titration & Identity Skeletons

**Phase:** 8b (Two-Layer Pipeline — Templates) | **Dependencies:** L10 (Foundation Models)
**Branch:** `prjoject_p_protatype`
**Estimated effort:** 3 days
**Status:** DONE (completed 2026-02-19)

## Completion Summary (2026-02-19)

All 4 MDA template skeletons implemented with full ground truth fidelity. All 163 LIMS tests pass (4 skipped = integration).

### Actual counts (ground truth verified)

| Template | Analyses | Components | CalcVars | Calculations | Ground Truth |
|----------|----------|------------|----------|--------------|--------------|
| Identity | 3 | 25 | 6 | 11 | AND_ACS_DYE |
| HPLC | 4 | 59 | 48 | 30 | AND_BCMA_CEX |
| LOD | 2 | 14 | 4 | 6 | AND_USP_LOD |
| Titration | 2 | 11 | 6 | 7 | FRE_KF_Config_w_Calcs.xlsx |

### Schema changes

- Added `HPLC`, `RM`, `KF` to `AnalysisType` enum in `mda_schema.py`
- Relaxed K-type `auto_calc` validator — K-type components now allow `auto_calc=False` (GOSUB triggers)

### Files created

| File | Purpose |
|------|---------|
| `main/src/lims/templates/identity.py` | Identity skeleton: 3 analyses, 25 components, 6 calc_vars, 11 calculations |
| `main/src/lims/templates/hplc.py` | HPLC skeleton: 4 analyses, 59 components, 48 calc_vars, 30 calculations |
| `main/src/lims/templates/lod.py` | LOD skeleton: 2 analyses, 14 components, 4 calc_vars, 6 calculations |
| `main/src/lims/templates/titration.py` | Titration skeleton: 2 analyses, 11 components, 6 calc_vars, 7 calculations |

### Files modified

| File | Change |
|------|--------|
| `main/src/lims/mda_schema.py` | Added HPLC, RM, KF to AnalysisType; relaxed K-type auto_calc validator |
| `main/src/lims/templates/__init__.py` | Added imports for all 4 template modules |
| `main/tests/lims/test_mda_schema.py` | Updated test for relaxed K-type auto_calc |
| `main/tests/lims/test_templates.py` | Full L11 test suite (45 template tests) |

---

## Handoff Update (2026-02-19)

- **Implementation readiness:** Data is prepared and usable after L10 foundation models are merged.
- **Use this corpus only:** `output/prepared_l10l15/per_document/` (4 documents).
- **Useful inputs for template calibration:** `cleaned_text.md`, `sections.json`, `tables_cleaned.json` in each per-document folder.
- **Ground truth baseline remains:** `demo_data/*.xlsx` as stated in task objective.
- **Parsed Excel quick-reference (secondary, not canonical):** `demo_data/parced/*_xlsx.md` and `demo_data/parced/*_Config_w_Calcs.md` are helpful for rapid component/calc pattern review; always verify final skeleton values against original `demo_data/*.xlsx`.
- **Coverage note for 4 target types:** parsed files currently provide strong exemplars for Identity (`AND_ACS_DYE`), HPLC (`AND_BCMA_CEX`), and LOD (`AND_USP_LOD`); for Titration use `demo_data/FRE_KF_Config_w_Calcs.xlsx` as primary truth even if parsed markdown is not present.
- **Parsed SOP linkage available:** source standards are parsed in `output/sop_parsed/` and transformed in `output/prepared_l10l15/` for convention sanity-checks during template design.
- **Known data caveat:** Ignore `output/prepared/` (legacy duplicate run); use `output/prepared_l10l15/`.
- **Next agent action:** Build template skeletons first from XLSX truth, then sanity-check against extracted SOP conventions in prepared corpus.

---

## Objective

Create curated MDA template skeletons for 4 test types (HPLC, LOD, Titration, Identity) based on analysis of ground truth XLSX files from `demo_data/`. Each template defines the ~46% of components that come from LIMS conventions rather than the PDF, marking variable slots for focused extraction.

---

## Context

Analysis of 18 demo XLSX files reveals consistent patterns per test type:
- **HPLC** (AND_BCMA_CEX, FRE_BOSU): 40+ components, 3-analysis pattern (primary + CTL + META)
- **LOD** (AND_USP_LOD): Simpler, fewer calculations, loss-on-drying specific
- **Titration** (FRE_KF_USP): Karl Fischer water content, specific equipment
- **Identity** (AND_ACS_DYE): Current ground truth, 25 components across 3 analyses

---

## Gate Criteria

- [x] All 4 templates registered in TemplateLibrary
- [x] `TemplateLibrary.get_template_for_type(TestType.HPLC)` returns HPLCTemplate instance
- [x] Each template's `to_mda_template()` produces a valid MDATemplate (passes Pydantic validation)
- [x] Identity template matches AND_ACS_DYE ground truth structure (3 analyses, 25 components)
- [x] HPLC template has 40+ template components
- [x] Each template clearly marks variable vs fixed fields
- [x] All existing LIMS tests pass

# LIMS-006: L11 Template Library — HPLC, LOD, Titration & Identity Skeletons

**Date:** 2026-02-19
**Task:** L11
**Status:** Complete

## Summary

Implemented 4 curated MDA template skeletons with full ground truth fidelity for the AI4LIMS two-layer pipeline. Each template defines the ~46% of components that come from LIMS conventions (not the PDF), marking variable slots for focused extraction.

## What Was Done

### Schema Modifications (`main/src/lims/mda_schema.py`)
- Added 3 new `AnalysisType` enum values: `HPLC`, `RM`, `KF`
- Relaxed K-type `auto_calc` validator — K-type components now allow `auto_calc=False` (GOSUB triggers rather than auto-calc)

### Templates Created

| Template | File | Analyses | Components | CalcVars | Calcs | Ground Truth |
|----------|------|----------|------------|----------|-------|--------------|
| Identity | `main/src/lims/templates/identity.py` | 3 | 25 | 6 | 11 | AND_ACS_DYE |
| HPLC | `main/src/lims/templates/hplc.py` | 4 | 59 | 48 | 30 | AND_BCMA_CEX |
| LOD | `main/src/lims/templates/lod.py` | 2 | 14 | 4 | 6 | AND_USP_LOD |
| Titration | `main/src/lims/templates/titration.py` | 2 | 11 | 6 | 7 | FRE_KF XLSX |

### Registry Updated (`main/src/lims/templates/__init__.py`)
All 4 template modules imported to trigger `@TemplateLibrary.register` decorators.

### Tests (`main/tests/lims/test_templates.py`)
45 template tests covering registration, MDA validity, count assertions, analysis types, variable/fixed field classification. All 163 LIMS tests pass.

## Files Created

| File | Purpose |
|------|---------|
| `main/src/lims/templates/identity.py` | Identity template (AND_ACS_DYE) |
| `main/src/lims/templates/hplc.py` | HPLC template (AND_BCMA_CEX) |
| `main/src/lims/templates/lod.py` | LOD template (AND_USP_LOD) |
| `main/src/lims/templates/titration.py` | Titration template (FRE_KF) |

## Files Modified

| File | Change |
|------|--------|
| `main/src/lims/mda_schema.py` | Added HPLC, RM, KF enum values; relaxed K-type validator |
| `main/src/lims/templates/__init__.py` | Added 4 template imports |
| `main/tests/lims/test_mda_schema.py` | Updated K-type auto_calc test |
| `main/tests/lims/test_templates.py` | Full L11 test suite |

## Issues Encountered

1. **Plan vs ground truth discrepancies:** Plan listed 44 HPLC calc_vars (actual: 48), 28 HPLC calculations (actual: 30), 10 Identity calculations (actual: 11). All resolved by using ground truth counts.
2. **KF analysis type missing from plan:** Plan only mentioned adding HPLC and RM to AnalysisType, but FRE_KF XLSX required KF type too.
3. **FRE_KF has no parsed markdown:** Had to parse XLSX directly with openpyxl to extract titration structure.

## Useful Commands

```bash
# Run template tests
uv run pytest main/tests/lims/test_templates.py -v

# Run all LIMS tests
uv run pytest main/tests/lims/ -v

# Smoke test all 4 templates
uv run python -c "
from main.src.lims.templates import TemplateLibrary
from main.src.lims.test_type import TestType
for tt in [TestType.IDENTITY, TestType.HPLC, TestType.LOD, TestType.TITRATION]:
    tpl = TemplateLibrary.get_template_for_type(tt)
    mda = tpl.to_mda_template()
    print(f'{tt.value}: {len(mda.analyses)}a, {len(mda.components)}c, {len(mda.calc_variables)}cv, {len(mda.calculations)}calc')
"
```

## Next Steps

- **L12:** Classifier — hybrid test-type detection (ready, depends on L10 not L11)
- **L13:** Standards RAG augmentation (uses templates from L11)
- **L14:** Pipeline core — extractor/merger/orchestrator (uses templates from L11)

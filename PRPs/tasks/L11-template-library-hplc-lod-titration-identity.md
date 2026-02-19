# Task L11 — Template Library: HPLC, LOD, Titration & Identity Skeletons

**Phase:** 8b (Two-Layer Pipeline — Templates) | **Dependencies:** L10 (Foundation Models)
**Branch:** `prjoject_p_protatype`
**Estimated effort:** 3 days
**Status:** NOT STARTED

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

## Files to Create

| File | Purpose |
|------|---------|
| `main/src/lims/templates/hplc.py` | HPLC skeleton: 3-analysis pattern, column/system suitability components, gradient/isocratic methods |
| `main/src/lims/templates/lod.py` | LOD skeleton: drying conditions, weight measurements, % loss calculation |
| `main/src/lims/templates/titration.py` | Titration skeleton: KF-specific equipment, sample prep, endpoint detection |
| `main/src/lims/templates/identity.py` | Identity skeleton: AND_ACS_DYE ground truth as reference template |

## Files to Modify

| File | Change | Risk |
|------|--------|------|
| `main/src/lims/templates/__init__.py` | Import and register all 4 template types | LOW |

---

## Implementation Details

### 1. identity.py — Identity Template (Reference Implementation)

Based on AND_ACS_DYE ground truth (25 components, 3 analyses). This serves as the reference implementation for all other templates.

```python
"""Identity test MDA template skeleton.

Ground truth: AND_ACS_DYE (ACS Dye-Binding Identity Test, LAB-2499)
3 analyses, 25 components.

Components marked is_variable=True must be extracted from the PDF.
Components marked is_variable=False are LIMS conventions.

GAMP-5 Category 5: Custom pharmaceutical software component.
NO FALLBACK LOGIC.
"""

from main.src.lims.mda_schema import (
    Analysis, AnalysisType, Component, ResultType,
    CalcVariable, Calculation, MDATemplate,
)
from main.src.lims.templates import TemplateLibrary
from main.src.lims.templates.base import TemplateComponent, TestTypeTemplate
from main.src.lims.test_type import TestType


@TemplateLibrary.register(TestType.IDENTITY)
class IdentityTemplate(TestTypeTemplate):
    """Identity test template based on AND_ACS_DYE ground truth.

    Structure:
    - Primary analysis (ID type, 9 components)
    - CTL analysis (QC_SAMPLES type, 7 components)
    - META analysis (QC_SAMPLES type, 9 components)
    """
    test_type = TestType.IDENTITY

    def get_components(self) -> list[TemplateComponent]:
        """Return all 25 template components across 3 analyses.

        Fixed (TEMPLATE) components: result_type, auto_calc, active, reportable,
            order_number, analysis_type — these follow LIMS conventions.
        Variable (EXTRACTED) components: component_name, units, minimum, maximum,
            places, list_key — these come from the specific test method PDF.
        """
        components = []

        # --- Primary Analysis (ID) ---
        # Structure: 9 components typical for identity tests
        components.extend([
            TemplateComponent(sheet="analyses", field_path="analyses[0].analysis_type", value="ID", is_variable=False),
            TemplateComponent(sheet="analyses", field_path="analyses[0].name", value=None, is_variable=True),
            TemplateComponent(sheet="components", field_path="components[0].result_type", value="L", is_variable=False),
            TemplateComponent(sheet="components", field_path="components[0].component_name", value=None, is_variable=True),
            TemplateComponent(sheet="components", field_path="components[0].active", value=True, is_variable=False),
        ])

        # --- CTL Analysis (QC_SAMPLES) ---
        components.extend([
            TemplateComponent(sheet="analyses", field_path="analyses[1].analysis_type", value="QC_SAMPLES", is_variable=False),
            TemplateComponent(sheet="analyses", field_path="analyses[1].name", value=None, is_variable=True),
        ])

        # --- META Analysis (QC_SAMPLES) ---
        components.extend([
            TemplateComponent(sheet="analyses", field_path="analyses[2].analysis_type", value="QC_SAMPLES", is_variable=False),
            TemplateComponent(sheet="analyses", field_path="analyses[2].name", value=None, is_variable=True),
        ])

        return components

    def to_mda_template(self) -> MDATemplate:
        """Build an MDATemplate skeleton from the identity template.

        Variable fields use placeholder values that will be overwritten
        by PDF extraction in the augmentation stage.
        """
        # Implementation: build MDATemplate with fixed values populated
        # and placeholder values for variable fields
        ...
```

### 2. hplc.py — HPLC Template

Based on analysis of AND_BCMA_CEX and FRE_BOSU XLSX files. HPLC templates are the most complex, with 40+ components.

```python
"""HPLC test MDA template skeleton.

Ground truth references: AND_BCMA_CEX, FRE_BOSU
3-analysis pattern: Primary (ASSAY) + CTL (QC_SAMPLES) + META (QC_SAMPLES)
40+ components including system suitability, injection sequences, peak identification.

GAMP-5 Category 5: Custom pharmaceutical software component.
NO FALLBACK LOGIC.
"""

from main.src.lims.templates import TemplateLibrary
from main.src.lims.templates.base import TemplateComponent, TestTypeTemplate
from main.src.lims.test_type import TestType


@TemplateLibrary.register(TestType.HPLC)
class HPLCTemplate(TestTypeTemplate):
    """HPLC test template.

    Key structural patterns:
    - System suitability components (RSD, tailing factor, plate count)
    - Column/instrument components (column ID, detector wavelength)
    - Sample prep components (dilution, weight, volume)
    - Result calculation components (assay %, area %)
    - Injection sequence components (sample, blank, standard, system suit)
    """
    test_type = TestType.HPLC

    def get_components(self) -> list[TemplateComponent]:
        """Return 40+ template components for HPLC methods.

        Fixed components: system suitability structure, injection order,
            calculation patterns (K-type auto_calc, FORMULA calculations).
        Variable components: column details, mobile phase composition,
            gradient program, wavelength, acceptance criteria.
        """
        components = []

        # --- Primary Analysis (ASSAY) ---
        # System suitability block (fixed structure, variable acceptance criteria)
        components.extend([
            TemplateComponent(sheet="analyses", field_path="analyses[0].analysis_type", value="ASSAY", is_variable=False),
            TemplateComponent(sheet="analyses", field_path="analyses[0].name", value=None, is_variable=True),
            # System suitability components
            TemplateComponent(sheet="components", field_path="components[0].result_type", value="N", is_variable=False),
            TemplateComponent(sheet="components", field_path="components[0].component_name", value="RSD_SYSTEM_SUITABILITY", is_variable=False),
            TemplateComponent(sheet="components", field_path="components[0].uses_instrument", value=True, is_variable=False),
            TemplateComponent(sheet="components", field_path="components[0].maximum", value=None, is_variable=True),
            # Column components
            TemplateComponent(sheet="components", field_path="components[1].result_type", value="T", is_variable=False),
            TemplateComponent(sheet="components", field_path="components[1].component_name", value="COLUMN_ID", is_variable=False),
            # Wavelength
            TemplateComponent(sheet="components", field_path="components[2].result_type", value="N", is_variable=False),
            TemplateComponent(sheet="components", field_path="components[2].component_name", value="WAVELENGTH", is_variable=False),
            TemplateComponent(sheet="components", field_path="components[2].units", value="nm", is_variable=False),
            TemplateComponent(sheet="components", field_path="components[2].value", value=None, is_variable=True),
        ])

        # Injection sequence, peak areas, assay calculations (K-type)
        components.extend([
            TemplateComponent(sheet="components", field_path="components[3].result_type", value="K", is_variable=False),
            TemplateComponent(sheet="components", field_path="components[3].auto_calc", value=True, is_variable=False),
            TemplateComponent(sheet="components", field_path="components[3].component_name", value="ASSAY_RESULT", is_variable=False),
        ])

        # --- CTL and META analyses follow same pattern as Identity ---
        components.extend([
            TemplateComponent(sheet="analyses", field_path="analyses[1].analysis_type", value="QC_SAMPLES", is_variable=False),
            TemplateComponent(sheet="analyses", field_path="analyses[2].analysis_type", value="QC_SAMPLES", is_variable=False),
        ])

        return components

    def to_mda_template(self):
        """Build HPLC MDATemplate skeleton."""
        ...
```

### 3. lod.py — Loss on Drying Template

Based on AND_USP_LOD. Simpler structure than HPLC.

```python
"""Loss on Drying (LOD) test MDA template skeleton.

Ground truth reference: AND_USP_LOD
Simpler structure: drying temp, duration, weight before/after, % loss.

GAMP-5 Category 5: Custom pharmaceutical software component.
NO FALLBACK LOGIC.
"""

from main.src.lims.templates import TemplateLibrary
from main.src.lims.templates.base import TemplateComponent, TestTypeTemplate
from main.src.lims.test_type import TestType


@TemplateLibrary.register(TestType.LOD)
class LODTemplate(TestTypeTemplate):
    """Loss on Drying template.

    Key structural patterns:
    - Drying conditions (temperature, duration) — variable from PDF
    - Weight measurements (before, after) — N-type numeric
    - % Loss calculation — K-type auto_calc
    - USP <731> reference — fixed LIMS convention
    """
    test_type = TestType.LOD

    def get_components(self) -> list[TemplateComponent]:
        """Return LOD template components.

        Fixed: result_type patterns, calculation structure, USP reference.
        Variable: drying temperature, drying time, acceptance criteria.
        """
        components = [
            # Primary analysis
            TemplateComponent(sheet="analyses", field_path="analyses[0].analysis_type", value="ASSAY", is_variable=False),
            TemplateComponent(sheet="analyses", field_path="analyses[0].name", value=None, is_variable=True),
            # Drying conditions (variable)
            TemplateComponent(sheet="components", field_path="components[0].component_name", value="DRYING_TEMPERATURE", is_variable=False),
            TemplateComponent(sheet="components", field_path="components[0].result_type", value="N", is_variable=False),
            TemplateComponent(sheet="components", field_path="components[0].units", value="deg C", is_variable=False),
            TemplateComponent(sheet="components", field_path="components[0].value", value=None, is_variable=True),
            # Drying duration
            TemplateComponent(sheet="components", field_path="components[1].component_name", value="DRYING_TIME", is_variable=False),
            TemplateComponent(sheet="components", field_path="components[1].result_type", value="N", is_variable=False),
            TemplateComponent(sheet="components", field_path="components[1].units", value="hours", is_variable=False),
            TemplateComponent(sheet="components", field_path="components[1].value", value=None, is_variable=True),
            # Weight before
            TemplateComponent(sheet="components", field_path="components[2].component_name", value="WEIGHT_BEFORE", is_variable=False),
            TemplateComponent(sheet="components", field_path="components[2].result_type", value="N", is_variable=False),
            TemplateComponent(sheet="components", field_path="components[2].units", value="g", is_variable=False),
            # Weight after
            TemplateComponent(sheet="components", field_path="components[3].component_name", value="WEIGHT_AFTER", is_variable=False),
            TemplateComponent(sheet="components", field_path="components[3].result_type", value="N", is_variable=False),
            TemplateComponent(sheet="components", field_path="components[3].units", value="g", is_variable=False),
            # % Loss (calculated)
            TemplateComponent(sheet="components", field_path="components[4].component_name", value="PERCENT_LOSS", is_variable=False),
            TemplateComponent(sheet="components", field_path="components[4].result_type", value="K", is_variable=False),
            TemplateComponent(sheet="components", field_path="components[4].auto_calc", value=True, is_variable=False),
            TemplateComponent(sheet="components", field_path="components[4].units", value="%", is_variable=False),
            TemplateComponent(sheet="components", field_path="components[4].maximum", value=None, is_variable=True),
        ]
        return components

    def to_mda_template(self):
        """Build LOD MDATemplate skeleton."""
        ...
```

### 4. titration.py — Titration Template

Based on FRE_KF_USP (Karl Fischer). KF-specific equipment, endpoint detection.

```python
"""Titration (Karl Fischer) test MDA template skeleton.

Ground truth reference: FRE_KF_USP
KF-specific: titrant, sample weight, endpoint volume, water content %.

GAMP-5 Category 5: Custom pharmaceutical software component.
NO FALLBACK LOGIC.
"""

from main.src.lims.templates import TemplateLibrary
from main.src.lims.templates.base import TemplateComponent, TestTypeTemplate
from main.src.lims.test_type import TestType


@TemplateLibrary.register(TestType.TITRATION)
class TitrationTemplate(TestTypeTemplate):
    """Karl Fischer Titration template.

    Key structural patterns:
    - Instrument components (titrator ID, buret volume)
    - Titrant standardization (KF reagent, factor)
    - Sample prep (weight, solvent volume)
    - Endpoint detection (drift, volume consumed)
    - Water content calculation (K-type, mg water / g sample)
    """
    test_type = TestType.TITRATION

    def get_components(self) -> list[TemplateComponent]:
        """Return KF titration template components.

        Fixed: instrument structure, calculation pattern, result types.
        Variable: sample weight ranges, acceptance criteria, titrant details.
        """
        components = [
            # Primary analysis
            TemplateComponent(sheet="analyses", field_path="analyses[0].analysis_type", value="ASSAY", is_variable=False),
            TemplateComponent(sheet="analyses", field_path="analyses[0].name", value=None, is_variable=True),
            # Titrator instrument
            TemplateComponent(sheet="components", field_path="components[0].component_name", value="TITRATOR_ID", is_variable=False),
            TemplateComponent(sheet="components", field_path="components[0].result_type", value="T", is_variable=False),
            TemplateComponent(sheet="components", field_path="components[0].uses_instrument", value=True, is_variable=False),
            # Sample weight
            TemplateComponent(sheet="components", field_path="components[1].component_name", value="SAMPLE_WEIGHT", is_variable=False),
            TemplateComponent(sheet="components", field_path="components[1].result_type", value="N", is_variable=False),
            TemplateComponent(sheet="components", field_path="components[1].units", value="g", is_variable=False),
            # Volume consumed
            TemplateComponent(sheet="components", field_path="components[2].component_name", value="VOLUME_CONSUMED", is_variable=False),
            TemplateComponent(sheet="components", field_path="components[2].result_type", value="N", is_variable=False),
            TemplateComponent(sheet="components", field_path="components[2].units", value="mL", is_variable=False),
            # KF factor
            TemplateComponent(sheet="components", field_path="components[3].component_name", value="KF_FACTOR", is_variable=False),
            TemplateComponent(sheet="components", field_path="components[3].result_type", value="N", is_variable=False),
            TemplateComponent(sheet="components", field_path="components[3].units", value="mg/mL", is_variable=False),
            TemplateComponent(sheet="components", field_path="components[3].value", value=None, is_variable=True),
            # Water content (calculated)
            TemplateComponent(sheet="components", field_path="components[4].component_name", value="WATER_CONTENT", is_variable=False),
            TemplateComponent(sheet="components", field_path="components[4].result_type", value="K", is_variable=False),
            TemplateComponent(sheet="components", field_path="components[4].auto_calc", value=True, is_variable=False),
            TemplateComponent(sheet="components", field_path="components[4].units", value="%", is_variable=False),
            TemplateComponent(sheet="components", field_path="components[4].maximum", value=None, is_variable=True),
        ]
        return components

    def to_mda_template(self):
        """Build Titration MDATemplate skeleton."""
        ...
```

### 5. templates/__init__.py — Import and Register All Templates

After L11 is complete, the `__init__.py` should import all template modules to trigger registration:

```python
"""Template library registry for test-type templates."""

from __future__ import annotations

from main.src.lims.test_type import TestType
from main.src.lims.templates.base import TestTypeTemplate


class TemplateLibrary:
    """Registry for test-type-specific MDA templates."""

    _registry: dict[TestType, type[TestTypeTemplate]] = {}

    @classmethod
    def register(cls, test_type: TestType):
        def decorator(template_cls: type[TestTypeTemplate]):
            cls._registry[test_type] = template_cls
            return template_cls
        return decorator

    @classmethod
    def get_template_for_type(cls, test_type: TestType) -> TestTypeTemplate:
        if test_type not in cls._registry:
            raise ValueError(
                f"No template registered for test type '{test_type.value}'. "
                f"Available: {sorted(t.value for t in cls._registry)}"
            )
        return cls._registry[test_type]()

    @classmethod
    def available_types(cls) -> list[TestType]:
        return sorted(cls._registry.keys(), key=lambda t: t.value)


# Import template modules to trigger @TemplateLibrary.register decorators
from main.src.lims.templates import hplc  # noqa: E402, F401
from main.src.lims.templates import lod  # noqa: E402, F401
from main.src.lims.templates import titration  # noqa: E402, F401
from main.src.lims.templates import identity  # noqa: E402, F401
```

---

## Testing Strategy

```bash
# Template instantiation tests
uv run pytest main/tests/lims/test_templates.py -v

# Verify templates produce valid MDATemplate objects
# Each template's to_mda_template() must pass MDATemplate.validate_cross_sheet_integrity()

# Verify all existing tests still pass
uv run pytest main/tests/lims/ -v
```

---

## Gate Criteria

- [ ] All 4 templates registered in TemplateLibrary
- [ ] `TemplateLibrary.get_template_for_type(TestType.HPLC)` returns HPLCTemplate instance
- [ ] Each template's `to_mda_template()` produces a valid MDATemplate (passes Pydantic validation)
- [ ] Identity template matches AND_ACS_DYE ground truth structure (3 analyses, 25 components)
- [ ] HPLC template has 40+ template components
- [ ] Each template clearly marks variable vs fixed fields
- [ ] All existing LIMS tests pass

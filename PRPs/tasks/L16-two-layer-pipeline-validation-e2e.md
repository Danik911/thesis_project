# Task L16 — Validation: Two-Layer Pipeline E2E Tests & Backward Compatibility

**Phase:** 8g (Two-Layer Pipeline — Validation) | **Dependencies:** L14, L15
**Branch:** `prjoject_p_protatype`
**Estimated effort:** 2 days
**Status:** NOT STARTED

---

## Objective

Comprehensive validation of the two-layer pipeline: unit tests for all new modules, integration tests for the full pipeline, backward compatibility verification (AND_ACS_DYE still works), and coverage comparison against ground truth XLSX files.

---

## Files to Create

| File | Purpose |
|------|---------|
| `main/tests/lims/test_provenance.py` | Provenance model unit tests: ComponentSource, FieldProvenance, ProvenanceMap |
| `main/tests/lims/test_templates.py` | Template instantiation, registration, MDATemplate validation per test type |
| `main/tests/lims/test_classifier.py` | Classification accuracy against demo PDF filenames and content |
| `main/tests/lims/test_merger.py` | Merge logic, conflict detection, provenance tracking |
| `main/tests/lims/test_pipeline.py` | Full pipeline integration tests per test type |
| `main/tests/lims/test_standards_loader.py` | Standards RAG seeding and querying |

---

## Implementation Details

### 1. test_provenance.py

```python
"""Tests for provenance tracking models."""

import pytest
from main.src.lims.provenance import (
    ComponentSource, FieldProvenance, ProvenanceMap,
)


class TestComponentSource:
    def test_all_sources_exist(self):
        assert len(ComponentSource) == 5

    def test_source_values(self):
        assert ComponentSource.TEMPLATE.value == "TEMPLATE"
        assert ComponentSource.EXTRACTED.value == "EXTRACTED"
        assert ComponentSource.INFERRED.value == "INFERRED"
        assert ComponentSource.SME_REQUIRED.value == "SME_REQUIRED"
        assert ComponentSource.SME_MODIFIED.value == "SME_MODIFIED"


class TestFieldProvenance:
    def test_confidence_bounds(self):
        # Valid
        fp = FieldProvenance(source=ComponentSource.TEMPLATE, confidence=0.95)
        assert fp.confidence == 0.95

        # Invalid
        with pytest.raises(ValueError):
            FieldProvenance(source=ComponentSource.TEMPLATE, confidence=1.5)


class TestProvenanceMap:
    def test_set_and_get(self):
        pm = ProvenanceMap()
        pm.set_provenance("analyses[0].name", ComponentSource.TEMPLATE, 1.0, "ground truth")
        fp = pm.get_provenance("analyses[0].name")
        assert fp is not None
        assert fp.source == ComponentSource.TEMPLATE

    def test_summary_counts(self):
        pm = ProvenanceMap()
        pm.set_provenance("a", ComponentSource.TEMPLATE, 1.0)
        pm.set_provenance("b", ComponentSource.TEMPLATE, 1.0)
        pm.set_provenance("c", ComponentSource.EXTRACTED, 0.9)
        summary = pm.summary()
        assert summary["TEMPLATE"] == 2
        assert summary["EXTRACTED"] == 1
```

### 2. test_templates.py

```python
"""Tests for template library and test-type templates."""

import pytest
from main.src.lims.test_type import TestType
from main.src.lims.templates import TemplateLibrary
from main.src.lims.mda_schema import MDATemplate


class TestTemplateLibrary:
    def test_all_types_registered(self):
        available = TemplateLibrary.available_types()
        assert TestType.HPLC in available
        assert TestType.LOD in available
        assert TestType.TITRATION in available
        assert TestType.IDENTITY in available

    def test_get_unknown_type_raises(self):
        with pytest.raises(ValueError, match="No template registered"):
            TemplateLibrary.get_template_for_type(TestType.OTHER)


class TestIdentityTemplate:
    def test_to_mda_template_valid(self):
        template = TemplateLibrary.get_template_for_type(TestType.IDENTITY)
        mda = template.to_mda_template()
        assert isinstance(mda, MDATemplate)
        assert len(mda.analyses) == 3  # Primary + CTL + META
        assert len(mda.components) == 25


class TestHPLCTemplate:
    def test_to_mda_template_valid(self):
        template = TemplateLibrary.get_template_for_type(TestType.HPLC)
        mda = template.to_mda_template()
        assert isinstance(mda, MDATemplate)
        assert len(template.get_components()) >= 40
```

### 3. test_classifier.py

```python
"""Tests for hybrid test type classifier."""

import pytest
from main.src.lims.classifier import TestTypeClassifier
from main.src.lims.test_type import TestType


DEMO_FILES = {
    "AND_ACS_DYE-LAB-2499.pdf": TestType.IDENTITY,
    "AND_BCMA_CEX-LAB-1234.pdf": TestType.HPLC,
    "AND_USP_LOD-LAB-5678.pdf": TestType.LOD,
    "FRE_KF_USP-LAB-9012.pdf": TestType.TITRATION,
}


class TestClassifierFilename:
    def test_known_demo_files(self):
        classifier = TestTypeClassifier()
        for filename, expected in DEMO_FILES.items():
            result = classifier.classify("", filename)
            assert result.test_type == expected, f"Failed for {filename}"


class TestClassifierKeywords:
    def test_hplc_keywords(self):
        classifier = TestTypeClassifier()
        text = "High Performance Liquid Chromatography mobile phase gradient"
        result = classifier.classify(text)
        assert result.test_type == TestType.HPLC
```

### 4. test_merger.py

```python
"""Tests for merge logic and conflict detection."""

import pytest
from main.src.lims.merger import merge_layers, MergeConflict
from main.src.lims.provenance import ComponentSource


class TestMerge:
    def test_template_values_preserved(self):
        # Template provides base, extracted fills variables
        ...

    def test_conflict_detected(self):
        # Template says units="mg", extraction says units="g"
        ...

    def test_provenance_complete(self):
        # Every field in result has provenance
        ...
```

### 5. test_pipeline.py

```python
"""Integration tests for the two-layer pipeline."""

import pytest


@pytest.mark.integration
class TestTwoLayerPipeline:
    def test_identity_backward_compat(self):
        """AND_ACS_DYE still works through identity template path."""
        ...

    def test_other_type_single_layer_fallback(self):
        """Unknown test type falls back to single-layer pipeline."""
        ...
```

---

## Testing Strategy

```bash
# All new tests
uv run pytest main/tests/lims/test_provenance.py -v
uv run pytest main/tests/lims/test_templates.py -v
uv run pytest main/tests/lims/test_classifier.py -v
uv run pytest main/tests/lims/test_merger.py -v
uv run pytest main/tests/lims/test_pipeline.py -v
uv run pytest main/tests/lims/test_standards_loader.py -v

# Full suite (verify backward compat)
uv run pytest main/tests/lims/ -v
```

---

## Gate Criteria

- [ ] All provenance model tests pass
- [ ] All template instantiation tests pass (4 types produce valid MDATemplates)
- [ ] Classifier >90% accuracy on demo filenames
- [ ] Merge produces complete MDA with full provenance
- [ ] Merge detects conflicts correctly
- [ ] AND_ACS_DYE backward compatibility verified
- [ ] TestType.OTHER falls back to single-layer pipeline
- [ ] All 96+ existing LIMS tests still pass
- [ ] No regressions in thesis test suite

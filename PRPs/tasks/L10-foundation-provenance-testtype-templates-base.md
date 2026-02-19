# Task L10 — Foundation Models: Provenance, TestType & Template Base Classes

**Phase:** 8a (Two-Layer Pipeline — Foundation) | **Dependencies:** L7 (done)
**Branch:** `prjoject_p_protatype`
**Estimated effort:** 2 days
**Status:** NOT STARTED (READY TO START — handoff updated 2026-02-19)

## Handoff Update (2026-02-19)

- **Implementation readiness:** Ready now. L10 is code-only and does not require additional data prep.
- **Canonical prepared corpus for downstream tasks:** `output/prepared_l10l15/`.
- **Reference manifests:** `output/sop_parsed/manifest.json`, `output/prepared_l10l15/manifest.json`.
- **Known data caveat (downstream):** `output/prepared/manifest.json` is legacy and includes duplicate ingestion; do **not** use it for L10-L16 execution.
- **Next agent action:** Implement files in this task exactly as specified, then run LIMS unit tests before moving to L11.

---

## Objective

Create the foundational data models for the two-layer pipeline: provenance tracking (source attribution for every MDA component), test type classification enum, and template base classes. Extend existing `job_store.py` and `config.py` with new pipeline states and configuration.

---

## Context

The AI4LIMS PoC pilot revealed only ~54% of MDA components exist in the test method PDF (range: 21-96% across 18 test methods). A two-layer architecture separates curated template components (~46%) from PDF-extracted variable components. Every component must be tagged with its source (Template/Extracted/Inferred/SME Required) for auditability.

---

## Files to Create

| File | Purpose |
|------|---------|
| `main/src/lims/provenance.py` | `ComponentSource` enum (TEMPLATE, EXTRACTED, INFERRED, SME_REQUIRED, SME_MODIFIED), `FieldProvenance` model (source, confidence, source_detail, original_value), `ProvenanceMap` model (parallel structure to MDATemplate) |
| `main/src/lims/test_type.py` | `TestType` enum (HPLC, LOD, TITRATION, IDENTITY, OTHER), `ClassificationResult` model (test_type, confidence, method, evidence) |
| `main/src/lims/templates/__init__.py` | `TemplateLibrary` registry class with `get_template_for_type(test_type)` method |
| `main/src/lims/templates/base.py` | `TemplateComponent` dataclass (sheet, field, value, source=TEMPLATE), `TestTypeTemplate` base class (test_type, components, to_mda_template(), get_variable_fields()) |

## Files to Modify

| File | Change | Risk |
|------|--------|------|
| `main/src/lims/job_store.py` | Add CLASSIFYING, LOADING_TEMPLATE, AUGMENTING, MERGING to `LIMSJobStatus` enum; add `classification`, `provenance`, `conflicts`, `stage_details` fields to `LIMSJob`; update `VALID_TRANSITIONS` | LOW |
| `main/src/lims/config.py` | Add `classification_mode`, `classification_confidence_threshold`, `standards_collection`, `calculations_collection` to `LIMSConfig` | LOW |

---

## Implementation Details

### 1. provenance.py — Source Attribution Model

```python
"""Provenance tracking for MDA components in the two-layer pipeline.

Every component in the final MDA is tagged with its source for audit trail
and SME review. Parallel structure to MDATemplate — does NOT modify mda_schema.py.

GAMP-5 Category 5: Custom pharmaceutical software component.
NO FALLBACK LOGIC.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ComponentSource(str, Enum):
    """Source attribution for each MDA component value."""
    TEMPLATE = "TEMPLATE"          # From curated template skeleton
    EXTRACTED = "EXTRACTED"        # Directly from PDF via LlamaExtract
    INFERRED = "INFERRED"          # AI-filled from standards RAG
    SME_REQUIRED = "SME_REQUIRED"  # Gap — needs human input
    SME_MODIFIED = "SME_MODIFIED"  # Changed by SME during review


class FieldProvenance(BaseModel):
    """Provenance metadata for a single field value."""
    source: ComponentSource
    confidence: float = Field(ge=0.0, le=1.0)
    source_detail: str = ""        # e.g., "PDF page 3" or "CD-026972 section 4.2"
    original_value: Optional[Any] = None  # Value before SME override


class ProvenanceMap(BaseModel):
    """Parallel provenance structure for an MDATemplate.

    Keys are dot-notation paths like "analyses[0].name" or
    "components[2].result_type". Every populated field in the final
    MDA should have an entry here.
    """
    fields: dict[str, FieldProvenance] = Field(default_factory=dict)

    def set_provenance(
        self, path: str, source: ComponentSource,
        confidence: float, detail: str = ""
    ) -> None:
        self.fields[path] = FieldProvenance(
            source=source, confidence=confidence, source_detail=detail
        )

    def get_provenance(self, path: str) -> Optional[FieldProvenance]:
        return self.fields.get(path)

    def summary(self) -> dict[str, int]:
        """Count of fields per source type."""
        counts: dict[str, int] = {}
        for fp in self.fields.values():
            counts[fp.source.value] = counts.get(fp.source.value, 0) + 1
        return counts
```

### 2. test_type.py — Test Type Classification

```python
"""Test type classification for the two-layer pipeline.

Supports HPLC, LOD, Titration, Identity (first iteration).
OTHER falls back to current single-layer pipeline for backward compat.

NO FALLBACK LOGIC.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TestType(str, Enum):
    """Supported pharmaceutical test method types."""
    HPLC = "HPLC"
    LOD = "LOD"
    TITRATION = "TITRATION"
    IDENTITY = "IDENTITY"
    OTHER = "OTHER"


class ClassificationResult(BaseModel):
    """Result of test type classification."""
    test_type: TestType
    confidence: float = Field(ge=0.0, le=1.0)
    method: str  # "rules" or "llm" or "hybrid"
    evidence: list[str] = Field(default_factory=list)  # Why this classification
    pdf_filename: Optional[str] = None
```

### 3. templates/base.py — Template Base Classes

```python
"""Base classes for test-type-specific MDA template skeletons.

Templates provide the ~46% of MDA components that come from LIMS
conventions and standards, not from the PDF.

NO FALLBACK LOGIC.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from main.src.lims.mda_schema import MDATemplate
from main.src.lims.provenance import ComponentSource
from main.src.lims.test_type import TestType


@dataclass
class TemplateComponent:
    """A single pre-defined component in a template skeleton."""
    sheet: str           # "analyses", "components", "calc_variables", "calculations"
    field_path: str      # e.g., "components[0].result_type"
    value: Any
    source: ComponentSource = ComponentSource.TEMPLATE
    is_variable: bool = False  # True = must be extracted from PDF


class TestTypeTemplate:
    """Base class for test-type-specific MDA templates.

    Subclasses (HPLCTemplate, LODTemplate, etc.) define the skeleton
    components. Variable fields (is_variable=True) are placeholders
    to be filled by PDF extraction.
    """
    test_type: TestType = TestType.OTHER

    def get_components(self) -> list[TemplateComponent]:
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement get_components()"
        )

    def get_variable_fields(self) -> list[str]:
        """Return field paths that need PDF extraction."""
        return [c.field_path for c in self.get_components() if c.is_variable]

    def get_fixed_fields(self) -> list[str]:
        """Return field paths from the template skeleton."""
        return [c.field_path for c in self.get_components() if not c.is_variable]

    def to_mda_template(self) -> MDATemplate:
        """Build an MDATemplate from just the template skeleton.
        Variable fields will have placeholder/default values."""
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement to_mda_template()"
        )
```

### 4. templates/__init__.py — Template Registry

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
```

### 5. job_store.py — Extended Status Enum & Job Model

Add to `LIMSJobStatus`:
```python
CLASSIFYING = "CLASSIFYING"
LOADING_TEMPLATE = "LOADING_TEMPLATE"
AUGMENTING = "AUGMENTING"
MERGING = "MERGING"
```

Add to `LIMSJob`:
```python
classification: Optional[dict[str, Any]] = None      # ClassificationResult dict
provenance: Optional[dict[str, Any]] = None           # ProvenanceMap dict
conflicts: list[dict[str, Any]] = Field(default_factory=list)  # MergeConflict dicts
stage_details: list[dict[str, Any]] = Field(default_factory=list)  # Per-stage reasoning
```

Update `VALID_TRANSITIONS`:
```python
VALID_TRANSITIONS = {
    LIMSJobStatus.EXTRACTING: {LIMSJobStatus.CLASSIFYING, LIMSJobStatus.GENERATING, LIMSJobStatus.FAILED},
    LIMSJobStatus.CLASSIFYING: {LIMSJobStatus.LOADING_TEMPLATE, LIMSJobStatus.FAILED},
    LIMSJobStatus.LOADING_TEMPLATE: {LIMSJobStatus.EXTRACTING, LIMSJobStatus.FAILED},  # re-extract with focused schema
    LIMSJobStatus.GENERATING: {LIMSJobStatus.PENDING_REVIEW, LIMSJobStatus.FAILED},
    LIMSJobStatus.AUGMENTING: {LIMSJobStatus.MERGING, LIMSJobStatus.FAILED},
    LIMSJobStatus.MERGING: {LIMSJobStatus.PENDING_REVIEW, LIMSJobStatus.FAILED},
    # ... existing terminal states
}
```

### 6. config.py — Pipeline Configuration

Add to `LIMSConfig`:
```python
classification_mode: str = "hybrid"           # "rules", "llm", "hybrid"
classification_confidence_threshold: float = 0.8
standards_collection: str = "lims_standards"
calculations_collection: str = "calculation_patterns"
```

---

## Testing Strategy

```bash
# Unit tests for foundation models
uv run pytest main/tests/lims/test_provenance.py -v
uv run pytest main/tests/lims/test_templates.py -v

# Verify existing tests still pass
uv run pytest main/tests/lims/ -v
```

---

## Gate Criteria

- [ ] `ComponentSource` enum has 5 values, `FieldProvenance` validates confidence [0,1]
- [ ] `ProvenanceMap.summary()` returns correct counts
- [ ] `TestType` enum has 5 values, `ClassificationResult` validates fields
- [ ] `TemplateLibrary.register()` decorator works, `get_template_for_type()` raises for unknown types
- [ ] Extended `LIMSJobStatus` has 10 states, `VALID_TRANSITIONS` covers new states
- [ ] Extended `LIMSJob` serializes/deserializes with new Optional fields
- [ ] Extended `LIMSConfig` reads new env vars
- [ ] All existing LIMS tests pass (backward compatible)

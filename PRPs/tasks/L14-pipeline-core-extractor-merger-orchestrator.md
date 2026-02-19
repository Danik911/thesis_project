# Task L14 — Pipeline Core: Focused Extractor, Merger & Two-Layer Orchestrator

**Phase:** 8e (Two-Layer Pipeline — Core) | **Dependencies:** L10, L11, L12, L13
**Branch:** `prjoject_p_protatype`
**Estimated effort:** 3 days
**Status:** NOT STARTED (WAITING ON L10-L13 CODE — handoff updated 2026-02-19)

## Handoff Update (2026-02-19)

- **Implementation readiness:** Data prerequisites are ready; code dependencies (L10-L13 modules) are not implemented yet.
- **Canonical test data for integration:** `output/prepared_l10l15/manifest.json` and `output/prepared_l10l15/per_document/`.
- **Parsed SOP source-of-truth path:** upstream OCR artifacts live in `output/sop_parsed/manifest.json` and `output/sop_parsed/documents/*`; use prepared derivatives (`prepared_l10l15`) during pipeline integration.
- **Parsed Excel support for expected structures (secondary):** `demo_data/parced/*_xlsx.md` and `*_Config_w_Calcs.md` are useful to draft merge/conflict test cases, but integration assertions should validate against canonical `demo_data/*.xlsx` and prepared corpus outputs.
- **Current upstream state:**
    - L12 artifacts directory exists but empty: `output/prepared_l10l15/L12_classifier/`
    - L13 artifacts directory exists but empty: `output/prepared_l10l15/L13_rag/`
- **Known caveat for orchestration:** Keep all references on canonical prepared set (`prepared_l10l15`) to avoid duplicate-ingestion regressions from legacy `output/prepared/`.
- **Next agent action:** Start L14 only after L10-L13 classes and artifacts are in place and validated.

---

## Objective

Build the three core pipeline modules (focused extractor, merger, orchestrator) and rewrite `lims_router.py` to use the new `TwoLayerPipeline`. Add `/classify` and `/template/{type}` endpoints. This is the integration task that connects all foundation models.

---

## Files to Create

| File | Purpose |
|------|---------|
| `main/src/lims/focused_extractor.py` | Builds reduced extraction schema per test type, calls existing `pdf_extractor.py` with narrowed scope |
| `main/src/lims/merger.py` | Merges Template + Variable layers with provenance tracking, detects `MergeConflict`s |
| `main/src/lims/pipeline.py` | `TwoLayerPipeline` orchestrator: Classify -> Template -> Extract -> Augment -> Merge -> Review |

## Files to Modify

| File | Change | Risk |
|------|--------|------|
| `main/api/lims_router.py` | Rewrite `extract_pdf` to use `TwoLayerPipeline`; add `POST /lims/classify`, `GET /lims/template/{type}` endpoints | MEDIUM |

---

## Implementation Details

### 1. focused_extractor.py — Narrowed Extraction

```python
"""Focused extraction: narrows LlamaExtract schema per test type.

Instead of extracting all possible MDA fields, builds a reduced schema
containing only the variable fields for the detected test type.
This reduces hallucination and improves extraction accuracy.

NO FALLBACK LOGIC.
"""

from __future__ import annotations

import logging
from typing import Any

from main.src.lims.config import LIMSConfig
from main.src.lims.test_type import TestType
from main.src.lims.templates.base import TestTypeTemplate

logger = logging.getLogger(__name__)


def build_focused_schema(template: TestTypeTemplate) -> dict[str, Any]:
    """Build a reduced extraction schema from template variable fields.

    Only includes fields marked is_variable=True in the template,
    reducing extraction scope to what's actually in the PDF.
    """
    variable_fields = template.get_variable_fields()
    # Build JSON schema for just these fields
    ...


async def focused_extract(
    pdf_content: bytes,
    filename: str,
    template: TestTypeTemplate,
    config: LIMSConfig,
) -> dict[str, Any]:
    """Extract only variable fields from PDF using focused schema.

    Calls existing pdf_extractor with a narrowed schema.
    """
    ...
```

### 2. merger.py — Template + Variable Merge

```python
"""Merge template skeleton with extracted variables and augmented values.

Produces a complete MDATemplate with full provenance tracking.
Detects conflicts where extracted values disagree with template values.

NO FALLBACK LOGIC.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from pydantic import BaseModel, Field

from main.src.lims.mda_schema import MDATemplate
from main.src.lims.provenance import ComponentSource, ProvenanceMap
from main.src.lims.test_type import TestType

logger = logging.getLogger(__name__)


class MergeConflict(BaseModel):
    """A conflict between template and extracted values."""
    field_path: str
    template_value: Any
    extracted_value: Any
    resolution: Optional[str] = None  # "template", "extracted", or None (SME decision)
    resolved_by: Optional[str] = None


class MergeResult(BaseModel):
    """Result of merging template + extraction + augmentation."""
    mda_template: dict[str, Any]  # Serialized MDATemplate
    provenance: dict[str, Any]     # Serialized ProvenanceMap
    conflicts: list[MergeConflict] = Field(default_factory=list)
    stats: dict[str, int] = Field(default_factory=dict)  # counts per source


def merge_layers(
    template_mda: MDATemplate,
    extracted_data: dict[str, Any],
    augmented_data: dict[str, Any] | None = None,
    test_type: TestType | None = None,
) -> MergeResult:
    """Merge template + extracted + augmented layers into final MDA.

    Priority: Extracted > Template > Augmented > SME_REQUIRED
    Conflicts are recorded, not auto-resolved.
    """
    ...
```

### 3. pipeline.py — Two-Layer Orchestrator

```python
"""Two-Layer Pipeline orchestrator.

Orchestrates the full pipeline:
1. CLASSIFY: Detect test type
2. TEMPLATE: Load curated skeleton
3. EXTRACT: Focused extraction from PDF
4. AUGMENT: Fill gaps from standards RAG
5. MERGE: Combine layers with provenance
6. REVIEW: Ready for SME review

Falls back to single-layer pipeline for TestType.OTHER (backward compat).

NO FALLBACK LOGIC for known test types.
"""

from __future__ import annotations

import logging
from typing import Any

from main.src.lims.classifier import TestTypeClassifier
from main.src.lims.config import LIMSConfig
from main.src.lims.focused_extractor import focused_extract
from main.src.lims.merger import MergeResult, merge_layers
from main.src.lims.provenance import ProvenanceMap
from main.src.lims.standards_loader import query_standards
from main.src.lims.templates import TemplateLibrary
from main.src.lims.test_type import ClassificationResult, TestType

logger = logging.getLogger(__name__)


class PipelineStageDetail(BaseModel):
    """Record of what happened at each pipeline stage."""
    stage: str
    duration_ms: int
    summary: str
    details: dict[str, Any] = {}


class TwoLayerPipeline:
    """Orchestrates the two-layer extraction pipeline."""

    def __init__(self, config: LIMSConfig):
        self.config = config
        self.classifier = TestTypeClassifier(
            confidence_threshold=config.classification_confidence_threshold
        )

    async def run(
        self, pdf_content: bytes, filename: str
    ) -> dict[str, Any]:
        """Run the full two-layer pipeline.

        Returns dict with: classification, mda_template, provenance,
        conflicts, stage_details
        """
        stages: list[PipelineStageDetail] = []

        # 1. Classify
        classification = self.classifier.classify(pdf_text, filename)

        # 2. Load template (or fall back to single-layer for OTHER)
        if classification.test_type == TestType.OTHER:
            return await self._single_layer_fallback(pdf_content, filename)

        template = TemplateLibrary.get_template_for_type(classification.test_type)
        template_mda = template.to_mda_template()

        # 3. Focused extraction
        extracted = await focused_extract(pdf_content, filename, template, self.config)

        # 4. Augment from standards RAG
        augmented = await self._augment_gaps(template_mda, extracted, classification)

        # 5. Merge
        merge_result = merge_layers(template_mda, extracted, augmented)

        return {
            "classification": classification.model_dump(),
            "mda_template": merge_result.mda_template,
            "provenance": merge_result.provenance,
            "conflicts": [c.model_dump() for c in merge_result.conflicts],
            "stage_details": [s.model_dump() for s in stages],
        }
```

### 4. lims_router.py — New Endpoints

Add:
- `POST /lims/classify` — classify a PDF without full extraction
- `GET /lims/template/{type}` — preview template skeleton for a test type
- Rewrite `POST /lims/extract` to use `TwoLayerPipeline`

---

## Testing Strategy

```bash
# Pipeline integration tests
uv run pytest main/tests/lims/test_pipeline.py -v
uv run pytest main/tests/lims/test_merger.py -v

# Full LIMS test suite
uv run pytest main/tests/lims/ -v
```

---

## Gate Criteria

- [ ] `TwoLayerPipeline.run()` produces complete MDA with provenance for all known test types
- [ ] `TestType.OTHER` falls back to single-layer pipeline (backward compat)
- [ ] `MergeConflict`s detected when template and extraction disagree
- [ ] `MDATemplate.validate_cross_sheet_integrity()` passes after merge
- [ ] Every component in final MDA has non-null provenance
- [ ] `/classify` endpoint returns classification result
- [ ] `/template/{type}` endpoint returns template skeleton
- [ ] Rewritten `/extract` uses TwoLayerPipeline
- [ ] AND_ACS_DYE still works (backward compat via identity template or OTHER fallback)
- [ ] All existing LIMS tests pass

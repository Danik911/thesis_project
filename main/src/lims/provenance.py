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

    TEMPLATE = "TEMPLATE"
    EXTRACTED = "EXTRACTED"
    INFERRED = "INFERRED"
    SME_REQUIRED = "SME_REQUIRED"
    SME_MODIFIED = "SME_MODIFIED"


class FieldProvenance(BaseModel):
    """Provenance metadata for a single field value."""

    source: ComponentSource
    confidence: float = Field(ge=0.0, le=1.0)
    source_detail: str = ""
    original_value: Optional[Any] = None


class ProvenanceMap(BaseModel):
    """Parallel provenance structure for an MDATemplate.

    Keys are dot-notation paths like "analyses[0].name" or
    "components[2].result_type". Every populated field in the final
    MDA should have an entry here.
    """

    fields: dict[str, FieldProvenance] = Field(default_factory=dict)

    def set_provenance(
        self,
        path: str,
        source: ComponentSource,
        confidence: float,
        detail: str = "",
    ) -> None:
        self.fields[path] = FieldProvenance(
            source=source,
            confidence=confidence,
            source_detail=detail,
        )

    def get_provenance(self, path: str) -> Optional[FieldProvenance]:
        return self.fields.get(path)

    def summary(self) -> dict[str, int]:
        """Count of fields per source type."""
        counts: dict[str, int] = {}
        for field_provenance in self.fields.values():
            counts[field_provenance.source.value] = (
                counts.get(field_provenance.source.value, 0) + 1
            )
        return counts
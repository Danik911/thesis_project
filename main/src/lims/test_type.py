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
    method: str
    evidence: list[str] = Field(default_factory=list)
    pdf_filename: Optional[str] = None
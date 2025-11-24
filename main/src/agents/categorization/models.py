"""Pydantic models and ambiguity guardrails for GAMP categorization."""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class GAMPCategorizationResult(BaseModel):
    """Structured output schema for GAMP categorization results."""

    category: int = Field(
        ...,
        ge=1,
        le=5,
        description="GAMP category number (must be 1, 3, 4, or 5)"
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 and 1.0"
    )
    reasoning: str = Field(
        ...,
        min_length=10,
        description="Brief justification for the categorization decision"
    )

    has_ambiguity_signals: bool = Field(
        default=False,
        description="True if ANY uncertainty detected (keywords, conflicting indicators, multiple interpretations)"
    )
    ambiguity_details: str | None = Field(
        default=None,
        description="Specific reason for ambiguity (e.g., 'Category 3/4 boundary: configuration unclear')"
    )
    requires_human_review: bool = Field(
        default=False,
        description="MANDATORY HIL trigger flag (true if confidence < 0.85 OR ambiguity detected)"
    )
    alternative_categories: List[int] | None = Field(
        default=None,
        description="Other plausible GAMP categories if ambiguous (e.g., [4, 5] for Cat 4/5 boundary)"
    )

    def validate_category(self) -> None:
        """Validate that category is a valid GAMP category (1, 3, 4, or 5)."""
        if self.category not in [1, 3, 4, 5]:
            raise ValueError(f"Invalid GAMP category: {self.category}. Must be 1, 3, 4, or 5.")


GAMPCategorizationResult.model_rebuild()


AMBIGUITY_KEYWORDS = [
    "optional",
    "optional module",
    "customizable",
    "customisable",
    "hybrid",
    "ambiguous",
    "unclear",
    "may include",
    "may require",
    "configurable modules",
    "plugin",
    "extensible",
    "extension"
]

CONFIGURATION_INDICATORS = [
    "configure",
    "configuration",
    "configured",
    "configurable",
    "workflow",
    "parameter",
    "rule",
    "setup",
    "templated",
    "vendor tool",
    "user-defined"
]

CUSTOM_DEVELOPMENT_INDICATORS = [
    "custom",
    "custom-developed",
    "bespoke",
    "proprietary",
    "module",
    "algorithm",
    "code",
    "development",
    "sdk",
    "plugin",
    "extension",
    "script"
]

INFRASTRUCTURE_INDICATORS = [
    "operating system",
    "os",
    "database",
    "firmware",
    "infrastructure",
    "middleware",
    "platform",
    "server",
    "virtual",
    "network"
]

APPLICATION_SOFTWARE_INDICATORS = [
    "lims",
    "mes",
    "erp",
    "workflow",
    "application",
    "software",
    "platform",
    "dashboard",
    "portal",
    "management system"
]

VAGUE_REQUIREMENT_PHRASES = [
    "tbd",
    "to be determined",
    "to be defined",
    "details to be",
    "insufficient detail",
    "missing information",
    "unclear",
    "unknown",
    "not specified"
]


def enforce_universal_ambiguity_guards(
    result: GAMPCategorizationResult,
    urs_content: str
) -> GAMPCategorizationResult:
    """Apply deterministic ambiguity detection on top of LLM output."""
    urs_text = (urs_content or "").lower()
    has_signals = result.has_ambiguity_signals
    requires_review = result.requires_human_review or result.confidence_score < 0.85
    ambiguity_reasons: list[str] = []
    alt_categories = set(result.alternative_categories or [])

    keyword_hits = [kw for kw in AMBIGUITY_KEYWORDS if kw in urs_text]
    if keyword_hits:
        has_signals = True
        ambiguity_reasons.append(
            "Mandatory ambiguity keywords detected: " + ", ".join(keyword_hits[:3])
        )

    has_config = any(term in urs_text for term in CONFIGURATION_INDICATORS)
    has_custom_dev = any(term in urs_text for term in CUSTOM_DEVELOPMENT_INDICATORS)
    if has_config and has_custom_dev:
        has_signals = True
        alt_categories.update({4, 5})
        ambiguity_reasons.append("Category 4/5 boundary: configuration plus custom development indicators present")

    has_infrastructure = any(term in urs_text for term in INFRASTRUCTURE_INDICATORS)
    has_application = any(term in urs_text for term in APPLICATION_SOFTWARE_INDICATORS)
    if has_infrastructure and has_application:
        has_signals = True
        alt_categories.update({1, 3})
        ambiguity_reasons.append("Category 1/3 boundary: infrastructure and application signals overlap")

    mentions_cots = "cots" in urs_text or "off-the-shelf" in urs_text
    if mentions_cots and has_config:
        has_signals = True
        alt_categories.update({3, 4})
        ambiguity_reasons.append("Category 3/4 boundary: COTS mention plus configuration requirements")

    if any(phrase in urs_text for phrase in VAGUE_REQUIREMENT_PHRASES):
        has_signals = True
        ambiguity_reasons.append("URS states requirements are incomplete or to be determined")

    if has_signals:
        requires_review = True

    existing_details = result.ambiguity_details.strip() if result.ambiguity_details else ""
    details = existing_details
    if ambiguity_reasons:
        reason_text = "; ".join(ambiguity_reasons)
        details = f"{existing_details}; {reason_text}" if existing_details else reason_text

    result.has_ambiguity_signals = has_signals
    result.ambiguity_details = details or None
    result.alternative_categories = sorted(alt_categories) if alt_categories else None
    result.requires_human_review = requires_review or has_signals
    return result


__all__ = [
    "GAMPCategorizationResult",
    "enforce_universal_ambiguity_guards",
]

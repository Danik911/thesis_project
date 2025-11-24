"""Unit tests for the consultation trigger helper."""

from src.core.consultation_utils import derive_consultation_triggers
from src.core.events import GAMPCategorizationEvent, GAMPCategory


def _base_event(**overrides) -> GAMPCategorizationEvent:
    """Create a baseline categorization event for testing."""
    payload = {
        "gamp_category": GAMPCategory.CATEGORY_4,
        "confidence_score": 0.95,
        "justification": "unit-test",
        "risk_assessment": {},
        "categorized_by": "unit-test-suite",
    }
    payload.update(overrides)
    return GAMPCategorizationEvent(**payload)


def test_triggers_when_ambiguity_detected():
    event = _base_event(
        has_ambiguity_signals=True,
        ambiguity_details="Category 4/5 boundary",
    )

    requires_consultation, reasons, original_confidence = derive_consultation_triggers(event, 0.85)

    assert requires_consultation is True
    assert any("Ambiguity signals" in reason for reason in reasons)
    assert original_confidence == event.confidence_score


def test_triggers_use_original_confidence():
    event = _base_event(
        confidence_score=0.95,
        risk_assessment={"original_confidence": 0.6},
    )

    requires_consultation, reasons, original_confidence = derive_consultation_triggers(event, 0.85)

    assert requires_consultation is True
    assert any("0.60" in reason for reason in reasons)
    assert original_confidence == 0.6


def test_triggers_include_risk_flag():
    event = _base_event(
        risk_assessment={"flags": ["consultation_required"]},
    )

    requires_consultation, reasons, _ = derive_consultation_triggers(event, 0.75)

    assert requires_consultation is True
    assert any("consultation_required" in reason for reason in reasons)


def test_no_triggers_for_clear_case():
    event = _base_event()

    requires_consultation, reasons, _ = derive_consultation_triggers(event, 0.75)

    assert requires_consultation is False
    assert reasons == []

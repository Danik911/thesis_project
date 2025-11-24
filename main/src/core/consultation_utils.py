"""Utility helpers for Human-in-the-Loop consultation gating.

These helpers encapsulate the consultation trigger logic so that it can be
unit-tested in isolation (without instantiating the full unified workflow)
and can follow the reference patterns from the official LlamaIndex human in
the loop demos.

Examples referenced for parity:
    - https://github.com/run-llama/human_in_the_loop_workflow_demo
    - https://github.com/run-llama/python-agents-tutorial/blob/main/5_human_in_the_loop.py
"""

from __future__ import annotations

from .events import GAMPCategorizationEvent


def derive_consultation_triggers(
    event: GAMPCategorizationEvent,
    confidence_threshold: float,
) -> tuple[bool, list[str], float]:
    """Return whether consultation is required and the reasons.

    Args:
        event: Categorization event emitted by the GAMP-5 workflow.
        confidence_threshold: Threshold below which confidence alone triggers review.

    Returns:
        A tuple of ``(requires_consultation, reasons, original_confidence)``.
    """
    risk_assessment = event.risk_assessment or {}
    original_confidence = risk_assessment.get("original_confidence", event.confidence_score)

    reasons: list[str] = []

    if event.review_required:
        reasons.append("Categorization agent flagged review_required")

    if getattr(event, "has_ambiguity_signals", False):
        ambiguity_details = getattr(event, "ambiguity_details", None)
        if ambiguity_details:
            reasons.append(f"Ambiguity signals detected ({ambiguity_details})")
        else:
            reasons.append("Ambiguity signals detected")

    if original_confidence < confidence_threshold:
        reasons.append(
            f"Confidence {original_confidence:.2f} below threshold {confidence_threshold:.2f}"
        )

    flags = risk_assessment.get("flags", [])
    if isinstance(flags, list) and "consultation_required" in flags:
        reasons.append("Risk assessment flagged consultation_required")

    requires_consultation = bool(reasons)
    return requires_consultation, reasons, original_confidence

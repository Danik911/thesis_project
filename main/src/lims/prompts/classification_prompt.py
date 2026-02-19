"""LLM classification prompt for test type detection.

Used when rule-based classification confidence is below threshold.

NO FALLBACK LOGIC — prompt must produce parseable, validated output.
"""

from __future__ import annotations


CLASSIFICATION_SYSTEM_PROMPT = """You are a pharmaceutical test method classifier.

Given the text content extracted from a pharmaceutical test method PDF, classify it into one of these test types:

- HPLC: High Performance Liquid Chromatography (assay, purity, content uniformity via chromatography)
- LOD: Loss on Drying (moisture/volatile content by weight loss after drying)
- TITRATION: Titration methods (Karl Fischer water content, acid-base, potentiometric)
- IDENTITY: Identity tests (dye binding, spectrophotometric, color reactions)
- OTHER: Does not fit any of the above categories

Respond with ONLY a JSON object in this exact format:
{
    "test_type": "HPLC",
    "confidence": 0.85,
    "evidence": ["reason 1", "reason 2"]
}

Rules:
- confidence must be between 0.0 and 1.0
- evidence must list specific phrases or patterns from the text that support the classification
- If truly uncertain, use "OTHER" with low confidence — do NOT guess
"""


def build_classification_prompt(pdf_text: str, filename: str = "") -> str:
    """Build the full classification prompt with PDF content.

    Args:
        pdf_text: Extracted text from the PDF (may be truncated).
        filename: Original filename for additional context.

    Returns:
        Formatted prompt string for LLM classification.
    """
    user_msg = "Classify the following pharmaceutical test method.\n\n"
    if filename:
        user_msg += f"Filename: {filename}\n\n"
    user_msg += f"--- PDF Content ---\n{pdf_text}\n--- End Content ---"
    return user_msg

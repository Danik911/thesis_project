# Task L12 — Hybrid Test Type Classifier

**Phase:** 8c (Two-Layer Pipeline — Classification) | **Dependencies:** L10 (Foundation Models)
**Branch:** `prjoject_p_protatype`
**Estimated effort:** 2 days
**Status:** NOT STARTED

---

## Objective

Build a hybrid classifier that detects test type (HPLC, LOD, Titration, Identity) from uploaded PDFs. Primary classification via deterministic rules (keyword matching, structure analysis); LLM fallback when rule confidence < threshold. Must achieve >90% accuracy on 18+ demo PDFs.

---

## Files to Create

| File | Purpose |
|------|---------|
| `main/src/lims/classifier.py` | `TestTypeClassifier` class with `classify(pdf_text, filename)` method. Rule engine + LLM fallback |
| `main/src/lims/prompts/classification_prompt.py` | LLM system prompt for test type classification when rules are uncertain |

## Files to Modify

None (uses foundation models from L10).

---

## Implementation Details

### 1. classifier.py — Hybrid Classifier

```python
"""Hybrid test type classifier: rules primary, LLM fallback.

Classification strategy:
1. Filename-based rules (highest confidence)
2. Content keyword matching (medium confidence)
3. Structure analysis (component patterns)
4. LLM fallback if confidence < threshold

GAMP-5 Category 5: Custom pharmaceutical software component.
NO FALLBACK LOGIC — if classification fails, raise with diagnostics.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from main.src.lims.test_type import ClassificationResult, TestType

logger = logging.getLogger(__name__)


# Keyword patterns per test type
KEYWORD_PATTERNS: dict[TestType, list[str]] = {
    TestType.HPLC: [
        r"hplc", r"high.?performance.?liquid.?chromatograph",
        r"column", r"mobile.?phase", r"gradient", r"isocratic",
        r"injection.?volume", r"retention.?time", r"system.?suitability",
        r"peak.?area", r"uv.?detect", r"wavelength",
    ],
    TestType.LOD: [
        r"loss.?on.?drying", r"lod\b", r"drying.?temperature",
        r"drying.?time", r"weight.?loss", r"moisture.?content",
        r"usp.*731", r"desiccator",
    ],
    TestType.TITRATION: [
        r"titrat", r"karl.?fischer", r"endpoint",
        r"buret", r"titrant", r"potentiometric",
        r"water.?content", r"kf\b",
    ],
    TestType.IDENTITY: [
        r"identity.?test", r"dye.?binding", r"acs\b",
        r"absorbance", r"spectrophotom", r"color.?reaction",
        r"visual.?inspection",
    ],
}

# Filename patterns (most reliable — lab naming conventions)
FILENAME_PATTERNS: dict[TestType, list[str]] = {
    TestType.HPLC: [r"hplc", r"cex", r"sec", r"rp_hplc", r"uplc"],
    TestType.LOD: [r"lod", r"loss.?on.?dry"],
    TestType.TITRATION: [r"kf", r"karl.?fischer", r"titrat"],
    TestType.IDENTITY: [r"acs", r"identity", r"dye"],
}


class TestTypeClassifier:
    """Hybrid test type classifier.

    Classification is attempted in order of confidence:
    1. Filename rules (confidence 0.95 if matched)
    2. Content keyword scoring (confidence based on match density)
    3. LLM classification (confidence from LLM response)

    If all strategies fail to produce a result above the confidence
    threshold, raises ValueError with full diagnostic information.
    """

    def __init__(self, confidence_threshold: float = 0.8):
        """Initialize classifier.

        Args:
            confidence_threshold: Minimum confidence for rule-based
                classification. Below this, LLM fallback is invoked.
        """
        self.confidence_threshold = confidence_threshold

    def classify(
        self, pdf_text: str, filename: str = ""
    ) -> ClassificationResult:
        """Classify test type using hybrid rules + LLM.

        Args:
            pdf_text: Extracted text content from the PDF.
            filename: Original PDF filename (used for filename-based rules).

        Returns:
            ClassificationResult with test_type, confidence, method, evidence.

        Raises:
            ValueError: If classification fails entirely (no rules match
                and LLM is unavailable or returns invalid result).
        """
        # 1. Try filename rules (highest confidence)
        result = self._classify_by_filename(filename)
        if result and result.confidence >= self.confidence_threshold:
            logger.info(
                "Classified '%s' as %s via filename (confidence: %.2f)",
                filename, result.test_type.value, result.confidence,
            )
            return result

        # 2. Try keyword matching
        result = self._classify_by_keywords(pdf_text)
        if result and result.confidence >= self.confidence_threshold:
            logger.info(
                "Classified '%s' as %s via keywords (confidence: %.2f)",
                filename, result.test_type.value, result.confidence,
            )
            return result

        # 3. LLM fallback
        logger.info(
            "Rule-based classification below threshold (%.2f). "
            "Invoking LLM classification for '%s'.",
            self.confidence_threshold, filename,
        )
        result = self._classify_by_llm(pdf_text, filename)
        return result

    def _classify_by_filename(self, filename: str) -> Optional[ClassificationResult]:
        """Classify based on filename patterns.

        Lab naming conventions are highly reliable indicators:
        - AND_BCMA_CEX -> HPLC (CEX = cation exchange chromatography)
        - AND_USP_LOD -> LOD
        - FRE_KF_USP -> TITRATION (KF = Karl Fischer)
        - AND_ACS_DYE -> IDENTITY (ACS = identity dye binding)

        Returns:
            ClassificationResult with confidence 0.95 if matched, None otherwise.
        """
        if not filename:
            return None

        filename_lower = filename.lower()
        for test_type, patterns in FILENAME_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, filename_lower):
                    return ClassificationResult(
                        test_type=test_type,
                        confidence=0.95,
                        method="rules",
                        evidence=[f"Filename '{filename}' matches pattern '{pattern}'"],
                        pdf_filename=filename,
                    )
        return None

    def _classify_by_keywords(self, pdf_text: str) -> Optional[ClassificationResult]:
        """Classify based on keyword frequency in PDF content.

        Scores each test type by counting keyword matches in the text.
        Confidence is proportional to match count relative to total patterns.

        Returns:
            ClassificationResult for highest-scoring type, or None if
            no type exceeds minimum match threshold.
        """
        if not pdf_text:
            return None

        text_lower = pdf_text.lower()
        scores: dict[TestType, list[str]] = {}

        for test_type, patterns in KEYWORD_PATTERNS.items():
            matched = []
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    matched.append(pattern)
            if matched:
                scores[test_type] = matched

        if not scores:
            return None

        # Find best match
        best_type = max(scores, key=lambda t: len(scores[t]))
        best_matches = scores[best_type]
        total_patterns = len(KEYWORD_PATTERNS[best_type])
        confidence = min(len(best_matches) / total_patterns, 0.95)

        return ClassificationResult(
            test_type=best_type,
            confidence=round(confidence, 2),
            method="rules",
            evidence=[f"Matched {len(best_matches)}/{total_patterns} keywords: {best_matches}"],
        )

    def _classify_by_llm(
        self, pdf_text: str, filename: str
    ) -> ClassificationResult:
        """Classify using LLM when rule-based methods are uncertain.

        Uses the classification prompt to ask the LLM to identify
        the test type from PDF content.

        Args:
            pdf_text: Full extracted PDF text.
            filename: Original filename.

        Returns:
            ClassificationResult from LLM analysis.

        Raises:
            RuntimeError: If LLM call fails or returns unparseable result.
        """
        # Import here to avoid circular dependency and allow rule-only usage
        from main.src.lims.prompts.classification_prompt import (
            build_classification_prompt,
        )

        # Build prompt with PDF text (truncated to avoid token limits)
        max_chars = 8000
        truncated_text = pdf_text[:max_chars]
        prompt = build_classification_prompt(truncated_text, filename)

        # LLM call will be integrated via the existing chat infrastructure
        # For now, raise explicit error if LLM integration is not yet available
        raise NotImplementedError(
            "LLM classification not yet integrated. "
            f"Rule-based classification failed for '{filename}'. "
            f"PDF text length: {len(pdf_text)} chars. "
            "Integrate LLM call in _classify_by_llm() to enable fallback."
        )
```

### 2. prompts/classification_prompt.py

System prompt that tells the LLM about pharmaceutical test types and asks it to classify based on PDF content.

```python
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
    user_msg = f"Classify the following pharmaceutical test method.\n\n"
    if filename:
        user_msg += f"Filename: {filename}\n\n"
    user_msg += f"--- PDF Content ---\n{pdf_text}\n--- End Content ---"
    return user_msg
```

---

## Testing Strategy

```bash
# Classification tests against demo PDFs
uv run pytest main/tests/lims/test_classifier.py -v

# Manual test: classify all 18 demo PDFs by filename
python -c "
from main.src.lims.classifier import TestTypeClassifier
classifier = TestTypeClassifier()

demo_files = [
    'AND_ACS_DYE-LAB-2499.pdf',
    'AND_BCMA_CEX-LAB-1234.pdf',
    'AND_USP_LOD-LAB-5678.pdf',
    'FRE_KF_USP-LAB-9012.pdf',
    # ... add all 18 demo filenames
]

for f in demo_files:
    result = classifier._classify_by_filename(f)
    print(f'{f}: {result.test_type.value if result else \"UNCLASSIFIED\"} ({result.confidence if result else 0})')
"
```

---

## Gate Criteria

- [ ] Rule-based classification correctly identifies test types from demo PDF filenames
- [ ] Keyword classification matches test types from PDF content
- [ ] LLM fallback produces valid ClassificationResult (once integrated)
- [ ] >90% accuracy across 18+ demo PDF filenames
- [ ] Confidence scores are meaningful (rules > keywords > LLM for clear cases)
- [ ] `TestType.OTHER` returned for unrecognized test methods
- [ ] All existing LIMS tests pass

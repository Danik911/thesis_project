"""Hybrid test type classifier: rules primary, LLM fallback.

Classification strategy (4-step):
1. Filename-based rules (highest confidence — 0.95)
2. Content keyword matching (step-function confidence 0.55-0.92)
3. Exclusion-based OTHER (confidence 0.85 when no keywords match)
4. LLM fallback (raises NotImplementedError until integrated)

GAMP-5 Category 5: Custom pharmaceutical software component.
NO FALLBACK LOGIC — if classification fails, raise with diagnostics.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from langfuse import observe

from main.src.lims.test_type import ClassificationResult, TestType

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Filename patterns — pharmaceutical lab naming conventions (most reliable)
# Uses (?:^|_) and (?:_|$) as word boundaries since filenames are
# underscore-delimited after normalization (hyphens → underscores, ext stripped).
# ---------------------------------------------------------------------------
_S = r"(?:^|_)"  # segment start
_E = r"(?:_|$)"  # segment end

FILENAME_PATTERNS: dict[TestType, list[str]] = {
    TestType.HPLC: [
        _S + r"asy" + _E, _S + r"assay" + _E,
        _S + r"as_pu" + _E, _S + r"aspu" + _E, _S + r"apu" + _E,
        _S + r"asy_imps" + _E, _S + r"reso" + _E,
        _S + r"cex" + _E, _S + r"sec" + _E,
        r"hplc", r"uplc", r"rp_hplc",
    ],
    TestType.LOD: [
        _S + r"lod" + _E, r"loss_on_dry",
    ],
    TestType.TITRATION: [
        _S + r"kf" + _E, r"karl_fischer", r"titrat",
    ],
    TestType.IDENTITY: [
        _S + r"acs" + _E, r"identity", _S + r"dye" + _E,
    ],
}


# ---------------------------------------------------------------------------
# Content keyword patterns — text-based classification
# ---------------------------------------------------------------------------
KEYWORD_PATTERNS: dict[TestType, list[str]] = {
    TestType.HPLC: [
        r"hplc",
        r"high.?performance.?liquid.?chromatograph",
        r"column",
        r"mobile.?phase",
        r"gradient",
        r"isocratic",
        r"injection.?volume",
        r"retention.?time",
        r"system.?suitability",
        r"peak.?area",
        r"uv.?detect",
        r"wavelength",
        r"chromatogra",
        r"assay.?purity",
        r"impurit",
        r"resolution.?factor",
    ],
    TestType.LOD: [
        r"loss.?on.?drying",
        r"\blod\b",
        r"drying.?temperature",
        r"drying.?time",
        r"weight.?loss",
        r"moisture.?content",
        r"usp.*731",
        r"desiccator",
    ],
    TestType.TITRATION: [
        r"titrat",
        r"karl.?fischer",
        r"endpoint",
        r"buret",
        r"titrant",
        r"potentiometric",
        r"water.?content",
        r"\bkf\b",
        r"coulometric",
        r"volumetric.?analysis",
    ],
    TestType.IDENTITY: [
        r"identity.?test",
        r"dye.?binding",
        r"\bacs\b",
        r"spectrophotom",
        r"color.?reaction",
        r"visual.?inspection",
        r"identification",
        r"suitability.?for.?use",
    ],
}


# ---------------------------------------------------------------------------
# Negative patterns — prevent misclassification
# ---------------------------------------------------------------------------
NEGATIVE_PATTERNS: dict[TestType, list[str]] = {
    TestType.HPLC: [
        r"ion.?chromatograph",
        r"ion.?exchange",
        r"residue.?on.?ignition",
        r"light.?diffraction",
        r"particle.?size",
        r"biological.?indicator",
        r"nitrate",
    ],
}


# ---------------------------------------------------------------------------
# Step-function confidence mapping for keyword matches
# ---------------------------------------------------------------------------
def _keyword_confidence(match_count: int) -> float:
    """Convert keyword match count to confidence score (step function).

    5+ matches → 0.92
    4  matches → 0.88
    3  matches → 0.85
    2  matches → 0.75
    1  match   → 0.55
    0  matches → 0.0
    """
    if match_count >= 5:
        return 0.92
    if match_count == 4:
        return 0.88
    if match_count == 3:
        return 0.85
    if match_count == 2:
        return 0.75
    if match_count == 1:
        return 0.55
    return 0.0


class TestTypeClassifier:
    """Hybrid test type classifier.

    Classification is attempted in order of confidence:
    1. Filename rules (confidence 0.95 if matched)
    2. Content keyword scoring (step-function confidence)
    3. Exclusion-based OTHER (confidence 0.85)
    4. LLM classification (raises NotImplementedError)

    If all strategies fail to produce a result above the confidence
    threshold, raises ValueError with full diagnostic information.
    """

    def __init__(self, confidence_threshold: float = 0.8) -> None:
        self.confidence_threshold = confidence_threshold

    @observe(name="lims-classify")
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
            NotImplementedError: If LLM classification is invoked (not yet integrated).
        """
        # Step 1: Filename rules (highest confidence)
        result = self._classify_by_filename(filename)
        if result and result.confidence >= self.confidence_threshold:
            logger.info(
                "Classified '%s' as %s via filename (confidence: %.2f)",
                filename, result.test_type.value, result.confidence,
            )
            return result

        # Step 2: Keyword matching
        result, keyword_scores = self._classify_by_keywords(pdf_text)
        if result and result.confidence >= self.confidence_threshold:
            logger.info(
                "Classified '%s' as %s via keywords (confidence: %.2f)",
                filename, result.test_type.value, result.confidence,
            )
            result.pdf_filename = filename
            return result

        # Step 3: Exclusion-based OTHER
        result = self._classify_by_exclusion(pdf_text, keyword_scores)
        if result and result.confidence >= self.confidence_threshold:
            logger.info(
                "Classified '%s' as OTHER via exclusion (confidence: %.2f)",
                filename, result.confidence,
            )
            result.pdf_filename = filename
            return result

        # Step 4: LLM fallback
        logger.info(
            "Rule-based classification below threshold (%.2f). "
            "Invoking LLM classification for '%s'.",
            self.confidence_threshold, filename,
        )
        return self._classify_by_llm(pdf_text, filename)

    def _classify_by_filename(self, filename: str) -> Optional[ClassificationResult]:
        """Classify based on filename patterns.

        Lab naming conventions are highly reliable indicators:
        - AND_ASY_HSUCC → HPLC (ASY = assay)
        - AND_USP_LOD   → LOD
        - FRE_KF_USP    → TITRATION (KF = Karl Fischer)
        - AND_ACS_DYE   → IDENTITY (ACS = identity dye binding)

        Returns:
            ClassificationResult with confidence 0.95 if matched, None otherwise.
        """
        if not filename:
            return None

        # Normalize: lowercase, hyphens→underscores, strip extension
        filename_lower = filename.lower().replace("-", "_")
        name_part = re.sub(r"\.[^.]+$", "", filename_lower)

        for test_type, patterns in FILENAME_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, name_part):
                    # Extract human-readable keyword from regex
                    keyword = re.sub(r"[\\()?:^|$_\[\]{}+*]", "", pattern).strip()
                    return ClassificationResult(
                        test_type=test_type,
                        confidence=0.95,
                        method="filename",
                        evidence=[
                            f"Filename '{filename}' contains "
                            f"'{keyword}' keyword for {test_type.value}"
                        ],
                        pdf_filename=filename,
                    )
        return None

    def _classify_by_keywords(
        self, pdf_text: str
    ) -> tuple[Optional[ClassificationResult], dict[TestType, list[str]]]:
        """Classify based on keyword frequency in PDF content.

        Scores each test type by counting keyword matches in the text.
        Applies negative patterns to suppress false positives.
        Uses step-function confidence based on match count.

        Returns:
            Tuple of (ClassificationResult or None, scores dict).
        """
        empty_scores: dict[TestType, list[str]] = {}
        if not pdf_text or not pdf_text.strip():
            return None, empty_scores

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
            return None, scores

        # Apply negative patterns to suppress false positives
        for test_type, neg_patterns in NEGATIVE_PATTERNS.items():
            if test_type in scores:
                for neg_pattern in neg_patterns:
                    if re.search(neg_pattern, text_lower):
                        logger.debug(
                            "Negative pattern '%s' suppresses %s classification",
                            neg_pattern, test_type.value,
                        )
                        del scores[test_type]
                        break

        if not scores:
            return None, scores

        # Find best match by count
        best_type = max(scores, key=lambda t: len(scores[t]))
        best_matches = scores[best_type]
        confidence = _keyword_confidence(len(best_matches))

        result = ClassificationResult(
            test_type=best_type,
            confidence=confidence,
            method="keywords",
            evidence=[
                f"Matched {len(best_matches)} keywords: "
                + ", ".join(best_matches)
            ],
        )
        return result, scores

    def _classify_by_exclusion(
        self,
        pdf_text: str,
        keyword_scores: dict[TestType, list[str]],
    ) -> Optional[ClassificationResult]:
        """Classify as OTHER when no keywords match significantly.

        If pdf_text is non-empty AND best keyword score is <=1 match,
        classify as OTHER with confidence 0.85.

        Returns:
            ClassificationResult for OTHER, or None.
        """
        if not pdf_text or not pdf_text.strip():
            return None

        # If we have some keyword matches but all weak (1 match only),
        # or no matches at all → OTHER
        best_match_count = 0
        if keyword_scores:
            best_match_count = max(len(v) for v in keyword_scores.values())

        if best_match_count <= 1:
            evidence_parts = ["No strong keyword matches found"]
            if keyword_scores:
                weak = [
                    f"{t.value}={len(m)}" for t, m in keyword_scores.items()
                ]
                evidence_parts.append(f"Weak matches: {', '.join(weak)}")

            return ClassificationResult(
                test_type=TestType.OTHER,
                confidence=0.85,
                method="exclusion",
                evidence=evidence_parts,
            )
        return None

    def _classify_by_llm(
        self, pdf_text: str, filename: str
    ) -> ClassificationResult:
        """Classify using LLM when rule-based methods are uncertain.

        Raises:
            NotImplementedError: LLM classification not yet integrated.
        """
        raise NotImplementedError(
            "LLM classification not yet integrated. "
            f"Rule-based classification failed for '{filename}'. "
            f"PDF text length: {len(pdf_text)} chars. "
            "Integrate LLM call in _classify_by_llm() to enable fallback."
        )

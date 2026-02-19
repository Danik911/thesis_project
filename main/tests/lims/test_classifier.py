"""Tests for the hybrid test type classifier (L12).

Ground truth: 25 demo PDFs from demo_data/parced/Data Exploration.md
Target: >90% accuracy (23/25 minimum), actual target 100%.

NO FALLBACK LOGIC — tests verify explicit failures, not silent degradation.
"""

from __future__ import annotations

import pytest

from main.src.lims.classifier import (
    FILENAME_PATTERNS,
    KEYWORD_PATTERNS,
    NEGATIVE_PATTERNS,
    TestTypeClassifier,
    _keyword_confidence,
)
from main.src.lims.test_type import ClassificationResult, TestType


# ---------------------------------------------------------------------------
# Ground truth for all 25 demo PDFs
# ---------------------------------------------------------------------------
GROUND_TRUTH: dict[str, TestType] = {
    # HPLC (14 files)
    "AND_ASY_HSUCC-LAB-2873.pdf": TestType.HPLC,
    "AND_BCMA_CEX-LAB-38176.pdf": TestType.HPLC,
    "FRE_ABRO_B_AS_PU-TM8832A.pdf": TestType.HPLC,
    "FRE_BOSU_R_ASSAY-TM6687A.pdf": TestType.HPLC,
    "FRE_BOSU_R_RESO-TM6692A.pdf": TestType.HPLC,
    "FRE_PALBO_ASY_IMPS-TM8439A.pdf": TestType.HPLC,
    "FRE_QUI_R_ASPU_ALT-TM0269A.pdf": TestType.HPLC,
    "FRE_TAF20_C_APU-TM0019B.pdf": TestType.HPLC,
    "FRE_TAF_CAP_AS_PU-TM9831.pdf": TestType.HPLC,
    "FRE_TM0240B_LAB-53697.pdf": TestType.HPLC,
    "FRE_TM9541A_LAB-53879.pdf": TestType.HPLC,
    "TUA_TM6735A_MCD-058255.pdf": TestType.HPLC,
    # IDENTITY (3 files)
    "AND_ACS_AQ126-LAB-2349.pdf": TestType.IDENTITY,
    "AND_ACS_DYE-LAB-2499.pdf": TestType.IDENTITY,
    "TUA_TM1678A-MCD-055379.pdf": TestType.IDENTITY,
    # TITRATION (2 files)
    "AND_FQ538_LAB-2315.pdf": TestType.TITRATION,
    "FRE_KF_USP_LAB54666.pdf": TestType.TITRATION,
    # LOD (1 file)
    "AND_USP_LOD_LAB-2384.pdf": TestType.LOD,
    # OTHER (6 files — no filename match)
    "AND_BI_STRIP-LAB-2387.pdf": TestType.OTHER,
    "AND_FIX_A280_LAB-20957.pdf": TestType.OTHER,
    "TUA_TM0265A-MCD-006943.pdf": TestType.OTHER,
    "TUA_TM0717A_MCD-007978.pdf": TestType.OTHER,
    "TUA_TM2008A-MCD-056293.pdf": TestType.OTHER,
    "TUA_TM7205A-MCD-057670.pdf": TestType.OTHER,
    "TUA_TM7948A-MCD-058350.pdf": TestType.OTHER,
}

# Mock PDF text for the 12 PDFs that cannot be classified by filename alone.
# These simulate keyword content that would come from real PDF extraction.
MOCK_PDF_TEXT: dict[str, str] = {
    # HPLC — 3 files not caught by filename
    "FRE_TM0240B_LAB-53697.pdf": (
        "HPLC method for assay purity determination. Mobile phase: acetonitrile "
        "and water gradient. Column: C18 reverse phase 250mm. Injection volume "
        "10 uL. UV detection at 220nm wavelength. System suitability test with "
        "resolution factor > 2.0. Peak area calculation for impurities."
    ),
    "FRE_TM9541A_LAB-53879.pdf": (
        "High performance liquid chromatography analysis. Gradient elution with "
        "mobile phase A (0.1% TFA in water) and mobile phase B (acetonitrile). "
        "Retention time of main peak at 8.5 minutes. System suitability: "
        "RSD of peak area < 2.0%. Column temperature 30C."
    ),
    "TUA_TM6735A_MCD-058255.pdf": (
        "Chromatographic purity by HPLC. Isocratic separation using C8 column. "
        "UV detector wavelength 254nm. Injection volume 20uL. Mobile phase "
        "phosphate buffer pH 6.8 with methanol. Peak area normalization."
    ),
    # TITRATION — 1 file not caught by filename
    "AND_FQ538_LAB-2315.pdf": (
        "Moisture content determination by Karl Fischer coulometric titration. "
        "Sample dissolved in methanol. Endpoint detection by potentiometric "
        "measurement. Water content reported as percentage w/w. "
        "Titrant: Hydranal Coulomat AG."
    ),
    # IDENTITY — 1 file not caught by filename
    "TUA_TM1678A-MCD-055379.pdf": (
        "Identification test for potassium. Visual inspection of precipitate "
        "formation. Color reaction with sodium tetraphenylborate. "
        "Identity confirmed by comparison with reference standard."
    ),
    # OTHER — 7 files with non-matching domain text
    "AND_BI_STRIP-LAB-2387.pdf": (
        "Biological indicator strip test. Sterilization validation using "
        "Geobacillus stearothermophilus spore strips. Incubation at 56C "
        "for 48 hours. Growth/no-growth determination."
    ),
    "AND_FIX_A280_LAB-20957.pdf": (
        "UV spectroscopy absorbance measurement at A280nm. Protein concentration "
        "determination using Beer-Lambert law. Extinction coefficient 1.0 for "
        "monoclonal antibody. Fixed pathlength measurement."
    ),
    "TUA_TM0265A-MCD-006943.pdf": (
        "Particle size distribution by light diffraction. Laser diffraction "
        "instrument. Volume-weighted median diameter D50. Sample dispersed in "
        "purified water with sonication."
    ),
    "TUA_TM0717A_MCD-007978.pdf": (
        "Ion chromatography analysis for anion determination. IC system with "
        "conductivity detector. Suppressed ion exchange separation. Eluent: "
        "sodium carbonate/bicarbonate. Chloride and sulfate quantitation."
    ),
    "TUA_TM2008A-MCD-056293.pdf": (
        "Nitrates determination in purified water. Limit test according to "
        "EP 2.4.1. Sulfanilic acid reagent. Comparison with standard "
        "solution. Visual assessment of color intensity."
    ),
    "TUA_TM7205A-MCD-057670.pdf": (
        "Residue on ignition test. Sulfated ash determination per USP 281. "
        "Sample heated in platinum crucible at 600C. Sulfuric acid treatment. "
        "Weight of residue expressed as percentage."
    ),
    "TUA_TM7948A-MCD-058350.pdf": (
        "Residue on ignition determination. Muffle furnace at 600 degrees. "
        "Platinum crucible tared before and after. Sulfated ash percentage "
        "calculated from weight difference."
    ),
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def classifier() -> TestTypeClassifier:
    """Classifier with default threshold (0.8)."""
    return TestTypeClassifier(confidence_threshold=0.8)


# ---------------------------------------------------------------------------
# Step-function confidence tests
# ---------------------------------------------------------------------------
class TestKeywordConfidence:
    def test_zero_matches(self) -> None:
        assert _keyword_confidence(0) == 0.0

    def test_one_match(self) -> None:
        assert _keyword_confidence(1) == 0.55

    def test_two_matches(self) -> None:
        assert _keyword_confidence(2) == 0.75

    def test_three_matches(self) -> None:
        assert _keyword_confidence(3) == 0.85

    def test_four_matches(self) -> None:
        assert _keyword_confidence(4) == 0.88

    def test_five_plus_matches(self) -> None:
        assert _keyword_confidence(5) == 0.92
        assert _keyword_confidence(10) == 0.92


# ---------------------------------------------------------------------------
# Filename classification tests (parametrized)
# ---------------------------------------------------------------------------
# 13 PDFs that should be classifiable by filename
FILENAME_CLASSIFIABLE = [
    ("AND_ASY_HSUCC-LAB-2873.pdf", TestType.HPLC),
    ("AND_BCMA_CEX-LAB-38176.pdf", TestType.HPLC),
    ("FRE_ABRO_B_AS_PU-TM8832A.pdf", TestType.HPLC),
    ("FRE_BOSU_R_ASSAY-TM6687A.pdf", TestType.HPLC),
    ("FRE_BOSU_R_RESO-TM6692A.pdf", TestType.HPLC),
    ("FRE_PALBO_ASY_IMPS-TM8439A.pdf", TestType.HPLC),
    ("FRE_QUI_R_ASPU_ALT-TM0269A.pdf", TestType.HPLC),
    ("FRE_TAF20_C_APU-TM0019B.pdf", TestType.HPLC),
    ("FRE_TAF_CAP_AS_PU-TM9831.pdf", TestType.HPLC),
    ("AND_USP_LOD_LAB-2384.pdf", TestType.LOD),
    ("FRE_KF_USP_LAB54666.pdf", TestType.TITRATION),
    ("AND_ACS_AQ126-LAB-2349.pdf", TestType.IDENTITY),
    ("AND_ACS_DYE-LAB-2499.pdf", TestType.IDENTITY),
]

# 12 PDFs that should NOT be classifiable by filename alone
FILENAME_NOT_CLASSIFIABLE = [
    "FRE_TM0240B_LAB-53697.pdf",
    "FRE_TM9541A_LAB-53879.pdf",
    "TUA_TM6735A_MCD-058255.pdf",
    "AND_FQ538_LAB-2315.pdf",
    "TUA_TM1678A-MCD-055379.pdf",
    "AND_BI_STRIP-LAB-2387.pdf",
    "AND_FIX_A280_LAB-20957.pdf",
    "TUA_TM0265A-MCD-006943.pdf",
    "TUA_TM0717A_MCD-007978.pdf",
    "TUA_TM2008A-MCD-056293.pdf",
    "TUA_TM7205A-MCD-057670.pdf",
    "TUA_TM7948A-MCD-058350.pdf",
]


class TestFilenameClassification:
    @pytest.mark.parametrize("filename,expected_type", FILENAME_CLASSIFIABLE)
    def test_filename_matches(
        self, classifier: TestTypeClassifier, filename: str, expected_type: TestType
    ) -> None:
        result = classifier._classify_by_filename(filename)
        assert result is not None, f"Expected {filename} to match a filename pattern"
        assert result.test_type == expected_type, (
            f"{filename}: expected {expected_type.value}, got {result.test_type.value}"
        )
        assert result.confidence == 0.95
        assert result.method == "filename"

    @pytest.mark.parametrize("filename", FILENAME_NOT_CLASSIFIABLE)
    def test_filename_no_match(
        self, classifier: TestTypeClassifier, filename: str
    ) -> None:
        result = classifier._classify_by_filename(filename)
        assert result is None, (
            f"Expected {filename} NOT to match any filename pattern, "
            f"but got {result.test_type.value if result else 'None'}"
        )

    def test_empty_filename(self, classifier: TestTypeClassifier) -> None:
        result = classifier._classify_by_filename("")
        assert result is None

    def test_none_like_empty(self, classifier: TestTypeClassifier) -> None:
        result = classifier._classify_by_filename("")
        assert result is None


# ---------------------------------------------------------------------------
# Keyword classification tests
# ---------------------------------------------------------------------------
class TestKeywordClassification:
    def test_hplc_keywords(self, classifier: TestTypeClassifier) -> None:
        text = (
            "HPLC analysis with mobile phase gradient elution. "
            "Column C18 250mm. Injection volume 10uL. "
            "UV detection at 220nm wavelength. Peak area normalization."
        )
        result, scores = classifier._classify_by_keywords(text)
        assert result is not None
        assert result.test_type == TestType.HPLC
        assert result.confidence >= 0.85

    def test_lod_keywords(self, classifier: TestTypeClassifier) -> None:
        text = (
            "Loss on drying test. Drying temperature 105C. "
            "Drying time 2 hours. Weight loss calculated. "
            "Sample placed in desiccator to cool."
        )
        result, scores = classifier._classify_by_keywords(text)
        assert result is not None
        assert result.test_type == TestType.LOD
        assert result.confidence >= 0.85

    def test_titration_keywords(self, classifier: TestTypeClassifier) -> None:
        text = (
            "Karl Fischer titration for water content determination. "
            "Coulometric endpoint detection. Titrant consumed measured."
        )
        result, scores = classifier._classify_by_keywords(text)
        assert result is not None
        assert result.test_type == TestType.TITRATION
        assert result.confidence >= 0.85

    def test_identity_keywords(self, classifier: TestTypeClassifier) -> None:
        text = (
            "Identity test by visual inspection. Color reaction observed. "
            "Spectrophotometric confirmation of identification."
        )
        result, scores = classifier._classify_by_keywords(text)
        assert result is not None
        assert result.test_type == TestType.IDENTITY
        assert result.confidence >= 0.85

    def test_empty_text(self, classifier: TestTypeClassifier) -> None:
        result, scores = classifier._classify_by_keywords("")
        assert result is None
        assert scores == {}

    def test_whitespace_only(self, classifier: TestTypeClassifier) -> None:
        result, scores = classifier._classify_by_keywords("   \n\t  ")
        assert result is None


# ---------------------------------------------------------------------------
# Negative pattern tests
# ---------------------------------------------------------------------------
class TestNegativePatterns:
    def test_ion_chromatography_not_hplc(
        self, classifier: TestTypeClassifier
    ) -> None:
        """IC text should NOT classify as HPLC even with shared keywords."""
        text = (
            "Ion chromatography analysis. Column separation with "
            "conductivity detection. Ion exchange mechanism. "
            "Chromatographic peak area calculation."
        )
        result, scores = classifier._classify_by_keywords(text)
        # HPLC should be suppressed by negative pattern
        if result is not None:
            assert result.test_type != TestType.HPLC, (
                "Ion chromatography should not be classified as HPLC"
            )

    def test_residue_on_ignition_not_hplc(
        self, classifier: TestTypeClassifier
    ) -> None:
        """ROI text should NOT classify as HPLC."""
        text = (
            "Residue on ignition test. Sulfated ash determination. "
            "Platinum crucible at 600C."
        )
        result, scores = classifier._classify_by_keywords(text)
        if result is not None:
            assert result.test_type != TestType.HPLC


# ---------------------------------------------------------------------------
# Exclusion classification tests
# ---------------------------------------------------------------------------
class TestExclusionClassification:
    def test_no_keywords_becomes_other(
        self, classifier: TestTypeClassifier
    ) -> None:
        """Text with no meaningful keyword matches → OTHER."""
        text = "Biological indicator strip sterilization validation test."
        result = classifier.classify(text, "unknown_test.pdf")
        assert result.test_type == TestType.OTHER
        assert result.confidence >= 0.8

    def test_empty_text_no_exclusion(
        self, classifier: TestTypeClassifier
    ) -> None:
        """Empty text should not produce exclusion result."""
        result = classifier._classify_by_exclusion("", {})
        assert result is None


# ---------------------------------------------------------------------------
# Full pipeline classify() tests
# ---------------------------------------------------------------------------
class TestFullClassify:
    def test_filename_takes_priority(
        self, classifier: TestTypeClassifier
    ) -> None:
        """Even with LOD keywords, CEX filename → HPLC."""
        result = classifier.classify(
            pdf_text="Loss on drying determination",
            filename="AND_BCMA_CEX-LAB-38176.pdf",
        )
        assert result.test_type == TestType.HPLC
        assert result.method == "filename"

    def test_keywords_when_no_filename(
        self, classifier: TestTypeClassifier
    ) -> None:
        """Keyword classification works when filename doesn't match."""
        result = classifier.classify(
            pdf_text=MOCK_PDF_TEXT["FRE_TM0240B_LAB-53697.pdf"],
            filename="FRE_TM0240B_LAB-53697.pdf",
        )
        assert result.test_type == TestType.HPLC

    def test_exclusion_for_other(
        self, classifier: TestTypeClassifier
    ) -> None:
        """Text with no matching keywords → OTHER via exclusion."""
        result = classifier.classify(
            pdf_text=MOCK_PDF_TEXT["AND_BI_STRIP-LAB-2387.pdf"],
            filename="AND_BI_STRIP-LAB-2387.pdf",
        )
        assert result.test_type == TestType.OTHER

    def test_llm_raises_not_implemented(
        self, classifier: TestTypeClassifier
    ) -> None:
        """LLM path raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match="LLM classification not yet"):
            classifier._classify_by_llm("some text", "file.pdf")


# ---------------------------------------------------------------------------
# Full accuracy gate — all 25 PDFs
# ---------------------------------------------------------------------------
class TestAccuracyGate:
    """Verify >90% accuracy across all 25 demo PDFs with mock text."""

    def test_accuracy_above_90_percent(
        self, classifier: TestTypeClassifier
    ) -> None:
        correct = 0
        total = len(GROUND_TRUTH)
        failures: list[str] = []

        for filename, expected_type in GROUND_TRUTH.items():
            mock_text = MOCK_PDF_TEXT.get(filename, "")
            result = classifier.classify(pdf_text=mock_text, filename=filename)

            if result.test_type == expected_type:
                correct += 1
            else:
                failures.append(
                    f"  {filename}: expected {expected_type.value}, "
                    f"got {result.test_type.value} "
                    f"(method={result.method}, conf={result.confidence})"
                )

        accuracy = correct / total
        min_accuracy = 0.90
        assert accuracy >= min_accuracy, (
            f"Accuracy {accuracy:.1%} ({correct}/{total}) below "
            f"{min_accuracy:.0%} threshold.\nFailures:\n"
            + "\n".join(failures)
        )

    def test_all_25_pdfs_classified(
        self, classifier: TestTypeClassifier
    ) -> None:
        """Every PDF must produce a ClassificationResult (no exceptions)."""
        for filename, expected_type in GROUND_TRUTH.items():
            mock_text = MOCK_PDF_TEXT.get(filename, "")
            result = classifier.classify(pdf_text=mock_text, filename=filename)
            assert isinstance(result, ClassificationResult), (
                f"{filename} did not produce a ClassificationResult"
            )
            assert result.test_type is not None

    @pytest.mark.parametrize(
        "filename,expected_type",
        list(GROUND_TRUTH.items()),
        ids=list(GROUND_TRUTH.keys()),
    )
    def test_individual_pdf_classification(
        self,
        classifier: TestTypeClassifier,
        filename: str,
        expected_type: TestType,
    ) -> None:
        """Each PDF individually classified correctly."""
        mock_text = MOCK_PDF_TEXT.get(filename, "")
        result = classifier.classify(pdf_text=mock_text, filename=filename)
        assert result.test_type == expected_type, (
            f"{filename}: expected {expected_type.value}, "
            f"got {result.test_type.value} "
            f"(method={result.method}, confidence={result.confidence}, "
            f"evidence={result.evidence})"
        )


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------
class TestEdgeCases:
    def test_empty_text_and_filename(
        self, classifier: TestTypeClassifier
    ) -> None:
        """Both empty → LLM path → NotImplementedError."""
        with pytest.raises(NotImplementedError):
            classifier.classify(pdf_text="", filename="")

    def test_whitespace_only_text(
        self, classifier: TestTypeClassifier
    ) -> None:
        """Whitespace-only text with no filename → NotImplementedError."""
        with pytest.raises(NotImplementedError):
            classifier.classify(pdf_text="   \n\t  ", filename="")

    def test_confidence_threshold_respected(self) -> None:
        """Higher threshold means more classifications fall through to LLM."""
        strict = TestTypeClassifier(confidence_threshold=0.99)
        # Filename gives 0.95 confidence, below 0.99 threshold
        with pytest.raises(NotImplementedError):
            strict.classify(
                pdf_text="",
                filename="AND_BCMA_CEX-LAB-38176.pdf",
            )

    def test_classification_result_has_pdf_filename(
        self, classifier: TestTypeClassifier
    ) -> None:
        """Result includes the original filename."""
        result = classifier.classify(
            pdf_text="", filename="AND_BCMA_CEX-LAB-38176.pdf"
        )
        assert result.pdf_filename == "AND_BCMA_CEX-LAB-38176.pdf"

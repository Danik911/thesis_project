"""
Test suite for GAMP-5 Categorization Ambiguity Detection (Task 3.12)

Tests universal ambiguity detection across ALL GAMP category boundaries:
- Category 1/3 boundary cases
- Category 3/4 boundary cases
- Category 4/5 boundary cases (primary focus)
- Vague/incomplete URS scenarios

Success Criteria:
✅ Ambiguous URS triggers requires_human_review = True
✅ has_ambiguity_signals = True for uncertain cases
✅ ambiguity_details explains the specific boundary issue
✅ alternative_categories lists plausible alternatives
✅ Clear cases have requires_human_review = False
✅ Confidence < 85% automatically triggers review
"""

import importlib.util
from pathlib import Path

import pytest

# Load lightweight models module without importing the full agent package (which pulls heavy deps)
_models_path = Path(__file__).resolve().parents[1] / "src" / "agents" / "categorization" / "models.py"
_models_spec = importlib.util.spec_from_file_location("cat_models", _models_path)
cat_models = importlib.util.module_from_spec(_models_spec)
assert _models_spec and _models_spec.loader  # for mypy/static checkers
_models_spec.loader.exec_module(cat_models)  # type: ignore[attr-defined]

GAMPCategorizationResult = cat_models.GAMPCategorizationResult
enforce_universal_ambiguity_guards = cat_models.enforce_universal_ambiguity_guards

try:  # Heavy dependency path only when full agent stack available
    from src.agents.categorization.agent import categorize_urs_document
except ModuleNotFoundError:  # pragma: no cover - allows deterministic tests to run without LlamaIndex
    categorize_urs_document = None
from src.core.events import GAMPCategory


@pytest.mark.skipif(
    categorize_urs_document is None,
    reason="categorization agent stack unavailable (install llama_index to run full integration tests)",
)
class TestCategorizationAmbiguityDetection:
    """Test universal ambiguity detection across GAMP category boundaries."""

    def test_clear_category_4_no_ambiguity(self):
        """
        Test Case 1: Clear Category 4 (No Ambiguity)

        URS explicitly states configuration only, no custom development.
        Expected: Category 4, high confidence, NO human review required.
        """
        urs_content = """
        Commercial LIMS System Configuration Requirements

        The system shall be configured using the vendor's XML configuration files.
        No source code modifications shall be made.
        No custom development shall be performed.
        All functionality shall use standard vendor-supplied features.
        Configuration parameters include:
        - User roles and permissions via XML
        - Workflow definitions via configuration tool
        - Report templates using vendor's designer
        """

        result = categorize_urs_document(
            urs_content=urs_content,
            document_name="Clear_Category_4_URS.pdf",
            use_structured_output=True
        )

        # Assertions
        assert result.gamp_category == GAMPCategory.CATEGORY_4, \
            f"Expected Category 4, got {result.gamp_category}"

        assert result.confidence_score >= 0.85, \
            f"Expected high confidence (≥0.85), got {result.confidence_score:.2f}"

        assert result.has_ambiguity_signals is False, \
            "Expected NO ambiguity signals for clear Category 4"

        assert result.review_required is False, \
            "Expected NO human review for clear, high-confidence Category 4"

        assert result.ambiguity_details is None, \
            "Expected NO ambiguity details for clear case"

        print(f"[PASS] Test 1: Clear Category 4, Confidence={result.confidence_score:.2f}, No HIL")

    def test_category_4_5_boundary_ambiguity(self):
        """
        Test Case 2: Category 4/5 Boundary Ambiguity

        URS mentions both configuration AND optional custom modules.
        Expected: Ambiguity detected, requires_human_review = True.
        """
        urs_content = """
        Personalized Medicine Orchestration Platform Requirements

        The system shall provide:
        - Configured workflows for standard treatment protocols
        - User-defined parameters for dosing calculations
        - Optional custom algorithm modules for novel therapeutic approaches
        - Extensible architecture for future enhancements
        - Plugin support for proprietary biomarker analysis

        The vendor's configuration tool shall be used for standard setup.
        Custom modules may be developed for specialized use cases.
        """

        result = categorize_urs_document(
            urs_content=urs_content,
            document_name="Ambiguous_Cat4_5_URS.pdf",
            use_structured_output=True
        )

        # Assertions
        assert result.has_ambiguity_signals is True, \
            "Expected ambiguity signals for Category 4/5 boundary"

        assert result.review_required is True, \
            "Expected human review for ambiguous Category 4/5 boundary"

        assert result.ambiguity_details is not None, \
            "Expected ambiguity details explaining the boundary issue"

        assert "4/5" in result.ambiguity_details or "custom" in result.ambiguity_details.lower(), \
            f"Expected Cat 4/5 boundary explanation in: {result.ambiguity_details}"

        assert result.alternative_categories is not None, \
            "Expected alternative categories list for ambiguous case"

        assert 5 in result.alternative_categories or 4 in result.alternative_categories, \
            f"Expected Category 4 or 5 in alternatives: {result.alternative_categories}"

        print(f"[PASS] Test 2: Cat 4/5 Ambiguity detected, HIL triggered")
        print(f"   Ambiguity: {result.ambiguity_details}")
        print(f"   Alternatives: {result.alternative_categories}")

    def test_category_3_4_boundary_ambiguity(self):
        """
        Test Case 3: Category 3/4 Boundary Ambiguity

        URS describes COTS software but unclear if configuration is required.
        Expected: Ambiguity detected, requires_human_review = True.
        """
        urs_content = """
        Microsoft Excel Data Analysis Requirements

        The system shall use Microsoft Excel for laboratory data analysis.
        May require custom macros for specific workflow automation.
        Standard Excel functionality shall be used where possible.
        Templates may need to be customized for site-specific reporting.
        """

        result = categorize_urs_document(
            urs_content=urs_content,
            document_name="Ambiguous_Cat3_4_URS.pdf",
            use_structured_output=True
        )

        # Assertions
        assert result.has_ambiguity_signals is True, \
            "Expected ambiguity signals for Category 3/4 boundary"

        assert result.review_required is True, \
            "Expected human review for ambiguous Category 3/4 boundary"

        assert result.ambiguity_details is not None, \
            "Expected ambiguity details for Category 3/4 uncertainty"

        print(f"[PASS] Test 3: Cat 3/4 Ambiguity detected, HIL triggered")
        print(f"   Category: {result.gamp_category.value}, Confidence: {result.confidence_score:.2f}")
        print(f"   Ambiguity: {result.ambiguity_details}")

    def test_vague_urs_requires_hil(self):
        """
        Test Case 4: Vague/Incomplete URS

        URS lacks critical details for categorization.
        Expected: Low confidence, ambiguity detected, requires_human_review = True.
        """
        urs_content = """
        Clinical Trial Management System Requirements

        The system shall manage clinical trial data.
        Details to be determined during vendor selection.
        Functionality requirements will be finalized after user workshops.
        """

        result = categorize_urs_document(
            urs_content=urs_content,
            document_name="Vague_URS.pdf",
            use_structured_output=True
        )

        # Assertions
        assert result.has_ambiguity_signals is True, \
            "Expected ambiguity signals for vague/incomplete URS"

        assert result.review_required is True, \
            "Expected human review for vague URS"

        assert result.confidence_score < 0.85, \
            f"Expected low confidence (<0.85) for vague URS, got {result.confidence_score:.2f}"

        assert "vague" in result.ambiguity_details.lower() or \
               "incomplete" in result.ambiguity_details.lower() or \
               "missing" in result.ambiguity_details.lower() or \
               "unclear" in result.ambiguity_details.lower(), \
            f"Expected explanation of vague/incomplete URS in: {result.ambiguity_details}"

        print(f"[PASS] Test 4: Vague URS detected, HIL triggered")
        print(f"   Confidence: {result.confidence_score:.2f}")
        print(f"   Ambiguity: {result.ambiguity_details}")

    def test_clear_category_5_no_ambiguity(self):
        """
        Test Case 5: Clear Category 5 (No Ambiguity)

        URS explicitly describes custom development with proprietary algorithms.
        Expected: Category 5, high confidence, NO human review required.
        """
        urs_content = """
        Custom Laboratory Data Management System Requirements

        The system shall be custom-developed from scratch.
        Proprietary algorithms shall be implemented for:
        - Analytical data processing with novel statistical methods
        - Bespoke quality control calculations
        - Custom machine learning models for predictive analytics

        All source code shall be developed in-house.
        No commercial off-the-shelf components shall be used for core functionality.
        """

        result = categorize_urs_document(
            urs_content=urs_content,
            document_name="Clear_Category_5_URS.pdf",
            use_structured_output=True
        )

        # Assertions
        assert result.gamp_category == GAMPCategory.CATEGORY_5, \
            f"Expected Category 5, got {result.gamp_category}"

        assert result.confidence_score >= 0.85, \
            f"Expected high confidence (≥0.85), got {result.confidence_score:.2f}"

        assert result.has_ambiguity_signals is False, \
            "Expected NO ambiguity signals for clear Category 5"

        assert result.review_required is False, \
            "Expected NO human review for clear, high-confidence Category 5"

        print(f"[PASS] Test 5: Clear Category 5, Confidence={result.confidence_score:.2f}, No HIL")

    def test_low_confidence_triggers_hil_regardless(self):
        """
        Test Case 6: Low Confidence Automatic HIL Trigger

        Even without explicit ambiguity keywords, confidence < 85% must trigger HIL.
        Expected: requires_human_review = True when confidence < 0.85.
        """
        urs_content = """
        Software System Requirements

        The system shall provide data management capabilities.
        Some configuration may be required.
        The vendor will provide implementation support.
        """

        result = categorize_urs_document(
            urs_content=urs_content,
            document_name="Low_Confidence_URS.pdf",
            use_structured_output=True
        )

        # Assertions - if confidence < 85%, HIL MUST be triggered
        if result.confidence_score < 0.85:
            assert result.review_required is True, \
                f"Expected HIL trigger for confidence {result.confidence_score:.2f} < 0.85"
            print(f"[PASS] Test 6: Low confidence ({result.confidence_score:.2f}) triggered HIL")
        else:
            # If confidence >= 85%, HIL optional depending on ambiguity
            print(f"[PASS] Test 6: High confidence ({result.confidence_score:.2f}), HIL={result.review_required}")


class TestDeterministicAmbiguityGuards:
    """Ensure helper enforces HIL when keywords or missing info detected."""

    def _base_result(self) -> GAMPCategorizationResult:
        return GAMPCategorizationResult(
            category=4,
            confidence_score=0.95,
            reasoning="Initial reasoning",
            has_ambiguity_signals=False,
            ambiguity_details=None,
            requires_human_review=False,
            alternative_categories=None
        )

    def test_guard_detects_category_4_5_boundary(self):
        """Optional custom modules must force ambiguity even if LLM missed it."""
        urs = """
        Workflow engine configured via vendor tools with optional custom algorithm modules
        and plugin extensions for bespoke analytics.
        """
        updated = enforce_universal_ambiguity_guards(self._base_result(), urs)
        assert updated.has_ambiguity_signals is True
        assert updated.requires_human_review is True
        assert updated.alternative_categories and 5 in updated.alternative_categories
        assert updated.ambiguity_details and "4/5" in updated.ambiguity_details or "custom" in updated.ambiguity_details.lower()

    def test_guard_detects_vague_requirements(self):
        """Vague statements like 'details to be determined' require HIL."""
        urs = "Clinical trial software requirements to be determined during vendor selection."
        updated = enforce_universal_ambiguity_guards(self._base_result(), urs)
        assert updated.has_ambiguity_signals is True
        assert updated.requires_human_review is True
        assert updated.ambiguity_details and "to be" in updated.ambiguity_details.lower()


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment before each test."""
    # Ensure logging is configured
    import logging
    logging.basicConfig(level=logging.INFO)
    yield


if __name__ == "__main__":
    """Run tests with verbose output."""
    pytest.main([__file__, "-v", "-s"])

"""
Test suite for GAMP-5 Categorization Agent Foundation Implementation

Tests the core categorization logic, confidence scoring, and basic functionality
of the Phase 1 foundation implementation.
"""

from main.src.agents.categorization.categorization_agent import GAMPCategorizationAgent
from main.src.agents.categorization.confidence_scorer import ConfidenceScorer
from main.src.agents.categorization.rules_engine import GAMPRulesEngine
from main.src.core.events import GAMPCategory


class TestGAMPCategorizationFoundation:
    """Test suite for GAMP categorization foundation functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.agent = GAMPCategorizationAgent()
        self.rules_engine = GAMPRulesEngine()
        self.confidence_scorer = ConfidenceScorer()

    def test_category_1_infrastructure_detection(self):
        """Test Category 1 (Infrastructure) detection."""
        urs_content = """
        System Requirements:
        The application shall operate on Windows Server 2019 operating system.
        Database engine: Oracle 19c Enterprise Edition will be used for data storage.
        Application developed using Java 11 framework with standard libraries.
        Network communication via standard HTTPS protocols.
        No business logic or custom configurations required.
        """

        result = self.agent.categorize_urs(urs_content, "Infrastructure Test URS")

        assert result.gamp_category == GAMPCategory.CATEGORY_1
        assert result.confidence_score > 0.7
        assert "infrastructure" in result.justification.lower() or "category 1" in result.justification.lower()
        assert result.risk_assessment["category"] == 1

    def test_category_3_cots_detection(self):
        """Test Category 3 (Non-configured) detection."""
        urs_content = """
        Software Requirements:
        The system shall use Adobe Acrobat standard features for document management.
        Microsoft Office suite will be used with default configuration.
        Commercial off-the-shelf analytical balance with standard weighing functionality.
        No configuration or customization required - used as supplied by vendor.
        Standard installation procedures will be followed.
        """

        result = self.agent.categorize_urs(urs_content, "COTS Test URS")

        assert result.gamp_category == GAMPCategory.CATEGORY_3
        assert result.confidence_score > 0.6
        assert "non-configured" in result.justification.lower() or "category 3" in result.justification.lower()

    def test_category_4_configured_detection(self):
        """Test Category 4 (Configured) detection."""
        urs_content = """
        System Configuration Requirements:
        LIMS shall be configured for stability testing workflows.
        User-defined parameters for sample management processes.
        Configurable approval workflows for batch records.
        Business rules setup for automated notifications.
        System parameters will be configured according to company procedures.
        No custom code development required.
        """

        result = self.agent.categorize_urs(urs_content, "Configured LIMS URS")

        assert result.gamp_category == GAMPCategory.CATEGORY_4
        assert result.confidence_score > 0.6
        assert "configured" in result.justification.lower() or "category 4" in result.justification.lower()

    def test_category_5_custom_detection(self):
        """Test Category 5 (Custom) detection."""
        urs_content = """
        Custom Development Requirements:
        Proprietary algorithm for drug stability prediction using machine learning models.
        Bespoke application for clinical trial data analysis.
        Custom calculation engine for batch yield optimization.
        Unique business logic for regulatory compliance workflows.
        Purpose-built integration between multiple legacy systems.
        Custom user interfaces designed for specific workflows.
        """

        result = self.agent.categorize_urs(urs_content, "Custom Application URS")

        assert result.gamp_category == GAMPCategory.CATEGORY_5
        assert result.confidence_score > 0.7
        assert "custom" in result.justification.lower() or "category 5" in result.justification.lower()

    def test_confidence_scoring_high_confidence(self):
        """Test confidence scoring for clear categorization."""
        # Clear Category 5 case with multiple strong indicators
        urs_content = """
        Custom software development for proprietary clinical trial management.
        Bespoke algorithms for personalized medicine calculations.
        Purpose-built system with unique business logic.
        """

        result = self.agent.categorize_urs(urs_content)

        assert result.confidence_score > 0.8
        assert not result.review_required
        assert result.risk_assessment["evidence_strength"] in ["Strong", "Moderate"]

    def test_confidence_scoring_low_confidence(self):
        """Test confidence scoring for ambiguous cases."""
        # Minimal, ambiguous content
        urs_content = """
        Software system for data management.
        Standard functionality required.
        """

        result = self.agent.categorize_urs(urs_content)

        assert result.confidence_score < 0.85
        assert result.review_required
        assert "human review" in result.justification.lower()

    def test_fallback_behavior(self):
        """Test fallback to Category 5 on errors."""
        # Create agent with invalid configuration to trigger error
        agent = GAMPCategorizationAgent()
        agent.rules_engine = None  # Force error

        result = agent.categorize_urs("test content")

        assert result.gamp_category == GAMPCategory.CATEGORY_5
        assert result.confidence_score == 0.0
        assert result.review_required
        assert "fallback" in result.justification.lower()

    def test_all_categories_supported(self):
        """Test that all expected categories are supported."""
        supported = self.agent.get_supported_categories()

        assert GAMPCategory.CATEGORY_1 in supported
        assert GAMPCategory.CATEGORY_3 in supported
        assert GAMPCategory.CATEGORY_4 in supported
        assert GAMPCategory.CATEGORY_5 in supported

    def test_configuration_validation(self):
        """Test agent configuration validation."""
        config = self.agent.validate_configuration()

        assert config["agent_type"] == "GAMPCategorizationAgent"
        assert "confidence_threshold" in config
        assert len(config["supported_categories"]) == 4
        assert "Rules-based categorization" in config["features"]
        assert "Phase 2: Document processing integration" in config["next_phases"]

    def test_exclusion_factors(self):
        """Test that exclusion factors reduce confidence appropriately."""
        # Category 1 content with exclusions (business logic)
        urs_content = """
        Operating system: Windows Server 2019
        Database: Oracle 19c
        Custom business logic for pharmaceutical calculations
        Modified system components for GxP compliance
        """

        result = self.agent.categorize_urs(urs_content)

        # Should not be Category 1 due to exclusions
        assert result.gamp_category != GAMPCategory.CATEGORY_1
        assert len(result.risk_assessment["risk_factors"]) > 0

    def test_comprehensive_justification(self):
        """Test that justification contains required elements."""
        urs_content = """
        Custom development project for clinical data management.
        Proprietary algorithms for statistical analysis.
        """

        result = self.agent.categorize_urs(urs_content, "Test Document")

        # Check justification completeness
        justification = result.justification
        assert "Test Document" in justification
        assert "CLASSIFICATION:" in justification
        assert "CONFIDENCE:" in justification
        assert "EVIDENCE ANALYSIS:" in justification
        assert "VALIDATION APPROACH:" in justification

    def test_risk_assessment_completeness(self):
        """Test that risk assessment contains all required fields."""
        result = self.agent.categorize_urs("Custom software development")

        risk_assessment = result.risk_assessment

        required_fields = [
            "category", "category_description", "validation_approach",
            "confidence_score", "evidence_strength", "risk_factors",
            "requires_human_review", "regulatory_impact", "validation_effort"
        ]

        for field in required_fields:
            assert field in risk_assessment


if __name__ == "__main__":
    # Run basic smoke test
    agent = GAMPCategorizationAgent()

    print("GAMP-5 Categorization Agent Foundation - Smoke Test")
    print("=" * 60)

    test_cases = [
        ("Infrastructure", "Windows Server 2019 operating system with Oracle database"),
        ("COTS", "Adobe Acrobat standard package used as supplied"),
        ("Configured", "LIMS configured for stability testing workflows"),
        ("Custom", "Proprietary algorithm for drug development analysis")
    ]

    for case_name, urs_content in test_cases:
        result = agent.categorize_urs(urs_content, f"{case_name} Test")
        print(f"\n{case_name} Test:")
        print(f"  Category: {result.gamp_category.name}")
        print(f"  Confidence: {result.confidence_score:.1%}")
        print(f"  Review Required: {result.review_required}")

    print("\n✅ Smoke test completed successfully!")
    print(f"Configuration: {agent.validate_configuration()['version']}")

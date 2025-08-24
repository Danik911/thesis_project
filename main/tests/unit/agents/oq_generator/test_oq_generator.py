"""
Unit tests for OQ test generator core functionality.

Tests the core test generation logic, LLMTextCompletionProgram integration,
and pharmaceutical compliance validation.
"""

from unittest.mock import MagicMock, patch

import pytest
from llama_index.llms.openai import OpenAI
from src.agents.oq_generator.generator import (
    GAMPValidationError,
    OQTestGenerator,
    TestGenerationFailure,
)
from src.agents.oq_generator.models import (
    OQGenerationConfig,
    OQTestCase,
    OQTestSuite,
    TestStep,
)
from src.core.events import GAMPCategory


class TestOQTestGenerator:
    """Test OQ test generator core functionality."""

    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM for testing."""
        llm = MagicMock(spec=OpenAI)
        return llm

    @pytest.fixture
    def generator(self, mock_llm):
        """Create OQ test generator instance."""
        return OQTestGenerator(llm=mock_llm, verbose=True)

    @pytest.fixture
    def valid_test_suite_category_3(self):
        """Create valid Category 3 test suite."""
        test_steps = [
            TestStep(
                step_number=1,
                action="Execute system functionality test",
                expected_result="System responds correctly"
            )
        ]

        test_cases = []
        for i in range(7):  # Valid Category 3 count
            test_case = OQTestCase(
                test_id=f"OQ-{i+1:03d}",
                test_name=f"Functional Test {i+1}",
                test_category="functional",
                gamp_category=3,
                objective=f"Verify functionality {i+1}",
                test_steps=test_steps,
                acceptance_criteria=[f"Function {i+1} works correctly"]
            )
            test_cases.append(test_case)

        return OQTestSuite(
            suite_id="OQ-SUITE-0001",
            gamp_category=3,
            document_name="Test Document",
            test_cases=test_cases,
            total_test_count=7,
            estimated_execution_time=210
        )

    def test_generator_initialization(self, mock_llm):
        """Test generator initialization."""
        generator = OQTestGenerator(llm=mock_llm, verbose=True)

        assert generator.llm == mock_llm
        assert generator.verbose is True
        assert generator._generation_program is None
        assert generator._last_generation_context is None

    def test_gamp_category_validation_success(self, generator):
        """Test successful GAMP category validation."""
        # Should not raise for valid categories
        generator._validate_gamp_category(GAMPCategory.CATEGORY_1)
        generator._validate_gamp_category(GAMPCategory.CATEGORY_3)
        generator._validate_gamp_category(GAMPCategory.CATEGORY_4)
        generator._validate_gamp_category(GAMPCategory.CATEGORY_5)

    def test_gamp_category_validation_failure(self, generator):
        """Test GAMP category validation failure."""
        # Mock an invalid category (not in requirements)
        invalid_category = MagicMock()
        invalid_category.value = 99

        with patch("src.agents.oq_generator.templates.GAMPCategoryConfig.CATEGORY_REQUIREMENTS", {}):
            with pytest.raises(GAMPValidationError) as exc_info:
                generator._validate_gamp_category(invalid_category)

            assert "Unsupported GAMP category" in str(exc_info.value)
            assert exc_info.value.error_context["no_fallback_available"] is True

    def test_context_summary_preparation_empty(self, generator):
        """Test context summary preparation with empty context."""
        summary = generator._prepare_context_summary(None)
        assert summary == "Standard pharmaceutical validation approach recommended"

        summary = generator._prepare_context_summary({})
        assert summary == "Standard pharmaceutical validation approach recommended"

    def test_context_summary_preparation_with_data(self, generator):
        """Test context summary preparation with context data."""
        context_data = {
            "sme_insights": {
                "expertise_areas": {"validation": 0.9, "compliance": 0.8}
            },
            "research_findings": {
                "regulatory_updates": ["Update 1", "Update 2"]
            },
            "context_provider_result": {
                "confidence_score": 0.85,
                "regulatory_documents": ["Doc 1", "Doc 2", "Doc 3"]
            },
            "validation_context": {
                "test_strategy_alignment": {"risk_based": True, "data_integrity": True}
            }
        }

        summary = generator._prepare_context_summary(context_data)

        assert "SME Expertise: 2 specialized areas" in summary
        assert "Regulatory Updates: 2 recent changes" in summary
        assert "Context Quality: 85.0%" in summary
        assert "Regulatory Context: 3 documents" in summary
        assert "Test Strategy: risk_based, data_integrity" in summary

    def test_context_summary_error_handling(self, generator):
        """Test context summary handles errors gracefully."""
        # Invalid context data that would cause errors
        invalid_context = {
            "sme_insights": "not a dict",  # Should be dict
            "research_findings": None      # Unexpected None
        }

        # Should not raise exception, but return fallback
        summary = generator._prepare_context_summary(invalid_context)
        assert "Context aggregation failed" in summary

    @patch("src.agents.oq_generator.generator.LLMTextCompletionProgram")
    def test_structured_output_generation_success(self, mock_program_class, generator, valid_test_suite_category_3):
        """Test successful structured output generation."""
        # Mock the program instance
        mock_program = MagicMock()
        mock_program.return_value = valid_test_suite_category_3
        mock_program_class.from_defaults.return_value = mock_program

        # Execute generation
        result = generator._generate_with_structured_output(
            gamp_category=GAMPCategory.CATEGORY_3,
            urs_content="Test URS content for generation",
            document_name="Test Document",
            test_count=7,
            context_summary="Test context summary",
            category_config={"min_tests": 5, "max_tests": 10}
        )

        # Verify result
        assert result == valid_test_suite_category_3
        assert generator._generation_program == mock_program
        assert generator._last_generation_context["gamp_category"] == 3

    @patch("src.agents.oq_generator.generator.LLMTextCompletionProgram")
    def test_structured_output_generation_failure(self, mock_program_class, generator):
        """Test structured output generation failure with NO fallbacks."""
        # Mock program to raise exception
        mock_program = MagicMock()
        mock_program.side_effect = Exception("LLM generation failed")
        mock_program_class.from_defaults.return_value = mock_program

        # Should raise TestGenerationFailure, NO fallbacks
        with pytest.raises(TestGenerationFailure) as exc_info:
            generator._generate_with_structured_output(
                gamp_category=GAMPCategory.CATEGORY_3,
                urs_content="Test content",
                document_name="Test Document",
                test_count=7,
                context_summary="Test summary",
                category_config={"min_tests": 5, "max_tests": 10}
            )

        assert "LLM test generation failed" in str(exc_info.value)
        assert exc_info.value.error_context["no_fallback_available"] is True

    @patch("src.agents.oq_generator.generator.LLMTextCompletionProgram")
    def test_structured_output_invalid_type_return(self, mock_program_class, generator):
        """Test handling of invalid return type from LLM."""
        # Mock program to return wrong type
        mock_program = MagicMock()
        mock_program.return_value = "invalid string result"  # Should be OQTestSuite
        mock_program_class.from_defaults.return_value = mock_program

        # Should raise TestGenerationFailure
        with pytest.raises(TestGenerationFailure) as exc_info:
            generator._generate_with_structured_output(
                gamp_category=GAMPCategory.CATEGORY_3,
                urs_content="Test content",
                document_name="Test Document",
                test_count=7,
                context_summary="Test summary",
                category_config={"min_tests": 5, "max_tests": 10}
            )

        assert "returned invalid type" in str(exc_info.value)
        assert "expected_type" in exc_info.value.error_context

    def test_generated_suite_validation_success(self, generator, valid_test_suite_category_3):
        """Test successful validation of generated test suite."""
        # Should not raise exception for valid suite
        generator._validate_generated_suite(
            test_suite=valid_test_suite_category_3,
            expected_category=GAMPCategory.CATEGORY_3,
            expected_count=7
        )

    def test_generated_suite_validation_category_mismatch(self, generator, valid_test_suite_category_3):
        """Test validation failure for GAMP category mismatch."""
        with pytest.raises(TestGenerationFailure) as exc_info:
            generator._validate_generated_suite(
                test_suite=valid_test_suite_category_3,
                expected_category=GAMPCategory.CATEGORY_4,  # Mismatch
                expected_count=7
            )

        assert "GAMP category mismatch" in str(exc_info.value)
        assert "expected 4, got 3" in str(exc_info.value)

    def test_generated_suite_validation_count_mismatch(self, generator, valid_test_suite_category_3):
        """Test validation failure for test count mismatch."""
        with pytest.raises(TestGenerationFailure) as exc_info:
            generator._validate_generated_suite(
                test_suite=valid_test_suite_category_3,
                expected_category=GAMPCategory.CATEGORY_3,
                expected_count=10  # Mismatch
            )

        assert "Test count mismatch" in str(exc_info.value)
        assert "expected 10, got 7" in str(exc_info.value)

    def test_generated_suite_validation_duplicate_ids(self, generator):
        """Test validation catches duplicate test IDs."""
        # Create suite with duplicate IDs
        test_steps = [TestStep(step_number=1, action="Test action", expected_result="Test result")]
        duplicate_test_cases = [
            OQTestCase(
                test_id="OQ-001",  # Duplicate ID
                test_name="Test 1",
                test_category="functional",
                gamp_category=3,
                objective="Test objective",
                test_steps=test_steps,
                acceptance_criteria=["Pass criteria"]
            ),
            OQTestCase(
                test_id="OQ-001",  # Duplicate ID
                test_name="Test 2",
                test_category="functional",
                gamp_category=3,
                objective="Test objective",
                test_steps=test_steps,
                acceptance_criteria=["Pass criteria"]
            )
        ]

        invalid_suite = OQTestSuite(
            suite_id="OQ-SUITE-0001",
            gamp_category=3,
            document_name="Test Document",
            test_cases=duplicate_test_cases,
            total_test_count=2
        )

        with pytest.raises(TestGenerationFailure) as exc_info:
            generator._validate_generated_suite(
                test_suite=invalid_suite,
                expected_category=GAMPCategory.CATEGORY_3,
                expected_count=2
            )

        assert "Duplicate test IDs found" in str(exc_info.value)

    def test_alcoa_compliance_validation(self, generator, valid_test_suite_category_3):
        """Test ALCOA+ compliance validation."""
        # Add traceability to meet ALCOA requirements
        for test_case in valid_test_suite_category_3.test_cases:
            test_case.urs_requirements = ["REQ-001", "REQ-002"]

        is_compliant = generator._validate_alcoa_compliance(valid_test_suite_category_3)
        assert is_compliant is True

    def test_alcoa_compliance_validation_insufficient_traceability(self, generator, valid_test_suite_category_3):
        """Test ALCOA+ compliance fails with insufficient traceability."""
        # Only add traceability to some tests (less than 80%)
        valid_test_suite_category_3.test_cases[0].urs_requirements = ["REQ-001"]
        # Leave others without traceability

        is_compliant = generator._validate_alcoa_compliance(valid_test_suite_category_3)
        assert is_compliant is False

    def test_cfr_part11_compliance_category_4(self, generator):
        """Test CFR Part 11 compliance validation for Category 4."""
        # Create Category 4 test suite with required test types
        test_steps = [TestStep(step_number=1, action="Test action", expected_result="Result")]
        test_cases = [
            OQTestCase(
                test_id="OQ-001",
                test_name="Data Integrity Test",
                test_category="data_integrity",  # Required for CFR Part 11
                gamp_category=4,
                objective="Verify data integrity",
                test_steps=test_steps,
                acceptance_criteria=["Data integrity maintained"]
            ),
            OQTestCase(
                test_id="OQ-002",
                test_name="Security Test",
                test_category="security",  # Required for CFR Part 11
                gamp_category=4,
                objective="Verify security controls",
                test_steps=test_steps,
                acceptance_criteria=["Security controls work"]
            )
        ]

        category_4_suite = OQTestSuite(
            suite_id="OQ-SUITE-0001",
            gamp_category=4,
            document_name="Category 4 Document",
            test_cases=test_cases,
            total_test_count=2
        )

        is_compliant = generator._validate_cfr_part11_compliance(category_4_suite)
        assert is_compliant is True

    def test_cfr_part11_compliance_missing_security_tests(self, generator):
        """Test CFR Part 11 compliance fails without security tests."""
        test_steps = [TestStep(step_number=1, action="Test action", expected_result="Result")]
        test_cases = [
            OQTestCase(
                test_id="OQ-001",
                test_name="Data Integrity Test",
                test_category="data_integrity",
                gamp_category=4,
                objective="Test objective",
                test_steps=test_steps,
                acceptance_criteria=["Pass criteria"]
            )
            # Missing security test for Category 4
        ]

        incomplete_suite = OQTestSuite(
            suite_id="OQ-SUITE-0001",
            gamp_category=4,
            document_name="Test Document",
            test_cases=test_cases,
            total_test_count=1
        )

        is_compliant = generator._validate_cfr_part11_compliance(incomplete_suite)
        assert is_compliant is False

    def test_data_integrity_validation(self, generator):
        """Test data integrity validation."""
        test_steps = [
            TestStep(
                step_number=1,
                action="Verify audit trail capture during data entry",
                expected_result="Audit trail records all data changes"
            )
        ]

        test_cases = [
            OQTestCase(
                test_id="OQ-001",
                test_name="Data Integrity Test",
                test_category="data_integrity",
                gamp_category=4,
                objective="Test data integrity",
                test_steps=test_steps,
                acceptance_criteria=["Data integrity maintained"],
                data_integrity_requirements=["ALCOA+", "Audit Trail"]
            )
        ]

        suite_with_di = OQTestSuite(
            suite_id="OQ-SUITE-0001",
            gamp_category=4,
            document_name="Test Document",
            test_cases=test_cases,
            total_test_count=1
        )

        is_valid = generator._validate_data_integrity(suite_with_di)
        assert is_valid is True

    @patch("src.agents.oq_generator.templates.GAMPCategoryConfig.get_category_config")
    @patch.object(OQTestGenerator, "_generate_with_structured_output")
    @patch.object(OQTestGenerator, "_validate_generated_suite")
    def test_full_generation_workflow_success(self, mock_validate, mock_generate, mock_config, generator, valid_test_suite_category_3):
        """Test complete generation workflow success."""
        # Setup mocks
        mock_config.return_value = {"min_tests": 5, "max_tests": 10, "description": "Non-configured Products"}
        mock_generate.return_value = valid_test_suite_category_3
        mock_validate.return_value = None  # No validation errors

        # Execute full generation
        result = generator.generate_oq_test_suite(
            gamp_category=GAMPCategory.CATEGORY_3,
            urs_content="Test URS content with sufficient detail for generation",
            document_name="Test URS Document",
            context_data={
                "sme_insights": {"expertise_areas": {"validation": 0.9}}
            }
        )

        # Verify result
        assert isinstance(result, OQTestSuite)
        assert result.gamp_category == 3
        assert result.total_test_count == 7

        # Verify compliance flags were set
        assert "alcoa_plus_compliant" in result.pharmaceutical_compliance
        assert "gamp5_compliant" in result.pharmaceutical_compliance

    def test_generation_with_custom_config(self, generator):
        """Test generation with custom configuration."""
        config = OQGenerationConfig(
            gamp_category=3,
            document_name="Custom Config Test",
            target_test_count=8,
            complexity_level="comprehensive",
            focus_areas=["data_integrity", "security"],
            require_traceability=True
        )

        with patch.object(generator, "_generate_with_structured_output") as mock_generate:
            with patch("src.agents.oq_generator.templates.GAMPCategoryConfig.get_category_config") as mock_config:
                mock_config.return_value = {"min_tests": 5, "max_tests": 10}
                mock_generate.return_value = MagicMock(spec=OQTestSuite)

                # Should use config target_test_count
                generator.generate_oq_test_suite(
                    gamp_category=GAMPCategory.CATEGORY_3,
                    urs_content="Test content",
                    document_name="Test Document",
                    config=config
                )

                # Verify custom test count was used
                mock_generate.assert_called_once()
                args = mock_generate.call_args[1]
                assert args["test_count"] == 8

    def test_generation_config_validation_failure(self, generator):
        """Test generation fails with invalid config test count."""
        config = OQGenerationConfig(
            gamp_category=3,
            document_name="Invalid Config Test",
            target_test_count=15  # Above maximum of 10 for Category 3
        )

        with patch("src.agents.oq_generator.templates.GAMPCategoryConfig.get_category_config") as mock_config:
            mock_config.return_value = {"min_tests": 5, "max_tests": 10}

            with pytest.raises(GAMPValidationError) as exc_info:
                generator.generate_oq_test_suite(
                    gamp_category=GAMPCategory.CATEGORY_3,
                    urs_content="Test content",
                    document_name="Test Document",
                    config=config
                )

            assert "outside valid range 5-10" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

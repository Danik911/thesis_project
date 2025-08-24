"""
Unit tests for OQ generator Pydantic models.

Tests the schema correctness, validation logic, and compliance requirements
of OQ test generation data models.
"""


import pytest
from pydantic import ValidationError
from src.agents.oq_generator.models import (
    OQGenerationConfig,
    OQTestCase,
    OQTestSuite,
    TestStep,
)


class TestTestStep:
    """Test TestStep model validation and behavior."""

    def test_valid_test_step(self):
        """Test creating a valid test step."""
        step = TestStep(
            step_number=1,
            action="Navigate to the main dashboard and verify display",
            expected_result="Dashboard displays with all required widgets",
            data_to_capture=["screenshot", "timestamp"],
            verification_method="visual_inspection",
            acceptance_criteria="All widgets visible and functional"
        )

        assert step.step_number == 1
        assert len(step.action) >= 10
        assert len(step.expected_result) >= 10
        assert step.data_to_capture == ["screenshot", "timestamp"]

    def test_invalid_short_action(self):
        """Test validation fails for short action text."""
        with pytest.raises(ValidationError) as exc_info:
            TestStep(
                step_number=1,
                action="Click",  # Too short
                expected_result="System responds correctly"
            )

        assert "Test steps must contain detailed pharmaceutical procedures" in str(exc_info.value)

    def test_invalid_short_expected_result(self):
        """Test validation fails for short expected result."""
        with pytest.raises(ValidationError) as exc_info:
            TestStep(
                step_number=1,
                action="Navigate to the main dashboard",
                expected_result="OK"  # Too short
            )

        assert "Test steps must contain detailed pharmaceutical procedures" in str(exc_info.value)


class TestOQTestCase:
    """Test OQTestCase model validation and behavior."""

    def create_valid_test_steps(self):
        """Create valid test steps for testing."""
        return [
            TestStep(
                step_number=1,
                action="Initialize system and navigate to test module",
                expected_result="Test module loads successfully with all functions available"
            ),
            TestStep(
                step_number=2,
                action="Execute primary test workflow with sample data",
                expected_result="Workflow completes without errors and generates expected output"
            )
        ]

    def test_valid_oq_test_case(self):
        """Test creating a valid OQ test case."""
        test_case = OQTestCase(
            test_id="OQ-001",
            test_name="System Installation Verification",
            test_category="installation",
            gamp_category=4,
            objective="Verify system installation meets requirements",
            test_steps=self.create_valid_test_steps(),
            acceptance_criteria=["System installed correctly", "All components functional"],
            regulatory_basis=["GAMP-5", "21 CFR Part 11"],
            urs_requirements=["REQ-001", "REQ-002"]
        )

        assert test_case.test_id == "OQ-001"
        assert test_case.gamp_category == 4
        assert len(test_case.test_steps) == 2
        assert len(test_case.acceptance_criteria) >= 1

    def test_invalid_test_id_format(self):
        """Test validation fails for invalid test ID format."""
        with pytest.raises(ValidationError) as exc_info:
            OQTestCase(
                test_id="TEST-001",  # Wrong format
                test_name="Test Case",
                test_category="functional",
                gamp_category=3,
                objective="Test system functionality",
                test_steps=self.create_valid_test_steps(),
                acceptance_criteria=["Success criteria"]
            )

        assert "Test ID must follow format 'OQ-XXX'" in str(exc_info.value)

    def test_test_steps_sequential_validation(self):
        """Test validation of sequential test step numbering."""
        invalid_steps = [
            TestStep(step_number=1, action="First step action", expected_result="First result"),
            TestStep(step_number=3, action="Third step action", expected_result="Third result")  # Skip 2
        ]

        with pytest.raises(ValidationError) as exc_info:
            OQTestCase(
                test_id="OQ-002",
                test_name="Sequential Test",
                test_category="functional",
                gamp_category=3,
                objective="Test sequential step validation",
                test_steps=invalid_steps,
                acceptance_criteria=["Steps execute in order"]
            )

        assert "Test steps must be sequentially numbered" in str(exc_info.value)

    def test_empty_test_steps_validation(self):
        """Test validation fails for empty test steps."""
        with pytest.raises(ValidationError) as exc_info:
            OQTestCase(
                test_id="OQ-003",
                test_name="Empty Steps Test",
                test_category="functional",
                gamp_category=3,
                objective="Test empty steps validation",
                test_steps=[],  # Empty list
                acceptance_criteria=["Some criteria"]
            )

        assert "Test case must contain at least one test step" in str(exc_info.value)


class TestOQTestSuite:
    """Test OQTestSuite model validation and behavior."""

    def create_valid_test_cases(self, count: int, gamp_category: int):
        """Create valid test cases for testing."""
        test_cases = []
        for i in range(count):
            test_id = f"OQ-{i+1:03d}"
            test_case = OQTestCase(
                test_id=test_id,
                test_name=f"Test Case {i+1}",
                test_category="functional",
                gamp_category=gamp_category,
                objective=f"Verify functionality for test case {i+1}",
                test_steps=[
                    TestStep(
                        step_number=1,
                        action=f"Execute test procedure {i+1}",
                        expected_result=f"Test {i+1} completes successfully"
                    )
                ],
                acceptance_criteria=[f"Test {i+1} passes all criteria"]
            )
            test_cases.append(test_case)
        return test_cases

    def test_valid_gamp_category_3_suite(self):
        """Test creating valid Category 3 test suite."""
        test_cases = self.create_valid_test_cases(7, 3)  # Valid range 5-10

        suite = OQTestSuite(
            suite_id="OQ-SUITE-0001",
            gamp_category=3,
            document_name="Test Document",
            test_cases=test_cases,
            total_test_count=7,
            estimated_execution_time=180  # Required field
        )

        assert suite.gamp_category == 3
        assert suite.total_test_count == 7
        assert len(suite.test_cases) == 7

    def test_valid_gamp_category_4_suite(self):
        """Test creating valid Category 4 test suite."""
        test_cases = self.create_valid_test_cases(18, 4)  # Valid range 15-20

        suite = OQTestSuite(
            suite_id="OQ-SUITE-0002",
            gamp_category=4,
            document_name="Test Document",
            test_cases=test_cases,
            total_test_count=18,
            estimated_execution_time=540  # Required field
        )

        assert suite.gamp_category == 4
        assert suite.total_test_count == 18
        assert len(suite.test_cases) == 18

    def test_valid_gamp_category_5_suite(self):
        """Test creating valid Category 5 test suite."""
        test_cases = self.create_valid_test_cases(27, 5)  # Valid range 25-30

        suite = OQTestSuite(
            suite_id="OQ-SUITE-0003",
            gamp_category=5,
            document_name="Test Document",
            test_cases=test_cases,
            total_test_count=27,
            estimated_execution_time=810  # Required field
        )

        assert suite.gamp_category == 5
        assert suite.total_test_count == 27
        assert len(suite.test_cases) == 27

    def test_insufficient_tests_category_3(self):
        """Test validation fails for insufficient tests in Category 3."""
        test_cases = self.create_valid_test_cases(3, 3)  # Below minimum of 5

        with pytest.raises(ValidationError) as exc_info:
            OQTestSuite(
                suite_id="OQ-SUITE-0004",
                gamp_category=3,
                document_name="Test Document",
                test_cases=test_cases,
                total_test_count=3,
                estimated_execution_time=90
            )

        error_msg = str(exc_info.value)
        assert "requires minimum 5 tests" in error_msg
        assert "NO fallback values available" in error_msg

    def test_excessive_tests_category_4(self):
        """Test validation fails for excessive tests in Category 4."""
        test_cases = self.create_valid_test_cases(25, 4)  # Above maximum of 20

        with pytest.raises(ValidationError) as exc_info:
            OQTestSuite(
                suite_id="OQ-SUITE-0005",
                gamp_category=4,
                document_name="Test Document",
                test_cases=test_cases,
                total_test_count=25,
                estimated_execution_time=750
            )

        error_msg = str(exc_info.value)
        assert "allows maximum 20 tests" in error_msg
        assert "NO fallback values available" in error_msg

    def test_invalid_gamp_category(self):
        """Test validation fails for invalid GAMP category."""
        test_cases = self.create_valid_test_cases(10, 6)  # Invalid category 6

        with pytest.raises(ValidationError) as exc_info:
            OQTestSuite(
                suite_id="OQ-SUITE-0006",
                gamp_category=6,  # Invalid category
                document_name="Test Document",
                test_cases=test_cases,
                total_test_count=10,
                estimated_execution_time=300
            )

        error_msg = str(exc_info.value)
        assert "Invalid GAMP category 6" in error_msg
        assert "Valid categories: [1, 3, 4, 5]" in error_msg

    def test_pharmaceutical_compliance_validation(self):
        """Test pharmaceutical compliance requirements validation."""
        test_cases = self.create_valid_test_cases(7, 3)

        suite = OQTestSuite(
            suite_id="OQ-SUITE-0007",
            gamp_category=3,
            document_name="Test Document",
            test_cases=test_cases,
            total_test_count=7,
            estimated_execution_time=210
        )

        # Should initialize required compliance flags as False
        required_flags = [
            "alcoa_plus_compliant",
            "cfr_part11_compliant",
            "gamp5_compliant",
            "audit_trail_verified",
            "data_integrity_validated"
        ]

        for flag in required_flags:
            assert flag in suite.pharmaceutical_compliance
            assert suite.pharmaceutical_compliance[flag] is False

    def test_coverage_metrics_calculation(self):
        """Test coverage metrics calculation functionality."""
        test_cases = self.create_valid_test_cases(5, 3)

        # Add some variety to test categories and risk levels
        test_cases[0].test_category = "installation"
        test_cases[0].risk_level = "high"
        test_cases[1].test_category = "security"
        test_cases[1].risk_level = "critical"
        test_cases[2].estimated_duration_minutes = 45

        suite = OQTestSuite(
            suite_id="OQ-SUITE-0008",
            gamp_category=3,
            document_name="Test Document",
            test_cases=test_cases,
            total_test_count=5,
            estimated_execution_time=150
        )

        metrics = suite.calculate_coverage_metrics()

        assert "category_distribution" in metrics
        assert "risk_distribution" in metrics
        assert "total_execution_time_minutes" in metrics
        assert "average_test_complexity" in metrics
        assert metrics["total_test_steps"] >= 5  # At least one step per test


class TestOQGenerationConfig:
    """Test OQGenerationConfig model validation and behavior."""

    def test_valid_config_category_3(self):
        """Test creating valid configuration for Category 3."""
        config = OQGenerationConfig(
            gamp_category=3,
            document_name="Test URS Document",
            target_test_count=8,  # Valid range 5-10
            complexity_level="standard",
            focus_areas=["functional_testing", "data_integrity"]
        )

        assert config.gamp_category == 3
        assert config.target_test_count == 8
        assert config.complexity_level == "standard"

    def test_invalid_test_count_for_category(self):
        """Test validation fails for invalid test count for category."""
        with pytest.raises(ValidationError) as exc_info:
            OQGenerationConfig(
                gamp_category=4,
                document_name="Test Document",
                target_test_count=25  # Above maximum of 20 for Category 4
            )

        error_msg = str(exc_info.value)
        assert "requires 15-20 tests" in error_msg
        assert "NO automatic adjustment available" in error_msg

    def test_configuration_constraints(self):
        """Test configuration constraint validation."""
        config = OQGenerationConfig(
            gamp_category=5,
            document_name="Custom Application URS",
            target_test_count=28,
            max_steps_per_test=15,
            min_execution_time=20,
            max_execution_time=90,
            require_traceability=True,
            include_negative_testing=True,
            validate_data_integrity=True
        )

        assert config.max_steps_per_test == 15
        assert config.min_execution_time == 20
        assert config.max_execution_time == 90
        assert config.require_traceability is True
        assert config.include_negative_testing is True
        assert config.validate_data_integrity is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

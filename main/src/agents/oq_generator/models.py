"""
Pydantic models for OQ test generation structures.

This module defines the data models used for Operational Qualification (OQ)
test generation, including test cases, test steps, and test suites with
GAMP-5 compliance validation and pharmaceutical regulatory requirements.
"""

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class TestStep(BaseModel):
    """
    Individual test step with ALCOA+ compliance requirements.
    
    Each step represents a single action in an OQ test case with clear
    expected results and data capture requirements for pharmaceutical validation.
    """
    step_number: int = Field(..., ge=1, description="Sequential step number")
    action: str = Field(..., min_length=10, description="Action to perform")
    expected_result: str = Field(..., min_length=10, description="Expected outcome")
    data_to_capture: list[str] = Field(default_factory=list, description="Data points to record")
    verification_method: str = Field(default="visual_inspection", description="How to verify result")
    acceptance_criteria: str = Field(default="", description="Specific pass/fail criteria")

    @field_validator("action", "expected_result")
    @classmethod
    def validate_pharmaceutical_language(cls, v: str) -> str:
        """Ensure professional pharmaceutical language in steps."""
        if not v or len(v.strip()) < 10:
            raise ValueError("Test steps must contain detailed pharmaceutical procedures")
        return v.strip()


class OQTestCase(BaseModel):
    """
    Individual OQ test case with pharmaceutical compliance requirements.
    
    Represents a complete test case following GAMP-5 guidelines with full
    traceability to URS requirements and regulatory compliance metadata.
    """
    test_id: str = Field(..., pattern=r"^OQ-\d{3}$", description="Test identifier (e.g., OQ-001)")
    test_name: str = Field(..., min_length=10, max_length=100, description="Descriptive test name")
    test_category: Literal["installation", "functional", "performance", "security", "data_integrity", "integration"]
    gamp_category: int = Field(..., ge=1, le=5, description="Associated GAMP category")

    # Test Structure
    objective: str = Field(..., min_length=20, description="Clear test objective")
    prerequisites: list[str] = Field(default_factory=list, description="Required conditions")
    test_steps: list[TestStep] = Field(..., min_items=1, description="Detailed test procedures")
    acceptance_criteria: list[str] = Field(..., min_items=1, description="Pass/fail criteria")

    # Compliance Fields
    regulatory_basis: list[str] = Field(default_factory=list, description="Regulatory references")
    risk_level: Literal["low", "medium", "high", "critical"] = "medium"
    data_integrity_requirements: list[str] = Field(default_factory=list)

    # Traceability
    urs_requirements: list[str] = Field(default_factory=list, description="Traced URS requirements")
    related_tests: list[str] = Field(default_factory=list, description="Related test IDs")

    # Execution metadata
    estimated_duration_minutes: int = Field(default=30, ge=5, description="Estimated execution time")
    required_expertise: list[str] = Field(default_factory=list, description="Required user expertise")

    @field_validator("test_steps")
    @classmethod
    def validate_test_steps_sequence(cls, v: list[TestStep]) -> list[TestStep]:
        """Ensure test steps are properly sequenced."""
        if not v:
            raise ValueError("Test case must contain at least one test step")

        # Validate sequential numbering
        expected_numbers = list(range(1, len(v) + 1))
        actual_numbers = [step.step_number for step in v]

        if actual_numbers != expected_numbers:
            raise ValueError("Test steps must be sequentially numbered starting from 1")

        return v

    @field_validator("test_id")
    @classmethod
    def validate_test_id_format(cls, v: str) -> str:
        """Validate OQ test ID format."""
        if not v.startswith("OQ-") or len(v) != 6:
            raise ValueError("Test ID must follow format 'OQ-XXX' where XXX is a 3-digit number")
        return v


class OQTestSuite(BaseModel):
    """
    Complete OQ test suite with category-specific structure and validation.
    
    Represents a comprehensive set of OQ tests for a specific GAMP category
    with full compliance metadata and traceability requirements.
    """
    suite_id: str = Field(..., pattern=r"^OQ-SUITE-\d{4}$", description="Unique suite identifier")
    gamp_category: int = Field(..., ge=1, le=5, description="GAMP software category")
    document_name: str = Field(..., min_length=1, description="Source document name")

    # Test Organization
    test_cases: list[OQTestCase] = Field(..., min_items=1, description="All test cases in suite")
    test_categories: dict[str, int] = Field(default_factory=dict, description="Test count by category")

    # Coverage Analysis
    requirements_coverage: dict[str, list[str]] = Field(default_factory=dict, description="Requirement to test mapping")
    risk_coverage: dict[str, int] = Field(default_factory=dict, description="Risk level distribution")
    compliance_coverage: dict[str, bool] = Field(default_factory=dict, description="Compliance requirements met")

    # Quality Metrics
    total_test_count: int = Field(..., ge=1, description="Total number of tests")
    estimated_execution_time: int = Field(..., ge=1, description="Total execution time in minutes")
    coverage_percentage: float = Field(default=0.0, ge=0.0, le=100.0, description="Requirements coverage")

    # Validation Metadata
    generation_timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    generation_method: str = Field(default="LLMTextCompletionProgram", description="How tests were generated")
    validation_approach: str = Field(default="", description="GAMP category validation approach")

    # Audit and Compliance
    created_by: str = Field(default="oq_generation_agent", description="System or user that created suite")
    review_required: bool = Field(default=True, description="Whether human review is required")
    pharmaceutical_compliance: dict[str, bool] = Field(default_factory=dict, description="Regulatory compliance flags")

    @field_validator("test_cases")
    @classmethod
    def validate_category_test_count(cls, v: list[OQTestCase], info) -> list[OQTestCase]:
        """Validate test count meets GAMP category requirements."""
        if not hasattr(info, "data") or "gamp_category" not in info.data:
            return v

        gamp_category = info.data.get("gamp_category")
        test_count = len(v)

        # GAMP category test count requirements - NO FALLBACKS
        category_requirements = {
            1: {"min": 3, "max": 5, "description": "Infrastructure software"},
            3: {"min": 5, "max": 10, "description": "Non-configured products"},
            4: {"min": 15, "max": 20, "description": "Configured products"},
            5: {"min": 25, "max": 30, "description": "Custom applications"}
        }

        if gamp_category not in category_requirements:
            raise ValueError(
                f"Invalid GAMP category {gamp_category}. "
                f"Valid categories: {list(category_requirements.keys())}"
            )

        requirements = category_requirements[gamp_category]
        min_required = requirements["min"]
        max_allowed = requirements["max"]

        if test_count < min_required:
            raise ValueError(
                f"GAMP Category {gamp_category} ({requirements['description']}) requires "
                f"minimum {min_required} tests, but only {test_count} provided. "
                f"NO fallback values available - must generate additional tests."
            )

        if test_count > max_allowed:
            raise ValueError(
                f"GAMP Category {gamp_category} ({requirements['description']}) allows "
                f"maximum {max_allowed} tests, but {test_count} provided. "
                f"NO fallback values available - must reduce test count."
            )

        return v

    @field_validator("pharmaceutical_compliance")
    @classmethod
    def validate_compliance_requirements(cls, v: dict[str, bool]) -> dict[str, bool]:
        """Ensure required pharmaceutical compliance checks are present."""
        required_compliance = [
            "alcoa_plus_compliant",
            "cfr_part11_compliant",
            "gamp5_compliant",
            "audit_trail_verified",
            "data_integrity_validated"
        ]

        # Initialize missing compliance flags as False (explicit)
        for requirement in required_compliance:
            if requirement not in v:
                v[requirement] = False

        return v

    def calculate_coverage_metrics(self) -> dict[str, Any]:
        """Calculate comprehensive coverage metrics for the test suite."""
        # Calculate test category distribution
        category_counts = {}
        for test in self.test_cases:
            category = test.test_category
            category_counts[category] = category_counts.get(category, 0) + 1

        # Calculate risk level distribution
        risk_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for test in self.test_cases:
            risk_counts[test.risk_level] += 1

        # Calculate total execution time
        total_time = sum(test.estimated_duration_minutes for test in self.test_cases)

        # Calculate average test complexity (based on steps)
        total_steps = sum(len(test.test_steps) for test in self.test_cases)
        avg_complexity = total_steps / len(self.test_cases) if self.test_cases else 0

        return {
            "category_distribution": category_counts,
            "risk_distribution": risk_counts,
            "total_execution_time_minutes": total_time,
            "average_test_complexity": round(avg_complexity, 2),
            "total_test_steps": total_steps,
            "requirements_traced": len(self.requirements_coverage),
            "coverage_completeness": self.coverage_percentage
        }


class OQGenerationConfig(BaseModel):
    """Configuration for OQ test generation with pharmaceutical validation parameters."""

    gamp_category: int = Field(..., ge=1, le=5, description="Target GAMP category")
    document_name: str = Field(..., min_length=1, description="Source URS document name")
    target_test_count: int = Field(..., ge=1, description="Desired number of tests")

    # Generation parameters
    complexity_level: Literal["basic", "standard", "comprehensive"] = "standard"
    focus_areas: list[str] = Field(default_factory=list, description="Specific areas to emphasize")
    regulatory_requirements: list[str] = Field(default_factory=list, description="Regulatory standards to meet")

    # Quality controls
    require_traceability: bool = Field(default=True, description="Require URS traceability")
    include_negative_testing: bool = Field(default=True, description="Include negative test scenarios")
    validate_data_integrity: bool = Field(default=True, description="Include data integrity tests")

    # Generation constraints
    max_steps_per_test: int = Field(default=10, ge=3, le=20, description="Maximum steps per test case")
    min_execution_time: int = Field(default=15, ge=5, description="Minimum test execution time")
    max_execution_time: int = Field(default=120, ge=30, description="Maximum test execution time")

    @field_validator("target_test_count")
    @classmethod
    def validate_test_count_for_category(cls, v: int, info) -> int:
        """Validate test count is appropriate for GAMP category."""
        if not hasattr(info, "data") or "gamp_category" not in info.data:
            return v

        gamp_category = info.data.get("gamp_category")

        # Category-specific validation
        category_limits = {
            1: (3, 5), 3: (5, 10), 4: (15, 20), 5: (25, 30)
        }

        if gamp_category in category_limits:
            min_tests, max_tests = category_limits[gamp_category]
            if not (min_tests <= v <= max_tests):
                raise ValueError(
                    f"GAMP Category {gamp_category} requires {min_tests}-{max_tests} tests, "
                    f"but {v} requested. NO automatic adjustment available."
                )

        return v

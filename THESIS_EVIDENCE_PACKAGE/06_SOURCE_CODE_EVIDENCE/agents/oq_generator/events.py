"""
Event classes for OQ test generation workflow.

This module defines the event classes used in the OQ test generation workflow,
providing structured data transfer between workflow steps with pharmaceutical
compliance and audit trail requirements.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from llama_index.core.workflow import Event
from pydantic import Field
from src.core.events import GAMPCategory

from .models import OQTestSuite


class OQTestGenerationEvent(Event):
    """
    Event containing OQ test generation requirements and context.
    
    This event triggers the OQ test generation process with all necessary
    context from upstream agents including GAMP categorization, planning
    strategy, and parallel agent insights.
    """
    # Core requirements
    gamp_category: GAMPCategory
    urs_content: str = Field(..., min_length=1, description="Source URS content")
    document_metadata: dict[str, Any] = Field(default_factory=dict, description="Document information")

    # Test generation parameters
    required_test_count: int = Field(..., ge=1, description="Number of tests to generate")
    test_strategy: dict[str, Any] = Field(default_factory=dict, description="Test generation strategy")
    compliance_requirements: list[str] = Field(default_factory=list, description="Regulatory requirements")

    # Context from upstream agents
    aggregated_context: dict[str, Any] = Field(default_factory=dict, description="Context from parallel agents")
    categorization_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="GAMP categorization confidence")

    # Quality parameters
    complexity_level: str = Field(default="standard", description="Test complexity level")
    focus_areas: list[str] = Field(default_factory=list, description="Areas to emphasize in testing")
    risk_level: str = Field(default="medium", description="Overall risk assessment")

    # Audit and traceability
    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    correlation_id: UUID = Field(default_factory=uuid4, description="Links to other workflow events")
    triggering_step: str = Field(default="oq_generation_requested", description="Step that triggered generation")


class OQTestSuiteEvent(Event):
    """
    Event containing generated OQ test suite with validation metadata.
    
    This event carries the complete generated OQ test suite along with
    quality metrics, coverage analysis, and compliance validation results.
    """
    # Generated test suite
    test_suite: OQTestSuite = Field(..., description="Complete generated test suite")
    generation_successful: bool = Field(default=True, description="Whether generation completed successfully")

    # Quality and coverage metrics
    coverage_analysis: dict[str, Any] = Field(default_factory=dict, description="Requirements coverage analysis")
    quality_metrics: dict[str, Any] = Field(default_factory=dict, description="Test suite quality metrics")
    compliance_validation: dict[str, bool] = Field(default_factory=dict, description="Compliance checks results")

    # Generation metadata
    generation_method: str = Field(default="LLMTextCompletionProgram", description="How tests were generated")
    context_quality: float = Field(default=0.0, ge=0.0, le=1.0, description="Quality of input context")
    generation_duration_seconds: float = Field(default=0.0, ge=0.0, description="Time taken to generate")

    # Validation and review requirements
    validation_issues: list[str] = Field(default_factory=list, description="Issues found during validation")
    human_review_required: bool = Field(default=True, description="Whether human review is needed")
    review_priority: str = Field(default="normal", description="Review priority level")

    # Traceability and audit
    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    correlation_id: UUID = Field(description="Links to triggering OQTestGenerationEvent")
    generated_by: str = Field(default="oq_generation_workflow", description="System component that generated tests")

    # Pharmaceutical compliance metadata
    gmp_compliant: bool = Field(default=False, description="GMP compliance validated")
    regulatory_basis: list[str] = Field(default_factory=list, description="Regulatory standards followed")
    audit_trail_complete: bool = Field(default=False, description="Complete audit trail maintained")


class OQValidationEvent(Event):
    """
    Event for validating generated OQ test suite quality and compliance.
    
    This event triggers validation of the generated test suite against
    pharmaceutical quality standards and regulatory requirements.
    """
    # Test suite to validate
    test_suite: OQTestSuite = Field(..., description="Test suite to validate")
    validation_type: str = Field(default="comprehensive", description="Type of validation to perform")

    # Validation parameters
    gamp_category: GAMPCategory = Field(..., description="Expected GAMP category")
    expected_test_count_range: tuple[int, int] = Field(..., description="Expected test count range")
    required_compliance_standards: list[str] = Field(default_factory=list, description="Required compliance standards")

    # Quality thresholds
    minimum_coverage_percentage: float = Field(default=80.0, ge=0.0, le=100.0, description="Minimum coverage required")
    maximum_acceptable_risk_level: str = Field(default="high", description="Maximum risk level allowed")
    require_traceability: bool = Field(default=True, description="Whether traceability is required")

    # Context for validation
    original_requirements: str = Field(default="", description="Original URS requirements")
    validation_context: dict[str, Any] = Field(default_factory=dict, description="Additional validation context")

    # Audit metadata
    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    correlation_id: UUID = Field(description="Links to OQTestSuiteEvent")
    validator_id: str = Field(default="oq_validation_system", description="System performing validation")


class OQValidationResultEvent(Event):
    """
    Event containing results of OQ test suite validation.
    
    This event carries the results of validating a generated OQ test suite,
    including pass/fail status, identified issues, and recommendations.
    """
    # Validation results
    validation_passed: bool = Field(..., description="Whether validation passed overall")
    validation_score: float = Field(..., ge=0.0, le=100.0, description="Overall validation score")

    # Detailed results
    compliance_results: dict[str, bool] = Field(default_factory=dict, description="Compliance check results")
    quality_issues: list[dict[str, Any]] = Field(default_factory=list, description="Quality issues found")
    coverage_gaps: list[str] = Field(default_factory=list, description="Coverage gaps identified")

    # Recommendations
    improvement_recommendations: list[str] = Field(default_factory=list, description="Suggestions for improvement")
    required_fixes: list[str] = Field(default_factory=list, description="Issues that must be fixed")
    optional_enhancements: list[str] = Field(default_factory=list, description="Optional improvements")

    # Risk assessment
    identified_risks: list[dict[str, Any]] = Field(default_factory=list, description="Risks identified in test suite")
    risk_mitigation_suggestions: list[str] = Field(default_factory=list, description="Risk mitigation suggestions")
    overall_risk_level: str = Field(default="medium", description="Overall risk assessment")

    # Decision support
    approval_recommended: bool = Field(default=False, description="Whether approval is recommended")
    human_review_required: bool = Field(default=True, description="Whether human review is required")
    review_focus_areas: list[str] = Field(default_factory=list, description="Areas requiring focused review")

    # Validation metadata
    validation_method: str = Field(default="automated_validation", description="Validation method used")
    validation_duration_seconds: float = Field(default=0.0, ge=0.0, description="Time taken for validation")
    validation_standards_applied: list[str] = Field(default_factory=list, description="Standards used for validation")

    # Audit and traceability
    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    correlation_id: UUID = Field(description="Links to OQValidationEvent")
    validated_by: str = Field(default="oq_validation_workflow", description="System that performed validation")

    # Pharmaceutical compliance
    regulatory_compliance_verified: bool = Field(default=False, description="Regulatory compliance verified")
    audit_trail_validated: bool = Field(default=False, description="Audit trail completeness validated")
    data_integrity_confirmed: bool = Field(default=False, description="Data integrity requirements confirmed")


# Export all event classes
__all__ = [
    "OQTestGenerationEvent",
    "OQTestSuiteEvent",
    "OQValidationEvent",
    "OQValidationResultEvent"
]

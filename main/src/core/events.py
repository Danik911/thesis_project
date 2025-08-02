"""
Custom event classes for the multi-agent pharmaceutical test generation workflow system.

This module defines all event types used in the GAMP-5 compliant test generation
workflow, providing Pydantic validation and ensuring regulatory compliance
with ALCOA+ principles and 21 CFR Part 11 requirements.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from llama_index.core.workflow import Event
from pydantic import Field, field_validator


class GAMPCategory(int, Enum):
    """GAMP-5 software categories for pharmaceutical validation."""
    CATEGORY_1 = 1  # Infrastructure software
    CATEGORY_3 = 3  # Non-configured products
    CATEGORY_4 = 4  # Configured products
    CATEGORY_5 = 5  # Custom applications


class ValidationStatus(str, Enum):
    """Validation status for compliance tracking."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    VALIDATED = "validated"
    REJECTED = "rejected"
    REQUIRES_REVIEW = "requires_review"


class URSIngestionEvent(Event):
    """
    Event triggered when a User Requirements Specification (URS) document is ingested.
    
    This event initiates the entire test generation workflow and contains
    the source URS content along with metadata for traceability.
    """
    urs_content: str
    document_name: str
    document_version: str
    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    author: str
    digital_signature: str | None = None


class GAMPCategorizationEvent(Event):
    """
    Event containing GAMP-5 software categorization results.
    
    Critical for determining validation approach and test rigor level
    according to pharmaceutical regulatory requirements.
    """
    gamp_category: GAMPCategory
    confidence_score: float
    justification: str
    risk_assessment: dict[str, Any]
    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    categorized_by: str
    review_required: bool = Field(default=False)

    @field_validator("confidence_score")
    @classmethod
    def validate_confidence_score(cls, v: float) -> float:
        """Validate confidence score range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        return v

    def __init__(self, **data: Any) -> None:
        """Initialize and set review_required based on confidence."""
        super().__init__(**data)
        if self.confidence_score < 0.7:
            self.review_required = True


class PlanningEvent(Event):
    """
    Event containing test planning information and strategy.
    
    Defines the overall approach for test generation based on
    GAMP categorization and regulatory requirements.
    """
    test_strategy: dict[str, Any]
    required_test_types: list[str]
    compliance_requirements: list[str]
    estimated_test_count: int
    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    planner_agent_id: str
    gamp_category: GAMPCategory


class AgentRequestEvent(Event):
    """
    Event for requesting agent services within the workflow.
    
    Enables communication between workflow steps and specialized agents
    while maintaining audit trail requirements.
    """
    agent_type: str
    request_data: dict[str, Any]
    priority: str = "normal"
    timeout_seconds: int | None = None
    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    requesting_step: str
    correlation_id: UUID = Field(default_factory=uuid4)


class AgentResultEvent(Event):
    """
    Event containing results from agent processing.
    
    Carries agent responses back to the workflow with
    validation status and any error information.
    """
    agent_type: str
    result_data: dict[str, Any]
    success: bool
    error_message: str | None = None
    processing_time: float
    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    correlation_id: UUID
    validation_status: ValidationStatus = ValidationStatus.PENDING


class ConsultationRequiredEvent(Event):
    """
    Event indicating human consultation is required.
    
    Triggered when automated processing encounters situations
    requiring human expertise or regulatory decision-making.
    """
    consultation_type: str
    context: dict[str, Any]
    urgency: str = "normal"  # normal, high, critical
    required_expertise: list[str]
    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    triggering_step: str
    consultation_id: UUID = Field(default_factory=uuid4)


class HumanResponseEvent(Event):
    """
    Event containing human responses for consultation requests.
    
    Captures human decisions with comprehensive pharmaceutical compliance
    metadata including user authentication, decision rationale, and
    regulatory compliance validation.
    """
    response_type: str  # decision, escalation, request_more_info
    response_data: dict[str, Any]
    user_id: str
    user_role: str
    decision_rationale: str
    confidence_level: float = Field(ge=0.0, le=1.0)
    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    consultation_id: UUID
    session_id: UUID
    digital_signature: str | None = None
    approval_level: str = "user"  # user, supervisor, quality_assurance
    regulatory_impact: str = "medium"  # low, medium, high, critical

    @field_validator("confidence_level")
    @classmethod
    def validate_confidence_level(cls, v: float) -> float:
        """Validate confidence level range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence level must be between 0.0 and 1.0")
        return v


class ConsultationTimeoutEvent(Event):
    """
    Event triggered when human consultation request times out.
    
    Indicates that no human response was received within the specified
    timeout period, triggering conservative default actions.
    """
    consultation_id: UUID
    timeout_duration_seconds: int
    conservative_action: str
    escalation_required: bool = True
    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    original_consultation: ConsultationRequiredEvent
    default_decision: dict[str, Any]
    escalation_contacts: list[str] = Field(default_factory=list)


class ConsultationSessionEvent(Event):
    """
    Event for managing consultation sessions and lifecycle.
    
    Tracks the complete lifecycle of consultation requests including
    session creation, updates, and completion for audit trail purposes.
    """
    session_action: str  # created, updated, completed, cancelled
    session_id: UUID
    consultation_id: UUID
    session_data: dict[str, Any]
    participants: list[str] = Field(default_factory=list)
    duration_seconds: int | None = None
    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    session_status: str = "active"  # active, completed, cancelled, escalated
    compliance_metadata: dict[str, Any] = Field(default_factory=dict)


class UserDecisionEvent(Event):
    """
    Event containing user decisions and approvals.
    
    Records human input and decisions with digital signatures
    for regulatory compliance and audit trail requirements.
    
    Note: This event is being phased out in favor of HumanResponseEvent
    for better pharmaceutical compliance features.
    """
    decision: str
    decision_context: dict[str, Any]
    user_id: str
    digital_signature: str
    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    consultation_id: UUID
    approval_level: str


class ScriptGenerationEvent(Event):
    """
    Event containing generated test scripts and associated metadata.
    
    Core event for the test generation workflow, including
    traceability matrix linking requirements to generated tests.
    """
    generated_tests: list[dict[str, Any]]
    traceability_matrix: dict[str, list[str]]
    test_coverage_metrics: dict[str, float]
    compliance_checklist: dict[str, bool]
    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    generator_agent_id: str
    gamp_category: GAMPCategory
    validation_required: bool = True

    @field_validator("generated_tests")
    @classmethod
    def validate_generated_tests(cls, v: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Validate that tests are provided."""
        if not v:
            raise ValueError("Generated tests cannot be empty")
        return v


class ValidationEvent(Event):
    """
    Event containing validation results for compliance checking.
    
    Records all validation activities and compliance verification
    according to ALCOA+ principles and regulatory requirements.
    """
    validation_type: str
    validation_results: dict[str, Any]
    compliance_score: float
    issues_found: list[dict[str, Any]]
    alcoa_compliance: dict[str, bool]
    cfr_part11_compliance: dict[str, bool]
    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    validator_id: str
    validation_status: ValidationStatus

    @field_validator("compliance_score")
    @classmethod
    def validate_compliance_score(cls, v: float) -> float:
        """Validate compliance score range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Compliance score must be between 0.0 and 1.0")
        return v


class DocumentProcessedEvent(Event):
    """
    Event triggered after document processing with LlamaParse.
    
    Contains structured document data including sections, metadata,
    charts, and requirements extracted from the URS document.
    """
    document_id: str
    document_name: str
    document_version: str
    metadata: dict[str, Any]
    content: str
    sections: list[dict[str, Any]]
    charts: list[dict[str, Any]]
    tables: list[dict[str, Any]]
    requirements: list[dict[str, Any]]
    processing_info: dict[str, Any]
    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    processor_id: str = "document_processor"


class ErrorRecoveryEvent(Event):
    """
    Event for error handling and recovery procedures.
    
    Provides structured error information and recovery strategies
    to maintain workflow continuity and regulatory compliance.
    """
    error_type: str
    error_message: str
    error_context: dict[str, Any]
    recovery_strategy: str
    recovery_actions: list[str]
    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    failed_step: str
    severity: str = "medium"  # low, medium, high, critical
    auto_recoverable: bool = False


class AgentResultsEvent(Event):
    """
    Event containing a collection of agent result events.
    
    This event wraps multiple AgentResultEvent instances to comply with
    LlamaIndex workflow validation that requires single Event parameters.
    """
    agent_results: list[AgentResultEvent]
    session_id: str
    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    success_count: int = Field(default=0)
    total_count: int = Field(default=0)
    
    def __init__(self, **data: Any) -> None:
        """Initialize and calculate success metrics."""
        super().__init__(**data)
        self.total_count = len(self.agent_results)
        self.success_count = sum(1 for result in self.agent_results if result.success)


class WorkflowCompletionEvent(Event):
    """
    Event indicating workflow completion readiness.
    
    This event is emitted to trigger the final completion step,
    carrying information about consultation requirements.
    """
    consultation_event: ConsultationRequiredEvent | None = None
    ready_for_completion: bool = True
    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    triggering_step: str


# OQ Test Generation Events - imported from OQ generator module
try:
    from src.agents.oq_generator.events import (
        OQTestGenerationEvent,
        OQTestSuiteEvent,
        OQValidationEvent,
        OQValidationResultEvent,
    )
    _OQ_EVENTS_AVAILABLE = True
except ImportError:
    # OQ generator not yet available
    _OQ_EVENTS_AVAILABLE = False


# Export all event classes for workflow use
__all__ = [
    "AgentRequestEvent",
    "AgentResultEvent",
    "AgentResultsEvent",
    "ConsultationRequiredEvent",
    "ConsultationSessionEvent",
    "ConsultationTimeoutEvent",
    "DocumentProcessedEvent",
    "ErrorRecoveryEvent",
    "GAMPCategorizationEvent",
    "GAMPCategory",
    "HumanResponseEvent",
    "PlanningEvent",
    "ScriptGenerationEvent",
    "URSIngestionEvent",
    "UserDecisionEvent",
    "ValidationEvent",
    "ValidationStatus",
    "WorkflowCompletionEvent",
]

# Add OQ events if available
if _OQ_EVENTS_AVAILABLE:
    __all__.extend([
        "OQTestGenerationEvent",
        "OQTestSuiteEvent",
        "OQValidationEvent",
        "OQValidationResultEvent"
    ])

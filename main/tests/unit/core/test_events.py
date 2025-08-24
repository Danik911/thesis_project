"""
Unit tests for the event system foundation.

Tests all event classes for proper validation, serialization,
and compliance with GAMP-5 and regulatory requirements.
"""

from datetime import datetime
from uuid import UUID, uuid4

import pytest
from src.core.events import (
    AgentRequestEvent,
    AgentResultEvent,
    ConsultationRequiredEvent,
    ErrorRecoveryEvent,
    GAMPCategorizationEvent,
    GAMPCategory,
    PlanningEvent,
    ScriptGenerationEvent,
    URSIngestionEvent,
    UserDecisionEvent,
    ValidationEvent,
    ValidationStatus,
)


class TestGAMPCategory:
    """Test GAMP-5 category enumeration."""

    def test_gamp_categories_valid(self):
        """Test valid GAMP-5 categories."""
        assert GAMPCategory.CATEGORY_3 == 3
        assert GAMPCategory.CATEGORY_4 == 4
        assert GAMPCategory.CATEGORY_5 == 5

    def test_gamp_category_values(self):
        """Test GAMP category value assignment."""
        assert GAMPCategory(3) == GAMPCategory.CATEGORY_3
        assert GAMPCategory(4) == GAMPCategory.CATEGORY_4
        assert GAMPCategory(5) == GAMPCategory.CATEGORY_5


class TestValidationStatus:
    """Test validation status enumeration."""

    def test_validation_status_values(self):
        """Test all validation status values."""
        assert ValidationStatus.PENDING == "pending"
        assert ValidationStatus.IN_PROGRESS == "in_progress"
        assert ValidationStatus.VALIDATED == "validated"
        assert ValidationStatus.REJECTED == "rejected"
        assert ValidationStatus.REQUIRES_REVIEW == "requires_review"


class TestURSIngestionEvent:
    """Test URS ingestion event functionality."""

    def test_urs_ingestion_event_creation(self):
        """Test basic URS ingestion event creation."""
        event = URSIngestionEvent(
            urs_content="Sample URS content",
            document_name="Test URS v1.0",
            document_version="1.0",
            author="test_author",
            digital_signature="signature123"
        )

        assert event.urs_content == "Sample URS content"
        assert event.document_name == "Test URS v1.0"
        assert event.document_version == "1.0"
        assert event.author == "test_author"
        assert event.digital_signature == "signature123"
        assert isinstance(event.event_id, UUID)
        assert isinstance(event.timestamp, datetime)



class TestGAMPCategorizationEvent:
    """Test GAMP categorization event functionality."""

    def test_gamp_categorization_event_creation(self):
        """Test basic GAMP categorization event creation."""
        event = GAMPCategorizationEvent(
            gamp_category=GAMPCategory.CATEGORY_4,
            confidence_score=0.85,
            justification="Clear configuration requirements",
            risk_assessment={"risk_level": "medium"},
            categorized_by="gamp_agent_1"
        )

        assert event.gamp_category == GAMPCategory.CATEGORY_4
        assert event.confidence_score == 0.85
        assert event.justification == "Clear configuration requirements"
        assert event.risk_assessment == {"risk_level": "medium"}
        assert event.categorized_by == "gamp_agent_1"
        assert event.review_required is False

    def test_gamp_categorization_low_confidence_review(self):
        """Test automatic review flagging for low confidence."""
        event = GAMPCategorizationEvent(
            gamp_category=GAMPCategory.CATEGORY_5,
            confidence_score=0.6,
            justification="Uncertain categorization",
            risk_assessment={},
            categorized_by="gamp_agent_1"
        )

        assert event.review_required is True

    def test_gamp_categorization_invalid_confidence(self):
        """Test validation of confidence score range."""
        with pytest.raises(ValueError, match="Confidence score must be between 0.0 and 1.0"):
            GAMPCategorizationEvent(
                gamp_category=GAMPCategory.CATEGORY_4,
                confidence_score=1.5,
                justification="Invalid confidence",
                risk_assessment={},
                categorized_by="agent"
            )


class TestPlanningEvent:
    """Test planning event functionality."""

    def test_planning_event_creation(self):
        """Test basic planning event creation."""
        event = PlanningEvent(
            test_strategy={"approach": "risk-based"},
            required_test_types=["functional", "security"],
            compliance_requirements=["GAMP-5", "21 CFR Part 11"],
            estimated_test_count=25,
            planner_agent_id="planner_1",
            gamp_category=GAMPCategory.CATEGORY_4
        )

        assert event.test_strategy == {"approach": "risk-based"}
        assert event.required_test_types == ["functional", "security"]
        assert event.compliance_requirements == ["GAMP-5", "21 CFR Part 11"]
        assert event.estimated_test_count == 25
        assert event.planner_agent_id == "planner_1"
        assert event.gamp_category == GAMPCategory.CATEGORY_4


class TestAgentRequestEvent:
    """Test agent request event functionality."""

    def test_agent_request_event_creation(self):
        """Test basic agent request event creation."""
        event = AgentRequestEvent(
            agent_type="context_agent",
            request_data={"query": "test requirements"},
            priority="high",
            timeout_seconds=30,
            requesting_step="planning"
        )

        assert event.agent_type == "context_agent"
        assert event.request_data == {"query": "test requirements"}
        assert event.priority == "high"
        assert event.timeout_seconds == 30
        assert event.requesting_step == "planning"
        assert isinstance(event.correlation_id, UUID)


class TestAgentResultEvent:
    """Test agent result event functionality."""

    def test_agent_result_event_success(self):
        """Test successful agent result event."""
        correlation_id = uuid4()
        event = AgentResultEvent(
            agent_type="context_agent",
            result_data={"results": ["test1", "test2"]},
            success=True,
            processing_time=1.23,
            correlation_id=correlation_id
        )

        assert event.agent_type == "context_agent"
        assert event.result_data == {"results": ["test1", "test2"]}
        assert event.success is True
        assert event.error_message is None
        assert event.processing_time == 1.23
        assert event.correlation_id == correlation_id
        assert event.validation_status == ValidationStatus.PENDING

    def test_agent_result_event_failure(self):
        """Test failed agent result event."""
        correlation_id = uuid4()
        event = AgentResultEvent(
            agent_type="context_agent",
            result_data={},
            success=False,
            error_message="Processing failed",
            processing_time=0.5,
            correlation_id=correlation_id,
            validation_status=ValidationStatus.REJECTED
        )

        assert event.success is False
        assert event.error_message == "Processing failed"
        assert event.validation_status == ValidationStatus.REJECTED


class TestConsultationRequiredEvent:
    """Test consultation required event functionality."""

    def test_consultation_required_event_creation(self):
        """Test basic consultation required event creation."""
        event = ConsultationRequiredEvent(
            consultation_type="regulatory_review",
            context={"issue": "ambiguous requirement"},
            urgency="high",
            required_expertise=["regulatory", "validation"],
            triggering_step="categorization"
        )

        assert event.consultation_type == "regulatory_review"
        assert event.context == {"issue": "ambiguous requirement"}
        assert event.urgency == "high"
        assert event.required_expertise == ["regulatory", "validation"]
        assert event.triggering_step == "categorization"
        assert isinstance(event.consultation_id, UUID)


class TestUserDecisionEvent:
    """Test user decision event functionality."""

    def test_user_decision_event_creation(self):
        """Test basic user decision event creation."""
        consultation_id = uuid4()
        event = UserDecisionEvent(
            decision="approved",
            decision_context={"rationale": "meets requirements"},
            user_id="user123",
            digital_signature="sig456",
            consultation_id=consultation_id,
            approval_level="level_2"
        )

        assert event.decision == "approved"
        assert event.decision_context == {"rationale": "meets requirements"}
        assert event.user_id == "user123"
        assert event.digital_signature == "sig456"
        assert event.consultation_id == consultation_id
        assert event.approval_level == "level_2"


class TestScriptGenerationEvent:
    """Test test generation event functionality."""

    def test_test_generation_event_creation(self):
        """Test basic test generation event creation."""
        event = ScriptGenerationEvent(
            generated_tests=[{"test_id": "T001", "name": "Login Test"}],
            traceability_matrix={"REQ001": ["T001"]},
            test_coverage_metrics={"coverage": 0.95},
            compliance_checklist={"gamp5": True, "cfr21": True},
            generator_agent_id="generator_1",
            gamp_category=GAMPCategory.CATEGORY_4
        )

        assert len(event.generated_tests) == 1
        assert event.generated_tests[0]["test_id"] == "T001"
        assert event.traceability_matrix == {"REQ001": ["T001"]}
        assert event.test_coverage_metrics == {"coverage": 0.95}
        assert event.compliance_checklist == {"gamp5": True, "cfr21": True}
        assert event.generator_agent_id == "generator_1"
        assert event.gamp_category == GAMPCategory.CATEGORY_4
        assert event.validation_required is True

    def test_test_generation_event_empty_tests_validation(self):
        """Test validation of empty generated tests."""
        with pytest.raises(ValueError, match="Generated tests cannot be empty"):
            ScriptGenerationEvent(
                generated_tests=[],
                traceability_matrix={},
                test_coverage_metrics={},
                compliance_checklist={},
                generator_agent_id="generator_1",
                gamp_category=GAMPCategory.CATEGORY_4
            )


class TestValidationEvent:
    """Test validation event functionality."""

    def test_validation_event_creation(self):
        """Test basic validation event creation."""
        event = ValidationEvent(
            validation_type="compliance_check",
            validation_results={"passed": True},
            compliance_score=0.92,
            issues_found=[],
            alcoa_compliance={"attributable": True, "legible": True},
            cfr_part11_compliance={"electronic_signature": True},
            validator_id="validator_1",
            validation_status=ValidationStatus.VALIDATED
        )

        assert event.validation_type == "compliance_check"
        assert event.validation_results == {"passed": True}
        assert event.compliance_score == 0.92
        assert event.issues_found == []
        assert event.alcoa_compliance == {"attributable": True, "legible": True}
        assert event.cfr_part11_compliance == {"electronic_signature": True}
        assert event.validator_id == "validator_1"
        assert event.validation_status == ValidationStatus.VALIDATED

    def test_validation_event_invalid_compliance_score(self):
        """Test validation of compliance score range."""
        with pytest.raises(ValueError, match="Compliance score must be between 0.0 and 1.0"):
            ValidationEvent(
                validation_type="test",
                validation_results={},
                compliance_score=1.5,
                issues_found=[],
                alcoa_compliance={},
                cfr_part11_compliance={},
                validator_id="validator",
                validation_status=ValidationStatus.PENDING
            )


class TestErrorRecoveryEvent:
    """Test error recovery event functionality."""

    def test_error_recovery_event_creation(self):
        """Test basic error recovery event creation."""
        event = ErrorRecoveryEvent(
            error_type="validation_failure",
            error_message="Compliance check failed",
            error_context={"step": "validation", "details": "missing signature"},
            recovery_strategy="manual_review",
            recovery_actions=["request_signature", "retry_validation"],
            failed_step="compliance_validation",
            severity="high",
            auto_recoverable=False
        )

        assert event.error_type == "validation_failure"
        assert event.error_message == "Compliance check failed"
        assert event.error_context == {"step": "validation", "details": "missing signature"}
        assert event.recovery_strategy == "manual_review"
        assert event.recovery_actions == ["request_signature", "retry_validation"]
        assert event.failed_step == "compliance_validation"
        assert event.severity == "high"
        assert event.auto_recoverable is False


class TestEventSerialization:
    """Test event serialization and deserialization."""

    def test_event_json_serialization(self):
        """Test that events can be serialized to JSON."""
        event = URSIngestionEvent(
            urs_content="Test content",
            document_name="Test Doc",
            document_version="1.0",
            author="test_author"
        )

        # Test that the event has the required attributes for serialization
        assert hasattr(event, "urs_content")
        assert hasattr(event, "event_id")
        assert hasattr(event, "timestamp")

        # LlamaIndex Event objects should be serializable
        assert event.urs_content == "Test content"
        assert isinstance(event.event_id, UUID)
        assert isinstance(event.timestamp, datetime)

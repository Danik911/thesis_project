"""
Tests for the human-in-the-loop consultation system.

Comprehensive test suite covering consultation lifecycle management, timeout handling,
conservative defaults, and regulatory compliance for pharmaceutical test generation.
"""

import asyncio
import pytest
from datetime import UTC, datetime, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from llama_index.core.workflow import Context

from src.core.events import (
    ConsultationRequiredEvent,
    ConsultationTimeoutEvent,
    GAMPCategory,
    HumanResponseEvent
)
from src.core.human_consultation import (
    ConsultationSession,
    HumanConsultationManager,
    request_human_consultation
)
from src.shared.config import Config, HumanConsultationConfig


@pytest.fixture
def consultation_config():
    """Create test consultation configuration."""
    return HumanConsultationConfig(
        default_timeout_seconds=2,  # Short timeout for testing
        escalation_timeout_seconds=4,
        critical_timeout_seconds=1,
        conservative_gamp_category=5,
        conservative_risk_level="HIGH",
        authorized_roles=["validation_engineer", "quality_assurance"],
        enable_notifications=True,
        detailed_audit_logging=True,
        consultation_timeouts={
            "categorization_failure": 2,  # Override for testing
            "categorization_error": 1,
            "planning_error": 2,
            "system_failure": 1
        }
    )


@pytest.fixture
def test_config(consultation_config):
    """Create test configuration with consultation settings."""
    config = Config()
    config.human_consultation = consultation_config
    return config


@pytest.fixture
def sample_consultation_event():
    """Create sample consultation required event."""
    return ConsultationRequiredEvent(
        consultation_type="categorization_failure",
        context={
            "error": "Unable to determine GAMP category",
            "confidence_score": 0.45,
            "urs_document": "test_document.pdf"
        },
        urgency="high",
        required_expertise=["gamp_specialist", "validation_engineer"],
        triggering_step="gamp_categorization"
    )


@pytest.fixture
def sample_human_response():
    """Create sample human response event."""
    consultation_id = uuid4()
    session_id = uuid4()
    
    return HumanResponseEvent(
        response_type="decision",
        response_data={
            "gamp_category": 4,
            "risk_assessment": {"risk_level": "MEDIUM"},
            "confidence_justification": "Clear software configuration parameters"
        },
        user_id="test_user",
        user_role="validation_engineer",
        decision_rationale="Software is clearly configured with standard parameters",
        confidence_level=0.85,
        consultation_id=consultation_id,
        session_id=session_id,
        approval_level="user"
    )


@pytest.fixture
def mock_context():
    """Create mock workflow context."""
    context = AsyncMock(spec=Context)
    context.set = AsyncMock()
    context.get = AsyncMock()
    context.send_event = AsyncMock()
    context.wait_for_event = AsyncMock()
    return context


class TestConsultationSession:
    """Test consultation session management."""

    @pytest.fixture
    def mock_compliance_logger(self):
        """Create mock compliance logger."""
        logger = AsyncMock()
        logger.log_audit_event = AsyncMock()
        return logger

    def test_session_initialization(self, sample_consultation_event, test_config, mock_compliance_logger):
        """Test consultation session initialization."""
        session = ConsultationSession(
            sample_consultation_event,
            test_config,
            mock_compliance_logger
        )

        assert session.consultation_event == sample_consultation_event
        assert session.config == test_config
        assert session.status == "active"
        assert session.timeout_seconds == 2  # From test config
        assert len(session.participants) == 0
        assert len(session.responses) == 0

    def test_timeout_for_consultation_type(self, sample_consultation_event, test_config, mock_compliance_logger):
        """Test timeout calculation based on consultation type."""
        session = ConsultationSession(
            sample_consultation_event,
            test_config,
            mock_compliance_logger
        )

        # Should use specific timeout for categorization_failure
        assert session.timeout_seconds == 2  # From test config

    def test_timeout_for_critical_urgency(self, test_config, mock_compliance_logger):
        """Test timeout for critical urgency consultations."""
        critical_consultation = ConsultationRequiredEvent(
            consultation_type="system_failure",
            context={"error": "Critical system error"},
            urgency="critical",
            required_expertise=["system_engineer"],
            triggering_step="system_check"
        )

        session = ConsultationSession(
            critical_consultation,
            test_config,
            mock_compliance_logger
        )

        # Should use critical timeout
        assert session.timeout_seconds == 1  # From test config

    @pytest.mark.asyncio
    async def test_add_response(self, sample_consultation_event, sample_human_response, 
                               test_config, mock_compliance_logger):
        """Test adding human response to session."""
        session = ConsultationSession(
            sample_consultation_event,
            test_config,
            mock_compliance_logger
        )

        # Update response to match session
        sample_human_response.session_id = session.session_id
        sample_human_response.consultation_id = sample_consultation_event.consultation_id

        await session.add_response(sample_human_response)

        assert len(session.responses) == 1
        assert sample_human_response.user_id in session.participants
        assert session.responses[0] == sample_human_response

        # Verify compliance logging
        mock_compliance_logger.log_audit_event.assert_called_once()
        audit_call = mock_compliance_logger.log_audit_event.call_args[0][0]
        assert audit_call["event_type"] == "CONSULTATION_RESPONSE"
        assert audit_call["user_id"] == sample_human_response.user_id

    @pytest.mark.asyncio
    async def test_session_completion(self, sample_consultation_event, test_config, mock_compliance_logger):
        """Test session completion."""
        session = ConsultationSession(
            sample_consultation_event,
            test_config,
            mock_compliance_logger
        )

        await session.complete_session("completed")

        assert session.status == "completed"
        assert session.timeout_task is None

        # Verify completion logging
        mock_compliance_logger.log_audit_event.assert_called_once()
        audit_call = mock_compliance_logger.log_audit_event.call_args[0][0]
        assert audit_call["event_type"] == "CONSULTATION_SESSION_COMPLETED"
        assert audit_call["final_status"] == "completed"

    def test_session_info(self, sample_consultation_event, test_config, mock_compliance_logger):
        """Test session information retrieval."""
        session = ConsultationSession(
            sample_consultation_event,
            test_config,
            mock_compliance_logger
        )

        info = session.get_session_info()

        assert info["consultation_type"] == sample_consultation_event.consultation_type
        assert info["urgency"] == sample_consultation_event.urgency
        assert info["status"] == "active"
        assert info["timeout_seconds"] == session.timeout_seconds
        assert "session_id" in info
        assert "created_at" in info


class TestHumanConsultationManager:
    """Test human consultation manager."""

    def test_manager_initialization(self, test_config):
        """Test consultation manager initialization."""
        manager = HumanConsultationManager(test_config)

        assert manager.config == test_config
        assert len(manager.active_sessions) == 0
        assert manager.total_consultations == 0

    @pytest.mark.asyncio
    async def test_successful_consultation(self, sample_consultation_event, sample_human_response,
                                         test_config, mock_context):
        """Test successful human consultation."""
        manager = HumanConsultationManager(test_config)

        # Mock successful human response
        mock_context.wait_for_event.return_value = sample_human_response
        sample_human_response.consultation_id = sample_consultation_event.consultation_id

        result = await manager.request_consultation(
            mock_context,
            sample_consultation_event,
            timeout_seconds=1  # Very short for testing
        )

        assert isinstance(result, HumanResponseEvent)
        assert result == sample_human_response
        assert manager.successful_consultations == 1
        assert len(manager.active_sessions) == 0  # Should be cleaned up

    @pytest.mark.asyncio
    async def test_consultation_timeout(self, sample_consultation_event, test_config, mock_context):
        """Test consultation timeout with conservative defaults."""
        manager = HumanConsultationManager(test_config)

        # Mock timeout
        mock_context.wait_for_event.side_effect = asyncio.TimeoutError()

        result = await manager.request_consultation(
            mock_context,
            sample_consultation_event,
            timeout_seconds=1  # Very short timeout (1 second)
        )

        assert isinstance(result, ConsultationTimeoutEvent)
        assert result.consultation_id == sample_consultation_event.consultation_id
        assert result.escalation_required is True
        assert "conservative_defaults_applied" in str(result.conservative_action).lower() or "category 5" in str(result.conservative_action).lower()
        assert manager.timed_out_consultations == 1

    def test_conservative_defaults_categorization(self, test_config):
        """Test conservative defaults for categorization consultation."""
        manager = HumanConsultationManager(test_config)

        consultation_event = ConsultationRequiredEvent(
            consultation_type="categorization_failure",
            context={"error": "Cannot determine category"},
            urgency="high",
            required_expertise=["gamp_specialist"],
            triggering_step="categorization"
        )

        defaults = manager._generate_conservative_defaults(consultation_event)

        assert defaults["gamp_category"] == GAMPCategory.CATEGORY_5
        assert defaults["risk_level"] == "HIGH"
        assert defaults["validation_approach"] == "full_validation_required"
        assert defaults["test_coverage"] == 1.0
        assert defaults["human_override_required"] is True
        assert "categorization" in defaults["action_description"].lower()

    def test_conservative_defaults_planning(self, test_config):
        """Test conservative defaults for planning consultation."""
        manager = HumanConsultationManager(test_config)

        consultation_event = ConsultationRequiredEvent(
            consultation_type="planning_error",
            context={"error": "Planning failed"},
            urgency="medium",
            required_expertise=["planning_specialist"],
            triggering_step="planning"
        )

        defaults = manager._generate_conservative_defaults(consultation_event)

        assert defaults["test_coverage"] == 1.0
        assert defaults["validation_approach"] == "full_validation_required"
        assert "maximum test coverage" in defaults["action_description"].lower()
        assert len(defaults["specific_actions"]) > 0

    def test_escalation_contacts(self, test_config):
        """Test escalation contact determination."""
        manager = HumanConsultationManager(test_config)

        consultation_event = ConsultationRequiredEvent(
            consultation_type="high_risk_issue",
            context={"risk": "High regulatory risk"},
            urgency="critical",
            required_expertise=["validation_engineer", "gamp_specialist"],
            triggering_step="validation"
        )

        contacts = manager._get_escalation_contacts(consultation_event)

        # Should include regulatory specialist for pharmaceutical compliance
        assert "regulatory_specialist" in contacts
        # Should include quality assurance for critical urgency
        assert "quality_assurance" in contacts

    @pytest.mark.asyncio
    async def test_escalate_consultation(self, sample_consultation_event, test_config):
        """Test consultation escalation."""
        manager = HumanConsultationManager(test_config)

        escalated_event = await manager.escalate_consultation(
            sample_consultation_event.consultation_id,
            "User requested supervisor review",
            "supervisor"
        )

        assert isinstance(escalated_event, ConsultationRequiredEvent)
        assert escalated_event.consultation_type == "escalated_supervisor"
        assert escalated_event.urgency == "high"
        assert "supervisor" in escalated_event.required_expertise
        assert manager.escalated_consultations == 1

    def test_manager_statistics(self, test_config):
        """Test manager statistics collection."""
        manager = HumanConsultationManager(test_config)

        # Simulate some consultations
        manager.total_consultations = 10
        manager.successful_consultations = 7
        manager.timed_out_consultations = 2
        manager.escalated_consultations = 1

        stats = manager.get_manager_statistics()

        assert stats["total_consultations"] == 10
        assert stats["successful_consultations"] == 7
        assert stats["success_rate"] == 0.7
        assert stats["timeout_rate"] == 0.2
        assert stats["escalation_rate"] == 0.1
        assert "configuration" in stats


class TestWorkflowIntegration:
    """Test integration with unified workflow."""

    @pytest.mark.asyncio
    async def test_request_human_consultation_function(self, sample_consultation_event,
                                                      sample_human_response, test_config, mock_context):
        """Test convenience function for workflow integration."""
        # Mock successful response
        mock_context.wait_for_event.return_value = sample_human_response
        sample_human_response.consultation_id = sample_consultation_event.consultation_id

        result = await request_human_consultation(
            mock_context,
            sample_consultation_event,
            timeout_seconds=1,
            config=test_config
        )

        assert isinstance(result, HumanResponseEvent)
        assert result == sample_human_response


class TestComplianceValidation:
    """Test regulatory compliance features."""

    @pytest.mark.asyncio
    async def test_audit_trail_logging(self, sample_consultation_event, test_config):
        """Test that all consultation activities are logged for compliance."""
        with patch('src.core.human_consultation.GAMP5ComplianceLogger') as mock_logger_class:
            mock_logger = AsyncMock()
            mock_logger_class.return_value = mock_logger

            manager = HumanConsultationManager(test_config)

            # Timeout scenario to trigger logging
            mock_context = AsyncMock()
            mock_context.wait_for_event.side_effect = asyncio.TimeoutError()
            mock_context.send_event = AsyncMock()

            await manager.request_consultation(
                mock_context,
                sample_consultation_event,
                timeout_seconds=1
            )

            # Verify audit logging occurred
            assert mock_logger.log_audit_event.call_count >= 1

    def test_alcoa_plus_compliance(self, sample_consultation_event, test_config):
        """Test ALCOA+ compliance in audit entries."""
        manager = HumanConsultationManager(test_config)

        # Test conservative defaults include compliance metadata
        defaults = manager._generate_conservative_defaults(sample_consultation_event)

        # Should include timestamp (Contemporaneous)
        assert "applied_at" in defaults
        
        # Should include rationale (Accurate)
        assert "regulatory_rationale" in defaults
        
        # Should include system metadata (Attributable)
        assert "system_version" in defaults
        assert "default_source" in defaults
        
        # Should include compliance standards (Complete)
        assert "compliance_standards" in defaults

    def test_conservative_defaults_are_truly_conservative(self, test_config):
        """Test that conservative defaults prioritize safety and compliance."""
        manager = HumanConsultationManager(test_config)

        consultation_event = ConsultationRequiredEvent(
            consultation_type="unknown_risk",
            context={"error": "Unknown risk level"},
            urgency="medium",
            required_expertise=["unknown_expert"],
            triggering_step="unknown_step"
        )

        defaults = manager._generate_conservative_defaults(consultation_event)

        # Should default to highest validation category
        assert defaults["gamp_category"] == GAMPCategory.CATEGORY_5
        # Should default to highest risk level
        assert defaults["risk_level"] == "HIGH"
        # Should require full validation
        assert defaults["validation_approach"] == "full_validation_required"
        # Should require 100% test coverage
        assert defaults["test_coverage"] == 1.0
        # Should require human review
        assert defaults["human_override_required"] is True

    def test_digital_signature_support(self, sample_human_response):
        """Test digital signature fields are properly handled."""
        # Test with digital signature
        sample_human_response.digital_signature = "digital_signature_hash_example"
        
        assert sample_human_response.digital_signature is not None
        assert isinstance(sample_human_response.digital_signature, str)

        # Test without digital signature (default)
        response_without_sig = HumanResponseEvent(
            response_type="decision",
            response_data={},
            user_id="test_user",
            user_role="validation_engineer", 
            decision_rationale="Test decision",
            confidence_level=0.8,
            consultation_id=uuid4(),
            session_id=uuid4()
        )
        
        assert response_without_sig.digital_signature is None


class TestErrorHandling:
    """Test error handling and recovery."""

    @pytest.mark.asyncio
    async def test_consultation_system_error(self, sample_consultation_event, test_config, mock_context):
        """Test handling of consultation system errors."""
        manager = HumanConsultationManager(test_config)

        # Mock system error
        mock_context.wait_for_event.side_effect = Exception("System error")

        result = await manager.request_consultation(
            mock_context,
            sample_consultation_event,
            timeout_seconds=1
        )

        # Should return timeout event with error information
        assert isinstance(result, ConsultationTimeoutEvent)
        assert result.escalation_required is True

    def test_invalid_response_validation(self, sample_consultation_event, test_config):
        """Test validation of invalid consultation responses."""
        # Create mock compliance logger
        mock_compliance_logger = AsyncMock()
        
        session = ConsultationSession(
            sample_consultation_event,
            test_config,
            mock_compliance_logger
        )

        # Test mismatched session ID
        invalid_response = HumanResponseEvent(
            response_type="decision",
            response_data={},
            user_id="test_user",
            user_role="validation_engineer",
            decision_rationale="Test",
            confidence_level=0.8,
            consultation_id=sample_consultation_event.consultation_id,
            session_id=uuid4()  # Wrong session ID
        )

        with pytest.raises(ValueError, match="session ID"):
            asyncio.run(session.add_response(invalid_response))


class TestPerformanceAndScalability:
    """Test performance and scalability considerations."""

    @pytest.mark.asyncio
    async def test_concurrent_consultations(self, test_config):
        """Test handling of multiple concurrent consultations."""
        manager = HumanConsultationManager(test_config)

        # Create multiple consultation events
        consultations = []
        for i in range(5):
            consultation = ConsultationRequiredEvent(
                consultation_type=f"test_consultation_{i}",
                context={"test": f"consultation_{i}"},
                urgency="medium",
                required_expertise=["test_expert"],
                triggering_step=f"test_step_{i}"
            )
            consultations.append(consultation)

        # Mock contexts
        mock_contexts = []
        for i in range(5):
            ctx = AsyncMock()
            ctx.wait_for_event.side_effect = asyncio.TimeoutError()
            ctx.send_event = AsyncMock()
            mock_contexts.append(ctx)

        # Run consultations concurrently
        tasks = []
        for i, consultation in enumerate(consultations):
            task = manager.request_consultation(
                mock_contexts[i],
                consultation,
                timeout_seconds=1
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # All should timeout with conservative defaults
        assert len(results) == 5
        assert all(isinstance(result, ConsultationTimeoutEvent) for result in results)
        assert manager.timed_out_consultations == 5

    @pytest.mark.asyncio
    async def test_session_cleanup(self, test_config):
        """Test cleanup of expired sessions."""
        manager = HumanConsultationManager(test_config)

        # Create a session (simulate expired)
        consultation = ConsultationRequiredEvent(
            consultation_type="test_consultation",
            context={"test": "cleanup"},
            urgency="low",
            required_expertise=["test_expert"],
            triggering_step="test_step"
        )

        session = ConsultationSession(
            consultation,
            test_config,
            manager.compliance_logger
        )

        # Manually add to active sessions and mark as old
        manager.active_sessions[session.session_id] = session
        session.updated_at = datetime.now(UTC) - timedelta(hours=1)  # 1 hour old

        # Run cleanup
        cleaned_count = await manager.cleanup_expired_sessions()

        assert cleaned_count == 1
        assert len(manager.active_sessions) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
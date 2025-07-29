"""
Human-in-the-Loop Consultation Manager for Pharmaceutical Test Generation System.

This module provides comprehensive human consultation capabilities with timeout handling,
conservative defaults, and full regulatory compliance for GAMP-5, ALCOA+, and
21 CFR Part 11 requirements.

Key Features:
- Timeout-based consultation with conservative defaults
- User authentication and role-based access control
- Digital signature support for regulatory compliance
- Complete audit trail with tamper-evident logging
- Escalation procedures for unresolved consultations
- Integration with Phoenix observability platform
"""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from llama_index.core.workflow import Context

from ..shared.config import Config, get_config
from ..shared.event_logging import GAMP5ComplianceLogger
from .events import (
    ConsultationRequiredEvent,
    ConsultationSessionEvent,
    ConsultationTimeoutEvent,
    GAMPCategory,
    HumanResponseEvent,
)


class ConsultationSession:
    """
    Manages a single consultation session with lifecycle tracking.
    
    Handles session creation, participant management, timeout monitoring,
    and audit trail generation for regulatory compliance.
    """

    def __init__(
        self,
        consultation_event: ConsultationRequiredEvent,
        config: Config,
        compliance_logger: GAMP5ComplianceLogger
    ):
        """
        Initialize consultation session.
        
        Args:
            consultation_event: The consultation request event
            config: System configuration
            compliance_logger: Logger for regulatory compliance
        """
        self.consultation_event = consultation_event
        self.config = config
        self.compliance_logger = compliance_logger

        # Session metadata
        self.session_id = uuid4()
        self.created_at = datetime.now(UTC)
        self.updated_at = self.created_at
        self.status = "active"
        self.participants: list[str] = []
        self.responses: list[HumanResponseEvent] = []

        # Timeout management
        self.timeout_task: asyncio.Task | None = None
        self.timeout_seconds = self._get_timeout_for_consultation_type()

        # Logger
        self.logger = logging.getLogger(f"{__name__}.ConsultationSession")

        self.logger.info(
            f"Created consultation session {self.session_id} for "
            f"consultation {self.consultation_event.consultation_id} "
            f"(type: {self.consultation_event.consultation_type}, timeout: {self.timeout_seconds}s)"
        )

    def _get_timeout_for_consultation_type(self) -> int:
        """Get timeout based on consultation type and urgency."""
        consultation_type = self.consultation_event.consultation_type
        urgency = self.consultation_event.urgency

        # Check for specific timeout configuration
        if consultation_type in self.config.human_consultation.consultation_timeouts:
            base_timeout = self.config.human_consultation.consultation_timeouts[consultation_type]
        else:
            base_timeout = self.config.human_consultation.default_timeout_seconds

        # Adjust based on urgency
        if urgency == "critical":
            return self.config.human_consultation.critical_timeout_seconds
        if urgency == "high":
            return min(base_timeout, self.config.human_consultation.critical_timeout_seconds * 2)
        return base_timeout

    async def start_timeout_monitoring(self) -> None:
        """Start timeout monitoring for the consultation session."""
        if self.timeout_task:
            self.timeout_task.cancel()

        self.timeout_task = asyncio.create_task(self._monitor_timeout())
        self.logger.debug(f"Started timeout monitoring for session {self.session_id}")

    async def _monitor_timeout(self) -> None:
        """Monitor session timeout and trigger conservative defaults."""
        try:
            await asyncio.sleep(self.timeout_seconds)

            # Timeout occurred - log and trigger conservative action
            self.logger.warning(
                f"Consultation session {self.session_id} timed out after {self.timeout_seconds}s"
            )

            # Mark session as timed out
            self.status = "timed_out"
            self.updated_at = datetime.now(UTC)

            # Log timeout event for compliance
            await self.compliance_logger.log_audit_event({
                "event_type": "CONSULTATION_TIMEOUT",
                "session_id": str(self.session_id),
                "consultation_id": str(self.consultation_event.consultation_id),
                "timeout_duration_seconds": self.timeout_seconds,
                "consultation_type": self.consultation_event.consultation_type,
                "urgency": self.consultation_event.urgency,
                "participants": self.participants,
                "responses_received": len(self.responses)
            })

        except asyncio.CancelledError:
            self.logger.debug(f"Timeout monitoring cancelled for session {self.session_id}")

    async def add_response(self, response: HumanResponseEvent) -> None:
        """
        Add a human response to the session.
        
        Args:
            response: Human response event
        """
        # Validate response belongs to this session
        if response.session_id != self.session_id:
            raise ValueError(f"Response session ID {response.session_id} does not match {self.session_id}")

        # Add participant if not already present
        if response.user_id not in self.participants:
            self.participants.append(response.user_id)

        # Store response
        self.responses.append(response)
        self.updated_at = datetime.now(UTC)

        # Log response for compliance
        await self.compliance_logger.log_audit_event({
            "event_type": "CONSULTATION_RESPONSE",
            "session_id": str(self.session_id),
            "consultation_id": str(self.consultation_event.consultation_id),
            "response_type": response.response_type,
            "user_id": response.user_id,
            "user_role": response.user_role,
            "confidence_level": response.confidence_level,
            "approval_level": response.approval_level,
            "regulatory_impact": response.regulatory_impact,
            "has_digital_signature": response.digital_signature is not None
        })

        self.logger.info(
            f"Added response from {response.user_id} ({response.user_role}) "
            f"to session {self.session_id}"
        )

    async def complete_session(self, final_status: str = "completed") -> None:
        """
        Complete the consultation session.
        
        Args:
            final_status: Final status for the session
        """
        # Cancel timeout monitoring
        if self.timeout_task:
            self.timeout_task.cancel()
            self.timeout_task = None

        # Update session status
        self.status = final_status
        self.updated_at = datetime.now(UTC)

        # Calculate session duration
        duration = (self.updated_at - self.created_at).total_seconds()

        # Log session completion
        await self.compliance_logger.log_audit_event({
            "event_type": "CONSULTATION_SESSION_COMPLETED",
            "session_id": str(self.session_id),
            "consultation_id": str(self.consultation_event.consultation_id),
            "final_status": final_status,
            "duration_seconds": duration,
            "participants": self.participants,
            "total_responses": len(self.responses),
            "consultation_type": self.consultation_event.consultation_type
        })

        self.logger.info(
            f"Completed consultation session {self.session_id} "
            f"with status '{final_status}' after {duration:.1f}s"
        )

    def is_timed_out(self) -> bool:
        """Check if the session has timed out."""
        if self.status == "timed_out":
            return True

        elapsed = (datetime.now(UTC) - self.created_at).total_seconds()
        return elapsed >= self.timeout_seconds

    def get_session_info(self) -> dict[str, Any]:
        """Get comprehensive session information."""
        duration = (self.updated_at - self.created_at).total_seconds()

        return {
            "session_id": str(self.session_id),
            "consultation_id": str(self.consultation_event.consultation_id),
            "consultation_type": self.consultation_event.consultation_type,
            "urgency": self.consultation_event.urgency,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "duration_seconds": duration,
            "timeout_seconds": self.timeout_seconds,
            "participants": self.participants,
            "total_responses": len(self.responses),
            "is_timed_out": self.is_timed_out()
        }


class HumanConsultationManager:
    """
    Manages human-in-the-loop consultations with pharmaceutical compliance.
    
    Provides comprehensive consultation lifecycle management including timeout
    handling, conservative defaults, user authentication, and audit trail
    generation for GAMP-5, ALCOA+, and 21 CFR Part 11 compliance.
    """

    def __init__(self, config: Config | None = None):
        """
        Initialize the human consultation manager.
        
        Args:
            config: System configuration (uses global if None)
        """
        self.config = config or get_config()
        self.logger = logging.getLogger(f"{__name__}.HumanConsultationManager")

        # Initialize compliance logger
        self.compliance_logger = GAMP5ComplianceLogger(self.config)

        # Active sessions tracking
        self.active_sessions: dict[UUID, ConsultationSession] = {}

        # Statistics
        self.total_consultations = 0
        self.successful_consultations = 0
        self.timed_out_consultations = 0
        self.escalated_consultations = 0

        self.logger.info("HumanConsultationManager initialized")

    async def request_consultation(
        self,
        ctx: Context,
        consultation_event: ConsultationRequiredEvent,
        timeout_seconds: int | None = None
    ) -> HumanResponseEvent | ConsultationTimeoutEvent:
        """
        Request human consultation with timeout handling.
        
        Args:
            ctx: Workflow context for event handling
            consultation_event: The consultation request
            timeout_seconds: Override timeout (uses config default if None)
            
        Returns:
            HumanResponseEvent if human responds, ConsultationTimeoutEvent if timeout
        """
        self.total_consultations += 1

        # Create consultation session
        session = ConsultationSession(
            consultation_event,
            self.config,
            self.compliance_logger
        )

        # Override timeout if specified
        if timeout_seconds:
            session.timeout_seconds = timeout_seconds

        # Store active session
        self.active_sessions[session.session_id] = session

        # Emit session creation event
        session_event = ConsultationSessionEvent(
            session_action="created",
            session_id=session.session_id,
            consultation_id=consultation_event.consultation_id,
            session_data=session.get_session_info(),
            participants=[],
            compliance_metadata={
                "consultation_type": consultation_event.consultation_type,
                "urgency": consultation_event.urgency,
                "required_expertise": consultation_event.required_expertise,
                "timeout_seconds": session.timeout_seconds
            }
        )

        # Send session creation event to workflow
        ctx.send_event(session_event)

        # Start timeout monitoring
        await session.start_timeout_monitoring()

        try:
            # Wait for human response or timeout
            self.logger.info(
                f"Waiting for human consultation response "
                f"(session: {session.session_id}, timeout: {session.timeout_seconds}s)"
            )

            # Use ctx.wait_for_event to wait for HumanResponseEvent
            try:
                response_event = await asyncio.wait_for(
                    ctx.wait_for_event(HumanResponseEvent),
                    timeout=session.timeout_seconds
                )

                # Validate response is for this consultation
                if response_event.consultation_id != consultation_event.consultation_id:
                    raise ValueError("Response consultation ID mismatch")

                # Add response to session
                await session.add_response(response_event)

                # Complete session successfully
                await session.complete_session("completed")
                self.successful_consultations += 1

                self.logger.info(
                    f"Received human consultation response from {response_event.user_id} "
                    f"for session {session.session_id}"
                )

                return response_event

            except TimeoutError:
                # Timeout occurred - apply conservative defaults
                self.logger.warning(
                    f"Consultation timed out for session {session.session_id}"
                )

                # Create timeout event with conservative defaults
                timeout_event = await self._create_timeout_event(session)

                # Complete session as timed out
                await session.complete_session("timed_out")
                self.timed_out_consultations += 1

                return timeout_event

        except Exception as e:
            # Handle unexpected errors
            self.logger.error(f"Error in consultation request: {e}")

            # Complete session with error status
            await session.complete_session("error")

            # Create error timeout event
            timeout_event = await self._create_timeout_event(session, error_message=str(e))
            return timeout_event

        finally:
            # Cleanup session
            if session.session_id in self.active_sessions:
                del self.active_sessions[session.session_id]

    async def _create_timeout_event(
        self,
        session: ConsultationSession,
        error_message: str | None = None
    ) -> ConsultationTimeoutEvent:
        """
        Create timeout event with conservative defaults.
        
        Args:
            session: The consultation session that timed out
            error_message: Optional error message
            
        Returns:
            ConsultationTimeoutEvent with conservative defaults
        """
        consultation_event = session.consultation_event

        # Generate conservative defaults based on pharmaceutical requirements
        conservative_defaults = self._generate_conservative_defaults(consultation_event)

        # Determine escalation contacts
        escalation_contacts = self._get_escalation_contacts(consultation_event)

        # Create timeout event
        timeout_event = ConsultationTimeoutEvent(
            consultation_id=consultation_event.consultation_id,
            timeout_duration_seconds=session.timeout_seconds,
            conservative_action=conservative_defaults["action_description"],
            escalation_required=True,
            original_consultation=consultation_event,
            default_decision=conservative_defaults,
            escalation_contacts=escalation_contacts
        )

        # Log timeout with conservative defaults for compliance
        await self.compliance_logger.log_audit_event({
            "event_type": "CONSULTATION_TIMEOUT_WITH_DEFAULTS",
            "session_id": str(session.session_id),
            "consultation_id": str(consultation_event.consultation_id),
            "consultation_type": consultation_event.consultation_type,
            "timeout_duration_seconds": session.timeout_seconds,
            "conservative_defaults_applied": conservative_defaults,
            "escalation_contacts": escalation_contacts,
            "error_message": error_message,
            "urgency": consultation_event.urgency,
            "regulatory_justification": "Conservative defaults applied per pharmaceutical validation requirements"
        })

        self.logger.warning(
            f"Applied conservative defaults for timed out consultation "
            f"{consultation_event.consultation_id}: {conservative_defaults['action_description']}"
        )

        return timeout_event

    def _generate_conservative_defaults(
        self,
        consultation_event: ConsultationRequiredEvent
    ) -> dict[str, Any]:
        """
        Generate conservative defaults for pharmaceutical compliance.
        
        Args:
            consultation_event: The consultation request
            
        Returns:
            Dictionary with conservative default decisions
        """
        consultation_type = consultation_event.consultation_type
        config = self.config.human_consultation

        # Base conservative defaults
        defaults = {
            "gamp_category": GAMPCategory(config.conservative_gamp_category),
            "risk_level": config.conservative_risk_level,
            "validation_approach": config.conservative_validation_approach,
            "test_coverage": config.conservative_test_coverage,
            "review_required": config.conservative_review_required,
            "confidence_score": 0.0,  # Lowest confidence for system defaults
            "human_override_required": True,
            "regulatory_rationale": "Conservative defaults applied due to timeout - requires human review",
            "default_source": "system_timeout_policy"
        }

        # Consultation-type specific adjustments
        if "categorization" in consultation_type.lower():
            defaults.update({
                "action_description": f"Applied Category {config.conservative_gamp_category} (highest validation rigor) due to categorization consultation timeout",
                "specific_actions": [
                    "Set GAMP Category 5 (custom application)",
                    "Require full validation lifecycle",
                    "Mandate design controls and source code review",
                    "Escalate to regulatory specialist for review"
                ]
            })
        elif "planning" in consultation_type.lower():
            defaults.update({
                "action_description": "Applied maximum test coverage and validation rigor due to planning consultation timeout",
                "specific_actions": [
                    "Set 100% test coverage requirement",
                    "Include all test types (unit, integration, system, UAT)",
                    "Require validation specialist review",
                    "Apply strictest acceptance criteria"
                ]
            })
        elif "missing_urs" in consultation_type.lower():
            defaults.update({
                "action_description": "Halt processing and escalate due to missing URS content",
                "specific_actions": [
                    "Stop automated processing",
                    "Escalate to document analyst",
                    "Require complete URS before proceeding",
                    "Document compliance risk"
                ]
            })
        else:
            defaults.update({
                "action_description": f"Applied conservative defaults for {consultation_type} consultation timeout",
                "specific_actions": [
                    "Apply highest validation rigor",
                    "Require human review before proceeding",
                    "Escalate to appropriate expertise",
                    "Document regulatory impact"
                ]
            })

        # Add timestamp and system metadata
        defaults.update({
            "applied_at": datetime.now(UTC).isoformat(),
            "system_version": "1.0.0",
            "compliance_standards": ["GAMP-5", "ALCOA+", "21 CFR Part 11"],
            "timeout_policy": "pharmaceutical_conservative_defaults_v1"
        })

        return defaults

    def _get_escalation_contacts(
        self,
        consultation_event: ConsultationRequiredEvent
    ) -> list[str]:
        """
        Get escalation contacts based on consultation type and required expertise.
        
        Args:
            consultation_event: The consultation request
            
        Returns:
            List of escalation contact roles
        """
        required_expertise = consultation_event.required_expertise
        hierarchy = self.config.human_consultation.escalation_hierarchy

        escalation_contacts = []

        # Add next level contacts for each required expertise
        for expertise in required_expertise:
            if expertise in hierarchy:
                escalation_contacts.extend(hierarchy[expertise])

        # Always include regulatory specialist for pharmaceutical compliance
        if "regulatory_specialist" not in escalation_contacts:
            escalation_contacts.append("regulatory_specialist")

        # Add quality assurance for high urgency
        if consultation_event.urgency in ["high", "critical"]:
            if "quality_assurance" not in escalation_contacts:
                escalation_contacts.append("quality_assurance")

        # Remove duplicates while preserving order
        seen = set()
        unique_contacts = []
        for contact in escalation_contacts:
            if contact not in seen:
                seen.add(contact)
                unique_contacts.append(contact)

        return unique_contacts

    async def escalate_consultation(
        self,
        consultation_id: UUID,
        escalation_reason: str,
        escalation_level: str = "supervisor"
    ) -> ConsultationRequiredEvent:
        """
        Escalate consultation to higher authority level.
        
        Args:
            consultation_id: Original consultation ID
            escalation_reason: Reason for escalation
            escalation_level: Level to escalate to
            
        Returns:
            New consultation event for escalated request
        """
        self.escalated_consultations += 1

        # Create escalated consultation event
        escalated_event = ConsultationRequiredEvent(
            consultation_type=f"escalated_{escalation_level}",
            context={
                "original_consultation_id": str(consultation_id),
                "escalation_reason": escalation_reason,
                "escalation_level": escalation_level,
                "escalated_at": datetime.now(UTC).isoformat()
            },
            urgency="high",
            required_expertise=[escalation_level, "regulatory_specialist"],
            triggering_step="human_consultation_escalation"
        )

        # Log escalation for compliance
        await self.compliance_logger.log_audit_event({
            "event_type": "CONSULTATION_ESCALATION",
            "original_consultation_id": str(consultation_id),
            "escalated_consultation_id": str(escalated_event.consultation_id),
            "escalation_reason": escalation_reason,
            "escalation_level": escalation_level,
            "escalated_at": datetime.now(UTC).isoformat(),
            "regulatory_impact": "HIGH"
        })

        self.logger.info(
            f"Escalated consultation {consultation_id} to {escalation_level} "
            f"level (new consultation: {escalated_event.consultation_id})"
        )

        return escalated_event

    def get_manager_statistics(self) -> dict[str, Any]:
        """Get consultation manager statistics."""
        return {
            "total_consultations": self.total_consultations,
            "successful_consultations": self.successful_consultations,
            "timed_out_consultations": self.timed_out_consultations,
            "escalated_consultations": self.escalated_consultations,
            "active_sessions": len(self.active_sessions),
            "success_rate": (
                self.successful_consultations / max(self.total_consultations, 1)
            ),
            "timeout_rate": (
                self.timed_out_consultations / max(self.total_consultations, 1)
            ),
            "escalation_rate": (
                self.escalated_consultations / max(self.total_consultations, 1)
            ),
            "configuration": {
                "default_timeout_seconds": self.config.human_consultation.default_timeout_seconds,
                "conservative_gamp_category": self.config.human_consultation.conservative_gamp_category,
                "authorized_roles": self.config.human_consultation.authorized_roles,
                "enable_notifications": self.config.human_consultation.enable_notifications
            }
        }

    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired consultation sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        expired_sessions = []
        current_time = datetime.now(UTC)

        for session_id, session in self.active_sessions.items():
            # Check if session has been inactive too long
            inactive_duration = (current_time - session.updated_at).total_seconds()
            max_inactive = self.config.human_consultation.session_cleanup_interval_seconds * 2

            if inactive_duration > max_inactive or session.is_timed_out():
                expired_sessions.append(session_id)

        # Clean up expired sessions
        for session_id in expired_sessions:
            session = self.active_sessions[session_id]
            await session.complete_session("expired")
            del self.active_sessions[session_id]

            self.logger.debug(f"Cleaned up expired session {session_id}")

        return len(expired_sessions)


# Convenience function for workflow integration
async def request_human_consultation(
    ctx: Context,
    consultation_event: ConsultationRequiredEvent,
    timeout_seconds: int | None = None,
    config: Config | None = None
) -> HumanResponseEvent | ConsultationTimeoutEvent:
    """
    Convenience function for requesting human consultation from workflows.
    
    Args:
        ctx: Workflow context
        consultation_event: Consultation request
        timeout_seconds: Optional timeout override
        config: Optional configuration override
        
    Returns:
        HumanResponseEvent or ConsultationTimeoutEvent
    """
    manager = HumanConsultationManager(config)
    return await manager.request_consultation(ctx, consultation_event, timeout_seconds)


# Export main classes and functions
__all__ = [
    "ConsultationSession",
    "HumanConsultationManager",
    "request_human_consultation"
]

"""
Custom pharmaceutical event handlers for domain-specific observability.

This module provides specialized event handlers that capture pharmaceutical
workflow events with rich context for GAMP-5 compliance and audit trails.
"""

import json
from datetime import datetime, UTC
from typing import Any, Dict, Optional
from uuid import uuid4

from openinference.instrumentation import using_attributes
from opentelemetry import trace
from llama_index.core.workflow import Event

from ..core.events import (
    GAMPCategorizationEvent,
    ValidationEvent,
    ConsultationRequiredEvent,
    UserDecisionEvent,
    ErrorRecoveryEvent
)


class PharmaceuticalEventHandler:
    """
    Custom event handler for pharmaceutical workflow events.
    
    Captures domain-specific events and enriches traces with compliance metadata.
    """
    
    def __init__(self, tracer: Optional[trace.Tracer] = None):
        """
        Initialize pharmaceutical event handler.
        
        Args:
            tracer: OpenTelemetry tracer instance
        """
        self.tracer = tracer or trace.get_tracer(__name__)
        self.processed_events = 0
        
    async def handle_event(self, event: Event) -> None:
        """
        Route event to appropriate handler based on type.
        
        Args:
            event: Event instance to handle
        """
        if isinstance(event, GAMPCategorizationEvent):
            await self.handle_gamp_categorization(event)
        elif isinstance(event, ValidationEvent):
            await self.handle_validation_event(event)
        elif isinstance(event, ConsultationRequiredEvent):
            await self.handle_consultation_event(event)
        elif isinstance(event, UserDecisionEvent):
            await self.handle_user_decision(event)
        elif isinstance(event, ErrorRecoveryEvent):
            await self.handle_error_recovery(event)
        else:
            # Generic handling for other events
            await self.handle_generic_event(event)
            
        self.processed_events += 1
    
    async def handle_gamp_categorization(self, event: GAMPCategorizationEvent) -> None:
        """
        Handle GAMP categorization with compliance tracing.
        
        Captures detailed categorization metadata for audit trail.
        """
        # Use OpenInference context manager
        with using_attributes(
            session_id=str(event.event_id),
            user_id=event.categorized_by,
            tags=["gamp_categorization"],
            metadata={
                "gamp_category": event.gamp_category.value,
                "confidence_score": event.confidence_score,
                "review_required": event.review_required,
                "risk_assessment": event.risk_assessment,
                "justification": event.justification,
                "alcoa_compliant": True,
                "cfr_part_11_compliant": True,
                "timestamp": event.timestamp.isoformat(),
                "event_id": str(event.event_id)
            }
        ):
            # Create a span for the categorization
            with self.tracer.start_as_current_span(
                "gamp_categorization",
                kind=trace.SpanKind.INTERNAL
            ) as span:
                # Add detailed span attributes
                # Document name not available in event
                span.set_attribute("gamp5.category", event.gamp_category.value)
                span.set_attribute("gamp5.confidence_score", event.confidence_score)
                span.set_attribute("gamp5.review_required", event.review_required)
                
                # Add risk assessment details
                if event.risk_assessment:
                    span.set_attribute("gamp5.risk.level", event.risk_assessment.get("level", ""))
                    span.set_attribute("gamp5.risk.patient_impact", event.risk_assessment.get("patient_impact", ""))
                    span.set_attribute("gamp5.risk.data_integrity", event.risk_assessment.get("data_integrity", ""))
                
                # Add categorization decision as span event
                span.add_event(
                    "GAMP-5 Categorization Decision",
                    attributes={
                        "event_type": "gamp_categorization",
                        "category": event.gamp_category.value,
                        "confidence": event.confidence_score,
                        "rationale": event.risk_assessment.get("rationale", ""),
                        "reviewer": event.categorized_by,
                        "requires_review": event.review_required
                    }
                )
    
    async def handle_validation_event(self, event: ValidationEvent) -> None:
        """
        Handle validation events with audit trail.
        
        Captures validation results and any errors for compliance.
        """
        with using_attributes(
            session_id=str(event.event_id),
            user_id=event.validator_id,
            tags=["validation"],
            metadata={
                "validation_type": event.validation_type,
                "validation_results": event.validation_results,
                "compliance_score": event.compliance_score,
                "issues_found": event.issues_found,
                "validation_status": event.validation_status.value,
                "timestamp": event.timestamp.isoformat()
            }
        ):
            with self.tracer.start_as_current_span(
                f"validation_{event.validation_type}",
                kind=trace.SpanKind.INTERNAL
            ) as span:
                span.set_attribute("validation.type", event.validation_type)
                span.set_attribute("validation.status", event.validation_status.value)
                span.set_attribute("validation.compliance_score", event.compliance_score)
                
                if event.issues_found:
                    span.set_attribute("validation.issue_count", len(event.issues_found))
                    span.set_attribute("validation.has_issues", True)
                    
                    # Add validation issues event
                    span.add_event(
                        "Validation Issues Found",
                        attributes={
                            "issue_count": len(event.issues_found),
                            "issues": json.dumps(event.issues_found[:5])  # Limit size
                        }
                    )
                else:
                    span.set_attribute("validation.has_issues", False)
    
    async def handle_consultation_event(self, event: ConsultationRequiredEvent) -> None:
        """
        Handle consultation required events.
        
        Tracks when human expertise is needed in the workflow.
        """
        with using_attributes(
            session_id=str(event.event_id),
            tags=["consultation_required"],
            metadata={
                "consultation_type": event.consultation_type,
                "urgency": event.urgency,
                "expertise_required": event.required_expertise,
                "context": event.context,
                "timestamp": event.timestamp.isoformat()
            }
        ):
            with self.tracer.start_as_current_span(
                "consultation_required",
                kind=trace.SpanKind.INTERNAL
            ) as span:
                span.set_attribute("consultation.type", event.consultation_type)
                span.set_attribute("consultation.urgency", event.urgency)
                span.set_attribute("consultation.expertise", ", ".join(event.required_expertise))
                
                # Add consultation event with recommendations
                span.add_event(
                    "Human Consultation Requested",
                    attributes={
                        "consultation_type": event.consultation_type,
                        "context": json.dumps(event.context),
                        "triggering_step": event.triggering_step,
                        "workflow_blocked": True
                    }
                )
    
    async def handle_user_decision(self, event: UserDecisionEvent) -> None:
        """
        Handle user decision events.
        
        Captures human-in-the-loop decisions for audit trail.
        """
        with using_attributes(
            session_id=str(event.event_id),
            user_id=event.user_id,
            tags=["user_decision"],
            metadata={
                "decision": event.decision,
                "decision_context": event.decision_context,
                "timestamp": event.timestamp.isoformat(),
                "consultation_id": str(event.consultation_id),
                "approval_level": event.approval_level
            }
        ):
            with self.tracer.start_as_current_span(
                "user_decision",
                kind=trace.SpanKind.INTERNAL
            ) as span:
                span.set_attribute("decision.value", event.decision)
                span.set_attribute("decision.maker", event.user_id)
                span.set_attribute("decision.approval_level", event.approval_level)
                
                # Add decision event with full context
                span.add_event(
                    "User Decision Recorded",
                    attributes={
                        "decision": event.decision,
                        "context": json.dumps(event.decision_context),
                        "digital_signature": event.digital_signature,
                        "consultation_id": str(event.consultation_id),
                        "approval_level": event.approval_level
                    }
                )
    
    async def handle_error_recovery(self, event: ErrorRecoveryEvent) -> None:
        """
        Handle error recovery events.
        
        Tracks error occurrence and recovery actions.
        """
        with using_attributes(
            session_id=str(event.event_id),
            tags=["error_recovery"],
            metadata={
                "error_type": event.error_type,
                "error_message": event.error_message,
                "recovery_strategy": event.recovery_strategy,
                "recovery_actions": event.recovery_actions,
                "error_context": event.error_context,
                "failed_step": event.failed_step,
                "severity": event.severity,
                "timestamp": event.timestamp.isoformat()
            }
        ):
            with self.tracer.start_as_current_span(
                "error_recovery",
                kind=trace.SpanKind.INTERNAL
            ) as span:
                span.set_attribute("error.type", event.error_type)
                span.set_attribute("error.message", event.error_message)
                span.set_attribute("error.recovery_strategy", event.recovery_strategy)
                span.set_attribute("error.failed_step", event.failed_step)
                span.set_attribute("error.severity", event.severity)
                retry_count = event.error_context.get('retry_count', 0)
                span.set_attribute("error.retry_count", retry_count)
                
                # Set span status based on severity
                if event.severity in ["high", "critical"]:
                    span.set_status(
                        trace.Status(
                            trace.StatusCode.ERROR,
                            f"High severity error: {event.error_message}"
                        )
                    )
                
                # Add recovery event
                span.add_event(
                    "Error Recovery Attempted",
                    attributes={
                        "error_type": event.error_type,
                        "strategy": event.recovery_strategy,
                        "actions": json.dumps(event.recovery_actions),
                        "context": json.dumps(event.error_context),
                        "severity": event.severity
                    }
                )
    
    async def handle_generic_event(self, event: Event) -> None:
        """
        Handle generic events not covered by specific handlers.
        
        Provides basic tracing for all event types.
        """
        event_id = str(getattr(event, 'event_id', uuid4()))
        
        with using_attributes(
            session_id=event_id,
            tags=[event.__class__.__name__],
            metadata={
                "event_type": event.__class__.__name__,
                "event_id": event_id,
                "timestamp": getattr(event, 'timestamp', datetime.now(UTC)).isoformat()
            }
        ):
            with self.tracer.start_as_current_span(
                f"event_{event.__class__.__name__}",
                kind=trace.SpanKind.INTERNAL
            ) as span:
                span.set_attribute("event.type", event.__class__.__name__)
                span.set_attribute("event.id", event_id)
                span.set_attribute("event.event_id", event_id)
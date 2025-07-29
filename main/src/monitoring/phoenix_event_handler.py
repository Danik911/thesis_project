"""
Phoenix event handler for pharmaceutical workflow observability.

This module extends the EventStreamHandler to add Phoenix tracing integration,
providing rich observability for GAMP-5 compliant workflows.
"""

import json
from typing import Any

from openinference.semconv.trace import SpanAttributes
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from ..shared.config import Config
from ..shared.event_logging import EventStreamHandler


class PhoenixEventStreamHandler(EventStreamHandler):
    """Extended event handler with Phoenix tracing integration."""

    def __init__(
        self,
        event_types: list[str] | None = None,
        config: Config | None = None,
        tracer: trace.Tracer | None = None
    ):
        """
        Initialize Phoenix-enabled event stream handler.
        
        Args:
            event_types: List of event types to capture
            config: Configuration instance
            tracer: OpenTelemetry tracer instance
        """
        super().__init__(event_types, config)
        self.tracer = tracer or trace.get_tracer(__name__)

    async def _process_event(self, event_data: dict[str, Any]) -> dict[str, Any] | None:
        """
        Process event with Phoenix span context.
        
        Adds pharmaceutical-specific attributes to the current span
        and ensures compliance metadata is captured.
        """
        # Get current span
        current_span = trace.get_current_span()

        if current_span and current_span.is_recording():
            event_type = event_data.get("event_type", "Unknown")

            # Add base event attributes
            current_span.set_attribute("event.type", event_type)
            current_span.set_attribute("event.id", event_data.get("event_id", ""))

            # Add pharmaceutical workflow attributes
            workflow_context = event_data.get("workflow_context", {})
            current_span.set_attribute(
                "pharmaceutical.workflow.step",
                workflow_context.get("step", "unknown")
            )
            current_span.set_attribute(
                "pharmaceutical.workflow.agent_id",
                workflow_context.get("agent_id", "")
            )
            current_span.set_attribute(
                "pharmaceutical.workflow.correlation_id",
                workflow_context.get("correlation_id", "")
            )

            # Handle specific event types with domain attributes
            if "GAMPCategorizationEvent" in event_type:
                self._add_gamp_attributes(current_span, event_data)
            elif "ValidationEvent" in event_type:
                self._add_validation_attributes(current_span, event_data)
            elif "ErrorRecoveryEvent" in event_type:
                self._add_error_attributes(current_span, event_data)
            elif "ConsultationRequiredEvent" in event_type:
                self._add_consultation_attributes(current_span, event_data)
            elif "UserDecisionEvent" in event_type:
                self._add_user_decision_attributes(current_span, event_data)

            # Add input/output for LLM observability
            payload = event_data.get("payload", {})
            if "message" in payload:
                current_span.set_attribute(
                    SpanAttributes.INPUT_VALUE,
                    str(payload["message"])[:1000]  # Limit size
                )
            if "result" in payload:
                current_span.set_attribute(
                    SpanAttributes.OUTPUT_VALUE,
                    str(payload["result"])[:1000]  # Limit size
                )

        # Process with parent implementation
        return await super()._process_event(event_data)

    def _add_gamp_attributes(self, span: trace.Span, event_data: dict[str, Any]) -> None:
        """Add GAMP-5 categorization attributes to span."""
        payload = event_data.get("payload", {})

        # GAMP category and confidence
        span.set_attribute("gamp5.category", payload.get("category", ""))
        span.set_attribute("gamp5.confidence_score", payload.get("confidence", 0.0))
        span.set_attribute("gamp5.review_required", payload.get("review_required", False))

        # Risk assessment
        risk_assessment = payload.get("risk_assessment", {})
        span.set_attribute("gamp5.risk.level", risk_assessment.get("level", ""))
        span.set_attribute("gamp5.risk.patient_impact", risk_assessment.get("patient_impact", ""))
        span.set_attribute("gamp5.risk.data_integrity", risk_assessment.get("data_integrity", ""))

        # Compliance metadata
        span.set_attribute("gamp5.alcoa_compliant", True)
        span.set_attribute("gamp5.cfr_part_11_compliant", True)

        # Add categorization rationale as span event
        if "rationale" in payload:
            span.add_event(
                "GAMP Categorization Decision",
                attributes={
                    "rationale": payload["rationale"],
                    "category": payload.get("category", ""),
                    "confidence": payload.get("confidence", 0.0)
                }
            )

    def _add_validation_attributes(self, span: trace.Span, event_data: dict[str, Any]) -> None:
        """Add validation event attributes to span."""
        payload = event_data.get("payload", {})

        span.set_attribute("validation.type", payload.get("validation_type", ""))
        span.set_attribute("validation.result", payload.get("result", ""))
        span.set_attribute("validation.gamp_category", payload.get("gamp_category", ""))

        # Add validation errors if present
        errors = payload.get("errors", [])
        if errors:
            span.set_attribute("validation.error_count", len(errors))
            span.set_attribute("validation.errors", json.dumps(errors[:5]))  # Limit size

            # Set span status to error
            span.set_status(
                Status(
                    StatusCode.ERROR,
                    f"Validation failed with {len(errors)} errors"
                )
            )

    def _add_error_attributes(self, span: trace.Span, event_data: dict[str, Any]) -> None:
        """Add error recovery event attributes to span."""
        payload = event_data.get("payload", {})

        span.set_attribute("error.type", payload.get("error_type", ""))
        span.set_attribute("error.message", payload.get("error_message", ""))
        span.set_attribute("error.recovery_action", payload.get("recovery_action", ""))
        span.set_attribute("error.retry_count", payload.get("retry_count", 0))

        # Set span status
        span.set_status(
            Status(
                StatusCode.ERROR,
                payload.get("error_message", "Unknown error")
            )
        )

        # Add error event with full context
        span.add_event(
            "Error Recovery Attempted",
            attributes={
                "error_type": payload.get("error_type", ""),
                "recovery_action": payload.get("recovery_action", ""),
                "success": payload.get("recovery_success", False)
            }
        )

    def _add_consultation_attributes(self, span: trace.Span, event_data: dict[str, Any]) -> None:
        """Add consultation required event attributes to span."""
        payload = event_data.get("payload", {})

        span.set_attribute("consultation.reason", payload.get("reason", ""))
        span.set_attribute("consultation.urgency", payload.get("urgency", "normal"))
        span.set_attribute("consultation.expertise_required", payload.get("expertise_required", ""))
        span.set_attribute("consultation.gamp_category", payload.get("gamp_category", ""))

        # Add consultation event
        span.add_event(
            "Human Consultation Required",
            attributes={
                "reason": payload.get("reason", ""),
                "context": payload.get("context", ""),
                "suggested_actions": json.dumps(payload.get("suggested_actions", []))
            }
        )

    def _add_user_decision_attributes(self, span: trace.Span, event_data: dict[str, Any]) -> None:
        """Add user decision event attributes to span."""
        payload = event_data.get("payload", {})

        span.set_attribute("user.decision_type", payload.get("decision_type", ""))
        span.set_attribute("user.decision_outcome", payload.get("outcome", ""))
        span.set_attribute("user.decision_maker", payload.get("user_id", ""))
        span.set_attribute("user.decision_timestamp", payload.get("timestamp", ""))

        # Add decision event with rationale
        span.add_event(
            "User Decision Made",
            attributes={
                "decision_type": payload.get("decision_type", ""),
                "outcome": payload.get("outcome", ""),
                "rationale": payload.get("rationale", ""),
                "impact": payload.get("impact", "")
            }
        )

"""
Error handling and fallback strategy for GAMP-5 categorization.

This module provides comprehensive error handling, fallback mechanisms, and audit logging
for the GAMP-5 categorization agent. Integrates with LlamaIndex native error handling
and prepares for Phoenix observability.

Key Features:
- Multiple error type detection (parsing, logic, ambiguity)
- Conservative fallback to Category 5
- Comprehensive audit trail generation
- LlamaIndex event-based tracking
- Phoenix observability preparation
"""

import logging
import traceback
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from llama_index.core.instrumentation.event_handlers import BaseEventHandler
from llama_index.core.instrumentation.events import BaseEvent
from src.core.events import GAMPCategorizationEvent, GAMPCategory


class ErrorType(Enum):
    """Types of errors that can occur during categorization."""
    PARSING_ERROR = "parsing_error"
    LOGIC_ERROR = "logic_error"
    AMBIGUITY_ERROR = "ambiguity_error"
    CONFIDENCE_ERROR = "confidence_error"
    TOOL_ERROR = "tool_error"
    LLM_ERROR = "llm_error"
    TIMEOUT_ERROR = "timeout_error"
    VALIDATION_ERROR = "validation_error"
    UNKNOWN_ERROR = "unknown_error"


class ErrorSeverity(Enum):
    """Severity levels for errors."""
    LOW = "low"          # Minor issues, can continue
    MEDIUM = "medium"    # Significant issues, needs review
    HIGH = "high"        # Critical issues, fallback required
    CRITICAL = "critical" # System failure, immediate fallback


@dataclass
class CategorizationError:
    """Structured error information for categorization failures."""
    error_id: str = field(default_factory=lambda: str(uuid4()))
    error_type: ErrorType = ErrorType.UNKNOWN_ERROR
    severity: ErrorSeverity = ErrorSeverity.HIGH
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    stack_trace: str | None = None
    recovery_action: str = "Fallback to Category 5"


@dataclass
class AuditLogEntry:
    """Audit log entry for regulatory compliance."""
    entry_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    action: str = ""
    actor: str = "GAMPCategorizationAgent"
    document_name: str = "Unknown"
    original_category: GAMPCategory | None = None
    fallback_category: GAMPCategory = GAMPCategory.CATEGORY_5
    error: CategorizationError | None = None
    confidence_score: float = 0.0
    decision_rationale: str = ""
    regulatory_impact: str = "High - Manual review required"


class CategorizationErrorHandler:
    """
    Comprehensive error handler for GAMP-5 categorization.
    
    Provides error detection, fallback mechanisms, and audit logging
    with LlamaIndex integration and Phoenix observability preparation.
    """

    def __init__(
        self,
        confidence_threshold: float = 0.60,
        ambiguity_threshold: float = 0.15,
        enable_audit_logging: bool = True,
        enable_phoenix_events: bool = True,
        verbose: bool = False
    ):
        """
        Initialize error handler.
        
        Args:
            confidence_threshold: Minimum confidence for successful categorization
            ambiguity_threshold: Maximum ambiguity score before triggering error
            enable_audit_logging: Enable comprehensive audit trail
            enable_phoenix_events: Enable Phoenix observability events
            verbose: Enable verbose logging
        """
        self.confidence_threshold = confidence_threshold
        self.ambiguity_threshold = ambiguity_threshold
        self.enable_audit_logging = enable_audit_logging
        self.enable_phoenix_events = enable_phoenix_events
        self.verbose = verbose

        # Audit log storage
        self.audit_log: list[AuditLogEntry] = []
        self.error_history: list[CategorizationError] = []

        # Logger setup
        self.logger = logging.getLogger(__name__)
        if verbose:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

        # Statistics tracking
        self.stats = {
            "total_errors": 0,
            "fallback_count": 0,
            "error_types": {},
            "recovery_success": 0
        }

    def handle_parsing_error(
        self,
        exception: Exception,
        document_content: str,
        document_name: str = "Unknown"
    ) -> GAMPCategorizationEvent:
        """
        Handle document parsing errors.
        
        Args:
            exception: The parsing exception
            document_content: Original document content
            document_name: Document identifier
            
        Returns:
            GAMPCategorizationEvent with Category 5 fallback
        """
        error = CategorizationError(
            error_type=ErrorType.PARSING_ERROR,
            severity=ErrorSeverity.HIGH,
            message=f"Failed to parse document: {exception!s}",
            details={
                "document_name": document_name,
                "content_length": len(document_content),
                "exception_type": type(exception).__name__,
                "content_preview": document_content[:200] if document_content else "Empty"
            },
            stack_trace=traceback.format_exc()
        )

        return self._create_fallback_event(error, document_name)

    def handle_logic_error(
        self,
        error_details: dict[str, Any],
        document_name: str = "Unknown",
        partial_results: dict[str, Any] | None = None
    ) -> GAMPCategorizationEvent:
        """
        Handle categorization logic failures.
        
        Args:
            error_details: Details about the logic failure
            document_name: Document identifier
            partial_results: Any partial results before failure
            
        Returns:
            GAMPCategorizationEvent with Category 5 fallback
        """
        error = CategorizationError(
            error_type=ErrorType.LOGIC_ERROR,
            severity=ErrorSeverity.HIGH,
            message=error_details.get("message", "Categorization logic failed"),
            details={
                "document_name": document_name,
                "error_details": error_details,
                "partial_results": partial_results,
                "failed_step": error_details.get("step", "unknown")
            }
        )

        return self._create_fallback_event(error, document_name)

    def check_ambiguity(
        self,
        categorization_results: dict[str, Any],
        confidence_scores: dict[int, float]
    ) -> CategorizationError | None:
        """
        Check for ambiguous categorization results.
        
        Args:
            categorization_results: Full categorization analysis
            confidence_scores: Confidence scores for each category
            
        Returns:
            CategorizationError if ambiguity detected, None otherwise
        """
        # Check for multiple high-confidence categories
        high_confidence_categories = [
            cat for cat, score in confidence_scores.items()
            if score > self.confidence_threshold
        ]

        if len(high_confidence_categories) > 1:
            return CategorizationError(
                error_type=ErrorType.AMBIGUITY_ERROR,
                severity=ErrorSeverity.MEDIUM,
                message=f"Multiple categories with high confidence: {high_confidence_categories}",
                details={
                    "confidence_scores": confidence_scores,
                    "high_confidence_categories": high_confidence_categories,
                    "ambiguity_score": self._calculate_ambiguity_score(confidence_scores)
                }
            )

        # Check for no clear winner
        max_confidence = max(confidence_scores.values()) if confidence_scores else 0
        if max_confidence < self.confidence_threshold:
            return CategorizationError(
                error_type=ErrorType.CONFIDENCE_ERROR,
                severity=ErrorSeverity.MEDIUM,
                message=f"No category meets confidence threshold ({self.confidence_threshold})",
                details={
                    "max_confidence": max_confidence,
                    "confidence_scores": confidence_scores,
                    "threshold": self.confidence_threshold
                }
            )

        return None

    def handle_tool_error(
        self,
        tool_name: str,
        exception: Exception,
        tool_input: Any,
        document_name: str = "Unknown"
    ) -> GAMPCategorizationEvent:
        """
        Handle errors from categorization tools.
        
        Args:
            tool_name: Name of the failed tool
            exception: The tool exception
            tool_input: Input that caused the error
            document_name: Document identifier
            
        Returns:
            GAMPCategorizationEvent with Category 5 fallback
        """
        error = CategorizationError(
            error_type=ErrorType.TOOL_ERROR,
            severity=ErrorSeverity.HIGH,
            message=f"Tool '{tool_name}' failed: {exception!s}",
            details={
                "tool_name": tool_name,
                "exception_type": type(exception).__name__,
                "tool_input_type": type(tool_input).__name__,
                "document_name": document_name
            },
            stack_trace=traceback.format_exc()
        )

        return self._create_fallback_event(error, document_name)

    def handle_llm_error(
        self,
        exception: Exception,
        prompt: str,
        document_name: str = "Unknown"
    ) -> GAMPCategorizationEvent:
        """
        Handle LLM-related errors.
        
        Args:
            exception: The LLM exception
            prompt: Prompt that caused the error
            document_name: Document identifier
            
        Returns:
            GAMPCategorizationEvent with Category 5 fallback
        """
        error = CategorizationError(
            error_type=ErrorType.LLM_ERROR,
            severity=ErrorSeverity.CRITICAL,
            message=f"LLM call failed: {exception!s}",
            details={
                "exception_type": type(exception).__name__,
                "prompt_length": len(prompt),
                "document_name": document_name,
                "prompt_preview": prompt[:200] if prompt else "Empty"
            },
            stack_trace=traceback.format_exc()
        )

        return self._create_fallback_event(error, document_name)

    def validate_categorization_result(
        self,
        result: dict[str, Any],
        document_name: str = "Unknown"
    ) -> CategorizationError | None:
        """
        Validate categorization results for completeness and consistency.
        
        Args:
            result: Categorization result to validate
            document_name: Document identifier
            
        Returns:
            CategorizationError if validation fails, None otherwise
        """
        required_fields = ["predicted_category", "evidence", "all_categories_analysis"]
        missing_fields = [field for field in required_fields if field not in result]

        if missing_fields:
            return CategorizationError(
                error_type=ErrorType.VALIDATION_ERROR,
                severity=ErrorSeverity.HIGH,
                message=f"Missing required fields in result: {missing_fields}",
                details={
                    "missing_fields": missing_fields,
                    "result_keys": list(result.keys()),
                    "document_name": document_name
                }
            )

        # Validate category value
        predicted_category = result.get("predicted_category")
        if predicted_category not in [1, 3, 4, 5]:
            return CategorizationError(
                error_type=ErrorType.VALIDATION_ERROR,
                severity=ErrorSeverity.HIGH,
                message=f"Invalid category value: {predicted_category}",
                details={
                    "predicted_category": predicted_category,
                    "valid_categories": [1, 3, 4, 5],
                    "document_name": document_name
                }
            )

        return None

    def _create_fallback_event(
        self,
        error: CategorizationError,
        document_name: str
    ) -> GAMPCategorizationEvent:
        """
        Create a fallback categorization event with Category 5.
        
        Args:
            error: The error that triggered fallback
            document_name: Document identifier
            
        Returns:
            GAMPCategorizationEvent with Category 5 and error details
        """
        # Update statistics
        self.stats["total_errors"] += 1
        self.stats["fallback_count"] += 1
        self.stats["error_types"][error.error_type.value] = \
            self.stats["error_types"].get(error.error_type.value, 0) + 1

        # Store error
        self.error_history.append(error)

        # Create audit log entry
        if self.enable_audit_logging:
            audit_entry = AuditLogEntry(
                action="FALLBACK_CATEGORIZATION",
                document_name=document_name,
                error=error,
                decision_rationale=f"Fallback to Category 5 due to {error.error_type.value}: {error.message}"
            )
            self.audit_log.append(audit_entry)
            self._log_audit_entry(audit_entry)

        # Generate comprehensive justification
        justification = self._generate_fallback_justification(error, document_name)

        # Create risk assessment
        risk_assessment = {
            "category": 5,
            "category_description": "Custom application - Conservative fallback due to error",
            "validation_approach": "Full GAMP-5 V-model validation required",
            "confidence_score": 0.0,
            "evidence_strength": "Error - No evidence available",
            "requires_human_review": True,
            "regulatory_impact": "High - Manual categorization required",
            "validation_effort": "Maximum - Full lifecycle validation",
            "error_details": {
                "error_type": error.error_type.value,
                "severity": error.severity.value,
                "message": error.message,
                "recovery_action": error.recovery_action
            }
        }

        # Log the fallback
        self.logger.warning(
            f"Categorization fallback triggered for '{document_name}': "
            f"{error.error_type.value} - {error.message}"
        )

        return GAMPCategorizationEvent(
            gamp_category=GAMPCategory.CATEGORY_5,
            confidence_score=0.0,
            justification=justification,
            risk_assessment=risk_assessment,
            event_id=uuid4(),
            timestamp=datetime.now(UTC),
            categorized_by="GAMPCategorizationAgent-ErrorHandler",
            review_required=True
        )

    def _generate_fallback_justification(
        self,
        error: CategorizationError,
        document_name: str
    ) -> str:
        """Generate detailed justification for fallback decision."""
        justification_parts = [
            f"GAMP-5 Categorization Error Report for '{document_name}'",
            "",
            "⚠️ AUTOMATIC FALLBACK TO CATEGORY 5",
            f"ERROR TYPE: {error.error_type.value.upper()}",
            f"SEVERITY: {error.severity.value.upper()}",
            f"TIMESTAMP: {error.timestamp.isoformat()}",
            "",
            "ERROR DETAILS:",
            f"- {error.message}",
            ""
        ]

        # Add specific error details
        if error.details:
            justification_parts.append("ADDITIONAL INFORMATION:")
            for key, value in error.details.items():
                if key not in ["stack_trace", "content_preview", "prompt_preview"]:
                    justification_parts.append(f"- {key}: {value}")
            justification_parts.append("")

        justification_parts.extend([
            "REGULATORY COMPLIANCE NOTICE:",
            "- This document requires manual expert review",
            "- Category 5 assigned as conservative default per GAMP-5 guidelines",
            "- Full V-model validation lifecycle required",
            "- All error details logged for audit trail (21 CFR Part 11)",
            "",
            "RECOVERY ACTION:",
            f"- {error.recovery_action}",
            "- Contact validation expert for manual categorization",
            "- Review error logs for root cause analysis"
        ])

        return "\n".join(justification_parts)

    def _calculate_ambiguity_score(self, confidence_scores: dict[int, float]) -> float:
        """Calculate ambiguity score based on confidence distribution."""
        if not confidence_scores:
            return 1.0

        scores = list(confidence_scores.values())
        scores.sort(reverse=True)

        if len(scores) < 2:
            return 0.0

        # Ambiguity is high when top scores are close
        return 1.0 - (scores[0] - scores[1])

    def _log_audit_entry(self, entry: AuditLogEntry):
        """Log audit entry for regulatory compliance."""
        audit_message = (
            f"AUDIT_LOG | ID: {entry.entry_id} | "
            f"Action: {entry.action} | "
            f"Document: {entry.document_name} | "
            f"Fallback: Category {entry.fallback_category.value} | "
            f"Reason: {entry.decision_rationale}"
        )

        # Always log audit entries at INFO level
        self.logger.info(audit_message)

    def get_audit_log(self) -> list[dict[str, Any]]:
        """Get audit log entries as dictionaries."""
        return [
            {
                "entry_id": entry.entry_id,
                "timestamp": entry.timestamp.isoformat(),
                "action": entry.action,
                "actor": entry.actor,
                "document_name": entry.document_name,
                "original_category": entry.original_category.value if entry.original_category else None,
                "fallback_category": entry.fallback_category.value,
                "error_type": entry.error.error_type.value if entry.error else None,
                "confidence_score": entry.confidence_score,
                "decision_rationale": entry.decision_rationale,
                "regulatory_impact": entry.regulatory_impact
            }
            for entry in self.audit_log
        ]

    def get_error_statistics(self) -> dict[str, Any]:
        """Get error handling statistics."""
        return {
            "total_errors": self.stats["total_errors"],
            "fallback_count": self.stats["fallback_count"],
            "error_type_distribution": self.stats["error_types"].copy(),
            "recovery_success_rate": (
                self.stats["recovery_success"] / self.stats["total_errors"]
                if self.stats["total_errors"] > 0 else 0
            ),
            "audit_log_entries": len(self.audit_log),
            "recent_errors": [
                {
                    "error_id": error.error_id,
                    "type": error.error_type.value,
                    "severity": error.severity.value,
                    "message": error.message,
                    "timestamp": error.timestamp.isoformat()
                }
                for error in self.error_history[-10:]  # Last 10 errors
            ]
        }

    def reset_statistics(self):
        """Reset error statistics (audit log is preserved)."""
        self.stats = {
            "total_errors": 0,
            "fallback_count": 0,
            "error_types": {},
            "recovery_success": 0
        }
        self.error_history.clear()


class CategorizationEventHandler(BaseEventHandler):
    """
    LlamaIndex event handler for categorization error tracking.
    
    Integrates with LlamaIndex's native event system for comprehensive
    error tracking and Phoenix observability preparation.
    """

    def __init__(self, error_handler: CategorizationErrorHandler):
        super().__init__()
        self.error_handler = error_handler
        self.logger = logging.getLogger(f"{__name__}.EventHandler")

    @classmethod
    def class_name(cls) -> str:
        return "CategorizationEventHandler"

    def handle(self, event: BaseEvent) -> None:
        """Handle categorization-related events."""
        try:
            event_type = event.class_name()

            # Track error events
            if "Error" in event_type or "Exception" in event_type:
                self.logger.error(f"Error event detected: {event_type}")
                # Future: Convert to CategorizationError and handle

            # Track tool events
            elif "Tool" in event_type:
                self.logger.debug(f"Tool event: {event_type}")

            # Track LLM events
            elif "LLM" in event_type or "Chat" in event_type:
                self.logger.debug(f"LLM event: {event_type}")

        except Exception as e:
            self.logger.error(f"Error handling event {event.class_name()}: {e}")

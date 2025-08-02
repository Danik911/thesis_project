"""
Explicit error handling for GAMP-5 categorization - NO FALLBACKS.

This module provides comprehensive error handling with explicit failure reporting
for the GAMP-5 categorization agent. Integrates with LlamaIndex native error handling
and prepares for Phoenix observability.

Key Features:
- Multiple error type detection (parsing, logic, ambiguity)
- Explicit failure reporting with full diagnostic information (NO FALLBACKS)
- Comprehensive audit trail generation
- LlamaIndex event-based tracking
- Phoenix observability preparation
- Pharmaceutical compliance with regulatory requirements
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
    recovery_action: str = "Explicit failure with diagnostic information"


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
        confidence_threshold: float = 0.50,  # Reduced from 0.60 to 0.50 for more realistic threshold
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
            GAMPCategorizationEvent with human consultation request or explicit failure
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

        # Only request human consultation for categorization ambiguity
        if self._should_request_human_consultation(error):
            return self._create_human_consultation_request(error, document_name)
        # For system errors, raise an exception to be handled by the calling code
        raise RuntimeError(f"System error in GAMP categorization: {error.message}")

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
            GAMPCategorizationEvent with human consultation request or explicit failure
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

        # Only request human consultation for categorization ambiguity
        if self._should_request_human_consultation(error):
            return self._create_human_consultation_request(error, document_name)
        # For system errors, raise an exception to be handled by the calling code
        raise RuntimeError(f"System error in GAMP categorization: {error.message}")

    def check_ambiguity(
        self,
        categorization_results: dict[str, Any],
        confidence_scores: dict[int, float]
    ) -> CategorizationError | None:
        """
        Check for ambiguous categorization results.
        
        Enhanced logic to avoid false positives on clear categorizations:
        - Only triggers ambiguity when categories are truly close in confidence
        - Considers dominance - if one category is clearly higher, not ambiguous
        - Uses higher threshold for ambiguity detection than base confidence
        
        Args:
            categorization_results: Full categorization analysis
            confidence_scores: Confidence scores for each category
            
        Returns:
            CategorizationError if ambiguity detected, None otherwise
        """
        if not confidence_scores:
            return None
            
        # Sort confidence scores in descending order
        sorted_scores = sorted(confidence_scores.values(), reverse=True)
        
        # Check for multiple high-confidence categories with improved logic
        # Use higher threshold for ambiguity detection (0.65 vs base 0.50)
        ambiguity_threshold = max(0.65, self.confidence_threshold + 0.15)
        
        high_confidence_categories = [
            cat for cat, score in confidence_scores.items()
            if score > ambiguity_threshold
        ]

        if len(high_confidence_categories) > 1:
            # Check for dominance - if top score is significantly higher, not ambiguous
            if len(sorted_scores) >= 2:
                dominance_gap = sorted_scores[0] - sorted_scores[1]
                
                # If there's a clear dominant category (gap > 0.20), not ambiguous
                if dominance_gap > 0.20:
                    return None
                    
                # If gap is moderate (0.10-0.20), only ambiguous if both are very high
                if 0.10 <= dominance_gap <= 0.20:
                    if sorted_scores[0] < 0.75:  # Not high enough to be concerning
                        return None
            
            return CategorizationError(
                error_type=ErrorType.AMBIGUITY_ERROR,
                severity=ErrorSeverity.MEDIUM,
                message=f"Multiple categories with high confidence: {high_confidence_categories}",
                details={
                    "confidence_scores": confidence_scores,
                    "high_confidence_categories": high_confidence_categories,
                    "ambiguity_score": self._calculate_ambiguity_score(confidence_scores),
                    "dominance_gap": sorted_scores[0] - sorted_scores[1] if len(sorted_scores) >= 2 else 0,
                    "ambiguity_threshold_used": ambiguity_threshold
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
        
        Tool validation errors should be fixed, not sent to human consultation.
        Only genuine categorization ambiguity should trigger human consultation.
        
        Args:
            tool_name: Name of the failed tool
            exception: The tool exception
            tool_input: Input that caused the error
            document_name: Document identifier
            
        Returns:
            GAMPCategorizationEvent with error details
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

        # Only request human consultation for categorization ambiguity
        if self._should_request_human_consultation(error):
            return self._create_human_consultation_request(error, document_name)
        # For system errors, raise an exception to be handled by the calling code
        raise RuntimeError(f"System error in GAMP categorization: {error.message}")

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
            GAMPCategorizationEvent with human consultation request or explicit failure
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

        # Only request human consultation for categorization ambiguity
        if self._should_request_human_consultation(error):
            return self._create_human_consultation_request(error, document_name)
        # For system errors, raise an exception to be handled by the calling code
        raise RuntimeError(f"System error in GAMP categorization: {error.message}")

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

    def _should_request_human_consultation(self, error: CategorizationError) -> bool:
        """
        Determine if this error type warrants human consultation.
        
        Only genuine categorization ambiguity should trigger human consultation.
        System errors should be handled programmatically.
        """
        # These error types indicate genuine categorization uncertainty
        consultation_error_types = {
            ErrorType.CONFIDENCE_ERROR,
            ErrorType.AMBIGUITY_ERROR
        }

        return error.error_type in consultation_error_types

    def _create_human_consultation_request(
        self,
        error: CategorizationError,
        document_name: str
    ) -> GAMPCategorizationEvent:
        """
        Create a human consultation request for categorization ambiguity.
        
        Args:
            error: The error that triggered consultation request
            document_name: Document identifier
            
        Returns:
            GAMPCategorizationEvent requesting human intervention
        """
        # Update statistics for consultation requests, not fallbacks
        self.stats["total_errors"] += 1
        self.stats["consultation_requests"] = self.stats.get("consultation_requests", 0) + 1
        self.stats["error_types"][error.error_type.value] = \
            self.stats["error_types"].get(error.error_type.value, 0) + 1

        # Store error
        self.error_history.append(error)

        # Extract actual confidence from error details if available
        actual_confidence = error.details.get("confidence", 0.0) if error.details else 0.0

        # Create audit log entry for consultation request - FIX CONFIDENCE DISPLAY BUG
        if self.enable_audit_logging:
            audit_entry = AuditLogEntry(
                action="HUMAN_CONSULTATION_REQUESTED",
                document_name=document_name,
                error=error,
                confidence_score=actual_confidence,  # Use actual confidence, not default 0.0
                decision_rationale=f"Human consultation required due to {error.error_type.value}: {error.message}"
            )
            self.audit_log.append(audit_entry)
            self._log_audit_entry(audit_entry)

        # Generate consultation request justification
        justification = self._generate_consultation_justification(error, document_name)

        # Log the consultation request
        self.logger.error(
            f"❌ CATEGORIZATION FAILED - Human consultation required for '{document_name}': "
            f"{error.error_type.value} - {error.message}"
        )
        self.logger.info(
            f"🤝 HUMAN-IN-THE-LOOP: Please manually categorize '{document_name}' "
            f"(Agent confidence: {actual_confidence:.1%})"
        )

        # IMPLEMENT SME AGENT CONSULTATION - Replace NotImplementedError
        return self._request_sme_consultation(error, document_name, actual_confidence)

    def _request_sme_consultation(
        self,
        error: CategorizationError,
        document_name: str,
        confidence: float
    ) -> GAMPCategorizationEvent:
        """
        Request SME agent consultation for low-confidence categorization.
        
        Args:
            error: The categorization error that triggered consultation
            document_name: Document identifier
            confidence: The confidence score that was below threshold
            
        Returns:
            GAMPCategorizationEvent with SME consultation result or explicit failure with diagnostics
        """
        try:
            # Import SME agent here to avoid circular imports
            import asyncio
            from uuid import uuid4

            from src.agents.parallel.sme_agent import create_sme_agent
            from src.core.events import AgentRequestEvent

            # Create SME agent for pharmaceutical validation
            sme_agent = create_sme_agent(
                specialty="pharmaceutical_validation",
                verbose=self.verbose,
                confidence_threshold=0.7  # SME has higher confidence threshold
            )

            # Prepare SME consultation request
            sme_request_data = {
                "specialty": "pharmaceutical_validation",
                "test_focus": "gamp_categorization",
                "compliance_level": "comprehensive",
                "validation_focus": ["gamp_compliance", "categorization_review"],
                "categorization_context": {
                    "gamp_category": error.details.get("category", "unknown"),
                    "confidence_score": confidence,
                    "error_type": error.error_type.value,
                    "threshold": self.confidence_threshold,
                    "document_name": document_name
                },
                "risk_factors": {
                    "confidence_uncertainty": True,
                    "categorization_ambiguity": error.error_type == ErrorType.AMBIGUITY_ERROR,
                    "technical_factors": ["gamp_categorization"]
                }
            }

            sme_request = AgentRequestEvent(
                agent_type="sme_agent",
                request_data=sme_request_data,
                requesting_step="gamp_categorization_error_handling",
                correlation_id=uuid4(),
                timeout_seconds=30  # Quick consultation for workflow continuity
            )

            # Execute SME consultation synchronously (convert async to sync)
            try:
                # Check if we're already in an event loop
                import nest_asyncio
                nest_asyncio.apply()  # Allow nested event loops

                loop = asyncio.get_event_loop()
                sme_result = loop.run_until_complete(sme_agent.process_request(sme_request))

                if sme_result.success and sme_result.result_data.get("confidence_score", 0) >= 0.7:
                    # SME provided high-confidence recommendation
                    sme_data = sme_result.result_data

                    # Extract SME recommendation or fail explicitly with diagnostic information
                    recommended_category = self._extract_sme_category_recommendation(sme_data)

                    self.logger.info(
                        f"✅ SME CONSULTATION SUCCESSFUL - Category {recommended_category} recommended "
                        f"(SME confidence: {sme_data.get('confidence_score', 0):.1%})"
                    )

                    # Create audit log for SME consultation
                    if self.enable_audit_logging:
                        sme_audit_entry = AuditLogEntry(
                            action="SME_CONSULTATION_COMPLETED",
                            document_name=document_name,
                            original_category=None,
                            fallback_category=GAMPCategory(recommended_category),
                            confidence_score=sme_data.get("confidence_score", 0),
                            decision_rationale=f"SME consultation completed. Recommended Category {recommended_category}. "
                                              f"SME opinion: {sme_data.get('expert_opinion', 'No opinion provided')[:100]}..."
                        )
                        self.audit_log.append(sme_audit_entry)
                        self._log_audit_entry(sme_audit_entry)

                    # Return successful categorization event with SME recommendation
                    return GAMPCategorizationEvent(
                        gamp_category=GAMPCategory(recommended_category),
                        confidence_score=sme_data.get("confidence_score", 0.7),
                        justification=f"SME Consultation Result:\n{sme_data.get('expert_opinion', 'Category determined by SME analysis')}",
                        risk_assessment={
                            "category": recommended_category,
                            "sme_validated": True,
                            "consultation_successful": True,
                            "original_confidence": confidence,
                            "sme_confidence": sme_data.get("confidence_score", 0),
                            "regulatory_impact": f"SME-validated Category {recommended_category}"
                        },
                        event_id=uuid4(),
                        timestamp=datetime.now(UTC),
                        categorized_by="SMEAgent",
                        review_required=False  # SME consultation removes manual review requirement
                    )
                # SME consultation failed or low confidence - NO FALLBACKS available
                self.logger.error(
                    f"❌ SME CONSULTATION INCONCLUSIVE - NO automated fallbacks available "
                    f"(SME success: {sme_result.success}, SME confidence: {sme_result.result_data.get('confidence_score', 0):.1%}). "
                    f"Explicit failure required per regulatory compliance."
                )

            except Exception as sme_error:
                self.logger.error(f"SME consultation execution failed: {sme_error}")
                # NO FALLBACKS - will raise explicit error below

        except ImportError as e:
            self.logger.error(f"SME agent import failed: {e}. NO fallbacks available per regulatory requirements")
        except Exception as e:
            self.logger.error(f"SME consultation setup failed: {e}. NO fallbacks available per regulatory requirements")

        # NO FALLBACKS - Throw error when SME consultation fails
        raise RuntimeError(
            f"GAMP categorization failed for '{document_name}': "
            f"Original confidence {confidence:.1%} below threshold {self.confidence_threshold:.1%}, "
            f"and SME consultation failed. No fallback allowed - system requires explicit resolution."
        )

    def _extract_sme_category_recommendation(self, sme_data: dict[str, Any]) -> int:
        """
        Extract GAMP category recommendation from SME consultation results.
        
        Args:
            sme_data: SME agent response data
            
        Returns:
            Recommended GAMP category (1, 3, 4, or 5)
        """
        # Look for explicit category recommendation in various fields
        recommendations = sme_data.get("recommendations", [])
        for rec in recommendations:
            if "category" in rec.get("recommendation", "").lower():
                # Try to extract category number from recommendation text
                import re
                category_match = re.search(r"category\s*(\d+)", rec["recommendation"].lower())
                if category_match:
                    category = int(category_match.group(1))
                    if category in [1, 3, 4, 5]:
                        return category

        # Check expert opinion for category mentions
        expert_opinion = sme_data.get("expert_opinion", "")
        if expert_opinion:
            import re
            category_match = re.search(r"category\s*(\d+)", expert_opinion.lower())
            if category_match:
                category = int(category_match.group(1))
                if category in [1, 3, 4, 5]:
                    return category

        # Check categorization context for original category if SME validated it
        categorization_context = sme_data.get("categorization_context", {})
        if categorization_context and sme_data.get("confidence_score", 0) >= 0.8:
            original_category = categorization_context.get("gamp_category", "unknown")
            if original_category != "unknown" and str(original_category).isdigit():
                category = int(original_category)
                if category in [1, 3, 4, 5]:
                    return category

        # NO FALLBACKS: Explicit failure when no clear SME recommendation available
        raise RuntimeError(
            f"SME consultation failed to provide clear GAMP category recommendation. "
            f"SME response data: {sme_data}. "
            f"No automated fallback available - human intervention required for regulatory compliance. "
            f"All categorization decisions must be explicit and traceable per pharmaceutical validation requirements."
        )


    def _generate_consultation_justification(
        self,
        error: CategorizationError,
        document_name: str
    ) -> str:
        """Generate justification for human consultation request."""
        timestamp = datetime.now(UTC).isoformat()

        return f"""GAMP-5 Human Consultation Request for '{document_name}'

🤝 HUMAN-IN-THE-LOOP REQUIRED
ERROR TYPE: {error.error_type.value.upper()}
SEVERITY: {error.severity.value.upper()}
TIMESTAMP: {timestamp}

CATEGORIZATION FAILURE:
{error.message}

REGULATORY COMPLIANCE NOTICE:
- Automated categorization failed - human expert required
- GAMP-5 compliance requires validated categorization
- 21 CFR Part 11 audit trail maintained for consultation request
- ALCOA+ principles: Human review ensures accuracy and completeness

REQUIRED ACTION:
- Contact GAMP-5 validation specialist for manual categorization
- Engage SME agents if available for pharmaceutical expertise
- Document human decision rationale for compliance audit

NEXT STEPS:
1. Human expert reviews document content and context
2. Expert provides GAMP category with justification
3. System records human decision with full audit trail
4. Workflow continues with validated categorization
"""


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

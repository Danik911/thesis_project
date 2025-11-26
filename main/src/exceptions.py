"""
Custom exceptions for pharmaceutical test generation workflow.

These exceptions enable proper error handling and human-in-the-loop workflows.
"""

from typing import Dict, Any, Optional
from datetime import datetime


class HumanApprovalRequired(Exception):
    """
    Raised when workflow requires human approval before continuing.

    This exception suspends workflow execution and triggers AWAITING_APPROVAL status.
    Worker catches this exception, stores approval data in job metadata, and exits cleanly.

    Workflow resumes when user submits approval via POST /jobs/{job_id}/approval.
    """

    def __init__(
        self,
        message: str,
        categorization_result: Dict[str, Any],
        ambiguity_signals: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 3600,
    ):
        """
        Initialize human approval required exception.

        Args:
            message: Human-readable description of why approval is needed
            categorization_result: GAMP-5 categorization result requiring approval
            ambiguity_signals: Optional ambiguity detection signals
            timeout_seconds: How long to wait for approval before expiring
        """
        super().__init__(message)
        self.categorization_result = categorization_result
        self.ambiguity_signals = ambiguity_signals or {}
        self.timeout_seconds = timeout_seconds
        self.requested_at = datetime.utcnow()

    def to_metadata(self) -> Dict[str, Any]:
        """
        Convert exception data to job metadata format.

        Returns:
            Dict suitable for storage in job.metadata JSON field
        """
        return {
            "approval_pending": {
                "message": str(self),
                "categorization_result": self.categorization_result,
                "ambiguity_signals": self.ambiguity_signals,
                "timeout_seconds": self.timeout_seconds,
                "requested_at": self.requested_at.isoformat(),
            }
        }


class ApprovalTimeoutError(Exception):
    """
    Raised when human approval timeout expires.

    Jobs in AWAITING_APPROVAL status that exceed timeout should transition to EXPIRED status.
    """
    pass


class WorkflowValidationError(Exception):
    """
    Raised when workflow input validation fails.

    This indicates invalid configuration or prerequisites not met.
    """
    pass

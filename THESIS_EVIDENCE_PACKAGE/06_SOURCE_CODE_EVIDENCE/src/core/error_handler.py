"""
Error handling system for the unified workflow.

This module provides comprehensive error handling with recovery strategies
for the pharmaceutical test generation workflow, ensuring GAMP-5 compliance
and regulatory traceability requirements.
"""

import asyncio
import logging
import traceback
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from llama_index.core.workflow import Context


class WorkflowErrorType(str, Enum):
    """Types of workflow errors with regulatory classification."""
    VALIDATION_ERROR = "validation_error"
    IO_ERROR = "io_error"
    AGENT_ERROR = "agent_error"
    WORKFLOW_ERROR = "workflow_error"
    TIMEOUT_ERROR = "timeout_error"
    COMPLIANCE_ERROR = "compliance_error"
    DATA_INTEGRITY_ERROR = "data_integrity_error"


class RecoveryStrategy(str, Enum):
    """Recovery strategies for different error types."""
    RETRY = "retry"
    ESCALATE = "escalate"
    FALLBACK = "fallback"
    ABORT = "abort"
    HUMAN_INTERVENTION = "human_intervention"


class WorkflowError(Exception):
    """Custom exception for workflow errors with regulatory compliance metadata."""

    def __init__(
        self,
        message: str,
        error_type: WorkflowErrorType,
        context: dict[str, Any] | None = None,
        recovery_strategy: RecoveryStrategy = RecoveryStrategy.ESCALATE
    ):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.context = context or {}
        self.recovery_strategy = recovery_strategy
        self.timestamp = datetime.now(UTC)
        self.error_id = f"ERR-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"


class ValidationError(WorkflowError):
    """Validation error for pharmaceutical compliance violations."""

    def __init__(
        self,
        message: str,
        error_type: WorkflowErrorType = WorkflowErrorType.VALIDATION_ERROR,
        context: dict[str, Any] | None = None
    ):
        super().__init__(message, error_type, context, RecoveryStrategy.ABORT)


class ErrorHandler:
    """
    Centralized error handling system for workflow operations.
    
    Provides structured error handling with recovery strategies and
    comprehensive audit trail for pharmaceutical compliance.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.error_count = 0
        self.recovery_attempts = {}

    async def handle_error(
        self,
        error: Exception,
        context: dict[str, Any],
        workflow_context: Context | None = None,
        max_retries: int = 3
    ) -> None:
        """
        Handle workflow errors with appropriate recovery strategies.
        
        This method provides structured error handling with audit trails
        for pharmaceutical compliance requirements.
        """
        self.error_count += 1

        # Determine error type and recovery strategy
        if isinstance(error, WorkflowError):
            error_type = error.error_type
            recovery_strategy = error.recovery_strategy
            error_context = {**context, **error.context}
        else:
            error_type = self._classify_error(error)
            recovery_strategy = self._determine_recovery_strategy(error_type)
            error_context = context

        # Log error with full context
        error_details = {
            "error_id": f"ERR-{datetime.now(UTC).strftime('%Y%m%d%H%M%S%f')}",
            "error_type": error_type,
            "error_message": str(error),
            "recovery_strategy": recovery_strategy,
            "context": error_context,
            "timestamp": datetime.now(UTC).isoformat(),
            "stack_trace": traceback.format_exc()
        }

        self.logger.error(f"Workflow error occurred: {error_details}")

        # Store error in workflow context if available
        if workflow_context:
            try:
                errors = await workflow_context.get("errors", [])
                errors.append(error_details)
                await workflow_context.set("errors", errors)
            except Exception as ctx_error:
                self.logger.warning(f"Could not store error in context: {ctx_error}")

        # Apply recovery strategy - NO FALLBACKS, explicit failures only
        if recovery_strategy == RecoveryStrategy.ABORT:
            self.logger.critical("Error requires workflow abortion - no recovery possible")
            raise error
        if recovery_strategy == RecoveryStrategy.ESCALATE:
            self.logger.error("Error requires escalation - raising to calling system")
            raise error
        if recovery_strategy == RecoveryStrategy.HUMAN_INTERVENTION:
            self.logger.warning("Error requires human intervention - workflow cannot continue")
            raise error
        # For other strategies, still raise the error - no masking
        self.logger.error(f"Error with recovery strategy {recovery_strategy} - raising for explicit handling")
        raise error

    def _classify_error(self, error: Exception) -> WorkflowErrorType:
        """Classify error type based on exception characteristics."""
        error_str = str(error).lower()

        if isinstance(error, (FileNotFoundError, PermissionError)):
            return WorkflowErrorType.IO_ERROR
        if isinstance(error, asyncio.TimeoutError):
            return WorkflowErrorType.TIMEOUT_ERROR
        if "validation" in error_str or "invalid" in error_str:
            return WorkflowErrorType.VALIDATION_ERROR
        if "compliance" in error_str or "regulatory" in error_str:
            return WorkflowErrorType.COMPLIANCE_ERROR
        if "agent" in error_str:
            return WorkflowErrorType.AGENT_ERROR
        return WorkflowErrorType.WORKFLOW_ERROR

    def _determine_recovery_strategy(self, error_type: WorkflowErrorType) -> RecoveryStrategy:
        """Determine appropriate recovery strategy for error type."""
        recovery_map = {
            WorkflowErrorType.VALIDATION_ERROR: RecoveryStrategy.ABORT,
            WorkflowErrorType.IO_ERROR: RecoveryStrategy.ESCALATE,
            WorkflowErrorType.AGENT_ERROR: RecoveryStrategy.ESCALATE,
            WorkflowErrorType.WORKFLOW_ERROR: RecoveryStrategy.ESCALATE,
            WorkflowErrorType.TIMEOUT_ERROR: RecoveryStrategy.ESCALATE,
            WorkflowErrorType.COMPLIANCE_ERROR: RecoveryStrategy.ABORT,
            WorkflowErrorType.DATA_INTEGRITY_ERROR: RecoveryStrategy.ABORT,
        }

        return recovery_map.get(error_type, RecoveryStrategy.ESCALATE)

    def get_error_statistics(self) -> dict[str, Any]:
        """Get error handling statistics for monitoring."""
        return {
            "total_errors": self.error_count,
            "recovery_attempts": len(self.recovery_attempts),
            "timestamp": datetime.now(UTC).isoformat()
        }

"""
LangFuse callback handler for LlamaIndex workflows.

Provides GAMP-5 compliant trace instrumentation for LlamaIndex workflow operations
including LLM calls, retrieval, and agent interactions. Uses CallbackHandler approach
(NOT Instrumentation) for stability with LlamaIndex Workflows.

NOTE: This module creates a CallbackManager factory. The actual LangFuse integration
uses the @observe decorator on FastAPI endpoints. For LlamaIndex workflows, we use
standard LlamaIndex callbacks which will be captured by the @observe decorator when
the workflow is called from an instrumented FastAPI endpoint.
"""

import logging
from datetime import UTC, datetime
from typing import Any, Optional

from llama_index.core.callbacks import CallbackManager

logger = logging.getLogger(__name__)


def create_langfuse_callback_manager(
    user_id: str,
    job_id: str,
    trace_name: str = "pharmaceutical_test_generation",
    **additional_metadata: Any
) -> CallbackManager:
    """
    Create CallbackManager with GAMP-5 metadata for LlamaIndex workflows.

    NOTE: This creates a standard LlamaIndex CallbackManager. The actual LangFuse
    tracing is handled by the @observe decorator on the FastAPI endpoint that calls
    the workflow. This function is provided for future integration when LangFuse
    LlamaIndex callback handler is installed.

    For now, GAMP-5 metadata is logged and will be captured by the @observe decorator
    when the workflow executes within an instrumented FastAPI endpoint.

    Args:
        user_id: Clerk user ID (ALCOA+ Attributable - who performed action)
        job_id: Job UUID for tracking and traceability
        trace_name: Human-readable trace name (default: pharmaceutical_test_generation)
        **additional_metadata: Additional GAMP-5 metadata (environment, version, etc.)

    Returns:
        CallbackManager for LlamaIndex workflows (standard callbacks, no LangFuse handler yet)

    Example:
        >>> callback_manager = create_langfuse_callback_manager(
        ...     user_id="clerk_user_123",
        ...     job_id="job-uuid-456",
        ...     trace_name="test_generation_workflow",
        ...     environment="production",
        ...     user_email="user@pharma.com"
        ... )
    """
    # GAMP-5 compliant metadata (MANDATORY for regulatory compliance)
    gamp_metadata = {
        # ALCOA+ Attributable: Who performed the action
        "user_id": user_id,
        # GAMP-5 Traceability: Job identifier
        "job_id": job_id,
        # GAMP-5 Categorization: Category 5 (Fully Configurable)
        "gamp_category": "5",
        # ALCOA+ Contemporaneous: When action occurred
        "timestamp": datetime.now(UTC).isoformat(),
        # ALCOA+ Compliance Markers
        "alcoa_attributable": True,
        "alcoa_contemporaneous": True,
        # Workflow Versioning (ALCOA+ Original)
        "workflow_version": "1.0",
        # Additional metadata from caller
        **additional_metadata,
    }

    # Log GAMP-5 metadata for audit trail
    # This will be captured by the @observe decorator on the calling FastAPI endpoint
    logger.info(
        f"Creating CallbackManager with GAMP-5 metadata\n"
        f"  Trace Name: {trace_name}\n"
        f"  Job ID: {job_id}\n"
        f"  User ID: {user_id}\n"
        f"  GAMP-5 Metadata: {gamp_metadata}"
    )

    # Create standard CallbackManager
    # Future: Add LangFuse handler when llama-index-instrumentation-langfuse installed
    callback_manager = CallbackManager([])

    return callback_manager

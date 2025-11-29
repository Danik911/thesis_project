"""
Worker execution logic for pharmaceutical test generation workflow.

This module implements the actual workflow execution for background jobs,
integrating with the UnifiedWorkflow to process URS documents end-to-end.

Supports Human-in-the-Loop (HIL) workflow:
- Detects when categorization requires human review
- Pauses workflow and updates job to AWAITING_APPROVAL
- Polls for approval decision every 2 seconds
- Resumes with human-approved category or rejects on timeout

CRITICAL: NO FALLBACK LOGIC
- All errors must raise exceptions with full context
- All status updates must reflect actual state
- All failures must be logged with complete diagnostic information
"""

import asyncio
import json
import logging
import os
import traceback
from contextlib import nullcontext
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from langfuse import get_client, observe
try:
    from langfuse.decorators import propagate_attributes  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover - older SDKs
    propagate_attributes = None

from main.src.adapters.chroma_adapter import ChromaVectorStoreAdapter
from main.src.adapters.local_adapter import LocalStorageAdapter
from main.src.core.unified_workflow import UnifiedTestGenerationWorkflow
from main.src.exceptions import HumanApprovalRequired

logger = logging.getLogger(__name__)


def _find_human_approval_required(exc: Exception) -> HumanApprovalRequired | None:
    """
    Search exception chain for HumanApprovalRequired.

    LlamaIndex workflow wraps step exceptions, so we need to check the cause chain.

    Args:
        exc: The exception to search

    Returns:
        HumanApprovalRequired if found in cause chain, None otherwise
    """
    current = exc
    seen = set()
    while current is not None:
        if id(current) in seen:
            break
        seen.add(id(current))

        if isinstance(current, HumanApprovalRequired):
            return current

        # Check __cause__ (from 'raise ... from')
        if current.__cause__ is not None:
            current = current.__cause__
        # Check __context__ (implicit exception chain)
        elif current.__context__ is not None:
            current = current.__context__
        else:
            break

    return None

# HIL Configuration (can be overridden via environment variables)
HIL_APPROVAL_TIMEOUT_SECONDS = int(os.getenv("HIL_APPROVAL_TIMEOUT_SECONDS", "3600"))  # 1 hour default
HIL_POLL_INTERVAL_SECONDS = int(os.getenv("HIL_POLL_INTERVAL_SECONDS", "2"))  # 2 seconds default
HIL_CONFIDENCE_THRESHOLD = float(os.getenv("HIL_CONFIDENCE_THRESHOLD", "0.85"))  # Below this triggers HIL
HIL_ENABLED = os.getenv("HIL_ENABLED", "true").lower() == "true"


class WorkflowExecutor:
    """
    Executes the unified pharmaceutical test generation workflow.

    Responsible for:
    - Loading URS documents from storage
    - Executing UnifiedWorkflow end-to-end
    - Saving generated test suites
    - Langfuse trace management
    - ALCOA+ compliant logging

    CRITICAL: NO FALLBACK LOGIC - All errors must fail explicitly
    """

    def __init__(
        self,
        storage_adapter: LocalStorageAdapter | None = None,
        vector_adapter: ChromaVectorStoreAdapter | None = None
    ):
        """
        Initialize workflow executor with storage adapters.

        Args:
            storage_adapter: Storage adapter for artifacts (default: LocalStorageAdapter)
            vector_adapter: Vector store adapter (default: ChromaVectorStoreAdapter)
        """
        self.storage_adapter = storage_adapter or LocalStorageAdapter(base_path="/app/output")
        self.vector_adapter = vector_adapter

    @observe(name="execute_workflow", capture_input=True, capture_output=True)
    async def execute_workflow(
        self,
        job_id: str,
        urs_content: str,
        user_id: str,
        metadata: dict[str, Any],
        approved_category: int | None = None,
        stage_callback: Any | None = None
    ) -> dict[str, Any]:
        """
        Execute the complete pharmaceutical test generation workflow.

        Workflow Steps:
        1. Initialize UnifiedWorkflow
        2. Run GAMP-5 categorization → parallel agents → test generation
        3. Save generated test suite to storage
        4. Return workflow results

        Args:
            job_id: Unique job identifier
            urs_content: URS document content (Markdown text)
            user_id: User identifier for audit trail
            metadata: Additional metadata (filename, hash, etc.)
            approved_category: Pre-approved GAMP category from HIL (skips categorization)
            stage_callback: Optional async callback(stage: str) for progress updates.
                           Called with 'agent_execution' and 'oq_generation' stages.

        Returns:
            dict containing:
                - test_suite_content: Generated YAML test suite
                - gamp_category: GAMP-5 category (1, 3, 4, 5)
                - result_uri: Storage URI for test suite
                - execution_time_seconds: Total workflow execution time
                - trace_id: Langfuse trace identifier
                - trace_url: Direct link to Langfuse trace for UI deep links

        Raises:
            ValueError: If URS content is invalid or empty
            RuntimeError: If workflow execution fails (with full diagnostic info)

        CRITICAL: NO FALLBACK LOGIC
        - Never return success if workflow fails
        - Never use placeholder/default values
        - Never mask exceptions with artificial success responses
        """
        start_time = datetime.now(UTC)

        # Validate inputs
        if not urs_content or not urs_content.strip():
            raise ValueError(
                f"CRITICAL: Empty or invalid URS content provided\n"
                f"Job ID: {job_id}\n"
                f"User ID: {user_id}\n"
                f"URS content length: {len(urs_content) if urs_content else 0}\n"
                "Cannot execute workflow without valid URS document"
            )

        trace_tags = [f"job_id:{job_id}", f"user_id:{user_id}"]
        trace_metadata = {
            "jobId": job_id,
            "userId": user_id,
            "ursFilename": metadata.get("urs_filename", "unknown")
        }

        def _safe_update_trace(**kwargs: Any) -> None:
            try:
                langfuse_client = get_client()
                if langfuse_client:
                    langfuse_client.update_current_trace(**kwargs)
            except Exception as update_error:
                logger.warning(f"Failed to update Langfuse trace context: {update_error}")

        # CRITICAL: Tag trace with job_id for observability filtering
        _safe_update_trace(tags=trace_tags, metadata=trace_metadata)

        propagation_context = nullcontext()
        if propagate_attributes is not None:
            try:
                propagation_context = propagate_attributes(
                    user_id=user_id,
                    tags=trace_tags,
                    metadata=trace_metadata
                )
            except Exception as e:
                logger.warning(f"Failed to propagate Langfuse attributes: {e}")
        else:
            logger.debug("Langfuse SDK does not expose propagate_attributes; skipping context propagation.")

        try:
            with propagation_context:
                # Save URS content to temporary file (workflow expects file path, not content)
                import tempfile
                from pathlib import Path

                temp_dir = Path("/tmp/urs_documents")
                temp_dir.mkdir(parents=True, exist_ok=True)
                temp_urs_path = temp_dir / f"{job_id}.md"

                logger.info(f"Saving URS content to temporary file: {temp_urs_path}")
                temp_urs_path.write_text(urs_content, encoding="utf-8")

                # Initialize UnifiedTestGenerationWorkflow
                # Pass approved_category if HIL already approved (skips categorization step)
                workflow = UnifiedTestGenerationWorkflow(
                    approved_category=approved_category
                )
                logger.info(f"UnifiedTestGenerationWorkflow initialized for job {job_id}")

                # Execute workflow
                # If approved_category is set (HIL re-execution), categorization step will be skipped
                if approved_category:
                    logger.info(
                        f"[HIL-RESUME] Executing workflow with pre-approved category {approved_category}\n"
                        f"  Job ID: {job_id}\n"
                        f"  Expected duration: 3-4 minutes (categorization skipped)"
                    )
                else:
                    logger.info(f"Executing UnifiedTestGenerationWorkflow for job {job_id} (expect 5-6 minutes)...")

                # Update stage to AGENT_EXECUTION before running workflow
                # The workflow includes parallel agent execution (Context, SME, Research)
                if stage_callback is not None:
                    try:
                        await stage_callback("agent_execution")
                    except Exception as cb_err:
                        logger.warning(f"Stage callback failed for agent_execution: {cb_err}")

                workflow_result_raw = await workflow.run(
                    document_path=str(temp_urs_path)
                )

                # Update stage to OQ_GENERATION after workflow completes but before saving
                # OQ generation happened during workflow.run() - this reflects completion of that phase
                if stage_callback is not None:
                    try:
                        await stage_callback("oq_generation")
                    except Exception as cb_err:
                        logger.warning(f"Stage callback failed for oq_generation: {cb_err}")

                if not workflow_result_raw:
                    raise RuntimeError(
                        f"CRITICAL: Workflow returned None/empty result\n"
                        f"Job ID: {job_id}\n"
                        f"Expected: WorkflowResult with test_suite, gamp_category, etc.\n"
                        f"Actual: {workflow_result_raw}\n"
                        "This indicates a critical workflow failure"
                    )

                # Unwrap StopEvent to get actual dictionary
                if hasattr(workflow_result_raw, "result"):
                    workflow_result = workflow_result_raw.result
                else:
                    workflow_result = workflow_result_raw

                # Validate result is a dictionary
                if not isinstance(workflow_result, dict):
                    raise RuntimeError(
                        f"CRITICAL: Workflow returned invalid type: {type(workflow_result)}. "
                        f"Expected dict containing workflow results. "
                        f"Job ID: {job_id}. "
                        f"Value: {workflow_result}"
                    )

                # Validate mandatory test_suite key exists
                if "test_suite" not in workflow_result:
                    available_keys = list(workflow_result.keys())
                    raise RuntimeError(
                        f"CRITICAL: Workflow result missing mandatory 'test_suite' key. "
                        f"Job ID: {job_id}. "
                        f"Available keys: {available_keys}. "
                        f"This indicates OQ test generation failed or didn't emit results."
                    )

                logger.debug(
                    f"Workflow result unwrapped successfully. "
                    f"Type: {type(workflow_result)}, "
                    f"Keys: {list(workflow_result.keys())}"
                )

                # Extract results
                test_suite_content = workflow_result.get("test_suite")
                gamp_category = workflow_result.get("gamp_category")

                # Extract HIL-related categorization metadata
                # The workflow returns categorization info at multiple locations:
                # 1. workflow_result["categorization"] - primary location with confidence, review_required
                # 2. workflow_result["summary"] - contains review_required, confidence
                categorization_data = workflow_result.get("categorization", {})
                summary_data = workflow_result.get("summary", {})

                if isinstance(categorization_data, dict):
                    review_required = categorization_data.get("review_required", False)
                    has_ambiguity_signals = False  # Will be set from summary if available
                    confidence_score = categorization_data.get("confidence_score",
                                       categorization_data.get("confidence", 1.0))
                    alternative_categories = categorization_data.get("alternative_categories")
                    ambiguity_reason = categorization_data.get("ambiguity_reason")
                    categorization_reasoning = categorization_data.get("reasoning", "")
                else:
                    # Default values if categorization data not available
                    review_required = False
                    has_ambiguity_signals = False
                    confidence_score = 1.0
                    alternative_categories = None
                    ambiguity_reason = None
                    categorization_reasoning = ""

                # Override from summary if available (more reliable source)
                if isinstance(summary_data, dict):
                    review_required = summary_data.get("review_required", review_required)
                    confidence_score = summary_data.get("confidence", confidence_score)

                logger.debug(
                    f"HIL metadata extracted: review_required={review_required}, "
                    f"ambiguity={has_ambiguity_signals}, confidence={confidence_score}"
                )

                if gamp_category:
                    _safe_update_trace(
                        tags=trace_tags + [f"gamp_category:{gamp_category}"],
                        metadata={
                            **trace_metadata,
                            "gampCategory": str(gamp_category)
                        }
                    )

                if not test_suite_content:
                    raise RuntimeError(
                        f"CRITICAL: Workflow completed but no test suite generated\n"
                        f"Job ID: {job_id}\n"
                        f"GAMP Category: {gamp_category}\n"
                        f"Workflow result keys: {list(workflow_result.keys())}\n"
                        "Test suite generation is mandatory - this is a workflow failure"
                    )

                logger.info(
                    f"Workflow completed successfully\n"
                    f"  Job ID: {job_id}\n"
                    f"  GAMP Category: {gamp_category}\n"
                    f"  Test suite length: {len(test_suite_content)} characters"
                )

                # Save test suite to storage
                artifact_metadata = {
                    "gamp_category": str(gamp_category),
                    "job_id": job_id,
                    "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                    "created_by": user_id,
                    "artifact_type": "test_suite",
                    "format": "yaml",  # Explicitly set format to match file extension
                    "urs_filename": metadata.get("urs_filename", "unknown"),
                    "urs_hash": metadata.get("urs_hash", "unknown")
                }

                result_uri = await self.storage_adapter.save_artifact(
                    artifact_id=f"{job_id}/test_suite.yaml",
                    content=test_suite_content.encode("utf-8"),
                    metadata=artifact_metadata
                )

                logger.info(f"Test suite saved: {result_uri}")

                # Calculate execution time
                end_time = datetime.now(UTC)
                execution_time = (end_time - start_time).total_seconds()

                trace_id = "unknown"
                trace_url = None
                try:
                    langfuse_client = get_client()
                    if langfuse_client:
                        current_trace_id = langfuse_client.get_current_trace_id()
                        if current_trace_id:
                            trace_id = current_trace_id
                            trace_url = langfuse_client.get_trace_url(trace_id=current_trace_id)
                except Exception as trace_error:
                    logger.warning(f"Failed to capture Langfuse trace metadata: {trace_error}")

                # Flush traces to Langfuse immediately after job completion
                try:
                    langfuse_client = get_client()
                    if langfuse_client:
                        langfuse_client.flush()
                        logger.info(f"Langfuse traces flushed for job (trace_id={trace_id})")
                except Exception as flush_error:
                    logger.warning(f"Failed to flush Langfuse traces: {flush_error}")

                return {
                    "test_suite_content": test_suite_content,
                    "gamp_category": gamp_category,
                    "result_uri": result_uri,
                    "execution_time_seconds": execution_time,
                    "trace_id": trace_id,
                    "trace_url": trace_url,
                    "workflow_metadata": {
                        "start_time": start_time.isoformat() + "Z",
                        "end_time": end_time.isoformat() + "Z",
                        "urs_filename": metadata.get("urs_filename"),
                        "user_id": user_id,
                        # HIL-related metadata for Task 3.13
                        "review_required": review_required,
                        "has_ambiguity_signals": has_ambiguity_signals,
                        "confidence_score": confidence_score,
                        "alternative_categories": alternative_categories,
                        "ambiguity_reason": ambiguity_reason,
                        "categorization_reasoning": categorization_reasoning
                    }
                }

        except Exception as e:
            # Check if this is a HumanApprovalRequired wrapped by LlamaIndex
            hil_exc = _find_human_approval_required(e)
            if hil_exc is not None:
                logger.info(
                    f"[HIL-WEB] HumanApprovalRequired found in exception chain for job {job_id}\n"
                    f"  Original error: {type(e).__name__}: {e!s}\n"
                    f"  HIL message: {str(hil_exc)}"
                )
                # Re-raise the HumanApprovalRequired directly so worker can catch it
                raise hil_exc from e

            # Log complete error context for debugging
            logger.exception(
                f"WORKFLOW EXECUTION FAILED\n"
                f"Job ID: {job_id}\n"
                f"User ID: {user_id}\n"
                f"Error: {e!s}\n"
                f"Stack trace: {traceback.format_exc()}"
            )

            # Re-raise with additional context
            raise RuntimeError(
                f"CRITICAL: Workflow execution failed\n"
                f"Job ID: {job_id}\n"
                f"User ID: {user_id}\n"
                f"URS filename: {metadata.get('urs_filename', 'unknown')}\n"
                f"Error type: {type(e).__name__}\n"
                f"Error message: {e!s}\n"
                "See logs for full stack trace"
            ) from e


async def read_urs_from_storage(storage_adapter: LocalStorageAdapter, job_id: str) -> str:
    """
    Read URS document content from storage.

    Args:
        storage_adapter: Storage adapter instance
        job_id: Job identifier

    Returns:
        URS document content as string

    Raises:
        FileNotFoundError: If URS file not found in storage
        RuntimeError: If file read fails

    CRITICAL: NO FALLBACK LOGIC - Never return empty string on error
    """
    try:
        # CRITICAL: Try new subdirectory format first (job_id/urs_document.md)
        # This resolves filesystem conflict where URS FILE blocked test suite DIRECTORY
        try:
            urs_bytes = await storage_adapter.retrieve_artifact(f"{job_id}/urs_document.md")
        except FileNotFoundError:
            # Backward compatibility: Try legacy format (job_id at root level)
            logger.warning(
                f"URS not found in new format ({job_id}/urs_document.md), "
                f"trying legacy format ({job_id})"
            )
            urs_bytes = await storage_adapter.retrieve_artifact(job_id)

        if not urs_bytes:
            raise RuntimeError(
                f"CRITICAL: URS file is empty\n"
                f"Job ID: {job_id}\n"
                f"Tried formats: {job_id}/urs_document.md, {job_id}\n"
                "Cannot process empty URS document"
            )

        return urs_bytes.decode("utf-8")

    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"CRITICAL: URS document not found in storage\n"
            f"Job ID: {job_id}\n"
            f"Expected artifact: {job_id}.json\n"
            f"Storage base path: {storage_adapter.base_path}\n"
            "URS must be uploaded before workflow execution"
        ) from e
    except Exception as e:
        raise RuntimeError(
            f"CRITICAL: Failed to read URS from storage\n"
            f"Job ID: {job_id}\n"
            f"Error: {e!s}\n"
            f"Stack trace: {traceback.format_exc()}"
        ) from e

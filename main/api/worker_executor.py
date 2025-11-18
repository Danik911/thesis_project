"""
Worker execution logic for pharmaceutical test generation workflow.

This module implements the actual workflow execution for background jobs,
integrating with the UnifiedWorkflow to process URS documents end-to-end.

CRITICAL: NO FALLBACK LOGIC
- All errors must raise exceptions with full context
- All status updates must reflect actual state
- All failures must be logged with complete diagnostic information
"""

import asyncio
import json
import logging
import traceback
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from langfuse import observe

from main.src.adapters.chroma_adapter import ChromaVectorStoreAdapter
from main.src.adapters.local_adapter import LocalStorageAdapter
from main.src.core.unified_workflow import UnifiedTestGenerationWorkflow

logger = logging.getLogger(__name__)


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
        metadata: dict[str, Any]
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

        Returns:
            dict containing:
                - test_suite_content: Generated YAML test suite
                - gamp_category: GAMP-5 category (1, 3, 4, 5)
                - result_uri: Storage URI for test suite
                - execution_time_seconds: Total workflow execution time
                - trace_id: Phoenix trace identifier

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

        logger.info(
            f"Starting workflow execution\n"
            f"  Job ID: {job_id}\n"
            f"  User ID: {user_id}\n"
            f"  URS length: {len(urs_content)} characters\n"
            f"  URS filename: {metadata.get('urs_filename', 'unknown')}"
        )

        try:
            # Save URS content to temporary file (workflow expects file path, not content)
            import tempfile
            from pathlib import Path

            temp_dir = Path("/tmp/urs_documents")
            temp_dir.mkdir(parents=True, exist_ok=True)
            temp_urs_path = temp_dir / f"{job_id}.md"

            logger.info(f"Saving URS content to temporary file: {temp_urs_path}")
            temp_urs_path.write_text(urs_content, encoding="utf-8")

            # Initialize UnifiedTestGenerationWorkflow
            workflow = UnifiedTestGenerationWorkflow()
            logger.info(f"UnifiedTestGenerationWorkflow initialized for job {job_id}")

            # Execute workflow (this takes 5-6 minutes for Category 3 URS)
            logger.info(f"Executing UnifiedTestGenerationWorkflow for job {job_id} (expect 5-6 minutes)...")
            workflow_result_raw = await workflow.run(
                document_path=str(temp_urs_path)
            )

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

            return {
                "test_suite_content": test_suite_content,
                "gamp_category": gamp_category,
                "result_uri": result_uri,
                "execution_time_seconds": execution_time,
                "trace_id": workflow_result.get("trace_id", "unknown"),
                "workflow_metadata": {
                    "start_time": start_time.isoformat() + "Z",
                    "end_time": end_time.isoformat() + "Z",
                    "urs_filename": metadata.get("urs_filename"),
                    "user_id": user_id
                }
            }

        except Exception as e:
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

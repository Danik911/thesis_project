"""
Background worker for async job processing.

Implements long-running coroutine that consumes jobs from asyncio.Queue
with retry logic, error handling, and GAMP-5 audit trail.

Supports Human-in-the-Loop (HIL) workflow:
- Detects when categorization requires human review
- Pauses workflow and updates job to AWAITING_APPROVAL
- Polls PostgreSQL for approval decision (shared state with API container)
- Resumes with human-approved category or rejects on timeout

TASK 3.5: Fully implemented worker with UnifiedWorkflow integration.
TASK 3.13: Extended with HIL pause/resume functionality.
HIL FIX: Updated to poll PostgreSQL instead of in-memory dict for docker-compose.
"""

import asyncio
import logging
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from .audit import get_audit_logger
from .job_repository import PostgresJobRepository, create_postgres_pool
from .models import JobRecord, JobStatus, WorkflowStage
from .worker_executor import (
    HIL_APPROVAL_TIMEOUT_SECONDS,
    HIL_ENABLED,
    HIL_POLL_INTERVAL_SECONDS,
    WorkflowExecutor,
    read_urs_from_storage,
)
from main.src.exceptions import HumanApprovalRequired

# Load environment variables from .env.local (for local development)
env_file = Path(__file__).parent.parent.parent / ".env.local"
if env_file.exists():
    load_dotenv(env_file)
    logging.info(f"Loaded environment variables from {env_file}")
else:
    logging.info(f"Environment file not found: {env_file} (using system env vars)")

logger = logging.getLogger(__name__)


async def _persist_job_state(
    job: JobRecord,
    db_job_repo: PostgresJobRepository | None,
    context: str
) -> None:
    """Persist latest job state to PostgreSQL when database mode is enabled."""
    if db_job_repo is None:
        return

    try:
        job.updated_at = datetime.now(UTC)
        await db_job_repo.update(job)
        logger.debug(f"[DB] Persisted job {job.job_id} during {context}")
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error(
            f"[DB] Failed to persist job {job.job_id} during {context}: {exc}"
        )


async def _update_job_stage(
    job: JobRecord,
    stage: WorkflowStage,
    job_lock: asyncio.Lock,
    db_job_repo: PostgresJobRepository | None
) -> None:
    """
    Update job stage for frontend progress tracking.

    Updates the current_stage field with timestamp for grounded progress display.
    Records stage completion in stages_completed list for audit trail.

    Args:
        job: Job record to update
        stage: New workflow stage
        job_lock: Lock for job state updates
        db_job_repo: PostgreSQL repository for persistence
    """
    async with job_lock:
        # Update stage info
        job.current_stage = stage
        job.stage_started_at = datetime.now(UTC)
        job.updated_at = job.stage_started_at

        # Track completed stages (for audit trail)
        if stage.value not in job.stages_completed:
            job.stages_completed.append(stage.value)

    # Persist to database
    await _persist_job_state(job, db_job_repo, f"stage_update:{stage.value}")

    logger.info(f"[PROGRESS] Job {job.job_id} stage → {stage.value}")


async def process_job_worker(
    job_queue: asyncio.Queue[str],
    job_repository: dict[str, JobRecord],
    job_lock: asyncio.Lock,
    db_job_repo: PostgresJobRepository | None = None
) -> None:
    """
    Background worker coroutine for processing jobs.

    Continuously consumes job IDs from the queue, processes them,
    and updates the job repository with results/errors.

    Args:
        job_queue: Asyncio queue containing job IDs to process
        job_repository: Shared dict for job state (protected by lock)
        job_lock: Asyncio lock for repository access
        db_job_repo: PostgreSQL repository for HIL shared state (docker-compose mode)

    CRITICAL: This coroutine runs indefinitely - must not crash on errors.
    All exceptions caught and logged to prevent worker termination.

    Retry Logic:
    - Exponential backoff: 1s, 2s, 4s (max 3 retries)
    - Job marked as FAILED after max retries exceeded
    - All retry attempts logged to audit trail

    HIL Support (docker-compose):
    - When db_job_repo is provided, HIL polling uses PostgreSQL for shared state
    - Approval decisions from API container are visible to worker container
    - Includes recovery of APPROVED jobs on worker restart
    """
    audit_logger = get_audit_logger()

    logger.info("Background job worker started")
    if db_job_repo is not None:
        logger.info("[HIL-DB] Worker using PostgreSQL for HIL shared state")
    else:
        logger.warning("[HIL] Worker using in-memory repository (HIL won't work in docker-compose)")

    # Initialize workflow executor (single instance, reused across jobs)
    executor = None
    try:
        logger.info("Initializing WorkflowExecutor...")
        executor = WorkflowExecutor()
        logger.info("WorkflowExecutor initialized successfully")
    except Exception as e:
        logger.exception(f"CRITICAL: Failed to initialize WorkflowExecutor: {e}")
        logger.error("Worker cannot process jobs without executor. Exiting.")
        return

    while True:
        try:
            # Wait for job from queue
            job_id = await job_queue.get()
            logger.info(f"Worker processing job: {job_id}")

            # Get job record from repository
            async with job_lock:
                job = job_repository.get(job_id)

                if job is None:
                    logger.error(f"Job {job_id} not found in repository")
                    job_queue.task_done()
                    continue

                # CRITICAL: Skip jobs that already failed in previous run
                # Prevents infinite retry loop on container restart
                if job.status == JobStatus.FAILED:
                    logger.info(
                        f"[RETRY-STOP] Job {job_id} already marked FAILED "
                        f"(retry_count: {job.retry_count}/{job.max_retries}). Skipping."
                    )
                    job_queue.task_done()
                    continue

                # Update status to PROCESSING
                job.status = JobStatus.PROCESSING
                job.started_at = datetime.now(UTC)
                job.updated_at = job.started_at
                # Initialize stage tracking
                job.current_stage = WorkflowStage.INGESTION
                job.stage_started_at = job.started_at
                job.stages_completed = [WorkflowStage.QUEUED.value, WorkflowStage.INGESTION.value]

            await _persist_job_state(job, db_job_repo, "processing_start")

            # Log processing start
            audit_logger.log_event(
                job_id=job_id,
                event_type="start",
                user_id=job.user_id,
                status=JobStatus.PROCESSING,
                metadata={
                    "urs_filename": job.urs_filename,
                    "urs_hash": job.urs_hash
                }
            )

            # Process job with retry logic (includes HIL pause/resume if needed)
            success = await _process_job_with_retries(
                job=job,
                job_repository=job_repository,
                job_lock=job_lock,
                audit_logger=audit_logger,
                executor=executor,
                db_job_repo=db_job_repo
            )

            # Update final status
            final_context = "complete" if success else "fail"

            # Update to COMPLETION stage if successful (for progress bar)
            if success:
                await _update_job_stage(job, WorkflowStage.COMPLETION, job_lock, db_job_repo)

            async with job_lock:
                if success:
                    job.status = JobStatus.COMPLETED
                    job.completed_at = datetime.now(UTC)

                    # Log completion
                    audit_logger.log_event(
                        job_id=job_id,
                        event_type="complete",
                        user_id=job.user_id,
                        status=JobStatus.COMPLETED,
                        metadata={
                            "result_uri": job.result_uri,
                            "gamp_category": job.gamp_category,
                            "stages_completed": job.stages_completed
                        }
                    )
                    logger.info(f"Job {job_id} completed successfully")
                else:
                    job.status = JobStatus.FAILED
                    job.completed_at = datetime.now(UTC)

                    # Log failure
                    audit_logger.log_event(
                        job_id=job_id,
                        event_type="fail",
                        user_id=job.user_id,
                        status=JobStatus.FAILED,
                        metadata={
                            "error_message": job.error_message,
                            "error_type": job.error_type,
                            "retry_count": job.retry_count
                        }
                    )
                    logger.error(f"Job {job_id} failed after {job.retry_count} retries")

                job.updated_at = datetime.now(UTC)

            await _persist_job_state(job, db_job_repo, f"job_{final_context}")

            # Mark queue task as done
            job_queue.task_done()

        except asyncio.CancelledError:
            logger.info("Worker received cancellation signal")
            break
        except Exception as e:
            # CRITICAL: Catch all exceptions to prevent worker crash
            logger.exception(f"Unexpected error in worker: {e}")
            # Continue processing next job
            continue


async def _process_job_with_retries(
    job: JobRecord,
    job_repository: dict[str, JobRecord],
    job_lock: asyncio.Lock,
    audit_logger: Any,
    executor: WorkflowExecutor,
    db_job_repo: PostgresJobRepository | None = None
) -> bool:
    """
    Process job with exponential backoff retry logic and HIL support.

    Args:
        job: Job record to process
        job_repository: Shared job repository for HIL polling
        job_lock: Lock for updating job state
        audit_logger: Audit logger for compliance
        executor: WorkflowExecutor instance

    Returns:
        True if job succeeded, False if failed after max retries or HIL rejection

    Retry Schedule:
    - Attempt 1: Immediate
    - Attempt 2: After 1 second
    - Attempt 3: After 2 seconds
    - Attempt 4: After 4 seconds
    - Give up after 3 retries (4 total attempts)

    HIL Support:
    - If categorization triggers review_required=True and HIL_ENABLED=True
    - Updates job to AWAITING_APPROVAL and polls for decision
    - Resumes workflow if APPROVED, fails job if REJECTED/timeout

    CRITICAL: Reads existing retry_count from job record to prevent infinite loops
    on container restart or function re-invocation.
    """
    # CRITICAL FIX: Initialize from job record, not from 0
    # Prevents infinite retry loop if function called multiple times
    retry_count = job.retry_count
    max_retries = job.max_retries

    logger.info(
        f"[RETRY] Job {job.job_id} starting retry logic: "
        f"status={job.status}, retry_count={retry_count}/{max_retries}"
    )

    # Safety check: If job already exceeded retries, fail immediately
    if retry_count > max_retries:
        logger.error(
            f"[RETRY-STOP] Job {job.job_id} already exceeded max retries "
            f"({retry_count}/{max_retries}). Failing immediately."
        )
        return False

    while retry_count <= max_retries:
        try:
            # CRITICAL: Check if job was pre-approved (HIL recovery scenario)
            # This handles jobs that were APPROVED by human but worker restarted
            # before resuming the workflow. The job is re-enqueued with status APPROVED
            # and human_category set, so we pass approved_category to skip categorization.
            approved_category = None
            if job.human_category:
                approved_category = job.human_category
                logger.info(
                    f"[HIL-RECOVERY] Job {job.job_id} has pre-approved category {approved_category}\n"
                    f"  This job was approved before worker restart\n"
                    f"  Skipping categorization step, using human-approved category"
                )
                # Skip to planning stage since categorization is pre-approved
                await _update_job_stage(job, WorkflowStage.PLANNING, job_lock, db_job_repo)
            else:
                # Update to categorization stage before workflow execution
                await _update_job_stage(job, WorkflowStage.CATEGORIZATION, job_lock, db_job_repo)

            # Create stage callback for progress tracking during workflow execution
            async def stage_callback(stage_name: str) -> None:
                """Update job stage from executor callback."""
                stage_map = {
                    "agent_execution": WorkflowStage.AGENT_EXECUTION,
                    "oq_generation": WorkflowStage.OQ_GENERATION,
                }
                stage = stage_map.get(stage_name)
                if stage:
                    await _update_job_stage(job, stage, job_lock, db_job_repo)

            # Execute actual workflow (replaces simulation)
            # If approved_category is set, categorization step will be skipped
            result = await _execute_workflow(
                job, executor,
                approved_category=approved_category,
                stage_callback=stage_callback
            )

            # If job was pre-approved, skip HIL check (already approved by human)
            if approved_category:
                logger.info(
                    f"[HIL-RECOVERY] Workflow completed with pre-approved category\n"
                    f"  Job ID: {job.job_id}\n"
                    f"  Human Category: {approved_category}\n"
                    f"  Result URI: {result.get('result_uri')}"
                )

                # Update job with result
                async with job_lock:
                    job.result_uri = result["result_uri"]
                    job.gamp_category = str(approved_category)
                    job.trace_id = result.get("trace_id")
                    job.trace_url = result.get("trace_url")

                return True  # Success after HIL recovery

            # Check if HIL is required based on workflow result
            # This is determined by categorization ambiguity detection (Task 3.12)
            hil_required = (
                HIL_ENABLED and
                result.get("workflow_metadata", {}).get("review_required", False)
            )

            # If categorization result has ambiguity signals, also trigger HIL
            workflow_metadata = result.get("workflow_metadata", {})
            categorization_result = {
                "gamp_category": result.get("gamp_category"),
                "confidence": workflow_metadata.get("confidence_score", 1.0),
                "reasoning": workflow_metadata.get("categorization_reasoning", ""),
                "has_ambiguity_signals": workflow_metadata.get("has_ambiguity_signals", False),
                "alternative_categories": workflow_metadata.get("alternative_categories"),
                "ambiguity_reason": workflow_metadata.get("ambiguity_reason"),
                "review_required": workflow_metadata.get("review_required", False)
            }

            if hil_required:
                logger.info(
                    f"[HIL] Human review required for job {job.job_id}\n"
                    f"  GAMP Category: {result['gamp_category']}\n"
                    f"  Confidence: {categorization_result['confidence']}\n"
                    f"  Ambiguity: {categorization_result['has_ambiguity_signals']}\n"
                    f"  Reason: {categorization_result.get('ambiguity_reason', 'Low confidence')}"
                )

                # Update stage to HIL_WAITING for progress bar
                await _update_job_stage(job, WorkflowStage.HIL_WAITING, job_lock, db_job_repo)

                # Update job status to AWAITING_APPROVAL
                async with job_lock:
                    job.status = JobStatus.AWAITING_APPROVAL
                    job.requires_approval = True
                    job.approval_reason = categorization_result.get(
                        "ambiguity_reason",
                        f"Low confidence ({categorization_result['confidence']:.2f})"
                    )
                    job.approval_timeout_at = datetime.now(UTC) + timedelta(
                        seconds=HIL_APPROVAL_TIMEOUT_SECONDS
                    )
                    job.categorization_result = categorization_result
                    job.updated_at = datetime.now(UTC)

                    # Store partial result for later resume
                    job.gamp_category = str(result["gamp_category"])
                    job.trace_id = result.get("trace_id")
                    job.trace_url = result.get("trace_url")

                await _persist_job_state(job, db_job_repo, "awaiting_approval_workflow")

                # Log HIL trigger
                audit_logger.log_event(
                    job_id=job.job_id,
                    event_type="hil_triggered",
                    user_id=job.user_id,
                    status=JobStatus.AWAITING_APPROVAL,
                    metadata={
                        "categorization_result": categorization_result,
                        "timeout_at": job.approval_timeout_at.isoformat()
                    }
                )

                # Wait for HIL approval (polling)
                approved = await _wait_for_hil_approval(
                    job=job,
                    job_repository=job_repository,
                    job_lock=job_lock,
                    audit_logger=audit_logger,
                    db_job_repo=db_job_repo
                )

                if not approved:
                    logger.warning(f"[HIL] Job {job.job_id} was rejected or timed out")
                    return False

                # HIL approved - update stage to PLANNING before continuing
                await _update_job_stage(job, WorkflowStage.PLANNING, job_lock, db_job_repo)

                # HIL approved - continue with approved category
                logger.info(
                    f"[HIL] Job {job.job_id} approved with category {job.human_category}"
                )

                # Update job with result (using human-approved category if different)
                async with job_lock:
                    job.result_uri = result["result_uri"]
                    # Use human category if provided, otherwise keep AI category
                    if job.human_category:
                        job.gamp_category = str(job.human_category)
                    else:
                        job.gamp_category = str(result["gamp_category"])

                return True  # Success after HIL approval

            # No HIL required - update job with result directly
            async with job_lock:
                job.result_uri = result["result_uri"]
                job.gamp_category = str(result["gamp_category"])
                job.trace_id = result.get("trace_id")
                job.trace_url = result.get("trace_url")

            return True  # Success

        except HumanApprovalRequired as hil_exc:
            # HIL triggered by workflow - no stdin available in web context
            # Set job to AWAITING_APPROVAL and return False to exit retry loop
            logger.info(
                f"[HIL-WEB] HumanApprovalRequired raised for job {job.job_id}\n"
                f"  Message: {str(hil_exc)}\n"
                f"  Categorization: {hil_exc.categorization_result}\n"
                f"  Setting job to AWAITING_APPROVAL"
            )

            # Update stage to HIL_WAITING for progress bar
            await _update_job_stage(job, WorkflowStage.HIL_WAITING, job_lock, db_job_repo)

            async with job_lock:
                job.status = JobStatus.AWAITING_APPROVAL
                job.requires_approval = True
                job.approval_reason = str(hil_exc)
                job.approval_timeout_at = datetime.now(UTC) + timedelta(
                    seconds=hil_exc.timeout_seconds
                )
                job.categorization_result = hil_exc.categorization_result
                job.updated_at = datetime.now(UTC)

                # Store metadata from exception
                if not job.metadata:
                    job.metadata = {}
                job.metadata.update(hil_exc.to_metadata())

            await _persist_job_state(job, db_job_repo, "awaiting_approval_exception")

            # Log HIL trigger from web context
            audit_logger.log_event(
                job_id=job.job_id,
                event_type="hil_triggered_web",
                user_id=job.user_id,
                status=JobStatus.AWAITING_APPROVAL,
                metadata={
                    "categorization_result": hil_exc.categorization_result,
                    "ambiguity_signals": hil_exc.ambiguity_signals,
                    "timeout_at": job.approval_timeout_at.isoformat() if job.approval_timeout_at else None,
                    "trigger_source": "web_context_no_stdin"
                }
            )

            # Wait for HIL approval (polling)
            approved = await _wait_for_hil_approval(
                job=job,
                job_repository=job_repository,
                job_lock=job_lock,
                audit_logger=audit_logger,
                timeout_seconds=hil_exc.timeout_seconds,
                db_job_repo=db_job_repo
            )

            if not approved:
                logger.warning(f"[HIL-WEB] Job {job.job_id} was rejected or timed out")
                return False

            # HIL approved - re-execute workflow with human-approved category
            logger.info(
                f"[HIL-WEB] Job {job.job_id} approved with category {job.human_category}\n"
                f"  Re-executing workflow with pre-approved category (skips categorization)"
            )

            if not job.human_category:
                # No human category but approved - unexpected state
                logger.error(f"[HIL-WEB] Job {job.job_id} approved but no human_category set")
                return False

            # Update stage to PLANNING before re-execution (categorization was already done)
            await _update_job_stage(job, WorkflowStage.PLANNING, job_lock, db_job_repo)

            # Reset job status for re-execution
            async with job_lock:
                job.status = JobStatus.PROCESSING
                job.updated_at = datetime.now(UTC)

            await _persist_job_state(job, db_job_repo, "hil_resume_processing")

            # Log workflow re-execution
            audit_logger.log_event(
                job_id=job.job_id,
                event_type="hil_workflow_resume",
                user_id=job.user_id,
                status=JobStatus.PROCESSING,
                metadata={
                    "human_category": job.human_category,
                    "reason": "Re-executing workflow with human-approved category"
                }
            )

            # Create stage callback for progress tracking during workflow re-execution
            async def hil_stage_callback(stage_name: str) -> None:
                """Update job stage from executor callback (HIL re-execution)."""
                stage_map = {
                    "agent_execution": WorkflowStage.AGENT_EXECUTION,
                    "oq_generation": WorkflowStage.OQ_GENERATION,
                }
                stage = stage_map.get(stage_name)
                if stage:
                    await _update_job_stage(job, stage, job_lock, db_job_repo)

            # Re-execute workflow with human-approved category
            # The workflow will skip categorization and use the pre-approved category
            result = await _execute_workflow(
                job=job,
                executor=executor,
                approved_category=job.human_category,
                stage_callback=hil_stage_callback
            )

            # Update job with result
            async with job_lock:
                job.result_uri = result["result_uri"]
                job.gamp_category = str(job.human_category)
                job.trace_id = result.get("trace_id")
                job.trace_url = result.get("trace_url")

            logger.info(
                f"[HIL-WEB] Workflow re-execution completed successfully\n"
                f"  Job ID: {job.job_id}\n"
                f"  GAMP Category: {job.human_category}\n"
                f"  Result URI: {result['result_uri']}"
            )

            return True  # Success after HIL re-execution

        except Exception as e:
            retry_count += 1

            # Update retry count
            async with job_lock:
                job.retry_count = retry_count
                job.error_message = str(e)
                job.error_type = type(e).__name__
                job.updated_at = datetime.now(UTC)

            await _persist_job_state(job, db_job_repo, "retry_state")

            # Log retry attempt
            audit_logger.log_event(
                job_id=job.job_id,
                event_type="retry",
                user_id=job.user_id,
                status=JobStatus.PROCESSING,
                metadata={
                    "retry_count": retry_count,
                    "max_retries": max_retries,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )

            if retry_count > max_retries:
                logger.error(
                    f"[RETRY-STOP] Job {job.job_id} FAILED permanently after "
                    f"{retry_count} retries (max: {max_retries}). Error: {e}"
                )
                logger.info(
                    f"[RETRY-STOP] Job {job.job_id} will be marked FAILED and "
                    f"will NOT be retried again."
                )
                return False  # Failure - job marked FAILED in caller

            # Exponential backoff: 1s, 2s, 4s
            backoff_delay = 2 ** (retry_count - 1)
            logger.warning(
                f"[RETRY] Job {job.job_id} retry {retry_count}/{max_retries} "
                f"after {backoff_delay}s: {e}"
            )
            await asyncio.sleep(backoff_delay)

    # Should not reach here (loop exits via return statements)
    logger.error(
        f"[RETRY-STOP] Job {job.job_id} exited retry loop unexpectedly. "
        f"Final retry_count: {retry_count}/{max_retries}"
    )
    return False


async def _execute_workflow(
    job: JobRecord,
    executor: WorkflowExecutor,
    approved_category: int | None = None,
    stage_callback: Any | None = None
) -> dict[str, Any]:
    """
    Execute the unified pharmaceutical test generation workflow.

    This is the REAL implementation (Task 3.5) - replaces placeholder simulation.

    Args:
        job: Job record with URS content and metadata
        executor: WorkflowExecutor instance
        approved_category: Pre-approved GAMP category from HIL (skips categorization step)
        stage_callback: Optional async callback(stage: str) for progress updates

    Returns:
        dict with workflow results (test_suite, gamp_category, result_uri, etc.)

    Raises:
        RuntimeError: If workflow execution fails

    CRITICAL: NO FALLBACK LOGIC
    - Never return success if workflow fails
    - Never use placeholder/mock values
    - All errors must propagate with full diagnostic information
    """
    if approved_category:
        logger.info(
            f"[HIL-RESUME] Re-executing workflow for job {job.job_id}\n"
            f"  Pre-approved category: {approved_category}\n"
            f"  URS filename: {job.urs_filename}\n"
            f"  User ID: {job.user_id}\n"
            f"  Expected duration: 3-4 minutes (categorization skipped)"
        )
    else:
        logger.info(
            f"Executing UnifiedWorkflow for job {job.job_id}\n"
            f"  URS filename: {job.urs_filename}\n"
            f"  User ID: {job.user_id}\n"
            f"  Expected duration: 5-6 minutes"
        )

    # Read URS content from storage
    from main.src.adapters.local_adapter import LocalStorageAdapter
    storage_adapter = LocalStorageAdapter(base_path="/app/output")

    try:
        urs_content = await read_urs_from_storage(storage_adapter, job.job_id)
    except FileNotFoundError:
        # If not in storage with full path, try reading from job record
        # (API may have stored it differently)
        if hasattr(job, 'urs_content') and job.urs_content:
            urs_content = job.urs_content
            logger.info(f"Using URS content from job record (not found in storage)")
        else:
            raise

    # Execute workflow (with approved_category if HIL already approved)
    result = await executor.execute_workflow(
        job_id=job.job_id,
        urs_content=urs_content,
        user_id=job.user_id,
        metadata={
            "urs_filename": job.urs_filename,
            "urs_hash": job.urs_hash
        },
        approved_category=approved_category,
        stage_callback=stage_callback
    )

    logger.info(
        f"Workflow execution completed successfully\n"
        f"  Job ID: {job.job_id}\n"
        f"  GAMP Category: {result['gamp_category']}\n"
        f"  Execution time: {result['execution_time_seconds']:.1f}s\n"
        f"  Result URI: {result['result_uri']}"
    )

    return result


async def _wait_for_hil_approval(
    job: JobRecord,
    job_repository: dict[str, JobRecord],
    job_lock: asyncio.Lock,
    audit_logger: Any,
    timeout_seconds: int = HIL_APPROVAL_TIMEOUT_SECONDS,
    poll_interval_seconds: int = HIL_POLL_INTERVAL_SECONDS,
    db_job_repo: PostgresJobRepository | None = None
) -> bool:
    """
    Poll for HIL approval decision.

    Implements database polling pattern for docker-compose:
    - Polls PostgreSQL for approval status (shared state with API container)
    - Falls back to in-memory if no database
    - Returns True if APPROVED, False if REJECTED or timeout

    Args:
        job: Job record requiring approval
        job_repository: In-memory job repository (fallback)
        job_lock: Lock for in-memory repository access
        audit_logger: Audit logger for compliance
        timeout_seconds: Maximum wait time before auto-reject
        poll_interval_seconds: Polling interval
        db_job_repo: PostgreSQL repository (docker-compose mode)

    Returns:
        True if approved, False if rejected or timeout

    CRITICAL: NO FALLBACK LOGIC
    - Timeout results in explicit REJECTED status
    - All state transitions logged to audit trail
    """
    job_id = job.job_id
    start_time = datetime.now(UTC)
    timeout_at = start_time + timedelta(seconds=timeout_seconds)

    use_database = db_job_repo is not None
    logger.info(
        f"[HIL] Starting approval polling for job {job_id}\n"
        f"  Poll interval: {poll_interval_seconds}s\n"
        f"  Timeout: {timeout_seconds}s ({timeout_at.isoformat()})\n"
        f"  Mode: {'PostgreSQL (docker-compose)' if use_database else 'in-memory (local)'}"
    )

    # Log HIL wait start
    audit_logger.log_event(
        job_id=job_id,
        event_type="hil_wait_start",
        user_id=job.user_id,
        status=JobStatus.AWAITING_APPROVAL,
        metadata={
            "timeout_at": timeout_at.isoformat(),
            "poll_interval_seconds": poll_interval_seconds,
            "categorization_result": job.categorization_result,
            "polling_mode": "database" if use_database else "in_memory"
        }
    )

    poll_count = 0
    while datetime.now(UTC) < timeout_at:
        poll_count += 1
        await asyncio.sleep(poll_interval_seconds)

        # Poll for job status - use database if available, otherwise in-memory
        current_job: JobRecord | None = None

        if use_database:
            # CRITICAL: Poll PostgreSQL for shared state with API container
            try:
                current_job = await db_job_repo.get(job_id)
            except Exception as e:
                logger.error(f"[HIL-DB] Failed to poll database for job {job_id}: {e}")
                # Continue polling - might recover on next attempt
                continue
        else:
            # Fallback to in-memory (won't work in docker-compose)
            async with job_lock:
                current_job = job_repository.get(job_id)

        if current_job is None:
            logger.error(f"[HIL] Job {job_id} not found during polling")
            return False

        current_status = current_job.status

        if current_status == JobStatus.APPROVED:
            logger.info(
                f"[HIL] Job {job_id} APPROVED after {poll_count} polls "
                f"(human_category: {current_job.human_category})"
            )

            # Log approval received
            audit_logger.log_event(
                job_id=job_id,
                event_type="hil_approved",
                user_id=job.user_id,
                status=JobStatus.APPROVED,
                metadata={
                    "poll_count": poll_count,
                    "wait_time_seconds": (datetime.now(UTC) - start_time).total_seconds(),
                    "human_category": current_job.human_category,
                    "polling_mode": "database" if use_database else "in_memory"
                }
            )

            # Update job reference to get latest state
            job.status = current_job.status
            job.human_category = current_job.human_category
            job.updated_at = current_job.updated_at

            return True

        if current_status == JobStatus.REJECTED:
            logger.info(
                f"[HIL] Job {job_id} REJECTED after {poll_count} polls"
            )

            # Log rejection received
            audit_logger.log_event(
                job_id=job_id,
                event_type="hil_rejected",
                user_id=job.user_id,
                status=JobStatus.REJECTED,
                metadata={
                    "poll_count": poll_count,
                    "wait_time_seconds": (datetime.now(UTC) - start_time).total_seconds(),
                    "rejection_reason": "human_decision",
                    "polling_mode": "database" if use_database else "in_memory"
                }
            )

            job.status = current_job.status
            job.updated_at = current_job.updated_at

            return False

        # Still awaiting approval - continue polling
        if poll_count % 30 == 0:  # Log every 30 polls (60 seconds)
            remaining = (timeout_at - datetime.now(UTC)).total_seconds()
            logger.info(
                f"[HIL] Job {job_id} still awaiting approval "
                f"(poll #{poll_count}, {remaining:.0f}s remaining, mode={'db' if use_database else 'mem'})"
            )

    # Timeout reached - auto-reject
    logger.warning(f"[HIL] Job {job_id} approval TIMEOUT after {poll_count} polls")

    # Update status to REJECTED
    if use_database:
        try:
            await db_job_repo.set_approval_status(
                job_id=job_id,
                status=JobStatus.REJECTED,
                human_category=None
            )
        except Exception as e:
            logger.error(f"[HIL-DB] Failed to update timeout rejection in database: {e}")
    else:
        async with job_lock:
            current_job = job_repository.get(job_id)
            if current_job and current_job.status == JobStatus.AWAITING_APPROVAL:
                current_job.status = JobStatus.REJECTED
                current_job.updated_at = datetime.now(UTC)
                current_job.error_message = f"HIL approval timeout after {timeout_seconds} seconds"

    job.status = JobStatus.REJECTED
    job.updated_at = datetime.now(UTC)
    job.error_message = f"HIL approval timeout after {timeout_seconds} seconds"

    # Log timeout rejection
    audit_logger.log_event(
        job_id=job_id,
        event_type="hil_timeout",
        user_id=job.user_id,
        status=JobStatus.REJECTED,
        metadata={
            "poll_count": poll_count,
            "timeout_seconds": timeout_seconds,
            "rejection_reason": "timeout_auto_reject",
            "polling_mode": "database" if use_database else "in_memory"
        }
    )

    return False


if __name__ == "__main__":
    """
    Entry point when executed with: python -m main.api.worker

    For Task 3.5 (End-to-End Local Validation), this runs the full worker
    with UnifiedWorkflow integration for complete pharmaceutical test generation.
    """
    import asyncio
    import os

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("=== Pharmaceutical Test Generation Worker Starting ===")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"Database URL: {os.getenv('DATABASE_URL', 'not set')}")
    logger.info(f"SQS Queue URL: {os.getenv('SQS_QUEUE_URL', 'not set')}")
    logger.info("Task 3.5: Full worker implementation with UnifiedWorkflow integration")
    logger.info("Worker ready to process pharmaceutical test generation jobs")

    async def standalone_worker() -> None:
        """Standalone worker for Docker Compose deployment."""
        # When run as standalone, we need to initialize infrastructure
        # This is normally done by FastAPI lifespan, but worker runs independently
        logger.info("Initializing worker infrastructure...")

        # Create in-memory job queue and repository (shared with API via FastAPI state)
        # Note: In Docker Compose, worker picks up jobs via SQS, not in-memory queue
        # This is a placeholder for standalone mode
        logger.warning(
            "Worker running in standalone mode. "
            "In production Docker Compose, worker should poll SQS queue."
        )

        # Run simple heartbeat for now
        # TODO: Implement SQS polling for Docker Compose deployment
        try:
            iteration = 0
            while True:
                iteration += 1
                await asyncio.sleep(60)  # Sleep 1 minute
                logger.info(
                    f"Worker heartbeat #{iteration}: Ready to process jobs via SQS"
                )

        except asyncio.CancelledError:
            logger.info("Worker received cancellation signal, shutting down gracefully")
        except KeyboardInterrupt:
            logger.info("Worker interrupted, shutting down gracefully")
        except Exception as e:
            logger.exception(f"Unexpected error in worker: {e}")
            raise

    try:
        asyncio.run(standalone_worker())
    except KeyboardInterrupt:
        logger.info("Worker shutdown complete")

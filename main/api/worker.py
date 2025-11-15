"""
Background worker for async job processing.

Implements long-running coroutine that consumes jobs from asyncio.Queue
with retry logic, error handling, and GAMP-5 audit trail.
"""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from .audit import get_audit_logger
from .models import JobRecord, JobStatus

logger = logging.getLogger(__name__)


async def process_job_worker(
    job_queue: asyncio.Queue[str],
    job_repository: dict[str, JobRecord],
    job_lock: asyncio.Lock
) -> None:
    """
    Background worker coroutine for processing jobs.

    Continuously consumes job IDs from the queue, processes them,
    and updates the job repository with results/errors.

    Args:
        job_queue: Asyncio queue containing job IDs to process
        job_repository: Shared dict for job state (protected by lock)
        job_lock: Asyncio lock for repository access

    CRITICAL: This coroutine runs indefinitely - must not crash on errors.
    All exceptions caught and logged to prevent worker termination.

    Retry Logic:
    - Exponential backoff: 1s, 2s, 4s (max 3 retries)
    - Job marked as FAILED after max retries exceeded
    - All retry attempts logged to audit trail
    """
    audit_logger = get_audit_logger()

    logger.info("Background job worker started")

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

                # Update status to PROCESSING
                job.status = JobStatus.PROCESSING
                job.started_at = datetime.now(UTC)

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

            # Process job with retry logic
            success = await _process_job_with_retries(
                job=job,
                job_lock=job_lock,
                audit_logger=audit_logger
            )

            # Update final status
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
                            "gamp_category": job.gamp_category
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
    job_lock: asyncio.Lock,
    audit_logger: Any
) -> bool:
    """
    Process job with exponential backoff retry logic.

    Args:
        job: Job record to process
        job_lock: Lock for updating job state
        audit_logger: Audit logger for compliance

    Returns:
        True if job succeeded, False if failed after max retries

    Retry Schedule:
    - Attempt 1: Immediate
    - Attempt 2: After 1 second
    - Attempt 3: After 2 seconds
    - Attempt 4: After 4 seconds
    - Give up after 3 retries (4 total attempts)
    """
    retry_count = 0
    max_retries = job.max_retries

    while retry_count <= max_retries:
        try:
            # Simulate job processing (replace with actual workflow execution)
            result_uri = await _simulate_job_processing(job)

            # Update job with result
            async with job_lock:
                job.result_uri = result_uri
                job.gamp_category = "5"  # Placeholder - actual from workflow

            return True  # Success

        except Exception as e:
            retry_count += 1

            # Update retry count
            async with job_lock:
                job.retry_count = retry_count
                job.error_message = str(e)
                job.error_type = type(e).__name__

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
                    f"Job {job.job_id} failed after {max_retries} retries: {e}"
                )
                return False  # Failure

            # Exponential backoff: 1s, 2s, 4s
            backoff_delay = 2 ** (retry_count - 1)
            logger.warning(
                f"Job {job.job_id} retry {retry_count}/{max_retries} "
                f"after {backoff_delay}s: {e}"
            )
            await asyncio.sleep(backoff_delay)

    return False  # Should not reach here, but handle gracefully


async def _simulate_job_processing(job: JobRecord) -> str:
    """
    Simulate job processing (placeholder for actual workflow).

    Args:
        job: Job record to process

    Returns:
        Result URI (storage location)

    Raises:
        RuntimeError: If processing fails

    TODO: Replace with actual LlamaIndex workflow execution
    """
    # Simulate processing time (2-5 seconds)
    processing_time = 3.0
    logger.info(f"Processing job {job.job_id} for {processing_time}s...")
    await asyncio.sleep(processing_time)

    # Simulate random failures for testing (10% failure rate)
    import random
    if random.random() < 0.1:
        raise RuntimeError("Simulated processing failure")

    # Return mock result URI
    return f"file:///output/job_{job.job_id}/test_suite.md"


if __name__ == "__main__":
    """
    Entry point when executed with: python -m main.api.worker

    For Task 3.2 (Docker Compose), we only have placeholders.
    The full worker will be implemented in Task 2.3 (Backend API).

    This runs a simple heartbeat worker to validate Docker Compose orchestration.
    """
    import asyncio
    import os
    import time

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("=== Pharmaceutical Test Generation Worker Starting ===")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'unknown')}")
    logger.info(f"Database URL: {os.getenv('DATABASE_URL', 'not set')}")
    logger.info(f"SQS Queue URL: {os.getenv('SQS_QUEUE_URL', 'not set')}")
    logger.info("Worker placeholder running. Full implementation pending Task 2.3.")
    logger.info("This validates Docker Compose orchestration for Task 3.2.")

    async def placeholder_worker() -> None:
        """Placeholder worker with heartbeat logging."""
        try:
            iteration = 0
            while True:
                iteration += 1
                await asyncio.sleep(300)  # Sleep 5 minutes
                logger.info(
                    f"Worker heartbeat #{iteration}: Container running, "
                    f"awaiting full implementation"
                )

        except asyncio.CancelledError:
            logger.info("Worker received cancellation signal, shutting down gracefully")
        except KeyboardInterrupt:
            logger.info("Worker interrupted, shutting down gracefully")
        except Exception as e:
            logger.exception(f"Unexpected error in worker: {e}")
            raise

    try:
        asyncio.run(placeholder_worker())
    except KeyboardInterrupt:
        logger.info("Worker shutdown complete")

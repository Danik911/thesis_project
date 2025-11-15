"""
FastAPI application for pharmaceutical test generation workflow.

Provides async job submission with GAMP-5 compliance, ALCOA+ audit trail,
and background job processing using asyncio.Queue and in-memory storage.
"""

import asyncio
import hashlib
import logging
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from langfuse import observe

# Load environment variables from .env.local (for local development)
# This must happen BEFORE importing dependencies that use environment variables
env_file = Path(__file__).parent.parent.parent / ".env.local"
if env_file.exists():
    load_dotenv(env_file)
    logging.info(f"Loaded environment variables from {env_file}")
else:
    logging.warning(f"Environment file not found: {env_file}")

from .audit import get_audit_logger, initialize_audit_logger
from .dependencies import (
    CurrentUserDep,
    JobLockDep,
    JobQueueDep,
    JobRepositoryDep,
    StorageAdapterDep,
    ValidatedFileDep,
    initialize_job_infrastructure,
)
from .models import JobRecord, JobStatus, JobStatusResponse, JobSubmitResponse
from .observability import initialize_langfuse, shutdown_langfuse
from .worker import process_job_worker

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.

    Handles startup and shutdown:
    - Initialize audit logger
    - Initialize job infrastructure (queue, repository, lock)
    - Start background worker task
    - Clean shutdown on termination

    Yields:
        None
    """
    # Startup
    logger.info("FastAPI application starting...")

    # Initialize audit logger
    initialize_audit_logger(audit_directory="logs/audit/jobs")
    logger.info("Audit logger initialized")

    # Initialize LangFuse observability
    try:
        initialize_langfuse()
        logger.info("LangFuse observability initialized")
    except Exception as e:
        logger.error(f"Failed to initialize LangFuse: {e}. Continuing without observability.")
        # Don't fail startup if LangFuse fails - observability is important but not critical

    # Initialize job infrastructure
    job_queue, job_repository, job_lock = initialize_job_infrastructure()
    logger.info("Job infrastructure initialized")

    # Start background worker task
    worker_task = asyncio.create_task(
        process_job_worker(
            job_queue=job_queue,
            job_repository=job_repository,
            job_lock=job_lock
        ),
        name="background_job_worker"
    )
    logger.info("Background worker started")

    logger.info("FastAPI application ready")

    yield  # Application running

    # Shutdown
    logger.info("FastAPI application shutting down...")

    # Cancel worker task
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        logger.info("Background worker stopped")

    # Shutdown LangFuse observability (flush pending traces)
    shutdown_langfuse()

    logger.info("FastAPI application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Pharmaceutical Test Generation API",
    description=(
        "Async job submission API for GAMP-5 compliant pharmaceutical test generation. "
        "Supports URS file upload, background processing, and status tracking with "
        "ALCOA+ audit trail requirements."
    ),
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/", response_model=dict[str, str])
async def root() -> dict[str, str]:
    """
    Root endpoint - health check.

    Returns:
        API status information
    """
    return {
        "status": "healthy",
        "service": "pharmaceutical-test-generation-api",
        "version": "1.0.0"
    }


@app.get("/health", response_model=dict[str, str])
async def health_check() -> dict[str, str]:
    """
    ECS Fargate healthcheck endpoint.

    Returns 200 OK if application is running and ready to accept requests.
    Used by Docker HEALTHCHECK directive and ECS target group health checks.

    GAMP-5 Compliance:
    - Shallow health check (fast, <100ms)
    - No database queries (prevents healthcheck from causing load)
    - Logged to audit trail via LangFuse (@observe decorator would add overhead)

    Returns:
        Health status information

    CRITICAL: NO FALLBACK LOGIC - If application not ready, let it fail
    """
    return {
        "status": "healthy",
        "service": "pharmaceutical-test-generation-api",
        "version": "1.0.0"
    }


@app.post("/jobs", response_model=JobSubmitResponse, status_code=status.HTTP_201_CREATED)
@observe(name="create_test_generation_job")
async def submit_job(
    file: ValidatedFileDep,
    storage: StorageAdapterDep,
    job_queue: JobQueueDep,
    job_repository: JobRepositoryDep,
    job_lock: JobLockDep,
    user: CurrentUserDep
) -> JobSubmitResponse:
    """
    Submit URS file for async processing.

    Workflow:
    1. Validate file (size, type) - handled by ValidatedFileDep
    2. Authenticate user - handled by CurrentUserDep (Clerk JWT)
    3. Compute SHA-256 hash of file content
    4. Persist file via storage adapter
    5. Create job record in repository
    6. Enqueue job for background processing
    7. Return job ID immediately

    Args:
        file: Validated URS upload file
        storage: Storage adapter dependency
        job_queue: Job queue dependency
        job_repository: Job repository dependency
        job_lock: Job lock dependency
        user: Current user dependency (Clerk JWT claims)

    Returns:
        JobSubmitResponse with job_id and status

    Raises:
        HTTPException 400: If file validation fails
        HTTPException 401: If authentication fails
        HTTPException 413: If file too large
        HTTPException 500: If storage or job creation fails

    CRITICAL: NO FALLBACK LOGIC - All errors propagate explicitly
    """
    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        logger.info(f"Submitting job {job_id} for user {user.sub} ({user.email})")

        # Read file content (already in memory from validation)
        urs_content = await file.read()

        # Compute SHA-256 hash (ONCE from memory)
        urs_hash = hashlib.sha256(urs_content).hexdigest()

        # Persist file via storage adapter
        # Note: Using "5" (custom software) as placeholder until workflow
        # completes GAMP-5 categorization. The workflow will update this
        # to the correct category (1, 3, 4, or 5) based on system analysis.
        storage_metadata = {
            "gamp_category": "5",  # Valid GAMP-5 placeholder (custom software)
            "job_id": job_id,
            "created_at": datetime.now(UTC).isoformat(),
            "created_by": user.sub,  # Clerk user ID
            "created_by_email": user.email,  # Human-readable attribution
            "artifact_type": "urs"
        }

        storage_key = await storage.save_artifact(
            artifact_id=job_id,
            content=urs_content,
            metadata=storage_metadata
        )
        logger.info(f"URS persisted: {storage_key}")

        # Create job record
        job_record = JobRecord(
            job_id=job_id,
            status=JobStatus.PENDING,
            created_at=datetime.now(UTC),
            urs_filename=file.filename or "unknown.txt",
            urs_storage_key=storage_key,
            urs_hash=urs_hash,
            urs_size_bytes=len(urs_content),
            user_id=user.sub  # Clerk user ID from JWT 'sub' claim
        )

        # Add to repository (thread-safe)
        async with job_lock:
            job_repository[job_id] = job_record

        # Enqueue job for background processing
        await job_queue.put(job_id)
        logger.info(f"Job {job_id} enqueued for processing")

        # Log to audit trail with Clerk authentication context
        audit_logger = get_audit_logger()
        audit_logger.log_event(
            job_id=job_id,
            event_type="submit",
            user_id=user.sub,  # Clerk user ID
            status=JobStatus.PENDING,
            user_email=user.email,  # ALCOA+ attribution
            token_iat=user.iat,  # JWT issued-at for lifecycle tracking
            metadata={
                "urs_filename": file.filename,
                "urs_size_bytes": len(urs_content),
                "urs_hash": urs_hash,
                "storage_key": storage_key,
                "token_exp": user.exp  # JWT expiration for security analysis
            }
        )

        # Return response immediately (non-blocking)
        return JobSubmitResponse(
            job_id=job_id,
            status=JobStatus.PENDING,
            created_at=job_record.created_at.isoformat(),
            urs_hash=urs_hash
        )

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        # CRITICAL: NO FALLBACK - Explicit error propagation
        logger.exception(f"Job submission failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CRITICAL: Job submission failed: {e}"
        ) from e
    finally:
        # Ensure file handle closed (prevent resource leaks)
        try:
            await file.close()
        except Exception as e:
            logger.warning(f"Failed to close file handle: {e}")


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
@observe(name="get_job_status")
async def get_job_status(
    job_id: str,
    job_repository: JobRepositoryDep,
    job_lock: JobLockDep,
    storage: StorageAdapterDep,
    user: CurrentUserDep
) -> JobStatusResponse:
    """
    Get job status and results.

    Args:
        job_id: Unique job identifier
        job_repository: Job repository dependency
        job_lock: Job lock dependency
        storage: Storage adapter dependency
        user: Current user dependency (Clerk JWT claims)

    Returns:
        JobStatusResponse with current status and results

    Raises:
        HTTPException 401: If authentication fails
        HTTPException 403: If user not authorized to view job
        HTTPException 404: If job not found

    CRITICAL: NO FALLBACK LOGIC - Missing jobs return 404, not empty data
    """
    try:
        # Get job record from repository
        async with job_lock:
            job = job_repository.get(job_id)

        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"CRITICAL: Job {job_id} not found"
            )

        # Authorization check: User can only access their own jobs
        if job.user_id != user.sub:
            logger.warning(
                f"Authorization denied: User {user.sub} ({user.email}) "
                f"attempted to access job {job_id} owned by {job.user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"CRITICAL: User not authorized to view job {job_id}"
            )

        # Generate download URL if job completed
        download_url: str | None = None
        if job.status == JobStatus.COMPLETED and job.result_uri:
            try:
                download_url = await storage.generate_download_url(
                    artifact_id=job_id,
                    expiry_seconds=86400  # 24 hours
                )
            except Exception as e:
                logger.warning(f"Failed to generate download URL: {e}")
                # Don't fail request if URL generation fails

        # Convert to response model
        return job.to_response(download_url=download_url)

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # CRITICAL: NO FALLBACK - Explicit error propagation
        logger.exception(f"Job status query failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CRITICAL: Job status query failed: {e}"
        ) from e


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for unhandled errors.

    Args:
        request: FastAPI request object
        exc: Exception raised

    Returns:
        JSONResponse with error details

    CRITICAL: NO FALLBACK LOGIC - All errors logged and reported explicitly
    """
    logger.exception(f"Unhandled exception: {exc}")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": f"CRITICAL: Unhandled server error: {exc}",
            "type": type(exc).__name__
        }
    )


if __name__ == "__main__":
    import uvicorn

    # Run FastAPI application
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

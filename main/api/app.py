"""
FastAPI application for pharmaceutical test generation workflow.

Provides async job submission with GAMP-5 compliance, ALCOA+ audit trail,
and background job processing using asyncio.Queue and in-memory storage.
"""

# CRITICAL: Configure logging FIRST, before ANY other imports that might log
# This prevents RecursionError from LoggerAdapter WeakRef issues
import logging
import sys
import warnings

# Suppress WeakValueDictionary recursion warnings during GC
warnings.filterwarnings("ignore", category=ResourceWarning)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
    force=True  # Force reconfiguration if already set
)

# Suppress DEBUG logging for internal modules to prevent recursion issues
# These modules can trigger recursive logging during GC cleanup
# The WeakValueDictionary in Python's logging manager can cause recursion
# when its remove callback tries to log during garbage collection
logging.getLogger().setLevel(logging.INFO)  # Root logger - no DEBUG anywhere
logging.getLogger("asyncio").setLevel(logging.WARNING)
logging.getLogger("concurrent.futures").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("opentelemetry").setLevel(logging.WARNING)
logging.getLogger("alembic").setLevel(logging.WARNING)
logging.getLogger("phoenix").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Now safe to import modules that might log during import
import asyncio
import hashlib
import os
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
import yaml
import aiofiles

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, Response
from langfuse import observe

# Load environment variables from .env.local (for local development)
# This must happen BEFORE importing dependencies that use environment variables
env_file = Path(__file__).parent.parent.parent / ".env.local"
if env_file.exists():
    load_dotenv(env_file)
    logger.info(f"Loaded environment variables from {env_file}")
else:
    # In Docker, env vars are passed via docker-compose, so file might not exist
    logger.info(f"Environment file not found: {env_file} (using system env vars)")

from .audit import get_audit_logger, initialize_audit_logger
from .dependencies import (
    ApprovalLockDep,
    ApprovalRepositoryDep,
    CurrentUserDep,
    DbJobRepositoryDep,
    JobLockDep,
    JobQueueDep,
    JobRepositoryDep,
    StorageAdapterDep,
    ValidatedFileDep,
    initialize_approval_infrastructure,
    initialize_database_repository,
    initialize_job_infrastructure,
    is_database_mode,
    shutdown_database_repository,
)
from .job_repository import PostgresJobRepository
from .models import (
    ApprovalDecision,
    ApprovalRecord,
    ApprovalRequest,
    ApprovalResponse,
    JobRecord,
    JobStatus,
    JobStatusResponse,
    JobStatusWithApproval,
    JobSubmitResponse,
    STAGE_LABELS,
    STAGE_PROGRESS_MAP,
)
from .observability import initialize_langfuse, shutdown_langfuse, get_langfuse_client
from .worker import process_job_worker
from .langfuse_routes import router as langfuse_router

# Note: logging.basicConfig and logger are configured at the top of the file
# to prevent RecursionError from early logger access


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.

    Handles startup and shutdown:
    - Initialize audit logger
    - Initialize job infrastructure (queue, repository, lock)
    - Initialize database repository (if DATABASE_URL set)
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

    # Initialize ChromaDB from S3 in staging/production
    # CRITICAL: API container needs ChromaDB for RAG workflow (Context Provider agent)
    # Worker also initializes this, but API runs the workflow directly
    env = os.getenv("ENVIRONMENT", "")
    if env in ("staging", "production") and os.getenv("S3_CHROMADB_BUCKET"):
        try:
            from main.scripts.init_chromadb import init_chromadb_from_s3
            chroma_path = init_chromadb_from_s3()
            logger.info(f"ChromaDB initialized from S3: {chroma_path}")
        except Exception as e:
            logger.error(f"CRITICAL: Failed to initialize ChromaDB from S3: {e}")
            raise  # Cannot proceed without RAG database - fail loudly

    # Initialize LangFuse observability
    try:
        initialize_langfuse()
        logger.info("LangFuse observability initialized")
    except Exception as e:
        logger.error(f"Failed to initialize LangFuse: {e}. Continuing without observability.")
        # Don't fail startup if LangFuse fails - observability is important but not critical

    # Initialize job infrastructure (in-memory, for backward compatibility)
    job_queue, job_repository, job_lock = initialize_job_infrastructure()
    logger.info("Job infrastructure initialized (in-memory)")

    # Initialize PostgreSQL database repository (if DATABASE_URL set)
    # This enables HIL workflow shared state between API and Worker containers
    database_url = os.getenv("DATABASE_URL")

    db_job_repo: PostgresJobRepository | None = None
    if database_url:
        try:
            db_job_repo = await initialize_database_repository(database_url)
            logger.info(
                "[HIL] PostgreSQL repository initialized - "
                "API and Worker containers now share job state"
            )

            # CRITICAL: Re-enqueue pending/approved jobs from database
            # This recovers jobs lost from in-memory queue during container restart
            # Also recovers APPROVED jobs that were waiting for HIL resumption
            try:
                restartable_jobs = await db_job_repo.get_pending_jobs()

                if restartable_jobs:
                    logger.info(
                        f"[RECOVERY] Found {len(restartable_jobs)} restartable jobs in database. Re-enqueuing..."
                    )
                    async with job_lock:
                        for job in restartable_jobs:
                            # 1. Restore to in-memory repository (required for worker)
                            job_repository[job.job_id] = job
                            # 2. Add to processing queue
                            await job_queue.put(job.job_id)
                            logger.debug(f"[RECOVERY] Re-enqueued job {job.job_id} (status={job.status.value})")
                    logger.info(f"[RECOVERY] Successfully re-enqueued {len(restartable_jobs)} jobs")
            except Exception as e:
                logger.error(f"[RECOVERY] Failed to re-enqueue restartable jobs: {e}")

        except Exception as e:
            logger.error(
                f"[HIL] Failed to initialize PostgreSQL repository: {e}. "
                f"HIL workflow resumption will NOT work in docker-compose mode!"
            )
            # Continue without database - HIL won't work but basic operations might
    else:
        logger.warning(
            "[HIL] DATABASE_URL not set - running in in-memory mode. "
            "HIL workflow resumption will NOT work between API and Worker containers!"
        )

    # Initialize approval infrastructure for HIL workflow
    approval_repository, approval_lock = initialize_approval_infrastructure()
    logger.info("Approval infrastructure initialized")

    # Start background worker task
    worker_task = asyncio.create_task(
        process_job_worker(
            job_queue=job_queue,
            job_repository=job_repository,
            job_lock=job_lock,
            db_job_repo=db_job_repo  # HIL shared state via PostgreSQL
        ),
        name="background_job_worker"
    )
    logger.info(f"Background worker started (db_mode={db_job_repo is not None})")

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

    # Shutdown database repository
    await shutdown_database_repository()

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

# Configure CORS
# GAMP-5 Compliance: Restrict origins to known trusted domains
origins = [
    "http://localhost:3000",  # Local development frontend (Docker)
    "http://localhost:3001",  # Local development frontend (npm run dev)
    "http://localhost:3002",  # Local development frontend (npm run dev alt port)
    "http://127.0.0.1:3000",  # Local development frontend (alternative)
    "http://127.0.0.1:3001",  # Local development frontend (alternative)
    "http://127.0.0.1:3002",  # Local development frontend (alternative)
    # AWS CloudFront (production/staging)
    "https://d2yiysdqio0ryi.cloudfront.net",
    "https://d3ij3pn3g49dzz.cloudfront.net",  # Current production CloudFront
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    # Allow local/private-network frontend dev origins (WSL/VM/LAN)
    # while still requiring explicit scheme + port pattern.
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+|192\.168\.\d+\.\d+):300\d$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Langfuse API routes (for /api/langfuse/trace endpoint)
# This proxies requests to Langfuse Cloud API for frontend observability dashboard
app.include_router(langfuse_router)


# =============================================================================
# DEBUG MIDDLEWARE - Logs ALL incoming requests BEFORE dependency resolution
# This helps diagnose issues where POST requests crash during dependency handling
# and never get logged by uvicorn (uvicorn logs AFTER request completion)
# =============================================================================
@app.middleware("http")
async def debug_request_middleware(request: Request, call_next):
    """
    Debug middleware to log all incoming requests immediately.

    This runs BEFORE any route handlers or dependency resolution,
    allowing us to see if requests reach the server even if they crash
    during dependency injection.
    """
    # Log immediately when request arrives (before any processing)
    method = request.method
    url = str(request.url)
    print(f">>> INCOMING: {method} {url}", file=sys.stderr, flush=True)
    logger.info(f">>> INCOMING: {method} {url}")

    try:
        response = await call_next(request)
        print(f"<<< RESPONSE: {method} {url} -> {response.status_code}", file=sys.stderr, flush=True)
        logger.info(f"<<< RESPONSE: {method} {url} -> {response.status_code}")
        return response
    except Exception as e:
        print(f"!!! EXCEPTION: {method} {url} -> {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        logger.exception(f"!!! Request failed: {method} {url} -> {e}")
        raise


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
async def submit_job(
    file: ValidatedFileDep,
    storage: StorageAdapterDep,
    job_queue: JobQueueDep,
    job_repository: JobRepositoryDep,
    job_lock: JobLockDep,
    db_job_repo: DbJobRepositoryDep,
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

    Note: Uses manual Langfuse tracing instead of @observe decorator
    to avoid serialization issues with file uploads (UploadFile contains
    non-serializable file descriptors that cause infinite hang).
    """
    # Manual Langfuse tracing - avoids @observe file serialization issue
    # Only serialize safe metadata (filename, content_type) NOT the file object
    # Uses start_span() instead of trace() - SDK 3.5.2 API
    langfuse = get_langfuse_client()
    span = None

    try:
        # =================================================================
        # DAILY JOB LIMIT CHECK (Task 4.5 - Cost Control)
        # Check BEFORE creating job to prevent resource waste
        # =================================================================
        daily_limit = int(os.getenv("DAILY_JOB_LIMIT", "10"))

        if daily_limit > 0 and db_job_repo is not None:
            job_count = await db_job_repo.count_jobs_today()

            if job_count >= daily_limit:
                # Log limit violation for audit trail (ALCOA+ compliance)
                audit_logger = get_audit_logger()
                if audit_logger:
                    audit_logger.log_event(
                        job_id=str(uuid.uuid4()),  # Unique event ID for this violation
                        event_type="rate_limit_exceeded",
                        user_id=user.sub,
                        status=JobStatus.PENDING,
                        user_email=user.email,
                        metadata={
                            "daily_limit": daily_limit,
                            "jobs_today": job_count,
                            "endpoint": "POST /jobs",
                            "filename": file.filename
                        }
                    )

                logger.warning(
                    f"[QUOTA] Daily job limit exceeded: {job_count}/{daily_limit} "
                    f"by user {user.sub} ({user.email})"
                )

                # CRITICAL: NO FALLBACK - Explicit rejection with full context
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=(
                        f"System daily job limit ({daily_limit}) reached. "
                        f"Resets at midnight UTC. Current count: {job_count}"
                    )
                )

        # Generate unique job ID
        job_id = str(uuid.uuid4())
        logger.info(f"Submitting job {job_id} for user {user.sub} ({user.email})")

        # Start span AFTER job_id is generated so we can include it
        # Note: user_id goes in metadata since start_span() doesn't have user_id param
        if langfuse:
            span = langfuse.start_span(
                name="create_test_generation_job",
                input={
                    "filename": file.filename,
                    "content_type": file.content_type,
                    "endpoint": "POST /jobs"
                },
                metadata={
                    "job_id": job_id,
                    "user_id": user.sub,
                    "user_email": user.email
                }
            )

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
            "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "created_by": user.sub,  # Clerk user ID
            "created_by_email": user.email or "unknown",  # Handle None email (Clerk session tokens may lack email claim)
            "artifact_type": "urs"
        }

        storage_key = await storage.save_artifact(
            artifact_id=f"{job_id}/urs_document.md",
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

        # Also create in PostgreSQL database (for HIL shared state)
        if db_job_repo is not None:
            try:
                await db_job_repo.create(job_record)
                logger.info(f"[HIL-DB] Job {job_id} created in PostgreSQL")
            except Exception as e:
                logger.error(f"[HIL-DB] Failed to create job in database: {e}")
                # Continue - in-memory job exists, basic operations will work
                # but HIL workflow resumption may fail

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
        response = JobSubmitResponse(
            job_id=job_id,
            status=JobStatus.PENDING,
            created_at=job_record.created_at.isoformat(),
            urs_hash=urs_hash
        )

        # Update span with success output
        if span:
            span.update(output={"job_id": job_id, "status": "submitted"})

        return response

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        if span:
            span.update(output={"error": "HTTPException"}, level="WARNING")
        raise
    except Exception as e:
        # CRITICAL: NO FALLBACK - Explicit error propagation
        logger.exception(f"Job submission failed: {e}")
        if span:
            span.update(output={"error": str(e)}, level="ERROR")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CRITICAL: Job submission failed: {e}"
        ) from e
    finally:
        # End span and flush Langfuse to ensure trace is sent
        if span:
            try:
                span.end()
            except Exception as end_error:
                logger.warning(f"Failed to end Langfuse span: {end_error}")
        if langfuse:
            try:
                langfuse.flush()
            except Exception as flush_error:
                logger.warning(f"Failed to flush Langfuse: {flush_error}")

        # Ensure file handle closed (prevent resource leaks)
        try:
            await file.close()
        except Exception as e:
            logger.warning(f"Failed to close file handle: {e}")


@app.get("/jobs", response_model=list[JobStatusResponse])
async def list_jobs(
    job_repository: JobRepositoryDep,
    job_lock: JobLockDep,
    db_job_repo: DbJobRepositoryDep,
    user: CurrentUserDep
) -> list[JobStatusResponse]:
    """
    List all jobs for the current user.

    Note: @observe decorator removed - causes hang by serializing
    non-serializable dependency objects (locks, connection pools).
    """
    # Try database first (docker-compose mode)
    if db_job_repo is not None:
        try:
            jobs = await db_job_repo.get_jobs_by_user(user.sub)
            return [job.to_response() for job in jobs]
        except Exception as e:
            logger.warning(f"[DB] Failed to list jobs from database: {e}")
            # Fall through to in-memory

    async with job_lock:
        user_jobs = [
            job.to_response() 
            for job in job_repository.values() 
            if job.user_id == user.sub
        ]
    # Sort by created_at desc
    user_jobs.sort(key=lambda x: x.created_at, reverse=True)
    return user_jobs


@app.get("/jobs/{job_id}/download")
async def download_job_result(
    job_id: str,
    job_repository: JobRepositoryDep,
    job_lock: JobLockDep,
    db_job_repo: DbJobRepositoryDep,
    user: CurrentUserDep
):
    """
    Download job result file.

    Note: @observe decorator removed - causes hang by serializing
    non-serializable dependency objects (locks, connection pools).
    """
    # Check PostgreSQL first (where jobs are persisted), then fall back to in-memory
    job = None
    if db_job_repo is not None:
        try:
            job = await db_job_repo.get(job_id)
        except Exception as e:
            logger.warning(f"Failed to get job from database: {e}")

    if job is None:
        async with job_lock:
            job = job_repository.get(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.user_id != user.sub:
        raise HTTPException(status_code=403, detail="Not authorized")

    if job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job not completed")

    if not job.result_uri:
        raise HTTPException(status_code=404, detail="Result not found")

    # Handle S3 URI (AWS deployment)
    if job.result_uri.startswith("s3://"):
        from aiobotocore.session import get_session
        from botocore.exceptions import ClientError

        # Parse S3 URI: s3://bucket/path/to/file
        uri_parts = job.result_uri.replace("s3://", "").split("/", 1)
        if len(uri_parts) != 2:
            raise HTTPException(status_code=500, detail=f"Invalid S3 URI format: {job.result_uri}")

        bucket = uri_parts[0]
        key = uri_parts[1]
        region = os.getenv("AWS_REGION", "eu-west-2")

        logger.info(f"[DOWNLOAD] Fetching from S3: bucket={bucket}, key={key}")

        session = get_session()
        try:
            async with session.create_client("s3", region_name=region) as client:
                response = await client.get_object(Bucket=bucket, Key=key)
                content = await response["Body"].read()

                return Response(
                    content=content,
                    media_type="application/x-yaml",
                    headers={"Content-Disposition": f"attachment; filename=test_suite_{job_id}.yaml"}
                )
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            if error_code in ["NoSuchKey", "404"]:
                raise HTTPException(status_code=404, detail=f"File not found in S3: {key}")
            raise HTTPException(status_code=500, detail=f"S3 error: {error_code}")

    # Handle file:// URI (local development)
    if job.result_uri.startswith("file://"):
        file_path = job.result_uri.replace("file://", "")
        # On Windows it might be file:///C:/... -> /C:/...
        # But inside Docker (Linux) it is file:///app/output/... -> /app/output/...

        # Handle Windows path if running locally
        if ":" in file_path and not file_path.startswith("/"):
             pass # It's likely absolute windows path
        elif file_path.startswith("/") and ":" in file_path[2:]: # /C:/...
             file_path = file_path[1:] # C:/...

        path_obj = Path(file_path).resolve()

        if not path_obj.exists():
             raise HTTPException(status_code=404, detail=f"File not found on server: {path_obj}")

        return FileResponse(
            path=path_obj,
            filename=f"test_suite_{job_id}.yaml",
            media_type="application/x-yaml"
        )

    raise HTTPException(status_code=501, detail=f"Unsupported storage URI scheme: {job.result_uri}")


@app.get("/jobs/{job_id}/result")
async def get_job_result_json(
    job_id: str,
    job_repository: JobRepositoryDep,
    job_lock: JobLockDep,
    db_job_repo: DbJobRepositoryDep,
    user: CurrentUserDep
):
    """
    Get job result as JSON for dashboard display.

    Note: @observe decorator removed - causes hang by serializing
    non-serializable dependency objects (locks, connection pools).
    """
    # Check PostgreSQL first (where jobs are persisted), then fall back to in-memory
    job = None
    if db_job_repo is not None:
        try:
            job = await db_job_repo.get(job_id)
        except Exception as e:
            logger.warning(f"Failed to get job from database: {e}")

    if job is None:
        async with job_lock:
            job = job_repository.get(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.user_id != user.sub:
        raise HTTPException(status_code=403, detail="Not authorized")

    if job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job not completed")

    if not job.result_uri:
        raise HTTPException(status_code=404, detail="Result not found")

    # Handle S3 URI (AWS deployment)
    if job.result_uri.startswith("s3://"):
        from aiobotocore.session import get_session
        from botocore.exceptions import ClientError

        uri_parts = job.result_uri.replace("s3://", "").split("/", 1)
        if len(uri_parts) != 2:
            raise HTTPException(status_code=500, detail=f"Invalid S3 URI: {job.result_uri}")

        bucket = uri_parts[0]
        key = uri_parts[1]
        region = os.getenv("AWS_REGION", "eu-west-2")

        session = get_session()
        try:
            async with session.create_client("s3", region_name=region) as client:
                response = await client.get_object(Bucket=bucket, Key=key)
                content = await response["Body"].read()
                data = yaml.safe_load(content.decode("utf-8"))
                return JSONResponse(content=data)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            if error_code in ["NoSuchKey", "404"]:
                raise HTTPException(status_code=404, detail=f"File not found in S3: {key}")
            raise HTTPException(status_code=500, detail=f"S3 error: {error_code}")

    # Handle file:// URI (local development)
    if job.result_uri.startswith("file://"):
        file_path = job.result_uri.replace("file://", "")
        # Handle Windows path logic if needed
        if file_path.startswith("/") and ":" in file_path[2:]:
             file_path = file_path[1:]

        path_obj = Path(file_path).resolve()

        if not path_obj.exists():
             raise HTTPException(status_code=404, detail="File not found on server")

        try:
            async with aiofiles.open(path_obj, "r") as f:
                content = await f.read()
                # Parse YAML
                data = yaml.safe_load(content)
                return JSONResponse(content=data)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse result: {e}")

    raise HTTPException(status_code=501, detail=f"Unsupported storage URI: {job.result_uri}")


@app.get("/jobs/quota", response_model=dict)
async def get_job_quota(
    db_job_repo: DbJobRepositoryDep,
) -> dict:
    """
    Get current job quota status.

    Returns quota information including:
    - Whether limit is enabled
    - Daily limit value
    - Jobs submitted today
    - Remaining quota
    - Reset time (midnight UTC)

    This endpoint does NOT require authentication to allow frontend
    to display quota status before user attempts job submission.

    GAMP-5 Compliance: Returns accurate real-time quota from database.
    ALCOA+ Compliance: No data modification, read-only query.

    Returns:
        dict with quota status information

    CRITICAL: NO FALLBACK LOGIC - Returns accurate state or error.
    """
    daily_limit = int(os.getenv("DAILY_JOB_LIMIT", "10"))

    # Check if limit is disabled
    if daily_limit <= 0:
        return {
            "limit_enabled": False,
            "message": "No daily limit configured"
        }

    # Check if database is available
    if db_job_repo is None:
        return {
            "limit_enabled": False,
            "message": "Database not available (in-memory mode)"
        }

    # Query actual job count from database
    # CRITICAL: No fallback - if query fails, let exception propagate
    job_count = await db_job_repo.count_jobs_today()

    return {
        "limit_enabled": True,
        "daily_limit": daily_limit,
        "jobs_today": job_count,
        "remaining": max(0, daily_limit - job_count),
        "resets_at": "00:00 UTC"
    }


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    job_repository: JobRepositoryDep,
    job_lock: JobLockDep,
    db_job_repo: DbJobRepositoryDep,
    storage: StorageAdapterDep,
    user: CurrentUserDep
) -> JobStatusResponse:
    """
    Get job status and results.

    Args:
        job_id: Unique job identifier
        job_repository: Job repository dependency
        job_lock: Job lock dependency
        db_job_repo: Database repository for HIL shared state
        storage: Storage adapter dependency
        user: Current user dependency (Clerk JWT claims)

    Returns:
        JobStatusResponse with current status and results

    Raises:
        HTTPException 401: If authentication fails
        HTTPException 403: If user not authorized to view job
        HTTPException 404: If job not found

    CRITICAL: NO FALLBACK LOGIC - Missing jobs return 404, not empty data

    HIL Note: In docker-compose mode, prefer database for latest status
    since worker updates database directly for AWAITING_APPROVAL state.
    """
    try:
        # Try database first for latest HIL status (docker-compose mode)
        job = None
        if db_job_repo is not None:
            try:
                job = await db_job_repo.get(job_id)
            except Exception as e:
                logger.warning(f"[HIL-DB] Failed to get job from database: {e}")
                # Fall through to in-memory

        # Fall back to in-memory if database unavailable or returned None
        if job is None:
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
            if job.result_uri.startswith("file://"):
                 # Return API endpoint for download
                 # We assume the client can construct the full URL or we return relative
                 download_url = f"/jobs/{job_id}/download"
            else:
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


# =============================================================================
# HIL (Human-in-the-Loop) Approval Endpoints
# =============================================================================


@app.get("/jobs/{job_id}/approval-status", response_model=JobStatusWithApproval)
async def get_job_approval_status(
    job_id: str,
    job_repository: JobRepositoryDep,
    job_lock: JobLockDep,
    db_job_repo: DbJobRepositoryDep,
    user: CurrentUserDep
) -> JobStatusWithApproval:
    """
    Get extended job status with approval details for HIL workflow.

    Returns detailed information including:
    - Current job status
    - Whether approval is required
    - Approval reason and timeout
    - AI categorization result with confidence
    - Alternative categories for human review

    Args:
        job_id: Unique job identifier
        job_repository: Job repository dependency
        job_lock: Job lock dependency
        db_job_repo: Database repository for HIL shared state
        user: Current user dependency (Clerk JWT claims)

    Returns:
        JobStatusWithApproval with full approval context

    Raises:
        HTTPException 401: If authentication fails
        HTTPException 403: If user not authorized to view job
        HTTPException 404: If job not found

    CRITICAL: NO FALLBACK LOGIC - All errors propagate explicitly

    HIL Note: In docker-compose mode, prefer database for latest status.

    FIX: Removed @observe decorator - causes hang by serializing
    non-serializable dependency objects (locks, connection pools).
    Manual span created with safe metadata only.
    """
    # Manual Langfuse span - DO NOT use @observe decorator (serialization hang)
    langfuse = get_langfuse_client()
    span = None
    if langfuse:
        span = langfuse.start_span(
            name="get_job_approval_status",
            input={"job_id": job_id, "endpoint": "GET /jobs/{job_id}/approval-status"},
            metadata={"user_id": user.sub}
        )

    try:
        # Try database first for latest HIL status (docker-compose mode)
        job = None
        if db_job_repo is not None:
            try:
                job = await db_job_repo.get(job_id)
            except Exception as e:
                logger.warning(f"[HIL-DB] Failed to get job from database: {e}")
                # Fall through to in-memory

        # Fall back to in-memory if database unavailable or returned None
        if job is None:
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

        # Calculate timeout remaining
        timeout_remaining_seconds: int | None = None
        if job.approval_timeout_at:
            remaining = (job.approval_timeout_at - datetime.now(UTC)).total_seconds()
            timeout_remaining_seconds = max(0, int(remaining))

        # Extract alternative categories from categorization result
        alternative_categories: list[int] | None = None
        if job.categorization_result and "alternative_categories" in job.categorization_result:
            alternative_categories = job.categorization_result["alternative_categories"]

        # Compute progress fields (same logic as JobRecord.to_response)
        progress_percentage: int | None = None
        current_stage_str: str | None = None
        current_stage_label: str | None = None

        if job.status == JobStatus.COMPLETED:
            progress_percentage = 100
            current_stage_str = "completion"
            current_stage_label = STAGE_LABELS.get("completion")
        elif job.status == JobStatus.FAILED or job.status == JobStatus.REJECTED:
            progress_percentage = 100  # Show 100% on failure (job ended)
            current_stage_str = job.current_stage.value if job.current_stage else None
            current_stage_label = STAGE_LABELS.get(current_stage_str) if current_stage_str else None
        elif job.current_stage:
            current_stage_str = job.current_stage.value
            progress_percentage = STAGE_PROGRESS_MAP.get(current_stage_str, 0)
            current_stage_label = STAGE_LABELS.get(current_stage_str)
        elif job.status == JobStatus.PENDING:
            progress_percentage = 0
            current_stage_str = "queued"
            current_stage_label = STAGE_LABELS.get("queued")
        elif job.status == JobStatus.PROCESSING:
            # PROCESSING but no stage set yet - default to ingestion (10%)
            progress_percentage = 10
            current_stage_str = "ingestion"
            current_stage_label = STAGE_LABELS.get("ingestion")
        elif job.status == JobStatus.AWAITING_APPROVAL:
            progress_percentage = 30
            current_stage_str = "hil_waiting"
            current_stage_label = STAGE_LABELS.get("hil_waiting")

        return JobStatusWithApproval(
            job_id=job.job_id,
            status=job.status,
            requires_approval=job.requires_approval,
            approval_reason=job.approval_reason,
            timeout_remaining_seconds=timeout_remaining_seconds,
            categorization_result=job.categorization_result,
            alternative_categories=alternative_categories,
            created_at=job.created_at.isoformat(),
            updated_at=job.updated_at.isoformat() if job.updated_at else None,
            current_stage=current_stage_str,
            current_stage_label=current_stage_label,
            progress_percentage=progress_percentage
        )
    finally:
        if span:
            span.end()
        langfuse = get_langfuse_client()
        if langfuse:
            langfuse.flush()


@app.post("/jobs/{job_id}/approval", response_model=ApprovalResponse)
async def submit_job_approval(
    job_id: str,
    approval_request: ApprovalRequest,
    job_repository: JobRepositoryDep,
    job_lock: JobLockDep,
    job_queue: JobQueueDep,
    approval_repository: ApprovalRepositoryDep,
    approval_lock: ApprovalLockDep,
    db_job_repo: DbJobRepositoryDep,
    user: CurrentUserDep,
    request: Request
) -> ApprovalResponse:
    """
    Submit human approval decision for HIL workflow.

    Validates:
    - Job exists and belongs to user
    - Job status is AWAITING_APPROVAL
    - Approval timeout not expired

    Actions:
    - Creates ALCOA+ compliant ApprovalRecord
    - Updates job status to APPROVED or REJECTED
    - Stores human category decision
    - Logs to audit trail

    Args:
        job_id: Unique job identifier
        approval_request: Approval decision with justification
        job_repository: Job repository dependency
        job_lock: Job lock dependency
        approval_repository: Approval repository dependency
        approval_lock: Approval lock dependency
        user: Current user dependency (Clerk JWT claims)
        request: FastAPI request for IP/User-Agent

    Returns:
        ApprovalResponse with updated job status

    Raises:
        HTTPException 400: If job not awaiting approval
        HTTPException 401: If authentication fails
        HTTPException 403: If user not authorized
        HTTPException 404: If job not found
        HTTPException 408: If approval timeout expired

    CRITICAL: NO FALLBACK LOGIC - All errors propagate explicitly

    FIX: Removed @observe decorator - causes hang by serializing
    non-serializable dependency objects (locks, connection pools).
    Manual span created with safe metadata only.
    """
    # Manual Langfuse span - DO NOT use @observe decorator (serialization hang)
    langfuse = get_langfuse_client()
    span = None
    if langfuse:
        span = langfuse.start_span(
            name="submit_job_approval",
            input={
                "job_id": job_id,
                "approval_decision": approval_request.approval_decision.value,
                "human_category": approval_request.human_category,
                "endpoint": "POST /jobs/{job_id}/approval"
            },
            metadata={"user_id": user.sub}
        )

    try:
        # FIX: Check database FIRST for HIL jobs (docker-compose mode)
        # Jobs may exist in PostgreSQL but not in-memory after API restart
        job = None
        if db_job_repo is not None:
            try:
                job = await db_job_repo.get(job_id)
                if job:
                    logger.info(f"[HIL-DB] Found job {job_id} in PostgreSQL (status: {job.status})")
            except Exception as e:
                logger.warning(f"[HIL-DB] Failed to get job from database: {e}")
                # Fall through to in-memory

        # Fall back to in-memory if database unavailable or returned None
        if job is None:
            async with job_lock:
                job = job_repository.get(job_id)

        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"CRITICAL: Job {job_id} not found in database or memory"
            )

        # Authorization check: User can only approve their own jobs
        if job.user_id != user.sub:
            logger.warning(
                f"Authorization denied: User {user.sub} ({user.email}) "
                f"attempted to approve job {job_id} owned by {job.user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"CRITICAL: User not authorized to approve job {job_id}"
            )

        # Validate job is awaiting approval
        if job.status != JobStatus.AWAITING_APPROVAL:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"CRITICAL: Job {job_id} is not awaiting approval (status: {job.status})"
            )

        # Check timeout not expired
        if job.approval_timeout_at and datetime.now(UTC) > job.approval_timeout_at:
            # Auto-reject on timeout
            job.status = JobStatus.REJECTED
            job.updated_at = datetime.now(UTC)
            logger.warning(f"Job {job_id} approval timeout expired - auto-rejecting")
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail=f"CRITICAL: Approval timeout expired for job {job_id}"
            )

        # Extract AI categorization details for audit record
        ai_category = 5  # Default
        ai_confidence = 0.0
        ai_reasoning = "Unknown"
        ambiguity_reason = None
        alternative_categories = None

        if job.categorization_result:
            ai_category = job.categorization_result.get("gamp_category", 5)
            ai_confidence = job.categorization_result.get("confidence", 0.0)
            ai_reasoning = job.categorization_result.get("reasoning", "No reasoning provided")
            ambiguity_reason = job.categorization_result.get("ambiguity_reason")
            alternative_categories = job.categorization_result.get("alternative_categories")

        # Create ALCOA+ compliant approval record
        approval_record = ApprovalRecord(
            job_id=job_id,
            # AI Recommendation
            ai_category=ai_category,
            ai_confidence=ai_confidence,
            ai_reasoning=ai_reasoning,
            ambiguity_reason=ambiguity_reason,
            alternative_categories=alternative_categories,
            # Human Decision
            approval_decision=approval_request.approval_decision,
            human_category=approval_request.human_category,
            justification=approval_request.justification,
            # ALCOA+ Compliance
            user_id=user.sub,
            user_email=user.email,
            digital_signature=f"{user.sub}_{datetime.now(UTC).isoformat()}",
            # Metadata
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )

        # Determine final job status and category
        if approval_request.approval_decision == ApprovalDecision.APPROVE:
            job.status = JobStatus.APPROVED
            # Use human category if provided, otherwise keep AI category
            job.human_category = approval_request.human_category or ai_category
            workflow_resumed = True
            message = f"Job approved with GAMP category {job.human_category}"
        elif approval_request.approval_decision == ApprovalDecision.REJECT:
            job.status = JobStatus.REJECTED
            job.human_category = None
            workflow_resumed = False
            message = "Job rejected by human reviewer"
        else:  # REQUEST_REVISION
            # Keep AWAITING_APPROVAL status, extend timeout
            job.approval_timeout_at = datetime.now(UTC) + timedelta(hours=1)
            workflow_resumed = False
            message = "Revision requested - timeout extended by 1 hour"

        job.updated_at = datetime.now(UTC)

        # CRITICAL: Update PostgreSQL database for HIL shared state
        # This allows Worker container to see the approval decision
        if db_job_repo is not None:
            try:
                await db_job_repo.set_approval_status(
                    job_id=job_id,
                    status=job.status,
                    human_category=job.human_category
                )
                logger.info(
                    f"[HIL-DB] Updated job {job_id} in PostgreSQL: "
                    f"status={job.status}, human_category={job.human_category}"
                )
            except Exception as e:
                logger.error(
                    f"[HIL-DB] Failed to update job {job_id} in PostgreSQL: {e}. "
                    f"Worker may not see approval!"
                )
                # Don't fail the request - in-memory update succeeded
                # Worker might eventually timeout, but at least API responded
        else:
            logger.warning(
                f"[HIL] Database repository not available - "
                f"Worker container cannot see approval for job {job_id}!"
            )

        # CRITICAL FIX: Re-enqueue APPROVED job to worker queue
        # This ensures workflow resumes even if the original HIL polling loop was killed
        # (e.g., by container restart). Without this, approved jobs would sit idle.
        if approval_request.approval_decision == ApprovalDecision.APPROVE:
            try:
                # Add to job queue so worker can resume processing
                await job_queue.put(job_id)
                logger.info(f"[HIL-RECOVERY] Re-enqueued approved job {job_id} to worker queue")
            except Exception as e:
                logger.error(f"[HIL-RECOVERY] Failed to re-enqueue job {job_id}: {e}")

        # Store approval record in repository
        async with approval_lock:
            if job_id not in approval_repository:
                approval_repository[job_id] = []
            approval_repository[job_id].append(approval_record)

        # Log to audit trail
        audit_logger = get_audit_logger()
        audit_logger.log_event(
            job_id=job_id,
            event_type="approval",
            user_id=user.sub,
            status=job.status,
            user_email=user.email,
            metadata={
                "approval_decision": approval_request.approval_decision.value,
                "human_category": approval_request.human_category,
                "justification": approval_request.justification,
                "ai_category": ai_category,
                "ai_confidence": ai_confidence,
                "digital_signature": approval_record.digital_signature
            }
        )

        logger.info(
            f"Approval recorded for job {job_id}: "
            f"decision={approval_request.approval_decision.value}, "
            f"human_category={approval_request.human_category}, "
            f"new_status={job.status}"
        )

        return ApprovalResponse(
            job_id=job_id,
            status=job.status,
            gamp_category=job.human_category or ai_category,
            workflow_resumed=workflow_resumed,
            trace_id=None,  # Will be populated by worker when resuming
            message=message
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Approval submission failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CRITICAL: Approval submission failed: {e}"
        ) from e
    finally:
        if span:
            span.end()
        langfuse = get_langfuse_client()
        if langfuse:
            langfuse.flush()


@app.get("/jobs/{job_id}/approval-history")
async def get_approval_history(
    job_id: str,
    job_repository: JobRepositoryDep,
    job_lock: JobLockDep,
    approval_repository: ApprovalRepositoryDep,
    approval_lock: ApprovalLockDep,
    user: CurrentUserDep
) -> list[dict]:
    """
    Get approval history for a job (ALCOA+ audit trail).

    Returns all approval records for the job in chronological order.

    Args:
        job_id: Unique job identifier
        job_repository: Job repository dependency
        job_lock: Job lock dependency
        approval_repository: Approval repository dependency
        approval_lock: Approval lock dependency
        user: Current user dependency

    Returns:
        List of approval records

    Raises:
        HTTPException 403: If user not authorized
        HTTPException 404: If job not found

    CRITICAL: NO FALLBACK LOGIC - All errors propagate explicitly
    """
    # Validate job exists and user has access
    async with job_lock:
        job = job_repository.get(job_id)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CRITICAL: Job {job_id} not found"
        )

    if job.user_id != user.sub:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"CRITICAL: User not authorized to view job {job_id}"
        )

    # Get approval records
    async with approval_lock:
        records = approval_repository.get(job_id, [])

    # Convert to dict for JSON serialization
    return [record.model_dump() for record in records]


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


# CORS middleware for public access removed to prevent duplication




# Import and register export router (safe, isolated)
from .export_formats import router as export_router
app.include_router(export_router)

# AI4LIMS PoC - LIMS router (public, no auth)
from .lims_router import router as lims_router
app.include_router(lims_router, prefix="/lims")

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

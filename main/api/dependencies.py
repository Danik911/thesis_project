"""
FastAPI dependency injection functions.

Provides dependency injection for storage adapters, job repositories,
queues, and authentication with testability and configurability.
"""

import asyncio
import logging
from typing import Annotated

from fastapi import Depends, HTTPException, UploadFile, status
from src.adapters.storage import StorageFactory, StorageProvider
from src.shared.config import get_config

from .models import JobRecord

logger = logging.getLogger(__name__)

# In-memory job storage (replaced by Aurora in production)
# Protected by asyncio lock for thread-safe access
_job_repository: dict[str, JobRecord] = {}
_job_lock: asyncio.Lock | None = None
_job_queue: asyncio.Queue[str] | None = None


def initialize_job_infrastructure() -> tuple[asyncio.Queue[str], dict[str, JobRecord], asyncio.Lock]:
    """
    Initialize job queue, repository, and lock.

    Returns:
        Tuple of (queue, repository, lock)

    Called during app lifespan startup.
    """
    global _job_repository, _job_lock, _job_queue

    _job_queue = asyncio.Queue()
    _job_repository = {}
    _job_lock = asyncio.Lock()

    logger.info("Job infrastructure initialized (in-memory mode)")
    return _job_queue, _job_repository, _job_lock


def get_job_queue() -> asyncio.Queue[str]:
    """
    Get job queue dependency.

    Returns:
        Asyncio queue for job IDs

    Raises:
        HTTPException: If queue not initialized
    """
    if _job_queue is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CRITICAL: Job queue not initialized. Check app lifespan."
        )
    return _job_queue


def get_job_repository() -> dict[str, JobRecord]:
    """
    Get job repository dependency.

    Returns:
        In-memory job storage dict

    Raises:
        HTTPException: If repository not initialized
    """
    if _job_repository is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CRITICAL: Job repository not initialized. Check app lifespan."
        )
    return _job_repository


def get_job_lock() -> asyncio.Lock:
    """
    Get job repository lock dependency.

    Returns:
        Asyncio lock for repository access

    Raises:
        HTTPException: If lock not initialized
    """
    if _job_lock is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CRITICAL: Job lock not initialized. Check app lifespan."
        )
    return _job_lock


def get_storage_adapter() -> StorageProvider:
    """
    Get storage adapter dependency.

    Returns:
        Configured storage provider (local or S3)

    Raises:
        HTTPException: If storage adapter creation fails

    CRITICAL: NO FALLBACK LOGIC - Errors must propagate explicitly
    """
    try:
        config = get_config()
        storage_config = config.storage

        # Create storage provider based on configuration
        storage_provider = StorageFactory.create_storage_provider(
            storage_mode=storage_config.storage_mode,
            # Local mode parameters
            base_path=storage_config.local_base_path,
            # S3 mode parameters
            bucket=storage_config.test_output_bucket,
            region=storage_config.aws_region,
            kms_key_id=storage_config.kms_key_id if storage_config.kms_key_id else ""
        )

        return storage_provider

    except Exception as e:
        # NO FALLBACK - Explicit failure required for compliance
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CRITICAL: Storage adapter initialization failed: {e}"
        ) from e


def get_current_user() -> str:
    """
    Get current user dependency (mock implementation).

    Returns:
        Mock user ID

    TODO: Replace with Clerk authentication (Task 1.4)
    Currently returns mock user for development/testing.
    """
    # Mock user for development (replace with Clerk integration)
    return "mock_user_dev_001"


async def validate_upload_file(file: UploadFile) -> UploadFile:
    """
    Validate uploaded file before processing.

    Args:
        file: FastAPI UploadFile object

    Returns:
        Validated UploadFile

    Raises:
        HTTPException: If file validation fails

    Validation Checks:
    - File size <= 100MB
    - File extension allowed (.txt, .pdf, .docx, .md)
    - Content type validation (future: python-magic)

    CRITICAL: NO FALLBACK LOGIC - Invalid files rejected explicitly
    """
    # Maximum file size: 100MB
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB in bytes
    ALLOWED_EXTENSIONS = {".txt", ".pdf", ".docx", ".md"}

    # Validate filename exists
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CRITICAL: No filename provided in upload"
        )

    # Validate file extension
    file_extension = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""

    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"CRITICAL: Invalid file extension '{file_extension}'\n"
                f"Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        )

    # Read file content for size validation
    # CRITICAL: Read ONCE and store in memory to avoid double-read
    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"CRITICAL: File too large ({len(content)} bytes)\n"
                f"Maximum allowed: {MAX_FILE_SIZE} bytes (100MB)"
            )
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CRITICAL: Uploaded file is empty"
        )

    # Recreate UploadFile with content in memory
    # This avoids reading file twice (once for validation, once for processing)
    import io
    file.file = io.BytesIO(content)

    logger.info(
        f"File validated: {file.filename} "
        f"({len(content)} bytes, {file_extension})"
    )

    return file


# Type aliases for dependency injection
StorageAdapterDep = Annotated[StorageProvider, Depends(get_storage_adapter)]
JobQueueDep = Annotated[asyncio.Queue[str], Depends(get_job_queue)]
JobRepositoryDep = Annotated[dict[str, JobRecord], Depends(get_job_repository)]
JobLockDep = Annotated[asyncio.Lock, Depends(get_job_lock)]
CurrentUserDep = Annotated[str, Depends(get_current_user)]
ValidatedFileDep = Annotated[UploadFile, Depends(validate_upload_file)]

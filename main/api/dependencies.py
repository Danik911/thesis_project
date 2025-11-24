"""
FastAPI dependency injection functions.

Provides dependency injection for storage adapters, job repositories,
queues, and authentication with testability and configurability.
"""

import asyncio
import logging
import os
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError
from src.adapters.storage import StorageFactory, StorageProvider
from src.shared.config import get_config

from .models import ApprovalRecord, ClerkClaims, JobRecord

logger = logging.getLogger(__name__)

# Clerk Authentication Configuration
CLERK_PEM_PUBLIC_KEY = os.getenv("CLERK_PEM_PUBLIC_KEY")
CLERK_ISSUER = os.getenv("CLERK_ISSUER")
CLERK_JWT_AUDIENCE = os.getenv("CLERK_JWT_AUDIENCE")  # Optional

# HTTPBearer security for token extraction
security = HTTPBearer()

# In-memory job storage (replaced by Aurora in production)
# Protected by asyncio lock for thread-safe access
_job_repository: dict[str, JobRecord] = {}
_job_lock: asyncio.Lock | None = None
_job_queue: asyncio.Queue[str] | None = None

# In-memory approval storage for HIL workflow
# Maps job_id -> list of ApprovalRecords (audit trail)
# Protected by asyncio lock for thread-safe access
_approval_repository: dict[str, list[ApprovalRecord]] = {}
_approval_lock: asyncio.Lock | None = None


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


def initialize_approval_infrastructure() -> tuple[dict[str, list[ApprovalRecord]], asyncio.Lock]:
    """
    Initialize approval repository and lock for HIL workflow.

    Returns:
        Tuple of (approval_repository, approval_lock)

    Called during app lifespan startup.
    """
    global _approval_repository, _approval_lock

    _approval_repository = {}
    _approval_lock = asyncio.Lock()

    logger.info("Approval infrastructure initialized (in-memory mode)")
    return _approval_repository, _approval_lock


def get_approval_repository() -> dict[str, list[ApprovalRecord]]:
    """
    Get approval repository dependency.

    Returns:
        In-memory approval storage dict (job_id -> list of ApprovalRecords)

    Raises:
        HTTPException: If repository not initialized

    CRITICAL: NO FALLBACK LOGIC - Errors must propagate explicitly
    """
    if _approval_repository is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CRITICAL: Approval repository not initialized. Check app lifespan."
        )
    return _approval_repository


def get_approval_lock() -> asyncio.Lock:
    """
    Get approval repository lock dependency.

    Returns:
        Asyncio lock for approval repository access

    Raises:
        HTTPException: If lock not initialized

    CRITICAL: NO FALLBACK LOGIC - Errors must propagate explicitly
    """
    if _approval_lock is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CRITICAL: Approval lock not initialized. Check app lifespan."
        )
    return _approval_lock


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


async def require_clerk_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> ClerkClaims:
    """
    Verify Clerk JWT and return user claims.

    Args:
        credentials: HTTP Authorization header with Bearer token

    Returns:
        Validated ClerkClaims object with user identity

    Raises:
        HTTPException 401: If token is invalid, expired, or missing required claims

    CRITICAL: FAIL CLOSED - NO FALLBACK LOGIC
    All authentication failures result in 401 with explicit error details.
    """
    token = credentials.credentials

    # Validate environment configuration
    if not CLERK_PEM_PUBLIC_KEY:
        logger.error("CLERK_PEM_PUBLIC_KEY not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CRITICAL: Authentication system not configured (missing CLERK_PEM_PUBLIC_KEY)",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not CLERK_ISSUER:
        logger.error("CLERK_ISSUER not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CRITICAL: Authentication system not configured (missing CLERK_ISSUER)",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        # Verify JWT using Clerk's public key with RS256 algorithm
        # Note: Session tokens don't include 'aud' claim, so we disable audience verification
        verify_options = {
            "verify_exp": True,
            "verify_iat": True,
            "verify_aud": False,  # Disable audience verification (session tokens don't have 'aud')
            "leeway": 10  # 10 seconds clock skew tolerance
        }

        payload = jwt.decode(
            token,
            CLERK_PEM_PUBLIC_KEY,
            algorithms=["RS256"],
            issuer=CLERK_ISSUER,
            options=verify_options
        )

        # Validate required claims exist
        if "sub" not in payload:
            logger.warning("JWT missing 'sub' claim")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user identifier",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Parse and validate claims with Pydantic
        user_claims = ClerkClaims(**payload)

        # Warn if email is missing (common in Clerk session tokens)
        if not user_claims.email:
            logger.warning(f"JWT missing 'email' claim for user {user_claims.sub} - will fetch from Clerk API if needed")

        logger.debug(f"Authentication successful for user {user_claims.sub}")

        return user_claims

    except jwt.ExpiredSignatureError:
        logger.info("JWT expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidIssuerError:
        logger.warning(f"Invalid JWT issuer (expected: {CLERK_ISSUER})")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token issuer",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidSignatureError:
        logger.warning("Invalid JWT signature")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token signature",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidAudienceError:
        logger.warning(f"Invalid JWT audience (expected: {CLERK_JWT_AUDIENCE})")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token audience",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except (jwt.DecodeError, PyJWTError) as e:
        logger.warning(f"JWT decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        # FAIL CLOSED: Any unexpected error = 401
        logger.exception("Unexpected authentication error")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"}
        )


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
CurrentUserDep = Annotated[ClerkClaims, Depends(require_clerk_user)]
ValidatedFileDep = Annotated[UploadFile, Depends(validate_upload_file)]

# HIL Approval type aliases
ApprovalRepositoryDep = Annotated[dict[str, list[ApprovalRecord]], Depends(get_approval_repository)]
ApprovalLockDep = Annotated[asyncio.Lock, Depends(get_approval_lock)]

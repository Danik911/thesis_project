"""
FastAPI dependency injection functions.

Provides dependency injection for storage adapters, job repositories,
queues, and authentication with testability and configurability.

Supports both in-memory (testing) and PostgreSQL (docker-compose) storage.
"""

import asyncio
import json
import logging
import os
import time
from typing import Annotated

import asyncpg
import httpx
import jwt
from fastapi import Depends, HTTPException, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError
from src.adapters.storage import StorageFactory, StorageProvider
from src.shared.config import get_config

from .job_repository import PostgresJobRepository, create_postgres_pool
from .models import ApprovalRecord, ClerkClaims, JobRecord

logger = logging.getLogger(__name__)

# Clerk Authentication Configuration
CLERK_PEM_PUBLIC_KEY = os.getenv("CLERK_PEM_PUBLIC_KEY")
CLERK_ISSUER = os.getenv("CLERK_ISSUER")
CLERK_JWT_AUDIENCE = os.getenv("CLERK_JWT_AUDIENCE")  # Optional

# HTTPBearer security for token extraction
security = HTTPBearer()

# JWKS cache for Clerk key rotation resilience
_jwks_cache: dict[str, tuple[float, list[dict[str, object]]]] = {}
_jwks_lock: asyncio.Lock | None = None


def _get_jwks_lock() -> asyncio.Lock:
    global _jwks_lock
    if _jwks_lock is None:
        _jwks_lock = asyncio.Lock()
    return _jwks_lock


def _jwks_url_for_issuer(issuer: str) -> str:
    # Clerk exposes JWKS at /.well-known/jwks.json
    return issuer.rstrip("/") + "/.well-known/jwks.json"


async def _fetch_clerk_jwks(issuer: str) -> list[dict[str, object]]:
    url = _jwks_url_for_issuer(issuer)
    timeout = httpx.Timeout(5.0, connect=5.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.get(url)

    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Authentication failed: unable to fetch Clerk JWKS\n"
                f"Issuer: {issuer}\n"
                f"JWKS URL: {url}\n"
                f"HTTP status: {resp.status_code}"
            ),
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = resp.json()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Authentication failed: invalid JWKS JSON from Clerk\n"
                f"Issuer: {issuer}\n"
                f"JWKS URL: {url}\n"
                f"Error: {e!s}"
            ),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    keys = payload.get("keys") if isinstance(payload, dict) else None
    if not isinstance(keys, list) or not keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Authentication failed: Clerk JWKS missing 'keys'\n"
                f"Issuer: {issuer}\n"
                f"JWKS URL: {url}"
            ),
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Keep only dict keys
    return [k for k in keys if isinstance(k, dict)]


async def _get_clerk_jwks_cached(issuer: str, *, force_refresh: bool = False) -> list[dict[str, object]]:
    # Cache for a short window to avoid per-request network calls.
    # Clerk keys rotate; we allow refresh on signature failure.
    ttl_seconds = 15 * 60
    now = time.time()

    async with _get_jwks_lock():
        if not force_refresh and issuer in _jwks_cache:
            cached_at, keys = _jwks_cache[issuer]
            if (now - cached_at) < ttl_seconds and keys:
                return keys

        keys = await _fetch_clerk_jwks(issuer)
        _jwks_cache[issuer] = (now, keys)
        return keys


def _select_rsa_public_key_from_jwks(token: str, jwks_keys: list[dict[str, object]]):
    try:
        header = jwt.get_unverified_header(token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: invalid JWT header ({e!s})",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    kid = header.get("kid") if isinstance(header, dict) else None
    if not kid or not isinstance(kid, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token validation failed: JWT missing 'kid' header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Find the matching JWK
    for jwk in jwks_keys:
        if jwk.get("kid") == kid:
            try:
                jwk_json = json.dumps(jwk)
                return jwt.algorithms.RSAAlgorithm.from_jwk(jwk_json)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Token validation failed: unable to build public key from JWK (kid={kid}): {e!s}",
                    headers={"WWW-Authenticate": "Bearer"},
                ) from e

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=(
            "Token validation failed: unknown signing key\n"
            f"kid: {kid}\n"
            f"Issuer: {CLERK_ISSUER or 'MISSING'}"
        ),
        headers={"WWW-Authenticate": "Bearer"},
    )

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

# PostgreSQL database connection pool and repository
# Used in docker-compose mode for HIL workflow shared state
_db_pool: asyncpg.Pool | None = None
_db_job_repository: PostgresJobRepository | None = None


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


# =============================================================================
# Database Repository Functions (PostgreSQL)
# =============================================================================


async def initialize_database_repository(database_url: str) -> PostgresJobRepository:
    """
    Initialize PostgreSQL connection pool and job repository.

    Args:
        database_url: PostgreSQL connection string

    Returns:
        PostgresJobRepository instance

    Called during app lifespan startup when DATABASE_URL is set.
    """
    global _db_pool, _db_job_repository

    logger.info(f"[DB] Initializing PostgreSQL connection pool...")
    _db_pool = await create_postgres_pool(database_url)
    _db_job_repository = PostgresJobRepository(_db_pool)

    # Auto-create schema if tables don't exist (idempotent)
    # This enables fresh RDS instances to be ready without manual SQL execution
    await _db_job_repository.ensure_schema()

    logger.info("[DB] PostgreSQL job repository initialized (HIL shared state enabled)")
    return _db_job_repository


async def shutdown_database_repository() -> None:
    """
    Shutdown PostgreSQL connection pool.

    Called during app lifespan shutdown.
    """
    global _db_pool, _db_job_repository

    if _db_pool is not None:
        await _db_pool.close()
        logger.info("[DB] PostgreSQL connection pool closed")

    _db_pool = None
    _db_job_repository = None


def get_db_job_repository() -> PostgresJobRepository | None:
    """
    Get database job repository dependency.

    Returns:
        PostgresJobRepository if initialized, None otherwise
        (None indicates in-memory mode, used for local testing without docker-compose)
    """
    return _db_job_repository


def is_database_mode() -> bool:
    """
    Check if running in database mode (docker-compose).

    Returns:
        True if DATABASE_URL is set and pool initialized
    """
    return _db_job_repository is not None


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
            "leeway": 30  # 30 seconds tolerance for async token refresh delays
        }

        # Primary: use configured PEM if provided; if signature fails, refresh via JWKS.
        # This prevents outages when Clerk rotates keys and PEM isn't updated.
        if CLERK_PEM_PUBLIC_KEY:
            try:
                payload = jwt.decode(
                    token,
                    CLERK_PEM_PUBLIC_KEY,
                    algorithms=["RS256"],
                    issuer=CLERK_ISSUER,
                    options=verify_options,
                )
            except jwt.InvalidSignatureError:
                logger.warning("JWT signature invalid with configured PEM key; retrying with Clerk JWKS (possible key rotation)")
                jwks = await _get_clerk_jwks_cached(CLERK_ISSUER, force_refresh=True)
                key = _select_rsa_public_key_from_jwks(token, jwks)
                payload = jwt.decode(
                    token,
                    key,
                    algorithms=["RS256"],
                    issuer=CLERK_ISSUER,
                    options=verify_options,
                )
        else:
            jwks = await _get_clerk_jwks_cached(CLERK_ISSUER)
            key = _select_rsa_public_key_from_jwks(token, jwks)
            payload = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                issuer=CLERK_ISSUER,
                options=verify_options,
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

# Database repository type alias (PostgreSQL)
DbJobRepositoryDep = Annotated[PostgresJobRepository | None, Depends(get_db_job_repository)]

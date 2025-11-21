"""
Pydantic models for FastAPI job submission and status endpoints.

Defines request/response models and data structures for async job processing
with GAMP-5 compliance requirements.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ClerkClaims(BaseModel):
    """
    Clerk JWT payload model for authentication.

    Pydantic v2 compatible model for validating and parsing Clerk session tokens.
    All fields extracted from JWT claims for GAMP-5 audit traceability.
    """

    sub: str = Field(..., description="Clerk user ID (unique identifier)")
    email: str | None = Field(default=None, description="User email address (optional in session tokens)")
    email_verified: bool = Field(default=False, description="Email verification status")
    iat: int = Field(..., description="Issued at timestamp (Unix epoch)")
    exp: int = Field(..., description="Expiration timestamp (Unix epoch)")
    iss: str = Field(..., description="Issuer URL (Clerk instance)")
    aud: str | None = Field(default=None, description="Audience (optional)")
    azp: str | None = Field(default=None, description="Authorized party (origin)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sub": "user_2j5k7x9m2n",
                "email": "user@example.com",
                "email_verified": True,
                "iat": 1699000000,
                "exp": 1699003600,
                "iss": "https://your-instance.clerk.accounts.dev",
                "aud": "https://api.example.com",
                "azp": "https://app.example.com"
            }
        }
    )


class JobStatus(str, Enum):
    """Job processing status enumeration."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobSubmitResponse(BaseModel):
    """Response model for job submission endpoint."""

    job_id: str = Field(description="Unique job identifier (UUID)")
    status: JobStatus = Field(description="Initial job status (always 'pending')")
    created_at: str = Field(description="Job creation timestamp (UTC ISO 8601)")
    urs_hash: str = Field(description="SHA-256 hash of uploaded URS file")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "pending",
                "created_at": "2025-11-11T14:30:00Z",
                "urs_hash": "a3b2c1d4e5f6..."
            }
        }
    )


class JobStatusResponse(BaseModel):
    """Response model for job status endpoint."""

    job_id: str = Field(description="Unique job identifier")
    status: JobStatus = Field(description="Current job status")
    created_at: str = Field(description="Job creation timestamp (UTC ISO 8601)")
    started_at: str | None = Field(default=None, description="Processing start timestamp")
    completed_at: str | None = Field(default=None, description="Completion timestamp")

    # File metadata
    urs_filename: str = Field(description="Original URS filename")
    urs_hash: str = Field(description="SHA-256 hash of URS content")
    urs_size_bytes: int = Field(description="URS file size in bytes")

    # Results (only present if completed)
    result_uri: str | None = Field(default=None, description="Storage URI for result artifact")
    download_url: str | None = Field(default=None, description="Pre-signed download URL")
    trace_id: str | None = Field(default=None, description="Langfuse trace identifier for observability")
    trace_url: str | None = Field(default=None, description="Direct Langfuse link for deep diagnostics")

    # Error details (only present if failed)
    error_message: str | None = Field(default=None, description="Error message if job failed")
    error_type: str | None = Field(default=None, description="Error type classification")
    retry_count: int = Field(default=0, description="Number of retry attempts")

    # GAMP-5 compliance metadata
    user_id: str = Field(description="User identifier (Clerk user ID)")
    gamp_category: str | None = Field(default=None, description="GAMP-5 categorization result")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "completed",
                "created_at": "2025-11-11T14:30:00Z",
                "started_at": "2025-11-11T14:30:05Z",
                "completed_at": "2025-11-11T14:32:45Z",
                "urs_filename": "requirements.txt",
                "urs_hash": "a3b2c1d4e5f6...",
                "urs_size_bytes": 5432,
                "result_uri": "file:///output/job_550e8400/test_suite.md",
                "trace_id": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6",
                "trace_url": "https://cloud.langfuse.com/project/example/traces/a1b2c3",
                "download_url": "http://localhost:8000/jobs/550e8400.../download",
                "error_message": None,
                "error_type": None,
                "retry_count": 0,
                "user_id": "user_2abc123xyz",
                "gamp_category": "5"
            }
        }
    )


class JobRecord(BaseModel):
    """Internal job record for in-memory storage."""

    job_id: str
    status: JobStatus
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # File metadata
    urs_filename: str
    urs_storage_key: str  # Storage adapter key
    urs_hash: str
    urs_size_bytes: int

    # Processing metadata
    result_uri: str | None = None
    trace_id: str | None = None
    trace_url: str | None = None
    error_message: str | None = None
    error_type: str | None = None
    retry_count: int = 0
    max_retries: int = 3

    # GAMP-5 compliance
    user_id: str
    gamp_category: str | None = None

    def to_response(self, download_url: str | None = None) -> JobStatusResponse:
        """
        Convert JobRecord to JobStatusResponse.

        Args:
            download_url: Optional pre-signed download URL

        Returns:
            JobStatusResponse model for API response
        """
        return JobStatusResponse(
            job_id=self.job_id,
            status=self.status,
            created_at=self.created_at.isoformat(),
            started_at=self.started_at.isoformat() if self.started_at else None,
            completed_at=self.completed_at.isoformat() if self.completed_at else None,
            urs_filename=self.urs_filename,
            urs_hash=self.urs_hash,
            urs_size_bytes=self.urs_size_bytes,
            result_uri=self.result_uri,
            download_url=download_url,
            trace_id=self.trace_id,
            trace_url=self.trace_url,
            error_message=self.error_message,
            error_type=self.error_type,
            retry_count=self.retry_count,
            user_id=self.user_id,
            gamp_category=self.gamp_category
        )


class AuditLogEntry(BaseModel):
    """Audit log entry for GAMP-5/ALCOA+ compliance."""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    job_id: str
    event_type: str  # submit, start, complete, fail, retry, auth_success, auth_failure
    user_id: str
    status: JobStatus

    # ALCOA+ principles
    # - Attributable: user_id, user_email, timestamp
    # - Contemporaneous: timestamp at event time, token_iat
    # - Original: immutable once created
    # - Accurate: reflects actual state
    # - Complete: all relevant context included (IP, session, token lifecycle)

    # Extended ALCOA+ fields for Clerk authentication
    user_email: str | None = Field(default=None, description="User email for attribution")
    token_iat: int | None = Field(default=None, description="JWT issued-at timestamp")
    ip_address: str | None = Field(default=None, description="Client IP address")
    session_id: str | None = Field(default=None, description="Session ID for event linking")

    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "timestamp": "2025-11-11T14:30:00Z",
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "event_type": "submit",
                "user_id": "user_2abc123xyz",
                "status": "pending",
                "user_email": "user@example.com",
                "token_iat": 1699000000,
                "ip_address": "192.168.1.1",
                "session_id": "sess_abc123xyz",
                "metadata": {
                    "urs_filename": "requirements.txt",
                    "urs_size_bytes": 5432,
                    "urs_hash": "a3b2c1d4e5f6...",
                    "token_exp": 1699003600
                }
            }
        }
    )

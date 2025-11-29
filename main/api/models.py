"""
Pydantic models for FastAPI job submission and status endpoints.

Defines request/response models and data structures for async job processing
with GAMP-5 compliance requirements.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

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
    AWAITING_APPROVAL = "awaiting_approval"  # HIL: Workflow paused for human decision
    APPROVED = "approved"                     # HIL: Human approved, resuming workflow
    REJECTED = "rejected"                     # HIL: Human rejected or approval timeout
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowStage(str, Enum):
    """
    Workflow stages for frontend progress tracking.

    Maps to stages in UnifiedTestGenerationWorkflow for grounded progress display.
    Progress percentages are fixed per stage (not time-based).
    """

    QUEUED = "queued"                      # 0% - Job submitted, waiting in queue
    INGESTION = "ingestion"                # 10% - Loading document, OWASP validation
    CATEGORIZATION = "categorization"      # 25% - GAMP-5 AI categorization
    HIL_WAITING = "hil_waiting"            # 30% - Human-in-the-loop approval pause
    PLANNING = "planning"                  # 45% - Test strategy generation
    AGENT_EXECUTION = "agent_execution"    # 65% - Parallel agent execution (Context, Research, SME)
    OQ_GENERATION = "oq_generation"        # 85% - OQ test case generation
    COMPLETION = "completion"              # 100% - Finalizing, saving results


# Stage-to-progress mapping for server-side calculation
STAGE_PROGRESS_MAP: dict[str, int] = {
    "queued": 0,
    "ingestion": 10,
    "categorization": 25,
    "hil_waiting": 30,
    "planning": 45,
    "agent_execution": 65,
    "oq_generation": 85,
    "completion": 100
}


# Human-readable stage labels for frontend display
STAGE_LABELS: dict[str, str] = {
    "queued": "Queued",
    "ingestion": "Loading Document",
    "categorization": "GAMP-5 Classification",
    "hil_waiting": "Awaiting Human Approval",
    "planning": "Planning Test Strategy",
    "agent_execution": "Executing AI Agents",
    "oq_generation": "Generating Test Cases",
    "completion": "Finalizing Results"
}


class ApprovalDecision(str, Enum):
    """Human approval decision options for GAMP-5 categorization."""

    APPROVE = "APPROVE"              # Accept AI categorization or override with human category
    REJECT = "REJECT"                # Reject categorization, stop workflow
    REQUEST_REVISION = "REQUEST_REVISION"  # Request additional information (future)


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

    # Progress tracking (for frontend progress bar)
    current_stage: str | None = Field(default=None, description="Current workflow stage (e.g., 'categorization', 'oq_generation')")
    current_stage_label: str | None = Field(default=None, description="Human-readable stage label (e.g., 'GAMP-5 Classification')")
    progress_percentage: int | None = Field(default=None, ge=0, le=100, description="Progress percentage (0-100) based on current stage")
    stage_started_at: str | None = Field(default=None, description="When current stage started (ISO 8601)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "processing",
                "created_at": "2025-11-11T14:30:00Z",
                "started_at": "2025-11-11T14:30:05Z",
                "completed_at": None,
                "urs_filename": "requirements.txt",
                "urs_hash": "a3b2c1d4e5f6...",
                "urs_size_bytes": 5432,
                "result_uri": None,
                "trace_id": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6",
                "trace_url": "https://cloud.langfuse.com/project/example/traces/a1b2c3",
                "download_url": None,
                "error_message": None,
                "error_type": None,
                "retry_count": 0,
                "user_id": "user_2abc123xyz",
                "gamp_category": None,
                "current_stage": "categorization",
                "current_stage_label": "GAMP-5 Classification",
                "progress_percentage": 25,
                "stage_started_at": "2025-11-11T14:30:10Z"
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
    updated_at: datetime | None = None  # Last modification timestamp (HIL updates)

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

    # HIL Approval Tracking (Task 3.13)
    requires_approval: bool = False
    approval_reason: str | None = None
    approval_timeout_at: datetime | None = None
    categorization_result: dict | None = None  # AI recommendation + ambiguity details
    human_category: int | None = None  # Final human-approved category (1, 3, 4, or 5)

    # Progress tracking (for frontend progress bar)
    current_stage: WorkflowStage | None = None  # Current workflow stage
    stage_started_at: datetime | None = None    # When current stage started
    stages_completed: list[str] = []            # List of completed stages (for audit trail)

    # Additional metadata
    metadata: dict[str, Any] | None = None

    def to_response(self, download_url: str | None = None) -> JobStatusResponse:
        """
        Convert JobRecord to JobStatusResponse.

        Args:
            download_url: Optional pre-signed download URL

        Returns:
            JobStatusResponse model for API response
        """
        # Calculate progress percentage based on current stage
        progress_percentage: int | None = None
        current_stage_str: str | None = None
        current_stage_label: str | None = None

        if self.status == JobStatus.COMPLETED:
            progress_percentage = 100
            current_stage_str = "completion"
            current_stage_label = STAGE_LABELS.get("completion")
        elif self.status == JobStatus.FAILED:
            progress_percentage = 100  # Show 100% on failure (job ended)
            current_stage_str = self.current_stage.value if self.current_stage else None
            current_stage_label = STAGE_LABELS.get(current_stage_str) if current_stage_str else None
        elif self.current_stage:
            current_stage_str = self.current_stage.value
            progress_percentage = STAGE_PROGRESS_MAP.get(current_stage_str, 0)
            current_stage_label = STAGE_LABELS.get(current_stage_str)
        elif self.status == JobStatus.PENDING:
            progress_percentage = 0
            current_stage_str = "queued"
            current_stage_label = STAGE_LABELS.get("queued")
        elif self.status == JobStatus.PROCESSING:
            # PROCESSING but no stage set yet - default to ingestion (10%)
            progress_percentage = 10
            current_stage_str = "ingestion"
            current_stage_label = STAGE_LABELS.get("ingestion")

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
            gamp_category=self.gamp_category,
            # Progress tracking fields
            current_stage=current_stage_str,
            current_stage_label=current_stage_label,
            progress_percentage=progress_percentage,
            stage_started_at=self.stage_started_at.isoformat() if self.stage_started_at else None
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


# =============================================================================
# HIL Approval Models (Task 3.13)
# =============================================================================


class ApprovalRecord(BaseModel):
    """
    ALCOA+ compliant audit trail for human approval decisions.

    Captures all human decisions with comprehensive pharmaceutical compliance
    metadata for regulatory audit requirements.

    ALCOA+ Compliance:
    - Attributable: user_id, user_email, user_role captured
    - Legible: justification in plain text
    - Contemporaneous: timestamp captured at decision time
    - Original: stored as immutable record
    - Accurate: digital signature validates authenticity
    - Complete: all decision context preserved
    - Consistent: single source of truth
    - Enduring: permanent audit trail
    - Available: queryable by job_id, user_id, timestamp
    """

    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique approval record ID")
    job_id: str = Field(..., description="Associated job ID")

    # AI Recommendation (captured at time of HIL trigger)
    ai_category: int = Field(..., ge=1, le=5, description="Original AI-recommended GAMP-5 category")
    ai_confidence: float = Field(..., ge=0.0, le=1.0, description="AI confidence score (0.0-1.0)")
    ai_reasoning: str = Field(..., description="AI reasoning for categorization")
    ambiguity_reason: str | None = Field(default=None, description="Why HIL was triggered")
    alternative_categories: list[int] | None = Field(
        default=None,
        description="Other plausible GAMP categories identified"
    )

    # Human Decision
    approval_decision: ApprovalDecision = Field(..., description="Human decision: APPROVE, REJECT, or REQUEST_REVISION")
    human_category: int | None = Field(
        default=None,
        ge=1,
        le=5,
        description="Final GAMP-5 category (if APPROVE, can override AI recommendation)"
    )
    justification: str = Field(
        ...,
        min_length=10,
        description="Human's reasoning for decision (minimum 10 characters for audit trail)"
    )

    # ALCOA+ Compliance Fields
    user_id: str = Field(..., description="Clerk user ID (unique identifier)")
    user_email: str | None = Field(default=None, description="User email for traceability")
    user_role: str = Field(default="User", description="User role (Quality Manager, etc.)")
    digital_signature: str = Field(..., description="Digital signature: {user_id}_{timestamp} format")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Decision timestamp (UTC)"
    )

    # Request Metadata
    ip_address: str | None = Field(default=None, description="Client IP address for audit")
    user_agent: str | None = Field(default=None, description="Browser/client info")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "ai_category": 4,
                "ai_confidence": 0.72,
                "ai_reasoning": "System appears to be configured COTS but contains optional custom modules",
                "ambiguity_reason": "Category 4/5 boundary: contains 'optional custom modules'",
                "alternative_categories": [4, 5],
                "approval_decision": "APPROVE",
                "human_category": 4,
                "justification": "System clearly falls under Category 4: configured COTS with no custom source code modifications.",
                "user_id": "user_2abc123xyz",
                "user_email": "quality.manager@pharma.com",
                "user_role": "Quality Manager",
                "digital_signature": "user_2abc123xyz_20251124_143052",
                "timestamp": "2025-11-24T14:30:52Z",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0..."
            }
        }
    )


class ApprovalRequest(BaseModel):
    """
    Request body for submitting human approval decision.

    Used by frontend to submit human decisions on ambiguous GAMP-5 categorizations.
    """

    approval_decision: ApprovalDecision = Field(
        ...,
        description="Human decision: APPROVE, REJECT, or REQUEST_REVISION"
    )
    human_category: int | None = Field(
        default=None,
        ge=1,
        le=5,
        description="Final GAMP-5 category if APPROVE (can override AI recommendation)"
    )
    justification: str = Field(
        ...,
        min_length=10,
        description="Human's reasoning for decision (minimum 10 characters for audit trail)"
    )
    user_signature: str = Field(
        ...,
        description="Digital signature: {user_id}_{timestamp} format (pre-filled from Clerk)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "approval_decision": "APPROVE",
                "human_category": 4,
                "justification": "System clearly falls under Category 4: configured COTS with no custom source code modifications.",
                "user_signature": "user_2abc123xyz_20251124_143052"
            }
        }
    )


class ApprovalResponse(BaseModel):
    """Response after approval decision submission."""

    job_id: str = Field(..., description="Job ID")
    status: JobStatus = Field(..., description="Updated job status")
    gamp_category: int = Field(..., description="Final GAMP-5 category")
    workflow_resumed: bool = Field(..., description="Whether workflow will resume")
    trace_id: str | None = Field(default=None, description="Langfuse trace ID")
    message: str = Field(..., description="Human-readable result message")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "approved",
                "gamp_category": 4,
                "workflow_resumed": True,
                "trace_id": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6",
                "message": "Approval decision 'APPROVE' recorded. Workflow resuming with Category 4."
            }
        }
    )


class JobStatusWithApproval(BaseModel):
    """
    Extended job status response including HIL approval details.

    Used by frontend for polling during approval workflow to get full context.
    """

    job_id: str = Field(..., description="Job ID")
    status: JobStatus = Field(..., description="Current job status")
    requires_approval: bool = Field(..., description="Whether job requires human approval")
    approval_reason: str | None = Field(default=None, description="Why approval is required")
    timeout_remaining_seconds: int | None = Field(
        default=None,
        description="Seconds remaining before approval timeout (auto-reject)"
    )

    # Categorization context for human decision
    categorization_result: dict | None = Field(
        default=None,
        description="AI categorization result including category, confidence, reasoning"
    )
    alternative_categories: list[int] | None = Field(
        default=None,
        description="Other plausible GAMP categories if ambiguous"
    )

    # Progress tracking (for frontend progress bar)
    current_stage: str | None = Field(default=None, description="Current workflow stage")
    current_stage_label: str | None = Field(default=None, description="Human-readable stage label")
    progress_percentage: int | None = Field(default=None, ge=0, le=100, description="Progress percentage (0-100)")

    # Timestamps
    created_at: str = Field(..., description="Job creation timestamp (ISO 8601)")
    updated_at: str | None = Field(default=None, description="Last update timestamp (ISO 8601)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "awaiting_approval",
                "requires_approval": True,
                "approval_reason": "Category 4/5 boundary: contains 'optional custom modules'",
                "timeout_remaining_seconds": 3542,
                "categorization_result": {
                    "category": 4,
                    "confidence_score": 0.72,
                    "reasoning": "System appears to be configured COTS...",
                    "has_ambiguity_signals": True,
                    "ambiguity_details": "Category 4/5 boundary detected"
                },
                "alternative_categories": [4, 5],
                "created_at": "2025-11-24T14:30:00Z",
                "updated_at": "2025-11-24T14:31:15Z"
            }
        }
    )

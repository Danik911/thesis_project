"""In-memory job store with mandatory HITL state machine.

Job lifecycle enforces human-in-the-loop approval:

    EXTRACTING -> GENERATING -> PENDING_REVIEW -> APPROVED -> EXPORTED
                                       |
                                     FAILED (from EXTRACTING or GENERATING only)

GAMP-5 Category 5: Custom pharmaceutical software component.
No fallback logic -- all errors propagate with full diagnostics.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class LIMSJobStatus(str, Enum):
    """Job status values for the LIMS state machine."""

    EXTRACTING = "EXTRACTING"
    GENERATING = "GENERATING"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    EXPORTED = "EXPORTED"
    FAILED = "FAILED"


# ---------------------------------------------------------------------------
# State machine transitions
# ---------------------------------------------------------------------------

VALID_TRANSITIONS: dict[LIMSJobStatus, set[LIMSJobStatus]] = {
    LIMSJobStatus.EXTRACTING: {LIMSJobStatus.GENERATING, LIMSJobStatus.FAILED},
    LIMSJobStatus.GENERATING: {LIMSJobStatus.PENDING_REVIEW, LIMSJobStatus.FAILED},
    LIMSJobStatus.PENDING_REVIEW: {LIMSJobStatus.APPROVED},
    LIMSJobStatus.APPROVED: {LIMSJobStatus.EXPORTED},
    LIMSJobStatus.EXPORTED: set(),  # terminal
    LIMSJobStatus.FAILED: set(),  # terminal
}


# ---------------------------------------------------------------------------
# Job model
# ---------------------------------------------------------------------------


class LIMSJob(BaseModel):
    """Persistent job record for the LIMS pipeline.

    Tracks the full lifecycle from PDF upload through HITL approval to
    XLSX export. chat_history and edit_log provide audit trail for
    ALCOA+ compliance.
    """

    job_id: str
    status: LIMSJobStatus
    created_at: datetime
    updated_at: datetime
    pdf_filename: str
    raw_extraction: Optional[dict[str, Any]] = None
    mda_template: Optional[dict[str, Any]] = None
    chat_history: list[dict[str, Any]] = Field(default_factory=list)
    edit_log: list[dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# In-memory store (acceptable for PoC)
# ---------------------------------------------------------------------------

_jobs: dict[str, LIMSJob] = {}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def create_job(pdf_filename: str) -> str:
    """Create a new LIMS job in EXTRACTING state.

    Args:
        pdf_filename: Original filename of the uploaded PDF.

    Returns:
        The generated job_id (UUID4 hex).

    Raises:
        ValueError: If pdf_filename is empty.
    """
    if not pdf_filename or not pdf_filename.strip():
        raise ValueError("pdf_filename must not be empty")

    job_id = uuid4().hex
    now = datetime.now(timezone.utc)

    job = LIMSJob(
        job_id=job_id,
        status=LIMSJobStatus.EXTRACTING,
        created_at=now,
        updated_at=now,
        pdf_filename=pdf_filename,
    )

    _jobs[job_id] = job

    logger.info(
        "Created LIMS job %s for '%s' (status=%s)",
        job_id,
        pdf_filename,
        job.status.value,
    )

    return job_id


def get_job(job_id: str) -> LIMSJob:
    """Retrieve a job by ID.

    Args:
        job_id: The UUID hex string returned by create_job().

    Returns:
        The LIMSJob record.

    Raises:
        KeyError: If job_id does not exist.
    """
    if job_id not in _jobs:
        raise KeyError(
            f"Job '{job_id}' not found. "
            f"Available jobs: {list(_jobs.keys()) if _jobs else '(none)'}"
        )
    return _jobs[job_id]


def update_status(job_id: str, new_status: LIMSJobStatus) -> LIMSJob:
    """Transition a job to a new status, enforcing the state machine.

    IMPORTANT: This function cannot transition to APPROVED. Use
    approve_job() instead -- that is the ONLY path to APPROVED status,
    ensuring mandatory human-in-the-loop approval.

    Args:
        job_id: The job to update.
        new_status: The target status.

    Returns:
        The updated LIMSJob.

    Raises:
        KeyError: If job_id does not exist.
        ValueError: If the transition is invalid per VALID_TRANSITIONS.
        ValueError: If attempting to set APPROVED via update_status
            (must use approve_job instead).
    """
    job = get_job(job_id)

    # Block APPROVED via update_status -- enforce HITL gate
    if new_status == LIMSJobStatus.APPROVED:
        raise ValueError(
            f"Cannot transition job '{job_id}' to APPROVED via update_status(). "
            f"Use approve_job() instead -- human approval is MANDATORY. "
            f"Current status: {job.status.value}"
        )

    allowed = VALID_TRANSITIONS.get(job.status, set())
    if new_status not in allowed:
        raise ValueError(
            f"Invalid state transition for job '{job_id}': "
            f"{job.status.value} -> {new_status.value}. "
            f"Allowed transitions from {job.status.value}: "
            f"{sorted(s.value for s in allowed) if allowed else '(terminal state, no transitions allowed)'}"
        )

    old_status = job.status
    job.status = new_status
    job.updated_at = datetime.now(timezone.utc)

    logger.info(
        "Job %s transitioned: %s -> %s",
        job_id,
        old_status.value,
        new_status.value,
    )

    return job


def approve_job(job_id: str) -> LIMSJob:
    """Human approval gate -- the ONLY path to APPROVED status.

    This function enforces mandatory HITL (Human-In-The-Loop) review.
    The job MUST be in PENDING_REVIEW state to be approved.

    Args:
        job_id: The job to approve.

    Returns:
        The updated LIMSJob with APPROVED status.

    Raises:
        KeyError: If job_id does not exist.
        ValueError: If job is not in PENDING_REVIEW state.
    """
    job = get_job(job_id)

    if job.status != LIMSJobStatus.PENDING_REVIEW:
        raise ValueError(
            f"Cannot approve job '{job_id}': current status is {job.status.value}. "
            f"Only jobs in PENDING_REVIEW can be approved. "
            f"This is a mandatory HITL gate -- no auto-approval is permitted."
        )

    job.status = LIMSJobStatus.APPROVED
    job.updated_at = datetime.now(timezone.utc)

    logger.info(
        "Job %s APPROVED by human reviewer (HITL gate passed)",
        job_id,
    )

    return job

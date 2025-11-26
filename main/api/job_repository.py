"""
Database-backed Job Repository for HIL workflow.

Provides shared state between API and Worker containers via PostgreSQL.
Implements adapter pattern for AWS migration compatibility (Task 4.2).

Local Development: PostgresJobRepository (asyncpg)
AWS Production: AuroraDataAPIJobRepository (boto3 rds-data) - TODO

CRITICAL: This replaces in-memory dict to fix HIL workflow resumption.
"""

import json
import logging
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

import asyncpg

from .models import JobRecord, JobStatus

logger = logging.getLogger(__name__)


class JobRepositoryProtocol(Protocol):
    """
    Abstract interface for job repository.

    Enables adapter pattern for local PostgreSQL vs Aurora Data API.
    """

    async def get(self, job_id: str) -> JobRecord | None:
        """Get job by ID."""
        ...

    async def create(self, job: JobRecord) -> None:
        """Create new job record."""
        ...

    async def update(self, job: JobRecord) -> None:
        """Update entire job record."""
        ...

    async def set_approval_status(
        self,
        job_id: str,
        status: JobStatus,
        human_category: int | None = None
    ) -> None:
        """Update job approval status (used by API approval endpoint)."""
        ...

    async def get_jobs_by_user(
        self,
        user_id: str,
        limit: int = 50
    ) -> list[JobRecord]:
        """Get jobs for a specific user."""
        ...

    async def get_pending_jobs(self) -> list[JobRecord]:
        """Get all jobs with PENDING status."""
        ...


class PostgresJobRepository:
    """
    PostgreSQL-backed job repository using asyncpg.

    Provides shared state between API and Worker containers.
    Used for local development with docker-compose.
    """

    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def get(self, job_id: str) -> JobRecord | None:
        """
        Get job by ID.

        Args:
            job_id: Job UUID as string

        Returns:
            JobRecord if found, None otherwise
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM jobs WHERE job_id = $1",
                UUID(job_id)
            )

            if row is None:
                return None

            return self._row_to_job_record(row)

    async def create(self, job: JobRecord) -> None:
        """
        Create new job record.

        Args:
            job: JobRecord to persist
        """
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO jobs (
                    job_id, status, created_at, started_at, completed_at, updated_at,
                    urs_filename, urs_storage_key, urs_hash, urs_size_bytes,
                    user_id, result_uri, gamp_category,
                    requires_approval, approval_reason, approval_timeout_at,
                    categorization_result, human_category,
                    trace_id, trace_url,
                    error_message, error_type, retry_count, max_retries
                ) VALUES (
                    $1, $2, $3, $4, $5, $6,
                    $7, $8, $9, $10,
                    $11, $12, $13,
                    $14, $15, $16,
                    $17, $18,
                    $19, $20,
                    $21, $22, $23, $24
                )
                """,
                UUID(job.job_id),
                job.status.value,
                job.created_at,
                job.started_at,
                job.completed_at,
                job.updated_at,
                job.urs_filename,
                job.urs_storage_key,
                job.urs_hash,
                job.urs_size_bytes,
                job.user_id,
                job.result_uri,
                job.gamp_category,
                job.requires_approval,
                job.approval_reason,
                job.approval_timeout_at,
                json.dumps(job.categorization_result) if job.categorization_result else None,
                str(job.human_category) if job.human_category else None,
                job.trace_id,
                job.trace_url,
                job.error_message,
                job.error_type,
                job.retry_count,
                job.max_retries
            )

            logger.debug(f"Created job record: {job.job_id}")

    async def update(self, job: JobRecord) -> None:
        """
        Update entire job record.

        Args:
            job: JobRecord with updated values
        """
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE jobs SET
                    status = $2,
                    started_at = $3,
                    completed_at = $4,
                    updated_at = $5,
                    result_uri = $6,
                    gamp_category = $7,
                    requires_approval = $8,
                    approval_reason = $9,
                    approval_timeout_at = $10,
                    categorization_result = $11,
                    human_category = $12,
                    trace_id = $13,
                    trace_url = $14,
                    error_message = $15,
                    error_type = $16,
                    retry_count = $17
                WHERE job_id = $1
                """,
                UUID(job.job_id),
                job.status.value,
                job.started_at,
                job.completed_at,
                datetime.now(UTC),  # Always update updated_at
                job.result_uri,
                job.gamp_category,
                job.requires_approval,
                job.approval_reason,
                job.approval_timeout_at,
                json.dumps(job.categorization_result) if job.categorization_result else None,
                str(job.human_category) if job.human_category else None,
                job.trace_id,
                job.trace_url,
                job.error_message,
                job.error_type,
                job.retry_count
            )

            logger.debug(f"Updated job record: {job.job_id}")

    async def set_approval_status(
        self,
        job_id: str,
        status: JobStatus,
        human_category: int | None = None
    ) -> None:
        """
        Update job approval status.

        Used by API approval endpoint to update status visible to worker.

        Args:
            job_id: Job UUID as string
            status: New job status (APPROVED, REJECTED, etc.)
            human_category: Human-approved GAMP category (optional)
        """
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE jobs SET
                    status = $2,
                    human_category = $3,
                    requires_approval = FALSE,
                    approval_timeout_at = NULL,
                    updated_at = $4
                WHERE job_id = $1
                """,
                UUID(job_id),
                status.value,
                str(human_category) if human_category else None,
                datetime.now(UTC)
            )

            logger.info(
                f"[HIL-DB] Updated job {job_id} status to {status.value}, "
                f"human_category={human_category}"
            )

    async def set_awaiting_approval(
        self,
        job_id: str,
        approval_reason: str,
        approval_timeout_at: datetime,
        categorization_result: dict | None = None
    ) -> None:
        """
        Set job to AWAITING_APPROVAL status with HIL metadata.

        Used by worker when categorization requires human review.

        Args:
            job_id: Job UUID as string
            approval_reason: Why approval is needed
            approval_timeout_at: Deadline for approval
            categorization_result: AI categorization data
        """
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE jobs SET
                    status = $2,
                    requires_approval = TRUE,
                    approval_reason = $3,
                    approval_timeout_at = $4,
                    categorization_result = $5,
                    updated_at = $6
                WHERE job_id = $1
                """,
                UUID(job_id),
                JobStatus.AWAITING_APPROVAL.value,
                approval_reason,
                approval_timeout_at,
                json.dumps(categorization_result) if categorization_result else None,
                datetime.now(UTC)
            )

            logger.info(
                f"[HIL-DB] Job {job_id} set to AWAITING_APPROVAL. "
                f"Timeout: {approval_timeout_at.isoformat()}"
            )

    async def get_jobs_by_user(
        self,
        user_id: str,
        limit: int = 50
    ) -> list[JobRecord]:
        """
        Get jobs for a specific user, ordered by creation date (newest first).

        Args:
            user_id: Clerk user ID
            limit: Maximum number of jobs to return

        Returns:
            List of JobRecord objects
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM jobs
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                user_id,
                limit
            )

            return [self._row_to_job_record(row) for row in rows]

    async def get_pending_jobs(self) -> list[JobRecord]:
        """
        Get all jobs awaiting processing (pending, processing, or approved).

        Returns jobs whose status is either 'pending', 'processing', or 'approved'.
        Used on startup to re-populate the job queue when the API/worker
        restarts and needs to recover work that never completed.

        CRITICAL: Includes APPROVED status for HIL workflow recovery.
        When a job is approved by human reviewer but worker restarts before
        resuming the workflow, this ensures the approved job is re-enqueued
        and processed with the human-approved category.

        Returns:
            List of JobRecord objects
        """
        async with self._pool.acquire() as conn:
            restartable_statuses = [
                JobStatus.PENDING.value,
                JobStatus.PROCESSING.value,
                JobStatus.APPROVED.value  # HIL recovery: resume approved jobs
            ]

            rows = await conn.fetch(
                """
                SELECT * FROM jobs
                WHERE status = ANY($1::text[])
                ORDER BY created_at ASC
                """,
                restartable_statuses
            )

            return [self._row_to_job_record(row) for row in rows]

    def _row_to_job_record(self, row: asyncpg.Record) -> JobRecord:
        """
        Convert asyncpg row to JobRecord.

        Handles type conversions between PostgreSQL and Python.
        """
        # Parse categorization_result from JSONB
        categorization_result = None
        if row['categorization_result']:
            if isinstance(row['categorization_result'], str):
                categorization_result = json.loads(row['categorization_result'])
            else:
                categorization_result = dict(row['categorization_result'])

        # Parse human_category from VARCHAR to int
        human_category = None
        if row['human_category']:
            human_category = int(row['human_category'])

        return JobRecord(
            job_id=str(row['job_id']),
            status=JobStatus(row['status']),
            created_at=row['created_at'],
            started_at=row['started_at'],
            completed_at=row['completed_at'],
            updated_at=row['updated_at'],
            urs_filename=row['urs_filename'],
            urs_storage_key=row['urs_storage_key'],
            urs_hash=row['urs_hash'],
            urs_size_bytes=row['urs_size_bytes'],
            user_id=row['user_id'],
            result_uri=row['result_uri'],
            gamp_category=row['gamp_category'],
            requires_approval=row['requires_approval'] or False,
            approval_reason=row['approval_reason'],
            approval_timeout_at=row['approval_timeout_at'],
            categorization_result=categorization_result,
            human_category=human_category,
            trace_id=row['trace_id'],
            trace_url=row['trace_url'],
            error_message=row['error_message'],
            error_type=row['error_type'],
            retry_count=row['retry_count'] or 0,
            max_retries=row['max_retries'] or 3
        )


async def create_postgres_pool(database_url: str) -> asyncpg.Pool:
    """
    Create asyncpg connection pool.

    Args:
        database_url: PostgreSQL connection string

    Returns:
        asyncpg.Pool instance
    """
    pool = await asyncpg.create_pool(
        database_url,
        min_size=2,
        max_size=10,
        command_timeout=60
    )

    logger.info(f"[DB] Created PostgreSQL connection pool (min=2, max=10)")
    return pool

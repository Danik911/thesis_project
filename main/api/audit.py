"""
Audit logging utilities for GAMP-5/ALCOA+ compliance.

Provides immutable audit trail for all job lifecycle events with
contemporaneous timestamping and user attribution.
"""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .models import AuditLogEntry, JobStatus

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Audit logger for pharmaceutical compliance requirements.

    Implements ALCOA+ principles:
    - Attributable: User ID captured for every event
    - Legible: Human-readable JSON format
    - Contemporaneous: Timestamps captured at event time
    - Original: Append-only, no modifications
    - Accurate: Reflects actual system state
    - Complete: All relevant context included
    - Consistent: Standard format across all events
    - Enduring: File-based persistence with retention
    - Available: Queryable via filesystem
    """

    def __init__(self, audit_directory: str = "logs/audit/jobs") -> None:
        """
        Initialize audit logger.

        Args:
            audit_directory: Directory for audit log files

        Raises:
            RuntimeError: If audit directory cannot be created
        """
        self.audit_directory = Path(audit_directory)

        try:
            self.audit_directory.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise RuntimeError(
                f"CRITICAL: Failed to create audit directory\n"
                f"Path: {audit_directory}\n"
                f"Error: {e}"
            ) from e

        logger.info(f"Audit logger initialized: {self.audit_directory}")

    def log_event(
        self,
        job_id: str,
        event_type: str,
        user_id: str,
        status: JobStatus,
        metadata: dict[str, Any] | None = None,
        user_email: str | None = None,
        token_iat: int | None = None,
        ip_address: str | None = None,
        session_id: str | None = None
    ) -> None:
        """
        Log an audit event with ALCOA+ compliance.

        Args:
            job_id: Unique job identifier
            event_type: Event type (submit, start, complete, fail, retry, auth_success, auth_failure)
            user_id: User identifier (Clerk user ID from 'sub' claim)
            status: Current job status
            metadata: Additional event context
            user_email: User email for human-readable attribution (ALCOA+)
            token_iat: JWT issued-at timestamp for lifecycle tracking (ALCOA+)
            ip_address: Client IP address for contemporaneous context (ALCOA+)
            session_id: Session ID for linking related events (ALCOA+)

        Raises:
            RuntimeError: If audit logging fails

        CRITICAL: NO FALLBACK LOGIC - Audit failures must be explicit
        """
        try:
            # Create audit entry with contemporaneous timestamp
            entry = AuditLogEntry(
                timestamp=datetime.now(UTC),
                job_id=job_id,
                event_type=event_type,
                user_id=user_id,
                status=status,
                metadata=metadata or {},
                user_email=user_email,
                token_iat=token_iat,
                ip_address=ip_address,
                session_id=session_id
            )

            # Write to append-only audit log (daily rotation)
            audit_file = self._get_audit_file()

            # Serialize to JSON (legible)
            audit_record = {
                "timestamp": entry.timestamp.isoformat(),
                "job_id": entry.job_id,
                "event_type": entry.event_type,
                "user_id": entry.user_id,
                "status": entry.status.value,
                "metadata": entry.metadata,
                # ALCOA+ extended fields
                "user_email": entry.user_email,
                "token_iat": entry.token_iat,
                "ip_address": entry.ip_address,
                "session_id": entry.session_id,
                # ALCOA+ compliance markers
                "alcoa_attributable": f"{entry.user_id} ({entry.user_email})" if entry.user_email else entry.user_id,
                "alcoa_contemporaneous": entry.timestamp.isoformat(),
                "alcoa_original": True  # Append-only, no modifications
            }

            # Append to audit log (atomic operation)
            with audit_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(audit_record) + "\n")

            logger.debug(f"Audit event logged: {event_type} for job {job_id}")

        except Exception as e:
            # CRITICAL: Audit failures must be explicit (NO FALLBACK)
            raise RuntimeError(
                f"CRITICAL: Audit logging failed\n"
                f"Job ID: {job_id}\n"
                f"Event: {event_type}\n"
                f"User: {user_id}\n"
                f"Error: {e}\n"
                "Pharmaceutical compliance requires complete audit trail"
            ) from e

    def _get_audit_file(self) -> Path:
        """
        Get current audit log file (daily rotation).

        Returns:
            Path to today's audit log file

        Format: audit_YYYYMMDD.jsonl
        """
        today = datetime.now(UTC).strftime("%Y%m%d")
        return self.audit_directory / f"audit_{today}.jsonl"

    def query_job_history(self, job_id: str) -> list[dict[str, Any]]:
        """
        Query audit history for a specific job.

        Args:
            job_id: Job identifier to query

        Returns:
            List of audit entries for the job (chronological order)

        Raises:
            RuntimeError: If audit query fails
        """
        try:
            entries: list[dict[str, Any]] = []

            # Search all audit files (could span multiple days)
            for audit_file in sorted(self.audit_directory.glob("audit_*.jsonl")):
                with audit_file.open("r", encoding="utf-8") as f:
                    for line in f:
                        record = json.loads(line.strip())
                        if record["job_id"] == job_id:
                            entries.append(record)

            return entries

        except Exception as e:
            raise RuntimeError(
                f"CRITICAL: Audit query failed\n"
                f"Job ID: {job_id}\n"
                f"Error: {e}"
            ) from e


# Global audit logger instance (initialized in app lifespan)
_audit_logger: AuditLogger | None = None


def get_audit_logger() -> AuditLogger:
    """
    Get global audit logger instance.

    Returns:
        Configured AuditLogger

    Raises:
        RuntimeError: If audit logger not initialized
    """
    if _audit_logger is None:
        raise RuntimeError(
            "CRITICAL: Audit logger not initialized\n"
            "Call initialize_audit_logger() in app lifespan context"
        )
    return _audit_logger


def initialize_audit_logger(audit_directory: str = "logs/audit/jobs") -> None:
    """
    Initialize global audit logger.

    Args:
        audit_directory: Directory for audit log files
    """
    global _audit_logger
    _audit_logger = AuditLogger(audit_directory=audit_directory)

"""Singleton AuditLogger — CloudWatch-backed ALCOA+ event emitter.

Emits structured JSON audit events to AWS CloudWatch Logs via
watchtower (batched, non-blocking). Every event includes SHA-512
hash chain integrity and full ALCOA+ compliance fields.

Usage:
    # At app startup:
    AuditLogger.initialize(config)

    # In any module:
    from src.bi.audit import get_audit_logger
    audit = get_audit_logger()
    await audit.log_data_uploaded(request, session_id=..., ...)
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from src.bi.audit.hash_chain import HashChainManager
from src.bi.audit.models import ALCOAPlusFields, AuditEvent, AuditEventType

logger = logging.getLogger(__name__)


class AuditLogger:
    """Singleton ALCOA+ audit logger backed by CloudWatch Logs.

    Uses watchtower for batched background writes (zero API latency impact).
    Optionally emits to CloudTrail Lake when enabled.
    """

    _instance: AuditLogger | None = None

    def __init__(self, config: Any) -> None:
        self._config = config
        self._hash_chain = HashChainManager()
        self._cw_handler: logging.Handler | None = None
        self._cw_logger: logging.Logger | None = None
        self._cloudtrail_emitter: Any = None

        if config.audit_enabled:
            self._init_cloudwatch(config)
            self._init_cloudtrail_lake(config)
            logger.info(
                "AuditLogger initialized — CloudWatch log group: %s",
                config.audit_log_group,
            )
        else:
            logger.info("AuditLogger disabled (BI_AUDIT_ENABLED=false)")

    def _init_cloudwatch(self, config: Any) -> None:
        """Initialize watchtower CloudWatch handler."""
        import boto3
        import watchtower
        from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError

        session = boto3.Session(region_name=config.audit_aws_region)
        cw_client = session.client("logs")

        try:
            cw_client.describe_log_groups(limit=1)
        except (NoCredentialsError, BotoCoreError, ClientError) as exc:
            raise RuntimeError(
                "BI_AUDIT_ENABLED=true but AWS CloudWatch credentials are invalid or missing. "
                "Set AWS credentials (or task role) before startup."
            ) from exc

        today = datetime.now(UTC).strftime("%Y-%m-%d")
        stream_name = f"{config.audit_log_stream_prefix}-{today}"

        self._cw_handler = watchtower.CloudWatchLogHandler(
            log_group_name=config.audit_log_group,
            log_stream_name=stream_name,
            boto3_client=cw_client,
            use_queues=True,
            send_interval=5,
            create_log_group=True,
            create_log_stream=True,
        )

        self._cw_logger = logging.getLogger("bi.audit.cloudwatch")
        self._cw_logger.setLevel(logging.INFO)
        self._cw_logger.addHandler(self._cw_handler)
        # Prevent propagation to root logger
        self._cw_logger.propagate = False

    def _init_cloudtrail_lake(self, config: Any) -> None:
        """Initialize CloudTrail Lake emitter if enabled."""
        if not config.cloudtrail_lake_enabled:
            return

        from src.bi.audit.cloudtrail_lake import CloudTrailLakeEmitter

        self._cloudtrail_emitter = CloudTrailLakeEmitter(config)

    @classmethod
    def initialize(cls, config: Any) -> AuditLogger:
        """Initialize the singleton. Must be called once at app startup."""
        if cls._instance is not None:
            logger.warning("AuditLogger.initialize() called more than once")
            return cls._instance
        cls._instance = cls(config)
        return cls._instance

    @classmethod
    def get_instance(cls) -> AuditLogger:
        """Return the singleton instance.

        Raises RuntimeError if not initialized.
        """
        if cls._instance is None:
            raise RuntimeError(
                "AuditLogger not initialized. Call AuditLogger.initialize(config) at startup."
            )
        return cls._instance

    # ------------------------------------------------------------------
    # Core emit
    # ------------------------------------------------------------------

    def _build_event(
        self,
        event_type: AuditEventType,
        *,
        request: Any | None = None,
        session_id: str = "",
        payload: dict[str, Any] | None = None,
        langfuse_trace_id: str = "",
        status_code: int = 200,
    ) -> AuditEvent:
        """Build an AuditEvent with ALCOA+ fields and hash chain."""
        now = datetime.now(UTC)
        timestamp = now.isoformat()
        payload = payload or {}

        # Request context from middleware-injected state
        request_id = ""
        user_id = "anonymous"
        user_role = "unknown"
        client_ip = ""
        endpoint = ""
        http_method = ""
        duration_ms = 0.0

        if request is not None:
            state = getattr(request, "state", None)
            if state:
                request_id = getattr(state, "request_id", "")
                user_id = getattr(state, "user_id", "anonymous")
                user_role = getattr(state, "user_role", "unknown")
                client_ip = getattr(state, "client_ip", "")
                start = getattr(state, "audit_start_time", None)
                if start is not None:
                    import time
                    duration_ms = (time.monotonic() - start) * 1000

            endpoint = str(request.url.path) if hasattr(request, "url") else ""
            http_method = getattr(request, "method", "")

        event_id = uuid.uuid4().hex[:24]

        # Compute hash chain
        event_hash, previous_hash = self._hash_chain.compute_hash(
            payload, timestamp
        )

        return AuditEvent(
            event_id=event_id,
            event_type=event_type,
            timestamp=timestamp,
            request_id=request_id,
            session_id=session_id,
            endpoint=endpoint,
            http_method=http_method,
            status_code=status_code,
            duration_ms=round(duration_ms, 1),
            client_ip=client_ip,
            payload=payload,
            alcoa=ALCOAPlusFields(
                user_id=user_id,
                user_role=user_role,
                recorded_at=timestamp,
                event_hash=event_hash,
                previous_hash=previous_hash,
            ),
            langfuse_trace_id=langfuse_trace_id,
        )

    def _emit_sync(self, event: AuditEvent) -> None:
        """Synchronously emit event to CloudWatch (+ CloudTrail Lake)."""
        if not self._config.audit_enabled:
            return

        import json

        msg = json.dumps(event.to_cloudwatch_dict(), default=str)

        if self._cw_logger:
            self._cw_logger.info(msg)

        if self._cloudtrail_emitter:
            self._cloudtrail_emitter.emit(event)

    async def emit(
        self,
        event_type: AuditEventType,
        *,
        request: Any | None = None,
        session_id: str = "",
        payload: dict[str, Any] | None = None,
        langfuse_trace_id: str = "",
        status_code: int = 200,
    ) -> AuditEvent:
        """Build and emit an audit event (async, non-blocking)."""
        event = self._build_event(
            event_type,
            request=request,
            session_id=session_id,
            payload=payload,
            langfuse_trace_id=langfuse_trace_id,
            status_code=status_code,
        )
        await asyncio.to_thread(self._emit_sync, event)
        return event

    # ------------------------------------------------------------------
    # Typed convenience methods
    # ------------------------------------------------------------------

    async def log_data_uploaded(
        self,
        request: Any,
        *,
        session_id: str,
        filename: str,
        total_rows: int,
        total_columns: int,
        file_size_bytes: int,
    ) -> None:
        await self.emit(
            AuditEventType.DATA_UPLOADED,
            request=request,
            session_id=session_id,
            payload={
                "filename": filename,
                "total_rows": total_rows,
                "total_columns": total_columns,
                "file_size_bytes": file_size_bytes,
            },
        )

    async def log_data_page_viewed(
        self,
        request: Any,
        *,
        session_id: str,
        page: int,
        page_size: int,
    ) -> None:
        await self.emit(
            AuditEventType.DATA_PAGE_VIEWED,
            request=request,
            session_id=session_id,
            payload={"page": page, "page_size": page_size},
        )

    async def log_filter_applied(
        self,
        request: Any,
        *,
        session_id: str,
        filters: list[dict[str, Any]],
        filtered_row_count: int,
    ) -> None:
        await self.emit(
            AuditEventType.FILTER_APPLIED,
            request=request,
            session_id=session_id,
            payload={
                "filters": filters,
                "filtered_row_count": filtered_row_count,
            },
        )

    async def log_copilot_chat(
        self,
        request: Any,
        *,
        session_id: str,
        message_length: int,
        response_length: int,
        tool_calls_count: int,
        tool_calls: list[str] | None = None,
        filters_changed: bool = False,
        filtered_row_count: int = 0,
        model: str = "",
        langfuse_trace_id: str = "",
    ) -> None:
        await self.emit(
            AuditEventType.COPILOT_CHAT,
            request=request,
            session_id=session_id,
            langfuse_trace_id=langfuse_trace_id,
            payload={
                "message_length": message_length,
                "response_length": response_length,
                "tool_calls_count": tool_calls_count,
                "tool_calls": tool_calls or [],
                "filters_changed": filters_changed,
                "filtered_row_count": filtered_row_count,
                "model": model,
            },
        )

    async def log_export(
        self,
        request: Any,
        *,
        format: str,
        session_id: str,
        row_count: int,
        active_filters: list[dict[str, Any]] | None = None,
        filename: str = "",
    ) -> None:
        event_type = (
            AuditEventType.EXPORT_EXCEL
            if format == "excel"
            else AuditEventType.EXPORT_PDF
        )
        await self.emit(
            event_type,
            request=request,
            session_id=session_id,
            payload={
                "format": format,
                "row_count": row_count,
                "active_filters": active_filters or [],
                "filename": filename,
            },
        )

    async def log_chart_operation(
        self,
        request: Any,
        *,
        event_type: AuditEventType,
        session_id: str,
        payload: dict[str, Any],
    ) -> None:
        await self.emit(
            event_type,
            request=request,
            session_id=session_id,
            payload=payload,
        )

    async def log_snowflake_operation(
        self,
        request: Any,
        *,
        event_type: AuditEventType,
        session_id: str = "",
        payload: dict[str, Any],
    ) -> None:
        await self.emit(
            event_type,
            request=request,
            session_id=session_id,
            payload=payload,
        )

    async def log_error(
        self,
        request: Any,
        *,
        session_id: str = "",
        error_type: str,
        error_message: str,
        endpoint: str = "",
    ) -> None:
        await self.emit(
            AuditEventType.SYSTEM_ERROR,
            request=request,
            session_id=session_id,
            status_code=500,
            payload={
                "error_type": error_type,
                "error_message": error_message,
                "endpoint": endpoint,
            },
        )

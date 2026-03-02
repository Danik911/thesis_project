"""ALCOA+ compliant audit event models for MES Agentic BI.

Structured Pydantic models ensuring every audit event carries
full ALCOA+ fields for pharmaceutical regulatory compliance.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AuditEventType(str, Enum):
    """All auditable event types in the MES Agentic BI system."""

    # Session lifecycle
    SESSION_CREATED = "session.created"
    SESSION_EXPIRED = "session.expired"
    SESSION_EVICTED = "session.evicted"

    # Data operations
    DATA_UPLOADED = "data.uploaded"
    DATA_PAGE_VIEWED = "data.page_viewed"
    SCHEMA_VIEWED = "schema.viewed"

    # Filter operations
    FILTER_APPLIED = "filter.applied"
    FILTER_REMOVED = "filter.removed"
    FILTER_BULK_SET = "filter.bulk_set"

    # Copilot operations
    COPILOT_CHAT = "copilot.chat"
    COPILOT_TOOL_CALLED = "copilot.tool_called"
    COPILOT_RESPONSE = "copilot.response"

    # Export operations
    EXPORT_EXCEL = "export.excel"
    EXPORT_PDF = "export.pdf"

    # Chart operations
    CHART_RECOMMENDED = "chart.recommended"
    CHART_DATA_REQUESTED = "chart.data_requested"

    # Snowflake operations
    SF_TABLES_LISTED = "snowflake.tables_listed"
    SF_TABLE_LOADED = "snowflake.table_loaded"
    SF_STAGE_FILES_LISTED = "snowflake.stage_files_listed"
    SF_STAGE_FILE_LOADED = "snowflake.stage_file_loaded"

    # Voice operations
    VOICE_SESSION_STARTED = "voice.session_started"
    VOICE_TTS_SYNTHESIZED = "voice.tts_synthesized"

    # System events
    AUTH_USER_IDENTIFIED = "auth.user_identified"
    SYSTEM_ERROR = "system.error"
    SYSTEM_STARTUP = "system.startup"


class ALCOAPlusFields(BaseModel):
    """ALCOA+ compliance fields present on every audit event."""

    # Attributable
    user_id: str = "anonymous"
    user_role: str = "unknown"
    system_id: str = "mes-agentic-bi"
    agent_name: str = ""

    # Contemporaneous
    recorded_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )

    # Original / Accurate
    event_hash: str = ""
    previous_hash: str = "GENESIS"
    hash_algorithm: str = "SHA-512"
    is_original: bool = True
    chain_verified: bool = True

    # Consistent
    validation_status: str = "recorded"
    schema_version: str = "ALCOA_BI_v1"
    procedure_id: str = "BI-AUDIT-001"

    # Enduring
    retention_years: int = 10

    # Available
    retrieval_method: str = "cloudwatch_insights"


class AuditEvent(BaseModel):
    """A single ALCOA+ compliant audit event."""

    event_id: str
    event_type: AuditEventType
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )

    # Request context
    request_id: str = ""
    session_id: str = ""
    endpoint: str = ""
    http_method: str = ""
    status_code: int = 0
    duration_ms: float = 0.0
    client_ip: str = ""

    # Event-specific data
    payload: dict[str, Any] = Field(default_factory=dict)

    # ALCOA+ compliance
    alcoa: ALCOAPlusFields = Field(default_factory=ALCOAPlusFields)

    # Cross-system correlation
    langfuse_trace_id: str = ""

    def to_cloudwatch_dict(self) -> dict[str, Any]:
        """Serialize for CloudWatch JSON log entry."""
        return self.model_dump(mode="json")

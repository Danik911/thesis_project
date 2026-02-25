"""Configuration for MES Agentic BI for PPRS."""

from __future__ import annotations

import os


class BIConfig:
    """Runtime BI configuration loaded from BI_* environment variables."""

    bedrock_region: str = os.getenv("BI_BEDROCK_REGION", "us-east-1")
    copilot_model: str = os.getenv("BI_COPILOT_MODEL", "anthropic/claude-sonnet-4")
    max_upload_size_mb: int = int(os.getenv("BI_MAX_UPLOAD_SIZE_MB", "50"))
    max_rows: int = int(os.getenv("BI_MAX_ROWS", "100000"))
    session_ttl_seconds: int = int(os.getenv("BI_SESSION_TTL_SECONDS", "3600"))
    max_sessions: int = int(os.getenv("BI_MAX_SESSIONS", "20"))


def get_bi_config() -> BIConfig:
    """Return BI configuration instance."""
    return BIConfig()

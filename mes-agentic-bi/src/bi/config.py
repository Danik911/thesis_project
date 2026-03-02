"""Configuration for MES Agentic BI for PPRS."""

from __future__ import annotations

import os


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class BIConfig:
    """Runtime BI configuration loaded from BI_* environment variables."""

    bedrock_region: str = os.getenv("BI_BEDROCK_REGION", "us-east-1")
    copilot_model: str = os.getenv("BI_COPILOT_MODEL", "anthropic/claude-sonnet-4")
    max_upload_size_mb: int = int(os.getenv("BI_MAX_UPLOAD_SIZE_MB", "50"))
    max_rows: int = int(os.getenv("BI_MAX_ROWS", "100000"))
    session_ttl_seconds: int = int(os.getenv("BI_SESSION_TTL_SECONDS", "3600"))
    max_sessions: int = int(os.getenv("BI_MAX_SESSIONS", "20"))

    sf_account: str = os.getenv("BI_SF_ACCOUNT", "")
    sf_user: str = os.getenv("BI_SF_USER", "")
    sf_password: str = os.getenv("BI_SF_PASSWORD", "")
    sf_warehouse: str = os.getenv("BI_SF_WAREHOUSE", "")
    sf_database: str = os.getenv("BI_SF_DATABASE", "")
    sf_schema: str = os.getenv("BI_SF_SCHEMA", "")

    voice_enabled: bool = _as_bool(os.getenv("BI_VOICE_ENABLED"), default=False)
    voice_transcribe_region: str = os.getenv("BI_VOICE_TRANSCRIBE_REGION", bedrock_region)
    voice_language_code: str = os.getenv("BI_VOICE_LANGUAGE_CODE", "en-US")
    voice_sample_rate_hz: int = int(os.getenv("BI_VOICE_SAMPLE_RATE_HZ", "16000"))

    voice_tts_enabled: bool = _as_bool(os.getenv("BI_VOICE_TTS_ENABLED"), default=False)
    voice_polly_region: str = os.getenv("BI_VOICE_POLLY_REGION", bedrock_region)
    voice_polly_voice_id: str = os.getenv("BI_VOICE_POLLY_VOICE_ID", "Joanna")
    voice_polly_output_format: str = os.getenv("BI_VOICE_POLLY_OUTPUT_FORMAT", "mp3")

    # --- Cognito RBAC ---
    auth_enabled: bool = _as_bool(os.getenv("BI_AUTH_ENABLED"), default=False)
    cognito_region: str = os.getenv("BI_COGNITO_REGION", "eu-west-1")
    cognito_user_pool_id: str = os.getenv("BI_COGNITO_USER_POOL_ID", "")
    cognito_client_id: str = os.getenv("BI_COGNITO_CLIENT_ID", "")
    site_column_name: str = os.getenv("BI_SITE_COLUMN_NAME", "Site")
    cors_origins: str = os.getenv("BI_CORS_ORIGINS", "*")

    # --- ALCOA+ Audit Trail ---
    audit_enabled: bool = _as_bool(os.getenv("BI_AUDIT_ENABLED"), default=True)
    audit_log_group: str = os.getenv("BI_AUDIT_LOG_GROUP", "/mes-agentic-bi/audit")
    audit_log_stream_prefix: str = os.getenv("BI_AUDIT_LOG_STREAM_PREFIX", "bi-audit")
    audit_aws_region: str = os.getenv("BI_AUDIT_AWS_REGION", "eu-west-2")

    # --- CloudTrail Lake (deferred, env-gated) ---
    cloudtrail_lake_enabled: bool = _as_bool(
        os.getenv("BI_CLOUDTRAIL_LAKE_ENABLED"),
        default=False,
    )
    cloudtrail_lake_channel_arn: str = os.getenv("BI_CLOUDTRAIL_LAKE_CHANNEL_ARN", "")
    cloudtrail_lake_region: str = os.getenv("BI_CLOUDTRAIL_LAKE_REGION", "eu-west-2")


def get_bi_config() -> BIConfig:
    """Return BI configuration instance."""
    return BIConfig()

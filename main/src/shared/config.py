"""
Configuration management for the pharmaceutical test generation system.

Provides centralized configuration for logging, compliance, and system settings
with environment variable support and validation.
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class LogLevel(str, Enum):
    """Supported logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ComplianceStandard(str, Enum):
    """Supported compliance standards."""
    GAMP5 = "GAMP-5"
    CFR_PART_11 = "21 CFR Part 11"
    ALCOA_PLUS = "ALCOA+"
    ISO_27001 = "ISO 27001"


@dataclass
class LoggingConfig:
    """Configuration for the logging system."""

    # Basic logging settings
    log_level: LogLevel = LogLevel.INFO
    log_directory: str = "logs/events"
    log_file_prefix: str = "pharma_events"

    # Console output settings
    enable_console: bool = True
    console_level: LogLevel = LogLevel.INFO
    console_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # File logging settings
    enable_file_logging: bool = True
    file_level: LogLevel = LogLevel.DEBUG
    file_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"

    # Rotation settings
    enable_rotation: bool = True
    max_file_size_mb: int = 50
    max_files: int = 30
    rotation_interval: str = "daily"  # daily, weekly, monthly

    # Performance settings
    buffer_size: int = 1000
    flush_interval_seconds: int = 5
    enable_async_logging: bool = True

    def __post_init__(self):
        """Validate configuration after initialization."""
        # Ensure log directory exists
        Path(self.log_directory).mkdir(parents=True, exist_ok=True)

        # Validate log levels
        if isinstance(self.log_level, str):
            self.log_level = LogLevel(self.log_level)
        if isinstance(self.console_level, str):
            self.console_level = LogLevel(self.console_level)
        if isinstance(self.file_level, str):
            self.file_level = LogLevel(self.file_level)


@dataclass
class GAMP5ComplianceConfig:
    """Configuration for GAMP-5 compliance features."""

    # Compliance enablement
    enable_compliance_logging: bool = True
    compliance_standards: list[ComplianceStandard] = field(
        default_factory=lambda: [
            ComplianceStandard.GAMP5,
            ComplianceStandard.CFR_PART_11,
            ComplianceStandard.ALCOA_PLUS
        ]
    )

    # Audit trail settings
    enable_audit_trail: bool = True
    audit_log_directory: str = "logs/audit"
    audit_retention_days: int = 2555  # 7 years for pharmaceutical records

    # Data integrity settings
    enable_tamper_evident: bool = True
    enable_digital_signatures: bool = False  # Requires PKI setup
    hash_algorithm: str = "SHA-256"

    # ALCOA+ principles
    ensure_attributable: bool = True
    ensure_legible: bool = True
    ensure_contemporaneous: bool = True
    ensure_original: bool = True
    ensure_accurate: bool = True

    # 21 CFR Part 11 settings
    require_electronic_signatures: bool = False
    enable_access_controls: bool = True
    enable_copy_protection: bool = True

    # Validation settings
    enable_validation_logging: bool = True
    validation_log_directory: str = "logs/validation"
    require_change_documentation: bool = True

    def __post_init__(self):
        """Validate compliance configuration."""
        # Ensure audit directories exist
        Path(self.audit_log_directory).mkdir(parents=True, exist_ok=True)
        Path(self.validation_log_directory).mkdir(parents=True, exist_ok=True)

        # Convert string enums
        if isinstance(self.compliance_standards, list):
            self.compliance_standards = [
                ComplianceStandard(std) if isinstance(std, str) else std
                for std in self.compliance_standards
            ]


@dataclass
class EventStreamConfig:
    """Configuration for event streaming and processing."""

    # Stream processing settings
    enable_event_streaming: bool = True
    stream_buffer_size: int = 1000
    max_stream_events: int = 10000

    # Event filtering
    captured_event_types: list[str] = field(
        default_factory=lambda: [
            "GAMPCategorizationEvent",
            "PlanningEvent",
            "AgentRequestEvent",
            "AgentResultEvent",
            "ValidationEvent",
            "ErrorRecoveryEvent",
            "ConsultationRequiredEvent",
            "ConsultationBypassedEvent",
            "UserDecisionEvent",
            "URSIngestionEvent",
            "DocumentProcessedEvent",
            "WorkflowCompletionEvent",
            "StopEvent",  # To capture final results
            "StartEvent"  # To capture workflow starts
        ]
    )

    # Processing settings
    enable_real_time_processing: bool = True
    batch_processing_size: int = 100
    processing_timeout_seconds: int = 30

    # Storage settings
    persist_events: bool = True
    event_storage_directory: str = "logs/events/streams"
    compress_old_events: bool = True
    compression_age_days: int = 30

    def __post_init__(self):
        """Validate event stream configuration."""
        # Ensure storage directory exists
        Path(self.event_storage_directory).mkdir(parents=True, exist_ok=True)


@dataclass
class HumanConsultationConfig:
    """Configuration for human-in-the-loop consultation system."""

    # Consultation timeouts
    default_timeout_seconds: int = 3600  # 1 hour default
    escalation_timeout_seconds: int = 7200  # 2 hours for escalation
    critical_timeout_seconds: int = 1800  # 30 minutes for critical issues

    # Consultation failure handling (NO fallback values - explicit failures only)
    require_explicit_consultation_resolution: bool = True
    disable_conservative_fallbacks: bool = True
    enable_strict_compliance_mode: bool = True

    # User roles and permissions
    authorized_roles: list[str] = field(
        default_factory=lambda: [
            "validation_engineer",
            "quality_assurance",
            "regulatory_specialist",
            "gamp_specialist",
            "system_engineer",
            "document_analyst",
            "planning_specialist"
        ]
    )

    # Escalation hierarchy
    escalation_hierarchy: dict[str, list[str]] = field(
        default_factory=lambda: {
            "user": ["supervisor", "quality_assurance"],
            "supervisor": ["quality_assurance", "regulatory_specialist"],
            "quality_assurance": ["regulatory_specialist", "gmp_officer"],
            "regulatory_specialist": ["gmp_officer", "system_owner"]
        }
    )

    # Consultation types and their default timeouts
    consultation_timeouts: dict[str, int] = field(
        default_factory=lambda: {
            "categorization_failure": 3600,
            "categorization_error": 1800,
            "planning_error": 3600,
            "planning_incomplete": 2400,
            "planning_result_invalid": 1800,
            "missing_urs_content": 7200,
            "low_confidence_categorization": 2400,
            "validation_failure": 3600,
            "compliance_issue": 1800
        }
    )

    # Notification settings
    enable_notifications: bool = True
    notification_channels: list[str] = field(
        default_factory=lambda: ["email", "dashboard", "audit_log"]
    )

    # Session management
    max_concurrent_sessions: int = 10
    session_cleanup_interval_seconds: int = 300  # 5 minutes
    session_history_retention_days: int = 90

    # Digital signature requirements
    require_digital_signature: bool = False  # Requires PKI setup
    signature_algorithm: str = "RSA-SHA256"

    # Audit trail settings
    detailed_audit_logging: bool = True
    include_decision_context: bool = True
    include_user_metadata: bool = True

    def __post_init__(self):
        """Validate consultation configuration."""
        # Ensure timeout values are positive
        if self.default_timeout_seconds <= 0:
            raise ValueError("Default timeout must be positive")

        if self.escalation_timeout_seconds <= 0:
            raise ValueError("Escalation timeout must be positive")

        if self.critical_timeout_seconds <= 0:
            raise ValueError("Critical timeout must be positive")

        # Validate strict compliance settings
        if not self.require_explicit_consultation_resolution:
            raise ValueError("Explicit consultation resolution is mandatory for pharmaceutical compliance")

        if not self.disable_conservative_fallbacks:
            raise ValueError("Conservative fallbacks must be disabled for regulatory compliance")

        # Validate roles
        if not self.authorized_roles:
            raise ValueError("At least one authorized role must be specified")


@dataclass
class ValidationModeConfig:
    """Configuration for validation mode testing capabilities."""

    # Validation mode settings - PRODUCTION SAFE defaults
    validation_mode: bool = field(
        default_factory=lambda: os.getenv("VALIDATION_MODE", "false").lower() == "true"
    )

    # Consultation bypass threshold (confidence score below which consultation would normally be required)
    bypass_consultation_threshold: float = field(
        default_factory=lambda: float(os.getenv("BYPASS_CONSULTATION_THRESHOLD", "0.7"))
    )

    # Category bypass settings (which GAMP categories can bypass consultation in validation mode)
    bypass_allowed_categories: list[int] = field(
        default_factory=lambda: [4, 5]  # Category 4 and 5 can bypass in validation mode
    )

    # Audit trail settings for bypassed consultations
    log_bypassed_consultations: bool = True
    bypass_audit_directory: str = "logs/validation/bypassed_consultations"

    # Quality metrics tracking for bypass impact
    track_bypass_quality_impact: bool = True
    bypass_metrics_file: str = "logs/validation/bypass_quality_metrics.json"

    # Safety settings
    require_explicit_validation_mode: bool = True  # Must be explicitly enabled
    max_bypass_rate_threshold: float = 0.8  # Alert if bypass rate exceeds 80%

    def __post_init__(self):
        """Validate validation mode configuration and ensure production safety."""
        # Ensure bypass threshold is valid
        if not 0.0 <= self.bypass_consultation_threshold <= 1.0:
            raise ValueError("Bypass consultation threshold must be between 0.0 and 1.0")

        # Ensure bypass directories exist if validation mode is enabled
        if self.validation_mode:
            Path(self.bypass_audit_directory).mkdir(parents=True, exist_ok=True)
            Path(Path(self.bypass_metrics_file).parent).mkdir(parents=True, exist_ok=True)

        # Validate GAMP categories
        valid_categories = [1, 3, 4, 5]
        for category in self.bypass_allowed_categories:
            if category not in valid_categories:
                raise ValueError(f"Invalid GAMP category for bypass: {category}. Must be one of {valid_categories}")

        # Production safety check
        if self.validation_mode and self.require_explicit_validation_mode:
            env_validation = os.getenv("VALIDATION_MODE_EXPLICIT", "false").lower() == "true"
            if not env_validation:
                # Allow validation mode but log warning for audit compliance
                import logging
                logger = logging.getLogger("ValidationModeConfig")
                logger.warning(
                    "VALIDATION MODE ACTIVE: This bypasses consultation requirements for testing. "
                    "Ensure this is intentional and not in production environment. "
                    "Set VALIDATION_MODE_EXPLICIT=true to suppress this warning."
                )


@dataclass
class PhoenixConfig:
    """Configuration for Arize Phoenix observability integration."""

    # Phoenix settings
    enable_phoenix: bool = field(
        default_factory=lambda: os.getenv("PHOENIX_ENABLE_TRACING", "true").lower() == "true"
    )
    enable_tracing: bool = field(
        default_factory=lambda: os.getenv("PHOENIX_ENABLE_TRACING", "true").lower() == "true"
    )
    phoenix_host: str = field(default_factory=lambda: os.getenv("PHOENIX_HOST", "localhost"))
    phoenix_port: int = field(default_factory=lambda: int(os.getenv("PHOENIX_PORT", "6006")))
    phoenix_api_key: str | None = field(default_factory=lambda: os.getenv("PHOENIX_API_KEY"))

    # Project settings
    project_name: str = field(
        default_factory=lambda: os.getenv("PHOENIX_PROJECT_NAME", "test_generation_thesis")
    )
    experiment_name: str = field(
        default_factory=lambda: os.getenv("PHOENIX_EXPERIMENT_NAME", "multi_agent_workflow")
    )

    # OTLP settings
    otlp_endpoint: str | None = field(
        default_factory=lambda: os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    )
    service_name: str = field(
        default_factory=lambda: os.getenv("OTEL_SERVICE_NAME", "test_generator")
    )

    # Performance settings
    enable_batch_export: bool = True
    batch_export_delay_ms: int = 5000

    # UI settings
    enable_local_ui: bool = field(
        default_factory=lambda: os.getenv("PHOENIX_ENABLE_LOCAL_UI", "true").lower() == "true"
    )

    # Environment
    deployment_environment: str = field(
        default_factory=lambda: os.getenv("DEPLOYMENT_ENVIRONMENT", "development")
    )

    def __post_init__(self):
        """Set default OTLP endpoint if not provided."""
        if not self.otlp_endpoint and self.enable_phoenix:
            self.otlp_endpoint = f"http://{self.phoenix_host}:{self.phoenix_port}/v1/traces"


@dataclass
class Config:
    """Main configuration class combining all system settings."""

    # Sub-configurations
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    gamp5_compliance: GAMP5ComplianceConfig = field(default_factory=GAMP5ComplianceConfig)
    event_streaming: EventStreamConfig = field(default_factory=EventStreamConfig)
    human_consultation: HumanConsultationConfig = field(default_factory=HumanConsultationConfig)
    validation_mode: ValidationModeConfig = field(default_factory=ValidationModeConfig)
    phoenix: PhoenixConfig = field(default_factory=PhoenixConfig)

    # Environment settings
    environment: str = "development"  # development, testing, production
    debug_mode: bool = False

    # System settings
    max_concurrent_workflows: int = 10
    workflow_timeout_seconds: int = 600
    enable_performance_monitoring: bool = True

    # Security settings
    enable_encryption: bool = False  # For sensitive data
    encryption_key_path: str | None = None

    @classmethod
    def from_environment(cls) -> "Config":
        """Create configuration from environment variables."""
        config = cls()

        # Override with environment variables
        if os.getenv("LOG_LEVEL"):
            config.logging.log_level = LogLevel(os.getenv("LOG_LEVEL"))

        if os.getenv("LOG_DIRECTORY"):
            config.logging.log_directory = os.getenv("LOG_DIRECTORY")

        if os.getenv("ENABLE_GAMP5_COMPLIANCE"):
            config.gamp5_compliance.enable_compliance_logging = (
                os.getenv("ENABLE_GAMP5_COMPLIANCE").lower() == "true"
            )

        if os.getenv("ENVIRONMENT"):
            config.environment = os.getenv("ENVIRONMENT")

        if os.getenv("DEBUG"):
            config.debug_mode = os.getenv("DEBUG").lower() == "true"
            if config.debug_mode:
                config.logging.log_level = LogLevel.DEBUG
                config.logging.console_level = LogLevel.DEBUG

        return config

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "logging": {
                "log_level": self.logging.log_level.value,
                "log_directory": self.logging.log_directory,
                "enable_console": self.logging.enable_console,
                "enable_rotation": self.logging.enable_rotation,
                "max_file_size_mb": self.logging.max_file_size_mb,
                "max_files": self.logging.max_files
            },
            "gamp5_compliance": {
                "enable_compliance_logging": self.gamp5_compliance.enable_compliance_logging,
                "compliance_standards": [std.value for std in self.gamp5_compliance.compliance_standards],
                "enable_audit_trail": self.gamp5_compliance.enable_audit_trail,
                "audit_retention_days": self.gamp5_compliance.audit_retention_days,
                "enable_tamper_evident": self.gamp5_compliance.enable_tamper_evident
            },
            "event_streaming": {
                "enable_event_streaming": self.event_streaming.enable_event_streaming,
                "captured_event_types": self.event_streaming.captured_event_types,
                "persist_events": self.event_streaming.persist_events,
                "stream_buffer_size": self.event_streaming.stream_buffer_size
            },
            "human_consultation": {
                "default_timeout_seconds": self.human_consultation.default_timeout_seconds,
                "require_explicit_consultation_resolution": self.human_consultation.require_explicit_consultation_resolution,
                "disable_conservative_fallbacks": self.human_consultation.disable_conservative_fallbacks,
                "authorized_roles": self.human_consultation.authorized_roles,
                "enable_notifications": self.human_consultation.enable_notifications,
                "require_digital_signature": self.human_consultation.require_digital_signature,
                "detailed_audit_logging": self.human_consultation.detailed_audit_logging
            },
            "validation_mode": {
                "validation_mode": self.validation_mode.validation_mode,
                "bypass_consultation_threshold": self.validation_mode.bypass_consultation_threshold,
                "bypass_allowed_categories": self.validation_mode.bypass_allowed_categories,
                "log_bypassed_consultations": self.validation_mode.log_bypassed_consultations,
                "track_bypass_quality_impact": self.validation_mode.track_bypass_quality_impact,
                "require_explicit_validation_mode": self.validation_mode.require_explicit_validation_mode,
                "max_bypass_rate_threshold": self.validation_mode.max_bypass_rate_threshold
            },
            "phoenix": {
                "enable_phoenix": self.phoenix.enable_phoenix,
                "phoenix_host": self.phoenix.phoenix_host,
                "phoenix_port": self.phoenix.phoenix_port,
                "project_name": self.phoenix.project_name,
                "experiment_name": self.phoenix.experiment_name,
                "otlp_endpoint": self.phoenix.otlp_endpoint,
                "service_name": self.phoenix.service_name
            },
            "environment": self.environment,
            "debug_mode": self.debug_mode
        }

    def validate(self) -> list[str]:
        """Validate configuration and return any issues."""
        issues = []

        # Check log directory permissions
        try:
            Path(self.logging.log_directory).mkdir(parents=True, exist_ok=True)
        except PermissionError:
            issues.append(f"Cannot create log directory: {self.logging.log_directory}")

        # Check audit directory permissions if compliance enabled
        if self.gamp5_compliance.enable_compliance_logging:
            try:
                Path(self.gamp5_compliance.audit_log_directory).mkdir(parents=True, exist_ok=True)
            except PermissionError:
                issues.append(f"Cannot create audit directory: {self.gamp5_compliance.audit_log_directory}")

        # Validate retention settings
        if self.gamp5_compliance.audit_retention_days < 1:
            issues.append("Audit retention days must be positive")

        # Check file size limits
        if self.logging.max_file_size_mb < 1:
            issues.append("Max file size must be at least 1MB")

        return issues


# Global configuration instance
_config_instance: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config.from_environment()
    return _config_instance


def set_config(config: Config) -> None:
    """Set the global configuration instance."""
    global _config_instance
    _config_instance = config


def reset_config() -> None:
    """Reset configuration to default values."""
    global _config_instance
    _config_instance = None

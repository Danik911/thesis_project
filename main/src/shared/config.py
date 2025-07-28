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
            "UserDecisionEvent"
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

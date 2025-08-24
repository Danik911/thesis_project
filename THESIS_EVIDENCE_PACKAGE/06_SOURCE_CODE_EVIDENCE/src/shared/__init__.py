"""Shared utilities and configuration."""

from .config import Config, GAMP5ComplianceConfig, LoggingConfig, get_config, set_config
from .event_logging import (
    EventStreamHandler,
    GAMP5ComplianceLogger,
    StructuredEventLogger,
    setup_event_logging,
)
from .event_logging_integration import run_workflow_with_event_logging
from .utils import chunk_large_text, count_tokens, setup_logging, should_chunk_text

__all__ = [
    # Configuration
    "Config",
    "get_config",
    "set_config",
    "LoggingConfig",
    "GAMP5ComplianceConfig",

    # Utilities
    "chunk_large_text",
    "setup_logging",
    "should_chunk_text",
    "count_tokens",

    # Event Logging
    "EventStreamHandler",
    "StructuredEventLogger",
    "GAMP5ComplianceLogger",
    "setup_event_logging",
    "run_workflow_with_event_logging"
]

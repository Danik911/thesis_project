"""
Monitoring and observability components for pharmaceutical test generation.

This module provides integration with Arize Phoenix for production-grade
observability of multi-agent LLM workflows.
"""

from .agent_instrumentation import (
    InstrumentedAgent,
    trace_agent_method,
    trace_workflow_step,
)
from .pharmaceutical_event_handler import PharmaceuticalEventHandler
from .phoenix_config import PhoenixConfig, PhoenixManager, setup_phoenix
from .phoenix_event_handler import PhoenixEventStreamHandler

__all__ = [
    "InstrumentedAgent",
    "PharmaceuticalEventHandler",
    "PhoenixConfig",
    "PhoenixEventStreamHandler",
    "PhoenixManager",
    "setup_phoenix",
    "trace_agent_method",
    "trace_workflow_step"
]

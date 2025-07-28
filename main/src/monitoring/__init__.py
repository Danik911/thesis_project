"""
Monitoring and observability components for pharmaceutical test generation.

This module provides integration with Arize Phoenix for production-grade
observability of multi-agent LLM workflows.
"""

from .phoenix_config import PhoenixConfig, PhoenixManager, setup_phoenix
from .phoenix_event_handler import PhoenixEventStreamHandler
from .pharmaceutical_event_handler import PharmaceuticalEventHandler
from .agent_instrumentation import (
    trace_agent_method,
    trace_workflow_step,
    InstrumentedAgent
)

__all__ = [
    "PhoenixConfig", 
    "PhoenixManager", 
    "setup_phoenix", 
    "PhoenixEventStreamHandler",
    "PharmaceuticalEventHandler",
    "trace_agent_method",
    "trace_workflow_step",
    "InstrumentedAgent"
]
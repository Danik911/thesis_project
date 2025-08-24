"""
GAMP-5 Categorization Agent Module

This module provides the GAMP-5 categorization agent following LlamaIndex patterns.
Exports the agent factory function, helper utilities, and workflow integration.

Note: The proper LlamaIndex workflow implementation is in 
src/core/categorization_workflow.py (GAMPCategorizationWorkflow class).
"""

from .agent import (
    categorize_with_structured_output,
    confidence_tool,
    create_categorization_event,
    create_gamp_categorization_agent,
    gamp_analysis_tool,
)
from .workflow_integration import CategorizationWorkflowStep

__all__ = [
    "CategorizationWorkflowStep",
    "categorize_with_structured_output",
    "confidence_tool",
    "create_categorization_event",
    "create_gamp_categorization_agent",
    "gamp_analysis_tool"
]

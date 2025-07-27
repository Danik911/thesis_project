"""
GAMP-5 Categorization Agent Module

This module provides the GAMP-5 categorization agent following LlamaIndex patterns.
Exports the agent factory function, helper utilities, and workflow integration.

Note: The proper LlamaIndex workflow implementation is in 
src/core/categorization_workflow.py (GAMPCategorizationWorkflow class).
"""

from .agent import (
    create_gamp_categorization_agent,
    create_categorization_event,
    gamp_analysis_tool,
    confidence_tool,
    categorize_with_structured_output
)

from .workflow_integration import (
    CategorizationWorkflowStep
)

__all__ = [
    "create_gamp_categorization_agent",
    "create_categorization_event", 
    "gamp_analysis_tool",
    "confidence_tool",
    "categorize_with_structured_output",
    "CategorizationWorkflowStep"
]
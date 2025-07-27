"""
Workflow integration module for GAMP-5 categorization agent.

This module provides a bridge between the categorization agent and the
LlamaIndex workflow system. The actual workflow implementation is in
src/core/categorization_workflow.py following proper LlamaIndex patterns.

This module maintains the CategorizationWorkflowStep class for backward
compatibility and provides utility functions for workflow integration.
"""

from typing import Dict, Any, Optional
from datetime import datetime, UTC

from src.core.events import GAMPCategory
from src.agents.categorization.agent import (
    create_gamp_categorization_agent,
    categorize_with_structured_output
)
from src.agents.categorization.error_handler import CategorizationErrorHandler


class CategorizationWorkflowStep:
    """
    Legacy workflow step wrapper for GAMP-5 categorization agent.
    
    This class is maintained for backward compatibility. New implementations
    should use GAMPCategorizationWorkflow from src/core/categorization_workflow.py
    which follows proper LlamaIndex workflow patterns.
    """
    
    def __init__(
        self,
        enable_error_handling: bool = True,
        confidence_threshold: float = 0.60,
        verbose: bool = False,
        retry_attempts: int = 2
    ):
        """
        Initialize the categorization workflow step.
        
        Args:
            enable_error_handling: Enable comprehensive error handling
            confidence_threshold: Minimum confidence before triggering review
            verbose: Enable detailed logging
            retry_attempts: Number of retry attempts on failure
        """
        self.enable_error_handling = enable_error_handling
        self.confidence_threshold = confidence_threshold
        self.verbose = verbose
        self.retry_attempts = retry_attempts
        self.agent = None
        self.error_handler = None
        
    def initialize_agent(self):
        """Initialize the categorization agent with configuration."""
        if not self.agent:
            self.agent = create_gamp_categorization_agent(
                enable_error_handling=self.enable_error_handling,
                confidence_threshold=self.confidence_threshold,
                verbose=self.verbose
            )
            # Access error handler if available
            if hasattr(self.agent, 'error_handler'):
                self.error_handler = self.agent.error_handler
        return self.agent
    
    def get_output_schema(self) -> Dict[str, Any]:
        """
        Get the output schema for downstream workflow steps.
        
        Returns:
            Dictionary describing the output schema
        """
        return {
            "event_type": "GAMPCategorizationEvent",
            "fields": {
                "gamp_category": {
                    "type": "enum",
                    "values": [1, 3, 4, 5],
                    "description": "GAMP-5 software category"
                },
                "confidence_score": {
                    "type": "float",
                    "range": [0.0, 1.0],
                    "description": "Confidence in categorization (0-1)"
                },
                "justification": {
                    "type": "string",
                    "description": "Detailed justification for categorization"
                },
                "risk_assessment": {
                    "type": "object",
                    "fields": {
                        "software_type": "string",
                        "risk_level": "enum[low, medium, high]",
                        "validation_rigor": "enum[minimal, standard, enhanced, full]",
                        "confidence_factors": "object"
                    }
                },
                "review_required": {
                    "type": "boolean",
                    "description": "Whether human review is required"
                },
                "event_id": {
                    "type": "uuid",
                    "description": "Unique event identifier"
                },
                "timestamp": {
                    "type": "datetime",
                    "description": "Event timestamp (UTC)"
                },
                "categorized_by": {
                    "type": "string",
                    "description": "Agent/system that performed categorization"
                }
            },
            "compliance": {
                "alcoa_plus": True,
                "cfr_part_11": True,
                "gamp_5": True
            }
        }
    
    def _determine_risk_level(self, category: GAMPCategory) -> str:
        """Determine risk level based on GAMP category."""
        risk_mapping = {
            GAMPCategory.CATEGORY_1: "low",
            GAMPCategory.CATEGORY_3: "low", 
            GAMPCategory.CATEGORY_4: "medium",
            GAMPCategory.CATEGORY_5: "high"
        }
        return risk_mapping.get(category, "high")
    
    def _determine_validation_rigor(self, category: GAMPCategory) -> str:
        """Determine validation rigor based on GAMP category."""
        rigor_mapping = {
            GAMPCategory.CATEGORY_1: "minimal",
            GAMPCategory.CATEGORY_3: "standard",
            GAMPCategory.CATEGORY_4: "enhanced", 
            GAMPCategory.CATEGORY_5: "full"
        }
        return rigor_mapping.get(category, "full")
    
    def get_error_statistics(self) -> Optional[Dict[str, Any]]:
        """Get error statistics if error handling is enabled."""
        if self.error_handler:
            return self.error_handler.get_error_statistics()
        return None
    
    def get_audit_log(self) -> Optional[list]:
        """Get audit log if error handling is enabled."""
        if self.error_handler:
            return self.error_handler.get_audit_log()
        return None


# Note: The categorization_workflow_step function has been removed.
# Use GAMPCategorizationWorkflow from src/core/categorization_workflow.py instead.

# Export the legacy components for backward compatibility
__all__ = [
    "CategorizationWorkflowStep"
]
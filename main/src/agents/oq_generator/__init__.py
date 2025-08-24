"""
OQ Test Generation Agent Module.

This module provides comprehensive Operational Qualification (OQ) test generation
capabilities for pharmaceutical computerized systems validation following GAMP-5
guidelines and regulatory compliance requirements.

Key Components:
- Pydantic models for structured OQ test data
- Event-driven workflow integration
- LLMTextCompletionProgram-based test generation
- GAMP category-specific templates and validation
- Pharmaceutical compliance validation

Usage:
    from src.agents.oq_generator import OQTestGenerationWorkflow, OQTestGenerator
    
    # Initialize workflow
    workflow = OQTestGenerationWorkflow(verbose=True)
    
    # Generate tests via workflow
    result = await workflow.run(oq_generation_event)
"""

from .events import (
    OQTestGenerationEvent,
    OQTestSuiteEvent,
    OQValidationEvent,
    OQValidationResultEvent,
)
from .generator import OQTestGenerationError, OQTestGenerator
from .generator_v2 import OQTestGeneratorV2, create_oq_test_generator_v2
from .models import OQGenerationConfig, OQTestCase, OQTestSuite, TestStep
from .templates import (
    ComplianceRequirements,
    GAMPCategoryConfig,
    OQPromptTemplates,
    TestCategoryTemplates,
)
from .workflow import OQGenerationWorkflow
# For backwards compatibility, create an alias
OQTestGenerationWorkflow = OQGenerationWorkflow

# Module metadata
__version__ = "1.0.0"
__author__ = "Pharmaceutical Test Generation System"
__description__ = "OQ test generation agent for GAMP-5 compliant pharmaceutical validation"

# Export public API
__all__ = [
    # Core workflow
    "OQTestGenerationWorkflow",

    # Generator engine
    "OQTestGenerator",
    "OQTestGeneratorV2",
    "create_oq_test_generator_v2",
    "OQTestGenerationError",

    # Data models
    "OQTestCase",
    "OQTestSuite",
    "TestStep",
    "OQGenerationConfig",

    # Events
    "OQTestGenerationEvent",
    "OQTestSuiteEvent",
    "OQValidationEvent",
    "OQValidationResultEvent",

    # Templates and configuration
    "GAMPCategoryConfig",
    "OQPromptTemplates",
    "TestCategoryTemplates",
    "ComplianceRequirements"
]

# Convenience functions
def create_oq_workflow(**kwargs) -> OQTestGenerationWorkflow:
    """
    Create OQ test generation workflow with default configuration.
    
    Args:
        **kwargs: Configuration parameters for workflow
        
    Returns:
        Configured OQTestGenerationWorkflow instance
    """
    return OQTestGenerationWorkflow(**kwargs)


def get_gamp_category_info(gamp_category) -> dict:
    """
    Get information about a specific GAMP category.
    
    Args:
        gamp_category: GAMP category (1, 3, 4, or 5)
        
    Returns:
        Dictionary with category configuration
    """
    from src.core.events import GAMPCategory

    if isinstance(gamp_category, int):
        if gamp_category == 1:
            gamp_category = GAMPCategory.CATEGORY_1
        elif gamp_category == 3:
            gamp_category = GAMPCategory.CATEGORY_3
        elif gamp_category == 4:
            gamp_category = GAMPCategory.CATEGORY_4
        elif gamp_category == 5:
            gamp_category = GAMPCategory.CATEGORY_5
        else:
            raise ValueError(f"Unsupported GAMP category: {gamp_category}")

    return GAMPCategoryConfig.get_category_config(gamp_category)


def validate_test_count_for_category(gamp_category, test_count: int) -> bool:
    """
    Validate if test count is appropriate for GAMP category.
    
    Args:
        gamp_category: GAMP category
        test_count: Proposed test count
        
    Returns:
        True if test count is valid for category
    """
    try:
        min_tests, max_tests = GAMPCategoryConfig.get_test_count_range(gamp_category)
        return min_tests <= test_count <= max_tests
    except (ValueError, KeyError):
        return False

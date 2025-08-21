"""
Cross-Validation Testing Framework for Pharmaceutical Test Generation System

This module provides a comprehensive cross-validation framework for evaluating
the performance and reliability of the pharmaceutical test generation system
across different URS documents and GAMP-5 categories.

Key Features:
- 5-fold cross-validation over URS corpus
- Integration with UnifiedTestGenerationWorkflow
- Phoenix observability monitoring
- GAMP-5 compliance with audit trails
- Metrics collection and reporting
- Error handling with explicit failures (no fallbacks)

Components:
- FoldManager: Handles fold assignment and document loading
- CrossValidationWorkflow: Main orchestration workflow
- ExecutionHarness: Entry point with error handling and monitoring
- MetricsCollector: Performance and cost tracking
"""

from .cross_validation_workflow import CrossValidationWorkflow
from .execution_harness import ExecutionHarness
from .fold_manager import FoldManager
from .metrics_collector import MetricsCollector

__all__ = [
    "CrossValidationWorkflow",
    "ExecutionHarness",
    "FoldManager",
    "MetricsCollector",
]

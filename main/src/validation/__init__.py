#!/usr/bin/env python3
"""
Validation Framework Package

This package provides comprehensive validation execution capabilities for
pharmaceutical test generation systems with GAMP-5 compliance.

Key Components:
- ValidationExecutionFramework: Main orchestrator for validation execution
- ParallelDocumentProcessor: Parallel processing with 3 concurrent documents
- ValidationMetricsCollector: Comprehensive metrics collection and analysis
- ProgressTracker: Real-time progress monitoring with ETA calculations
- ErrorRecoveryManager: Robust error recovery with checkpointing
- ResultsAggregator: Statistical analysis and reporting
- ValidationExecutionConfig: Comprehensive configuration management

This framework ensures NO FALLBACK LOGIC and explicit error handling
throughout all validation processes.
"""

__version__ = "1.0.0"
__author__ = "Validation Framework Team"
__description__ = "Comprehensive validation execution framework for pharmaceutical test generation"

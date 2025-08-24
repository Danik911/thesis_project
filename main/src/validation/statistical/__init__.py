#!/usr/bin/env python3
"""
Statistical Analysis Package

This package provides comprehensive statistical analysis for thesis validation,
including ANOVA, post-hoc tests, hypothesis testing, and significance analysis
for pharmaceutical validation frameworks.
"""

from .pipeline import ValidationStatisticalPipeline
from .report_generator import StatisticalReportGenerator
from .thesis_validator import ThesisClaimsValidator

__all__ = [
    "StatisticalReportGenerator",
    "ThesisClaimsValidator",
    "ValidationStatisticalPipeline"
]

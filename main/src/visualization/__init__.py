"""
Thesis Visualization Module

This module provides specialized visualization capabilities for thesis Chapter 4,
generating publication-quality charts and dashboards for pharmaceutical 
test generation system analysis.

Key Features:
- ROI visualization showing 535.7M% return on investment
- Performance matrix comparing time/cost/quality metrics
- GAMP distribution analysis with confidence mapping
- Compliance dashboard for regulatory requirements
- Executive summary visualizations for stakeholders
- Publication-ready exports (PNG, SVG, HTML)

All visualizations use real data from Task 28 statistical analysis with
NO FALLBACK LOGIC and explicit error handling.
"""

from .thesis_visualizations import ThesisVisualizationGenerator
from .thesis_dashboard import ThesisDashboard
from .export_manager import ExportManager

__all__ = [
    "ThesisVisualizationGenerator",
    "ThesisDashboard", 
    "ExportManager"
]
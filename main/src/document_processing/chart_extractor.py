"""
Chart Extractor for URS Documents

This module handles extraction and processing of charts, diagrams,
and other visual elements from pharmaceutical URS documents.
"""

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class ChartExtractor:
    """
    Extracts and processes charts/diagrams from URS documents.
    
    This class handles visual elements that are critical for
    understanding technical specifications and system architecture.
    """

    def __init__(self):
        """Initialize chart extractor."""
        self.logger = logging.getLogger(__name__)

        # Chart type classifications
        self.chart_types = {
            "flowchart": ["flow", "process", "workflow", "sequence"],
            "architecture": ["architecture", "system", "component", "deployment"],
            "data_model": ["data", "entity", "relationship", "erd", "schema"],
            "interface": ["interface", "api", "integration", "connection"],
            "state": ["state", "transition", "lifecycle", "status"],
            "hierarchy": ["hierarchy", "organization", "structure", "tree"],
            "network": ["network", "topology", "infrastructure"],
            "uml": ["uml", "class", "sequence", "activity", "use case"]
        }

    def process_charts(
        self,
        charts: list[dict[str, Any]],
        source_file: Path
    ) -> list[dict[str, Any]]:
        """
        Process extracted charts and add metadata.
        
        Args:
            charts: List of charts from LlamaParse
            source_file: Source document path
            
        Returns:
            Enhanced chart data with classification and metadata
        """
        processed_charts = []

        for idx, chart in enumerate(charts):
            processed_chart = self._process_single_chart(
                chart, idx, source_file
            )
            processed_charts.append(processed_chart)

        # Analyze chart relationships
        self._analyze_chart_relationships(processed_charts)

        return processed_charts

    def _process_single_chart(
        self,
        chart: dict[str, Any],
        index: int,
        source_file: Path
    ) -> dict[str, Any]:
        """Process a single chart."""
        # Extract base information
        processed = {
            "id": f"chart_{index + 1}",
            "page": chart.get("page", 0),
            "index": chart.get("index", index),
            "type": self._classify_chart_type(chart),
            "caption": chart.get("caption", ""),
            "path": chart.get("path"),
            "source_document": source_file.name,
            "metadata": {
                "extracted_at": datetime.now(UTC).isoformat(),
                "quality_score": self._assess_chart_quality(chart),
                "gamp_relevance": self._assess_gamp_relevance(chart)
            }
        }

        # Extract technical details from caption/context
        if processed["caption"]:
            processed["technical_details"] = self._extract_technical_details(
                processed["caption"]
            )

        return processed

    def _classify_chart_type(self, chart: dict[str, Any]) -> str:
        """Classify the type of chart based on caption and content."""
        caption_lower = (chart.get("caption", "") or "").lower()

        # Check against known chart types
        for chart_type, keywords in self.chart_types.items():
            for keyword in keywords:
                if keyword in caption_lower:
                    return chart_type

        # Default classification
        if "figure" in caption_lower:
            return "diagram"
        if "table" in caption_lower:
            return "table"
        return "unknown"

    def _assess_chart_quality(self, chart: dict[str, Any]) -> float:
        """Assess the quality/completeness of chart data."""
        score = 0.0

        # Has caption
        if chart.get("caption"):
            score += 0.4

        # Has file path (actual image)
        if chart.get("path"):
            score += 0.3

        # Has page reference
        if chart.get("page", 0) > 0:
            score += 0.2

        # Caption is descriptive
        caption = chart.get("caption", "")
        if len(caption) > 20:
            score += 0.1

        return min(score, 1.0)

    def _assess_gamp_relevance(self, chart: dict[str, Any]) -> str:
        """Assess relevance of chart for GAMP-5 categorization."""
        caption_lower = (chart.get("caption", "") or "").lower()

        # High relevance indicators
        high_relevance_keywords = [
            "system architecture", "software architecture",
            "data flow", "integration", "interface",
            "configuration", "deployment", "infrastructure"
        ]

        # Medium relevance indicators
        medium_relevance_keywords = [
            "process", "workflow", "validation",
            "test", "requirement", "specification"
        ]

        for keyword in high_relevance_keywords:
            if keyword in caption_lower:
                return "high"

        for keyword in medium_relevance_keywords:
            if keyword in caption_lower:
                return "medium"

        return "low"

    def _extract_technical_details(self, caption: str) -> dict[str, Any]:
        """Extract technical details from chart caption."""
        details = {
            "components": [],
            "technologies": [],
            "interfaces": []
        }

        # Common technical terms to look for
        tech_terms = {
            "components": ["server", "client", "database", "api", "service",
                          "module", "component", "system", "application"],
            "technologies": ["java", "python", ".net", "oracle", "sql",
                           "rest", "soap", "http", "tcp/ip", "xml"],
            "interfaces": ["interface", "api", "endpoint", "protocol",
                         "connection", "integration", "communication"]
        }

        caption_lower = caption.lower()

        # Extract mentioned components/technologies
        for category, terms in tech_terms.items():
            for term in terms:
                if term in caption_lower:
                    details[category].append(term)

        return details

    def _analyze_chart_relationships(
        self,
        charts: list[dict[str, Any]]
    ) -> None:
        """Analyze relationships between charts."""
        # Group charts by type
        charts_by_type = {}
        for chart in charts:
            chart_type = chart["type"]
            if chart_type not in charts_by_type:
                charts_by_type[chart_type] = []
            charts_by_type[chart_type].append(chart)

        # Add grouping information
        for chart in charts:
            chart["metadata"]["chart_groups"] = {
                "total_charts": len(charts),
                "same_type_count": len(charts_by_type.get(chart["type"], [])),
                "chart_types_present": list(charts_by_type.keys())
            }

    def extract_chart_text(
        self,
        chart: dict[str, Any],
        ocr_enabled: bool = False
    ) -> str | None:
        """
        Extract text content from chart if possible.
        
        Args:
            chart: Chart data
            ocr_enabled: Whether to attempt OCR (not implemented)
            
        Returns:
            Extracted text or None
        """
        # For now, return caption as text
        # In future, could integrate OCR for actual image text extraction
        return chart.get("caption", "")

    def create_chart_summary(
        self,
        charts: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Create a summary of all charts in the document."""
        summary = {
            "total_charts": len(charts),
            "chart_types": {},
            "high_relevance_charts": [],
            "pages_with_charts": set(),
            "technical_indicators": {
                "has_architecture_diagrams": False,
                "has_data_models": False,
                "has_integration_diagrams": False,
                "has_process_flows": False
            }
        }

        # Analyze charts
        for chart in charts:
            # Count by type
            chart_type = chart["type"]
            summary["chart_types"][chart_type] = summary["chart_types"].get(chart_type, 0) + 1

            # Track high relevance
            if chart["metadata"]["gamp_relevance"] == "high":
                summary["high_relevance_charts"].append(chart["id"])

            # Track pages
            summary["pages_with_charts"].add(chart["page"])

            # Update technical indicators
            if chart_type == "architecture":
                summary["technical_indicators"]["has_architecture_diagrams"] = True
            elif chart_type == "data_model":
                summary["technical_indicators"]["has_data_models"] = True
            elif chart_type == "interface":
                summary["technical_indicators"]["has_integration_diagrams"] = True
            elif chart_type == "flowchart":
                summary["technical_indicators"]["has_process_flows"] = True

        # Convert set to list for JSON serialization
        summary["pages_with_charts"] = sorted(list(summary["pages_with_charts"]))

        return summary

    def filter_charts_by_relevance(
        self,
        charts: list[dict[str, Any]],
        min_relevance: str = "medium"
    ) -> list[dict[str, Any]]:
        """Filter charts by GAMP relevance level."""
        relevance_levels = {"low": 0, "medium": 1, "high": 2}
        min_level = relevance_levels.get(min_relevance, 1)

        filtered = []
        for chart in charts:
            chart_level = relevance_levels.get(
                chart["metadata"]["gamp_relevance"], 0
            )
            if chart_level >= min_level:
                filtered.append(chart)

        return filtered

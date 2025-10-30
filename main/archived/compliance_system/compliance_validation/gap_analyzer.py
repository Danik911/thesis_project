"""
Gap Analysis System for Compliance Validation

This module provides comprehensive gap analysis capabilities for identifying,
classifying, and prioritizing compliance gaps across GAMP-5, 21 CFR Part 11,
and ALCOA+ frameworks with risk-based prioritization.

Key Features:
- Cross-framework gap consolidation
- Risk-based gap prioritization
- Impact assessment and classification
- Gap correlation and dependency analysis
- Remediation priority ranking
- NO FALLBACKS - explicit gap analysis with full diagnostics
"""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from .evidence_collector import EvidenceCollector
from .models import ComplianceFramework, Evidence, EvidenceType, Gap, GapSeverity


class GapAnalysisError(Exception):
    """Exception raised when gap analysis fails."""


class GapPrioritizationError(Exception):
    """Exception raised when gap prioritization fails."""


class ConsolidatedGap(Gap):
    """Extended gap model for consolidated analysis."""
    related_gaps: list[str] = []
    framework_impact: dict[str, str] = {}
    business_impact_score: float = 0.0
    technical_complexity_score: float = 0.0
    remediation_effort_estimate: int = 0  # hours
    priority_rank: int = 0
    dependencies: list[str] = []


class GapAnalyzer:
    """
    Gap analyzer for comprehensive compliance gap analysis and prioritization.
    
    This class provides systematic gap analysis across multiple compliance
    frameworks with risk-based prioritization and remediation planning support.
    
    NO FALLBACKS: All gap analysis failures surface explicitly with complete
    diagnostic information for regulatory compliance.
    """

    def __init__(self, evidence_collector: EvidenceCollector):
        """
        Initialize the gap analyzer.
        
        Args:
            evidence_collector: Evidence collector for gathering gap-related evidence
        """
        self.logger = logging.getLogger(__name__)
        self.evidence_collector = evidence_collector

        # Gap analysis state
        self.consolidated_gaps: list[ConsolidatedGap] = []
        self.gap_correlations: dict[str, list[str]] = {}
        self.risk_matrix: dict[str, dict[str, float]] = {}

        # Risk scoring weights
        self.risk_weights = {
            "patient_safety": 0.4,
            "product_quality": 0.3,
            "data_integrity": 0.2,
            "compliance_exposure": 0.1
        }

        self.logger.info("GapAnalyzer initialized")

    def consolidate_gaps(
        self,
        system_name: str,
        gap_sources: dict[str, list[Gap]],
        analyzer_name: str = "gap_analyzer"
    ) -> dict[str, Any]:
        """
        Consolidate gaps from multiple compliance frameworks.
        
        Args:
            system_name: Name of system being analyzed
            gap_sources: Dictionary mapping source to list of gaps
            analyzer_name: Name of analyzer performing consolidation
            
        Returns:
            Consolidated gap analysis results
            
        Raises:
            GapAnalysisError: If gap consolidation fails
        """
        try:
            consolidation_id = str(uuid4())
            consolidation_timestamp = datetime.now(UTC).isoformat()

            self.logger.info(f"Consolidating gaps for {system_name}")

            # Flatten all gaps from sources
            all_gaps = []
            for source, gaps in gap_sources.items():
                for gap in gaps:
                    # Convert to ConsolidatedGap if needed
                    if isinstance(gap, ConsolidatedGap):
                        consolidated_gap = gap
                    else:
                        consolidated_gap = ConsolidatedGap(**gap.model_dump())

                    # Track source framework
                    consolidated_gap.framework_impact[source] = gap.severity.value
                    all_gaps.append(consolidated_gap)

            # Identify related gaps
            self._identify_gap_correlations(all_gaps)

            # Calculate business impact scores
            self._calculate_business_impact_scores(all_gaps)

            # Estimate technical complexity
            self._estimate_technical_complexity(all_gaps)

            # Estimate remediation effort
            self._estimate_remediation_effort(all_gaps)

            # Store consolidated gaps
            self.consolidated_gaps = all_gaps

            # Generate analysis summary
            consolidation_result = {
                "consolidation_id": consolidation_id,
                "system_name": system_name,
                "consolidation_timestamp": consolidation_timestamp,
                "total_gaps": len(all_gaps),
                "gaps_by_framework": {
                    framework: len([g for g in all_gaps if framework in g.framework_impact])
                    for framework in gap_sources
                },
                "gaps_by_severity": {
                    severity.value: len([g for g in all_gaps if g.severity == severity])
                    for severity in GapSeverity
                },
                "cross_framework_gaps": len([g for g in all_gaps if len(g.framework_impact) > 1]),
                "high_business_impact_gaps": len([g for g in all_gaps if g.business_impact_score >= 0.8]),
                "high_complexity_gaps": len([g for g in all_gaps if g.technical_complexity_score >= 0.8]),
                "total_remediation_effort": sum(g.remediation_effort_estimate for g in all_gaps)
            }

            # Collect consolidation evidence
            evidence = self._collect_consolidation_evidence(
                system_name, consolidation_result, analyzer_name
            )
            consolidation_result["evidence_id"] = evidence.evidence_id

            self.logger.info(f"Gap consolidation completed: {len(all_gaps)} gaps identified")
            return consolidation_result

        except Exception as e:
            error_msg = f"Gap consolidation failed for {system_name}: {e!s}"
            self.logger.error(error_msg)
            raise GapAnalysisError(error_msg) from e

    def prioritize_gaps(
        self,
        prioritization_method: str = "risk_based",
        business_context: dict[str, Any] | None = None
    ) -> list[ConsolidatedGap]:
        """
        Prioritize consolidated gaps using specified method.
        
        Args:
            prioritization_method: Method for prioritization ("risk_based", "impact_based", "effort_based")
            business_context: Optional business context for prioritization
            
        Returns:
            Prioritized list of gaps
            
        Raises:
            GapPrioritizationError: If gap prioritization fails
        """
        try:
            if not self.consolidated_gaps:
                raise GapPrioritizationError("No consolidated gaps available for prioritization")

            self.logger.info(f"Prioritizing {len(self.consolidated_gaps)} gaps using {prioritization_method}")

            # Apply prioritization method
            if prioritization_method == "risk_based":
                prioritized_gaps = self._prioritize_by_risk()
            elif prioritization_method == "impact_based":
                prioritized_gaps = self._prioritize_by_impact(business_context or {})
            elif prioritization_method == "effort_based":
                prioritized_gaps = self._prioritize_by_effort()
            else:
                raise GapPrioritizationError(f"Unknown prioritization method: {prioritization_method}")

            # Assign priority ranks
            for rank, gap in enumerate(prioritized_gaps, 1):
                gap.priority_rank = rank

            self.logger.info(f"Gap prioritization completed using {prioritization_method} method")
            return prioritized_gaps

        except Exception as e:
            error_msg = f"Gap prioritization failed: {e!s}"
            self.logger.error(error_msg)
            raise GapPrioritizationError(error_msg) from e

    def analyze_gap_dependencies(self) -> dict[str, Any]:
        """
        Analyze dependencies between gaps for remediation sequencing.
        
        Returns:
            Gap dependency analysis results
            
        Raises:
            GapAnalysisError: If dependency analysis fails
        """
        try:
            self.logger.info("Analyzing gap dependencies")

            dependency_analysis = {
                "dependency_chains": [],
                "blocking_gaps": [],
                "independent_gaps": [],
                "circular_dependencies": []
            }

            # Identify dependency relationships
            for gap in self.consolidated_gaps:
                dependencies = self._identify_gap_dependencies(gap)
                gap.dependencies = dependencies

                if dependencies:
                    dependency_analysis["dependency_chains"].append({
                        "gap_id": gap.gap_id,
                        "depends_on": dependencies
                    })
                else:
                    dependency_analysis["independent_gaps"].append(gap.gap_id)

            # Find blocking gaps (gaps that many others depend on)
            dependency_counts = {}
            for gap in self.consolidated_gaps:
                for dep in gap.dependencies:
                    dependency_counts[dep] = dependency_counts.get(dep, 0) + 1

            # Gaps with 3+ dependents are considered blocking
            blocking_threshold = 3
            dependency_analysis["blocking_gaps"] = [
                {"gap_id": gap_id, "dependent_count": count}
                for gap_id, count in dependency_counts.items()
                if count >= blocking_threshold
            ]

            # Check for circular dependencies (simplified check)
            dependency_analysis["circular_dependencies"] = self._detect_circular_dependencies()

            self.logger.info(f"Dependency analysis completed: {len(dependency_analysis['blocking_gaps'])} blocking gaps identified")
            return dependency_analysis

        except Exception as e:
            error_msg = f"Gap dependency analysis failed: {e!s}"
            self.logger.error(error_msg)
            raise GapAnalysisError(error_msg) from e

    def generate_risk_matrix(self) -> dict[str, Any]:
        """
        Generate risk matrix for gap visualization and analysis.
        
        Returns:
            Risk matrix data for gap visualization
            
        Raises:
            GapAnalysisError: If risk matrix generation fails
        """
        try:
            self.logger.info("Generating gap risk matrix")

            risk_matrix = {
                "matrix_data": [],
                "risk_categories": {
                    "high_impact_high_probability": [],
                    "high_impact_low_probability": [],
                    "low_impact_high_probability": [],
                    "low_impact_low_probability": []
                },
                "framework_distribution": {},
                "severity_distribution": {}
            }

            for gap in self.consolidated_gaps:
                # Calculate impact and probability scores
                impact_score = gap.business_impact_score
                probability_score = self._calculate_gap_probability(gap)

                matrix_entry = {
                    "gap_id": gap.gap_id,
                    "title": gap.title,
                    "impact_score": impact_score,
                    "probability_score": probability_score,
                    "risk_score": impact_score * probability_score,
                    "severity": gap.severity.value,
                    "framework": gap.framework.value,
                    "remediation_effort": gap.remediation_effort_estimate
                }

                risk_matrix["matrix_data"].append(matrix_entry)

                # Categorize by risk quadrants
                if impact_score >= 0.7 and probability_score >= 0.7:
                    risk_matrix["risk_categories"]["high_impact_high_probability"].append(gap.gap_id)
                elif impact_score >= 0.7 and probability_score < 0.7:
                    risk_matrix["risk_categories"]["high_impact_low_probability"].append(gap.gap_id)
                elif impact_score < 0.7 and probability_score >= 0.7:
                    risk_matrix["risk_categories"]["low_impact_high_probability"].append(gap.gap_id)
                else:
                    risk_matrix["risk_categories"]["low_impact_low_probability"].append(gap.gap_id)

            # Generate distribution summaries
            risk_matrix["framework_distribution"] = {
                framework.value: len([g for g in self.consolidated_gaps if g.framework == framework])
                for framework in ComplianceFramework
            }

            risk_matrix["severity_distribution"] = {
                severity.value: len([g for g in self.consolidated_gaps if g.severity == severity])
                for severity in GapSeverity
            }

            self.risk_matrix = risk_matrix

            self.logger.info(f"Risk matrix generated with {len(risk_matrix['matrix_data'])} gaps")
            return risk_matrix

        except Exception as e:
            error_msg = f"Risk matrix generation failed: {e!s}"
            self.logger.error(error_msg)
            raise GapAnalysisError(error_msg) from e

    def _identify_gap_correlations(self, gaps: list[ConsolidatedGap]) -> None:
        """Identify correlations between gaps."""
        for i, gap1 in enumerate(gaps):
            correlations = []

            for j, gap2 in enumerate(gaps):
                if i != j:
                    # Check for correlation indicators
                    correlation_score = self._calculate_gap_correlation(gap1, gap2)
                    if correlation_score > 0.7:  # High correlation threshold
                        correlations.append(gap2.gap_id)

            gap1.related_gaps = correlations
            if correlations:
                self.gap_correlations[gap1.gap_id] = correlations

    def _calculate_gap_correlation(self, gap1: ConsolidatedGap, gap2: ConsolidatedGap) -> float:
        """Calculate correlation score between two gaps."""
        correlation_factors = []

        # Same framework
        if gap1.framework == gap2.framework:
            correlation_factors.append(0.3)

        # Similar severity
        severity_mapping = {GapSeverity.CRITICAL: 4, GapSeverity.HIGH: 3, GapSeverity.MEDIUM: 2, GapSeverity.LOW: 1}
        severity_diff = abs(severity_mapping[gap1.severity] - severity_mapping[gap2.severity])
        if severity_diff <= 1:
            correlation_factors.append(0.2)

        # Similar root causes (simple keyword matching)
        gap1_keywords = set(gap1.root_cause.lower().split())
        gap2_keywords = set(gap2.root_cause.lower().split())
        keyword_overlap = len(gap1_keywords & gap2_keywords) / len(gap1_keywords | gap2_keywords) if gap1_keywords | gap2_keywords else 0
        if keyword_overlap > 0.3:
            correlation_factors.append(keyword_overlap * 0.3)

        # Similar impact areas
        if gap1.risk_to_patient == gap2.risk_to_patient:
            correlation_factors.append(0.2)

        return sum(correlation_factors)

    def _calculate_business_impact_scores(self, gaps: list[ConsolidatedGap]) -> None:
        """Calculate business impact scores for gaps."""
        for gap in gaps:
            impact_components = []

            # Risk to patient (highest weight)
            patient_risk_score = self._score_risk_level(gap.risk_to_patient)
            impact_components.append(patient_risk_score * self.risk_weights["patient_safety"])

            # Risk to product
            product_risk_score = self._score_risk_level(gap.risk_to_product)
            impact_components.append(product_risk_score * self.risk_weights["product_quality"])

            # Risk to data
            data_risk_score = self._score_risk_level(gap.risk_to_data)
            impact_components.append(data_risk_score * self.risk_weights["data_integrity"])

            # Compliance exposure
            compliance_risk_score = self._score_risk_level(gap.compliance_exposure)
            impact_components.append(compliance_risk_score * self.risk_weights["compliance_exposure"])

            gap.business_impact_score = sum(impact_components)

    def _score_risk_level(self, risk_description: str) -> float:
        """Convert risk description to numerical score."""
        risk_description_lower = risk_description.lower()

        if "critical" in risk_description_lower:
            return 1.0
        if "high" in risk_description_lower:
            return 0.8
        if "medium" in risk_description_lower:
            return 0.6
        if "low" in risk_description_lower:
            return 0.3
        return 0.5  # Unknown/unclear risk level

    def _estimate_technical_complexity(self, gaps: list[ConsolidatedGap]) -> None:
        """Estimate technical complexity for each gap."""
        for gap in gaps:
            complexity_factors = []

            # Framework complexity
            framework_complexity = {
                ComplianceFramework.GAMP5: 0.6,
                ComplianceFramework.CFR_PART_11: 0.8,
                ComplianceFramework.ALCOA_PLUS: 0.7,
                ComplianceFramework.ISO_13485: 0.7
            }
            complexity_factors.append(framework_complexity.get(gap.framework, 0.5))

            # Severity implies complexity
            severity_complexity = {
                GapSeverity.CRITICAL: 1.0,
                GapSeverity.HIGH: 0.8,
                GapSeverity.MEDIUM: 0.6,
                GapSeverity.LOW: 0.3
            }
            complexity_factors.append(severity_complexity[gap.severity])

            # Root cause complexity indicators
            complex_indicators = ["custom", "integration", "infrastructure", "process change", "system modification"]
            root_cause_lower = gap.root_cause.lower()
            complexity_boost = sum(0.1 for indicator in complex_indicators if indicator in root_cause_lower)
            complexity_factors.append(min(complexity_boost, 0.5))

            gap.technical_complexity_score = min(sum(complexity_factors) / len(complexity_factors) + complexity_boost, 1.0)

    def _estimate_remediation_effort(self, gaps: list[ConsolidatedGap]) -> None:
        """Estimate remediation effort in hours for each gap."""
        for gap in gaps:
            base_hours = {
                GapSeverity.CRITICAL: 80,
                GapSeverity.HIGH: 40,
                GapSeverity.MEDIUM: 20,
                GapSeverity.LOW: 8
            }

            effort = base_hours[gap.severity]

            # Adjust based on technical complexity
            complexity_multiplier = 1.0 + (gap.technical_complexity_score * 2.0)
            effort = int(effort * complexity_multiplier)

            # Adjust based on framework requirements
            framework_multipliers = {
                ComplianceFramework.CFR_PART_11: 1.5,  # More regulatory overhead
                ComplianceFramework.ALCOA_PLUS: 1.3,
                ComplianceFramework.GAMP5: 1.2
            }
            framework_multiplier = framework_multipliers.get(gap.framework, 1.0)
            effort = int(effort * framework_multiplier)

            gap.remediation_effort_estimate = effort

    def _prioritize_by_risk(self) -> list[ConsolidatedGap]:
        """Prioritize gaps by risk score (impact × probability)."""
        scored_gaps = []

        for gap in self.consolidated_gaps:
            impact_score = gap.business_impact_score
            probability_score = self._calculate_gap_probability(gap)
            risk_score = impact_score * probability_score

            scored_gaps.append((risk_score, gap))

        # Sort by risk score (descending)
        scored_gaps.sort(key=lambda x: x[0], reverse=True)
        return [gap for _, gap in scored_gaps]

    def _prioritize_by_impact(self, business_context: dict[str, Any]) -> list[ConsolidatedGap]:
        """Prioritize gaps by business impact with context weighting."""
        scored_gaps = []

        # Apply business context weighting if provided
        context_weights = business_context.get("priority_weights", self.risk_weights)

        for gap in self.consolidated_gaps:
            # Recalculate impact with business context
            weighted_impact = self._calculate_contextual_impact(gap, context_weights)
            scored_gaps.append((weighted_impact, gap))

        # Sort by weighted impact (descending)
        scored_gaps.sort(key=lambda x: x[0], reverse=True)
        return [gap for _, gap in scored_gaps]

    def _prioritize_by_effort(self) -> list[ConsolidatedGap]:
        """Prioritize gaps by effort (quick wins first)."""
        # Sort by effort ascending, then by impact descending
        return sorted(
            self.consolidated_gaps,
            key=lambda gap: (gap.remediation_effort_estimate, -gap.business_impact_score)
        )

    def _calculate_gap_probability(self, gap: ConsolidatedGap) -> float:
        """Calculate probability of gap occurrence/impact."""
        probability_factors = []

        # Severity implies higher probability of impact
        severity_probability = {
            GapSeverity.CRITICAL: 0.9,
            GapSeverity.HIGH: 0.7,
            GapSeverity.MEDIUM: 0.5,
            GapSeverity.LOW: 0.3
        }
        probability_factors.append(severity_probability[gap.severity])

        # Framework regulatory scrutiny
        framework_probability = {
            ComplianceFramework.CFR_PART_11: 0.8,  # High regulatory scrutiny
            ComplianceFramework.ALCOA_PLUS: 0.7,
            ComplianceFramework.GAMP5: 0.6
        }
        probability_factors.append(framework_probability.get(gap.framework, 0.5))

        return sum(probability_factors) / len(probability_factors)

    def _calculate_contextual_impact(self, gap: ConsolidatedGap, context_weights: dict[str, float]) -> float:
        """Calculate impact score with business context weighting."""
        impact_components = []

        # Apply context-specific weights
        patient_risk_score = self._score_risk_level(gap.risk_to_patient)
        impact_components.append(patient_risk_score * context_weights.get("patient_safety", 0.4))

        product_risk_score = self._score_risk_level(gap.risk_to_product)
        impact_components.append(product_risk_score * context_weights.get("product_quality", 0.3))

        data_risk_score = self._score_risk_level(gap.risk_to_data)
        impact_components.append(data_risk_score * context_weights.get("data_integrity", 0.2))

        compliance_risk_score = self._score_risk_level(gap.compliance_exposure)
        impact_components.append(compliance_risk_score * context_weights.get("compliance_exposure", 0.1))

        return sum(impact_components)

    def _identify_gap_dependencies(self, gap: ConsolidatedGap) -> list[str]:
        """Identify dependencies for a specific gap."""
        dependencies = []

        # Check for infrastructure dependencies
        if "infrastructure" in gap.root_cause.lower():
            # Find other infrastructure gaps
            for other_gap in self.consolidated_gaps:
                if (other_gap.gap_id != gap.gap_id and
                    "infrastructure" in other_gap.root_cause.lower() and
                    other_gap.severity in [GapSeverity.CRITICAL, GapSeverity.HIGH]):
                    dependencies.append(other_gap.gap_id)

        # Check for system modification dependencies
        if "system" in gap.root_cause.lower() and "modification" in gap.root_cause.lower():
            # System gaps often depend on configuration gaps
            for other_gap in self.consolidated_gaps:
                if (other_gap.gap_id != gap.gap_id and
                    "configuration" in other_gap.root_cause.lower()):
                    dependencies.append(other_gap.gap_id)

        # Check for process dependencies
        if "process" in gap.root_cause.lower():
            # Process gaps may depend on documentation gaps
            for other_gap in self.consolidated_gaps:
                if (other_gap.gap_id != gap.gap_id and
                    "documentation" in other_gap.root_cause.lower()):
                    dependencies.append(other_gap.gap_id)

        return dependencies

    def _detect_circular_dependencies(self) -> list[dict[str, Any]]:
        """Detect circular dependencies in gap relationships."""
        circular_deps = []

        # Simple cycle detection using visited tracking
        for gap in self.consolidated_gaps:
            visited = set()
            path = []

            if self._has_cycle(gap.gap_id, visited, path):
                circular_deps.append({
                    "cycle_start": gap.gap_id,
                    "cycle_path": path.copy()
                })

        return circular_deps

    def _has_cycle(self, gap_id: str, visited: set, path: list) -> bool:
        """Check if gap has circular dependency using DFS."""
        if gap_id in visited:
            cycle_start = path.index(gap_id) if gap_id in path else 0
            return len(path[cycle_start:]) > 1

        visited.add(gap_id)
        path.append(gap_id)

        # Find gap object
        gap = next((g for g in self.consolidated_gaps if g.gap_id == gap_id), None)
        if not gap:
            return False

        for dep_id in gap.dependencies:
            if self._has_cycle(dep_id, visited.copy(), path.copy()):
                return True

        return False

    def _collect_consolidation_evidence(
        self, system_name: str, consolidation_result: dict[str, Any], analyzer_name: str
    ) -> Evidence:
        """Collect evidence for gap consolidation analysis."""
        return self.evidence_collector.collect_evidence_from_system(
            system_name=system_name,
            evidence_type=EvidenceType.PROCESS_RECORD,
            collection_method="automated_gap_consolidation_analysis",
            collector_name=analyzer_name,
            analysis_data=consolidation_result,
            compliance_framework="Multi-Framework"
        )

    def get_gap_analysis_summary(self) -> dict[str, Any]:
        """Get summary of gap analysis results."""
        if not self.consolidated_gaps:
            return {"status": "no_gaps_analyzed"}

        return {
            "total_gaps": len(self.consolidated_gaps),
            "gaps_by_severity": {
                severity.value: len([g for g in self.consolidated_gaps if g.severity == severity])
                for severity in GapSeverity
            },
            "gaps_by_framework": {
                framework.value: len([g for g in self.consolidated_gaps
                                     if any(framework.value in impact for impact in g.framework_impact.keys())])
                for framework in ComplianceFramework
            },
            "high_priority_gaps": len([g for g in self.consolidated_gaps if g.priority_rank <= 10]),
            "total_remediation_effort": sum(g.remediation_effort_estimate for g in self.consolidated_gaps),
            "average_business_impact": sum(g.business_impact_score for g in self.consolidated_gaps) / len(self.consolidated_gaps),
            "complex_gaps": len([g for g in self.consolidated_gaps if g.technical_complexity_score >= 0.7]),
            "correlated_gaps": len(self.gap_correlations),
            "gaps_with_dependencies": len([g for g in self.consolidated_gaps if g.dependencies])
        }

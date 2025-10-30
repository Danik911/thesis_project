"""
GAMP-5 Compliance Assessor

This module provides comprehensive GAMP-5 compliance assessment capabilities
including categorization validation, lifecycle coverage analysis, and risk-based
testing approach verification.

Key Features:
- Software categorization accuracy assessment
- Risk-based testing approach validation  
- Lifecycle artifact completeness verification
- Documentation standards compliance checking
- Integration with existing GAMP strategies
- NO FALLBACKS - explicit error handling and validation
"""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from src.agents.planner.gamp_strategies import (
    GAMP_CATEGORY_STRATEGIES,
    calculate_estimated_test_count,
    get_category_strategy,
)
from src.core.events import GAMPCategory
from src.cross_validation.quality_metrics import QualityMetrics

from .evidence_collector import EvidenceCollector
from .models import (
    ComplianceFramework,
    ComplianceResult,
    ComplianceStatus,
    Evidence,
    EvidenceType,
    Gap,
    GapSeverity,
)


class GAMP5AssessmentError(Exception):
    """Exception raised when GAMP-5 assessment fails."""


class CategoryValidationError(Exception):
    """Exception raised when category validation fails."""


class LifecycleValidationError(Exception):
    """Exception raised when lifecycle validation fails."""


class GAMP5Assessor:
    """
    GAMP-5 compliance assessor for pharmaceutical test generation systems.
    
    This class provides comprehensive GAMP-5 compliance assessment including
    categorization validation, lifecycle coverage analysis, and risk-based
    testing approach verification.
    
    NO FALLBACKS: All assessment failures surface explicitly with complete
    diagnostic information for regulatory compliance.
    """

    def __init__(
        self,
        evidence_collector: EvidenceCollector,
        quality_metrics: QualityMetrics | None = None
    ):
        """
        Initialize the GAMP-5 assessor.
        
        Args:
            evidence_collector: Evidence collector for gathering compliance evidence
            quality_metrics: Optional quality metrics analyzer
        """
        self.logger = logging.getLogger(__name__)
        self.evidence_collector = evidence_collector
        self.quality_metrics = quality_metrics

        # Assessment state
        self.current_assessment: dict[str, Any] = {}
        self.identified_gaps: list[Gap] = []

        self.logger.info("GAMP5Assessor initialized")

    def assess_system_categorization(
        self,
        system_name: str,
        predicted_category: GAMPCategory,
        expected_category: GAMPCategory | None = None,
        categorization_rationale: str = "",
        confidence_score: float = 0.0,
        assessor_name: str = "gamp5_assessor"
    ) -> dict[str, Any]:
        """
        Assess GAMP-5 system categorization accuracy and compliance.
        
        Args:
            system_name: Name of system being assessed
            predicted_category: Predicted GAMP category
            expected_category: Expected/ground truth category (if available)
            categorization_rationale: Rationale for category determination
            confidence_score: Confidence in categorization
            assessor_name: Name of assessor performing evaluation
            
        Returns:
            Assessment results with compliance status and evidence
            
        Raises:
            CategoryValidationError: If categorization assessment fails
        """
        try:
            assessment_id = str(uuid4())
            assessment_timestamp = datetime.now(UTC).isoformat()

            self.logger.info(f"Assessing GAMP-5 categorization for {system_name}")

            # Validate predicted category is supported
            if predicted_category not in GAMP_CATEGORY_STRATEGIES:
                raise CategoryValidationError(
                    f"Unsupported GAMP category: {predicted_category}. "
                    f"Supported categories: {list(GAMP_CATEGORY_STRATEGIES.keys())}"
                )

            # Get category strategy
            strategy = get_category_strategy(predicted_category)

            # Assessment results
            assessment_result = {
                "assessment_id": assessment_id,
                "system_name": system_name,
                "assessment_timestamp": assessment_timestamp,
                "predicted_category": predicted_category.name,
                "predicted_category_value": predicted_category.value,
                "expected_category": expected_category.name if expected_category else None,
                "categorization_rationale": categorization_rationale,
                "confidence_score": confidence_score,
                "strategy": {
                    "validation_rigor": strategy.validation_rigor,
                    "test_types": strategy.test_types,
                    "compliance_requirements": strategy.compliance_requirements,
                    "estimated_count": strategy.estimated_count,
                    "focus_areas": strategy.focus_areas,
                    "risk_level": strategy.risk_level,
                    "documentation_level": strategy.documentation_level,
                    "review_requirements": strategy.review_requirements
                }
            }

            # Determine compliance status
            compliance_status = self._assess_category_compliance(
                predicted_category, expected_category, confidence_score, categorization_rationale
            )
            assessment_result["compliance_status"] = compliance_status.value

            # Validate categorization decision process
            decision_validation = self._validate_categorization_decision(
                system_name, predicted_category, categorization_rationale
            )
            assessment_result["decision_validation"] = decision_validation

            # Check for gaps if non-compliant
            if compliance_status != ComplianceStatus.COMPLIANT:
                gaps = self._identify_categorization_gaps(
                    system_name, predicted_category, expected_category,
                    confidence_score, categorization_rationale
                )
                assessment_result["gaps_identified"] = [gap.gap_id for gap in gaps]
                self.identified_gaps.extend(gaps)

            # Collect evidence
            evidence = self._collect_categorization_evidence(
                system_name, assessment_result, assessor_name
            )
            assessment_result["evidence_id"] = evidence.evidence_id

            # Store assessment
            self.current_assessment["categorization"] = assessment_result

            self.logger.info(f"Categorization assessment completed: {compliance_status.value}")
            return assessment_result

        except Exception as e:
            error_msg = f"GAMP-5 categorization assessment failed for {system_name}: {e!s}"
            self.logger.error(error_msg)
            raise CategoryValidationError(error_msg) from e

    def validate_lifecycle_coverage(
        self,
        system_name: str,
        gamp_category: GAMPCategory,
        lifecycle_artifacts: dict[str, Any],
        assessor_name: str = "gamp5_assessor"
    ) -> dict[str, Any]:
        """
        Validate lifecycle artifact coverage per GAMP-5 requirements.
        
        Args:
            system_name: Name of system being assessed
            gamp_category: GAMP category for the system
            lifecycle_artifacts: Available lifecycle artifacts
            assessor_name: Name of assessor performing evaluation
            
        Returns:
            Lifecycle coverage assessment results
            
        Raises:
            LifecycleValidationError: If lifecycle validation fails
        """
        try:
            assessment_id = str(uuid4())
            assessment_timestamp = datetime.now(UTC).isoformat()

            self.logger.info(f"Validating lifecycle coverage for {system_name}")

            # Get required artifacts for category
            strategy = get_category_strategy(gamp_category)
            required_artifacts = self._get_required_lifecycle_artifacts(gamp_category, strategy)

            # Check artifact availability
            artifact_coverage = self._assess_artifact_coverage(
                required_artifacts, lifecycle_artifacts
            )

            # Validate artifact quality
            artifact_quality = self._assess_artifact_quality(
                lifecycle_artifacts, gamp_category
            )

            # Calculate overall coverage score
            coverage_score = self._calculate_lifecycle_coverage_score(
                artifact_coverage, artifact_quality
            )

            # Determine compliance status
            compliance_status = self._determine_lifecycle_compliance(coverage_score, artifact_coverage)

            assessment_result = {
                "assessment_id": assessment_id,
                "system_name": system_name,
                "assessment_timestamp": assessment_timestamp,
                "gamp_category": gamp_category.name,
                "required_artifacts": required_artifacts,
                "artifact_coverage": artifact_coverage,
                "artifact_quality": artifact_quality,
                "coverage_score": coverage_score,
                "compliance_status": compliance_status.value,
                "validation_rigor": strategy.validation_rigor,
                "documentation_level": strategy.documentation_level
            }

            # Identify gaps if needed
            if compliance_status != ComplianceStatus.COMPLIANT:
                gaps = self._identify_lifecycle_gaps(
                    system_name, gamp_category, required_artifacts,
                    artifact_coverage, artifact_quality
                )
                assessment_result["gaps_identified"] = [gap.gap_id for gap in gaps]
                self.identified_gaps.extend(gaps)

            # Collect evidence
            evidence = self._collect_lifecycle_evidence(
                system_name, assessment_result, assessor_name
            )
            assessment_result["evidence_id"] = evidence.evidence_id

            # Store assessment
            self.current_assessment["lifecycle_coverage"] = assessment_result

            self.logger.info(f"Lifecycle coverage assessment completed: {compliance_status.value}")
            return assessment_result

        except Exception as e:
            error_msg = f"Lifecycle coverage validation failed for {system_name}: {e!s}"
            self.logger.error(error_msg)
            raise LifecycleValidationError(error_msg) from e

    def assess_risk_based_testing(
        self,
        system_name: str,
        gamp_category: GAMPCategory,
        risk_assessment: dict[str, Any],
        testing_approach: dict[str, Any],
        assessor_name: str = "gamp5_assessor"
    ) -> dict[str, Any]:
        """
        Assess risk-based testing approach alignment with GAMP-5.
        
        Args:
            system_name: Name of system being assessed
            gamp_category: GAMP category for the system
            risk_assessment: Risk assessment data
            testing_approach: Implemented testing approach
            assessor_name: Name of assessor performing evaluation
            
        Returns:
            Risk-based testing assessment results
            
        Raises:
            GAMP5AssessmentError: If risk assessment fails
        """
        try:
            assessment_id = str(uuid4())
            assessment_timestamp = datetime.now(UTC).isoformat()

            self.logger.info(f"Assessing risk-based testing for {system_name}")

            strategy = get_category_strategy(gamp_category)

            # Validate risk assessment completeness
            risk_validation = self._validate_risk_assessment(risk_assessment, gamp_category)

            # Assess testing approach alignment
            testing_alignment = self._assess_testing_alignment(
                testing_approach, strategy, risk_assessment
            )

            # Calculate estimated vs actual test counts
            test_count_analysis = self._analyze_test_counts(
                gamp_category, risk_assessment, testing_approach
            )

            # Determine compliance with risk-based principles
            compliance_score = self._calculate_risk_testing_compliance(
                risk_validation, testing_alignment, test_count_analysis
            )

            compliance_status = (
                ComplianceStatus.COMPLIANT if compliance_score >= 0.9
                else ComplianceStatus.PARTIALLY_COMPLIANT if compliance_score >= 0.7
                else ComplianceStatus.NON_COMPLIANT
            )

            assessment_result = {
                "assessment_id": assessment_id,
                "system_name": system_name,
                "assessment_timestamp": assessment_timestamp,
                "gamp_category": gamp_category.name,
                "risk_validation": risk_validation,
                "testing_alignment": testing_alignment,
                "test_count_analysis": test_count_analysis,
                "compliance_score": compliance_score,
                "compliance_status": compliance_status.value,
                "strategy_requirements": {
                    "validation_rigor": strategy.validation_rigor,
                    "risk_level": strategy.risk_level,
                    "test_types": strategy.test_types,
                    "estimated_count": strategy.estimated_count
                }
            }

            # Identify gaps if needed
            if compliance_status != ComplianceStatus.COMPLIANT:
                gaps = self._identify_risk_testing_gaps(
                    system_name, gamp_category, risk_validation,
                    testing_alignment, test_count_analysis
                )
                assessment_result["gaps_identified"] = [gap.gap_id for gap in gaps]
                self.identified_gaps.extend(gaps)

            # Collect evidence
            evidence = self._collect_risk_testing_evidence(
                system_name, assessment_result, assessor_name
            )
            assessment_result["evidence_id"] = evidence.evidence_id

            # Store assessment
            self.current_assessment["risk_based_testing"] = assessment_result

            self.logger.info(f"Risk-based testing assessment completed: {compliance_status.value}")
            return assessment_result

        except Exception as e:
            error_msg = f"Risk-based testing assessment failed for {system_name}: {e!s}"
            self.logger.error(error_msg)
            raise GAMP5AssessmentError(error_msg) from e

    def generate_compliance_report(
        self,
        system_name: str,
        assessor_name: str = "gamp5_assessor"
    ) -> ComplianceResult:
        """
        Generate comprehensive GAMP-5 compliance report.
        
        Args:
            system_name: Name of system being assessed
            assessor_name: Name of assessor generating report
            
        Returns:
            Comprehensive compliance result
            
        Raises:
            GAMP5AssessmentError: If report generation fails
        """
        try:
            if not self.current_assessment:
                raise GAMP5AssessmentError("No assessments performed. Run assessments before generating report.")

            # Aggregate assessment results
            framework_results = {
                "gamp5": {
                    "categorization": self.current_assessment.get("categorization", {}),
                    "lifecycle_coverage": self.current_assessment.get("lifecycle_coverage", {}),
                    "risk_based_testing": self.current_assessment.get("risk_based_testing", {})
                }
            }

            # Calculate overall compliance status and score
            overall_status, overall_score = self._calculate_overall_compliance(framework_results)

            # Create compliance result
            compliance_result = ComplianceResult(
                assessment_name=f"GAMP-5 Compliance Assessment - {system_name}",
                system_under_assessment=system_name,
                frameworks_assessed=[ComplianceFramework.GAMP5],
                assessment_scope="GAMP-5 categorization, lifecycle coverage, and risk-based testing validation",
                framework_results=framework_results,
                overall_status=overall_status,
                overall_score=overall_score,
                total_gaps_identified=len(self.identified_gaps),
                critical_gaps=len([g for g in self.identified_gaps if g.severity == GapSeverity.CRITICAL]),
                high_priority_gaps=len([g for g in self.identified_gaps if g.severity == GapSeverity.HIGH]),
                assessment_team=[assessor_name],
                assessment_start_date=datetime.now(UTC).isoformat(),
                gap_ids=[gap.gap_id for gap in self.identified_gaps]
            )

            # Add framework-specific results
            compliance_result.add_framework_result(ComplianceFramework.GAMP5, {
                "status": overall_status,
                "score": overall_score,
                "categorization_compliant": self.current_assessment.get("categorization", {}).get("compliance_status") == "compliant",
                "lifecycle_compliant": self.current_assessment.get("lifecycle_coverage", {}).get("compliance_status") == "compliant",
                "risk_testing_compliant": self.current_assessment.get("risk_based_testing", {}).get("compliance_status") == "compliant"
            })

            self.logger.info(f"GAMP-5 compliance report generated: {overall_status.value}")
            return compliance_result

        except Exception as e:
            error_msg = f"GAMP-5 compliance report generation failed: {e!s}"
            self.logger.error(error_msg)
            raise GAMP5AssessmentError(error_msg) from e

    def _assess_category_compliance(
        self,
        predicted_category: GAMPCategory,
        expected_category: GAMPCategory | None,
        confidence_score: float,
        rationale: str
    ) -> ComplianceStatus:
        """Assess categorization compliance based on accuracy and confidence."""
        # If we have ground truth, check accuracy
        if expected_category is not None:
            if predicted_category != expected_category:
                return ComplianceStatus.NON_COMPLIANT

        # Check confidence score
        if confidence_score < 0.8:
            return ComplianceStatus.PARTIALLY_COMPLIANT

        # Check rationale completeness
        if not rationale or len(rationale.strip()) < 50:
            return ComplianceStatus.PARTIALLY_COMPLIANT

        return ComplianceStatus.COMPLIANT

    def _validate_categorization_decision(
        self,
        system_name: str,
        predicted_category: GAMPCategory,
        rationale: str
    ) -> dict[str, Any]:
        """Validate the categorization decision process."""
        validation_result = {
            "follows_decision_tree": self._check_decision_tree_compliance(rationale),
            "rationale_completeness": len(rationale.strip()) >= 50,
            "category_justification": self._validate_category_justification(predicted_category, rationale),
            "risk_consideration": "risk" in rationale.lower(),
            "business_impact_consideration": any(term in rationale.lower() for term in ["business", "impact", "critical"]),
            "validation_score": 0.0
        }

        # Calculate validation score
        score_components = [
            validation_result["follows_decision_tree"],
            validation_result["rationale_completeness"],
            validation_result["category_justification"],
            validation_result["risk_consideration"],
            validation_result["business_impact_consideration"]
        ]
        validation_result["validation_score"] = sum(score_components) / len(score_components)

        return validation_result

    def _check_decision_tree_compliance(self, rationale: str) -> bool:
        """Check if rationale follows GAMP-5 decision tree logic."""
        decision_keywords = [
            "operating system", "firmware", "standard", "configured", "custom", "bespoke"
        ]
        return any(keyword in rationale.lower() for keyword in decision_keywords)

    def _validate_category_justification(self, category: GAMPCategory, rationale: str) -> bool:
        """Validate category-specific justification."""
        category_keywords = {
            GAMPCategory.CATEGORY_1: ["infrastructure", "operating system", "firmware"],
            GAMPCategory.CATEGORY_3: ["standard", "unmodified", "supplier"],
            GAMPCategory.CATEGORY_4: ["configured", "configurable", "parameter"],
            GAMPCategory.CATEGORY_5: ["custom", "bespoke", "developed"]
        }

        expected_keywords = category_keywords.get(category, [])
        return any(keyword in rationale.lower() for keyword in expected_keywords)

    def _identify_categorization_gaps(
        self,
        system_name: str,
        predicted_category: GAMPCategory,
        expected_category: GAMPCategory | None,
        confidence_score: float,
        rationale: str
    ) -> list[Gap]:
        """Identify gaps in categorization process."""
        gaps = []

        if expected_category and predicted_category != expected_category:
            gap = Gap(
                title="Incorrect GAMP Category Assignment",
                description=f"System {system_name} incorrectly categorized as {predicted_category.name}, expected {expected_category.name}",
                framework=ComplianceFramework.GAMP5,
                requirement_reference="GAMP-5 Section 3.1 - Software Categorization",
                severity=GapSeverity.HIGH,
                risk_to_patient="Medium - incorrect validation approach may miss critical risks",
                risk_to_product="High - validation rigor mismatch affects product quality assurance",
                risk_to_data="Medium - data integrity controls may be insufficient",
                compliance_exposure="High - regulatory inspection findings likely",
                root_cause="Categorization algorithm or decision process failure",
                current_state_description=f"System categorized as {predicted_category.name}",
                required_state_description=f"System should be categorized as {expected_category.name}",
                identified_by="gamp5_assessor",
                identification_method="automated_comparison"
            )
            gaps.append(gap)

        if confidence_score < 0.8:
            gap = Gap(
                title="Low Categorization Confidence",
                description=f"Categorization confidence score {confidence_score:.2f} below acceptable threshold",
                framework=ComplianceFramework.GAMP5,
                requirement_reference="Internal Quality Standard - Categorization Confidence",
                severity=GapSeverity.MEDIUM,
                risk_to_patient="Low - may require additional review",
                risk_to_product="Medium - uncertainty in validation approach",
                risk_to_data="Low - standard controls still apply",
                compliance_exposure="Medium - may require additional justification",
                root_cause="Insufficient evidence or complex system characteristics",
                current_state_description=f"Confidence score: {confidence_score:.2f}",
                required_state_description="Confidence score ≥ 0.8",
                identified_by="gamp5_assessor",
                identification_method="confidence_threshold_check"
            )
            gaps.append(gap)

        if not rationale or len(rationale.strip()) < 50:
            gap = Gap(
                title="Insufficient Categorization Rationale",
                description="Categorization rationale is incomplete or missing",
                framework=ComplianceFramework.GAMP5,
                requirement_reference="GAMP-5 Section 3.1 - Documentation Requirements",
                severity=GapSeverity.MEDIUM,
                risk_to_patient="Low - documentation gap only",
                risk_to_product="Medium - inability to verify categorization logic",
                risk_to_data="Low - no direct data impact",
                compliance_exposure="High - regulatory requirement for documented rationale",
                root_cause="Incomplete documentation process",
                current_state_description=f"Rationale length: {len(rationale.strip())} characters",
                required_state_description="Comprehensive rationale ≥ 50 characters with decision logic",
                identified_by="gamp5_assessor",
                identification_method="rationale_completeness_check"
            )
            gaps.append(gap)

        return gaps

    def _get_required_lifecycle_artifacts(self, category: GAMPCategory, strategy) -> dict[str, bool]:
        """Get required lifecycle artifacts based on GAMP category."""
        base_artifacts = {
            "user_requirements_specification": True,
            "risk_assessment": True,
            "validation_plan": True,
            "test_plan": True,
            "installation_qualification": True,
            "operational_qualification": True
        }

        if category in [GAMPCategory.CATEGORY_4, GAMPCategory.CATEGORY_5]:
            base_artifacts.update({
                "functional_requirements_specification": True,
                "design_document_specification": True,
                "performance_qualification": True,
                "traceability_matrix": True
            })

        if category == GAMPCategory.CATEGORY_5:
            base_artifacts.update({
                "design_qualification": True,
                "code_review_records": True,
                "unit_test_results": True,
                "integration_test_results": True
            })

        return base_artifacts

    def _assess_artifact_coverage(
        self, required_artifacts: dict[str, bool], available_artifacts: dict[str, Any]
    ) -> dict[str, Any]:
        """Assess artifact coverage against requirements."""
        coverage_analysis = {}

        for artifact, required in required_artifacts.items():
            if required:
                available = artifact in available_artifacts and available_artifacts[artifact] is not None
                coverage_analysis[artifact] = {
                    "required": required,
                    "available": available,
                    "status": "covered" if available else "missing"
                }

                if available:
                    artifact_data = available_artifacts[artifact]
                    coverage_analysis[artifact]["quality_score"] = self._assess_single_artifact_quality(artifact_data)

        total_required = sum(1 for req in required_artifacts.values() if req)
        total_covered = sum(1 for analysis in coverage_analysis.values() if analysis.get("available", False))

        coverage_analysis["summary"] = {
            "total_required": total_required,
            "total_covered": total_covered,
            "coverage_percentage": (total_covered / total_required * 100) if total_required > 0 else 0.0
        }

        return coverage_analysis

    def _assess_artifact_quality(self, artifacts: dict[str, Any], category: GAMPCategory) -> dict[str, float]:
        """Assess quality of lifecycle artifacts."""
        quality_scores = {}

        for artifact_name, artifact_data in artifacts.items():
            if artifact_data is not None:
                quality_scores[artifact_name] = self._assess_single_artifact_quality(artifact_data)

        return quality_scores

    def _assess_single_artifact_quality(self, artifact_data: Any) -> float:
        """Assess quality of a single artifact."""
        if artifact_data is None:
            return 0.0

        if isinstance(artifact_data, dict):
            # Check for key quality indicators
            quality_indicators = [
                "version" in artifact_data,
                "approval_date" in artifact_data,
                "approved_by" in artifact_data,
                "content" in artifact_data or "description" in artifact_data,
                len(str(artifact_data)) > 100  # Non-trivial content
            ]
            return sum(quality_indicators) / len(quality_indicators)

        # For non-dict data, basic quality check
        return 0.8 if len(str(artifact_data)) > 50 else 0.5

    def _calculate_lifecycle_coverage_score(
        self, coverage_analysis: dict[str, Any], quality_scores: dict[str, float]
    ) -> float:
        """Calculate overall lifecycle coverage score."""
        coverage_percentage = coverage_analysis.get("summary", {}).get("coverage_percentage", 0.0)

        if not quality_scores:
            return coverage_percentage / 100.0

        avg_quality = sum(quality_scores.values()) / len(quality_scores)

        # Weight coverage 70%, quality 30%
        return (coverage_percentage / 100.0 * 0.7) + (avg_quality * 0.3)

    def _determine_lifecycle_compliance(
        self, coverage_score: float, coverage_analysis: dict[str, Any]
    ) -> ComplianceStatus:
        """Determine lifecycle compliance status."""
        if coverage_score >= 0.95:
            return ComplianceStatus.COMPLIANT
        if coverage_score >= 0.8:
            return ComplianceStatus.PARTIALLY_COMPLIANT
        return ComplianceStatus.NON_COMPLIANT

    def _identify_lifecycle_gaps(
        self,
        system_name: str,
        category: GAMPCategory,
        required_artifacts: dict[str, bool],
        coverage_analysis: dict[str, Any],
        quality_scores: dict[str, float]
    ) -> list[Gap]:
        """Identify lifecycle coverage gaps."""
        gaps = []

        # Check for missing artifacts
        for artifact_name, analysis in coverage_analysis.items():
            if artifact_name != "summary" and not analysis.get("available", False):
                severity = GapSeverity.HIGH if artifact_name in ["user_requirements_specification", "validation_plan"] else GapSeverity.MEDIUM

                gap = Gap(
                    title=f"Missing Lifecycle Artifact: {artifact_name}",
                    description=f"Required artifact '{artifact_name}' is missing for {category.name} system",
                    framework=ComplianceFramework.GAMP5,
                    requirement_reference=f"GAMP-5 V-Model - {category.name} Requirements",
                    severity=severity,
                    risk_to_patient="Medium - incomplete validation lifecycle",
                    risk_to_product="High - validation gaps affect product assurance",
                    risk_to_data="Medium - data integrity controls may be incomplete",
                    compliance_exposure="High - regulatory requirement for complete lifecycle",
                    root_cause="Incomplete validation lifecycle execution",
                    current_state_description=f"Artifact '{artifact_name}' not provided",
                    required_state_description=f"Complete '{artifact_name}' artifact required",
                    identified_by="gamp5_assessor",
                    identification_method="lifecycle_coverage_analysis"
                )
                gaps.append(gap)

        # Check for low-quality artifacts
        for artifact_name, quality_score in quality_scores.items():
            if quality_score < 0.6:
                gap = Gap(
                    title=f"Low Quality Lifecycle Artifact: {artifact_name}",
                    description=f"Artifact '{artifact_name}' quality score {quality_score:.2f} below acceptable threshold",
                    framework=ComplianceFramework.GAMP5,
                    requirement_reference="GAMP-5 Document Quality Standards",
                    severity=GapSeverity.MEDIUM,
                    risk_to_patient="Low - quality issue in documentation",
                    risk_to_product="Medium - incomplete validation documentation",
                    risk_to_data="Low - no direct data impact",
                    compliance_exposure="Medium - documentation quality expectations",
                    root_cause="Incomplete or inadequate artifact development",
                    current_state_description=f"Quality score: {quality_score:.2f}",
                    required_state_description="Quality score ≥ 0.6",
                    identified_by="gamp5_assessor",
                    identification_method="artifact_quality_analysis"
                )
                gaps.append(gap)

        return gaps

    def _validate_risk_assessment(self, risk_assessment: dict[str, Any], category: GAMPCategory) -> dict[str, Any]:
        """Validate risk assessment completeness and quality."""
        required_elements = [
            "patient_safety_impact",
            "product_quality_impact",
            "data_integrity_impact",
            "business_continuity_impact",
            "risk_mitigation_measures"
        ]

        validation_result = {
            "completeness_score": 0.0,
            "quality_indicators": {},
            "missing_elements": [],
            "overall_status": "not_validated"
        }

        # Check completeness
        present_elements = 0
        for element in required_elements:
            present = element in risk_assessment and risk_assessment[element] is not None
            validation_result["quality_indicators"][element] = present
            if present:
                present_elements += 1
            else:
                validation_result["missing_elements"].append(element)

        validation_result["completeness_score"] = present_elements / len(required_elements)

        # Determine status
        if validation_result["completeness_score"] >= 0.9:
            validation_result["overall_status"] = "compliant"
        elif validation_result["completeness_score"] >= 0.7:
            validation_result["overall_status"] = "partially_compliant"
        else:
            validation_result["overall_status"] = "non_compliant"

        return validation_result

    def _assess_testing_alignment(
        self,
        testing_approach: dict[str, Any],
        strategy,
        risk_assessment: dict[str, Any]
    ) -> dict[str, Any]:
        """Assess testing approach alignment with GAMP strategy."""
        alignment_result = {
            "test_types_alignment": 0.0,
            "rigor_alignment": 0.0,
            "focus_areas_alignment": 0.0,
            "overall_alignment": 0.0
        }

        # Check test types alignment
        required_test_types = set(strategy.test_types)
        provided_test_types = set(testing_approach.get("test_types", []))

        if required_test_types:
            alignment_result["test_types_alignment"] = len(required_test_types & provided_test_types) / len(required_test_types)

        # Check rigor alignment
        provided_rigor = testing_approach.get("validation_rigor", "unknown")
        alignment_result["rigor_alignment"] = 1.0 if provided_rigor == strategy.validation_rigor else 0.5

        # Check focus areas alignment
        required_focus = set(strategy.focus_areas)
        provided_focus = set(testing_approach.get("focus_areas", []))

        if required_focus:
            alignment_result["focus_areas_alignment"] = len(required_focus & provided_focus) / len(required_focus)

        # Calculate overall alignment
        alignment_result["overall_alignment"] = (
            alignment_result["test_types_alignment"] * 0.4 +
            alignment_result["rigor_alignment"] * 0.3 +
            alignment_result["focus_areas_alignment"] * 0.3
        )

        return alignment_result

    def _analyze_test_counts(
        self,
        category: GAMPCategory,
        risk_assessment: dict[str, Any],
        testing_approach: dict[str, Any]
    ) -> dict[str, Any]:
        """Analyze test count appropriateness."""
        # Calculate estimated test count based on category and risk
        risk_multiplier = self._calculate_risk_multiplier(risk_assessment)
        estimated_count = calculate_estimated_test_count(category, risk_assessment, risk_multiplier)

        actual_count = testing_approach.get("planned_test_count", 0)

        return {
            "estimated_count": estimated_count,
            "actual_count": actual_count,
            "variance_percentage": abs(actual_count - estimated_count) / estimated_count * 100 if estimated_count > 0 else 0,
            "adequacy_assessment": self._assess_test_count_adequacy(estimated_count, actual_count),
            "risk_multiplier_applied": risk_multiplier
        }

    def _calculate_risk_multiplier(self, risk_assessment: dict[str, Any]) -> float:
        """Calculate risk multiplier from risk assessment."""
        base_multiplier = 1.0

        # Increase based on risk levels
        if risk_assessment.get("patient_safety_impact") == "high":
            base_multiplier += 0.3
        if risk_assessment.get("product_quality_impact") == "high":
            base_multiplier += 0.2
        if risk_assessment.get("data_integrity_impact") == "high":
            base_multiplier += 0.15

        return min(base_multiplier, 2.0)  # Cap at 2x

    def _assess_test_count_adequacy(self, estimated: int, actual: int) -> str:
        """Assess adequacy of test count."""
        if actual == 0:
            return "insufficient"

        ratio = actual / estimated

        if ratio >= 0.8 and ratio <= 1.5:
            return "adequate"
        if ratio > 1.5:
            return "excessive"
        return "insufficient"

    def _calculate_risk_testing_compliance(
        self,
        risk_validation: dict[str, Any],
        testing_alignment: dict[str, Any],
        test_count_analysis: dict[str, Any]
    ) -> float:
        """Calculate overall risk-based testing compliance score."""
        risk_score = 1.0 if risk_validation["overall_status"] == "compliant" else 0.5 if risk_validation["overall_status"] == "partially_compliant" else 0.0
        alignment_score = testing_alignment["overall_alignment"]
        count_score = 1.0 if test_count_analysis["adequacy_assessment"] == "adequate" else 0.5

        return (risk_score * 0.4) + (alignment_score * 0.4) + (count_score * 0.2)

    def _identify_risk_testing_gaps(
        self,
        system_name: str,
        category: GAMPCategory,
        risk_validation: dict[str, Any],
        testing_alignment: dict[str, Any],
        test_count_analysis: dict[str, Any]
    ) -> list[Gap]:
        """Identify risk-based testing gaps."""
        gaps = []

        # Risk assessment gaps
        if risk_validation["overall_status"] != "compliant":
            for missing_element in risk_validation["missing_elements"]:
                gap = Gap(
                    title=f"Missing Risk Assessment Element: {missing_element}",
                    description=f"Risk assessment missing required element: {missing_element}",
                    framework=ComplianceFramework.GAMP5,
                    requirement_reference="GAMP-5 Risk-Based Approach",
                    severity=GapSeverity.HIGH,
                    risk_to_patient="High - incomplete risk assessment",
                    risk_to_product="High - inadequate risk control measures",
                    risk_to_data="Medium - data risks may not be addressed",
                    compliance_exposure="High - regulatory requirement for risk assessment",
                    root_cause="Incomplete risk assessment process",
                    current_state_description=f"Missing: {missing_element}",
                    required_state_description=f"Complete risk assessment with {missing_element}",
                    identified_by="gamp5_assessor",
                    identification_method="risk_validation_analysis"
                )
                gaps.append(gap)

        # Testing alignment gaps
        if testing_alignment["overall_alignment"] < 0.8:
            gap = Gap(
                title="Poor Testing Approach Alignment",
                description=f"Testing approach alignment score {testing_alignment['overall_alignment']:.2f} below acceptable threshold",
                framework=ComplianceFramework.GAMP5,
                requirement_reference="GAMP-5 Category-Specific Testing",
                severity=GapSeverity.MEDIUM,
                risk_to_patient="Medium - testing approach may miss critical aspects",
                risk_to_product="High - inadequate validation approach",
                risk_to_data="Medium - data validation may be incomplete",
                compliance_exposure="High - testing approach must align with category",
                root_cause="Mismatch between testing strategy and GAMP category requirements",
                current_state_description=f"Alignment score: {testing_alignment['overall_alignment']:.2f}",
                required_state_description="Alignment score ≥ 0.8",
                identified_by="gamp5_assessor",
                identification_method="testing_alignment_analysis"
            )
            gaps.append(gap)

        # Test count gaps
        if test_count_analysis["adequacy_assessment"] != "adequate":
            severity = GapSeverity.HIGH if test_count_analysis["adequacy_assessment"] == "insufficient" else GapSeverity.MEDIUM
            gap = Gap(
                title=f"Inadequate Test Count: {test_count_analysis['adequacy_assessment']}",
                description=f"Test count assessment: {test_count_analysis['adequacy_assessment']} (estimated: {test_count_analysis['estimated_count']}, actual: {test_count_analysis['actual_count']})",
                framework=ComplianceFramework.GAMP5,
                requirement_reference="GAMP-5 Risk-Based Testing Volume",
                severity=severity,
                risk_to_patient="Medium - test coverage may be inadequate",
                risk_to_product="High - insufficient validation depth",
                risk_to_data="Medium - data validation coverage concerns",
                compliance_exposure="Medium - test adequacy expectations",
                root_cause="Test planning process not aligned with risk assessment",
                current_state_description=f"Test count: {test_count_analysis['actual_count']} ({test_count_analysis['adequacy_assessment']})",
                required_state_description=f"Adequate test count around {test_count_analysis['estimated_count']}",
                identified_by="gamp5_assessor",
                identification_method="test_count_analysis"
            )
            gaps.append(gap)

        return gaps

    def _collect_categorization_evidence(
        self, system_name: str, assessment_result: dict[str, Any], assessor_name: str
    ) -> Evidence:
        """Collect evidence for categorization assessment."""
        return self.evidence_collector.collect_evidence_from_system(
            system_name=system_name,
            evidence_type=EvidenceType.TEST_RESULT,
            collection_method="automated_gamp5_categorization_assessment",
            collector_name=assessor_name,
            assessment_data=assessment_result,
            compliance_framework="GAMP-5",
            experiment_id=f"gamp5_cat_{assessment_result.get('assessment_id', 'unknown')}"
        )

    def _collect_lifecycle_evidence(
        self, system_name: str, assessment_result: dict[str, Any], assessor_name: str
    ) -> Evidence:
        """Collect evidence for lifecycle coverage assessment."""
        return self.evidence_collector.collect_evidence_from_system(
            system_name=system_name,
            evidence_type=EvidenceType.DOCUMENT,
            collection_method="automated_gamp5_lifecycle_assessment",
            collector_name=assessor_name,
            assessment_data=assessment_result,
            compliance_framework="GAMP-5",
            experiment_id=f"gamp5_lc_{assessment_result.get('assessment_id', 'unknown')}"
        )

    def _collect_risk_testing_evidence(
        self, system_name: str, assessment_result: dict[str, Any], assessor_name: str
    ) -> Evidence:
        """Collect evidence for risk-based testing assessment."""
        return self.evidence_collector.collect_evidence_from_system(
            system_name=system_name,
            evidence_type=EvidenceType.PROCESS_RECORD,
            collection_method="automated_gamp5_risk_testing_assessment",
            collector_name=assessor_name,
            assessment_data=assessment_result,
            compliance_framework="GAMP-5",
            experiment_id=f"gamp5_rt_{assessment_result.get('assessment_id', 'unknown')}"
        )

    def _calculate_overall_compliance(
        self, framework_results: dict[str, Any]
    ) -> tuple[ComplianceStatus, float]:
        """Calculate overall compliance status and score."""
        gamp5_results = framework_results.get("gamp5", {})

        # Get individual assessment statuses
        categorization_status = gamp5_results.get("categorization", {}).get("compliance_status", "not_assessed")
        lifecycle_status = gamp5_results.get("lifecycle_coverage", {}).get("compliance_status", "not_assessed")
        risk_testing_status = gamp5_results.get("risk_based_testing", {}).get("compliance_status", "not_assessed")

        # Map status to scores
        status_scores = {
            "compliant": 1.0,
            "partially_compliant": 0.7,
            "non_compliant": 0.3,
            "not_assessed": 0.0
        }

        categorization_score = status_scores.get(categorization_status, 0.0)
        lifecycle_score = status_scores.get(lifecycle_status, 0.0)
        risk_testing_score = status_scores.get(risk_testing_status, 0.0)

        # Calculate weighted overall score
        overall_score = (categorization_score * 0.3) + (lifecycle_score * 0.4) + (risk_testing_score * 0.3)
        overall_score_percentage = overall_score * 100

        # Determine overall status
        if overall_score >= 0.95:
            overall_status = ComplianceStatus.COMPLIANT
        elif overall_score >= 0.7:
            overall_status = ComplianceStatus.PARTIALLY_COMPLIANT
        else:
            overall_status = ComplianceStatus.NON_COMPLIANT

        return overall_status, overall_score_percentage

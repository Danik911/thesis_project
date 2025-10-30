"""
Test Strategy Generator for GAMP-5 Categorized Systems

This module implements intelligent test strategy generation based on GAMP-5 categorization
and URS analysis. It creates comprehensive test plans that adapt to system complexity,
risk assessment, and regulatory requirements.

Key Features:
- GAMP-category-driven strategy selection
- Risk-based test count estimation
- Compliance requirement mapping
- Timeline and resource estimation
- Integration with parallel agent coordination
"""

from dataclasses import asdict, dataclass
from typing import Any

from src.core.events import GAMPCategorizationEvent, GAMPCategory

from .gamp_strategies import (
    calculate_estimated_test_count,
    determine_compliance_requirements,
    determine_sme_requirements,
    get_category_strategy,
    get_test_focus_areas,
)


@dataclass
class TestStrategyResult:
    """Result of test strategy generation."""
    validation_rigor: str
    test_types: list[str]
    compliance_requirements: list[str]
    estimated_count: int
    focus_areas: list[str]
    sme_requirements: list[dict[str, Any]]
    timeline_estimate_days: int
    resource_requirements: dict[str, Any]
    risk_factors: dict[str, Any]
    quality_gates: list[dict[str, Any]]
    deliverables: list[str]
    assumptions: list[str]
    strategy_rationale: str


class GAMPStrategyGenerator:
    """
    Generates comprehensive test strategies based on GAMP-5 categorization.
    
    This class implements sophisticated strategy generation that considers:
    - GAMP category validation requirements
    - Risk assessment and complexity factors
    - Resource constraints and timeline requirements
    - Regulatory compliance needs
    - Integration with multi-agent coordination
    """

    def __init__(self, verbose: bool = False):
        """Initialize the strategy generator."""
        self.verbose = verbose
        self._quality_gates_templates = self._initialize_quality_gates()
        self._deliverable_templates = self._initialize_deliverables()

    def generate_test_strategy(
        self,
        categorization_event: GAMPCategorizationEvent,
        urs_context: dict[str, Any] | None = None,
        constraints: dict[str, Any] | None = None
    ) -> TestStrategyResult:
        """
        Generate comprehensive test strategy based on GAMP categorization.
        
        Args:
            categorization_event: GAMP categorization results
            urs_context: Optional URS analysis context
            constraints: Optional project constraints (timeline, budget, resources)
            
        Returns:
            TestStrategyResult with complete strategy
        """
        if self.verbose:
            print(f"Generating test strategy for GAMP Category {categorization_event.gamp_category.value}")

        # Get base strategy for category
        base_strategy = get_category_strategy(categorization_event.gamp_category)

        # Extract complexity and risk factors
        risk_factors = self._analyze_risk_factors(categorization_event, urs_context)

        # Calculate risk multiplier
        risk_multiplier = self._calculate_risk_multiplier(risk_factors)

        # Generate test types and counts
        test_types = self._determine_test_types(
            categorization_event.gamp_category,
            risk_factors,
            urs_context
        )

        estimated_count = calculate_estimated_test_count(
            categorization_event.gamp_category,
            risk_factors.get("complexity_factors", {}),
            risk_multiplier
        )

        # Determine compliance requirements
        compliance_reqs = determine_compliance_requirements(
            categorization_event.gamp_category,
            risk_factors.get("risk_level", "medium")
        )

        # Get focus areas
        focus_areas = get_test_focus_areas(
            categorization_event.gamp_category,
            urs_context
        )

        # Determine SME requirements
        sme_reqs = [asdict(req) for req in determine_sme_requirements(categorization_event.gamp_category)]

        # Calculate timeline and resources
        timeline_days = self._estimate_timeline(estimated_count, categorization_event.gamp_category, constraints)
        resources = self._estimate_resources(estimated_count, categorization_event.gamp_category, constraints)

        # Generate quality gates
        quality_gates = self._generate_quality_gates(categorization_event.gamp_category, risk_factors)

        # Generate deliverables
        deliverables = self._generate_deliverables(categorization_event.gamp_category, compliance_reqs)

        # Create assumptions
        assumptions = self._generate_assumptions(categorization_event, urs_context, constraints)

        # Generate strategy rationale
        rationale = self._generate_strategy_rationale(
            categorization_event,
            risk_factors,
            estimated_count,
            timeline_days
        )

        return TestStrategyResult(
            validation_rigor=base_strategy.validation_rigor,
            test_types=test_types,
            compliance_requirements=compliance_reqs,
            estimated_count=estimated_count,
            focus_areas=focus_areas,
            sme_requirements=sme_reqs,
            timeline_estimate_days=timeline_days,
            resource_requirements=resources,
            risk_factors=risk_factors,
            quality_gates=quality_gates,
            deliverables=deliverables,
            assumptions=assumptions,
            strategy_rationale=rationale
        )

    def _analyze_risk_factors(
        self,
        categorization_event: GAMPCategorizationEvent,
        urs_context: dict[str, Any] | None
    ) -> dict[str, Any]:
        """Analyze risk factors from categorization and URS context."""
        risk_factors = {
            "confidence_level": categorization_event.confidence_score,
            "review_required": categorization_event.review_required,
            "risk_level": categorization_event.risk_assessment.get("risk_level", "medium"),
            "complexity_factors": {}
        }

        # Extract complexity factors from risk assessment
        if "complexity_factors" in categorization_event.risk_assessment:
            risk_factors["complexity_factors"] = categorization_event.risk_assessment["complexity_factors"]

        # Analyze URS context for additional risk factors
        if urs_context:
            complexity_factors = risk_factors["complexity_factors"]

            # Integration complexity
            complexity_factors["has_integrations"] = urs_context.get("integration_count", 0) > 0
            complexity_factors["integration_complexity"] = urs_context.get("integration_complexity", "low")

            # Data complexity
            complexity_factors["complex_data_flows"] = urs_context.get("data_flow_complexity", "simple") != "simple"
            complexity_factors["data_volume"] = urs_context.get("data_volume", "low")

            # Regulatory complexity
            complexity_factors["high_regulatory_impact"] = urs_context.get("regulatory_impact", "low") == "high"
            complexity_factors["compliance_scope"] = urs_context.get("compliance_scope", [])

            # Functional complexity
            complexity_factors["custom_requirements"] = urs_context.get("custom_requirement_count", 0)
            complexity_factors["user_roles"] = urs_context.get("user_role_count", 1)

            # Technical complexity
            complexity_factors["technology_stack_complexity"] = urs_context.get("tech_complexity", "standard")
            complexity_factors["performance_requirements"] = urs_context.get("performance_critical", False)

        return risk_factors

    def _calculate_risk_multiplier(self, risk_factors: dict[str, Any]) -> float:
        """Calculate risk multiplier for test count estimation."""
        base_multiplier = 1.0

        # Low confidence increases risk
        if risk_factors["confidence_level"] < 0.7:
            base_multiplier += 0.3
        elif risk_factors["confidence_level"] < 0.8:
            base_multiplier += 0.15

        # High risk level increases multiplier
        risk_level = risk_factors.get("risk_level", "medium")
        if risk_level == "high":
            base_multiplier += 0.5
        elif risk_level == "critical":
            base_multiplier += 0.8

        # Complexity factors
        complexity = risk_factors.get("complexity_factors", {})

        if complexity.get("has_integrations", False):
            base_multiplier += 0.2

        if complexity.get("complex_data_flows", False):
            base_multiplier += 0.15

        if complexity.get("high_regulatory_impact", False):
            base_multiplier += 0.25

        if complexity.get("custom_requirements", 0) > 20:
            base_multiplier += 0.3

        return min(base_multiplier, 2.5)  # Cap at 2.5x

    def _determine_test_types(
        self,
        category: GAMPCategory,
        risk_factors: dict[str, Any],
        urs_context: dict[str, Any] | None
    ) -> list[str]:
        """Determine specific test types based on category and context."""
        base_strategy = get_category_strategy(category)
        test_types = base_strategy.test_types.copy()

        # Add additional test types based on risk and context
        risk_level = risk_factors.get("risk_level", "medium")
        complexity = risk_factors.get("complexity_factors", {})

        if risk_level in ["high", "critical"]:
            if category in [GAMPCategory.CATEGORY_4, GAMPCategory.CATEGORY_5]:
                test_types.extend([
                    "stress_testing",
                    "load_testing",
                    "security_penetration_testing",
                    "disaster_recovery_testing"
                ])

        # Add based on complexity factors
        if complexity.get("has_integrations", False):
            if "integration_testing" not in test_types:
                test_types.append("integration_testing")
            test_types.append("end_to_end_testing")

        if complexity.get("performance_requirements", False):
            test_types.extend([
                "performance_testing",
                "scalability_testing"
            ])

        if complexity.get("high_regulatory_impact", False):
            test_types.extend([
                "compliance_testing",
                "audit_trail_testing",
                "data_integrity_testing"
            ])

        # Add URS-specific test types
        if urs_context:
            if urs_context.get("has_clinical_data", False):
                test_types.append("clinical_data_validation")

            if urs_context.get("requires_electronic_signatures", False):
                test_types.append("electronic_signature_testing")

            if urs_context.get("has_reporting_requirements", False):
                test_types.append("reporting_validation")

        return list(set(test_types))  # Remove duplicates

    def _estimate_timeline(
        self,
        test_count: int,
        category: GAMPCategory,
        constraints: dict[str, Any] | None
    ) -> int:
        """Estimate timeline in days for test execution."""
        # Base days per test by category
        base_days_per_test = {
            GAMPCategory.CATEGORY_1: 0.5,
            GAMPCategory.CATEGORY_3: 1.0,
            GAMPCategory.CATEGORY_4: 1.5,
            GAMPCategory.CATEGORY_5: 2.0
        }

        days_per_test = base_days_per_test.get(category, 2.0)
        base_timeline = int(test_count * days_per_test)

        # Add overhead for planning, review, and coordination
        overhead_percentage = {
            GAMPCategory.CATEGORY_1: 0.2,
            GAMPCategory.CATEGORY_3: 0.3,
            GAMPCategory.CATEGORY_4: 0.4,
            GAMPCategory.CATEGORY_5: 0.5
        }

        overhead = int(base_timeline * overhead_percentage.get(category, 0.5))
        total_timeline = base_timeline + overhead

        # Apply constraints if provided
        if constraints and "max_timeline_days" in constraints:
            max_days = constraints["max_timeline_days"]
            if total_timeline > max_days:
                # Timeline compression may require additional resources
                total_timeline = max_days

        return max(total_timeline, 5)  # Minimum 5 days

    def _estimate_resources(
        self,
        test_count: int,
        category: GAMPCategory,
        constraints: dict[str, Any] | None
    ) -> dict[str, Any]:
        """Estimate resource requirements."""
        # Base resource requirements
        resources = {
            "test_engineers": max(1, test_count // 20),
            "validation_specialists": 1 if category in [GAMPCategory.CATEGORY_4, GAMPCategory.CATEGORY_5] else 0,
            "domain_experts": len(determine_sme_requirements(category)),
            "test_environments": 1,
            "tools_required": [],
            "estimated_cost_category": "medium"
        }

        # Adjust based on category
        if category == GAMPCategory.CATEGORY_5:
            resources["test_engineers"] += 1
            resources["security_specialists"] = 1
            resources["compliance_engineers"] = 1
            resources["test_environments"] = 2
            resources["estimated_cost_category"] = "high"
        elif category == GAMPCategory.CATEGORY_4:
            resources["integration_specialists"] = 1
            resources["test_environments"] = 2
        elif category == GAMPCategory.CATEGORY_1:
            resources["estimated_cost_category"] = "low"

        # Tool requirements by category
        tool_requirements = {
            GAMPCategory.CATEGORY_1: ["basic_test_tools"],
            GAMPCategory.CATEGORY_3: ["test_management", "functional_testing_tools"],
            GAMPCategory.CATEGORY_4: ["test_management", "automation_tools", "integration_testing"],
            GAMPCategory.CATEGORY_5: ["comprehensive_test_suite", "security_tools", "performance_tools"]
        }

        resources["tools_required"] = tool_requirements.get(category, [])

        # Apply constraints
        if constraints:
            if "max_team_size" in constraints:
                total_people = (resources["test_engineers"] +
                              resources.get("validation_specialists", 0) +
                              resources.get("domain_experts", 0))
                if total_people > constraints["max_team_size"]:
                    # Scale down resources
                    scale_factor = constraints["max_team_size"] / total_people
                    resources["test_engineers"] = max(1, int(resources["test_engineers"] * scale_factor))
                    resources["validation_specialists"] = int(resources.get("validation_specialists", 0) * scale_factor)

        return resources

    def _generate_quality_gates(
        self,
        category: GAMPCategory,
        risk_factors: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Generate quality gates for the test strategy."""
        base_gates = self._quality_gates_templates.get(category, [])
        gates = []

        for gate in base_gates:
            gate_copy = gate.copy()

            # Adjust criteria based on risk factors
            if risk_factors.get("risk_level") == "high":
                if "pass_threshold" in gate_copy:
                    gate_copy["pass_threshold"] = min(gate_copy["pass_threshold"] + 0.1, 1.0)

            gates.append(gate_copy)

        return gates

    def _generate_deliverables(
        self,
        category: GAMPCategory,
        compliance_requirements: list[str]
    ) -> list[str]:
        """Generate required deliverables."""
        base_deliverables = self._deliverable_templates.get(category, [])
        deliverables = base_deliverables.copy()

        # Add compliance-specific deliverables
        if "21_cfr_part_11" in compliance_requirements:
            deliverables.extend([
                "21_cfr_part_11_compliance_matrix",
                "electronic_signature_validation_report",
                "audit_trail_verification_report"
            ])

        if "alcoa_plus" in compliance_requirements:
            deliverables.append("alcoa_plus_compliance_checklist")

        if "full_traceability" in compliance_requirements:
            deliverables.append("requirements_traceability_matrix")

        return list(set(deliverables))  # Remove duplicates

    def _generate_assumptions(
        self,
        categorization_event: GAMPCategorizationEvent,
        urs_context: dict[str, Any] | None,
        constraints: dict[str, Any] | None
    ) -> list[str]:
        """Generate strategy assumptions."""
        assumptions = [
            "URS document is complete and approved",
            "System requirements are stable",
            "Test environments will be available as scheduled",
            "Required subject matter experts will be available",
        ]

        if categorization_event.review_required:
            assumptions.append("GAMP categorization will be confirmed by expert review")

        if categorization_event.confidence_score < 0.8:
            assumptions.append("Category determination assumptions may require validation")

        if constraints:
            if "max_timeline_days" in constraints:
                assumptions.append(f"Timeline compressed to meet {constraints['max_timeline_days']} day constraint")

            if "max_team_size" in constraints:
                assumptions.append(f"Team size limited to {constraints['max_team_size']} resources")

        return assumptions

    def _generate_strategy_rationale(
        self,
        categorization_event: GAMPCategorizationEvent,
        risk_factors: dict[str, Any],
        test_count: int,
        timeline_days: int
    ) -> str:
        """Generate rationale for the test strategy."""
        rationale_parts = [
            f"Test strategy based on GAMP Category {categorization_event.gamp_category.value} classification",
            f"with {categorization_event.confidence_score:.1%} confidence."
        ]

        if categorization_event.review_required:
            rationale_parts.append("Human review required due to low confidence or complexity.")

        risk_level = risk_factors.get("risk_level", "medium")
        rationale_parts.append(f"Risk level assessed as {risk_level}.")

        complexity = risk_factors.get("complexity_factors", {})
        if complexity.get("has_integrations", False):
            rationale_parts.append("Additional integration testing included due to system integrations.")

        if complexity.get("high_regulatory_impact", False):
            rationale_parts.append("Enhanced compliance testing due to high regulatory impact.")

        rationale_parts.extend([
            f"Estimated {test_count} tests over {timeline_days} days.",
            f"Strategy follows {get_category_strategy(categorization_event.gamp_category).validation_rigor} validation rigor."
        ])

        return " ".join(rationale_parts)

    def _initialize_quality_gates(self) -> dict[GAMPCategory, list[dict[str, Any]]]:
        """Initialize quality gate templates."""
        return {
            GAMPCategory.CATEGORY_1: [
                {
                    "name": "Installation Review",
                    "phase": "IQ",
                    "criteria": "All installation verification complete",
                    "pass_threshold": 0.95,
                    "required_approvers": ["infrastructure_specialist"]
                }
            ],
            GAMPCategory.CATEGORY_3: [
                {
                    "name": "Functional Testing Complete",
                    "phase": "OQ",
                    "criteria": "All functional tests passed",
                    "pass_threshold": 0.95,
                    "required_approvers": ["functional_analyst"]
                },
                {
                    "name": "User Acceptance",
                    "phase": "UAT",
                    "criteria": "User acceptance criteria met",
                    "pass_threshold": 0.90,
                    "required_approvers": ["business_user", "functional_analyst"]
                }
            ],
            GAMPCategory.CATEGORY_4: [
                {
                    "name": "Configuration Validation",
                    "phase": "OQ",
                    "criteria": "All configurations validated",
                    "pass_threshold": 0.98,
                    "required_approvers": ["configuration_specialist"]
                },
                {
                    "name": "Integration Testing",
                    "phase": "PQ",
                    "criteria": "All integrations verified",
                    "pass_threshold": 0.95,
                    "required_approvers": ["integration_analyst"]
                }
            ],
            GAMPCategory.CATEGORY_5: [
                {
                    "name": "Design Qualification",
                    "phase": "DQ",
                    "criteria": "Design requirements verified",
                    "pass_threshold": 0.98,
                    "required_approvers": ["validation_engineer", "compliance_engineer"]
                },
                {
                    "name": "Security Validation",
                    "phase": "Custom",
                    "criteria": "Security requirements validated",
                    "pass_threshold": 0.98,
                    "required_approvers": ["security_analyst"]
                },
                {
                    "name": "Compliance Verification",
                    "phase": "Final",
                    "criteria": "All compliance requirements met",
                    "pass_threshold": 0.98,
                    "required_approvers": ["compliance_engineer", "quality_assurance"]
                }
            ]
        }

    def _initialize_deliverables(self) -> dict[GAMPCategory, list[str]]:
        """Initialize deliverable templates."""
        return {
            GAMPCategory.CATEGORY_1: [
                "installation_qualification_protocol",
                "installation_qualification_report",
                "vendor_qualification_summary"
            ],
            GAMPCategory.CATEGORY_3: [
                "test_plan",
                "functional_test_scripts",
                "user_acceptance_test_plan",
                "test_execution_report",
                "validation_summary_report"
            ],
            GAMPCategory.CATEGORY_4: [
                "validation_master_plan",
                "configuration_specification",
                "test_plan",
                "test_scripts",
                "integration_test_plan",
                "performance_qualification_protocol",
                "validation_report",
                "traceability_matrix"
            ],
            GAMPCategory.CATEGORY_5: [
                "validation_master_plan",
                "design_qualification_protocol",
                "installation_qualification_protocol",
                "operational_qualification_protocol",
                "performance_qualification_protocol",
                "test_plan",
                "test_scripts",
                "security_test_plan",
                "validation_report",
                "compliance_matrix",
                "traceability_matrix",
                "change_control_procedures"
            ]
        }

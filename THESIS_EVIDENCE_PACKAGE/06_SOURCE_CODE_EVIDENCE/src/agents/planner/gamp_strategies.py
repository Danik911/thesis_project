"""
GAMP-5 Category-Specific Test Strategies

This module defines test strategies, compliance requirements, and SME requirements
for each GAMP-5 category. It implements the category-specific validation approaches
required for pharmaceutical software according to GAMP-5 guidelines.

Key Features:
- Category-specific test type determination
- Compliance requirement mapping (ALCOA+, 21 CFR Part 11)
- SME agent specialization based on category complexity
- Risk-based estimation for test counts and timelines
"""

from dataclasses import dataclass
from typing import Any

from src.core.events import GAMPCategory


@dataclass
class TestStrategy:
    """Test strategy definition for a GAMP category."""
    validation_rigor: str
    test_types: list[str]
    compliance_requirements: list[str]
    estimated_count: int
    focus_areas: list[str]
    risk_level: str
    documentation_level: str
    review_requirements: list[str]


@dataclass
class SMERequirement:
    """SME agent requirement definition."""
    specialty: str
    priority: str
    min_experience_years: int
    domain_knowledge: list[str]
    validation_focus: list[str]


# GAMP-5 Category-specific test strategies
GAMP_CATEGORY_STRATEGIES: dict[GAMPCategory, TestStrategy] = {
    GAMPCategory.CATEGORY_1: TestStrategy(
        validation_rigor="minimal",
        test_types=[
            "installation_qualification",
            "vendor_verification",
            "supplier_audit",
            "infrastructure_testing"
        ],
        compliance_requirements=[
            "basic_documentation",
            "vendor_verification",
            "supplier_assessment",
            "installation_records"
        ],
        estimated_count=5,
        focus_areas=[
            "infrastructure_verification",
            "vendor_compliance",
            "installation_validation"
        ],
        risk_level="low",
        documentation_level="minimal",
        review_requirements=[
            "infrastructure_specialist_review",
            "vendor_qualification_review"
        ]
    ),

    GAMPCategory.CATEGORY_3: TestStrategy(
        validation_rigor="standard",
        test_types=[
            "installation_qualification",
            "operational_qualification",
            "user_acceptance_testing",
            "functional_testing",
            "integration_testing"
        ],
        compliance_requirements=[
            "alcoa_basic",
            "user_training_records",
            "sop_creation",
            "change_control_basic",
            "incident_management"
        ],
        estimated_count=15,
        focus_areas=[
            "functional_testing",
            "user_workflows",
            "business_process_validation",
            "standard_operations"
        ],
        risk_level="low_to_medium",
        documentation_level="standard",
        review_requirements=[
            "functional_analyst_review",
            "business_process_review",
            "user_acceptance_sign_off"
        ]
    ),

    GAMPCategory.CATEGORY_4: TestStrategy(
        validation_rigor="enhanced",
        test_types=[
            "installation_qualification",
            "operational_qualification",
            "performance_qualification",
            "configuration_validation",
            "integration_testing",
            "regression_testing",
            "data_migration_testing"
        ],
        compliance_requirements=[
            "alcoa_plus",
            "configuration_management",
            "change_control_enhanced",
            "risk_assessment",
            "data_integrity_validation",
            "audit_trail_verification"
        ],
        estimated_count=30,
        focus_areas=[
            "configuration_testing",
            "integration_testing",
            "performance_validation",
            "data_integrity",
            "workflow_validation"
        ],
        risk_level="medium_to_high",
        documentation_level="enhanced",
        review_requirements=[
            "configuration_specialist_review",
            "integration_analyst_review",
            "validation_engineer_review",
            "quality_assurance_review"
        ]
    ),

    GAMPCategory.CATEGORY_5: TestStrategy(
        validation_rigor="full",
        test_types=[
            "installation_qualification",
            "operational_qualification",
            "performance_qualification",
            "design_qualification",
            "custom_validation",
            "security_testing",
            "data_integrity_testing",
            "user_interface_testing",
            "api_testing",
            "database_testing",
            "backup_recovery_testing",
            "disaster_recovery_testing"
        ],
        compliance_requirements=[
            "alcoa_plus",
            "21_cfr_part_11",
            "full_traceability",
            "custom_validation_protocols",
            "security_validation",
            "data_integrity_full",
            "electronic_signatures",
            "audit_trail_comprehensive"
        ],
        estimated_count=50,
        focus_areas=[
            "custom_functionality",
            "security_testing",
            "data_integrity",
            "full_lifecycle_validation",
            "regulatory_compliance",
            "risk_management"
        ],
        risk_level="high",
        documentation_level="comprehensive",
        review_requirements=[
            "custom_development_specialist_review",
            "security_analyst_review",
            "compliance_engineer_review",
            "validation_specialist_review",
            "regulatory_affairs_review"
        ]
    )
}


# SME agent requirements by GAMP category
GAMP_SME_REQUIREMENTS: dict[GAMPCategory, list[SMERequirement]] = {
    GAMPCategory.CATEGORY_1: [
        SMERequirement(
            specialty="infrastructure_specialist",
            priority="high",
            min_experience_years=3,
            domain_knowledge=["infrastructure", "vendor_management", "system_administration"],
            validation_focus=["installation_validation", "vendor_qualification"]
        )
    ],

    GAMPCategory.CATEGORY_3: [
        SMERequirement(
            specialty="functional_analyst",
            priority="high",
            min_experience_years=5,
            domain_knowledge=["business_process", "functional_requirements", "user_workflows"],
            validation_focus=["functional_testing", "user_acceptance"]
        ),
        SMERequirement(
            specialty="user_experience_specialist",
            priority="medium",
            min_experience_years=3,
            domain_knowledge=["user_interface", "usability", "workflow_design"],
            validation_focus=["user_testing", "workflow_validation"]
        )
    ],

    GAMPCategory.CATEGORY_4: [
        SMERequirement(
            specialty="configuration_specialist",
            priority="high",
            min_experience_years=5,
            domain_knowledge=["system_configuration", "integration", "data_mapping"],
            validation_focus=["configuration_testing", "integration_validation"]
        ),
        SMERequirement(
            specialty="integration_analyst",
            priority="high",
            min_experience_years=4,
            domain_knowledge=["system_integration", "api_design", "data_flow"],
            validation_focus=["integration_testing", "data_validation"]
        ),
        SMERequirement(
            specialty="validation_engineer",
            priority="medium",
            min_experience_years=6,
            domain_knowledge=["validation_protocols", "gmp", "quality_systems"],
            validation_focus=["protocol_development", "validation_execution"]
        )
    ],

    GAMPCategory.CATEGORY_5: [
        SMERequirement(
            specialty="custom_development_specialist",
            priority="high",
            min_experience_years=7,
            domain_knowledge=["software_development", "custom_applications", "architecture"],
            validation_focus=["design_qualification", "custom_testing"]
        ),
        SMERequirement(
            specialty="security_analyst",
            priority="high",
            min_experience_years=5,
            domain_knowledge=["cybersecurity", "data_protection", "access_control"],
            validation_focus=["security_testing", "vulnerability_assessment"]
        ),
        SMERequirement(
            specialty="compliance_engineer",
            priority="high",
            min_experience_years=6,
            domain_knowledge=["21_cfr_part_11", "gamp_5", "regulatory_compliance"],
            validation_focus=["compliance_validation", "regulatory_alignment"]
        )
    ]
}


def get_category_strategy(category: GAMPCategory) -> TestStrategy:
    """
    Get the test strategy for a specific GAMP category.
    
    Args:
        category: GAMP category
        
    Returns:
        TestStrategy for the category
        
    Raises:
        ValueError: If category is not supported
    """
    if category not in GAMP_CATEGORY_STRATEGIES:
        raise ValueError(f"Unsupported GAMP category: {category}")

    return GAMP_CATEGORY_STRATEGIES[category]


def determine_sme_requirements(category: GAMPCategory) -> list[SMERequirement]:
    """
    Determine SME agent requirements for a GAMP category.
    
    Args:
        category: GAMP category
        
    Returns:
        List of SME requirements for the category
    """
    return GAMP_SME_REQUIREMENTS.get(category, [])


def determine_compliance_requirements(category: GAMPCategory, risk_level: str = None) -> list[str]:
    """
    Determine compliance requirements based on GAMP category and risk level.
    
    Args:
        category: GAMP category
        risk_level: Optional risk level override ("low", "medium", "high")
        
    Returns:
        List of compliance requirements
    """
    strategy = get_category_strategy(category)
    base_requirements = strategy.compliance_requirements.copy()

    # Enhance requirements based on risk level
    if risk_level == "high":
        if category == GAMPCategory.CATEGORY_3:
            base_requirements.extend(["enhanced_documentation", "additional_review"])
        elif category == GAMPCategory.CATEGORY_4:
            base_requirements.extend(["security_assessment", "performance_validation"])
        # Category 5 already has comprehensive requirements

    return base_requirements


def calculate_estimated_test_count(
    category: GAMPCategory,
    complexity_factors: dict[str, Any] = None,
    risk_multiplier: float = 1.0
) -> int:
    """
    Calculate estimated test count based on category and complexity factors.
    
    Args:
        category: GAMP category
        complexity_factors: Optional complexity factors from categorization
        risk_multiplier: Risk-based multiplier (default 1.0)
        
    Returns:
        Estimated number of tests needed
    """
    strategy = get_category_strategy(category)
    base_count = strategy.estimated_count

    # Apply risk multiplier
    adjusted_count = int(base_count * risk_multiplier)

    # Apply complexity factors if provided
    if complexity_factors:
        # Integration complexity
        if complexity_factors.get("has_integrations", False):
            adjusted_count = int(adjusted_count * 1.2)

        # Data complexity
        if complexity_factors.get("complex_data_flows", False):
            adjusted_count = int(adjusted_count * 1.15)

        # Regulatory complexity
        if complexity_factors.get("high_regulatory_impact", False):
            adjusted_count = int(adjusted_count * 1.3)

        # Custom requirements
        custom_req_count = complexity_factors.get("custom_requirements", 0)
        if custom_req_count > 10:
            adjusted_count = int(adjusted_count * (1 + (custom_req_count - 10) * 0.05))

    return max(adjusted_count, strategy.estimated_count)  # Never go below base count


def get_test_focus_areas(category: GAMPCategory, urs_context: dict[str, Any] = None) -> list[str]:
    """
    Get test focus areas for a category, optionally enhanced by URS context.
    
    Args:
        category: GAMP category
        urs_context: Optional URS analysis context
        
    Returns:
        List of test focus areas
    """
    strategy = get_category_strategy(category)
    focus_areas = strategy.focus_areas.copy()

    # Enhance focus areas based on URS context
    if urs_context:
        # Add specific focus areas based on URS content analysis
        if urs_context.get("has_clinical_data", False):
            focus_areas.append("clinical_data_validation")

        if urs_context.get("has_financial_data", False):
            focus_areas.append("financial_data_integrity")

        if urs_context.get("has_manufacturing_processes", False):
            focus_areas.append("manufacturing_execution_validation")

        if urs_context.get("requires_electronic_signatures", False):
            focus_areas.append("electronic_signature_validation")

    return focus_areas


def validate_strategy_compatibility(
    primary_category: GAMPCategory,
    secondary_categories: list[GAMPCategory] = None
) -> dict[str, Any]:
    """
    Validate strategy compatibility when multiple GAMP categories are involved.
    
    Args:
        primary_category: Primary GAMP category
        secondary_categories: Optional list of secondary categories
        
    Returns:
        Dictionary with compatibility analysis and recommendations
    """
    result = {
        "is_compatible": True,
        "conflicts": [],
        "recommendations": [],
        "merged_requirements": []
    }

    primary_strategy = get_category_strategy(primary_category)
    result["merged_requirements"] = primary_strategy.compliance_requirements.copy()

    if secondary_categories:
        for secondary in secondary_categories:
            secondary_strategy = get_category_strategy(secondary)

            # Check for conflicts in validation rigor
            if (primary_strategy.validation_rigor == "minimal" and
                secondary_strategy.validation_rigor in ["enhanced", "full"]):
                result["conflicts"].append(
                    f"Validation rigor conflict: {primary_category.name} requires minimal, "
                    f"{secondary.name} requires {secondary_strategy.validation_rigor}"
                )
                result["is_compatible"] = False

            # Merge requirements (take the more stringent)
            for req in secondary_strategy.compliance_requirements:
                if req not in result["merged_requirements"]:
                    result["merged_requirements"].append(req)

    # Generate recommendations
    if not result["is_compatible"]:
        result["recommendations"].append(
            "Consider treating as highest rigor category for conservative validation"
        )
        result["recommendations"].append(
            "Request SME review for category determination refinement"
        )

    return result

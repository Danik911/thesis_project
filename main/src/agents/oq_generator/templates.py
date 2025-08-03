"""
GAMP category-specific templates for OQ test generation.

This module provides templates, prompts, and configuration for generating
OQ tests appropriate to each GAMP software category with pharmaceutical
compliance requirements and regulatory best practices.
"""

from typing import Any

from src.core.events import GAMPCategory


class GAMPCategoryConfig:
    """Configuration for GAMP category-specific test generation."""

    # GAMP category requirements mapping
    CATEGORY_REQUIREMENTS = {
        GAMPCategory.CATEGORY_1: {
            "min_tests": 3,
            "max_tests": 5,
            "description": "Infrastructure Software",
            "focus": "installation_verification",
            "validation_approach": "supplier_assessment",
            "test_categories": ["installation", "functional"],
            "complexity": "basic",
            "regulatory_emphasis": "minimal"
        },
        GAMPCategory.CATEGORY_3: {
            "min_tests": 5,
            "max_tests": 10,
            "description": "Non-configured Products",
            "focus": "functional_testing",
            "validation_approach": "supplier_assessment_plus_testing",
            "test_categories": ["installation", "functional", "data_integrity"],
            "complexity": "standard",
            "regulatory_emphasis": "moderate"
        },
        GAMPCategory.CATEGORY_4: {
            "min_tests": 15,
            "max_tests": 20,
            "description": "Configured Products",
            "focus": "configuration_verification",
            "validation_approach": "risk_based_validation",
            "test_categories": ["installation", "functional", "performance", "security", "data_integrity"],
            "complexity": "comprehensive",
            "regulatory_emphasis": "high"
        },
        GAMPCategory.CATEGORY_5: {
            "min_tests": 25,
            "max_tests": 30,
            "description": "Custom Applications",
            "focus": "comprehensive_validation",
            "validation_approach": "full_validation_required",
            "test_categories": ["installation", "functional", "performance", "security", "data_integrity", "integration"],
            "complexity": "maximum",
            "regulatory_emphasis": "critical"
        }
    }

    @classmethod
    def get_category_config(cls, gamp_category: GAMPCategory) -> dict[str, Any]:
        """Get configuration for specific GAMP category."""
        if gamp_category not in cls.CATEGORY_REQUIREMENTS:
            raise ValueError(f"Unsupported GAMP category: {gamp_category}")
        return cls.CATEGORY_REQUIREMENTS[gamp_category].copy()

    @classmethod
    def get_test_count_range(cls, gamp_category: GAMPCategory) -> tuple[int, int]:
        """Get valid test count range for GAMP category."""
        config = cls.get_category_config(gamp_category)
        return (config["min_tests"], config["max_tests"])


class OQPromptTemplates:
    """Templates for OQ test generation prompts by GAMP category."""

    BASE_SYSTEM_PROMPT = """You are an expert pharmaceutical validation engineer specializing in GAMP-5 OQ test generation.

Your task is to generate comprehensive Operational Qualification (OQ) test cases that:
1. Meet GAMP-5 regulatory requirements for the specified category
2. Follow ALCOA+ data integrity principles
3. Include proper traceability to URS requirements
4. Ensure 21 CFR Part 11 electronic records compliance
5. Use pharmaceutical industry best practices

CRITICAL REQUIREMENTS:
- Generate EXACTLY the specified number of tests (no more, no less)
- Include detailed test steps with clear acceptance criteria
- Ensure all tests are executable and verifiable
- Maintain audit trail requirements throughout
- Focus on the specified GAMP category validation approach

Respond with a valid JSON structure matching the OQTestSuite schema."""

    CATEGORY_SPECIFIC_PROMPTS = {
        GAMPCategory.CATEGORY_1: """
GAMP Category 1: Infrastructure Software Validation

Focus: Installation verification and basic operational confirmation
Approach: Minimal testing relying primarily on supplier validation
Test Count: 3-5 tests

Key Testing Areas:
- Installation qualification verification
- Basic connectivity and communication
- System integration points
- Standard operational procedures
- Error handling for common scenarios

Test Characteristics:
- Streamlined procedures focusing on intended use
- Emphasis on installation and setup verification
- Basic functional testing of core features
- Minimal customization testing required
- Supplier documentation verification
""",

        GAMPCategory.CATEGORY_3: """
GAMP Category 3: Non-configured Products Validation

Focus: Functional testing of standard features with verification of intended use
Approach: Supplier assessment plus focused functional testing
Test Count: 5-10 tests

Key Testing Areas:
- Standard functionality verification
- Data input/output validation
- User interface testing
- Basic reporting capabilities
- Data integrity verification
- Standard workflow testing

Test Characteristics:
- Focus on functions directly used in GxP environment
- Verify calculations and data processing accuracy
- Test standard user workflows and procedures
- Validate data integrity and audit trail features
- Confirm system meets intended use requirements
""",

        GAMPCategory.CATEGORY_4: """
GAMP Category 4: Configured Products Validation

Focus: Configuration verification and business process validation
Approach: Risk-based validation of configured elements
Test Count: 15-20 tests

Key Testing Areas:
- Configuration parameter verification
- Business process workflow testing
- User role and permission validation
- Integration testing with other systems
- Performance testing under load
- Security and access control verification
- Data integrity and audit trail validation
- Deviation and error handling procedures

Test Characteristics:
- Comprehensive testing of configured elements
- Business process scenario validation
- Multi-user and role-based testing
- Integration and interface verification
- Performance and scalability testing
- Security and compliance validation
""",

        GAMPCategory.CATEGORY_5: """
GAMP Category 5: Custom Applications Validation

Focus: Comprehensive validation including code-level verification
Approach: Full validation with extensive testing across all functions
Test Count: 25-30 tests

Key Testing Areas:
- Complete functional testing of all features
- Algorithm and calculation verification
- Comprehensive integration testing
- Performance and stress testing
- Security penetration testing
- Complete data lifecycle validation
- Comprehensive error handling and recovery
- Full audit trail and compliance verification
- User acceptance testing scenarios
- Boundary and edge case testing

Test Characteristics:
- Exhaustive testing covering all system functions
- Mathematical and algorithmic verification
- Comprehensive negative testing scenarios
- Full integration and system testing
- Performance testing under various conditions
- Complete security and compliance validation
- Detailed verification of custom business logic
"""
    }

    @classmethod
    def get_generation_prompt(
        cls,
        gamp_category: GAMPCategory,
        urs_content: str,
        document_name: str,
        test_count: int,
        context_summary: str = ""
    ) -> str:
        """Generate complete prompt for OQ test generation."""

        category_config = GAMPCategoryConfig.get_category_config(gamp_category)
        category_prompt = cls.CATEGORY_SPECIFIC_PROMPTS.get(gamp_category, "")

        # Build comprehensive prompt
        prompt = f"""{cls.BASE_SYSTEM_PROMPT}

{category_prompt}

GENERATION PARAMETERS:
- GAMP Category: {gamp_category.value}
- Document: {document_name}
- Required Tests: {test_count}
- Focus Areas: {category_config['focus']}
- Validation Approach: {category_config['validation_approach']}
- Test Categories: {', '.join(category_config['test_categories'])}
- Complexity Level: {category_config['complexity']}

URS CONTENT:
{urs_content[:3000]}  # Reduced truncation for prompt size optimization

CONTEXT INFORMATION:
{context_summary if context_summary else 'Standard pharmaceutical validation approach recommended'}

SPECIFIC REQUIREMENTS:
1. Generate exactly {test_count} test cases within the range {category_config['min_tests']}-{category_config['max_tests']}
2. Each test must have a unique ID following the pattern OQ-XXX
3. Include at least {len(category_config['test_categories'])} different test categories
4. Ensure all tests are traceable to URS requirements
5. Include proper ALCOA+ compliance measures
6. Add appropriate regulatory references (21 CFR Part 11, GAMP-5, etc.)

CRITICAL: Respond with a complete OQTestSuite JSON object that passes all Pydantic validation."""

        return prompt


class TestCategoryTemplates:
    """Templates for specific test categories within OQ testing."""

    INSTALLATION_TESTS = {
        "template": {
            "test_category": "installation",
            "objective_template": "Verify proper installation and configuration of {system_name}",
            "common_steps": [
                "Verify system installation completed successfully",
                "Check all required components are installed",
                "Validate system configuration parameters",
                "Confirm database connectivity (if applicable)",
                "Verify system services are running properly"
            ],
            "acceptance_template": "All installation components verified and system operational"
        }
    }

    FUNCTIONAL_TESTS = {
        "template": {
            "test_category": "functional",
            "objective_template": "Validate core functional capabilities of {system_name}",
            "common_steps": [
                "Log in with validated user credentials",
                "Navigate to primary system functions",
                "Execute typical user workflows",
                "Verify data processing accuracy",
                "Confirm output generation and format"
            ],
            "acceptance_template": "All functional requirements met per specification"
        }
    }

    DATA_INTEGRITY_TESTS = {
        "template": {
            "test_category": "data_integrity",
            "objective_template": "Verify data integrity and audit trail capabilities",
            "common_steps": [
                "Create test data entries",
                "Verify audit trail capture",
                "Test data modification restrictions",
                "Validate electronic signature requirements",
                "Confirm backup and recovery procedures"
            ],
            "acceptance_template": "Data integrity maintained per ALCOA+ principles"
        }
    }

    SECURITY_TESTS = {
        "template": {
            "test_category": "security",
            "objective_template": "Validate security controls and access restrictions",
            "common_steps": [
                "Test user authentication mechanisms",
                "Verify role-based access controls",
                "Test session timeout functionality",
                "Validate password complexity requirements",
                "Confirm security audit logging"
            ],
            "acceptance_template": "Security controls function as designed"
        }
    }

    PERFORMANCE_TESTS = {
        "template": {
            "test_category": "performance",
            "objective_template": "Verify system performance under expected load conditions",
            "common_steps": [
                "Establish baseline performance metrics",
                "Execute standard operations under load",
                "Monitor system response times",
                "Validate resource utilization limits",
                "Confirm performance acceptance criteria"
            ],
            "acceptance_template": "Performance meets specified requirements"
        }
    }

    INTEGRATION_TESTS = {
        "template": {
            "test_category": "integration",
            "objective_template": "Validate integration with connected systems",
            "common_steps": [
                "Test data exchange with external systems",
                "Verify interface error handling",
                "Validate data format compatibility",
                "Test synchronization mechanisms",
                "Confirm transaction integrity"
            ],
            "acceptance_template": "Integration functions correctly with all connected systems"
        }
    }

    @classmethod
    def get_category_template(cls, category: str) -> dict[str, Any]:
        """Get template for specific test category."""
        templates = {
            "installation": cls.INSTALLATION_TESTS,
            "functional": cls.FUNCTIONAL_TESTS,
            "data_integrity": cls.DATA_INTEGRITY_TESTS,
            "security": cls.SECURITY_TESTS,
            "performance": cls.PERFORMANCE_TESTS,
            "integration": cls.INTEGRATION_TESTS
        }

        return templates.get(category, {}).get("template", {})


class ComplianceRequirements:
    """Pharmaceutical compliance requirements for OQ testing."""

    ALCOA_PLUS_REQUIREMENTS = [
        "Attributable: All actions traceable to specific users",
        "Legible: All test procedures clearly written and understandable",
        "Contemporaneous: Data captured at time of testing",
        "Original: Tests work with original data sources",
        "Accurate: Test procedures accurately reflect system functionality",
        "Complete: All required testing aspects covered",
        "Consistent: Test formats and procedures standardized",
        "Enduring: Test records preserved for regulatory timelines",
        "Available: Test documentation retrievable for inspection"
    ]

    CFR_PART_11_REQUIREMENTS = [
        "Electronic signature functionality validated",
        "Audit trail completeness and tamper-evidence verified",
        "User authentication and authorization controls tested",
        "Data backup and recovery procedures validated",
        "system security and access controls verified"
    ]

    GAMP5_REQUIREMENTS = [
        "Risk-based validation approach applied",
        "Supplier assessment completed where applicable",
        "Configuration management verified",
        "Change control procedures validated",
        "Documentation and traceability maintained"
    ]

    @classmethod
    def get_compliance_checklist(cls, gamp_category: GAMPCategory) -> list[str]:
        """Get compliance requirements for specific GAMP category."""
        base_requirements = cls.ALCOA_PLUS_REQUIREMENTS.copy()

        if gamp_category in [GAMPCategory.CATEGORY_4, GAMPCategory.CATEGORY_5]:
            base_requirements.extend(cls.CFR_PART_11_REQUIREMENTS)

        base_requirements.extend(cls.GAMP5_REQUIREMENTS)

        return base_requirements

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

    BASE_SYSTEM_PROMPT = """Generate {test_count} complete OQ test cases in JSON format for pharmaceutical validation.

You are an expert pharmaceutical validation engineer specializing in GAMP-5 OQ test generation.

CRITICAL REQUIREMENTS - ALL FIELDS MUST BE INCLUDED:
- Generate exactly {test_count} tests with unique IDs (OQ-001, OQ-002, etc.)
- MANDATORY SUITE FIELDS: suite_id, gamp_category, document_name, test_cases, total_test_count, estimated_execution_time
- MANDATORY TEST FIELDS: test_name, test_category, gamp_category, objective, prerequisites, test_steps, acceptance_criteria, estimated_duration_minutes
- CRITICAL: Each test case MUST include "gamp_category" field with the numeric GAMP category value
- CRITICAL: Each test case MUST include "estimated_duration_minutes" field with realistic execution time
- CRITICAL: Suite MUST include "estimated_execution_time" calculated as sum of all test execution times
- Minimum 3 detailed test steps per test
- Valid JSON format with proper structure

Pharmaceutical Compliance:
- GAMP-5 regulatory requirements
- ALCOA+ data integrity principles  
- 21 CFR Part 11 electronic records compliance
- Audit trail and traceability to URS requirements

Output valid JSON with proper structure and ALL required fields included."""

    CATEGORY_SPECIFIC_PROMPTS = {
        GAMPCategory.CATEGORY_1: """
GAMP Category 1: Infrastructure Software - Generate {test_count} tests

Focus Areas:
- Installation qualification verification
- Basic connectivity and communication
- System integration points
- Standard operational procedures
- Error handling for common scenarios

Each test requires:
- Streamlined procedures focusing on intended use
- Basic functional testing of core features
- Supplier documentation verification
- Clear acceptance criteria
""",

        GAMPCategory.CATEGORY_3: """
GAMP Category 3: Non-configured Products - Generate {test_count} tests

Focus Areas:
- Standard functionality verification
- Data input/output validation
- User interface testing
- Basic reporting capabilities
- Data integrity verification
- Standard workflow testing

Each test requires:
- Clear objective and test steps
- Detailed acceptance criteria
- Traceability to URS requirements
- ALCOA+ compliance measures
""",

        GAMPCategory.CATEGORY_4: """
GAMP Category 4: Configured Products - Generate {test_count} tests

Key Test Areas:
- Configuration parameter verification
- Business process workflow testing
- User role and permission validation
- Integration testing with other systems
- Performance testing under load
- Security and access control verification
- Data integrity and audit trail validation
- Deviation and error handling procedures

Each test must have:
- Comprehensive test steps (5-8 steps minimum)
- Clear acceptance criteria
- Risk assessment
- Traceability to URS requirements
""",

        GAMPCategory.CATEGORY_5: """
GAMP Category 5: Custom Applications - Generate {test_count} comprehensive tests

Core Test Areas (comprehensive coverage required):
- Installation and setup verification
- User authentication and authorization  
- Core functional testing (multiple feature sets)
- Data input validation and processing
- Algorithm and calculation verification
- Database operations and data integrity
- Integration testing with external systems
- Performance testing (normal and stress conditions)
- Security testing (access controls and data protection)
- Audit trail verification
- Error handling and recovery procedures
- User interface and usability testing
- Reporting functionality verification
- Data export and import testing
- Backup and recovery testing
- Boundary and edge case testing
- Negative testing scenarios
- Compliance verification (21 CFR Part 11)
- Full system integration testing
- User acceptance testing scenarios

Each test must contain:
- Detailed objective and prerequisites
- Comprehensive test steps (minimum 5 steps per test)
- Expected results for each step
- Clear acceptance criteria
- Risk level assignment
- URS requirements traceability
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
        """Generate OSS-optimized prompt for OQ test generation."""

        category_config = GAMPCategoryConfig.get_category_config(gamp_category)

        # Format the base system prompt with test count
        formatted_base_prompt = cls.BASE_SYSTEM_PROMPT.format(test_count=test_count)

        # Format the category-specific prompt with test count
        category_prompt_template = cls.CATEGORY_SPECIFIC_PROMPTS.get(gamp_category, "")
        formatted_category_prompt = category_prompt_template.format(test_count=test_count)

        # Create simple, direct example for OSS models
        example_test = cls._get_example_test_structure(gamp_category)

        # Build streamlined prompt
        prompt = f"""{formatted_base_prompt}

{formatted_category_prompt}

EXAMPLE TEST STRUCTURE:
{example_test}

JSON Requirements:
- GAMP Category: {gamp_category.value}
- Document: {document_name}
- Test Categories: {', '.join(category_config['test_categories'])}
- MANDATORY: Every test case must include "gamp_category": {gamp_category.value}
- Use proper JSON syntax with correct structure

URS Content:
{urs_content[:2500]}

Context: {context_summary if context_summary else 'Standard pharmaceutical validation approach recommended'}

Output Structure - INCLUDE ALL REQUIRED FIELDS:
{{
  "suite_id": "OQ-SUITE-{gamp_category.value:04d}",
  "gamp_category": {gamp_category.value},
  "document_name": "{document_name}",
  "test_cases": [
    // Each test case MUST include ALL these required fields:
    {{
      "test_id": "OQ-001",
      "test_name": "...",
      "test_category": "...",
      "gamp_category": {gamp_category.value},  // REQUIRED - numeric GAMP category
      "objective": "...",
      "prerequisites": [...],
      "test_steps": [...],
      "acceptance_criteria": [...],
      "estimated_duration_minutes": 45  // REQUIRED - realistic execution time in minutes
    }}
  ],
  "total_test_count": {test_count},
  "estimated_execution_time": 315  // REQUIRED - sum of all test execution times in minutes
}}

Return complete JSON document with proper formatting. Start with {{ and end with }}."""

        return prompt

    @classmethod
    def _get_example_test_structure(cls, gamp_category: GAMPCategory) -> str:
        """Get example test structure for OSS model guidance in JSON format."""
        return '''{
  "test_id": "OQ-001",
  "test_name": "Installation Verification Test",
  "test_category": "installation",
  "gamp_category": ''' + str(gamp_category.value) + ''',
  "objective": "Verify system installation completed successfully and all components are properly configured",
  "prerequisites": [
    "System hardware requirements verified",
    "Network connectivity established"
  ],
  "test_steps": [
    {
      "step_number": 1,
      "action": "Verify system installation completed without errors",
      "expected_result": "Installation log shows successful completion",
      "data_to_capture": [
        "Installation log",
        "System version"
      ],
      "verification_method": "visual_inspection"
    },
    {
      "step_number": 2,
      "action": "Check all required services are running",
      "expected_result": "All critical services show active status",
      "data_to_capture": [
        "Service status list"
      ],
      "verification_method": "system_query"
    },
    {
      "step_number": 3,
      "action": "Verify database connectivity and schema creation",
      "expected_result": "Database connection established and schema complete",
      "data_to_capture": [
        "Connection test results",
        "Schema validation"
      ],
      "verification_method": "automated_test"
    }
  ],
  "acceptance_criteria": [
    "Installation completed successfully",
    "All services operational",
    "Database accessible"
  ],
  "regulatory_basis": [
    "GAMP-5 Category ''' + str(gamp_category.value) + '''",
    "21 CFR Part 11"
  ],
  "risk_level": "medium",
  "urs_requirements": [
    "REQ-001: System Installation",
    "REQ-002: Component Verification"
  ],
  "estimated_duration_minutes": 45,  // REQUIRED - realistic execution time
  "required_expertise": [
    "System Administrator",
    "Validation Engineer"
  ]
}'''


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

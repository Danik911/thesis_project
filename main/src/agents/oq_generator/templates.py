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

    BASE_SYSTEM_PROMPT = """🚨 CRITICAL TEST COUNT REQUIREMENT 🚨
YOU MUST GENERATE EXACTLY {test_count} TESTS - NO MORE, NO LESS!

Count them as you generate: Test 1, Test 2, Test 3... up to Test {test_count}

You are an expert pharmaceutical validation engineer specializing in GAMP-5 OQ test generation.

PRIMARY TASK: Generate EXACTLY {test_count} complete OQ test cases in YAML format

MANDATORY REQUIREMENTS (NO EXCEPTIONS):
1. EXACTLY {test_count} tests - count each one as you create it
2. Each test must have ALL required fields filled out completely
3. Each test must have a unique ID: OQ-001, OQ-002, OQ-003, etc.
4. Each test must have detailed test steps (minimum 3 steps per test)
5. Each test must have clear acceptance criteria
6. Output must be valid YAML format with proper indentation

PHARMACEUTICAL COMPLIANCE:
- Follow GAMP-5 regulatory requirements
- Include ALCOA+ data integrity principles
- Ensure 21 CFR Part 11 electronic records compliance
- Maintain proper audit trail requirements
- Include traceability to URS requirements

CRITICAL SUCCESS CRITERIA:
✅ Generate ALL {test_count} tests (not 1, not 2, not 10 - exactly {test_count})
✅ Fill out ALL required fields for each test
✅ Use proper YAML structure with correct indentation and quotes
✅ Include unique test IDs for each test
✅ Make tests executable and verifiable

REMEMBER: You must generate exactly {test_count} complete tests in YAML format. This is not negotiable."""

    CATEGORY_SPECIFIC_PROMPTS = {
        GAMPCategory.CATEGORY_1: """
🎯 GAMP Category 1: INFRASTRUCTURE SOFTWARE VALIDATION
🎯 REQUIRED TESTS: {test_count} (YOU MUST GENERATE ALL {test_count} TESTS)

GENERATION INSTRUCTIONS:
1. Create Test 1: Installation qualification verification
2. Create Test 2: Basic connectivity and communication testing
3. Create Test 3: System integration points verification
4. Create Test 4: Standard operational procedures validation
5. Create Test 5: Error handling for common scenarios (if {test_count} = 5)

FOCUS AREAS FOR EACH TEST:
- Installation qualification verification
- Basic connectivity and communication
- System integration points
- Standard operational procedures
- Error handling for common scenarios

TEST REQUIREMENTS FOR EACH:
- Unique test ID (OQ-001, OQ-002, etc.)
- Streamlined procedures focusing on intended use
- Basic functional testing of core features
- Supplier documentation verification
- Clear acceptance criteria

CRITICAL: Generate ALL {test_count} tests for Category 1!
""",

        GAMPCategory.CATEGORY_3: """
🎯 GAMP Category 3: NON-CONFIGURED PRODUCTS VALIDATION
🎯 REQUIRED TESTS: {test_count} (YOU MUST GENERATE ALL {test_count} TESTS)

GENERATION INSTRUCTIONS:
1. Create Test 1: Installation verification
2. Create Test 2: Basic functionality verification  
3. Create Test 3: Data input/output validation
4. Create Test 4: User interface testing
5. Create Test 5: Data integrity verification
6. Continue until you have created ALL {test_count} tests

FOCUS AREAS FOR EACH TEST:
- Standard functionality verification
- Data input/output validation
- User interface testing
- Basic reporting capabilities
- Data integrity verification
- Standard workflow testing

TEST REQUIREMENTS FOR EACH:
- Unique test ID (OQ-001, OQ-002, etc.)
- Clear objective and test steps
- Detailed acceptance criteria
- Traceability to URS requirements
- ALCOA+ compliance measures

CRITICAL: Generate ALL {test_count} tests - not less, not more!
""",

        GAMPCategory.CATEGORY_4: """
🎯 GAMP Category 4: CONFIGURED PRODUCTS VALIDATION  
🎯 REQUIRED TESTS: {test_count} (YOU MUST GENERATE ALL {test_count} TESTS)

GENERATION INSTRUCTIONS (Generate tests in this order):
1. Create Test 1: Installation and configuration verification
2. Create Test 2: Configuration parameter verification
3. Create Test 3: User role and permission validation
4. Create Test 4: Business process workflow testing
5. Create Test 5: Integration testing with other systems
6. Create Test 6: Performance testing under load
7. Create Test 7: Security and access control verification
8. Create Test 8: Data integrity validation
9. Create Test 9: Audit trail validation
10. Create Test 10: Deviation and error handling
11. Continue with additional tests until you reach {test_count} tests

KEY TEST AREAS TO COVER:
- Configuration parameter verification
- Business process workflow testing
- User role and permission validation
- Integration testing with other systems
- Performance testing under load
- Security and access control verification
- Data integrity and audit trail validation
- Deviation and error handling procedures

EACH TEST MUST HAVE:
- Unique test ID (OQ-001, OQ-002, etc.)
- Comprehensive test steps (5-8 steps minimum)
- Clear acceptance criteria
- Risk assessment
- Traceability to URS requirements

CRITICAL: Generate ALL {test_count} tests - you must count to ensure completeness!
""",

        GAMPCategory.CATEGORY_5: """
🚨🚨🚨 GAMP Category 5: CUSTOM APPLICATIONS VALIDATION 🚨🚨🚨
🚨 CRITICAL: YOU MUST GENERATE EXACTLY {test_count} TESTS 🚨
🚨 THIS IS THE MOST COMPLEX CATEGORY - ALL {test_count} TESTS REQUIRED! 🚨

MANDATORY GENERATION SEQUENCE (Follow this exact order):
1. Test 1: Installation and setup verification  
2. Test 2: User authentication and authorization
3. Test 3: Core functional testing - Feature Set 1
4. Test 4: Core functional testing - Feature Set 2  
5. Test 5: Data input validation and processing
6. Test 6: Algorithm and calculation verification
7. Test 7: Database operations and data integrity
8. Test 8: Integration testing - External System 1
9. Test 9: Integration testing - External System 2
10. Test 10: Performance testing under normal load
11. Test 11: Performance testing under stress conditions
12. Test 12: Security testing - Access controls
13. Test 13: Security testing - Data protection
14. Test 14: Audit trail verification
15. Test 15: Error handling and recovery procedures
16. Test 16: User interface and usability testing
17. Test 17: Reporting functionality verification
18. Test 18: Data export and import testing
19. Test 19: Backup and recovery testing  
20. Test 20: Boundary and edge case testing
21. Test 21: Negative testing scenarios
22. Test 22: Compliance verification (21 CFR Part 11)
23. Test 23: Full system integration testing
24. Test 24: User acceptance testing scenarios
25. Test 25: Final validation and sign-off testing
... Continue numbering until you reach Test {test_count}

EACH TEST MUST CONTAIN:
- Unique test ID: OQ-001, OQ-002, etc.
- Detailed objective (what exactly is being tested)
- Prerequisites (what must be done before the test)
- Comprehensive test steps (minimum 5 steps per test)
- Expected results for each step
- Clear acceptance criteria
- Risk level assignment
- URS requirements traceability

🚨 ABSOLUTE REQUIREMENT 🚨
You MUST generate ALL {test_count} tests. Count as you go: 
- "Test 1 complete"
- "Test 2 complete" 
- "Test 3 complete"
... continue until "Test {test_count} complete"

DO NOT STOP until you have generated ALL {test_count} tests!
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

        # Build OSS-optimized prompt with clear structure
        prompt = f"""{formatted_base_prompt}

{formatted_category_prompt}

📋 EXAMPLE TEST STRUCTURE (Follow this YAML format for ALL {test_count} tests):
{example_test}

🎯 YAML GENERATION REQUIREMENTS:
✅ GAMP Category: {gamp_category.value} 
✅ Document: {document_name}
✅ REQUIRED TESTS: {test_count} (Generate ALL of them!)
✅ Test Categories Required: {', '.join(category_config['test_categories'])}
✅ Use proper YAML syntax with correct indentation (2 spaces)
✅ Quote all string values consistently

📄 URS CONTENT TO USE:
{urs_content[:2500]}

📊 CONTEXT INFORMATION:
{context_summary if context_summary else 'Standard pharmaceutical validation approach recommended'}

🚨 YAML GENERATION INSTRUCTIONS:
1. Start with suite_id: "OQ-SUITE-{gamp_category.value:04d}"
2. Set gamp_category: {gamp_category.value}
3. Set document_name: "{document_name}"
4. Create test_cases array with {test_count} tests
5. Generate Test 1 with test_id: "OQ-001"
6. Generate Test 2 with test_id: "OQ-002" 
7. Generate Test 3 with test_id: "OQ-003"
8. Continue until Test {test_count} with test_id: "OQ-{test_count:03d}"
9. Set total_test_count: {test_count}
10. Include all required metadata fields

🔍 YAML VALIDATION CHECKLIST (Verify before responding):
□ Generated exactly {test_count} tests?
□ Each test has unique test_id (OQ-001, OQ-002, etc.)?
□ Each test has all required fields?
□ Proper YAML indentation (2 spaces)?
□ All strings properly quoted?
□ All test categories represented?

🚨 CRITICAL REMINDER: Generate exactly {test_count} complete tests - no more, no less!

Return your response as a complete YAML document with proper formatting and indentation."""

        return prompt
    
    @classmethod
    def _get_example_test_structure(cls, gamp_category: GAMPCategory) -> str:
        """Get example test structure for OSS model guidance in YAML format."""
        return '''test_id: "OQ-001"
test_name: "Installation Verification Test"
test_category: "installation"
gamp_category: ''' + str(gamp_category.value) + '''
objective: "Verify system installation completed successfully and all components are properly configured"
prerequisites:
  - "System hardware requirements verified"
  - "Network connectivity established"
test_steps:
  - step_number: 1
    action: "Verify system installation completed without errors"
    expected_result: "Installation log shows successful completion"
    data_to_capture:
      - "Installation log"
      - "System version"
    verification_method: "visual_inspection"
  - step_number: 2
    action: "Check all required services are running"
    expected_result: "All critical services show active status"
    data_to_capture:
      - "Service status list"
    verification_method: "system_query"
  - step_number: 3
    action: "Verify database connectivity and schema creation"
    expected_result: "Database connection established and schema complete"
    data_to_capture:
      - "Connection test results"
      - "Schema validation"
    verification_method: "automated_test"
acceptance_criteria:
  - "Installation completed successfully"
  - "All services operational"
  - "Database accessible"
regulatory_basis:
  - "GAMP-5 Category ''' + str(gamp_category.value) + '''"
  - "21 CFR Part 11"
risk_level: "medium"
urs_requirements:
  - "REQ-001: System Installation"
  - "REQ-002: Component Verification"
estimated_duration_minutes: 45
required_expertise:
  - "System Administrator"
  - "Validation Engineer"'''


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

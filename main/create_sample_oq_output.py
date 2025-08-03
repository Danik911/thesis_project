#!/usr/bin/env python3
"""Create a sample OQ test suite output to demonstrate the expected format"""
import json
from pathlib import Path
from datetime import datetime
import uuid

# Create output directory
output_dir = Path("output/test_suites")
output_dir.mkdir(parents=True, exist_ok=True)

# Create sample OQ test suite
test_suite = {
    "metadata": {
        "generated_at": datetime.now().isoformat(),
        "suite_id": f"OQ_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "gamp_category": 5,
        "total_test_count": 3,
        "file_version": "1.0",
        "compliance_standards": ["GAMP-5", "ALCOA+", "21 CFR Part 11"],
        "generator_version": "OQTestGenerationWorkflow v1.0"
    },
    "test_suite": {
        "suite_id": f"OQ_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "suite_name": "GAMP Category 5 - Operational Qualification Test Suite",
        "gamp_category": 5,
        "tests": [
            {
                "test_id": f"OQ-{str(uuid.uuid4())[:8]}",
                "test_name": "User Authentication and Access Control Verification",
                "test_category": "Security",
                "test_type": "functional",
                "priority": "critical",
                "description": "Verify that the system enforces proper user authentication and role-based access control as per 21 CFR Part 11 requirements",
                "objective": "Ensure only authorized users can access the system and perform actions within their assigned privileges",
                "prerequisites": [
                    "Test environment configured with test user accounts",
                    "User roles and permissions matrix defined",
                    "System in operational state"
                ],
                "test_steps": [
                    {
                        "step_number": 1,
                        "description": "Attempt to access system without credentials",
                        "expected_result": "System displays login screen and denies access",
                        "data_capture_required": True
                    },
                    {
                        "step_number": 2,
                        "description": "Login with valid administrator credentials",
                        "expected_result": "System grants access and displays administrator dashboard",
                        "data_capture_required": True
                    },
                    {
                        "step_number": 3,
                        "description": "Verify audit trail captures login event",
                        "expected_result": "Audit log shows timestamp, user ID, and successful login action",
                        "data_capture_required": True
                    }
                ],
                "expected_results": "System enforces authentication and maintains compliant audit trail",
                "acceptance_criteria": "All access attempts are properly authenticated and logged",
                "regulatory_references": ["21 CFR Part 11.10(d)", "21 CFR Part 11.300(b)"],
                "gamp5_alignment": "Addresses GAMP 5 Category 5 requirements for configurable software",
                "estimated_duration": "45 minutes",
                "data_recording_requirements": "Screenshot evidence and audit log extracts required"
            },
            {
                "test_id": f"OQ-{str(uuid.uuid4())[:8]}",
                "test_name": "Data Integrity and ALCOA+ Compliance Verification",
                "test_category": "Data Integrity",
                "test_type": "functional",
                "priority": "critical",
                "description": "Verify system maintains data integrity according to ALCOA+ principles throughout data lifecycle",
                "objective": "Ensure data remains Attributable, Legible, Contemporaneous, Original, and Accurate",
                "prerequisites": [
                    "Test data sets prepared",
                    "Data integrity procedures documented",
                    "System operational with audit trail enabled"
                ],
                "test_steps": [
                    {
                        "step_number": 1,
                        "description": "Create new data record with all required fields",
                        "expected_result": "System captures user identity, timestamp, and data values",
                        "data_capture_required": True
                    },
                    {
                        "step_number": 2,
                        "description": "Attempt to modify data record",
                        "expected_result": "System maintains original value and records change with reason",
                        "data_capture_required": True
                    },
                    {
                        "step_number": 3,
                        "description": "Export data and verify completeness",
                        "expected_result": "Exported data includes all metadata and audit trail",
                        "data_capture_required": True
                    }
                ],
                "expected_results": "Data integrity maintained throughout all operations",
                "acceptance_criteria": "ALCOA+ principles demonstrably enforced",
                "regulatory_references": ["FDA Data Integrity Guidance", "EU Annex 11"],
                "gamp5_alignment": "Critical quality attribute for Category 5 systems",
                "estimated_duration": "60 minutes",
                "data_recording_requirements": "Complete audit trail extracts and data lifecycle documentation"
            },
            {
                "test_id": f"OQ-{str(uuid.uuid4())[:8]}",
                "test_name": "Electronic Signature Functionality Verification",
                "test_category": "Compliance",
                "test_type": "functional",
                "priority": "high",
                "description": "Verify electronic signature functionality meets 21 CFR Part 11 Subpart C requirements",
                "objective": "Ensure electronic signatures are linked to records and include required components",
                "prerequisites": [
                    "E-signature functionality enabled",
                    "Test users with signature privileges configured",
                    "Test records requiring signatures prepared"
                ],
                "test_steps": [
                    {
                        "step_number": 1,
                        "description": "Attempt to sign record with invalid credentials",
                        "expected_result": "System rejects signature attempt and logs security event",
                        "data_capture_required": True
                    },
                    {
                        "step_number": 2,
                        "description": "Sign record with valid credentials",
                        "expected_result": "System captures signature with user ID, timestamp, and meaning",
                        "data_capture_required": True
                    },
                    {
                        "step_number": 3,
                        "description": "Verify signature cannot be removed or altered",
                        "expected_result": "Signature permanently linked to record",
                        "data_capture_required": True
                    }
                ],
                "expected_results": "Electronic signatures meet all regulatory requirements",
                "acceptance_criteria": "Signatures are secure, attributable, and permanent",
                "regulatory_references": ["21 CFR Part 11.50", "21 CFR Part 11.70", "21 CFR Part 11.200"],
                "gamp5_alignment": "Essential control for Category 5 validated systems",
                "estimated_duration": "30 minutes",
                "data_recording_requirements": "Signed records and signature manifestation evidence"
            }
        ],
        "total_test_count": 3,
        "estimated_total_duration": "135 minutes",
        "coverage_percentage": 85.0,
        "created_at": datetime.now().isoformat(),
        "created_by": "OQTestGenerationWorkflow",
        "review_required": True,
        "pharmaceutical_compliance": {
            "gamp5_compliant": True,
            "cfr_part_11_addressed": True,
            "eu_annex_11_addressed": True,
            "data_integrity_focus": True,
            "risk_based_approach": True
        },
        "test_environment_requirements": {
            "system_state": "Operational Qualification phase",
            "test_data": "Validated test data sets required",
            "user_accounts": "Test accounts with various privilege levels",
            "external_systems": "Interfaces in test mode"
        },
        "execution_instructions": {
            "prerequisites_verification": "Verify all prerequisites before starting each test",
            "evidence_collection": "Capture screenshots and system outputs as specified",
            "deviation_handling": "Document any deviations with justification",
            "approval_required": "QA approval required before execution"
        }
    },
    "audit_trail": {
        "created_by": "OQTestGenerationWorkflow",
        "creation_timestamp": datetime.now().isoformat(),
        "validation_status": "generated",
        "review_required": True,
        "pharmaceutical_compliance": {
            "gamp5_compliant": True,
            "cfr_part_11_addressed": True,
            "eu_annex_11_addressed": True
        }
    }
}

# Save to file
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"test_suite_OQ_{timestamp}_SAMPLE.json"
output_file = output_dir / filename

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(test_suite, f, indent=2, ensure_ascii=False)

print(f"Sample OQ Test Suite created successfully!")
print(f"File: {output_file}")
print(f"Size: {output_file.stat().st_size:,} bytes")
print(f"\nThis demonstrates the expected output format from the OQ Generator.")
print(f"The file contains {len(test_suite['test_suite']['tests'])} complete OQ test cases.")
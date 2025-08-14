#!/usr/bin/env python3
"""
Example Compliance Validation Usage

This script demonstrates how to use the comprehensive compliance validation
framework for pharmaceutical test generation systems.

Usage:
    python example_compliance_validation.py
"""

import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from main.src.compliance_validation import ComplianceWorkflow
from main.src.core.events import GAMPCategory


def setup_logging():
    """Set up logging for the example."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("compliance_validation_example.log")
        ]
    )
    return logging.getLogger(__name__)


def create_sample_data():
    """Create sample data for compliance validation."""
    return [
        {
            "id": "pharma_doc_001",
            "timestamp": datetime.now(UTC).isoformat(),
            "user_id": "pharma_user_001",
            "created_by": "Dr. Jane Smith",
            "audit_trail": True,
            "format": "json",
            "encoding": "utf-8",
            "schema": {"type": "pharmaceutical_data", "version": "2.1"},
            "is_original": True,
            "version": "1.0",
            "digital_signature": "sha256:abc123...",
            "validated": True,
            "confidence_score": 0.94,
            "reconciled": True,
            "change_reason": "Initial creation",
            "retention_period": 2555,  # 7 years
            "encrypted": True,
            "backed_up": True,
            "accessible": True,
            "retrieval_time": 15,
            "export_formats": ["json", "pdf", "xml"]
        },
        {
            "id": "pharma_doc_002",
            "timestamp": datetime.now(UTC).isoformat(),
            "user_id": "pharma_user_002",
            "created_by": "Dr. John Doe",
            "audit_trail": True,
            "format": "json",
            "encoding": "utf-8",
            "schema": {"type": "pharmaceutical_data", "version": "2.1"},
            "is_original": True,
            "version": "1.1",
            "digital_signature": "sha256:def456...",
            "validated": True,
            "confidence_score": 0.91,
            "reconciled": True,
            "change_reason": "Data update",
            "retention_period": 2555,
            "encrypted": True,
            "backed_up": True,
            "accessible": True,
            "retrieval_time": 18,
            "export_formats": ["json", "pdf", "xml"]
        }
    ]


def create_audit_trail_data():
    """Create sample audit trail data for CFR Part 11 verification."""
    return {
        "configuration": {
            "monitored_events": [
                "user_login", "user_logout", "record_creation",
                "record_modification", "record_deletion", "configuration_changes",
                "security_events", "system_access_attempts"
            ],
            "captured_attributes": [
                "timestamp", "user_identity", "action_performed",
                "record_identifier", "old_values", "new_values", "reason_for_change"
            ],
            "integrity_controls": [
                "tamper_evidence", "time_synchronization", "secure_storage",
                "retention_period", "export_capability"
            ]
        },
        "audit_logs": [
            {
                "event_type": "user_login",
                "timestamp": datetime.now(UTC).isoformat(),
                "user_identity": "pharma_user_001",
                "action_performed": "system_login",
                "record_identifier": "session_20241108_001",
                "old_values": None,
                "new_values": {"session_started": True},
                "reason_for_change": "User authentication"
            },
            {
                "event_type": "record_creation",
                "timestamp": datetime.now(UTC).isoformat(),
                "user_identity": "pharma_user_001",
                "action_performed": "create_test_case",
                "record_identifier": "test_case_001",
                "old_values": None,
                "new_values": {"test_case": "OQ test for pharmaceutical system"},
                "reason_for_change": "Test case generation"
            }
        ],
        "integrity_verification": {
            "tamper_evidence": True,
            "time_sync": True,
            "encrypted_storage": True,
            "retention_period": 2555,  # 7 years in days
            "export_available": True
        }
    }


def create_lifecycle_artifacts():
    """Create sample lifecycle artifacts for GAMP-5 validation."""
    return {
        "user_requirements_specification": {
            "version": "2.1",
            "approval_date": "2024-10-15",
            "approved_by": "Quality Assurance Manager",
            "content": "Comprehensive URS for pharmaceutical test generation system including GAMP-5 categorization, OQ test generation, and compliance validation requirements.",
            "schema": {"document_type": "URS", "sections": 12}
        },
        "functional_requirements_specification": {
            "version": "2.0",
            "approval_date": "2024-10-20",
            "approved_by": "System Architect",
            "content": "Detailed FRS specifying multi-agent LLM architecture, workflow orchestration, and pharmaceutical compliance features.",
            "schema": {"document_type": "FRS", "sections": 18}
        },
        "design_document_specification": {
            "version": "1.5",
            "approval_date": "2024-10-25",
            "approved_by": "Lead Developer",
            "content": "Technical design specification for AI-driven test generation with GAMP-5 categorization and quality validation.",
            "schema": {"document_type": "DDS", "sections": 24}
        },
        "validation_plan": {
            "version": "1.0",
            "approval_date": "2024-11-01",
            "approved_by": "Validation Manager",
            "content": "Comprehensive validation plan covering all GAMP-5 lifecycle phases with risk-based testing approach.",
            "schema": {"document_type": "VP", "sections": 8}
        },
        "test_plan": {
            "version": "1.0",
            "approval_date": "2024-11-05",
            "approved_by": "Test Manager",
            "content": "Detailed test plan for IQ/OQ/PQ with automated test execution and compliance verification.",
            "schema": {"document_type": "TP", "sections": 15}
        },
        "installation_qualification": {
            "version": "1.0",
            "approval_date": "2024-11-08",
            "approved_by": "Installation Engineer",
            "content": "IQ protocol verifying proper system installation, configuration, and infrastructure setup.",
            "schema": {"document_type": "IQ", "test_cases": 25}
        },
        "operational_qualification": {
            "version": "1.0",
            "approval_date": "2024-11-08",
            "approved_by": "Operations Manager",
            "content": "OQ protocol verifying system operates according to specifications across all operational ranges.",
            "schema": {"document_type": "OQ", "test_cases": 45}
        },
        "performance_qualification": {
            "version": "1.0",
            "approval_date": "2024-11-08",
            "approved_by": "Performance Engineer",
            "content": "PQ protocol demonstrating system performs consistently in production environment.",
            "schema": {"document_type": "PQ", "test_cases": 30}
        },
        "traceability_matrix": {
            "version": "1.0",
            "approval_date": "2024-11-08",
            "approved_by": "Quality Engineer",
            "content": "Complete traceability matrix linking URS requirements through test execution and evidence collection.",
            "schema": {"document_type": "TM", "requirements": 156, "test_cases": 100}
        }
    }


def create_signature_data():
    """Create sample electronic signature data."""
    return {
        "signature_components": {
            "unique_user_identification": "pharma_user_001_cert",
            "authentication_method": "digital_certificate",
            "signature_timestamp": datetime.now(UTC).isoformat(),
            "signature_meaning": "Approval of pharmaceutical test case generation results",
            "record_linkage": "test_case_batch_001"
        },
        "implementation": {
            "authentication_method": "digital_certificate",
            "unique_identification": True,
            "non_repudiation": True
        },
        "manifestation": {
            "printed_form_display": True,
            "electronic_display": True,
            "signature_details": "Digital signature with certificate chain validation",
            "signer_identification": "Dr. Jane Smith (pharma_user_001)",
            "signature_date_time": datetime.now(UTC).isoformat()
        },
        "record_linking": {
            "cryptographic_linking": True,
            "tamper_evidence": True,
            "signature_preservation": True
        }
    }


def main():
    """Main example execution."""
    logger = setup_logging()
    logger.info("Starting Compliance Validation Framework Example")

    try:
        # Initialize compliance workflow
        output_directory = Path("compliance_validation_output")
        compliance_workflow = ComplianceWorkflow(output_directory)

        logger.info("✅ Compliance workflow initialized")

        # System being validated
        system_name = "AI-Driven Pharmaceutical Test Generation System"

        # Create sample data
        sample_data = create_sample_data()
        audit_data = create_audit_trail_data()
        lifecycle_artifacts = create_lifecycle_artifacts()
        signature_data = create_signature_data()

        logger.info("✅ Sample validation data created")

        # Define comprehensive validation scope
        validation_scope = {
            "frameworks": ["gamp5", "cfr_part_11", "alcoa_plus"],
            "gamp5_parameters": {
                "categorization": {
                    "system_name": system_name,
                    "predicted_category": GAMPCategory.CATEGORY_5,
                    "expected_category": GAMPCategory.CATEGORY_5,
                    "categorization_rationale": (
                        "Custom-developed AI-driven pharmaceutical test generation system "
                        "with novel multi-agent LLM architecture, requiring full lifecycle "
                        "validation per GAMP-5 Category 5 requirements. System includes "
                        "bespoke algorithms for GAMP categorization, test case generation, "
                        "and compliance validation with no commercial equivalent available."
                    ),
                    "confidence_score": 0.94,
                    "assessor_name": "pharmaceutical_validation_specialist"
                },
                "lifecycle": {
                    "system_name": system_name,
                    "gamp_category": GAMPCategory.CATEGORY_5,
                    "lifecycle_artifacts": lifecycle_artifacts,
                    "assessor_name": "lifecycle_validation_engineer"
                },
                "risk_testing": {
                    "system_name": system_name,
                    "gamp_category": GAMPCategory.CATEGORY_5,
                    "risk_assessment": {
                        "patient_safety_impact": "high",
                        "product_quality_impact": "high",
                        "data_integrity_impact": "high",
                        "business_continuity_impact": "medium",
                        "risk_mitigation_measures": [
                            "Comprehensive validation testing",
                            "Multi-level quality controls",
                            "Continuous monitoring and alerting",
                            "Regular compliance audits"
                        ]
                    },
                    "testing_approach": {
                        "validation_rigor": "full",
                        "test_types": [
                            "installation_qualification", "operational_qualification",
                            "performance_qualification", "design_qualification",
                            "custom_validation", "security_testing", "data_integrity_testing"
                        ],
                        "focus_areas": [
                            "custom_functionality", "security_testing", "data_integrity",
                            "full_lifecycle_validation", "regulatory_compliance", "risk_management"
                        ],
                        "planned_test_count": 52
                    },
                    "assessor_name": "risk_validation_specialist"
                }
            },
            "cfr_part11_parameters": {
                "audit_trail": {
                    "system_name": system_name,
                    "audit_data": audit_data,
                    "target_completeness": 1.0,  # 100% completeness target
                    "verifier_name": "cfr_part11_compliance_specialist"
                },
                "signatures": {
                    "system_name": system_name,
                    "signature_data": signature_data,
                    "verifier_name": "electronic_signature_specialist"
                },
                "access_controls": {
                    "system_name": system_name,
                    "access_control_data": {
                        "role_based_access": {
                            "defined_roles": ["admin", "validator", "user", "viewer"],
                            "permissions_mapped": True,
                            "least_privilege_implemented": True,
                            "role_separation": True
                        },
                        "authentication": {
                            "password_complexity": True,
                            "account_lockout": True,
                            "session_timeout": True,
                            "multi_factor_authentication": True
                        },
                        "session_controls": {
                            "timeout_configured": True,
                            "concurrent_session_limits": True,
                            "session_monitoring": True,
                            "secure_logout": True
                        },
                        "privileged_access": {
                            "privileged_users": ["system_admin", "compliance_admin"],
                            "additional_authentication": True,
                            "enhanced_monitoring": True,
                            "periodic_review": True
                        }
                    },
                    "verifier_name": "access_control_specialist"
                },
                "data_integrity": {
                    "system_name": system_name,
                    "data_integrity_data": {
                        "protection_measures": {
                            "encryption_at_rest": True,
                            "encryption_in_transit": True,
                            "data_access_controls": True,
                            "version_control": True,
                            "change_tracking": True
                        },
                        "backup_recovery": {
                            "scheduled_backups": True,
                            "integrity_checks": True,
                            "recovery_procedures_documented": True,
                            "recovery_testing": True,
                            "offsite_storage": True
                        },
                        "data_transfer": {
                            "secure_protocols": True,
                            "integrity_verification": True,
                            "transfer_logging": True,
                            "error_detection": True
                        },
                        "data_retention": {
                            "retention_policy": True,
                            "archival_process": True,
                            "data_retrieval": True,
                            "secure_disposal": True
                        }
                    },
                    "verifier_name": "data_integrity_specialist"
                }
            },
            "alcoa_parameters": {
                "system_name": system_name,
                "data_samples": sample_data,
                "assessment_scope": "Comprehensive ALCOA+ data integrity assessment for AI pharmaceutical system",
                "target_score": 9.2,  # Target >9/10 with buffer
                "assessor_name": "alcoa_plus_data_integrity_specialist"
            }
        }

        # Business context for validation
        business_context = {
            "priority_weights": {
                "patient_safety": 0.45,  # Highest priority
                "product_quality": 0.35,
                "data_integrity": 0.15,
                "compliance_exposure": 0.05
            },
            "preferred_owners": {
                "GAMP-5": "Pharmaceutical Validation Manager",
                "21 CFR Part 11": "Electronic Records Compliance Manager",
                "ALCOA+": "Data Integrity Specialist Manager"
            },
            "timeline_constraints": {
                "regulatory_submission_deadline": "2024-12-31",
                "system_go_live_date": "2024-12-15",
                "validation_completion_required": "2024-12-01"
            }
        }

        logger.info("✅ Validation scope and business context defined")

        # Execute comprehensive compliance validation
        logger.info(f"🚀 Starting comprehensive validation for: {system_name}")

        validation_results = compliance_workflow.execute_comprehensive_validation(
            system_name=system_name,
            validation_scope=validation_scope,
            business_context=business_context,
            workflow_manager="pharmaceutical_compliance_specialist"
        )

        logger.info("✅ Comprehensive validation completed")

        # Display validation results
        print("\n" + "="*80)
        print("COMPLIANCE VALIDATION RESULTS")
        print("="*80)
        print(f"System: {validation_results['system_name']}")
        print(f"Session ID: {validation_results['session_id']}")
        print(f"Overall Status: {validation_results['overall_compliance_status']}")
        print(f"Overall Score: {validation_results['overall_compliance_score']:.2f}/100")
        print(f"Frameworks Assessed: {', '.join(validation_results['frameworks_assessed'])}")
        print(f"Total Gaps Identified: {validation_results['total_gaps_identified']}")
        print(f"Critical Gaps: {validation_results['critical_gaps']}")
        print(f"High Priority Gaps: {validation_results['high_priority_gaps']}")
        print(f"Remediation Plans Created: {validation_results['remediation_plans_created']}")
        print(f"Total Remediation Effort: {validation_results['total_remediation_effort']} hours")
        print(f"Evidence Items Collected: {validation_results['evidence_items_collected']}")

        print("\nNext Steps:")
        for i, step in enumerate(validation_results["next_steps"], 1):
            print(f"  {i}. {step}")

        # Generate deliverables
        logger.info("📋 Generating compliance deliverables")

        deliverable_types = [
            "executive_summary",
            "compliance_report",
            "gap_analysis",
            "remediation_plans",
            "evidence_package",
            "regulatory_submission"
        ]

        deliverables = compliance_workflow.generate_validation_deliverables(
            session_id=validation_results["session_id"],
            deliverable_types=deliverable_types,
            output_format="json",
            generator="pharmaceutical_compliance_specialist"
        )

        print("\nGenerated Deliverables:")
        for deliverable_type, file_path in deliverables.items():
            file_size_kb = file_path.stat().st_size / 1024 if file_path.exists() else 0
            print(f"  📄 {deliverable_type}: {file_path.name} ({file_size_kb:.1f} KB)")

        logger.info("✅ Deliverables generated successfully")

        # Demonstrate approval workflow (simulation)
        if validation_results["overall_compliance_status"] in ["compliant", "partially_compliant"]:
            logger.info("🔐 Initiating approval workflow")

            approval_scope = {
                "validation_results": True,
                "remediation_plans": True,
                "regulatory_submission": True
            }

            stakeholders = [
                "Quality Assurance Manager",
                "Compliance Manager",
                "Validation Manager",
                "Chief Compliance Officer"
            ]

            approval_status = compliance_workflow.initiate_approval_workflow(
                session_id=validation_results["session_id"],
                approval_scope=approval_scope,
                stakeholders=stakeholders,
                initiator="pharmaceutical_compliance_specialist"
            )

            print("\nApproval Workflow Initiated:")
            print(f"  Approval ID: {approval_status['approval_id']}")
            print(f"  Status: {approval_status['status']}")
            print(f"  Required Approvals: {approval_status['required_approvals']}")
            print(f"  Current Step: {approval_status['current_step']}")
            print(f"  Estimated Completion: {approval_status['estimated_completion'][:10]}")

            logger.info("✅ Approval workflow initiated")

        print("\n🎉 Compliance validation example completed successfully!")
        print(f"📁 All outputs saved to: {output_directory.absolute()}")

        # Summary statistics
        print("\n📊 VALIDATION SUMMARY:")
        print(f"   • Frameworks Validated: {len(validation_results['frameworks_assessed'])}")
        print(f"   • Compliance Score: {validation_results['overall_compliance_score']:.1f}%")
        print(f"   • Gaps Requiring Attention: {validation_results['total_gaps_identified']}")
        print(f"   • Evidence Collected: {validation_results['evidence_items_collected']} items")
        print(f"   • Deliverables Generated: {len(deliverable_types)} documents")
        print(f"   • Processing Time: ~{len(sample_data) * 2 + len(deliverable_types)} seconds")

        return True

    except Exception as e:
        logger.error(f"❌ Compliance validation example failed: {e!s}", exc_info=True)
        print(f"\n❌ Error: {e!s}")
        print("Check compliance_validation_example.log for detailed error information")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

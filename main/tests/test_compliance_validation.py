"""
Test Suite for Compliance Validation Framework

This module provides comprehensive tests for the compliance validation framework
including unit tests, integration tests, and end-to-end validation scenarios.

Key Test Coverage:
- GAMP-5 compliance assessment
- 21 CFR Part 11 verification
- ALCOA+ data integrity scoring
- Gap analysis and remediation planning
- Evidence collection and traceability
- Workflow orchestration
"""

import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from src.compliance_validation.models import (
    ComplianceFramework,
    ComplianceStatus,
    Evidence,
    EvidenceType,
    Gap,
    GapSeverity,
    ValidationTemplate
)
from src.compliance_validation.evidence_collector import EvidenceCollector
from src.compliance_validation.gamp5_assessor import GAMP5Assessor
from src.compliance_validation.cfr_part11_verifier import CFRPart11Verifier
from src.compliance_validation.alcoa_scorer import ALCOAScorer
from src.compliance_validation.gap_analyzer import GapAnalyzer
from src.compliance_validation.remediation_planner import RemediationPlanner
from src.compliance_validation.compliance_workflow import ComplianceWorkflow
from src.core.events import GAMPCategory


class TestComplianceValidationFramework(unittest.TestCase):
    """Test suite for compliance validation framework."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_system_name = "Test Pharmaceutical System"
        
        # Initialize components
        self.evidence_collector = EvidenceCollector(self.temp_dir / "evidence")
        self.gamp5_assessor = GAMP5Assessor(self.evidence_collector)
        self.cfr_part11_verifier = CFRPart11Verifier(self.evidence_collector)
        self.alcoa_scorer = ALCOAScorer(self.evidence_collector)
        self.gap_analyzer = GapAnalyzer(self.evidence_collector)
        self.remediation_planner = RemediationPlanner(self.evidence_collector)
        self.compliance_workflow = ComplianceWorkflow(self.temp_dir / "workflow")
        
        # Test data
        self.sample_gap = Gap(
            title="Test Compliance Gap",
            description="Sample gap for testing",
            framework=ComplianceFramework.GAMP5,
            requirement_reference="GAMP-5 Test Requirement",
            severity=GapSeverity.HIGH,
            risk_to_patient="Medium test risk",
            risk_to_product="High test risk",
            risk_to_data="Medium test risk",
            compliance_exposure="High test exposure",
            root_cause="Test root cause",
            current_state_description="Current test state",
            required_state_description="Required test state",
            identified_by="test_framework",
            identification_method="automated_test"
        )
        
        self.sample_data = [
            {
                "id": "test_doc_1",
                "timestamp": datetime.now(UTC).isoformat(),
                "user_id": "test_user",
                "created_by": "Test User",
                "audit_trail": True,
                "format": "json",
                "encoding": "utf-8",
                "schema": {"type": "test"},
                "is_original": True,
                "version": "1.0",
                "validated": True,
                "confidence_score": 0.95,
                "accessible": True,
                "retrieval_time": 30
            }
        ]
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_evidence_collector_initialization(self):
        """Test evidence collector initialization and template creation."""
        # Test initialization
        self.assertIsInstance(self.evidence_collector, EvidenceCollector)
        self.assertTrue(self.evidence_collector.evidence_directory.exists())
        self.assertTrue(self.evidence_collector.template_directory.exists())
        
        # Test template creation
        self.evidence_collector.create_default_templates()
        self.assertGreater(len(self.evidence_collector.template_registry), 0)
        
        # Verify templates exist on disk
        template_files = list(self.evidence_collector.template_directory.glob("*.json"))
        self.assertGreater(len(template_files), 0)
    
    def test_evidence_collection_system_integration(self):
        """Test evidence collection from system integration."""
        # Collect test evidence
        evidence = self.evidence_collector.collect_evidence_from_system(
            system_name=self.test_system_name,
            evidence_type=EvidenceType.TEST_RESULT,
            collection_method="automated_test_collection",
            collector_name="test_collector",
            experiment_id="test_experiment_1",
            metrics={"accuracy": 0.95, "precision": 0.90}
        )
        
        # Verify evidence collection
        self.assertIsInstance(evidence, Evidence)
        self.assertEqual(evidence.evidence_type, EvidenceType.TEST_RESULT)
        self.assertEqual(evidence.collected_by, "test_collector")
        self.assertGreater(evidence.completeness_score, 0.0)
        self.assertGreater(evidence.reliability_score, 0.0)
        
        # Verify evidence storage
        self.assertIn(evidence.evidence_id, self.evidence_collector.evidence_registry)
    
    def test_gamp5_categorization_assessment(self):
        """Test GAMP-5 categorization assessment."""
        # Test categorization assessment (providing experiment_id for evidence collection)
        assessment_result = self.gamp5_assessor.assess_system_categorization(
            system_name=self.test_system_name,
            predicted_category=GAMPCategory.CATEGORY_5,
            expected_category=GAMPCategory.CATEGORY_5,
            categorization_rationale="Custom-developed pharmaceutical test generation system with complex algorithms",
            confidence_score=0.92,
            assessor_name="test_assessor"
        )
        
        # Verify assessment results
        self.assertIsInstance(assessment_result, dict)
        self.assertEqual(assessment_result["system_name"], self.test_system_name)
        self.assertEqual(assessment_result["predicted_category"], "CATEGORY_5")
        self.assertEqual(assessment_result["confidence_score"], 0.92)
        self.assertIn("compliance_status", assessment_result)
        self.assertIn("evidence_id", assessment_result)
        
        # Verify strategy information
        self.assertIn("strategy", assessment_result)
        strategy = assessment_result["strategy"]
        self.assertEqual(strategy["validation_rigor"], "full")
        self.assertGreater(len(strategy["test_types"]), 0)
        self.assertIn("custom_validation", strategy["test_types"])
    
    def test_lifecycle_coverage_validation(self):
        """Test GAMP-5 lifecycle coverage validation."""
        # Prepare lifecycle artifacts
        lifecycle_artifacts = {
            "user_requirements_specification": {
                "version": "1.0",
                "approval_date": "2024-01-15",
                "approved_by": "Test Manager",
                "content": "Comprehensive URS for pharmaceutical system"
            },
            "functional_requirements_specification": {
                "version": "1.0",
                "approval_date": "2024-02-01",
                "approved_by": "Test Architect",
                "content": "Detailed FRS with functional specifications"
            },
            "validation_plan": {
                "version": "1.0",
                "approval_date": "2024-02-15",
                "approved_by": "Validation Manager",
                "content": "Comprehensive validation plan"
            }
        }
        
        # Test lifecycle validation
        validation_result = self.gamp5_assessor.validate_lifecycle_coverage(
            system_name=self.test_system_name,
            gamp_category=GAMPCategory.CATEGORY_5,
            lifecycle_artifacts=lifecycle_artifacts,
            assessor_name="test_assessor"
        )
        
        # Verify validation results
        self.assertIsInstance(validation_result, dict)
        self.assertEqual(validation_result["system_name"], self.test_system_name)
        self.assertEqual(validation_result["gamp_category"], "CATEGORY_5")
        self.assertIn("coverage_score", validation_result)
        self.assertIn("compliance_status", validation_result)
        self.assertGreater(validation_result["coverage_score"], 0.0)
    
    def test_cfr_part11_audit_trail_verification(self):
        """Test 21 CFR Part 11 audit trail verification."""
        # Prepare audit trail data
        audit_data = {
            "configuration": {
                "monitored_events": ["user_login", "record_creation", "record_modification", "record_deletion"],
                "captured_attributes": ["timestamp", "user_identity", "action_performed", "record_identifier"],
                "integrity_controls": ["tamper_evidence", "secure_storage", "retention_period"]
            },
            "audit_logs": [
                {
                    "event_type": "user_login",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "user_identity": "test_user",
                    "action_performed": "system_login",
                    "record_identifier": "session_001"
                }
            ],
            "integrity_verification": {
                "tamper_evidence": True,
                "time_sync": True,
                "encrypted_storage": True,
                "retention_period": 2555,  # 7 years
                "export_available": True
            }
        }
        
        # Test audit trail verification
        verification_result = self.cfr_part11_verifier.verify_audit_trail_completeness(
            system_name=self.test_system_name,
            audit_data=audit_data,
            target_completeness=1.0,
            verifier_name="test_verifier"
        )
        
        # Verify verification results
        self.assertIsInstance(verification_result, dict)
        self.assertEqual(verification_result["system_name"], self.test_system_name)
        self.assertEqual(verification_result["target_completeness"], 1.0)
        self.assertIn("actual_completeness", verification_result)
        self.assertIn("compliance_status", verification_result)
        self.assertGreater(verification_result["actual_completeness"], 0.0)
    
    def test_electronic_signatures_verification(self):
        """Test electronic signatures verification."""
        # Prepare signature data
        signature_data = {
            "signature_components": {
                "unique_user_identification": "test_user_001",
                "authentication_method": "username_password",
                "signature_timestamp": datetime.now(UTC).isoformat(),
                "signature_meaning": "Approval of test document",
                "record_linkage": "doc_12345"
            },
            "implementation": {
                "authentication_method": "username_password",
                "unique_identification": True,
                "non_repudiation": True
            },
            "manifestation": {
                "printed_form_display": True,
                "electronic_display": True,
                "signature_details": "Complete signature information displayed",
                "signer_identification": "Test User (test_user_001)",
                "signature_date_time": datetime.now(UTC).isoformat()
            },
            "record_linking": {
                "cryptographic_linking": True,
                "tamper_evidence": True,
                "signature_preservation": True
            }
        }
        
        # Test signature verification
        verification_result = self.cfr_part11_verifier.verify_electronic_signatures(
            system_name=self.test_system_name,
            signature_data=signature_data,
            verifier_name="test_verifier"
        )
        
        # Verify verification results
        self.assertIsInstance(verification_result, dict)
        self.assertEqual(verification_result["system_name"], self.test_system_name)
        self.assertIn("compliance_score", verification_result)
        self.assertIn("compliance_status", verification_result)
        self.assertGreater(verification_result["compliance_score"], 0.0)
    
    def test_alcoa_plus_assessment(self):
        """Test ALCOA+ data integrity assessment."""
        # Test ALCOA+ assessment
        assessment = self.alcoa_scorer.assess_system_data_integrity(
            system_name=self.test_system_name,
            data_samples=self.sample_data,
            assessment_scope="Comprehensive ALCOA+ assessment for pharmaceutical system",
            target_score=9.0,
            assessor_name="test_assessor"
        )
        
        # Verify assessment results
        from src.compliance_validation.alcoa_scorer import ALCOAAssessment
        self.assertIsInstance(assessment, ALCOAAssessment)
        self.assertEqual(assessment.system_name, self.test_system_name)
        self.assertEqual(assessment.target_score, 9.0)
        self.assertEqual(assessment.data_samples_assessed, 1)
        self.assertGreater(assessment.overall_score, 0.0)
        self.assertLessEqual(assessment.overall_score, 10.0)
        
        # Verify attribute scores
        self.assertEqual(len(assessment.attribute_scores), 9)  # All 9 ALCOA+ attributes
        
        # Check weighted scores for Original and Accurate
        if "original" in assessment.attribute_scores:
            self.assertEqual(assessment.attribute_scores["original"].weight, 2.0)
        if "accurate" in assessment.attribute_scores:
            self.assertEqual(assessment.attribute_scores["accurate"].weight, 2.0)
        
        # Verify compliance status determination
        self.assertIn(assessment.compliance_status, [
            ComplianceStatus.COMPLIANT, 
            ComplianceStatus.PARTIALLY_COMPLIANT, 
            ComplianceStatus.NON_COMPLIANT
        ])
    
    def test_gap_analysis_and_prioritization(self):
        """Test gap analysis and prioritization."""
        # Create test gaps for different frameworks
        gamp5_gap = Gap(
            title="GAMP-5 Categorization Gap",
            description="Incorrect category assignment",
            framework=ComplianceFramework.GAMP5,
            requirement_reference="GAMP-5 Section 3.1",
            severity=GapSeverity.HIGH,
            risk_to_patient="Medium - validation approach mismatch",
            risk_to_product="High - inadequate validation rigor",
            risk_to_data="Medium - data controls may be insufficient",
            compliance_exposure="High - regulatory inspection risk",
            root_cause="Algorithm classification error",
            current_state_description="System categorized as Category 4",
            required_state_description="System should be Category 5",
            identified_by="gamp5_assessor",
            identification_method="automated_assessment"
        )
        
        cfr_gap = Gap(
            title="Audit Trail Completeness Gap",
            description="Incomplete audit trail configuration",
            framework=ComplianceFramework.CFR_PART_11,
            requirement_reference="21 CFR Part 11.10(e)",
            severity=GapSeverity.CRITICAL,
            risk_to_patient="High - traceability compromised",
            risk_to_product="Critical - quality decisions lack audit trail",
            risk_to_data="Critical - data integrity monitoring incomplete",
            compliance_exposure="Critical - regulatory non-compliance",
            root_cause="Insufficient audit trail configuration",
            current_state_description="Partial audit trail coverage",
            required_state_description="Complete audit trail for all events",
            identified_by="cfr_part11_verifier",
            identification_method="automated_verification"
        )
        
        # Test gap consolidation
        gap_sources = {
            "gamp5": [gamp5_gap],
            "cfr_part_11": [cfr_gap]
        }
        
        consolidation_result = self.gap_analyzer.consolidate_gaps(
            system_name=self.test_system_name,
            gap_sources=gap_sources,
            analyzer_name="test_analyzer"
        )
        
        # Verify consolidation results
        self.assertIsInstance(consolidation_result, dict)
        self.assertEqual(consolidation_result["system_name"], self.test_system_name)
        self.assertEqual(consolidation_result["total_gaps"], 2)
        self.assertIn("gaps_by_framework", consolidation_result)
        self.assertIn("gaps_by_severity", consolidation_result)
        
        # Test gap prioritization
        prioritized_gaps = self.gap_analyzer.prioritize_gaps("risk_based")
        
        # Verify prioritization
        self.assertIsInstance(prioritized_gaps, list)
        self.assertEqual(len(prioritized_gaps), 2)
        
        # Critical gaps should be prioritized higher
        if len(prioritized_gaps) > 1:
            first_gap = prioritized_gaps[0]
            self.assertLessEqual(first_gap.priority_rank, prioritized_gaps[1].priority_rank)
    
    def test_remediation_planning(self):
        """Test remediation plan creation."""
        # Test individual remediation plan
        remediation_plan = self.remediation_planner.create_remediation_plan(
            gap=self.sample_gap,
            priority_level=1,
            business_context={"preferred_owners": {"GAMP-5": "Test Validation Manager"}},
            planner_name="test_planner"
        )
        
        # Verify remediation plan
        from src.compliance_validation.models import RemediationPlan
        self.assertIsInstance(remediation_plan, RemediationPlan)
        self.assertEqual(remediation_plan.gap_id, self.sample_gap.gap_id)
        self.assertGreater(remediation_plan.estimated_effort_hours, 0)
        self.assertGreater(len(remediation_plan.required_resources), 0)
        self.assertGreater(len(remediation_plan.corrective_actions), 0)
        self.assertGreater(len(remediation_plan.preventive_actions), 0)
        
        # Verify CAPA structure
        for action in remediation_plan.corrective_actions:
            self.assertIn("action_id", action)
            self.assertIn("title", action)
            self.assertIn("category", action)
            self.assertEqual(action["category"], "corrective")
        
        for action in remediation_plan.preventive_actions:
            self.assertIn("action_id", action)
            self.assertIn("title", action)
            self.assertIn("category", action)
            self.assertEqual(action["category"], "preventive")
    
    def test_consolidated_remediation_planning(self):
        """Test consolidated remediation planning for multiple gaps."""
        # Create additional test gap
        second_gap = Gap(
            title="Second Test Gap",
            description="Another sample gap",
            framework=ComplianceFramework.GAMP5,
            requirement_reference="GAMP-5 Test Requirement 2",
            severity=GapSeverity.MEDIUM,
            risk_to_patient="Low test risk",
            risk_to_product="Medium test risk",
            risk_to_data="Low test risk",
            compliance_exposure="Medium test exposure",
            root_cause="Second test root cause",
            current_state_description="Second current state",
            required_state_description="Second required state",
            identified_by="test_framework",
            identification_method="automated_test"
        )
        
        # Test consolidated planning
        consolidated_plan = self.remediation_planner.create_consolidated_plan(
            gaps=[self.sample_gap, second_gap],
            plan_name="Consolidated Test Remediation Plan",
            business_context={},
            planner_name="test_planner"
        )
        
        # Verify consolidated plan
        from src.compliance_validation.models import RemediationPlan
        self.assertIsInstance(consolidated_plan, RemediationPlan)
        self.assertIn("Consolidated", consolidated_plan.plan_title)
        self.assertGreater(len(consolidated_plan.dependencies), 0)
        self.assertGreater(len(consolidated_plan.corrective_actions), 0)
        self.assertGreater(len(consolidated_plan.preventive_actions), 0)
    
    def test_comprehensive_compliance_workflow(self):
        """Test end-to-end compliance validation workflow."""
        # Prepare validation scope
        validation_scope = {
            "frameworks": ["gamp5", "cfr_part_11", "alcoa_plus"],
            "gamp5_parameters": {
                "categorization": {
                    "system_name": self.test_system_name,
                    "predicted_category": GAMPCategory.CATEGORY_5,
                    "categorization_rationale": "Custom pharmaceutical system",
                    "confidence_score": 0.95
                }
            },
            "cfr_part11_parameters": {
                "audit_trail": {
                    "system_name": self.test_system_name,
                    "audit_data": {
                        "configuration": {"monitored_events": ["user_login"]},
                        "audit_logs": [],
                        "integrity_verification": {"tamper_evidence": True}
                    }
                }
            },
            "alcoa_parameters": {
                "system_name": self.test_system_name,
                "data_samples": self.sample_data
            }
        }
        
        business_context = {
            "priority_weights": {
                "patient_safety": 0.5,
                "product_quality": 0.3,
                "data_integrity": 0.15,
                "compliance_exposure": 0.05
            }
        }
        
        # Execute comprehensive validation
        workflow_results = self.compliance_workflow.execute_comprehensive_validation(
            system_name=self.test_system_name,
            validation_scope=validation_scope,
            business_context=business_context,
            workflow_manager="test_workflow_manager"
        )
        
        # Verify workflow results
        self.assertIsInstance(workflow_results, dict)
        self.assertEqual(workflow_results["system_name"], self.test_system_name)
        self.assertIn("session_id", workflow_results)
        self.assertIn("overall_compliance_status", workflow_results)
        self.assertIn("overall_compliance_score", workflow_results)
        self.assertIn("frameworks_assessed", workflow_results)
        self.assertIn("total_gaps_identified", workflow_results)
        self.assertIn("evidence_items_collected", workflow_results)
        self.assertIn("next_steps", workflow_results)
        self.assertIn("compliance_report", workflow_results)
        
        # Verify frameworks were assessed
        self.assertGreater(len(workflow_results["frameworks_assessed"]), 0)
        
        # Verify compliance report structure
        compliance_report = workflow_results["compliance_report"]
        self.assertIn("assessment_name", compliance_report)
        self.assertIn("system_under_assessment", compliance_report)
        self.assertIn("overall_status", compliance_report)
        self.assertIn("overall_score", compliance_report)
    
    def test_workflow_error_handling(self):
        """Test workflow error handling and NO FALLBACKS principle."""
        # Test with invalid validation scope
        invalid_scope = {
            "frameworks": ["invalid_framework"],
            "invalid_parameters": {}
        }
        
        # Should raise explicit error, not fallback
        with self.assertRaises(Exception):
            self.compliance_workflow.execute_comprehensive_validation(
                system_name=self.test_system_name,
                validation_scope=invalid_scope
            )
    
    def test_evidence_traceability(self):
        """Test evidence collection and traceability matrix."""
        # Build traceability matrix
        requirements = {
            "REQ-001": {
                "title": "System categorization accuracy",
                "description": "System must be correctly categorized per GAMP-5"
            },
            "REQ-002": {
                "title": "Audit trail completeness",
                "description": "System must maintain complete audit trails per 21 CFR Part 11"
            }
        }
        
        test_cases = {
            "TC-001": {
                "title": "GAMP-5 categorization test",
                "description": "Verify system categorization accuracy"
            },
            "TC-002": {
                "title": "Audit trail verification test",
                "description": "Verify audit trail completeness"
            }
        }
        
        # Build traceability matrix
        matrix = self.evidence_collector.build_traceability_matrix(
            matrix_name="Test Traceability Matrix",
            project_id="TEST_PROJECT_001",
            creator_name="test_creator",
            requirements=requirements,
            test_cases=test_cases
        )
        
        # Verify matrix creation
        from src.compliance_validation.models import TraceabilityMatrix
        self.assertIsInstance(matrix, TraceabilityMatrix)
        self.assertEqual(matrix.matrix_name, "Test Traceability Matrix")
        self.assertEqual(len(matrix.requirements), 2)
        self.assertEqual(len(matrix.test_cases), 2)
        
        # Link requirements to test cases
        matrix.link_requirement_to_test("REQ-001", "TC-001")
        matrix.link_requirement_to_test("REQ-002", "TC-002")
        
        # Calculate coverage
        coverage = matrix.calculate_coverage()
        self.assertGreater(coverage, 0.0)
        self.assertLessEqual(coverage, 100.0)
    
    def test_integration_with_cross_validation(self):
        """Test integration with existing cross-validation framework."""
        # This test verifies that compliance validation can work with
        # quality metrics from the cross-validation framework
        
        # Mock quality metrics
        mock_quality_metrics = MagicMock()
        mock_quality_metrics.analyze_classification_quality.return_value = MagicMock(
            overall_accuracy=0.95,
            false_positive_rate=0.02,
            false_negative_rate=0.03
        )
        
        # Create ALCOA scorer with quality metrics
        alcoa_scorer_with_metrics = ALCOAScorer(
            self.evidence_collector,
            mock_quality_metrics
        )
        
        # Test assessment with quality metrics integration
        assessment = alcoa_scorer_with_metrics.assess_system_data_integrity(
            system_name=self.test_system_name,
            data_samples=self.sample_data
        )
        
        # Verify assessment works with quality metrics integration
        from src.compliance_validation.alcoa_scorer import ALCOAAssessment
        self.assertIsInstance(assessment, ALCOAAssessment)
        self.assertGreater(assessment.overall_score, 0.0)


class TestComplianceValidationIntegration(unittest.TestCase):
    """Integration tests for compliance validation framework."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.compliance_workflow = ComplianceWorkflow(self.temp_dir)
    
    def tearDown(self):
        """Clean up integration test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_end_to_end_validation_scenario(self):
        """Test complete end-to-end validation scenario."""
        # This test simulates a real pharmaceutical system validation
        
        system_name = "Pharmaceutical Quality Management System"
        
        validation_scope = {
            "frameworks": ["gamp5", "cfr_part_11", "alcoa_plus"],
            "gamp5_parameters": {
                "categorization": {
                    "system_name": system_name,
                    "predicted_category": GAMPCategory.CATEGORY_4,
                    "categorization_rationale": "Configurable COTS pharmaceutical quality system with customizations",
                    "confidence_score": 0.88
                },
                "lifecycle": {
                    "system_name": system_name,
                    "gamp_category": GAMPCategory.CATEGORY_4,
                    "lifecycle_artifacts": {
                        "user_requirements_specification": {
                            "version": "2.1",
                            "approval_date": "2024-03-01",
                            "approved_by": "QA Manager"
                        }
                    }
                }
            },
            "cfr_part11_parameters": {
                "audit_trail": {
                    "system_name": system_name,
                    "audit_data": {
                        "configuration": {
                            "monitored_events": ["user_login", "record_creation"],
                            "captured_attributes": ["timestamp", "user_identity"],
                            "integrity_controls": ["tamper_evidence"]
                        },
                        "audit_logs": [{"event_type": "user_login"}],
                        "integrity_verification": {"tamper_evidence": True}
                    }
                }
            },
            "alcoa_parameters": {
                "system_name": system_name,
                "data_samples": [
                    {
                        "id": "qms_record_1",
                        "timestamp": datetime.now(UTC).isoformat(),
                        "user_id": "qms_user",
                        "created_by": "QMS User",
                        "format": "json",
                        "is_original": True,
                        "validated": True,
                        "accessible": True
                    }
                ]
            }
        }
        
        # Execute validation
        results = self.compliance_workflow.execute_comprehensive_validation(
            system_name=system_name,
            validation_scope=validation_scope
        )
        
        # Verify end-to-end execution
        self.assertIsInstance(results, dict)
        self.assertIn("session_id", results)
        self.assertIn("overall_compliance_status", results)
        
        # Test deliverables generation
        deliverable_types = ["executive_summary", "compliance_report", "gap_analysis"]
        deliverables = self.compliance_workflow.generate_validation_deliverables(
            session_id=results["session_id"],
            deliverable_types=deliverable_types
        )
        
        # Verify deliverables
        self.assertIsInstance(deliverables, dict)
        for deliverable_type in deliverable_types:
            self.assertIn(deliverable_type, deliverables)
            self.assertTrue(deliverables[deliverable_type].exists())


if __name__ == "__main__":
    # Run tests with detailed output
    unittest.main(verbosity=2)
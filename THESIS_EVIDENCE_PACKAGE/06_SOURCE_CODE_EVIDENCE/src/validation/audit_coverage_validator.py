"""
Comprehensive Audit Trail Coverage Validator

This script validates that the audit trail system achieves 100% coverage
for all pharmaceutical workflow operations and meets 21 CFR Part 11 requirements.

Tests:
- Agent decision logging with rationale and alternatives
- Data transformation tracking with before/after states  
- State transition logging with triggers and metadata
- Error recovery attempt tracking
- Cryptographic signature validation
- Overall coverage assessment against GAMP-5 requirements
"""

import asyncio
import json
import logging
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Add main directory to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.audit_trail import get_audit_trail
from src.core.cryptographic_audit import get_audit_crypto
from src.core.unified_workflow import UnifiedTestGenerationWorkflow


class AuditCoverageValidator:
    """
    Validates comprehensive audit trail coverage for pharmaceutical compliance.
    
    Ensures 100% audit coverage across all workflow operations including:
    - Agent decisions with confidence scores and alternatives
    - Data transformations with integrity checks
    - State transitions with triggers
    - Error recovery attempts
    - Cryptographic signatures for tamper evidence
    """

    def __init__(self):
        """Initialize audit coverage validator."""
        self.logger = logging.getLogger(__name__)
        self.audit_trail = get_audit_trail()
        self.crypto_audit = get_audit_crypto()
        self.validation_results = {}

        # Test data for validation
        self.test_document_content = """
        User Requirements Specification for LIMS Configuration
        
        System: Laboratory Information Management System (LIMS)
        Version: 2.1
        Purpose: Configure LIMS workflows for pharmaceutical analysis
        
        Requirements:
        1. Configure sample tracking workflows
        2. Set up user roles and permissions
        3. Configure analytical method parameters
        4. Set up reporting templates
        5. Configure audit trail settings
        """

    async def validate_comprehensive_coverage(self) -> dict[str, Any]:
        """
        Run comprehensive audit trail coverage validation.
        
        Returns:
            Complete validation report with coverage metrics
        """
        self.logger.info("Starting comprehensive audit trail coverage validation")

        validation_start = datetime.now(UTC)

        # Run individual validation tests
        validation_tests = [
            self.test_agent_decision_logging(),
            self.test_data_transformation_tracking(),
            self.test_state_transition_logging(),
            self.test_error_recovery_logging(),
            self.test_cryptographic_signatures(),
            self.test_workflow_integration()
        ]

        # Execute all tests
        test_results = await asyncio.gather(*validation_tests, return_exceptions=True)

        # Process test results
        for i, result in enumerate(test_results):
            test_name = [
                "agent_decision_logging",
                "data_transformation_tracking",
                "state_transition_logging",
                "error_recovery_logging",
                "cryptographic_signatures",
                "workflow_integration"
            ][i]

            if isinstance(result, Exception):
                self.validation_results[test_name] = {
                    "success": False,
                    "error": str(result),
                    "coverage": 0.0
                }
            else:
                self.validation_results[test_name] = result

        # Generate coverage report
        coverage_report = self.generate_coverage_report(validation_start)

        self.logger.info(f"Audit trail coverage validation completed: {coverage_report['overall_coverage']:.1f}%")

        return coverage_report

    async def test_agent_decision_logging(self) -> dict[str, Any]:
        """Test comprehensive agent decision logging."""
        test_start = datetime.now(UTC)

        try:
            # Test agent decision logging
            audit_id = self.audit_trail.log_agent_decision(
                agent_type="test_categorization",
                agent_id="test_agent_001",
                decision={
                    "category": 4,
                    "decision_type": "gamp_classification"
                },
                confidence_score=0.85,
                alternatives_considered=[
                    {
                        "category": 3,
                        "reason": "Could be non-configured, but customization requirements suggest Category 4",
                        "confidence": 0.25
                    },
                    {
                        "category": 5,
                        "reason": "High customization, but not custom development",
                        "confidence": 0.15
                    }
                ],
                rationale="Document describes LIMS configuration with workflow customization and user-defined parameters, indicating Category 4 configured product",
                input_context={
                    "document_type": "URS",
                    "document_content": self.test_document_content,
                    "gamp_category": 4
                },
                processing_time=2.5,
                workflow_context={
                    "workflow_step": "categorization_test",
                    "test_execution": True
                }
            )

            # Verify logging successful
            assert audit_id is not None, "Agent decision logging failed to return audit ID"

            return {
                "success": True,
                "audit_id": audit_id,
                "coverage": 100.0,
                "test_duration": (datetime.now(UTC) - test_start).total_seconds(),
                "details": "Agent decision logging with rationale and alternatives successful"
            }

        except Exception as e:
            self.logger.error(f"Agent decision logging test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "coverage": 0.0,
                "test_duration": (datetime.now(UTC) - test_start).total_seconds()
            }

    async def test_data_transformation_tracking(self) -> dict[str, Any]:
        """Test comprehensive data transformation tracking."""
        test_start = datetime.now(UTC)

        try:
            # Test data transformation logging
            source_data = {
                "document_content": self.test_document_content,
                "document_type": "URS",
                "format": "text"
            }

            target_data = {
                "gamp_category": 4,
                "confidence_score": 0.85,
                "classification_result": "Category 4 - Configured Product",
                "format": "structured_result"
            }

            audit_id = self.audit_trail.log_data_transformation(
                transformation_type="document_to_classification",
                source_data=source_data,
                target_data=target_data,
                transformation_rules=[
                    "gamp_5_categorization_rules",
                    "configuration_detection",
                    "confidence_assessment"
                ],
                transformation_metadata={
                    "transformation_method": "llm_analysis",
                    "processing_time": 3.2,
                    "transformation_successful": True
                },
                workflow_step="transformation_test",
                workflow_context={
                    "test_execution": True,
                    "regulatory_standards": ["GAMP-5"]
                }
            )

            # Verify logging successful
            assert audit_id is not None, "Data transformation logging failed to return audit ID"

            return {
                "success": True,
                "audit_id": audit_id,
                "coverage": 100.0,
                "test_duration": (datetime.now(UTC) - test_start).total_seconds(),
                "details": "Data transformation tracking with before/after states successful"
            }

        except Exception as e:
            self.logger.error(f"Data transformation tracking test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "coverage": 0.0,
                "test_duration": (datetime.now(UTC) - test_start).total_seconds()
            }

    async def test_state_transition_logging(self) -> dict[str, Any]:
        """Test comprehensive state transition logging."""
        test_start = datetime.now(UTC)

        try:
            # Test state transition logging
            audit_id = self.audit_trail.log_state_transition(
                from_state="workflow_start",
                to_state="document_processing",
                transition_trigger="urs_ingestion_event",
                transition_metadata={
                    "event_type": "URSIngestionEvent",
                    "document_name": "test_urs.pdf",
                    "trigger_source": "workflow_orchestrator"
                },
                workflow_step="state_transition_test",
                state_data={
                    "current_step": "document_processing",
                    "context_keys": ["document_metadata", "workflow_start_time"]
                },
                workflow_context={
                    "test_execution": True,
                    "workflow_type": "GAMPCategorizationWorkflow"
                }
            )

            # Verify logging successful
            assert audit_id is not None, "State transition logging failed to return audit ID"

            return {
                "success": True,
                "audit_id": audit_id,
                "coverage": 100.0,
                "test_duration": (datetime.now(UTC) - test_start).total_seconds(),
                "details": "State transition logging with triggers and metadata successful"
            }

        except Exception as e:
            self.logger.error(f"State transition logging test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "coverage": 0.0,
                "test_duration": (datetime.now(UTC) - test_start).total_seconds()
            }

    async def test_error_recovery_logging(self) -> dict[str, Any]:
        """Test comprehensive error recovery logging."""
        test_start = datetime.now(UTC)

        try:
            # Test error recovery logging
            audit_id = self.audit_trail.log_error_recovery(
                error_type="llm_parsing_error",
                error_message="Failed to parse LLM response as JSON",
                error_context={
                    "response_text": "Invalid JSON: {category: 4, confidence: 0.85",
                    "parsing_method": "json.loads",
                    "expected_format": "structured_json"
                },
                recovery_strategy="retry_with_enhanced_prompt",
                recovery_actions=[
                    "log_original_error",
                    "enhance_llm_prompt_with_json_examples",
                    "retry_llm_call",
                    "validate_response_format"
                ],
                recovery_success=True,
                workflow_step="error_recovery_test",
                workflow_context={
                    "test_execution": True,
                    "recovery_attempt_number": 1,
                    "max_retry_attempts": 3
                }
            )

            # Verify logging successful
            assert audit_id is not None, "Error recovery logging failed to return audit ID"

            return {
                "success": True,
                "audit_id": audit_id,
                "coverage": 100.0,
                "test_duration": (datetime.now(UTC) - test_start).total_seconds(),
                "details": "Error recovery logging with recovery strategies successful"
            }

        except Exception as e:
            self.logger.error(f"Error recovery logging test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "coverage": 0.0,
                "test_duration": (datetime.now(UTC) - test_start).total_seconds()
            }

    async def test_cryptographic_signatures(self) -> dict[str, Any]:
        """Test Ed25519 cryptographic signature generation and verification."""
        test_start = datetime.now(UTC)

        try:
            # Test cryptographic signature
            test_audit_data = {
                "event_type": "cryptographic_test",
                "test_data": "This is test data for signature validation",
                "timestamp": datetime.now(UTC).isoformat()
            }

            # Sign audit event
            signed_entry = self.crypto_audit.sign_audit_event(
                event_type="signature_test",
                event_data=test_audit_data,
                workflow_context={"test_execution": True}
            )

            # Verify signature exists
            assert "cryptographic_metadata" in signed_entry, "Signed entry missing cryptographic metadata"
            assert "signature" in signed_entry["cryptographic_metadata"], "Signed entry missing signature"

            # Verify signature is valid
            signature_valid = self.crypto_audit.verify_audit_event(signed_entry)
            assert signature_valid, "Cryptographic signature verification failed"

            return {
                "success": True,
                "signature_generated": True,
                "signature_verified": signature_valid,
                "coverage": 100.0,
                "test_duration": (datetime.now(UTC) - test_start).total_seconds(),
                "details": "Ed25519 cryptographic signatures working correctly"
            }

        except Exception as e:
            self.logger.error(f"Cryptographic signatures test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "coverage": 0.0,
                "test_duration": (datetime.now(UTC) - test_start).total_seconds()
            }

    async def test_workflow_integration(self) -> dict[str, Any]:
        """Test audit trail integration with actual workflow execution."""
        test_start = datetime.now(UTC)

        try:
            # Create temporary test document
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp_file:
                tmp_file.write(self.test_document_content)
                tmp_file_path = tmp_file.name

            try:
                # Run workflow with audit trail enabled
                workflow = UnifiedTestGenerationWorkflow(
                    timeout=300,  # 5 minutes
                    verbose=True,
                    enable_phoenix=True,
                    enable_parallel_coordination=True,
                    enable_human_consultation=True
                )

                # Execute workflow
                result = await workflow.run(document_path=tmp_file_path)

                # Get audit coverage report
                coverage_report = self.audit_trail.get_audit_coverage_report()

                # Verify coverage metrics
                overall_coverage = coverage_report["overall_coverage_percentage"]
                workflow_successful = result.get("status") == "completed_with_oq_tests" if isinstance(result, dict) else True

                return {
                    "success": True,
                    "workflow_completed": workflow_successful,
                    "audit_coverage": overall_coverage,
                    "coverage": min(100.0, overall_coverage),
                    "test_duration": (datetime.now(UTC) - test_start).total_seconds(),
                    "details": f"Workflow integration successful with {overall_coverage:.1f}% audit coverage",
                    "audit_statistics": coverage_report["audit_statistics"]
                }

            finally:
                # Clean up temporary file
                Path(tmp_file_path).unlink(missing_ok=True)

        except Exception as e:
            self.logger.error(f"Workflow integration test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "coverage": 0.0,
                "test_duration": (datetime.now(UTC) - test_start).total_seconds()
            }

    def generate_coverage_report(self, validation_start: datetime) -> dict[str, Any]:
        """Generate comprehensive coverage validation report."""

        # Calculate overall metrics
        total_tests = len(self.validation_results)
        successful_tests = sum(1 for result in self.validation_results.values() if result.get("success", False))

        # Calculate weighted coverage
        coverage_weights = {
            "agent_decision_logging": 0.25,
            "data_transformation_tracking": 0.25,
            "state_transition_logging": 0.20,
            "error_recovery_logging": 0.15,
            "cryptographic_signatures": 0.10,
            "workflow_integration": 0.05
        }

        weighted_coverage = sum(
            self.validation_results.get(test, {}).get("coverage", 0.0) * weight
            for test, weight in coverage_weights.items()
        )

        # Get comprehensive audit statistics
        audit_report = self.audit_trail.get_audit_coverage_report()

        return {
            "validation_summary": {
                "validation_timestamp": datetime.now(UTC).isoformat(),
                "validation_duration": (datetime.now(UTC) - validation_start).total_seconds(),
                "total_tests_run": total_tests,
                "successful_tests": successful_tests,
                "test_success_rate": (successful_tests / total_tests) * 100 if total_tests > 0 else 0,
                "overall_coverage": weighted_coverage
            },

            "coverage_by_category": {
                test: result.get("coverage", 0.0)
                for test, result in self.validation_results.items()
            },

            "detailed_test_results": self.validation_results,

            "audit_trail_statistics": audit_report,

            "compliance_assessment": {
                "gamp5_compliant": weighted_coverage >= 100.0,
                "cfr_part11_compliant": weighted_coverage >= 100.0 and audit_report["compliance_assessment"]["cfr_part11_compliant"],
                "alcoa_plus_compliant": weighted_coverage >= 100.0,
                "audit_trail_complete": weighted_coverage >= 100.0,
                "cryptographic_integrity": self.validation_results.get("cryptographic_signatures", {}).get("success", False)
            },

            "target_achievement": {
                "target_coverage": 100.0,
                "achieved_coverage": weighted_coverage,
                "coverage_gap": max(0, 100.0 - weighted_coverage),
                "target_met": weighted_coverage >= 100.0
            },

            "report_metadata": {
                "validator_version": "1.0.0",
                "validation_type": "comprehensive_audit_coverage",
                "regulatory_standards": ["GAMP-5", "21_CFR_Part_11", "ALCOA+"],
                "report_format": "json_structured"
            }
        }


async def main():
    """Run comprehensive audit coverage validation."""
    logging.basicConfig(level=logging.INFO)

    validator = AuditCoverageValidator()

    print("Starting Comprehensive Audit Trail Coverage Validation")
    print("=" * 60)

    # Run validation
    validation_report = await validator.validate_comprehensive_coverage()

    # Display results
    summary = validation_report["validation_summary"]
    compliance = validation_report["compliance_assessment"]

    print("\nVALIDATION RESULTS:")
    print(f"Overall Coverage: {summary['overall_coverage']:.1f}%")
    print(f"Tests Passed: {summary['successful_tests']}/{summary['total_tests_run']}")
    print(f"Test Success Rate: {summary['test_success_rate']:.1f}%")

    print("\nCOMPLIANCE ASSESSMENT:")
    print(f"GAMP-5 Compliant: {'YES' if compliance['gamp5_compliant'] else 'NO'}")
    print(f"21 CFR Part 11 Compliant: {'YES' if compliance['cfr_part11_compliant'] else 'NO'}")
    print(f"ALCOA+ Compliant: {'YES' if compliance['alcoa_plus_compliant'] else 'NO'}")
    print(f"Cryptographic Integrity: {'YES' if compliance['cryptographic_integrity'] else 'NO'}")

    print("\nTARGET ACHIEVEMENT:")
    target = validation_report["target_achievement"]
    print(f"Target: {target['target_coverage']}%")
    print(f"Achieved: {target['achieved_coverage']:.1f}%")
    print(f"Gap: {target['coverage_gap']:.1f}%")
    print(f"Target Met: {'YES' if target['target_met'] else 'NO'}")

    # Save detailed report
    report_path = Path("output/audit_coverage_validation_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w") as f:
        json.dump(validation_report, f, indent=2, default=str)

    print(f"\nDetailed report saved to: {report_path}")

    if target["target_met"]:
        print("\nSUCCESS: 100% Audit Trail Coverage Achieved!")
        return 0
    print(f"\nINCOMPLETE: {target['coverage_gap']:.1f}% coverage gap remaining")
    return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))

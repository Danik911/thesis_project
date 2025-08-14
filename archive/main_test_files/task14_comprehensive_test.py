#!/usr/bin/env python3
"""
Task 14 Comprehensive End-to-End Testing
========================================

This script executes comprehensive testing of all 5 URS cases with:
- GAMP-5 categorization validation
- Phoenix observability monitoring
- Error recovery testing
- Performance benchmarking
- Compliance verification

NO FALLBACK LOGIC - All errors must fail explicitly
"""

import asyncio
import logging
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.events import WorkflowStartEvent
from src.core.unified_workflow import UnifiedWorkflow
from src.monitoring.phoenix_enhanced import PhoenixHandler
from src.shared.event_logging import EventLogger


class Task14ComprehensiveTester:
    """
    Comprehensive end-to-end tester for Task 14 with strict compliance validation.
    
    CRITICAL: NO FALLBACKS - All failures must be explicit and observable.
    """

    def __init__(self):
        self.results = {}
        self.phoenix_handler = None
        self.test_start_time = datetime.now()
        self.event_logger = EventLogger()

        # Configure logging to capture everything
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(f'task14_test_{self.test_start_time.strftime("%Y%m%d_%H%M%S")}.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

        # URS test cases with expected results
        self.urs_test_cases = [
            {
                "id": "URS-001",
                "name": "Environmental Monitoring System",
                "expected_category": 3,
                "expected_confidence": "high",
                "description": "Vendor-supplied temperature monitoring with standard configuration"
            },
            {
                "id": "URS-002",
                "name": "Laboratory Information Management System",
                "expected_category": 4,
                "expected_confidence": "high",
                "description": "Commercial LIMS with extensive configuration and custom scripting"
            },
            {
                "id": "URS-003",
                "name": "Manufacturing Execution System",
                "expected_category": 5,
                "expected_confidence": "high",
                "description": "Custom-developed MES with proprietary algorithms - MUST NOT BE AMBIGUOUS"
            },
            {
                "id": "URS-004",
                "name": "Chromatography Data System",
                "expected_category": [3, 4],  # Ambiguous case
                "expected_confidence": "medium_to_low",
                "description": "Commercial CDS with some custom elements - designed to be ambiguous"
            },
            {
                "id": "URS-005",
                "name": "Clinical Trial Management System",
                "expected_category": [4, 5],  # Ambiguous case
                "expected_confidence": "medium_to_low",
                "description": "Hybrid CTMS with significant custom development - designed to be ambiguous"
            }
        ]

    async def setup_environment(self) -> bool:
        """Initialize testing environment and verify Phoenix connectivity."""
        self.logger.info("=== Task 14 Comprehensive Testing Setup ===")

        try:
            # Verify Phoenix server
            phoenix_status = await self.check_phoenix_server()
            if not phoenix_status:
                self.logger.error("CRITICAL: Phoenix server not accessible - CANNOT PROCEED")
                return False

            # Initialize Phoenix handler
            self.phoenix_handler = PhoenixHandler()
            self.logger.info("Phoenix handler initialized")

            # Clear any existing logs for clean test
            await self.clear_test_logs()

            self.logger.info("Environment setup complete")
            return True

        except Exception as e:
            self.logger.error(f"CRITICAL: Environment setup failed: {e}")
            self.logger.error(traceback.format_exc())
            return False

    async def check_phoenix_server(self) -> bool:
        """Verify Phoenix server is running and accessible."""
        try:
            response = requests.get("http://localhost:6006", timeout=5)
            if response.status_code == 200:
                self.logger.info("Phoenix server accessible at http://localhost:6006")

                # Check traces endpoint
                traces_response = requests.get("http://localhost:6006/v1/traces", timeout=5)
                self.logger.info(f"Phoenix traces endpoint status: {traces_response.status_code}")

                return True
            self.logger.error(f"Phoenix server returned status {response.status_code}")
            return False

        except Exception as e:
            self.logger.error(f"Phoenix server check failed: {e}")
            return False

    async def clear_test_logs(self):
        """Clear existing test logs for clean execution."""
        try:
            log_dirs = ["logs/audit", "logs/events", "logs/test_events"]
            for log_dir in log_dirs:
                log_path = Path(log_dir)
                if log_path.exists():
                    for log_file in log_path.glob("*.log"):
                        if log_file.stat().st_size > 0:
                            self.logger.info(f"Backing up existing log: {log_file}")
                            backup_name = f"{log_file.stem}_backup_{int(time.time())}{log_file.suffix}"
                            log_file.rename(log_path / backup_name)
        except Exception as e:
            self.logger.warning(f"Log cleanup warning: {e}")

    async def execute_urs_test_case(self, test_case: dict) -> dict[str, Any]:
        """
        Execute a single URS test case through the complete workflow.
        
        CRITICAL: Must fail explicitly if categorization is incorrect or confidence is artificial.
        """
        urs_id = test_case["id"]
        self.logger.info(f"=== Executing {urs_id}: {test_case['name']} ===")

        test_result = {
            "urs_id": urs_id,
            "name": test_case["name"],
            "expected_category": test_case["expected_category"],
            "expected_confidence": test_case["expected_confidence"],
            "start_time": datetime.now(),
            "status": "FAILED",  # Assume failure until proven otherwise
            "errors": [],
            "warnings": [],
            "execution_time_seconds": None,
            "actual_category": None,
            "actual_confidence": None,
            "confidence_score": None,
            "phoenix_traces": [],
            "compliance_violations": [],
            "fallback_detected": False
        }

        execution_start = time.time()

        try:
            # Prepare test data file path
            test_data_path = Path("tests/test_data/gamp5_test_data/testing_data.md")
            if not test_data_path.exists():
                raise FileNotFoundError(f"Test data file not found: {test_data_path}")

            # Initialize workflow
            workflow = UnifiedWorkflow()

            # Create workflow event
            start_event = WorkflowStartEvent(
                workflow_id=f"task14_test_{urs_id}_{int(time.time())}",
                document_path=str(test_data_path),
                user_id="task14_tester",
                gxp_context=True
            )

            # Execute workflow - THIS MUST NOT USE FALLBACKS
            self.logger.info(f"Starting workflow execution for {urs_id}")
            result = await workflow.run(start_event)

            execution_time = time.time() - execution_start
            test_result["execution_time_seconds"] = execution_time

            # Extract results - FAIL EXPLICITLY IF DATA IS INVALID
            if not result or not hasattr(result, "category"):
                raise ValueError("Workflow returned invalid result - NO FALLBACK PERMITTED")

            test_result["actual_category"] = result.category
            test_result["actual_confidence"] = getattr(result, "confidence_level", "unknown")
            test_result["confidence_score"] = getattr(result, "confidence_score", None)

            # CRITICAL VALIDATION: Check for fallback behavior
            await self.validate_no_fallbacks(test_result, result)

            # Validate categorization correctness
            await self.validate_categorization_result(test_case, test_result, result)

            # Check Phoenix traces
            phoenix_traces = await self.collect_phoenix_traces(urs_id)
            test_result["phoenix_traces"] = phoenix_traces

            # Validate compliance
            compliance_issues = await self.validate_compliance(result)
            test_result["compliance_violations"] = compliance_issues

            # Determine overall test status
            if (test_result["fallback_detected"] or
                len(test_result["compliance_violations"]) > 0 or
                len(test_result["errors"]) > 0):
                test_result["status"] = "FAILED"
            else:
                test_result["status"] = "PASSED"

            self.logger.info(f"{urs_id} execution completed: {test_result['status']}")

        except Exception as e:
            execution_time = time.time() - execution_start
            test_result["execution_time_seconds"] = execution_time
            test_result["errors"].append(f"Execution failed: {e!s}")
            test_result["status"] = "CRITICAL_FAILURE"

            self.logger.error(f"{urs_id} failed with exception: {e}")
            self.logger.error(traceback.format_exc())

        test_result["end_time"] = datetime.now()
        return test_result

    async def validate_no_fallbacks(self, test_result: dict, workflow_result: Any):
        """
        CRITICAL: Detect any fallback behavior and mark as compliance violation.
        
        This is the most important validation - NO FALLBACKS PERMITTED.
        """
        try:
            # Check for artificial confidence scores
            if hasattr(workflow_result, "confidence_score"):
                confidence = workflow_result.confidence_score
                if confidence is not None:
                    # Check for common fallback values
                    fallback_values = [0.5, 0.7, 0.8, 0.9, 1.0]
                    if confidence in fallback_values:
                        test_result["fallback_detected"] = True
                        test_result["errors"].append(f"CRITICAL: Artificial confidence score detected: {confidence}")

            # Check for fallback categories
            if hasattr(workflow_result, "category"):
                category = workflow_result.category
                if category is not None and hasattr(workflow_result, "reasoning"):
                    reasoning = workflow_result.reasoning.lower()
                    fallback_indicators = ["default", "fallback", "assume", "generic", "standard"]
                    for indicator in fallback_indicators:
                        if indicator in reasoning:
                            test_result["fallback_detected"] = True
                            test_result["errors"].append(f"CRITICAL: Fallback reasoning detected: {indicator}")

            # Check for masked errors
            if hasattr(workflow_result, "errors") and workflow_result.errors:
                for error in workflow_result.errors:
                    if "fallback" in str(error).lower() or "default" in str(error).lower():
                        test_result["fallback_detected"] = True
                        test_result["errors"].append(f"CRITICAL: Masked error with fallback: {error}")

        except Exception as e:
            test_result["warnings"].append(f"Fallback validation error: {e}")

    async def validate_categorization_result(self, test_case: dict, test_result: dict, workflow_result: Any):
        """Validate the categorization result against expected outcomes."""
        expected = test_case["expected_category"]
        actual = test_result["actual_category"]

        if isinstance(expected, list):
            # Ambiguous case - should trigger human consultation or confidence error
            if actual not in expected:
                test_result["errors"].append(f"Ambiguous case categorized incorrectly: expected {expected}, got {actual}")
            else:
                # Check if confidence is appropriately low for ambiguous cases
                confidence_score = test_result.get("confidence_score")
                if confidence_score is not None and confidence_score > 0.7:
                    test_result["warnings"].append(f"Ambiguous case has high confidence: {confidence_score}")
        else:
            # Clear case - must match exactly
            if actual != expected:
                test_result["errors"].append(f"Clear case categorized incorrectly: expected {expected}, got {actual}")

            # Special validation for URS-003 (MUST be Category 5, not ambiguous)
            if test_case["id"] == "URS-003" and actual != 5:
                test_result["errors"].append(f"CRITICAL: URS-003 must be clear Category 5, got {actual}")

    async def collect_phoenix_traces(self, urs_id: str) -> list[dict]:
        """Collect Phoenix traces for the test execution."""
        try:
            response = requests.get("http://localhost:6006/v1/traces", timeout=10)
            if response.status_code == 200:
                traces_data = response.json()
                # Filter traces related to this test
                relevant_traces = []
                for trace in traces_data.get("data", []):
                    if urs_id.lower() in str(trace).lower():
                        relevant_traces.append(trace)

                self.logger.info(f"Collected {len(relevant_traces)} Phoenix traces for {urs_id}")
                return relevant_traces
            self.logger.warning(f"Phoenix traces collection failed: {response.status_code}")
            return []

        except Exception as e:
            self.logger.warning(f"Phoenix trace collection error: {e}")
            return []

    async def validate_compliance(self, workflow_result: Any) -> list[str]:
        """Validate GAMP-5 compliance requirements."""
        violations = []

        try:
            # Check for audit trail
            if not hasattr(workflow_result, "audit_trail") or not workflow_result.audit_trail:
                violations.append("Missing audit trail - GAMP-5 compliance violation")

            # Check for electronic signatures where applicable
            if hasattr(workflow_result, "category") and workflow_result.category in [4, 5]:
                if not hasattr(workflow_result, "electronic_signature"):
                    violations.append("Missing electronic signature for Category 4/5 system")

            # Check for data integrity markers
            if not hasattr(workflow_result, "data_integrity_verified"):
                violations.append("Missing data integrity verification")

        except Exception as e:
            violations.append(f"Compliance validation error: {e}")

        return violations

    async def run_performance_benchmarks(self) -> dict[str, Any]:
        """Execute performance benchmarking tests."""
        self.logger.info("=== Running Performance Benchmarks ===")

        benchmark_results = {
            "total_execution_time": 0,
            "average_execution_time": 0,
            "phoenix_response_times": [],
            "memory_usage": {},
            "throughput": 0
        }

        try:
            # Calculate total and average execution times
            execution_times = []
            for result in self.results.values():
                if result.get("execution_time_seconds"):
                    execution_times.append(result["execution_time_seconds"])

            if execution_times:
                benchmark_results["total_execution_time"] = sum(execution_times)
                benchmark_results["average_execution_time"] = sum(execution_times) / len(execution_times)
                benchmark_results["throughput"] = len(execution_times) / sum(execution_times)

            # Test Phoenix response times
            phoenix_start = time.time()
            response = requests.get("http://localhost:6006/v1/traces", timeout=5)
            phoenix_time = time.time() - phoenix_start
            benchmark_results["phoenix_response_times"].append(phoenix_time)

        except Exception as e:
            self.logger.error(f"Performance benchmark error: {e}")

        return benchmark_results

    async def test_error_recovery(self) -> dict[str, Any]:
        """Test error recovery mechanisms."""
        self.logger.info("=== Testing Error Recovery ===")

        recovery_results = {
            "low_confidence_handling": "NOT_TESTED",
            "ambiguity_handling": "NOT_TESTED",
            "human_consultation_trigger": "NOT_TESTED",
            "explicit_error_propagation": "NOT_TESTED"
        }

        try:
            # Test low confidence scenario
            # This should trigger CONFIDENCE_ERROR, not fallback
            self.logger.info("Testing low confidence handling...")

            # Create a test case with intentionally ambiguous data
            test_data_path = Path("test_low_confidence.md")
            with open(test_data_path, "w") as f:
                f.write("""
# Ambiguous System Requirements

This system could be Category 3, 4, or 5 depending on interpretation.
It has unclear requirements that should trigger low confidence.

## Functional Requirements
- System requirements are vague
- Implementation approach is unclear  
- Vendor/custom boundary is undefined
""")

            workflow = UnifiedWorkflow()
            start_event = WorkflowStartEvent(
                workflow_id=f"error_recovery_test_{int(time.time())}",
                document_path=str(test_data_path),
                user_id="error_recovery_tester",
                gxp_context=True
            )

            try:
                result = await workflow.run(start_event)

                # Check if low confidence was handled properly
                if hasattr(result, "confidence_score") and result.confidence_score < 0.6:
                    if hasattr(result, "human_consultation_required") and result.human_consultation_required:
                        recovery_results["low_confidence_handling"] = "PASSED"
                        recovery_results["human_consultation_trigger"] = "PASSED"
                    else:
                        recovery_results["low_confidence_handling"] = "FAILED - No human consultation triggered"
                else:
                    recovery_results["low_confidence_handling"] = "FAILED - Confidence not appropriately low"

            except Exception as e:
                # This is GOOD - explicit error is better than fallback
                if "CONFIDENCE_ERROR" in str(e):
                    recovery_results["explicit_error_propagation"] = "PASSED"
                    recovery_results["low_confidence_handling"] = "PASSED"
                else:
                    recovery_results["explicit_error_propagation"] = "FAILED"

            # Clean up test file
            if test_data_path.exists():
                test_data_path.unlink()

        except Exception as e:
            self.logger.error(f"Error recovery testing failed: {e}")
            recovery_results["error"] = str(e)

        return recovery_results

    async def generate_comprehensive_report(self) -> str:
        """Generate comprehensive test report with honest assessment."""
        report_timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        report_path = f"docs/reports/task14_comprehensive_test_{report_timestamp}.md"

        # Ensure reports directory exists
        os.makedirs("docs/reports", exist_ok=True)

        # Calculate summary statistics
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results.values() if r["status"] == "PASSED"])
        failed_tests = len([r for r in self.results.values() if r["status"] == "FAILED"])
        critical_failures = len([r for r in self.results.values() if r["status"] == "CRITICAL_FAILURE"])

        fallback_violations = len([r for r in self.results.values() if r.get("fallback_detected", False)])
        compliance_violations = sum(len(r.get("compliance_violations", [])) for r in self.results.values())

        # Determine overall status
        if critical_failures > 0 or fallback_violations > 0:
            overall_status = "CRITICAL_FAILURE"
        elif failed_tests > passed_tests:
            overall_status = "FAILED"
        elif failed_tests > 0:
            overall_status = "CONDITIONAL_PASS"
        else:
            overall_status = "PASSED"

        report_content = f"""# Task 14 Comprehensive End-to-End Test Report

**Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Tester**: Task 14 End-to-End Testing Agent  
**Overall Status**: **{overall_status}**  

## Executive Summary

This report provides a comprehensive assessment of the pharmaceutical multi-agent system's end-to-end functionality, focusing on GAMP-5 compliance, Phoenix observability, and strict no-fallback enforcement.

**Key Findings:**
- **Total Tests Executed**: {total_tests}
- **Passed**: {passed_tests}
- **Failed**: {failed_tests} 
- **Critical Failures**: {critical_failures}
- **Fallback Violations Detected**: {fallback_violations}
- **Total Compliance Violations**: {compliance_violations}

## Critical Issues

### Fallback Violations
{self._generate_fallback_violations_section()}

### Compliance Failures  
{self._generate_compliance_failures_section()}

### Performance Issues
{self._generate_performance_issues_section()}

## Detailed Test Results

### URS Test Case Execution

{self._generate_urs_results_section()}

## Phoenix Observability Assessment

{self._generate_phoenix_assessment_section()}

## Error Recovery Validation

{self._generate_error_recovery_section()}

## Performance Benchmarks

{self._generate_performance_benchmarks_section()}

## Recommendations

### Immediate Actions Required
{self._generate_immediate_actions_section()}

### Performance Improvements
{self._generate_performance_improvements_section()}

### Compliance Strengthening
{self._generate_compliance_improvements_section()}

## Overall Assessment

**Final Verdict**: {overall_status}  
**Production Readiness**: {self._determine_production_readiness()}  
**Confidence Level**: {self._determine_confidence_level()}

## Evidence and Artifacts

- **Test Execution Log**: `task14_test_{self.test_start_time.strftime("%Y%m%d_%H%M%S")}.log`
- **Phoenix Traces**: Collected during execution
- **Audit Trails**: Available in `logs/audit/`
- **Event Logs**: Available in `logs/events/`

---
*Generated by Task 14 End-to-End Testing Agent*  
*Test Duration: {(datetime.now() - self.test_start_time).total_seconds():.2f} seconds*
"""

        # Write report to file
        with open(report_path, "w") as f:
            f.write(report_content)

        self.logger.info(f"Comprehensive report generated: {report_path}")
        return report_path

    def _generate_fallback_violations_section(self) -> str:
        """Generate fallback violations section."""
        violations = []
        for urs_id, result in self.results.items():
            if result.get("fallback_detected", False):
                violations.append(f"- **{urs_id}**: {result['name']}")
                for error in result.get("errors", []):
                    if "CRITICAL" in error and "fallback" in error.lower():
                        violations.append(f"  - {error}")

        if violations:
            return "\n".join(["**CRITICAL: Fallback behavior detected in the following tests:**"] + violations)
        return "No fallback violations detected. ✅"

    def _generate_compliance_failures_section(self) -> str:
        """Generate compliance failures section."""
        failures = []
        for urs_id, result in self.results.items():
            violations = result.get("compliance_violations", [])
            if violations:
                failures.append(f"- **{urs_id}**: {result['name']}")
                for violation in violations:
                    failures.append(f"  - {violation}")

        if failures:
            return "\n".join(["**Compliance violations detected:**"] + failures)
        return "No compliance violations detected. ✅"

    def _generate_performance_issues_section(self) -> str:
        """Generate performance issues section."""
        issues = []
        for urs_id, result in self.results.items():
            exec_time = result.get("execution_time_seconds", 0)
            if exec_time > 60:  # More than 60 seconds is concerning
                issues.append(f"- **{urs_id}**: Execution time {exec_time:.2f}s exceeds 60s threshold")

        if issues:
            return "\n".join(["**Performance issues detected:**"] + issues)
        return "No significant performance issues detected. ✅"

    def _generate_urs_results_section(self) -> str:
        """Generate detailed URS results section."""
        sections = []
        for urs_id, result in self.results.items():
            status_emoji = "✅" if result["status"] == "PASSED" else "❌" if result["status"] == "FAILED" else "🚨"

            section = f"""
#### {urs_id}: {result['name']} {status_emoji}

- **Status**: {result['status']}
- **Expected Category**: {result['expected_category']}
- **Actual Category**: {result['actual_category']}
- **Confidence Score**: {result.get('confidence_score', 'N/A')}
- **Execution Time**: {result.get('execution_time_seconds', 'N/A'):.2f}s
- **Fallback Detected**: {'YES 🚨' if result.get('fallback_detected') else 'NO ✅'}

**Issues:**
{chr(10).join(['- ' + error for error in result.get('errors', ['None'])])}

**Warnings:**
{chr(10).join(['- ' + warning for warning in result.get('warnings', ['None'])])}
"""
            sections.append(section)

        return "\n".join(sections)

    def _generate_phoenix_assessment_section(self) -> str:
        """Generate Phoenix observability assessment."""
        total_traces = sum(len(result.get("phoenix_traces", [])) for result in self.results.values())

        return f"""
**Phoenix Server Status**: Accessible at http://localhost:6006 ✅  
**Total Traces Collected**: {total_traces}  
**Trace Collection**: {'Working ✅' if total_traces > 0 else 'Not Working ❌'}  
**Real-time Monitoring**: {'Active ✅' if total_traces > 0 else 'Inactive ❌'}  

**Assessment**: {'Phoenix observability is functional' if total_traces > 0 else 'Phoenix observability may have issues'}
"""

    def _generate_error_recovery_section(self) -> str:
        """Generate error recovery validation section."""
        if hasattr(self, "recovery_results"):
            results = self.recovery_results
            return f"""
**Low Confidence Handling**: {results.get('low_confidence_handling', 'NOT_TESTED')}  
**Ambiguity Handling**: {results.get('ambiguity_handling', 'NOT_TESTED')}  
**Human Consultation Trigger**: {results.get('human_consultation_trigger', 'NOT_TESTED')}  
**Explicit Error Propagation**: {results.get('explicit_error_propagation', 'NOT_TESTED')}  
"""
        return "Error recovery testing was not completed."

    def _generate_performance_benchmarks_section(self) -> str:
        """Generate performance benchmarks section."""
        if hasattr(self, "benchmark_results"):
            results = self.benchmark_results
            return f"""
**Total Execution Time**: {results.get('total_execution_time', 'N/A'):.2f}s  
**Average Execution Time**: {results.get('average_execution_time', 'N/A'):.2f}s  
**Throughput**: {results.get('throughput', 'N/A'):.2f} tests/second  
**Phoenix Response Time**: {results.get('phoenix_response_times', [0])[0]:.3f}s  
"""
        return "Performance benchmarking was not completed."

    def _generate_immediate_actions_section(self) -> str:
        """Generate immediate actions required."""
        actions = []

        # Check for critical failures
        critical_failures = [r for r in self.results.values() if r["status"] == "CRITICAL_FAILURE"]
        if critical_failures:
            actions.append("- Fix critical workflow failures preventing execution")

        # Check for fallback violations
        fallback_violations = [r for r in self.results.values() if r.get("fallback_detected", False)]
        if fallback_violations:
            actions.append("- Remove ALL fallback logic - system must fail explicitly")

        # Check for URS-003 specific issues
        urs003_result = self.results.get("URS-003")
        if urs003_result and urs003_result["actual_category"] != 5:
            actions.append("- Fix URS-003 categorization - must be clear Category 5, not ambiguous")

        if not actions:
            actions.append("- No immediate critical actions required")

        return "\n".join(actions)

    def _generate_performance_improvements_section(self) -> str:
        """Generate performance improvement recommendations."""
        improvements = []

        # Check execution times
        slow_tests = [r for r in self.results.values() if r.get("execution_time_seconds", 0) > 30]
        if slow_tests:
            improvements.append("- Optimize workflow execution - some tests exceed 30s")

        # Check Phoenix performance
        if hasattr(self, "benchmark_results"):
            phoenix_times = self.benchmark_results.get("phoenix_response_times", [])
            if phoenix_times and max(phoenix_times) > 1.0:
                improvements.append("- Improve Phoenix response times")

        if not improvements:
            improvements.append("- Performance is within acceptable limits")

        return "\n".join(improvements)

    def _generate_compliance_improvements_section(self) -> str:
        """Generate compliance improvement recommendations."""
        improvements = []

        # Check for compliance violations
        total_violations = sum(len(r.get("compliance_violations", [])) for r in self.results.values())
        if total_violations > 0:
            improvements.append("- Address GAMP-5 compliance violations in audit trails and signatures")

        # Check for data integrity
        missing_integrity = [r for r in self.results.values() if "data integrity" in str(r.get("compliance_violations", []))]
        if missing_integrity:
            improvements.append("- Implement comprehensive data integrity verification")

        if not improvements:
            improvements.append("- Compliance requirements are being met")

        return "\n".join(improvements)

    def _determine_production_readiness(self) -> str:
        """Determine production readiness status."""
        critical_failures = len([r for r in self.results.values() if r["status"] == "CRITICAL_FAILURE"])
        fallback_violations = len([r for r in self.results.values() if r.get("fallback_detected", False)])

        if critical_failures > 0 or fallback_violations > 0:
            return "NOT READY - Critical issues must be resolved"

        failed_tests = len([r for r in self.results.values() if r["status"] == "FAILED"])
        total_tests = len(self.results)

        if failed_tests == 0:
            return "READY"
        if failed_tests / total_tests < 0.2:
            return "CONDITIONAL - Minor issues need resolution"
        return "NOT READY - Too many failures"

    def _determine_confidence_level(self) -> str:
        """Determine confidence level in assessment."""
        total_tests = len(self.results)
        if total_tests < 5:
            return "LOW - Insufficient test coverage"

        critical_failures = len([r for r in self.results.values() if r["status"] == "CRITICAL_FAILURE"])
        if critical_failures > 0:
            return "HIGH - Clear critical issues identified"

        return "MEDIUM - Good test coverage with reliable results"

    async def run_comprehensive_test(self):
        """Execute the complete comprehensive test suite."""
        self.logger.info("🚀 Starting Task 14 Comprehensive End-to-End Testing")

        try:
            # Phase 1: Environment Setup
            if not await self.setup_environment():
                self.logger.error("Environment setup failed - cannot proceed")
                return

            # Phase 2: Execute all URS test cases
            self.logger.info("=== Phase 2: URS Test Case Execution ===")
            for test_case in self.urs_test_cases:
                urs_id = test_case["id"]
                self.logger.info(f"Executing {urs_id}...")

                result = await self.execute_urs_test_case(test_case)
                self.results[urs_id] = result

                # Log immediate result
                self.logger.info(f"{urs_id} Result: {result['status']} - Category: {result.get('actual_category', 'N/A')}")

                # Brief pause between tests
                await asyncio.sleep(2)

            # Phase 3: Error Recovery Testing
            self.logger.info("=== Phase 3: Error Recovery Testing ===")
            self.recovery_results = await self.test_error_recovery()

            # Phase 4: Performance Benchmarking
            self.logger.info("=== Phase 4: Performance Benchmarking ===")
            self.benchmark_results = await self.run_performance_benchmarks()

            # Phase 5: Generate Report
            self.logger.info("=== Phase 5: Report Generation ===")
            report_path = await self.generate_comprehensive_report()

            # Summary
            self.logger.info("=== COMPREHENSIVE TEST COMPLETE ===")
            self.logger.info(f"Report generated: {report_path}")

            # Print key results
            total_tests = len(self.results)
            passed_tests = len([r for r in self.results.values() if r["status"] == "PASSED"])
            fallback_violations = len([r for r in self.results.values() if r.get("fallback_detected", False)])

            self.logger.info(f"Tests: {passed_tests}/{total_tests} passed")
            self.logger.info(f"Fallback violations: {fallback_violations}")

            if fallback_violations > 0:
                self.logger.error("🚨 CRITICAL: Fallback violations detected - system is NOT compliant")
            elif passed_tests == total_tests:
                self.logger.info("✅ All tests passed - system appears functional")
            else:
                self.logger.warning("⚠️ Some tests failed - review required")

        except Exception as e:
            self.logger.error(f"Comprehensive test execution failed: {e}")
            self.logger.error(traceback.format_exc())


async def main():
    """Main execution function."""
    tester = Task14ComprehensiveTester()
    await tester.run_comprehensive_test()


if __name__ == "__main__":
    asyncio.run(main())

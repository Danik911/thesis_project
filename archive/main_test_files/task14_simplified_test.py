#!/usr/bin/env python3
"""
Task 14 Simplified End-to-End Testing
====================================

This script executes comprehensive testing of all 5 URS cases by using the existing
main.py entry point and parsing results. This ensures we test the actual production
workflow path.

NO FALLBACK LOGIC - All errors must fail explicitly
"""

import asyncio
import logging
import os
import re
import subprocess
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

import requests


class Task14SimplifiedTester:
    """
    Simplified end-to-end tester that uses the actual main.py workflow.
    """

    def __init__(self):
        self.results = {}
        self.test_start_time = datetime.now()

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(f'task14_simplified_test_{self.test_start_time.strftime("%Y%m%d_%H%M%S")}.log'),
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
                "description": "Vendor-supplied temperature monitoring"
            },
            {
                "id": "URS-002",
                "name": "Laboratory Information Management System",
                "expected_category": 4,
                "expected_confidence": "high",
                "description": "Commercial LIMS with configuration"
            },
            {
                "id": "URS-003",
                "name": "Manufacturing Execution System",
                "expected_category": 5,
                "expected_confidence": "high",
                "description": "Custom-developed MES - MUST BE CLEAR CATEGORY 5"
            },
            {
                "id": "URS-004",
                "name": "Chromatography Data System",
                "expected_category": [3, 4],  # Ambiguous case
                "expected_confidence": "medium",
                "description": "CDS with mixed commercial/custom elements"
            },
            {
                "id": "URS-005",
                "name": "Clinical Trial Management System",
                "expected_category": [4, 5],  # Ambiguous case
                "expected_confidence": "medium",
                "description": "Hybrid CTMS with custom development"
            }
        ]

    async def setup_environment(self) -> bool:
        """Initialize testing environment and verify Phoenix connectivity."""
        self.logger.info("=== Task 14 Simplified Testing Setup ===")

        try:
            # Verify Phoenix server
            phoenix_status = await self.check_phoenix_server()
            if not phoenix_status:
                self.logger.warning("Phoenix server not accessible - continuing without observability")

            # Check test data files
            test_data_path = Path("tests/test_data/gamp5_test_data/testing_data.md")
            if not test_data_path.exists():
                self.logger.error(f"Critical test data missing: {test_data_path}")
                return False

            self.logger.info("Environment setup complete")
            return True

        except Exception as e:
            self.logger.error(f"Environment setup failed: {e}")
            return False

    async def check_phoenix_server(self) -> bool:
        """Verify Phoenix server is running."""
        try:
            response = requests.get("http://localhost:6006", timeout=5)
            if response.status_code == 200:
                self.logger.info("Phoenix server accessible")
                return True
            self.logger.warning(f"Phoenix server status: {response.status_code}")
            return False
        except Exception as e:
            self.logger.warning(f"Phoenix check failed: {e}")
            return False

    def create_individual_urs_file(self, test_case: dict) -> Path:
        """Create individual URS file for testing a specific case."""
        urs_id = test_case["id"]

        # Read the full testing data file
        full_data_path = Path("tests/test_data/gamp5_test_data/testing_data.md")
        with open(full_data_path, encoding="utf-8") as f:
            full_content = f.read()

        # Extract the specific URS section
        pattern = rf"## {urs_id}:.*?(?=## URS-|\Z)"
        match = re.search(pattern, full_content, re.DOTALL)

        if not match:
            raise ValueError(f"Could not find {urs_id} section in test data")

        urs_content = match.group(0)

        # Create individual test file
        test_file_path = Path(f"test_{urs_id.lower()}_individual.md")
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(f"# GAMP-5 Categorization Test - {urs_id}\n\n")
            f.write(urs_content)

        return test_file_path

    async def execute_urs_test_case(self, test_case: dict) -> dict[str, Any]:
        """Execute a single URS test case using main.py."""
        urs_id = test_case["id"]
        self.logger.info(f"=== Executing {urs_id}: {test_case['name']} ===")

        test_result = {
            "urs_id": urs_id,
            "name": test_case["name"],
            "expected_category": test_case["expected_category"],
            "start_time": datetime.now(),
            "status": "FAILED",
            "errors": [],
            "warnings": [],
            "execution_time_seconds": None,
            "actual_category": None,
            "confidence_score": None,
            "raw_output": "",
            "fallback_detected": False,
            "phoenix_traces_available": False
        }

        execution_start = time.time()
        individual_file = None

        try:
            # Create individual URS file for focused testing
            individual_file = self.create_individual_urs_file(test_case)

            # Execute main.py with the individual URS file
            cmd = [
                sys.executable, "main.py",
                str(individual_file),
                "--verbose",
                "--workflow-type", "categorization"
            ]

            self.logger.info(f"Running command: {' '.join(cmd)}")

            # Execute with timeout
            process = subprocess.run(
                cmd,
                check=False, capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout per test
                encoding="utf-8",
                errors="replace"  # Handle encoding issues gracefully
            )

            execution_time = time.time() - execution_start
            test_result["execution_time_seconds"] = execution_time
            test_result["raw_output"] = process.stdout + "\n" + process.stderr

            # Parse results from output
            if process.returncode == 0:
                self.logger.info(f"{urs_id} subprocess completed successfully")
                self.parse_workflow_output(test_result, process.stdout)
            else:
                self.logger.error(f"{urs_id} subprocess failed with return code {process.returncode}")
                test_result["errors"].append(f"Subprocess failed: return code {process.returncode}")
                # Still try to parse output for partial results
                self.parse_workflow_output(test_result, process.stdout + process.stderr)

            # Validate results
            self.validate_test_result(test_case, test_result)

        except subprocess.TimeoutExpired:
            execution_time = time.time() - execution_start
            test_result["execution_time_seconds"] = execution_time
            test_result["errors"].append("Test execution timed out after 120 seconds")
            test_result["status"] = "TIMEOUT"

        except Exception as e:
            execution_time = time.time() - execution_start
            test_result["execution_time_seconds"] = execution_time
            test_result["errors"].append(f"Execution failed: {e!s}")
            test_result["status"] = "CRITICAL_FAILURE"
            self.logger.error(f"{urs_id} failed: {e}")

        finally:
            # Clean up individual test file
            if individual_file and individual_file.exists():
                try:
                    individual_file.unlink()
                except Exception as e:
                    self.logger.warning(f"Failed to clean up test file: {e}")

        test_result["end_time"] = datetime.now()
        return test_result

    def parse_workflow_output(self, test_result: dict, output: str):
        """Parse workflow output to extract categorization results."""
        try:
            # Look for category information
            category_patterns = [
                r"Category:\s*(\d+)",
                r"GAMP\s*Category:\s*(\d+)",
                r"Categorized as.*Category\s*(\d+)",
                r"Category\s*(\d+)\s*determined",
            ]

            category_found = False
            for pattern in category_patterns:
                match = re.search(pattern, output, re.IGNORECASE)
                if match:
                    test_result["actual_category"] = int(match.group(1))
                    category_found = True
                    break

            # Look for confidence information
            confidence_patterns = [
                r"confidence.*?(\d+\.?\d*)%",
                r"confidence.*?(\d+\.?\d*)",
                r"Confidence Score:\s*(\d+\.?\d*)",
            ]

            for pattern in confidence_patterns:
                match = re.search(pattern, output, re.IGNORECASE)
                if match:
                    confidence_value = float(match.group(1))
                    # Convert percentage to decimal if needed
                    if confidence_value > 1.0:
                        confidence_value = confidence_value / 100.0
                    test_result["confidence_score"] = confidence_value
                    break

            # Check for fallback indicators
            fallback_indicators = [
                "fallback", "default", "assume", "generic",
                "standard approach", "typical", "conservative"
            ]

            output_lower = output.lower()
            for indicator in fallback_indicators:
                if indicator in output_lower:
                    test_result["fallback_detected"] = True
                    test_result["errors"].append(f"CRITICAL: Fallback indicator detected: '{indicator}'")

            # Check for success indicators
            success_indicators = [
                "categorization complete", "✅", "success",
                "workflow completed", "result:"
            ]

            if any(indicator in output_lower for indicator in success_indicators):
                if category_found and not test_result["fallback_detected"]:
                    test_result["status"] = "PASSED"
                else:
                    test_result["status"] = "PARTIAL"

            # Check for Phoenix traces
            if "phoenix" in output_lower and ("trace" in output_lower or "observability" in output_lower):
                test_result["phoenix_traces_available"] = True

        except Exception as e:
            test_result["warnings"].append(f"Output parsing error: {e}")

    def validate_test_result(self, test_case: dict, test_result: dict):
        """Validate test results against expectations."""
        expected = test_case["expected_category"]
        actual = test_result["actual_category"]

        if actual is None:
            test_result["errors"].append("No category determined by workflow")
            return

        if isinstance(expected, list):
            # Ambiguous case
            if actual not in expected:
                test_result["errors"].append(f"Ambiguous case incorrect: expected {expected}, got {actual}")
            else:
                # Check if confidence appropriately reflects ambiguity
                confidence = test_result.get("confidence_score")
                if confidence and confidence > 0.8:
                    test_result["warnings"].append(f"Ambiguous case has high confidence: {confidence}")
        # Clear case
        elif actual != expected:
            test_result["errors"].append(f"Clear case incorrect: expected {expected}, got {actual}")

            # Special check for URS-003
            if test_case["id"] == "URS-003" and actual != 5:
                test_result["errors"].append("CRITICAL: URS-003 MUST be Category 5, not ambiguous!")

        # Final status determination
        if test_result["fallback_detected"]:
            test_result["status"] = "CRITICAL_FAILURE"
        elif len(test_result["errors"]) == 0:
            test_result["status"] = "PASSED"
        elif "CRITICAL" in str(test_result["errors"]):
            test_result["status"] = "CRITICAL_FAILURE"
        else:
            test_result["status"] = "FAILED"

    async def check_phoenix_traces(self) -> dict[str, Any]:
        """Check if Phoenix collected traces during testing."""
        phoenix_status = {
            "server_accessible": False,
            "traces_collected": 0,
            "recent_traces": []
        }

        try:
            # Check server
            response = requests.get("http://localhost:6006", timeout=5)
            if response.status_code == 200:
                phoenix_status["server_accessible"] = True

                # Try to get traces
                traces_response = requests.get("http://localhost:6006/v1/traces", timeout=10)
                if traces_response.status_code == 200:
                    traces_data = traces_response.json()
                    phoenix_status["traces_collected"] = len(traces_data.get("data", []))

                    # Get recent traces (last hour)
                    recent_cutoff = time.time() - 3600
                    for trace in traces_data.get("data", [])[:10]:  # Check last 10 traces
                        phoenix_status["recent_traces"].append({
                            "timestamp": trace.get("start_time", "unknown"),
                            "duration": trace.get("duration", "unknown"),
                            "status": trace.get("status", "unknown")
                        })

        except Exception as e:
            self.logger.warning(f"Phoenix trace check failed: {e}")

        return phoenix_status

    def generate_comprehensive_report(self) -> str:
        """Generate comprehensive test report."""
        report_timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        report_path = f"docs/reports/task14_simplified_test_{report_timestamp}.md"

        # Ensure reports directory exists
        os.makedirs("docs/reports", exist_ok=True)

        # Calculate statistics
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results.values() if r["status"] == "PASSED"])
        failed_tests = len([r for r in self.results.values() if r["status"] == "FAILED"])
        critical_failures = len([r for r in self.results.values() if r["status"] == "CRITICAL_FAILURE"])
        timeouts = len([r for r in self.results.values() if r["status"] == "TIMEOUT"])

        fallback_violations = len([r for r in self.results.values() if r.get("fallback_detected", False)])

        # Determine overall status
        if critical_failures > 0 or fallback_violations > 0:
            overall_status = "CRITICAL_FAILURE"
        elif timeouts > 0:
            overall_status = "TIMEOUT"
        elif failed_tests > passed_tests:
            overall_status = "FAILED"
        elif failed_tests > 0:
            overall_status = "CONDITIONAL_PASS"
        else:
            overall_status = "PASSED"

        # Calculate performance metrics
        execution_times = [r.get("execution_time_seconds", 0) for r in self.results.values() if r.get("execution_time_seconds")]
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        max_execution_time = max(execution_times) if execution_times else 0

        report_content = f"""# Task 14 Simplified End-to-End Test Report

**Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Tester**: Task 14 Simplified Testing Agent  
**Overall Status**: **{overall_status}**  

## Executive Summary

This report provides an honest assessment of the pharmaceutical multi-agent system's 
end-to-end functionality using the actual production workflow (main.py).

**Key Results:**
- **Total Tests**: {total_tests}
- **Passed**: {passed_tests}
- **Failed**: {failed_tests}
- **Critical Failures**: {critical_failures}
- **Timeouts**: {timeouts}
- **Fallback Violations**: {fallback_violations}

**Performance:**
- **Average Execution Time**: {avg_execution_time:.2f} seconds
- **Maximum Execution Time**: {max_execution_time:.2f} seconds

## Critical Issues Assessment

### Fallback Violations {self._get_status_emoji(fallback_violations == 0)}
{self._generate_fallback_section()}

### URS-003 Validation {self._get_urs003_status_emoji()}
{self._generate_urs003_section()}

### Performance Issues {self._get_performance_status_emoji()}
{self._generate_performance_section()}

## Detailed Test Results

{self._generate_detailed_results()}

## Phoenix Observability Assessment

{self._generate_phoenix_section()}

## Recommendations

### Immediate Actions Required
{self._generate_immediate_actions()}

### Performance Improvements
{self._generate_performance_recommendations()}

### System Health
{self._generate_system_health_assessment()}

## Overall Assessment

**Final Verdict**: {overall_status}  
**Production Readiness**: {self._determine_production_readiness()}  
**Regulatory Compliance**: {self._assess_regulatory_compliance()}

**Key Findings:**
{self._generate_key_findings()}

---
*Generated by Task 14 Simplified Testing Agent*  
*Using actual production workflow path (main.py)*  
*Test Duration: {(datetime.now() - self.test_start_time).total_seconds():.1f} seconds*
"""

        # Write report
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        self.logger.info(f"Report generated: {report_path}")
        return report_path

    def _get_status_emoji(self, is_good: bool) -> str:
        return "✅" if is_good else "❌"

    def _get_urs003_status_emoji(self) -> str:
        urs003 = self.results.get("URS-003")
        if urs003 and urs003.get("actual_category") == 5:
            return "✅"
        return "❌"

    def _get_performance_status_emoji(self) -> str:
        execution_times = [r.get("execution_time_seconds", 0) for r in self.results.values()]
        max_time = max(execution_times) if execution_times else 0
        return "✅" if max_time < 60 else "⚠️" if max_time < 120 else "❌"

    def _generate_fallback_section(self) -> str:
        violations = [r for r in self.results.values() if r.get("fallback_detected", False)]
        if violations:
            content = ["**CRITICAL: Fallback behavior detected - System is NOT compliant**"]
            for result in violations:
                content.append(f"- **{result['urs_id']}**: {result['name']}")
                for error in result.get("errors", []):
                    if "fallback" in error.lower():
                        content.append(f"  - {error}")
            return "\n".join(content)
        return "No fallback violations detected. System properly fails explicitly. ✅"

    def _generate_urs003_section(self) -> str:
        urs003 = self.results.get("URS-003")
        if not urs003:
            return "URS-003 test was not executed."

        if urs003.get("actual_category") == 5:
            return f"URS-003 correctly categorized as Category 5. ✅\nConfidence: {urs003.get('confidence_score', 'N/A')}"
        return f"**CRITICAL**: URS-003 categorized as Category {urs003.get('actual_category')} instead of 5. This custom MES must be Category 5, not ambiguous. ❌"

    def _generate_performance_section(self) -> str:
        execution_times = [r.get("execution_time_seconds", 0) for r in self.results.values() if r.get("execution_time_seconds")]
        if not execution_times:
            return "No performance data available."

        avg_time = sum(execution_times) / len(execution_times)
        max_time = max(execution_times)

        if max_time > 120:
            return f"**Performance Issues Detected**: Maximum execution time {max_time:.1f}s exceeds 2-minute threshold. Average: {avg_time:.1f}s"
        if max_time > 60:
            return f"**Performance Warning**: Maximum execution time {max_time:.1f}s approaches 1-minute threshold. Average: {avg_time:.1f}s"
        return f"Performance within acceptable limits. Average: {avg_time:.1f}s, Maximum: {max_time:.1f}s ✅"

    def _generate_detailed_results(self) -> str:
        sections = []
        for urs_id in ["URS-001", "URS-002", "URS-003", "URS-004", "URS-005"]:
            result = self.results.get(urs_id)
            if not result:
                sections.append(f"### {urs_id}: NOT EXECUTED ❌")
                continue

            status_emoji = "✅" if result["status"] == "PASSED" else "❌"

            section = f"""### {urs_id}: {result['name']} {status_emoji}

**Status**: {result['status']}  
**Expected**: Category {result['expected_category']}  
**Actual**: Category {result.get('actual_category', 'N/A')}  
**Confidence**: {result.get('confidence_score', 'N/A')}  
**Execution Time**: {result.get('execution_time_seconds', 0):.1f}s  
**Fallback Detected**: {'YES 🚨' if result.get('fallback_detected') else 'NO ✅'}

**Issues:**
{chr(10).join(['- ' + error for error in result.get('errors', ['None'])])}

**Warnings:**
{chr(10).join(['- ' + warning for warning in result.get('warnings', ['None'])])}
"""
            sections.append(section)

        return "\n".join(sections)

    def _generate_phoenix_section(self) -> str:
        traces_available = any(r.get("phoenix_traces_available", False) for r in self.results.values())
        return f"""**Phoenix Server**: {'Accessible ✅' if hasattr(self, 'phoenix_accessible') and self.phoenix_accessible else 'Status Unknown'}  
**Trace Collection**: {'Active ✅' if traces_available else 'Not Detected ⚠️'}  
**Observability**: {'Functional' if traces_available else 'May need verification'}"""

    def _generate_immediate_actions(self) -> str:
        actions = []

        # Check critical failures
        critical_failures = [r for r in self.results.values() if r["status"] == "CRITICAL_FAILURE"]
        if critical_failures:
            actions.append("- **CRITICAL**: Fix workflow failures preventing execution")

        # Check fallback violations
        fallback_violations = [r for r in self.results.values() if r.get("fallback_detected", False)]
        if fallback_violations:
            actions.append("- **CRITICAL**: Remove ALL fallback logic - system must fail explicitly")

        # Check URS-003
        urs003 = self.results.get("URS-003")
        if urs003 and urs003.get("actual_category") != 5:
            actions.append("- **CRITICAL**: Fix URS-003 categorization - must be clear Category 5")

        # Check timeouts
        timeouts = [r for r in self.results.values() if r["status"] == "TIMEOUT"]
        if timeouts:
            actions.append("- **HIGH**: Resolve execution timeouts - may indicate system issues")

        if not actions:
            actions.append("- No immediate critical actions required")

        return "\n".join(actions)

    def _generate_performance_recommendations(self) -> str:
        recommendations = []

        execution_times = [r.get("execution_time_seconds", 0) for r in self.results.values() if r.get("execution_time_seconds")]
        if execution_times and max(execution_times) > 60:
            recommendations.append("- Optimize workflow execution time")

        failed_tests = [r for r in self.results.values() if r["status"] in ["FAILED", "CRITICAL_FAILURE"]]
        if len(failed_tests) > 0:
            recommendations.append("- Improve workflow reliability and error handling")

        if not recommendations:
            recommendations.append("- System performance appears adequate")

        return "\n".join(recommendations)

    def _generate_system_health_assessment(self) -> str:
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results.values() if r["status"] == "PASSED"])

        if total_tests == 0:
            return "No tests completed - system health unknown"

        success_rate = passed_tests / total_tests

        if success_rate >= 0.8:
            return f"System health: GOOD ({success_rate:.0%} success rate)"
        if success_rate >= 0.6:
            return f"System health: FAIR ({success_rate:.0%} success rate) - improvements needed"
        return f"System health: POOR ({success_rate:.0%} success rate) - significant issues"

    def _determine_production_readiness(self) -> str:
        critical_failures = len([r for r in self.results.values() if r["status"] == "CRITICAL_FAILURE"])
        fallback_violations = len([r for r in self.results.values() if r.get("fallback_detected", False)])

        if critical_failures > 0 or fallback_violations > 0:
            return "NOT READY - Critical compliance violations"

        passed_tests = len([r for r in self.results.values() if r["status"] == "PASSED"])
        total_tests = len(self.results)

        if total_tests == 0:
            return "UNKNOWN - No tests completed"

        success_rate = passed_tests / total_tests

        if success_rate >= 0.9:
            return "READY"
        if success_rate >= 0.7:
            return "CONDITIONAL - Some issues need resolution"
        return "NOT READY - Too many failures"

    def _assess_regulatory_compliance(self) -> str:
        fallback_violations = len([r for r in self.results.values() if r.get("fallback_detected", False)])

        if fallback_violations > 0:
            return "NON-COMPLIANT - Fallback behavior violates GAMP-5 requirements"

        urs003 = self.results.get("URS-003")
        if urs003 and urs003.get("actual_category") != 5:
            return "QUESTIONABLE - URS-003 categorization concerns"

        return "APPEARS COMPLIANT - No obvious violations detected"

    def _generate_key_findings(self) -> str:
        findings = []

        # Overall execution
        executed_tests = len([r for r in self.results.values() if r["status"] != "NOT_EXECUTED"])
        if executed_tests == 5:
            findings.append("✅ All 5 URS test cases were executed")
        else:
            findings.append(f"⚠️ Only {executed_tests}/5 URS test cases completed")

        # Fallback compliance
        fallback_violations = len([r for r in self.results.values() if r.get("fallback_detected", False)])
        if fallback_violations == 0:
            findings.append("✅ No fallback behavior detected - system fails explicitly")
        else:
            findings.append(f"❌ {fallback_violations} fallback violations detected - COMPLIANCE ISSUE")

        # URS-003 specific
        urs003 = self.results.get("URS-003")
        if urs003:
            if urs003.get("actual_category") == 5:
                findings.append("✅ URS-003 correctly identified as Category 5 (not ambiguous)")
            else:
                findings.append("❌ URS-003 incorrectly categorized - should be clear Category 5")

        # Performance
        execution_times = [r.get("execution_time_seconds", 0) for r in self.results.values() if r.get("execution_time_seconds")]
        if execution_times and max(execution_times) < 60:
            findings.append("✅ Execution times within acceptable limits")
        elif execution_times:
            findings.append("⚠️ Some tests exceeded 60-second threshold")

        return "\n".join(findings)

    async def run_comprehensive_test(self):
        """Execute the complete simplified test suite."""
        self.logger.info("🚀 Starting Task 14 Simplified End-to-End Testing")

        try:
            # Phase 1: Environment Setup
            if not await self.setup_environment():
                self.logger.error("Environment setup failed - cannot proceed")
                return

            # Check Phoenix before tests
            self.phoenix_accessible = await self.check_phoenix_server()

            # Phase 2: Execute all URS test cases
            self.logger.info("=== Executing All URS Test Cases ===")
            for test_case in self.urs_test_cases:
                urs_id = test_case["id"]
                self.logger.info(f"Starting {urs_id}...")

                result = await self.execute_urs_test_case(test_case)
                self.results[urs_id] = result

                # Log immediate result
                status = result["status"]
                category = result.get("actual_category", "N/A")
                confidence = result.get("confidence_score", "N/A")
                exec_time = result.get("execution_time_seconds", 0)

                self.logger.info(f"{urs_id} Complete: {status} | Category: {category} | Confidence: {confidence} | Time: {exec_time:.1f}s")

                # Brief pause between tests
                await asyncio.sleep(1)

            # Phase 3: Check Phoenix traces
            self.logger.info("=== Checking Phoenix Observability ===")
            phoenix_status = await self.check_phoenix_traces()
            self.logger.info(f"Phoenix traces: {phoenix_status.get('traces_collected', 0)} collected")

            # Phase 4: Generate Report
            self.logger.info("=== Generating Comprehensive Report ===")
            report_path = self.generate_comprehensive_report()

            # Final Summary
            self.logger.info("=== TASK 14 TESTING COMPLETE ===")
            self.logger.info(f"Report: {report_path}")

            total_tests = len(self.results)
            passed_tests = len([r for r in self.results.values() if r["status"] == "PASSED"])
            fallback_violations = len([r for r in self.results.values() if r.get("fallback_detected", False)])
            critical_failures = len([r for r in self.results.values() if r["status"] == "CRITICAL_FAILURE"])

            self.logger.info(f"Results: {passed_tests}/{total_tests} passed")
            self.logger.info(f"Critical failures: {critical_failures}")
            self.logger.info(f"Fallback violations: {fallback_violations}")

            if fallback_violations > 0:
                self.logger.error("🚨 CRITICAL: Fallback violations detected - SYSTEM NOT COMPLIANT")
            elif critical_failures > 0:
                self.logger.error("🚨 CRITICAL: System failures detected")
            elif passed_tests == total_tests:
                self.logger.info("✅ All tests passed - system functional")
            else:
                self.logger.warning("⚠️ Some tests failed - review needed")

            # Print report location for user
            print(f"\n📋 DETAILED REPORT: {os.path.abspath(report_path)}")

        except Exception as e:
            self.logger.error(f"Test execution failed: {e}")
            self.logger.error(traceback.format_exc())


async def main():
    """Main execution function."""
    tester = Task14SimplifiedTester()
    await tester.run_comprehensive_test()


if __name__ == "__main__":
    asyncio.run(main())

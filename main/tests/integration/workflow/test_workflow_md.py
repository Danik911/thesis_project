#!/usr/bin/env python3
"""
GAMP-5 Categorization Workflow Test Script - MD Data
====================================================

This script tests the GAMP-5 categorization workflow using the markdown test data.
It validates the workflow's ability to correctly categorize different types of 
pharmaceutical URS documents according to GAMP-5 standards.

Test Data Coverage:
- URS-001 (EMS): Target Category 3 - Environmental monitoring
- URS-002 (LIMS): Target Category 4 - Laboratory information system  
- URS-003 (MES): Target Category 5 - Custom manufacturing execution
- URS-004 (CDS): Ambiguous 3/4 - Chromatography data system
- URS-005 (CTMS): Ambiguous 4/5 - Clinical trial management

Author: Test Automation for Thesis Project
Date: 2025-01-28
"""

import asyncio
import logging
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Add main directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "main"))

try:
    from src.core.categorization_workflow import (
        GAMPCategorizationWorkflow,
        run_categorization_workflow,
    )
    from src.core.events import GAMPCategory
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the project root and main/ is in the path")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("workflow_test_results.log")
    ]
)
logger = logging.getLogger(__name__)

class WorkflowTester:
    """Test harness for GAMP-5 categorization workflow."""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.test_results = []
        self.test_data_file = Path(__file__).parent / "gamp5_test_data" / "testing_data.md"

    def parse_test_data(self) -> list[dict[str, Any]]:
        """Parse the MD test data file to extract URS examples."""
        try:
            with open(self.test_data_file, encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            logger.error(f"Test data file not found: {self.test_data_file}")
            return []

        test_cases = []

        # Split content by URS sections
        sections = content.split("## URS-")

        for i, section in enumerate(sections[1:], 1):  # Skip header section
            lines = section.strip().split("\n")
            if not lines:
                continue

            # Extract URS info from first few lines
            urs_number = f"URS-{lines[0].split(':')[0].strip()}"
            title = lines[0].split(":", 1)[1].strip() if ":" in lines[0] else "Unknown"

            # Extract target category
            target_category = None
            system_type = None

            for line in lines[1:5]:  # Check first few lines for metadata
                if line.startswith("**Target Category**:"):
                    cat_text = line.split(":", 1)[1].strip()
                    if "Ambiguous" in cat_text:
                        # Handle ambiguous cases like "Ambiguous 3/4"
                        cats = cat_text.replace("Ambiguous", "").strip().split("/")
                        target_category = [int(c.strip()) for c in cats if c.strip().isdigit()]
                    else:
                        # Handle clear cases like "3 (Clear)"
                        cat_num = cat_text.split()[0]
                        if cat_num.isdigit():
                            target_category = int(cat_num)
                elif line.startswith("**System Type**:"):
                    system_type = line.split(":", 1)[1].strip()

            # Extract the main content (everything after metadata)
            content_start = 0
            for j, line in enumerate(lines):
                if line.startswith("### 1. Introduction") or line.startswith("1. Introduction"):
                    content_start = j
                    break

            urs_content = "\n".join(lines[content_start:])

            test_case = {
                "urs_number": urs_number,
                "title": title,
                "target_category": target_category,
                "system_type": system_type,
                "content": urs_content,
                "full_section": section
            }

            test_cases.append(test_case)

        logger.info(f"Parsed {len(test_cases)} test cases from MD file")
        return test_cases

    async def test_single_case(
        self,
        test_case: dict[str, Any],
        workflow_config: dict[str, Any] = None
    ) -> dict[str, Any]:
        """Test a single URS case with the workflow."""
        urs_number = test_case["urs_number"]
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing {urs_number}: {test_case['title']}")
        logger.info(f"Expected Category: {test_case['target_category']}")
        logger.info(f"System Type: {test_case['system_type']}")
        logger.info(f"{'='*60}")

        # Default workflow configuration
        default_config = {
            "timeout": 300,
            "verbose": self.verbose,
            "enable_error_handling": True,
            "confidence_threshold": 0.60,
            "retry_attempts": 2,
            "enable_document_processing": False  # Start with basic mode
        }

        if workflow_config:
            default_config.update(workflow_config)

        start_time = time.time()

        try:
            # Run the workflow
            result = await run_categorization_workflow(
                urs_content=test_case["content"],
                document_name=f"{urs_number}.urs",
                document_version="1.0",
                author="test_automation",
                **default_config
            )

            execution_time = time.time() - start_time

            # Extract results
            categorization_event = result.get("categorization_event")
            summary = result.get("summary", {})

            actual_category = summary.get("category")
            confidence_score = summary.get("confidence", 0.0)
            review_required = summary.get("review_required", False)
            is_fallback = summary.get("is_fallback", False)

            # Determine success
            success = self._evaluate_success(
                test_case["target_category"],
                actual_category,
                confidence_score
            )

            test_result = {
                "urs_number": urs_number,
                "title": test_case["title"],
                "expected_category": test_case["target_category"],
                "actual_category": actual_category,
                "confidence_score": confidence_score,
                "review_required": review_required,
                "is_fallback": is_fallback,
                "execution_time": execution_time,
                "success": success,
                "justification": getattr(categorization_event, "justification", "") if categorization_event else "",
                "error": None,
                "raw_result": result
            }

            # Log results
            self._log_test_result(test_result)

            return test_result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Test failed for {urs_number}: {e}")

            return {
                "urs_number": urs_number,
                "title": test_case["title"],
                "expected_category": test_case["target_category"],
                "actual_category": None,
                "confidence_score": 0.0,
                "review_required": True,
                "is_fallback": True,
                "execution_time": execution_time,
                "success": False,
                "justification": "",
                "error": str(e),
                "raw_result": None
            }

    def _evaluate_success(self, expected, actual, confidence) -> bool:
        """Evaluate if the test result is successful."""
        if expected is None or actual is None:
            return False

        # Handle ambiguous cases (list of acceptable categories)
        if isinstance(expected, list):
            return actual in expected and confidence >= 0.5

        # Handle clear cases (exact match required)
        return actual == expected and confidence >= 0.7

    def _log_test_result(self, result: dict[str, Any]):
        """Log the test result in a readable format."""
        status = "✅ PASS" if result["success"] else "❌ FAIL"

        logger.info(f"\n{status} {result['urs_number']}")
        logger.info(f"Expected: {result['expected_category']}")
        logger.info(f"Actual: {result['actual_category']}")
        logger.info(f"Confidence: {result['confidence_score']:.1%}")
        logger.info(f"Review Required: {result['review_required']}")
        logger.info(f"Execution Time: {result['execution_time']:.2f}s")

        if result["error"]:
            logger.error(f"Error: {result['error']}")

        if result["justification"]:
            logger.info(f"Justification: {result['justification'][:200]}...")

    async def run_all_tests(self) -> dict[str, Any]:
        """Run all test cases and return comprehensive results."""
        logger.info("Starting GAMP-5 Categorization Workflow Tests")
        logger.info(f"Test data file: {self.test_data_file}")
        logger.info(f"Timestamp: {datetime.now(UTC).isoformat()}")

        # Parse test data
        test_cases = self.parse_test_data()

        if not test_cases:
            logger.error("No test cases found. Exiting.")
            return {"error": "No test cases found"}

        # Run tests
        results = []
        start_time = time.time()

        for test_case in test_cases:
            result = await self.test_single_case(test_case)
            results.append(result)
            self.test_results.append(result)

            # Brief pause between tests
            await asyncio.sleep(1)

        total_time = time.time() - start_time

        # Calculate summary statistics
        summary = self._calculate_summary(results, total_time)

        # Log final summary
        self._log_summary(summary)

        return {
            "summary": summary,
            "results": results,
            "test_cases": test_cases
        }

    def _calculate_summary(self, results: list[dict[str, Any]], total_time: float) -> dict[str, Any]:
        """Calculate summary statistics from test results."""
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r["success"])
        failed_tests = total_tests - passed_tests

        avg_execution_time = sum(r["execution_time"] for r in results) / total_tests if total_tests > 0 else 0
        avg_confidence = sum(r["confidence_score"] for r in results) / total_tests if total_tests > 0 else 0

        fallback_count = sum(1 for r in results if r["is_fallback"])
        review_required_count = sum(1 for r in results if r["review_required"])

        # Category distribution
        category_distribution = {}
        for result in results:
            if result["actual_category"]:
                cat = result["actual_category"]
                category_distribution[cat] = category_distribution.get(cat, 0) + 1

        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
            "total_execution_time": total_time,
            "avg_execution_time": avg_execution_time,
            "avg_confidence_score": avg_confidence,
            "fallback_count": fallback_count,
            "review_required_count": review_required_count,
            "category_distribution": category_distribution
        }

    def _log_summary(self, summary: dict[str, Any]):
        """Log the final test summary."""
        logger.info(f"\n{'='*60}")
        logger.info("WORKFLOW TEST SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Total Tests: {summary['total_tests']}")
        logger.info(f"Passed: {summary['passed_tests']} ({summary['success_rate']:.1%})")
        logger.info(f"Failed: {summary['failed_tests']}")
        logger.info(f"Average Confidence: {summary['avg_confidence_score']:.1%}")
        logger.info(f"Average Execution Time: {summary['avg_execution_time']:.2f}s")
        logger.info(f"Total Execution Time: {summary['total_execution_time']:.2f}s")
        logger.info(f"Fallback Cases: {summary['fallback_count']}")
        logger.info(f"Review Required: {summary['review_required_count']}")
        logger.info(f"Category Distribution: {summary['category_distribution']}")
        logger.info(f"{'='*60}")

async def main():
    """Main test execution function."""
    print("🧪 GAMP-5 Categorization Workflow Testing")
    print("==========================================")

    # Initialize tester
    tester = WorkflowTester(verbose=True)

    try:
        # Run all tests
        results = await tester.run_all_tests()

        if "error" in results:
            print(f"❌ Test execution failed: {results['error']}")
            return 1

        # Display results
        summary = results["summary"]

        print("\n🎯 Results Summary:")
        print(f"   Success Rate: {summary['success_rate']:.1%}")
        print(f"   Tests Passed: {summary['passed_tests']}/{summary['total_tests']}")
        print(f"   Average Confidence: {summary['avg_confidence_score']:.1%}")
        print(f"   Total Time: {summary['total_execution_time']:.1f}s")

        # Return appropriate exit code
        return 0 if summary["success_rate"] >= 0.8 else 1

    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        logger.exception("Unexpected error during testing")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

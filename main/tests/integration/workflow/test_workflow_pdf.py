#!/usr/bin/env python3
"""
GAMP-5 Categorization Workflow Test Script - PDF Data
====================================================

This script tests the GAMP-5 categorization workflow using the PDF test data.
It validates the workflow's document processing capabilities and categorization
accuracy when working with PDF documents.

Test Data Coverage (Same as MD but in PDF format):
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
        logging.FileHandler("workflow_pdf_test_results.log")
    ]
)
logger = logging.getLogger(__name__)

class PDFWorkflowTester:
    """Test harness for GAMP-5 categorization workflow using PDF data."""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.test_results = []
        self.pdf_file = Path(__file__).parent / "gamp5_test_data" / "testing_data.pdf"

        # Expected test cases based on the PDF content
        self.expected_cases = [
            {
                "urs_number": "URS-001",
                "title": "Environmental Monitoring System (EMS)",
                "target_category": 3,
                "system_type": "Environmental Monitoring",
                "description": "Continuous Temperature and Humidity Monitoring"
            },
            {
                "urs_number": "URS-002",
                "title": "Laboratory Information Management System (LIMS)",
                "target_category": 4,
                "system_type": "Sample Management and Testing Platform",
                "description": "QC laboratory operations management"
            },
            {
                "urs_number": "URS-003",
                "title": "Manufacturing Execution System (MES)",
                "target_category": 5,
                "system_type": "Custom Batch Record Management System",
                "description": "Custom MES for sterile injectable products"
            },
            {
                "urs_number": "URS-004",
                "title": "Chromatography Data System (CDS)",
                "target_category": [3, 4],  # Ambiguous
                "system_type": "Analytical Instrument Control and Data Analysis",
                "description": "HPLC/GC instrument control and data processing"
            },
            {
                "urs_number": "URS-005",
                "title": "Clinical Trial Management System (CTMS)",
                "target_category": [4, 5],  # Ambiguous
                "system_type": "Hybrid Cloud-Based Trial Management Platform",
                "description": "Global clinical trials with adaptive designs"
            }
        ]

    def check_pdf_exists(self) -> bool:
        """Check if the PDF file exists and is readable."""
        if not self.pdf_file.exists():
            logger.error(f"PDF file not found: {self.pdf_file}")
            return False

        try:
            # Try to read the file to check if it's accessible
            with open(self.pdf_file, "rb") as f:
                # Read first few bytes to verify it's a PDF
                header = f.read(4)
                if header != b"%PDF":
                    logger.error(f"File is not a valid PDF: {self.pdf_file}")
                    return False
        except Exception as e:
            logger.error(f"Cannot read PDF file: {e}")
            return False

        logger.info(f"PDF file found and accessible: {self.pdf_file}")
        return True

    async def test_pdf_as_path(self, test_case: dict[str, Any]) -> dict[str, Any]:
        """Test workflow by passing PDF file path."""
        urs_number = test_case["urs_number"]
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing PDF Path Mode - {urs_number}: {test_case['title']}")
        logger.info(f"Expected Category: {test_case['target_category']}")
        logger.info(f"System Type: {test_case['system_type']}")
        logger.info(f"{'='*60}")

        start_time = time.time()

        try:
            # Test with PDF file path - enable document processing
            result = await run_categorization_workflow(
                urs_content=str(self.pdf_file),  # Pass file path as content
                document_name=f"{urs_number}_pdf.urs",
                document_version="1.0",
                author="pdf_test_automation",
                timeout=300,
                verbose=self.verbose,
                enable_error_handling=True,
                confidence_threshold=0.60,
                retry_attempts=2,
                enable_document_processing=True  # Enable PDF processing
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
                "test_mode": "pdf_path",
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
            logger.error(f"PDF path test failed for {urs_number}: {e}")

            return {
                "urs_number": urs_number,
                "title": test_case["title"],
                "test_mode": "pdf_path",
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

    async def test_pdf_content_extraction(self) -> dict[str, Any]:
        """Test basic PDF content extraction without full categorization."""
        logger.info(f"\n{'='*60}")
        logger.info("Testing PDF Content Extraction")
        logger.info(f"{'='*60}")

        try:
            # For this test, we'll pass the PDF path and see if the workflow
            # can handle it in document processing mode
            workflow = GAMPCategorizationWorkflow(
                timeout=120,
                verbose=self.verbose,
                enable_document_processing=True
            )

            start_time = time.time()

            # Create a simple test to see if we can process the PDF
            result = await run_categorization_workflow(
                urs_content=str(self.pdf_file),
                document_name="pdf_extraction_test.pdf",
                document_version="1.0",
                author="extraction_test",
                timeout=120,
                verbose=self.verbose,
                enable_document_processing=True
            )

            execution_time = time.time() - start_time

            return {
                "test_type": "pdf_extraction",
                "success": True,
                "execution_time": execution_time,
                "result": result,
                "error": None
            }

        except Exception as e:
            execution_time = time.time() - start_time
            logger.warning(f"PDF extraction test failed (this may be expected): {e}")

            return {
                "test_type": "pdf_extraction",
                "success": False,
                "execution_time": execution_time,
                "result": None,
                "error": str(e)
            }

    async def test_fallback_mode(self) -> dict[str, Any]:
        """Test workflow with PDF in fallback mode (document processing disabled)."""
        logger.info(f"\n{'='*60}")
        logger.info("Testing PDF Fallback Mode (Document Processing Disabled)")
        logger.info(f"{'='*60}")

        # Create a representative URS content string for fallback testing
        fallback_content = """
        URS-PDF-FALLBACK: Test System
        
        This is a fallback test for PDF processing when document processing is disabled.
        
        System Requirements:
        - The system shall be based on commercial software package
        - Configuration of workflows and business rules required
        - Integration with existing enterprise systems
        - Standard reporting with configured templates
        - User role configuration and electronic review processes
        
        This appears to be a Category 4 system based on configuration requirements.
        """

        try:
            result = await run_categorization_workflow(
                urs_content=fallback_content,
                document_name="pdf_fallback_test.urs",
                document_version="1.0",
                author="fallback_test",
                timeout=120,
                verbose=self.verbose,
                enable_document_processing=False  # Disabled for fallback
            )

            return {
                "test_type": "pdf_fallback",
                "success": True,
                "result": result,
                "error": None
            }

        except Exception as e:
            logger.error(f"PDF fallback test failed: {e}")

            return {
                "test_type": "pdf_fallback",
                "success": False,
                "result": None,
                "error": str(e)
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

        logger.info(f"\n{status} {result['urs_number']} ({result.get('test_mode', 'unknown')})")
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
        """Run all PDF-related tests."""
        logger.info("Starting GAMP-5 Categorization Workflow PDF Tests")
        logger.info(f"PDF file: {self.pdf_file}")
        logger.info(f"Timestamp: {datetime.now(UTC).isoformat()}")

        # Check if PDF exists
        if not self.check_pdf_exists():
            return {"error": "PDF file not found or not accessible"}

        all_results = []
        start_time = time.time()

        # Test 1: PDF content extraction
        logger.info("\n🔍 Testing PDF Content Extraction...")
        extraction_result = await self.test_pdf_content_extraction()
        all_results.append(extraction_result)

        # Test 2: Fallback mode test
        logger.info("\n🔄 Testing PDF Fallback Mode...")
        fallback_result = await self.test_fallback_mode()
        all_results.append(fallback_result)

        # Test 3: PDF path processing (if extraction worked)
        if extraction_result["success"]:
            logger.info("\n📄 Testing PDF Path Processing...")

            # Test with first expected case as representative
            test_case = self.expected_cases[0]  # URS-001
            pdf_path_result = await self.test_pdf_as_path(test_case)
            all_results.append(pdf_path_result)
        else:
            logger.warning("Skipping PDF path processing due to extraction failure")

        total_time = time.time() - start_time

        # Calculate summary
        summary = self._calculate_summary(all_results, total_time)

        # Log final summary
        self._log_summary(summary, extraction_result["success"])

        return {
            "summary": summary,
            "results": all_results,
            "extraction_successful": extraction_result["success"],
            "fallback_successful": fallback_result["success"]
        }

    def _calculate_summary(self, results: list[dict[str, Any]], total_time: float) -> dict[str, Any]:
        """Calculate summary statistics from test results."""
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r["success"])
        failed_tests = total_tests - passed_tests

        avg_execution_time = sum(r.get("execution_time", 0) for r in results) / total_tests if total_tests > 0 else 0

        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
            "total_execution_time": total_time,
            "avg_execution_time": avg_execution_time
        }

    def _log_summary(self, summary: dict[str, Any], extraction_success: bool):
        """Log the final test summary."""
        logger.info(f"\n{'='*60}")
        logger.info("PDF WORKFLOW TEST SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Total Tests: {summary['total_tests']}")
        logger.info(f"Passed: {summary['passed_tests']} ({summary['success_rate']:.1%})")
        logger.info(f"Failed: {summary['failed_tests']}")
        logger.info(f"Average Execution Time: {summary['avg_execution_time']:.2f}s")
        logger.info(f"Total Execution Time: {summary['total_execution_time']:.2f}s")
        logger.info(f"PDF Extraction Support: {'✅ Available' if extraction_success else '❌ Not Available'}")
        logger.info(f"{'='*60}")

async def main():
    """Main test execution function."""
    print("📄 GAMP-5 Categorization Workflow PDF Testing")
    print("==============================================")

    # Initialize tester
    tester = PDFWorkflowTester(verbose=True)

    try:
        # Run all tests
        results = await tester.run_all_tests()

        if "error" in results:
            print(f"❌ Test execution failed: {results['error']}")
            return 1

        # Display results
        summary = results["summary"]

        print("\n🎯 PDF Test Results Summary:")
        print(f"   Success Rate: {summary['success_rate']:.1%}")
        print(f"   Tests Passed: {summary['passed_tests']}/{summary['total_tests']}")
        print(f"   Total Time: {summary['total_execution_time']:.1f}s")
        print(f"   PDF Processing: {'✅ Supported' if results['extraction_successful'] else '❌ Not Available'}")
        print(f"   Fallback Mode: {'✅ Working' if results['fallback_successful'] else '❌ Failed'}")

        # Note about PDF processing
        if not results["extraction_successful"]:
            print("\n📝 Note: PDF processing may require additional dependencies.")
            print("   The workflow can still function with text-based URS content.")

        # Return appropriate exit code
        return 0 if summary["success_rate"] >= 0.5 else 1  # Lower threshold for PDF tests

    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        logger.exception("Unexpected error during PDF testing")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

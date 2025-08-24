#!/usr/bin/env python3
"""
Test script for OSS model OQ generation JSON extraction functionality.

This script tests the enhanced JSON extraction capabilities added to handle
OSS model responses that include explanatory text and markdown formatting.
"""

import logging
import os
import sys

# Add the main directory to path to import modules
sys.path.append(os.path.dirname(__file__))

from src.agents.oq_generator.generator import (
    clean_unicode_characters,
    extract_json_from_mixed_response,
)
from src.agents.oq_generator.models import OQTestSuite

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_json_extraction():
    """Test JSON extraction from various OSS model response formats."""

    logger.info("Testing OSS model JSON extraction functionality...")

    # Test case 1: Standard markdown code block
    test_response_1 = """
    Here's your comprehensive OQ test suite for GAMP Category 5 pharmaceutical validation:

    ```json
    {
        "suite_id": "OQ-SUITE-1234",
        "gamp_category": 5,
        "document_name": "Test Document",
        "test_cases": [
            {
                "test_id": "OQ-001",
                "test_name": "Installation Verification Test",
                "test_category": "installation",
                "gamp_category": 5,
                "objective": "Verify proper system installation and configuration",
                "prerequisites": ["System hardware verified", "Network connectivity confirmed"],
                "test_steps": [
                    {
                        "step_number": 1,
                        "action": "Verify all system components are properly installed",
                        "expected_result": "All components present and configured correctly",
                        "data_to_capture": ["Component list", "Configuration settings"],
                        "verification_method": "visual_inspection"
                    }
                ],
                "acceptance_criteria": ["All installation requirements met"],
                "regulatory_basis": ["GAMP-5", "21 CFR Part 11"],
                "risk_level": "medium",
                "data_integrity_requirements": ["Audit trail maintained"],
                "urs_requirements": ["REQ-001"],
                "related_tests": [],
                "estimated_duration_minutes": 30,
                "required_expertise": ["System Administrator"]
            }
        ],
        "test_categories": {"installation": 1},
        "requirements_coverage": {"REQ-001": ["OQ-001"]},
        "risk_coverage": {"medium": 1},
        "compliance_coverage": {},
        "total_test_count": 1,
        "estimated_execution_time": 30,
        "coverage_percentage": 100.0,
        "generation_timestamp": "2025-08-08T12:00:00Z",
        "generation_method": "LLMTextCompletionProgram",
        "validation_approach": "GAMP Category 5 comprehensive validation",
        "created_by": "oq_generation_agent",
        "review_required": true,
        "pharmaceutical_compliance": {
            "alcoa_plus_compliant": true,
            "cfr_part11_compliant": true,
            "gamp5_compliant": true,
            "audit_trail_verified": true,
            "data_integrity_validated": true
        }
    }
    ```

    This test suite meets all GAMP-5 pharmaceutical validation requirements and ensures regulatory compliance.
    """

    # Test case 2: Generic code block without json tag
    test_response_2 = """
    Based on your requirements, I'll generate the OQ test suite:

    ```
    {
        "suite_id": "OQ-SUITE-5678",
        "gamp_category": 4,
        "document_name": "LIMS Configuration",
        "test_cases": [],
        "test_categories": {},
        "total_test_count": 0,
        "estimated_execution_time": 0
    }
    ```
    """

    # Test case 3: No markdown, just JSON in mixed text
    test_response_3 = """
    I understand your pharmaceutical validation needs. Here's the structured response:

    {"suite_id": "OQ-SUITE-9999", "gamp_category": 3, "document_name": "Simple Test", "test_cases": [], "test_categories": {}, "total_test_count": 0, "estimated_execution_time": 0}

    This should provide the basic structure you need for your validation process.
    """

    # Test case 4: Response with Unicode characters
    test_response_4 = """Here's your test suite:

    ```json\u200b
    {\ufeff
        "suite_id": "OQ-SUITE-1111",
        "gamp_category": 5,\u2028
        "document_name": "Unicode Test",
        "test_cases": [],
        "test_categories": {},
        "total_test_count": 0,
        "estimated_execution_time": 0\u2029
    }
    ```"""

    test_cases = [
        ("Standard markdown", test_response_1),
        ("Generic code block", test_response_2),
        ("No markdown", test_response_3),
        ("Unicode characters", test_response_4)
    ]

    results = []

    for test_name, response in test_cases:
        logger.info(f"\n--- Testing: {test_name} ---")

        try:
            # Test JSON extraction
            json_string, diagnostic_context = extract_json_from_mixed_response(response)

            logger.info("✅ JSON extracted successfully")
            logger.info(f"   Method: {diagnostic_context.get('extraction_method', 'unknown')}")
            logger.info(f"   Unicode issues: {diagnostic_context.get('unicode_issues_detected', False)}")
            logger.info(f"   JSON length: {len(json_string)} characters")

            # Test Pydantic validation
            import json
            json_data = json.loads(json_string)
            test_suite = OQTestSuite(**json_data)

            logger.info("✅ Pydantic validation successful")
            logger.info(f"   Suite ID: {test_suite.suite_id}")
            logger.info(f"   GAMP Category: {test_suite.gamp_category}")
            logger.info(f"   Test Count: {test_suite.total_test_count}")

            results.append((test_name, "SUCCESS", None))

        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            results.append((test_name, "FAILED", str(e)))

    # Summary
    logger.info("\n" + "="*50)
    logger.info("TEST SUMMARY")
    logger.info("="*50)

    successful = 0
    for test_name, status, error in results:
        if status == "SUCCESS":
            logger.info(f"✅ {test_name}: {status}")
            successful += 1
        else:
            logger.error(f"❌ {test_name}: {status} - {error}")

    logger.info(f"\nResults: {successful}/{len(results)} tests passed")

    return successful == len(results)


def test_unicode_cleaning():
    """Test Unicode character cleaning functionality."""

    logger.info("\nTesting Unicode character cleaning...")

    test_string = '\ufeff{"test": "value\u200b with\u200c invisible\u200d chars\u2028here\u2029"}'
    cleaned = clean_unicode_characters(test_string)

    logger.info(f"Original length: {len(test_string)}")
    logger.info(f"Cleaned length: {len(cleaned)}")
    logger.info(f"Characters removed: {len(test_string) - len(cleaned)}")

    expected = '{"test": "value with invisible chars here"}'

    if cleaned == expected:
        logger.info("✅ Unicode cleaning test passed")
        return True
    logger.error("❌ Unicode cleaning test failed")
    logger.error(f"Expected: {expected}")
    logger.error(f"Got: {cleaned}")
    return False


if __name__ == "__main__":
    logger.info("Starting OSS OQ JSON Extraction Tests")
    logger.info("="*60)

    # Run tests
    json_test_passed = test_json_extraction()
    unicode_test_passed = test_unicode_cleaning()

    # Overall result
    if json_test_passed and unicode_test_passed:
        logger.info("\n🎉 ALL TESTS PASSED - OSS JSON extraction is working!")
        sys.exit(0)
    else:
        logger.error("\n💥 SOME TESTS FAILED - Implementation needs fixes")
        sys.exit(1)

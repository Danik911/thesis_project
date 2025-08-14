#!/usr/bin/env python3
"""Test OQ Generator directly"""
import asyncio
from datetime import datetime

from dotenv import load_dotenv

# Load environment variables
load_dotenv("../.env")

# Set encoding for Windows
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from src.agents.oq_generator.models import OQTestGenerationRequest, ValidationContext
from src.agents.oq_generator.workflow import OQTestGenerationWorkflow


async def test_oq_generation():
    """Test OQ generation directly"""

    print("Testing OQ Generator directly...")
    print("This will generate actual OQ tests")

    # Create OQ workflow
    workflow = OQTestGenerationWorkflow(timeout=600.0)  # 10 minutes

    # Create test request
    request = OQTestGenerationRequest(
        document_name="test_document.md",
        gamp_category=5,
        test_count=3,  # Generate only 3 tests for quick testing
        validation_context=ValidationContext(
            compliance_level="GAMP-5",
            risk_level="high",
            test_types=["functional", "integration"],
            regulatory_requirements=["21 CFR Part 11", "EU Annex 11"]
        ),
        agent_context={
            "sme_recommendations": [
                {
                    "category": "Data Integrity",
                    "priority": "high",
                    "recommendation": "Implement audit trail testing"
                }
            ],
            "research_findings": {
                "regulatory_updates": ["FDA guidance on CSV updated 2024"]
            }
        },
        categorization_confidence=0.95
    )

    try:
        # Run the workflow
        result = await workflow.run(oq_request=request)

        if result:
            print(f"\nSUCCESS: Generated {len(result.test_suites[0].tests)} OQ tests")
            print(f"Test Suite ID: {result.test_suites[0].suite_id}")
            print(f"GAMP Category: {result.test_suites[0].gamp_category}")

            # Show first test as example
            if result.test_suites[0].tests:
                first_test = result.test_suites[0].tests[0]
                print("\nExample Test:")
                print(f"  ID: {first_test.test_id}")
                print(f"  Name: {first_test.test_name}")
                print(f"  Category: {first_test.test_category}")
                print(f"  Description: {first_test.description[:100]}...")

            # Save to file
            output_file = f"oq_test_suite_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, "w") as f:
                f.write(result.model_dump_json(indent=2))
            print(f"\nTest suite saved to: {output_file}")

        else:
            print("\nERROR: No result returned from OQ generator")

    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_oq_generation())

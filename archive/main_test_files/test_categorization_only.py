#!/usr/bin/env python3
"""Test just the categorization for URS-003"""

import asyncio
import sys
from pathlib import Path

# Add the main directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.categorization_workflow import GAMPCategorizationWorkflow
from src.core.events import URSIngestionEvent


async def test_categorization():
    """Test categorization for URS-003"""

    # Extract just URS-003 from the test file
    test_file = Path("tests/test_data/gamp5_test_data/testing_data.md")
    content = test_file.read_text()

    # Find URS-003 section
    start_marker = "## URS-003: Manufacturing Execution System (MES)"
    end_marker = "## URS-004:"

    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)

    if start_idx == -1:
        print("Could not find URS-003 in test file")
        return

    urs003_content = content[start_idx:end_idx].strip()

    print("Testing categorization for URS-003 (Manufacturing Execution System)")
    print("Expected Category: 5")
    print("-" * 60)

    try:
        # Run categorization workflow
        workflow = GAMPCategorizationWorkflow(
            confidence_threshold=0.6,
            verbose=True
        )

        event = URSIngestionEvent(
            document_path="temp_urs003.md",
            urs_content=urs003_content,
            document_name="URS-003: Manufacturing Execution System",
            document_version="1.0",
            author="Test User",
            session_id="test_session"
        )

        result = await workflow.run(event)

        # Print results
        if result and hasattr(result, "result"):
            final_result = result.result
            print("\nCategorization completed!")

            if "gamp_category" in final_result:
                print(f"GAMP Category: {final_result['gamp_category']}")
                print(f"Confidence: {final_result.get('confidence_score', 0):.2%}")
                print(f"Justification: {final_result.get('justification', 'N/A')}")
            else:
                print("No categorization result")

        else:
            print("\nCategorization failed to produce results")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_categorization())

#!/usr/bin/env python3
"""Test script specifically for URS-003 (Category 5)"""

import asyncio
import sys
from pathlib import Path

# Add the main directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.unified_workflow import UnifiedTestGenerationWorkflow


async def test_urs003():
    """Test URS-003 which should be Category 5"""

    # Extract just URS-003 from the test file
    test_file = Path("tests/test_data/gamp5_test_data/testing_data.md")
    content = test_file.read_text()

    # Find URS-003 section
    start_marker = "## URS-003: Manufacturing Execution System (MES)"
    end_marker = "## URS-004:"

    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)

    if start_idx == -1:
        print("❌ Could not find URS-003 in test file")
        return

    urs003_content = content[start_idx:end_idx].strip()

    # Save to temp file
    temp_file = Path("temp_urs003.md")
    temp_file.write_text(urs003_content)

    print("Testing with URS-003 (Manufacturing Execution System)")
    print("Expected Category: 5")
    print("-" * 60)

    try:
        # Run workflow
        workflow = UnifiedTestGenerationWorkflow(
            enable_phoenix=False,  # Disable for cleaner output
            enable_parallel_coordination=False,  # Disable to simplify
            enable_human_consultation=False,  # Disable consultation
            verbose=True
        )

        result = await workflow.run(
            document_path=str(temp_file),
            enable_document_processing=False
        )

        # Print results
        if result and hasattr(result, "result"):
            final_result = result.result
            print("\nWorkflow completed!")
            print(f"Status: {final_result.get('status', 'unknown')}")

            if cat_info := final_result.get("categorization"):
                print(f"GAMP Category: {cat_info.get('gamp_category')}")
                print(f"Confidence: {cat_info.get('confidence_score', 0):.2%}")

            if oq_info := final_result.get("oq_generation"):
                print(f"\nOQ Tests Generated: {oq_info.get('total_tests', 0)}")
                print(f"Test Suite ID: {oq_info.get('test_suite_id', 'N/A')}")
            else:
                print("\nNo OQ tests generated")

        else:
            print("\nWorkflow failed to produce results")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        if temp_file.exists():
            temp_file.unlink()

if __name__ == "__main__":
    asyncio.run(test_urs003())

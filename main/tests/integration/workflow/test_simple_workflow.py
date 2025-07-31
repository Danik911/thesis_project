#!/usr/bin/env python3

import asyncio
import sys
from pathlib import Path

# Add main to path
sys.path.insert(0, str(Path(__file__).parent / "main"))

from src.core.unified_workflow import run_unified_test_generation_workflow


async def test_unified_workflow():
    # Simple test URS content
    urs_content = """
    This is a pharmaceutical system that needs validation according to GAMP-5 guidelines.
    
    System Requirements:
    - Data integrity for patient records
    - Secure authentication and authorization  
    - Audit trail for all system activities
    - Compliance with 21 CFR Part 11
    
    The system is a custom software application developed specifically for pharmaceutical use.
    """

    try:
        print("Testing unified workflow...")
        result = await run_unified_test_generation_workflow(
            urs_content=urs_content,
            document_name="test_urs.md",
            timeout=60,  # Short timeout for testing
            verbose=False
        )

        print("Result received:")
        print(f"- Status: {result.get('workflow_metadata', {}).get('status', 'Unknown')}")
        print(f"- Duration: {result.get('workflow_metadata', {}).get('duration_seconds', 0):.2f}s")

        if result.get("categorization", {}).get("category"):
            print(f"- GAMP Category: {result['categorization']['category']}")

        return result

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_unified_workflow())
    if result:
        print("✅ Unified workflow test successful!")
    else:
        print("❌ Unified workflow test failed!")

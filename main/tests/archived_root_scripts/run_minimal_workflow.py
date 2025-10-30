#!/usr/bin/env python3
"""Run minimal workflow with only 3 tests for quick validation"""
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv("../.env")

# Redirect output to avoid terminal issues
sys.stdout = open("minimal_workflow.log", "w", buffering=1)
sys.stderr = sys.stdout

print("Starting MINIMAL workflow test (3 tests only)")
print("="*60)

from llama_index.llms.openai import OpenAI
from src.core.unified_workflow import UnifiedTestGenerationWorkflow


async def run_minimal_test():
    """Run workflow with minimal configuration"""

    # Create output directory
    output_dir = Path("output/test_suites")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create workflow with explicit configuration
    workflow = UnifiedTestGenerationWorkflow(
        llm=OpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY")),
        timeout=1200,  # 20 minutes total
        verbose=True
    )

    # Override test count in the workflow
    workflow.default_test_count = 3  # Only generate 3 tests

    try:
        result = await workflow.run(
            document_path="tests/test_data/gamp5_test_data/testing_data.md",
            test_suite_type="oq"
        )

        print("\nWORKFLOW COMPLETED!")
        print(f"Result: {result}")

        # Check for files
        json_files = list(output_dir.glob("*.json"))
        print(f"\nFound {len(json_files)} output files")

        return result

    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(run_minimal_test())

    # Summary to console
    print("\nDONE - Check minimal_workflow.log for details")

    # Check for output files
    output_dir = Path("output/test_suites")
    json_files = list(output_dir.glob("*.json"))

    if json_files:
        print(f"\nSUCCESS! Generated {len(json_files)} test suite files:")
        for f in json_files:
            print(f"  - {f.name}")

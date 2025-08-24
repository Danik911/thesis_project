#!/usr/bin/env python3
"""Run the complete workflow and monitor for output files"""
import asyncio
import time
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv("../.env")

# Import after loading env vars
from src.core.unified_workflow import run_unified_test_generation_workflow


async def monitor_workflow():
    """Run workflow and monitor output directory"""

    print("Starting COMPLETE workflow test...")
    print("This will generate the FINAL OQ test script")
    print("Monitoring output/test_suites/ directory for results")
    print("="*60)

    # Create output directory
    output_dir = Path("output/test_suites")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Start monitoring in background
    start_time = time.time()

    # Run workflow with fewer tests for faster completion
    try:
        # Note: We'll modify the workflow to generate only 3 tests for testing
        result = await run_unified_test_generation_workflow(
            document_path="tests/test_data/gamp5_test_data/testing_data.md",
            test_suite_type="oq",
            test_count=3  # Generate only 3 tests for faster completion
        )

        print(f"\nWorkflow completed in {time.time() - start_time:.1f} seconds")

    except Exception as e:
        print(f"\nERROR during workflow: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

    # Check for output files
    print("\n" + "="*60)
    print("Checking for output files...")

    json_files = list(output_dir.glob("*.json"))
    if json_files:
        print(f"\nSUCCESS! Found {len(json_files)} test suite files:")
        for f in json_files:
            print(f"  - {f.name} ({f.stat().st_size} bytes)")

            # Show first 500 chars of content
            with open(f) as file:
                content = file.read()
                print(f"\nFirst 500 characters of {f.name}:")
                print(content[:500])
                print("...")
    else:
        print("\nWARNING: No test suite JSON files found in output/test_suites/")

        # Check if files exist elsewhere
        all_json = list(Path().rglob("test_suite*.json"))
        if all_json:
            print(f"\nFound {len(all_json)} test suite files in other locations:")
            for f in all_json[:5]:  # Show first 5
                print(f"  - {f}")

if __name__ == "__main__":
    asyncio.run(monitor_workflow())

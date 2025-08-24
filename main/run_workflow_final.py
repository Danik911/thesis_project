#!/usr/bin/env python3
"""Run the complete workflow and wait for final results"""
import asyncio
import os
import time
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv("../.env")

# Set encoding
os.environ["PYTHONIOENCODING"] = "utf-8"

from src.core.unified_workflow import run_unified_test_generation_workflow


async def run_final_workflow():
    """Run workflow to completion"""

    print("="*80)
    print("RUNNING COMPLETE PHARMACEUTICAL WORKFLOW")
    print("This will generate the FINAL OQ test script")
    print("Expected duration: 5-10 minutes")
    print("="*80)

    # Create output directory
    output_dir = Path("output/test_suites")
    output_dir.mkdir(parents=True, exist_ok=True)

    start_time = time.time()

    try:
        # Run the complete workflow
        print("\n[1/5] Starting workflow...")
        result = await run_unified_test_generation_workflow(
            document_path="tests/test_data/gamp5_test_data/testing_data.md",
            test_suite_type="oq"
        )

        elapsed = time.time() - start_time
        print(f"\n[5/5] Workflow completed in {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")

        # Check for results
        if result and isinstance(result, dict):
            print("\nWORKFLOW RESULT:")
            print(f"- Status: {result.get('status', 'unknown')}")
            print(f"- Workflow Type: {result.get('workflow_type', 'unknown')}")

            if "test_suite" in result:
                print("\nTEST SUITE GENERATED:")
                print(f"- Suite ID: {result['test_suite'].get('suite_id')}")
                print(f"- Test Count: {result['test_suite'].get('total_test_count')}")
                print(f"- Coverage: {result['test_suite'].get('coverage_percentage')}%")

            if "output_file" in result:
                print(f"\nOUTPUT FILE: {result['output_file']}")

        # Check for physical files
        json_files = list(output_dir.glob("*.json"))

        print("\n" + "="*80)
        if json_files:
            print(f"SUCCESS! Found {len(json_files)} test suite files:")
            for f in json_files:
                print(f"\n📄 {f.name} ({f.stat().st_size:,} bytes)")

                # Show content preview
                with open(f) as file:
                    content = file.read()

                # Parse JSON to show test count
                import json
                data = json.loads(content)
                if "test_suite" in data and "tests" in data["test_suite"]:
                    test_count = len(data["test_suite"]["tests"])
                    print(f"   Contains {test_count} OQ tests")

                    # Show first test as example
                    if test_count > 0:
                        first_test = data["test_suite"]["tests"][0]
                        print("\n   Example Test:")
                        print(f"   - ID: {first_test.get('test_id')}")
                        print(f"   - Name: {first_test.get('test_name')}")
                        print(f"   - Category: {first_test.get('test_category')}")
                        print(f"   - Priority: {first_test.get('priority')}")
        else:
            print("WARNING: No test suite files found in output/test_suites/")

            # Check other locations
            all_json = list(Path().rglob("test_suite*.json"))
            if all_json:
                print("\nFound files in other locations:")
                for f in all_json[:3]:
                    print(f"  - {f}")

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\nERROR after {elapsed:.1f} seconds: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*80)
    print("WORKFLOW EXECUTION COMPLETE")

if __name__ == "__main__":
    # Run without asyncio debug for cleaner output
    asyncio.run(run_final_workflow())

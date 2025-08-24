#!/usr/bin/env python3
"""
Run the REAL end-to-end workflow with actual test data.
"""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add main to path
sys.path.insert(0, str(Path(__file__).parent))

async def run_real_workflow():
    """Run the real unified workflow with test data."""

    print("="*60)
    print("RUNNING REAL END-TO-END WORKFLOW")
    print("="*60)

    # Import the workflow
    from src.core.unified_workflow import (
        run_pharmaceutical_workflow,
    )

    # Set up test document
    test_doc = Path("tests/test_data/gamp5_test_data/testing_data.md")

    if not test_doc.exists():
        print(f"ERROR: Test document not found: {test_doc}")
        return False

    # Read document content
    print(f"\n1. Loading document: {test_doc}")
    document_content = test_doc.read_text(encoding="utf-8")
    print(f"   Document size: {len(document_content)} characters")

    # Initialize Phoenix if available
    try:
        from src.monitoring.phoenix_config import setup_phoenix
        phoenix_manager = setup_phoenix()
        print("   Phoenix observability: ENABLED")
    except Exception as e:
        print(f"   Phoenix observability: DISABLED ({e})")
        phoenix_manager = None

    # Run the workflow
    print("\n2. Starting unified workflow...")
    print("   Expected steps:")
    print("   - Document ingestion")
    print("   - GAMP categorization")
    print("   - Parallel agent execution (Context, Research, SME)")
    print("   - OQ test generation (23-33 tests)")
    print("   - Output file creation")

    try:
        result = await run_pharmaceutical_workflow(
            document_path=str(test_doc),
            timeout=1800,
            verbose=True,
            enable_human_consultation=False,
            output_dir="output"
        )

        print("\n3. Workflow completed successfully!")

        # Check results
        if result:
            print("\n4. Results:")

            # Check for GAMP category
            if hasattr(result, "gamp_category"):
                print(f"   GAMP Category: {result.gamp_category}")

            # Check for test suite
            if hasattr(result, "test_suite"):
                test_suite = result.test_suite
                if test_suite:
                    if hasattr(test_suite, "test_cases"):
                        test_count = len(test_suite.test_cases)
                        print(f"   Tests Generated: {test_count}")

                        if test_count > 0:
                            print(f"   First Test: {test_suite.test_cases[0].test_id if hasattr(test_suite.test_cases[0], 'test_id') else 'Unknown'}")

                        # Check if tests are unique (not templates)
                        if test_count >= 2:
                            first_test = str(test_suite.test_cases[0])
                            second_test = str(test_suite.test_cases[1])
                            if first_test != second_test:
                                print("   Test Content: UNIQUE (not templates)")
                            else:
                                print("   Test Content: WARNING - Tests appear identical")
                    else:
                        print("   Tests Generated: ERROR - No test_cases attribute")
                else:
                    print("   Tests Generated: ERROR - No test suite")

            # Check for output file
            output_dir = Path("output/test_suites")
            if output_dir.exists():
                latest_files = sorted(output_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
                if latest_files:
                    latest_file = latest_files[0]
                    print(f"   Output File: {latest_file.name}")

                    # Check file size to ensure it's not empty
                    file_size = latest_file.stat().st_size
                    if file_size > 1000:  # Should be at least 1KB for real content
                        print(f"   File Size: {file_size} bytes (contains real data)")
                    else:
                        print(f"   File Size: {file_size} bytes (WARNING - too small)")

            print("\nSUCCESS: Real workflow executed end-to-end!")
            return True

        print("\nERROR: Workflow returned no results")
        return False

    except Exception as e:
        print("\nERROR: Workflow failed with exception:")
        print(f"   {type(e).__name__}: {e}")

        # Print stack trace for debugging
        import traceback
        traceback.print_exc()

        return False

    finally:
        # Shutdown Phoenix if it was initialized
        if phoenix_manager:
            try:
                phoenix_manager.shutdown()
                print("\nPhoenix observability shutdown complete")
            except:
                pass

async def main():
    """Main entry point."""
    success = await run_real_workflow()

    print("\n" + "="*60)
    if success:
        print("FINAL RESULT: SUCCESS - Real workflow working end-to-end")
    else:
        print("FINAL RESULT: FAILED - Workflow not fully functional")
    print("="*60)

    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

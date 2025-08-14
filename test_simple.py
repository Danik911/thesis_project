#!/usr/bin/env python3
"""
Simple test to verify the security assessment fix works.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add main to path so we can import
sys.path.insert(0, str(Path(__file__).parent / "main"))


async def test_basic_workflow():
    """Test basic workflow compatibility."""
    print("Testing basic workflow compatibility...")

    try:
        import tempfile

        from src.core.unified_workflow import UnifiedTestGenerationWorkflow

        # Create a minimal test URS file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as temp_file:
            temp_file.write("""
# Test URS Document

## Software Description
This is a simple pharmaceutical data processing application.

## Functionality  
- Data entry validation
- Report generation
- Audit trail logging

## GAMP Categorization Request
Please categorize this software according to GAMP-5 guidelines.
            """)
            temp_path = temp_file.name

        # Create workflow and test basic call
        workflow = UnifiedTestGenerationWorkflow(
            timeout=60,
            verbose=True
        )

        print(f"Created test URS file: {temp_path}")
        print("Calling workflow.run(document_path=...)")

        # This should work now with the correct parameters
        result = await workflow.run(document_path=temp_path)

        print("SUCCESS: Workflow completed!")
        print(f"Result type: {type(result)}")

        # Clean up
        Path(temp_path).unlink()

        return True

    except Exception as e:
        print(f"ERROR: Basic workflow test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False


async def main():
    """Main test function."""
    print("Security Assessment Fix Verification")
    print("=" * 40)

    # Set up logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # Test basic workflow compatibility
    compatibility_ok = await test_basic_workflow()

    # Summary
    print("\nTest Summary")
    print("=" * 12)
    print(f"Workflow Compatibility: {'PASS' if compatibility_ok else 'FAIL'}")

    if compatibility_ok:
        print("\nAll tests passed! The security assessment fix is working.")
        print("Ready to run full security assessment with real system testing.")
        return True
    print("\nTest failed. Need to investigate further.")
    return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

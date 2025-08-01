#!/usr/bin/env uv run python
"""
Quick test script for the unified workflow integration.

This script tests whether the unified workflow system is properly integrated
and can run without errors.
"""

import asyncio
import sys
from pathlib import Path

# Add the main directory to the path
sys.path.insert(0, str(Path(__file__).parent / "main"))

from src.core.unified_workflow import (
    UnifiedTestGenerationWorkflow,
    run_unified_test_generation_workflow,
)


async def test_unified_workflow():
    """Test the unified workflow with sample URS content."""

    sample_urs_content = """
    # Sample User Requirements Specification
    
    ## System Description
    This is a sample pharmaceutical system for testing purposes.
    
    ## Requirements
    1. The system shall provide data validation capabilities
    2. The system shall maintain audit trails
    3. The system shall support electronic signatures
    
    ## Technical Details
    - Database: PostgreSQL
    - Framework: Web-based application
    - Integration: REST APIs with laboratory instruments
    """

    print("🧪 Testing Unified Test Generation Workflow Integration")
    print("=" * 60)

    try:
        print("📋 Creating unified workflow instance...")
        workflow = UnifiedTestGenerationWorkflow(
            timeout=60,  # Short timeout for test
            verbose=True,
            enable_error_handling=True,
            confidence_threshold=0.60,
            enable_document_processing=False,  # Disable for test
            enable_parallel_coordination=False  # Disable for test
        )
        print("✅ Workflow instance created successfully")

        print("\n🚀 Running unified workflow test...")
        result = await run_unified_test_generation_workflow(
            urs_content=sample_urs_content,
            document_name="test_urs.md",
            document_version="1.0",
            author="test_user",
            timeout=60,
            verbose=True,
            enable_error_handling=True,
            confidence_threshold=0.60,
            enable_document_processing=False,
            enable_parallel_coordination=False
        )

        print("\n✅ Workflow completed successfully!")
        print(f"📊 Result type: {type(result)}")

        if result:
            # Display basic result information
            workflow_metadata = result.get("workflow_metadata", {})
            summary = result.get("summary", {})
            categorization = result.get("categorization", {})

            print("\n📋 Workflow Summary:")
            print(f"  - Session ID: {workflow_metadata.get('session_id', 'N/A')}")
            print(f"  - Status: {workflow_metadata.get('status', 'N/A')}")
            print(f"  - Duration: {workflow_metadata.get('duration_seconds', 0):.2f}s")
            print(f"  - Workflow Type: {workflow_metadata.get('workflow_type', 'N/A')}")

            if categorization:
                print("\n🏷️ GAMP Categorization:")
                print(f"  - Category: {categorization.get('category', 'N/A')}")
                print(f"  - Confidence: {categorization.get('confidence', 0):.1%}")
                print(f"  - Review Required: {categorization.get('review_required', 'N/A')}")

            print(f"\n📈 Summary Status: {summary.get('status', 'N/A')}")

            consultation = result.get("consultation", {})
            if consultation.get("required"):
                print(f"👥 Consultation Required: {consultation.get('event', {}).get('consultation_type', 'N/A')}")

        return True

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    success = await test_unified_workflow()

    if success:
        print("\n🎉 Unified workflow integration test PASSED!")
        print("The system is ready for end-to-end pharmaceutical test generation.")
        return 0
    print("\n💥 Unified workflow integration test FAILED!")
    print("Please check the error messages above and fix any issues.")
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

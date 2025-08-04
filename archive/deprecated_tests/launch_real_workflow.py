#!/usr/bin/env uv run python
"""
Launch the real GAMP-5 categorization workflow for testing.
This script runs the actual workflow implementation, not a test.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the main directory to Python path
sys.path.append(str(Path(__file__).parent / "main"))

from src.core.categorization_workflow import run_categorization_workflow


def setup_logging():
    """Setup concise logging to avoid terminal overload."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("workflow_execution.log")
        ]
    )

    # Reduce noise from verbose libraries
    logging.getLogger("llama_index").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


async def run_workflow_on_md_file():
    """Run the real workflow on the MD test data."""
    print("🚀 Launching REAL GAMP-5 Categorization Workflow")
    print("=" * 60)

    # Read the test data
    test_file = Path("gamp5_test_data/testing_data.md")
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return None

    print(f"📄 Processing: {test_file}")
    content = test_file.read_text()

    try:
        # Run the REAL workflow
        result = await run_categorization_workflow(
            urs_content=content,
            document_name=test_file.name,
            document_version="1.0",
            author="test_runner",
            verbose=False,  # Reduce verbosity to prevent terminal kill
            timeout=300,
            enable_error_handling=True,
            confidence_threshold=0.60,
            retry_attempts=2,
            enable_document_processing=False  # Disable to avoid complexity
        )

        print("\n✅ WORKFLOW COMPLETED SUCCESSFULLY!")
        print("=" * 60)

        # Extract and display results
        summary = result.get("summary", {})
        print(f"🏷️  GAMP Category: {summary.get('category', 'Unknown')}")
        print(f"🎯 Confidence: {summary.get('confidence', 0):.1%}")
        print(f"👁️  Review Required: {summary.get('review_required', True)}")
        print(f"⏱️  Duration: {summary.get('workflow_duration_seconds', 0):.2f}s")

        # Show categorization details
        if "categorization_event" in result:
            cat_event = result["categorization_event"]
            print(f"\n📋 Justification: {cat_event.justification[:200]}...")
            print(f"🔍 Risk Assessment: {cat_event.risk_assessment.get('risk_level', 'unknown')}")

        # Show consultation if required
        if result.get("consultation_event"):
            print("\n⚠️  Human consultation required")
            print(f"   Urgency: {result['consultation_event'].urgency}")

        print("\n" + "=" * 60)
        print("✅ Real workflow execution completed successfully!")

        return result

    except Exception as e:
        print(f"\n❌ WORKFLOW FAILED: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Main execution function."""
    setup_logging()

    print("🧪 GAMP-5 Categorization Workflow - REAL EXECUTION")
    print("This is the actual workflow, not a test or simulation")
    print()

    # Run on MD file first
    result = await run_workflow_on_md_file()

    if result:
        print("\n🎉 SUCCESS: Real workflow executed successfully!")
        print("📝 Check workflow_execution.log for detailed logs")
    else:
        print("\n💥 FAILURE: Workflow execution failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

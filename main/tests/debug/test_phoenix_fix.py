#!/usr/bin/env uv run python
"""Test script to verify Phoenix observability fix."""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add main directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.shared.output_manager import safe_print


async def test_phoenix_observability():
    """Test Phoenix observability with proper shutdown."""
    safe_print("🧪 Testing Phoenix Observability Fix")
    safe_print("=" * 50)

    # Import after path setup
    from src.core.categorization_workflow import run_categorization_workflow
    from src.shared import setup_event_logging, shutdown_event_logging

    try:
        # Setup event logging (which initializes Phoenix)
        safe_print("📊 Setting up event logging with Phoenix...")
        event_handler = setup_event_logging()

        # Give Phoenix a moment to initialize
        await asyncio.sleep(2)

        # Run a simple categorization workflow
        safe_print("\n🚀 Running test categorization workflow...")
        result = await run_categorization_workflow(
            urs_content="Simple test URS for a pharmaceutical system that requires GAMP-5 categorization.",
            document_name="test_phoenix_fix.txt",
            enable_error_handling=True,
            verbose=True
        )

        if result:
            safe_print("\n✅ Workflow completed successfully")
            summary = result.get("summary", {})
            safe_print(f"  - Category: {summary.get('category', 'Unknown')}")
            safe_print(f"  - Confidence: {summary.get('confidence', 0):.1%}")

        # Give time for spans to be exported
        safe_print("\n⏳ Waiting for trace export...")
        await asyncio.sleep(3)

    except Exception as e:
        safe_print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Ensure proper shutdown
        safe_print("\n🔒 Shutting down event logging and Phoenix...")
        try:
            shutdown_event_logging()
            safe_print("✅ Shutdown completed successfully")
        except Exception as shutdown_error:
            safe_print(f"⚠️  Shutdown error: {shutdown_error}")

    safe_print("\n📊 Check Phoenix UI at http://localhost:6006/ for traces")
    safe_print("💡 If empty, check Docker: docker ps | grep phoenix")


if __name__ == "__main__":
    asyncio.run(test_phoenix_observability())

#!/usr/bin/env uv run python
"""
Debug script to check if workflow actually emits events to stream.
"""

import asyncio
import sys
from pathlib import Path

# Add main directory to Python path
sys.path.append(str(Path(__file__).parent / "main"))

from llama_index.core.workflow import StopEvent
from src.core.categorization_workflow import GAMPCategorizationWorkflow


async def test_workflow_streaming():
    """Test if workflow emits events to stream."""
    print("🔍 Testing Workflow Event Streaming")
    print("=" * 50)

    # Create workflow
    workflow = GAMPCategorizationWorkflow(
        timeout=60,
        verbose=False,
        enable_error_handling=True
    )

    # Simple test content
    test_content = "Test URS document for GAMP-5 categorization."

    # Run workflow
    print("\n🚀 Starting workflow...")
    handler = workflow.run(
        urs_content=test_content,
        document_name="test.md"
    )

    # Try to stream events
    print("\n📡 Attempting to stream events...")
    event_count = 0

    try:
        async for event in handler.stream_events():
            event_count += 1
            print(f"  ✓ Event {event_count}: {event.__class__.__name__}")

            # Show event details
            if hasattr(event, "__dict__"):
                for key, value in event.__dict__.items():
                    if not key.startswith("_"):
                        print(f"    - {key}: {str(value)[:50]}...")

            if isinstance(event, StopEvent):
                print(f"\n📊 Final result: {event.result}")
                break
    except Exception as e:
        print(f"\n❌ Error streaming events: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n📈 Total events streamed: {event_count}")

    # Also check if we can get the result directly
    try:
        result = await handler
        print(f"\n✅ Direct result obtained: {type(result)}")
    except Exception as e:
        print(f"\n❌ Error getting direct result: {e}")


if __name__ == "__main__":
    asyncio.run(test_workflow_streaming())

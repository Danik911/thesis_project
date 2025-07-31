#!/usr/bin/env python3
"""
Fixed test for the real GAMP-5 categorization workflow with Task 15 event logging integration.

This script properly integrates the event logging system by using LlamaIndex's
stream_events() pattern to capture real workflow events.
"""

import asyncio
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

# Add main to path and change working directory
main_path = Path(__file__).parent / "main"
sys.path.insert(0, str(main_path))

# Change to main directory for proper imports
original_cwd = os.getcwd()
os.chdir(str(main_path))

from llama_index.core.workflow import StopEvent
from src.core.categorization_workflow import GAMPCategorizationWorkflow
from src.shared.config import get_config
from src.shared.event_logging import EventStreamHandler, setup_event_logging


def load_environment():
    """Load environment variables from .env file."""
    from dotenv import load_dotenv

    # Load from parent directory since we change to main/
    env_path = Path("../.env")
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Environment loaded from {env_path}")

        # Verify OpenAI API key
        if os.getenv("OPENAI_API_KEY"):
            api_key = os.getenv("OPENAI_API_KEY")
            print(f"✅ OpenAI API key loaded: {api_key[:10]}...{api_key[-4:]}")
        else:
            print("⚠️ No OpenAI API key found")
    else:
        print(f"⚠️ No .env file found at {env_path}")


def setup_logging():
    """Setup controlled logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler()
        ]
    )

    # Control verbose output
    logging.getLogger("llama_index").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("src.shared.event_logging").setLevel(logging.INFO)


async def process_workflow_event(
    event_handler: EventStreamHandler,
    event: Any
) -> dict[str, Any] | None:
    """
    Process a real LlamaIndex workflow event through the event logging system.
    
    Args:
        event_handler: The event stream handler
        event: LlamaIndex workflow event
        
    Returns:
        Processed event data or None if filtered
    """
    # Convert LlamaIndex event to our event format
    event_data = {
        "event_type": event.__class__.__name__,
        "event_id": str(getattr(event, "event_id", "unknown")),
        "timestamp": str(getattr(event, "timestamp", "unknown")),
        "workflow_context": {
            "step": getattr(event, "step", "unknown"),
            "agent_id": getattr(event, "agent_id", "categorization_workflow"),
            "correlation_id": str(getattr(event, "correlation_id", "unknown"))
        },
        "payload": {}
    }

    # Extract event-specific data
    if hasattr(event, "__dict__"):
        for key, value in event.__dict__.items():
            if not key.startswith("_"):
                # Convert complex objects to strings
                if isinstance(value, (str, int, float, bool, dict, list)):
                    event_data["payload"][key] = value
                else:
                    event_data["payload"][key] = str(value)

    # Process through event handler
    return await event_handler._process_event(event_data)


async def test_real_workflow_integration():
    """Test the real workflow with proper event logging integration."""
    print("🔬 Testing Real GAMP-5 Workflow with Fixed Event Logging Integration")
    print("=" * 70)

    # Load environment
    load_environment()

    # Setup logging
    setup_logging()

    # Setup event logging system
    print("\n📊 Setting up event logging system...")
    config = get_config()
    config.logging.log_directory = "logs/workflow_test_fixed"
    config.gamp5_compliance.audit_log_directory = "logs/workflow_test_fixed/audit"

    event_handler = setup_event_logging(config)
    print("✅ Event logging system initialized")

    # Test with simple document
    test_document = Path("../simple_test_data.md")
    if not test_document.exists():
        print(f"❌ Test document not found: {test_document}")
        return False

    print(f"\n📄 Testing with document: {test_document}")

    try:
        # Create workflow WITHOUT EventLoggingMixin
        workflow = GAMPCategorizationWorkflow(
            timeout=120,
            verbose=False,
            enable_error_handling=True,
            confidence_threshold=0.60,
            enable_document_processing=False  # Keep simple for testing
        )

        print("✅ Workflow created")

        # Prepare document content
        document_content = test_document.read_text()
        print(f"📖 Document content: {len(document_content)} characters")

        # Run workflow with event streaming
        print("\n🚀 Running workflow with real event streaming...")
        start_time = time.time()

        # Start the workflow
        handler = workflow.run(
            urs_content=document_content,
            document_name=test_document.name
        )

        # Process events as they stream
        events_captured = []
        result = None

        print("\n📡 Streaming workflow events:")
        async for event in handler.stream_events():
            # Process event through our event handler
            processed_event = await process_workflow_event(event_handler, event)

            if processed_event:
                events_captured.append(processed_event)
                print(f"  ✓ Captured: {processed_event['event_type']} - {processed_event.get('payload', {}).get('message', 'No message')[:50]}...")

            # Check if this is the final result
            if isinstance(event, StopEvent):
                result = event.result

        end_time = time.time()
        execution_time = end_time - start_time

        print(f"\n⏱️ Workflow completed in {execution_time:.2f} seconds")
        print(f"📊 Total events captured: {len(events_captured)}")

        # Analyze results
        if result:
            print("\n📊 Workflow Results:")
            if isinstance(result, dict):
                summary = result.get("summary", {})
                print(f"  - Category: {summary.get('category', 'Unknown')}")
                print(f"  - Confidence: {summary.get('confidence', 0):.1%}")
                print(f"  - Review Required: {summary.get('review_required', False)}")
                print(f"  - Is Fallback: {summary.get('is_fallback', False)}")
                print(f"  - Duration: {summary.get('workflow_duration_seconds', 0):.2f}s")
            else:
                print(f"  - Result: {result}")

            # Get event handler statistics (now should show real events)
            stats = event_handler.get_statistics()
            print("\n📈 Event Processing Statistics:")
            print(f"  - Events Processed: {stats['events_processed']}")
            print(f"  - Events Filtered: {stats['events_filtered']}")
            print(f"  - Processing Rate: {stats['events_per_second']:.2f} events/sec")
            print(f"  - Runtime: {stats['runtime_seconds']:.2f}s")

            # Get compliance statistics
            compliance_stats = event_handler.compliance_logger.get_audit_statistics()
            print("\n🔒 GAMP-5 Compliance Statistics:")
            print(f"  - Audit Entries: {compliance_stats['total_audit_entries']}")
            print(f"  - Audit Files: {compliance_stats['audit_file_count']}")
            print(f"  - Storage Size: {compliance_stats['total_size_mb']:.2f} MB")
            print(f"  - Tamper Evident: {compliance_stats['tamper_evident']}")

            # Show captured event types
            print("\n📋 Captured Event Types:")
            event_types = {}
            for event in events_captured:
                event_type = event["event_type"]
                event_types[event_type] = event_types.get(event_type, 0) + 1

            for event_type, count in sorted(event_types.items()):
                print(f"  - {event_type}: {count}")

            return True
        print("❌ Workflow returned no result")
        return False

    except Exception as e:
        print(f"❌ Workflow execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def verify_log_files():
    """Verify that log files were actually created with real events."""
    print("\n📁 Verifying Log File Creation")
    print("-" * 50)

    log_directories = [
        "logs/workflow_test_fixed",
        "logs/workflow_test_fixed/audit"
    ]

    files_found = 0
    total_size = 0
    real_events_found = False

    for log_dir in log_directories:
        log_path = Path(log_dir)
        if log_path.exists():
            print(f"✅ Directory exists: {log_dir}")

            # Find log files
            log_files = list(log_path.glob("*.log")) + list(log_path.glob("*.jsonl"))
            if log_files:
                print(f"  📄 Found {len(log_files)} log files:")
                for log_file in log_files:
                    file_size = log_file.stat().st_size
                    files_found += 1
                    total_size += file_size
                    print(f"    - {log_file.name} ({file_size} bytes)")

                    # Check for real workflow events
                    if file_size > 0:
                        try:
                            with open(log_file) as f:
                                content = f.read()
                                # Look for real event types
                                if any(event_type in content for event_type in [
                                    "URSIngestionEvent",
                                    "GAMPCategorizationEvent",
                                    "WorkflowCompletionEvent",
                                    "ConsultationRequiredEvent"
                                ]):
                                    real_events_found = True
                                    print("      ✓ Contains real workflow events!")
                        except Exception:
                            pass
            else:
                print(f"  ⚠️ No log files found in {log_dir}")
        else:
            print(f"❌ Directory missing: {log_dir}")

    print("\n📊 Log File Summary:")
    print(f"  - Total Files: {files_found}")
    print(f"  - Total Size: {total_size} bytes ({total_size/1024:.2f} KB)")
    print(f"  - Real Events Found: {'✅ Yes' if real_events_found else '❌ No'}")

    return files_found > 0 and real_events_found


async def main():
    """Main test function."""
    try:
        print("🧪 REAL WORKFLOW + EVENT LOGGING INTEGRATION TEST (FIXED)")
        print("=" * 70)

        # Test workflow integration
        workflow_success = await test_real_workflow_integration()

        # Verify log files
        logs_success = await verify_log_files()

        # Final assessment
        print("\n" + "=" * 70)
        print("📋 INTEGRATION TEST SUMMARY")
        print("=" * 70)

        print(f"Real Workflow Execution    | {'✅ PASSED' if workflow_success else '❌ FAILED'}")
        print(f"Event Log File Generation  | {'✅ PASSED' if logs_success else '❌ FAILED'}")
        print("-" * 70)

        if workflow_success and logs_success:
            print("🎉 INTEGRATION TEST PASSED - Event logging captures REAL workflow events!")
            print("\n📊 Key Achievements:")
            print("  - ✅ Real LlamaIndex workflow events captured (not simulated)")
            print("  - ✅ Event statistics show actual processing counts")
            print("  - ✅ Audit trails contain real workflow event data")
            print("  - ✅ GAMP-5 compliance features work with production events")
            print("\n🔧 Fixed Issues:")
            print("  - Used handler.stream_events() to capture real events")
            print("  - Processed actual workflow events through EventStreamHandler")
            print("  - No more simulated event streams")
            return True
        print("⚠️ INTEGRATION TEST FAILED - Event logging still not capturing real events")
        return False

    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        return False
    except Exception as e:
        print(f"\n💥 Unexpected error during integration test: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Restore original working directory
        os.chdir(original_cwd)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

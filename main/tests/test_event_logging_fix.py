#!/usr/bin/env python3
"""
Test script to verify the event logging fix captures real workflow events.
"""

import asyncio
import sys
from pathlib import Path

# Add main directory to Python path
sys.path.append(str(Path(__file__).parent / "main"))

from src.core.categorization_workflow import GAMPCategorizationWorkflow
from src.shared import setup_event_logging, run_workflow_with_event_logging
from src.shared.config import get_config


async def test_event_logging_fix():
    """Test that event logging now captures real workflow events."""
    print("🧪 Testing Event Logging Fix")
    print("=" * 50)
    
    # Setup event logging
    config = get_config()
    config.logging.log_directory = "logs/fix_test"
    config.gamp5_compliance.audit_log_directory = "logs/fix_test/audit"
    
    event_handler = setup_event_logging(config)
    print("✅ Event logging system initialized")
    
    # Create workflow
    workflow = GAMPCategorizationWorkflow(
        timeout=60,
        verbose=False,
        enable_error_handling=True,
        confidence_threshold=0.60
    )
    print("✅ Workflow created")
    
    # Test document
    test_content = """
    # Test URS Document
    
    This is a test document for verifying event logging.
    
    ## System Requirements
    - The system should categorize pharmaceutical software
    - It should follow GAMP-5 guidelines
    - Events should be logged for compliance
    """
    
    try:
        # Run workflow with event logging
        print("\n🚀 Running workflow with event logging...")
        result, events = await run_workflow_with_event_logging(
            workflow,
            event_handler,
            urs_content=test_content,
            document_name="test_urs.md"
        )
        
        print(f"\n✅ Workflow completed successfully!")
        print(f"📊 Events captured: {len(events)}")
        
        # Show event types
        print("\n📋 Captured Event Types:")
        event_types = {}
        for event in events:
            event_type = event['event_type']
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        for event_type, count in sorted(event_types.items()):
            print(f"  - {event_type}: {count}")
        
        # Check if we captured real events
        real_event_types = {"URSIngestionEvent", "GAMPCategorizationEvent", "WorkflowCompletionEvent"}
        captured_types = set(event_types.keys())
        
        if captured_types & real_event_types:
            print("\n✅ SUCCESS: Real workflow events were captured!")
            print(f"   Found: {captured_types & real_event_types}")
            
            # Show event handler statistics
            stats = event_handler.get_statistics()
            print(f"\n📈 Event Processing Statistics:")
            print(f"  - Events Processed: {stats['events_processed']}")
            print(f"  - Processing Rate: {stats['events_per_second']:.2f} events/sec")
            
            return True
        else:
            print("\n❌ FAILURE: No real workflow events captured")
            print(f"   Expected: {real_event_types}")
            print(f"   Got: {captured_types}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    success = await test_event_logging_fix()
    
    if success:
        print("\n🎉 Event logging fix verified - real events are now captured!")
    else:
        print("\n⚠️ Event logging still not capturing real events")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
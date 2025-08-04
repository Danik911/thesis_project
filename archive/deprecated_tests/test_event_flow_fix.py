#!/usr/bin/env python3
"""
Test the event flow fixes to see if they work
"""

import sys
from pathlib import Path

# Add the main directory to path
sys.path.insert(0, str(Path(__file__).parent / "main"))

try:
    from src.core.unified_workflow import UnifiedTestGenerationWorkflow

    print("🔧 Testing Event Flow Architecture Fixes")
    print("=" * 60)

    print("Creating workflow instance...")
    workflow = UnifiedTestGenerationWorkflow(verbose=False)

    print("Running workflow validation...")
    try:
        workflow._validate()
        print("✅ SUCCESS: Workflow validation passed - no orphaned events detected!")
        print("🎉 Event flow architecture has been fixed!")

        # Now test the individual validation tests
        print("\n" + "=" * 60)
        print("Running full test suite...")

        # Import and run the original test
        from test_event_flow_validation import main
        result = main()

        if result == 0:
            print("\n🎉 ALL TESTS PASSED! Event flow architecture is now working correctly!")
        else:
            print(f"\n❌ Some tests still failing. Exit code: {result}")

    except Exception as e:
        print(f"❌ Workflow validation failed: {e}")

        # Parse the error message to extract specific event issues
        error_msg = str(e)

        if "produced but never consumed" in error_msg:
            print("\n🔍 REMAINING ORPHANED EVENT ISSUES:")
            start = error_msg.find("produced but never consumed: ") + len("produced but never consumed: ")
            orphaned_events = error_msg[start:].strip()
            print(f"   Orphaned Events: {orphaned_events}")

        if "consumed but never produced" in error_msg:
            print("\n🔍 REMAINING MISSING PRODUCER ISSUES:")
            start = error_msg.find("consumed but never produced: ") + len("consumed but never produced: ")
            missing_producers = error_msg[start:].strip()
            print(f"   Missing Producers: {missing_producers}")

        import traceback
        traceback.print_exc()

except Exception as e:
    print(f"❌ Failed to create workflow: {e}")
    import traceback
    traceback.print_exc()

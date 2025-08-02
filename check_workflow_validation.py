#!/usr/bin/env python3
"""
Simple workflow validation checker to identify event flow issues
"""

import sys
from pathlib import Path

# Add the main directory to path
sys.path.insert(0, str(Path(__file__).parent / "main"))

try:
    from src.core.unified_workflow import UnifiedTestGenerationWorkflow
    
    print("Creating workflow instance...")
    workflow = UnifiedTestGenerationWorkflow(verbose=False)
    
    print("Running workflow validation...")
    try:
        workflow._validate()
        print("✅ Workflow validation passed - no orphaned events detected")
    except Exception as e:
        print(f"❌ Workflow validation failed: {e}")
        
        # Parse the error message to extract specific event issues
        error_msg = str(e)
        
        if "produced but never consumed" in error_msg:
            print("\n🔍 ORPHANED EVENT ANALYSIS:")
            start = error_msg.find("produced but never consumed: ") + len("produced but never consumed: ")
            orphaned_events = error_msg[start:].strip()
            print(f"   Orphaned Events: {orphaned_events}")
            
        if "consumed but never produced" in error_msg:
            print("\n🔍 MISSING PRODUCER ANALYSIS:")
            start = error_msg.find("consumed but never produced: ") + len("consumed but never produced: ")
            missing_producers = error_msg[start:].strip()
            print(f"   Missing Producers: {missing_producers}")
            
        # Check for multiple consumers
        if "GAMPCategorizationEvent" in error_msg:
            print("\n🔍 MULTIPLE CONSUMER ANALYSIS:")
            print("   GAMPCategorizationEvent is being consumed by multiple steps:")
            print("   - check_consultation_required (line 647)")
            print("   - run_planning_workflow (line 277)")
            print("   This violates the 'one consumer per event' principle")
            
except Exception as e:
    print(f"❌ Failed to create workflow: {e}")
    import traceback
    traceback.print_exc()
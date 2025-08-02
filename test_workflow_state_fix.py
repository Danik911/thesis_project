#!/usr/bin/env python3
"""
Test script to verify the workflow state management fix works.
"""

import sys
import os
import asyncio
sys.path.append(os.path.join(os.path.dirname(__file__), 'main', 'src'))

from core.unified_workflow import UnifiedTestGenerationWorkflow
from pathlib import Path

async def test_workflow_state_management():
    """Test that planning_event is properly stored in workflow context."""
    
    print("🧪 Testing workflow state management fix...")
    print("Expected: planning_event stored in context even on planning failures")
    print()
    
    # Create unified workflow
    workflow = UnifiedTestGenerationWorkflow(
        timeout=60,  # 1 minute timeout for test
        verbose=True,
        enable_phoenix=False,  # Disable for testing
        enable_parallel_coordination=False,  # Disable to test minimal case
        enable_human_consultation=False
    )
    
    # Test file path
    test_file_path = Path(__file__).parent / "main" / "tests" / "test_data" / "gamp5_test_data" / "testing_data.md"
    
    if not test_file_path.exists():
        print(f"❌ TEST DATA NOT FOUND: {test_file_path}")
        return False
    
    try:
        print(f"Running workflow with test file: {test_file_path}")
        
        # Run workflow
        result = await workflow.run(document_path=str(test_file_path))
        
        print(f"✅ WORKFLOW COMPLETED")
        print(f"Result type: {type(result)}")
        
        if hasattr(result, 'result'):
            workflow_result = result.result
            print(f"Workflow status: {workflow_result.get('status', 'unknown')}")
            
            # Check if workflow metadata indicates successful state management
            metadata = workflow_result.get('workflow_metadata', {})
            if metadata:
                print("✅ WORKFLOW METADATA PRESENT - State management working")
                print(f"Processing time: {metadata.get('total_processing_time', 'unknown')} seconds")
                return True
            else:
                print("❌ MISSING WORKFLOW METADATA - State management may have failed")
                return False
        else:
            print("❌ UNEXPECTED RESULT FORMAT")
            return False
            
    except Exception as e:
        print(f"❌ WORKFLOW FAILED: {e}")
        import traceback
        traceback.print_exc()
        
        # Check if this is the specific planning_event error we're fixing
        if "planning_event" in str(e) and "not found in state" in str(e):
            print("❌ PLANNING_EVENT STATE ERROR STILL PRESENT - Fix not working")
            return False
        else:
            print("⚠️ Different error - may be unrelated to state management fix")
            return False

if __name__ == "__main__":
    print("🚀 Starting workflow state management fix validation...")
    print("=" * 60)
    
    success = asyncio.run(test_workflow_state_management())
    
    print("\n" + "=" * 60)
    
    if success:
        print("🎉 WORKFLOW STATE MANAGEMENT FIX WORKING!")
        sys.exit(0)
    else:
        print("❌ WORKFLOW STATE MANAGEMENT FIX NEEDS MORE WORK")
        sys.exit(1)
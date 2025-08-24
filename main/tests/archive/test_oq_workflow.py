#!/usr/bin/env python3
"""
Isolated test for OQ generation workflow to identify the exact issue.
"""

import asyncio
import sys
import traceback
from pathlib import Path

# Add main to path
sys.path.insert(0, str(Path(__file__).parent / "main"))

async def test_oq_workflow_instantiation():
    """Test OQ workflow instantiation to find the exact error."""
    
    try:
        print("=== Testing OQ Workflow Instantiation ===")
        
        # Test 1: Direct import and instantiation
        print("\n1. Testing direct import...")
        from main.src.agents.oq_generator.workflow import OQGenerationWorkflow
        print("   ✅ Import successful")
        
        print("\n2. Testing instantiation with timeout only...")
        workflow = OQGenerationWorkflow(timeout=1500)
        print("   ✅ Instantiation successful")
        
        # Test 2: Test StartEvent creation
        print("\n3. Testing StartEvent creation...")
        from llama_index.core.workflow import StartEvent
        
        test_data = {
            "gamp_category": 3,
            "urs_content": "Test content",
            "document_metadata": {"name": "test"},
            "required_test_count": 5,
            "agent_results": {},
            "correlation_id": "test-123"
        }
        
        start_event = StartEvent(data=test_data)
        print(f"   ✅ StartEvent created with data: {list(test_data.keys())}")
        
        # Test 3: Check if StartEvent has _cancel_flag attribute
        print("\n4. Testing StartEvent attributes...")
        print(f"   StartEvent attributes: {dir(start_event)}")
        
        if hasattr(start_event, '_cancel_flag'):
            print("   ✅ StartEvent has _cancel_flag")
        else:
            print("   ❌ StartEvent missing _cancel_flag attribute")
        
        # Test 4: Test workflow.run() call
        print("\n5. Testing workflow.run() call...")
        result = await asyncio.wait_for(workflow.run(start_event), timeout=30)
        print(f"   ✅ Workflow executed, result type: {type(result)}")
        print(f"   Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print(f"Error type: {type(e).__name__}")
        print(f"Full traceback:")
        print(traceback.format_exc())
        return False

async def test_unified_workflow_integration():
    """Test the unified workflow integration that's actually failing."""
    
    try:
        print("\n=== Testing Unified Workflow Integration ===")
        
        # Import what the unified workflow uses
        from main.src.agents.oq_generator.workflow import OQGenerationWorkflow
        from llama_index.core.workflow import StartEvent
        
        print("\n1. Creating workflow like unified_workflow.py does...")
        oq_workflow = OQGenerationWorkflow(timeout=1500)
        print("   ✅ Workflow created")
        
        # Create StartEvent like unified_workflow.py does
        print("\n2. Creating StartEvent like unified_workflow.py does...")
        start_event = StartEvent(data={
            "gamp_category": 3,
            "urs_content": "Test URS content",
            "document_metadata": {"name": "test_doc"},
            "required_test_count": 5,
            "test_strategy": {},
            "agent_results": {},
            "categorization_confidence": 0.8,
            "correlation_id": "test-correlation-123"
        })
        print("   ✅ StartEvent created")
        
        print("\n3. Testing workflow.run() call...")
        # This is the exact call from unified_workflow.py line 1424
        result = await asyncio.wait_for(oq_workflow.run(start_event), timeout=60)
        print(f"   ✅ Workflow completed, result type: {type(result)}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ UNIFIED WORKFLOW TEST ERROR: {e}")
        print(f"Error type: {type(e).__name__}")
        print(f"Full traceback:")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("🧪 OQ Generation Workflow Isolated Testing")
    print("=" * 60)
    
    # Run tests
    success1 = asyncio.run(test_oq_workflow_instantiation())
    success2 = asyncio.run(test_unified_workflow_integration())
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print(f"Basic Instantiation: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"Unified Integration: {'✅ PASS' if success2 else '❌ FAIL'}")
    
    overall = success1 and success2
    print(f"\nOverall Status: {'✅ ALL TESTS PASSED' if overall else '❌ SOME TESTS FAILED'}")
    
    sys.exit(0 if overall else 1)
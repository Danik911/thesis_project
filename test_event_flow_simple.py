#!/usr/bin/env python3
"""
Simple test for event flow architecture fixes.
"""

import asyncio
import tempfile
from pathlib import Path

async def test_imports():
    """Test that imports work and no syntax errors."""
    print("Testing imports...")
    
    try:
        import sys
        sys.path.append("main")
        
        from src.core.unified_workflow import UnifiedTestGenerationWorkflow, safe_context_get, safe_context_set
        from src.core.events import GAMPCategorizationEvent, PlanningEvent, AgentResultsEvent
        
        print("SUCCESS: All imports working")
        return True
        
    except Exception as e:
        print(f"FAILED: Import error - {e}")
        return False

async def test_workflow_creation():
    """Test that workflow can be created without errors."""
    print("Testing workflow creation...")
    
    try:
        import sys
        sys.path.append("main")
        
        from src.core.unified_workflow import UnifiedTestGenerationWorkflow
        
        # Create workflow with basic config
        workflow = UnifiedTestGenerationWorkflow(
            timeout=30,
            verbose=False,
            enable_phoenix=False,
            enable_parallel_coordination=False,
            enable_human_consultation=False
        )
        
        print("SUCCESS: Workflow created without errors")
        return True
        
    except Exception as e:
        print(f"FAILED: Workflow creation error - {e}")
        return False

async def test_event_types():
    """Test that event types have correct signatures."""
    print("Testing event type signatures...")
    
    try:
        import sys
        sys.path.append("main")
        
        from src.core.unified_workflow import UnifiedTestGenerationWorkflow
        
        # Check that methods have correct return type annotations
        workflow = UnifiedTestGenerationWorkflow(
            timeout=30,
            verbose=False,
            enable_phoenix=False,
            enable_parallel_coordination=False,
            enable_human_consultation=False
        )
        
        # Verify method signatures - should not have WorkflowCompletionEvent in intermediate steps
        import inspect
        
        # Check coordinate_parallel_agents return type
        coord_method = getattr(workflow, 'coordinate_parallel_agents')
        sig = inspect.signature(coord_method)
        return_annotation = sig.return_annotation
        
        # The return type should be AgentRequestEvent | AgentResultsEvent (not WorkflowCompletionEvent)
        if 'WorkflowCompletionEvent' in str(return_annotation):
            print("FAILED: coordinate_parallel_agents still returns WorkflowCompletionEvent")
            return False
        
        print("SUCCESS: Event type signatures look correct")
        return True
        
    except Exception as e:
        print(f"FAILED: Event type test error - {e}")
        return False

async def main():
    """Run simple tests."""
    print("Event Flow Architecture Fix Testing")
    print("=" * 40)
    
    tests = [
        ("Imports", test_imports),
        ("Workflow Creation", test_workflow_creation), 
        ("Event Types", test_event_types)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n[{test_name}]")
        result = await test_func()
        results.append((test_name, result))
    
    print("\nTest Summary:")
    all_passed = True
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"  {test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\nAll basic tests passed! Event flow fixes look good.")
    else:
        print("\nSome tests failed - check the fixes.")
    
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
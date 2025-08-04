#!/usr/bin/env python3
"""
Quick test to verify the tracer fix works in UnifiedTestGenerationWorkflow
"""

import sys
from pathlib import Path

# Add main directory to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_tracer_fix():
    """Test that UnifiedTestGenerationWorkflow can access tracer without error."""
    try:
        from src.core.unified_workflow import UnifiedTestGenerationWorkflow
        
        # Initialize workflow
        workflow = UnifiedTestGenerationWorkflow(
            timeout=300,  # Short timeout for test
            verbose=True
        )
        
        # Test that tracer is accessible
        print(f"✅ Workflow initialized successfully")
        print(f"✅ Tracer available: {workflow.tracer is not None}")
        print(f"✅ Tracer type: {type(workflow.tracer)}")
        
        # Test tracer log_error method (the one causing AttributeError)
        try:
            workflow.tracer.log_error("test_component", Exception("Test error for verification"))
            print(f"✅ Tracer.log_error() works without AttributeError")
        except AttributeError as e:
            print(f"❌ Tracer.log_error() still fails: {e}")
            return False
        except Exception as e:
            print(f"ℹ️  Tracer.log_error() accessible but failed with: {e}")
            # This is expected - the error itself doesn't matter, just that we can call the method
        
        print("✅ Tracer fix verification successful!")
        return True
        
    except Exception as e:
        print(f"❌ Tracer fix verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import asyncio
    result = asyncio.run(test_tracer_fix())
    sys.exit(0 if result else 1)
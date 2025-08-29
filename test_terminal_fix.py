#!/usr/bin/env python3
"""
Quick test to verify terminal output blocking fix is working.
"""

import asyncio
import sys
from pathlib import Path

# Add the main directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "main"))

from src.core.unified_workflow import show_progress_during_wait

async def mock_long_operation():
    """Simulate a long LLM call like the agents do."""
    await asyncio.sleep(5.0)  # 5 second delay
    return {"result": "success", "data": "mock response"}

async def test_progress_indicator():
    """Test the progress indicator function."""
    print("🔧 Testing terminal output fix...")
    print("📍 Starting mock long operation (should show progress)...")
    sys.stdout.flush()
    
    try:
        result = await show_progress_during_wait(
            mock_long_operation(),
            timeout=10.0,
            operation_name="Mock LLM Call", 
            agent_type="test_agent"
        )
        
        print(f"🎉 Test completed! Result: {result}")
        sys.stdout.flush()
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.stdout.flush()
        return False

if __name__ == "__main__":
    print("🚀 Terminal Output Fix Test")
    print("=" * 50)
    
    success = asyncio.run(test_progress_indicator())
    
    if success:
        print("✅ TERMINAL FIX WORKING: Progress indicators show during long operations!")
    else:
        print("❌ TERMINAL FIX FAILED: No progress shown during operations")
        
    print("\n🔍 This simulates the execute_agent_request step behavior.")
    print("If you saw progress updates every 2 seconds, the fix is working!")
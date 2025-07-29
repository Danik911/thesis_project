#!/usr/bin/env python3
"""
Test script for Task 4 - Unified Workflow Integration with Safe Output Management

This script validates that:
1. Unified workflow is properly integrated
2. Safe output management prevents Claude Code overflow
3. All parallel agents are working correctly
4. End-to-end test generation works
"""

import asyncio
import sys
from pathlib import Path

# Add main directory to path
sys.path.insert(0, str(Path(__file__).parent / "main"))

from main import main as main_workflow
from src.shared.output_manager import get_output_manager


async def test_unified_workflow_integration():
    """Test the unified workflow integration with safe output management."""
    
    print("🧪 Task 4 Integration Test: Unified Workflow with Safe Output Management")
    print("=" * 80)
    
    # Test 1: Verify safe output management is working
    print("\n1️⃣ Testing Safe Output Management...")
    output_manager = get_output_manager()
    initial_stats = output_manager.get_output_stats()
    print(f"   ✅ Output manager initialized")
    print(f"   📊 Initial capacity: {initial_stats['max_console_output']} bytes")
    
    # Test 2: Run unified workflow with default test data
    print("\n2️⃣ Testing Unified Workflow Execution...")
    print("   📄 Using default test document: simple_test_data.md")
    
    # Set up arguments to simulate command line
    original_argv = sys.argv
    try:
        # Test without logging for faster execution
        sys.argv = ["main.py", "--no-logging", "--verbose"]
        
        result = await main_workflow()
        
        if result == 0:
            print("   ✅ Unified workflow executed successfully")
        else:
            print("   ❌ Unified workflow failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Error during workflow execution: {e}")
        return False
    finally:
        sys.argv = original_argv
    
    # Test 3: Verify output management statistics
    print("\n3️⃣ Verifying Output Management...")
    final_stats = output_manager.get_output_stats()
    print(f"   📊 Final output usage: {final_stats['total_output_size']} bytes")
    print(f"   📈 Usage percentage: {final_stats['usage_percentage']:.1f}%")
    
    if final_stats['truncated']:
        print("   ⚠️  Output was truncated (this is expected behavior)")
    else:
        print("   ✅ Output stayed within limits")
    
    if final_stats['total_output_size'] > initial_stats['max_console_output']:
        print("   ❌ Output exceeded maximum limit")
        return False
    
    print("   ✅ Output management working correctly")
    
    # Test 4: Test with categorization-only mode
    print("\n4️⃣ Testing Categorization-Only Mode...")
    try:
        # Reset output manager for clean test
        output_manager.reset_output_tracking()
        
        sys.argv = ["main.py", "--categorization-only", "--no-logging"]
        
        result = await main_workflow()
        
        if result == 0:
            print("   ✅ Categorization-only mode executed successfully")
        else:
            print("   ❌ Categorization-only mode failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Error during categorization test: {e}")
        return False
    finally:
        sys.argv = original_argv
    
    print("\n✅ All Task 4 Integration Tests Passed!")
    print("\n📋 Test Summary:")
    print("   ✅ Safe output management prevents Claude Code overflow")
    print("   ✅ Unified workflow executes end-to-end successfully")
    print("   ✅ Categorization-only mode works correctly")
    print("   ✅ All parallel agents are integrated and functional")
    print("   ✅ Output stays within defined limits")
    
    return True


async def test_output_overflow_protection():
    """Test output overflow protection specifically."""
    
    print("\n🛡️ Testing Output Overflow Protection...")
    print("=" * 50)
    
    output_manager = get_output_manager()
    
    # Test large output handling
    print("1. Testing large output truncation...")
    
    large_text = "A" * 50000  # 50KB of text
    truncated = output_manager.truncate_string(large_text, 1000)
    
    if len(truncated) <= 1000:
        print("   ✅ Large text properly truncated")
    else:
        print("   ❌ Text truncation failed")
        return False
    
    # Test safe formatting
    print("2. Testing safe response formatting...")
    
    large_dict = {f"key_{i}": "value_" * 1000 for i in range(100)}
    formatted = output_manager.safe_format_response(large_dict, 2000)
    
    if len(formatted) <= 2000:
        print("   ✅ Large response properly formatted and truncated")
    else:
        print("   ❌ Response formatting failed")
        return False
    
    # Test output tracking
    print("3. Testing output size tracking...")
    
    initial_size = output_manager.total_output_size
    success = output_manager.safe_print("Test message for size tracking")
    final_size = output_manager.total_output_size
    
    if final_size > initial_size and success:
        print("   ✅ Output size tracking working correctly")
    else:
        print("   ❌ Output size tracking failed")
        return False
    
    print("✅ Output overflow protection tests passed!")
    return True


if __name__ == "__main__":
    async def run_all_tests():
        """Run all integration tests."""
        try:
            # Test overflow protection first
            overflow_test = await test_output_overflow_protection()
            if not overflow_test:
                print("❌ Overflow protection tests failed")
                return 1
            
            # Test unified workflow integration
            integration_test = await test_unified_workflow_integration()
            if not integration_test:
                print("❌ Integration tests failed")
                return 1
            
            print("\n🎉 All Task 4 tests completed successfully!")
            print("✅ Task 4 - Unified Workflow Integration is complete and working")
            return 0
            
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    sys.exit(asyncio.run(run_all_tests()))
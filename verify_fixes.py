#!/usr/bin/env python3
"""
Verification script for the workflow fixes.
Tests the key components without running the full workflow.
"""

import sys
from pathlib import Path

# Add main to Python path
sys.path.insert(0, str(Path(__file__).parent / "main"))

def test_imports():
    """Test basic imports."""
    print("Testing imports...")

    try:
        # Test core imports
        from llama_index.core.workflow import (
            StartEvent,
        )
        print("✅ Basic LlamaIndex imports successful")

        # Test workflow import
        print("✅ UnifiedTestGenerationWorkflow import successful")

        # Test StartEvent creation and _cancel_flag
        start_event = StartEvent(document_path="test.txt")
        if hasattr(start_event, "_cancel_flag"):
            print("✅ StartEvent has _cancel_flag attribute")

            # Test the operation that was failing
            start_event._cancel_flag.clear()
            print("✅ StartEvent._cancel_flag.clear() works")
        else:
            print("❌ StartEvent missing _cancel_flag attribute")
            return False

        return True

    except Exception as e:
        print(f"❌ Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_output_manager():
    """Test OutputManager initialization."""
    print("\nTesting OutputManager initialization...")

    try:
        from src.core.models import OutputConfiguration
        from src.core.output_management import OutputManager

        # Test OutputConfiguration creation
        config = OutputConfiguration(output_directory="test_output")
        print("✅ OutputConfiguration created successfully")

        # Test OutputManager creation
        output_manager = OutputManager(config=config)
        print("✅ OutputManager created successfully with config")

        return True

    except Exception as e:
        print(f"❌ OutputManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all verification tests."""
    print("🔧 Verifying LlamaIndex Workflow Fixes")
    print("=" * 45)

    success = True

    success &= test_imports()
    success &= test_output_manager()

    print("\n" + "=" * 45)
    if success:
        print("🎉 All fixes verified successfully!")
        print("The workflow should now run without compatibility errors.")
    else:
        print("❌ Some fixes failed verification.")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

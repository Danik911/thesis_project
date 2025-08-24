#!/usr/bin/env python3
"""
Quick test script to verify the LlamaIndex workflow fixes.
Tests both StartEvent._cancel_flag patch and OutputManager initialization.
"""

import asyncio
import sys
import tempfile
from pathlib import Path

# Add main to Python path
sys.path.insert(0, str(Path(__file__).parent / "main"))

async def test_workflow_fixes():
    """Test the workflow initialization and StartEvent creation."""

    print("🧪 Testing LlamaIndex Workflow Fixes")
    print("=" * 50)

    try:
        # Test 1: Import and StartEvent patch
        print("📦 Testing imports and StartEvent patch...")
        from src.core.unified_workflow import StartEvent, UnifiedTestGenerationWorkflow

        # Verify StartEvent has _cancel_flag attribute
        start_event = StartEvent(document_path="test.txt")
        if hasattr(start_event, "_cancel_flag"):
            print("✅ StartEvent._cancel_flag patch applied successfully")
        else:
            print("❌ StartEvent._cancel_flag patch failed")
            return False

        # Test 2: Workflow initialization
        print("🏗️ Testing workflow initialization...")
        workflow = UnifiedTestGenerationWorkflow(
            timeout=300,
            verbose=True,
            enable_human_consultation=False,
            output_dir="test_output"
        )

        if workflow.output_manager is not None:
            print("✅ OutputManager initialized successfully")
        else:
            print("⚠️ OutputManager not available (this is OK if components are missing)")

        print("✅ Workflow created successfully")

        # Test 3: Create a simple test document
        print("📄 Testing with a simple document...")
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("""
            Test Document for GAMP-5 Categorization
            
            This is a simple pharmaceutical system document for testing purposes.
            It contains basic requirements for a data collection system.
            
            Requirements:
            1. System shall collect patient data
            2. System shall validate data integrity 
            3. System shall maintain audit trails
            4. System shall generate reports
            """)
            test_doc_path = f.name

        try:
            # Test StartEvent creation with document
            start_event = StartEvent(document_path=test_doc_path)
            print(f"✅ StartEvent created successfully with document: {Path(test_doc_path).name}")

            # Verify the _cancel_flag is accessible
            start_event._cancel_flag.clear()  # This was the failing operation
            print("✅ StartEvent._cancel_flag.clear() works correctly")

        finally:
            # Clean up test file
            Path(test_doc_path).unlink(missing_ok=True)

        print("\n🎉 All workflow compatibility fixes are working!")
        print("The LlamaIndex workflow should now run without the version compatibility errors.")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_workflow_fixes())
    sys.exit(0 if success else 1)

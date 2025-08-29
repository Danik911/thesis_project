#!/usr/bin/env python3
"""
Minimal test to validate the infinite loop fix works.
"""

import sys
import asyncio
from pathlib import Path

# Add project paths
sys.path.insert(0, str(Path(__file__).parent / "main"))

# Test the fixed workflow
async def main():
    print("Testing infinite loop fix...")
    
    try:
        from src.core.categorization_workflow import GAMPCategorizationWorkflow
        
        # Create workflow with document processing disabled
        workflow = GAMPCategorizationWorkflow(
            enable_document_processing=False,
            timeout=5  # Short timeout
        )
        
        # Test content
        result = await workflow.run(
            urs_content="Simple test LIMS system for pharmaceutical compliance.",
            document_name="test.md"
        )
        
        print(f"✅ SUCCESS: Workflow completed!")
        print(f"   Result: {result}")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    print(f"\n{'✅ PASS' if success else '❌ FAIL'}: Infinite loop fix validation")
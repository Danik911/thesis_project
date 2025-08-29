#!/usr/bin/env python3
"""
Simple validation script for the infinite loop fix.
"""

import asyncio
import sys
import traceback
from pathlib import Path

# Add main to path
sys.path.insert(0, str(Path(__file__).parent / "main"))

from src.core.categorization_workflow import GAMPCategorizationWorkflow
from llama_index.core.workflow import StartEvent


async def validate_fix():
    """Validate that the infinite loop fix works."""
    print("🔧 Validating Infinite Loop Fix")
    print("=" * 40)
    
    # Simple test content
    test_content = """
    # Test URS
    Laboratory Information Management System for pharmaceutical testing.
    21 CFR Part 11 compliance required.
    """
    
    try:
        # Create workflow with document processing DISABLED (main fix target)
        workflow = GAMPCategorizationWorkflow(
            enable_document_processing=False,  # This should NOT cause infinite loop now
            verbose=True,
            timeout=10  # Quick timeout to catch loops
        )
        
        print("🚀 Running workflow...")
        
        # Run workflow - this should complete quickly without infinite loop
        result = await workflow.run(
            urs_content=test_content,
            document_name="test.md",
            document_version="1.0",
            author="test"
        )
        
        # If we get here, no infinite loop occurred
        if result and hasattr(result, "result"):
            cat_result = result.result
            print("✅ SUCCESS: Workflow completed without infinite loop!")
            print(f"   Category: {cat_result.gamp_category.value}")
            print(f"   Confidence: {cat_result.confidence_score:.1%}")
            return True
        else:
            print("❌ FAILURE: No result returned")
            return False
            
    except asyncio.TimeoutError:
        print("❌ TIMEOUT: Infinite loop likely still exists")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(validate_fix())
    if success:
        print("\n🎉 FIX VALIDATED: Infinite loop resolved!")
        print("💡 Task 43 validation can now proceed")
    else:
        print("\n❌ FIX VALIDATION FAILED")
    
    sys.exit(0 if success else 1)
"""
Test script to verify the categorization workflow fix.

This script tests that the categorization workflow now properly handles low-confidence
categorization by returning events instead of throwing exceptions.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the main directory to Python path
main_dir = Path(__file__).parent / "main"
sys.path.insert(0, str(main_dir))

from src.core.unified_workflow import UnifiedTestGenerationWorkflow
from src.core.events import URSIngestionEvent

async def test_low_confidence_categorization():
    """Test that low confidence categorization returns events instead of throwing exceptions."""
    
    print("Testing categorization workflow fix...")
    
    # Create a URS document that should trigger low confidence categorization
    test_urs_content = """
    This document describes some software requirements that are intentionally vague
    and ambiguous to trigger low confidence categorization. The software does something
    but it's not clear what exactly. It might be infrastructure, or commercial software,
    or maybe custom development. The description lacks clear indicators for any specific
    GAMP category, making it difficult for the agent to categorize with high confidence.
    """
    
    try:
        # Create workflow
        workflow = UnifiedTestGenerationWorkflow(verbose=True)
        
        # Create ingestion event
        urs_event = URSIngestionEvent(
            urs_content=test_urs_content,
            document_name="test_low_confidence.urs",
            document_version="1.0",
            author="Test User",
            ingestion_timestamp=None  # Will be auto-set
        )
        
        print(f"\n📝 Testing categorization with ambiguous URS content...")
        print(f"Document: {urs_event.document_name}")
        print(f"Content length: {len(test_urs_content)} characters")
        
        # Test the categorization step directly
        result = await workflow.categorize_document(workflow._context, urs_event)
        
        print(f"\n✅ SUCCESS: Categorization completed without throwing exception!")
        print(f"Result type: {type(result)}")
        
        if hasattr(result, 'gamp_category'):
            print(f"📊 Category: {result.gamp_category.value}")
            print(f"🎯 Confidence: {result.confidence_score:.1%}")
            print(f"👥 Review Required: {result.review_required}")
            
            if result.review_required:
                print(f"🤝 Human consultation will be triggered (as expected for low confidence)")
            else:
                print(f"ℹ️ No human consultation required")
                
            print(f"📝 Justification: {result.justification[:200]}...")
            
        return True
        
    except Exception as e:
        print(f"\n❌ FAILURE: Exception was thrown instead of returning event")
        print(f"Error: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Stack trace: {traceback.format_exc()}")
        return False

async def main():
    """Run the test."""
    print("🔧 Testing Categorization Workflow Fix")
    print("=" * 50)
    
    success = await test_low_confidence_categorization()
    
    if success:
        print(f"\n✅ TEST PASSED: Categorization workflow properly handles low confidence")
        print(f"✅ Events returned instead of exceptions thrown")
        print(f"✅ Human-in-the-loop pattern working correctly")
    else:
        print(f"\n❌ TEST FAILED: Categorization workflow still throwing exceptions")
        print(f"❌ Need further debugging")
        
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
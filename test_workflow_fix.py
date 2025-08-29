#!/usr/bin/env python3
"""
Test the workflow fix for the process_document issue.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "main"))

async def test_workflow_fix():
    """Test if the workflow fix resolves the issue."""
    print("=== TESTING WORKFLOW FIX ===")
    
    try:
        from src.core.unified_workflow import UnifiedTestGenerationWorkflow
        
        # Use the same document that was failing
        test_document = project_root / "datasets" / "corpus_3" / "special_cases" / "URS-030.md"
        
        if not test_document.exists():
            print(f"❌ Test document not found: {test_document}")
            return
        
        print(f"📁 Testing with document: {test_document}")
        print(f"📄 Document exists: {test_document.exists()}")
        
        # Create workflow with validation mode enabled to bypass consultation
        workflow = UnifiedTestGenerationWorkflow(
            timeout=300,  # 5 minutes
            verbose=True,
            enable_parallel_coordination=False,  # Simplify test
            enable_phoenix=False,  # Disable for test
            enable_human_consultation=False  # Disable for test
        )
        
        print("🚀 Starting workflow...")
        
        # Run the workflow
        result = await workflow.run(document_path=str(test_document))
        
        print("✅ WORKFLOW COMPLETED!")
        print(f"Result type: {type(result)}")
        
        if hasattr(result, 'result'):
            actual_result = result.result
        else:
            actual_result = result
        
        print(f"Actual result type: {type(actual_result)}")
        
        if isinstance(actual_result, dict):
            print("📊 Result summary:")
            print(f"  Status: {actual_result.get('status', 'Unknown')}")
            if 'categorization' in actual_result:
                cat = actual_result['categorization']
                print(f"  Category: {cat.get('category', 'Unknown')}")
                print(f"  Confidence: {cat.get('confidence', 0):.2%}")
        
        print("🎉 TEST SUCCESSFUL - Workflow completed without terminating early!")
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_workflow_fix())
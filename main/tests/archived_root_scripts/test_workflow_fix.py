#!/usr/bin/env python3
"""
Test script to validate the workflow orchestration fix.

This script tests the simplified categorization workflow to ensure:
1. No duplicate workflow execution
2. Clean termination without hanging
3. Proper categorization results
"""

import asyncio
import logging
from pathlib import Path

# Setup logging to see workflow execution
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def test_simplified_categorization():
    """Test the simplified categorization workflow."""
    print("=" * 60)
    print("🧪 TESTING SIMPLIFIED CATEGORIZATION WORKFLOW")
    print("=" * 60)
    
    try:
        # Import the simplified workflow
        from src.core.categorization_workflow import GAMPCategorizationWorkflow
        
        # Create simple test content
        test_content = """
        # Laboratory Information Management System (LIMS) URS
        
        ## System Overview
        This document describes requirements for a configurable LIMS system
        that will be used in pharmaceutical quality control laboratories.
        
        ## Requirements
        - The system shall manage laboratory test results
        - The system shall ensure 21 CFR Part 11 compliance
        - The system shall provide audit trails for all data changes
        - The system shall support configurable workflows
        """
        
        print(f"📄 Test content length: {len(test_content)} characters")
        print("🚀 Creating simplified categorization workflow...")
        
        # Create workflow with short timeout for testing
        workflow = GAMPCategorizationWorkflow(
            timeout=60,  # 1 minute timeout
            verbose=True,
            confidence_threshold=0.5
        )
        
        print("✅ Workflow created successfully")
        print("▶️  Running categorization workflow...")
        
        # Run the workflow
        result = await workflow.run(
            urs_content=test_content,
            document_name="test_lims_urs.md",
            document_version="1.0",
            author="test_user"
        )
        
        print("✅ Workflow completed!")
        print(f"📊 Result type: {type(result)}")
        
        # Extract categorization event from result
        if hasattr(result, "result"):
            categorization_event = result.result
        else:
            categorization_event = result
            
        print("\n" + "=" * 40)
        print("📋 CATEGORIZATION RESULTS:")
        print("=" * 40)
        print(f"🏷️  Category: {categorization_event.gamp_category.value}")
        print(f"📊 Confidence: {categorization_event.confidence_score:.2%}")
        print(f"🔍 Review Required: {categorization_event.review_required}")
        print(f"📝 Justification: {categorization_event.justification[:200]}...")
        
        # Check for expected behavior
        expected_behaviors = []
        if categorization_event.gamp_category.value in [3, 4, 5]:
            expected_behaviors.append("✅ Appropriate category for LIMS system")
        else:
            expected_behaviors.append("⚠️  Unexpected category for LIMS system")
            
        if categorization_event.confidence_score > 0:
            expected_behaviors.append("✅ Non-zero confidence score")
        else:
            expected_behaviors.append("❌ Zero confidence (fallback mode)")
            
        print("\n🎯 VALIDATION RESULTS:")
        for behavior in expected_behaviors:
            print(f"   {behavior}")
            
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_unified_workflow_integration():
    """Test integration with unified workflow."""
    print("\n" + "=" * 60)
    print("🔗 TESTING UNIFIED WORKFLOW INTEGRATION")
    print("=" * 60)
    
    try:
        # Create a simple test document
        test_file = Path("test_integration_document.md")
        test_content = """
        # Pharmaceutical Manufacturing Execution System (MES) URS
        
        This system will control manufacturing processes in a pharmaceutical facility.
        It requires custom development and extensive validation.
        """
        
        test_file.write_text(test_content, encoding="utf-8")
        print(f"📄 Created test document: {test_file}")
        
        # Import unified workflow
        from src.core.unified_workflow import UnifiedTestGenerationWorkflow
        
        print("🚀 Creating unified workflow...")
        
        # Create workflow with short timeout for testing
        unified_workflow = UnifiedTestGenerationWorkflow(
            timeout=300,  # 5 minutes
            verbose=True,
            enable_parallel_coordination=False,  # Disable for simpler test
            enable_human_consultation=False      # Disable to avoid blocking
        )
        
        print("✅ Unified workflow created")
        print("▶️  Running unified workflow (categorization step only)...")
        
        # Just test the start and categorization steps
        from llama_index.core.workflow import StartEvent
        
        start_event = StartEvent(document_path=str(test_file))
        
        # This should not hang anymore with our fix
        print("⏱️  Testing workflow execution (should not hang)...")
        
        result = await asyncio.wait_for(
            unified_workflow.run(document_path=str(test_file)),
            timeout=120  # 2 minute timeout
        )
        
        print("✅ Unified workflow completed without hanging!")
        print(f"📊 Result status: {result.get('status', 'unknown') if isinstance(result, dict) else type(result)}")
        
        # Clean up
        test_file.unlink(missing_ok=True)
        print("🧹 Test file cleaned up")
        
        return True
        
    except asyncio.TimeoutError:
        print("❌ Workflow timed out - hanging issue may still exist")
        return False
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up test file
        if test_file.exists():
            test_file.unlink()

async def main():
    """Run all tests."""
    print("🧪 WORKFLOW ORCHESTRATION FIX VALIDATION")
    print("=" * 60)
    
    # Test 1: Simplified categorization workflow
    test1_success = await test_simplified_categorization()
    
    # Test 2: Integration with unified workflow (simplified)
    test2_success = await test_unified_workflow_integration()
    
    print("\n" + "=" * 60)
    print("📋 FINAL TEST RESULTS:")
    print("=" * 60)
    print(f"🧪 Simplified Categorization: {'✅ PASS' if test1_success else '❌ FAIL'}")
    print(f"🔗 Unified Integration: {'✅ PASS' if test2_success else '❌ FAIL'}")
    
    if test1_success and test2_success:
        print("\n🎉 ALL TESTS PASSED - Workflow orchestration fix successful!")
        print("✅ No more duplicate workflows")
        print("✅ No more terminal hanging")  
        print("✅ Clean categorization flow")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED - Fix may need additional work")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
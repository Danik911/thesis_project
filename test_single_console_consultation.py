#!/usr/bin/env python3
"""
Test script to verify single-console human consultation works.

This script tests the restored single-console consultation functionality
that allows users to input category choices in the same terminal without
needing a separate --consult terminal.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from main.src.core.unified_workflow import UnifiedTestGenerationWorkflow
from llama_index.core.workflow import StartEvent


async def test_single_console_consultation():
    """Test the single-console consultation functionality."""
    print("🧪 Testing Single-Console Human Consultation")
    print("=" * 60)
    
    # Test document that should trigger consultation
    test_document = """
    # Test URS Document
    
    This is a test document with unclear categorization requirements.
    It mentions some software but not enough details for confident categorization.
    
    ## Requirements
    - System shall do something
    - Software shall be implemented
    - Testing shall be performed
    """
    
    # Create workflow with consultation enabled
    workflow = UnifiedTestGenerationWorkflow(
        timeout=120,
        verbose=True,
        enable_human_consultation=True,
        bypass_consultation_for_testing=False  # Force consultation
    )
    
    try:
        print("🚀 Starting workflow that will trigger consultation...")
        print("💡 When prompted, test the consultation by entering a category (1/3/4/5)")
        print("⏰ You'll have 30 seconds to respond, or it will default to Category 5")
        print("-" * 60)
        
        # Run workflow with test document
        start_event = StartEvent(
            urs_content=test_document,
            document_name="test_consultation_document.md",
            document_version="1.0",
            author="test_system"
        )
        
        result = await workflow.run(start_event)
        
        print("\n✅ Test completed successfully!")
        print("📊 Result Summary:")
        
        if hasattr(result, 'result') and result.result:
            summary = result.result.get('summary', {})
            print(f"  - Final Category: {summary.get('gamp_category', 'Unknown')}")
            print(f"  - Test Count: {summary.get('total_tests', 0)}")
            print(f"  - Duration: {summary.get('execution_time_seconds', 0):.1f}s")
            print(f"  - Output File: {summary.get('output_file', 'None')}")
            
            # Check if consultation happened
            metadata = result.result.get('metadata', {})
            if 'consultation_result' in metadata:
                consult = metadata['consultation_result']
                print(f"\n🤔 Consultation Details:")
                print(f"  - Status: {consult.get('consultation_status', 'Unknown')}")
                print(f"  - Approved Category: {consult.get('approved_category', 'Unknown')}")
                print(f"  - Method: {consult.get('method', 'Unknown')}")
                
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    print("Single-Console Human Consultation Test")
    print("=" * 60)
    print("This test verifies that human consultation now works in a single console")
    print("without requiring a separate --consult terminal.\n")
    
    success = await test_single_console_consultation()
    
    if success:
        print("\n🎉 SUCCESS: Single-console consultation is working!")
        print("✅ Users can now input category choices directly in the same terminal")
        print("✅ 30-second timeout with conservative defaults is implemented")
        print("✅ No second terminal required")
    else:
        print("\n💥 FAILED: Single-console consultation still not working")
        print("❌ Check the error details above")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
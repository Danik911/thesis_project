#!/usr/bin/env python3
"""
Test script to verify the human consultation Category 4 override fix (Windows compatible).

This script tests that when a human selects Category 4 during consultation,
both the OQ generation and final output display Category 4 correctly.
"""

import asyncio
import sys
from pathlib import Path

# Add main to path
sys.path.insert(0, str(Path(__file__).parent / "main"))

from src.core.unified_workflow import UnifiedTestGenerationWorkflow
from src.shared.config import get_config

async def test_human_consultation_fix():
    """Test that human consultation Category 4 selection is properly applied."""
    
    print("Testing Human Consultation Category 4 Override Fix")
    print("=" * 60)
    
    # Use test document that normally gets Category 1
    test_document_path = "main/tests/test_data/gamp5_test_data/testing_data.md"
    
    if not Path(test_document_path).exists():
        print(f"ERROR: Test document not found: {test_document_path}")
        return False
    
    print(f"Testing with document: {test_document_path}")
    
    # Create workflow with human consultation enabled
    workflow = UnifiedTestGenerationWorkflow(
        timeout=1800,
        verbose=True,
        enable_human_consultation=True,
        enable_parallel_coordination=True
    )
    
    print("Starting workflow...")
    print("IMPORTANT: When prompted, select Category 4 to test the fix")
    print("   The AI will likely suggest Category 1, but you should override to Category 4")
    print()
    
    try:
        # Run workflow
        result = await workflow.run(document_path=test_document_path)
        
        # Extract results
        if hasattr(result, "result"):
            final_result = result.result
        else:
            final_result = result
            
        # Check the key indicators
        print("\nVERIFICATION RESULTS:")
        print("=" * 40)
        
        # Check 1: Final categorization display
        categorization = final_result.get("categorization", {})
        displayed_category = categorization.get("gamp_category")
        
        print(f"Final Categorization Display: Category {displayed_category}")
        
        # Check 2: OQ generation results
        oq_results = final_result.get("oq_generation", {})
        test_count = oq_results.get("total_tests", 0)
        suite_id = oq_results.get("test_suite_id", "N/A")
        
        print(f"OQ Tests Generated: {test_count} tests")
        print(f"Test Suite ID: {suite_id}")
        
        # Check 3: Test suite file content (if available)
        output_file = oq_results.get("output_file")
        if output_file and Path(output_file).exists():
            print(f"Test suite saved to: {output_file}")
            
            import json
            try:
                with open(output_file, 'r') as f:
                    test_suite_data = json.load(f)
                    
                file_category = test_suite_data.get("gamp_category")
                print(f"Category in saved file: Category {file_category}")
                
                # VERIFICATION: Check if human override was applied
                if displayed_category == 4 and file_category == 4:
                    print("\nSUCCESS: Human consultation Category 4 override is working correctly!")
                    print("   - Final display shows Category 4")
                    print("   - OQ tests were generated for Category 4")  
                    print("   - Saved test suite contains Category 4")
                    return True
                elif displayed_category == 1 or file_category == 1:
                    print("\nFAILURE: Human consultation override was ignored!")
                    print("   - Despite selecting Category 4, the system still shows Category 1")
                    print("   - This confirms the bug still exists")
                    return False
                else:
                    print(f"\nUNCLEAR: Unexpected category values:")
                    print(f"   - Display category: {displayed_category}")
                    print(f"   - File category: {file_category}")
                    return False
                    
            except Exception as e:
                print(f"Could not verify test suite file: {e}")
        else:
            print("Test suite file not available for verification")
            
        # Basic verification based on displayed category
        if displayed_category == 4:
            print("\nLIKELY SUCCESS: Final display shows Category 4")
            return True
        elif displayed_category == 1:
            print("\nLIKELY FAILURE: Final display still shows Category 1 despite human override")
            return False
        else:
            print(f"\nUNCLEAR: Unexpected category {displayed_category}")
            return False
            
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        workflow.close()

if __name__ == "__main__":
    print("Human Consultation Category 4 Override Fix Test")
    print("=" * 50)
    
    # Enable validation mode to bypass some checks during testing
    config = get_config()
    original_mode = config.validation_mode.validation_mode
    
    try:
        # Run the test
        success = asyncio.run(test_human_consultation_fix())
        
        print("\n" + "=" * 50)
        if success:
            print("TEST PASSED: Human consultation override fix is working!")
        else:
            print("TEST FAILED: Human consultation override fix needs more work")
            
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest setup failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Restore original validation mode
        config.validation_mode.validation_mode = original_mode
"""
Test script to verify the asyncio.run() fix in OQ generator V2.

This script tests that the o1 model generation works correctly within
an async context without the nested event loop error.
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add main directory to path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from src.agents.oq_generator.generator_v2 import create_oq_test_generator_v2
from src.core.events import GAMPCategory

async def test_o1_generation_fix():
    """Test that o1 model generation works without asyncio.run() errors."""
    print("Testing asyncio.run() fix for o1 model generation...")
    
    # Create V2 generator with o1 model support
    generator = create_oq_test_generator_v2(
        verbose=True,
        generation_timeout=300  # 5 minutes for testing
    )
    
    # Test content for Category 5 (uses o1-2025-04-16)
    urs_content = """
    # Advanced Pharmaceutical System - Category 5
    
    ## Purpose
    This is a Category 5 system requiring complex validation with o1 model generation.
    
    ## Requirements
    1. The system shall implement advanced data integrity controls
    2. The system shall provide comprehensive audit trails
    3. The system shall support complex business logic validation
    4. The system shall integrate with regulatory reporting systems
    5. The system shall maintain ALCOA+ compliance
    """
    
    try:
        print("Testing async o1 model generation (Category 5)...")
        
        # This call should now work without asyncio.run() errors
        test_suite = await generator.generate_oq_test_suite(
            gamp_category=GAMPCategory.CATEGORY_5,
            urs_content=urs_content,
            document_name="test_category5_system.md",
            context_data=None  # No context for this test
        )
        
        print(f"SUCCESS! Generated test suite: {test_suite.test_suite_id}")
        print(f"Total tests: {len(test_suite.tests)}")
        print(f"Model used: {test_suite.generation_metadata.get('model_used', 'unknown')}")
        
        # Verify it's using o1 model
        expected_model = "o3-2025-04-16"
        actual_model = test_suite.generation_metadata.get("llm_model", "")
        if expected_model in actual_model:
            print(f"[OK] Correctly used o3 model: {actual_model}")
        else:
            print(f"[WARNING] Unexpected model used: {actual_model}")
        
        # Show first test as verification
        if test_suite.tests:
            first_test = test_suite.tests[0]
            print(f"\nFirst test generated:")
            print(f"ID: {first_test.test_id}")
            print(f"Title: {first_test.test_title}")
            print(f"Risk Level: {first_test.risk_level}")
            print(f"Steps: {len(first_test.test_steps)}")
        
        return True
        
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_standard_model_generation():
    """Test that standard model generation still works."""
    print("\nTesting standard model generation (Category 3)...")
    
    generator = create_oq_test_generator_v2(verbose=True)
    
    urs_content = """
    # Standard System - Category 3
    
    ## Purpose
    Simple Category 3 system for testing standard model generation.
    
    ## Requirements
    1. System shall display data correctly
    2. System shall validate user inputs
    3. System shall generate reports
    """
    
    try:
        test_suite = await generator.generate_oq_test_suite(
            gamp_category=GAMPCategory.CATEGORY_3,
            urs_content=urs_content,
            document_name="test_category3_system.md"
        )
        
        print(f"SUCCESS! Standard model test suite: {test_suite.test_suite_id}")
        print(f"Total tests: {len(test_suite.tests)}")
        return True
        
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")
        return False

async def main():
    """Run all tests to verify the asyncio fix."""
    print("[TEST] Testing asyncio.run() fix for OQ Generator V2\n")
    
    # Test 1: o1 model generation (the main fix)
    o1_success = await test_o1_generation_fix()
    
    # Test 2: Standard model generation (regression test)
    standard_success = await test_standard_model_generation()
    
    # Summary
    print("\n" + "="*50)
    print("TEST RESULTS:")
    print(f"o3 Model Generation:      {'PASS' if o1_success else 'FAIL'}")
    print(f"Standard Model Generation: {'PASS' if standard_success else 'FAIL'}")
    
    if o1_success and standard_success:
        print("\n[SUCCESS] All tests passed! asyncio.run() fix is working correctly.")
        return True
    else:
        print("\n[ERROR] Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
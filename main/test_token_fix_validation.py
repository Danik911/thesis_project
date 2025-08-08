#!/usr/bin/env python3
"""
Test to validate the token limit fix for OSS model JSON generation.
This test specifically checks if increasing max_tokens from 4000 to 8000 resolves the truncation issue.
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv('../.env')

# Set OSS model configuration
os.environ["LLM_PROVIDER"] = "openrouter"  
os.environ["LLM_MODEL"] = "openai/gpt-oss-120b"
os.environ["OPENROUTER_API_TIMEOUT"] = "300"

from src.config.llm_config import LLMConfig
from src.agents.oq_generator.generator import OQTestGenerator
from src.core.events import GAMPCategory

async def test_token_limit_fix():
    """Test if the increased token limit (8000) fixes the JSON generation truncation."""
    print("=" * 60)
    print("TOKEN LIMIT FIX VALIDATION TEST")
    print("=" * 60)
    
    try:
        # Get LLM configuration
        llm = LLMConfig.get_llm()
        print(f"LLM Model: {llm.model}")
        print(f"Max Tokens: {llm.max_tokens}")
        print(f"Temperature: {llm.temperature}")
        
        # Verify we have the increased token limit
        if hasattr(llm, 'max_tokens') and llm.max_tokens >= 8000:
            print("✅ Token limit increased to 8000+ as expected")
        else:
            print("❌ Token limit not increased - still at default")
            return False
            
        # Initialize generator
        generator = OQTestGenerator(llm=llm, verbose=True, generation_timeout=60)
        
        # Test parameters - Category 5 requires 25 tests (high token usage)
        urs_content = """
# Environmental Monitoring System (EMS) Requirements

## Functional Requirements
- URS-EMS-001: The system shall continuously monitor temperature in all GMP storage areas.
- URS-EMS-002: Temperature readings shall be recorded at intervals not exceeding 5 minutes.
- URS-EMS-003: The system shall use vendor-supplied software without modification.
- URS-EMS-004: System shall generate real-time alerts for temperature excursions.
- URS-EMS-005: The system shall maintain calibration records for all sensors.

## Regulatory Requirements  
- URS-EMS-008: System shall maintain an audit trail per 21 CFR Part 11.
- URS-EMS-009: Electronic signatures shall use vendor's built-in functionality.
- URS-EMS-010: System shall support user access controls and role-based permissions.
- URS-EMS-011: All data must be backed up according to GMP requirements.
- URS-EMS-012: System must be validated according to GAMP-5 Category 5 requirements.
"""
        
        context_data = {
            "document": "Environmental Monitoring System for pharmaceutical storage",
            "category": GAMPCategory.CATEGORY_5,
            "requirements": ["Monitor temperature", "Generate alerts", "Maintain audit trail", "Support electronic signatures"]
        }
        
        print("\nGenerating OQ test suite for Category 5 (25 tests expected)...")
        print("This will test if increased token limit prevents JSON truncation...")
        
        result = generator.generate_oq_test_suite(
            gamp_category=GAMPCategory.CATEGORY_5,
            urs_content=urs_content,
            document_name="EMS_Testing_Data.md",
            context_data=context_data
        )
        
        # Validate results
        actual_tests = len(result.test_cases)
        expected_tests = 25  # Category 5 should generate 25 tests
        
        print(f"\n📊 RESULTS:")
        print(f"Expected tests for Category 5: {expected_tests}")
        print(f"Actual tests generated: {actual_tests}")
        print(f"Test suite ID: {result.suite_id}")
        print(f"Category: {result.category}")
        
        if actual_tests >= expected_tests:
            print("✅ SUCCESS: Generated expected number of tests!")
            print("✅ Token limit fix appears to be working")
            
            # Show a few sample tests
            print(f"\n📝 Sample Tests (first 3 of {actual_tests}):")
            for i, test in enumerate(result.test_cases[:3], 1):
                print(f"  Test {i}: {test.test_description[:80]}...")
                
            return True
        else:
            print(f"❌ PARTIAL SUCCESS: Generated {actual_tests}/{expected_tests} tests")
            print("❌ Token limit may still be insufficient or other issues exist")
            return False
        
    except Exception as e:
        print(f"❌ FAILED: Token limit fix validation error: {str(e)}")
        import traceback
        print("Full error:")
        print(traceback.format_exc())
        return False

async def main():
    """Main test function."""
    print("Testing OSS model JSON generation with increased token limit...")
    
    # Check environment setup
    provider = os.getenv("LLM_PROVIDER")
    model = os.getenv("LLM_MODEL")  
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
    
    print(f"Provider: {provider}")
    print(f"Model: {model}")
    print(f"OpenRouter key: {'Present' if openrouter_key else 'Missing'}")
    
    if not openrouter_key:
        print("❌ ERROR: OPENROUTER_API_KEY not found in environment")
        return False
        
    # Run the token limit validation test
    success = await test_token_limit_fix()
    
    print("-" * 60)
    if success:
        print("🎉 VALIDATION RESULT: Token limit fix SUCCESSFUL")
        print("✅ OSS model can now generate complete 25-test suites")
        print("✅ JSON truncation issue resolved")
    else:
        print("💥 VALIDATION RESULT: Token limit fix FAILED or INCOMPLETE")
        print("❌ Further investigation needed")
    print("=" * 60)
    
    return success

if __name__ == "__main__":
    asyncio.run(main())
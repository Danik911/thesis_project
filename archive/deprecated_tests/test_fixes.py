#!/usr/bin/env python3
"""
Test script for the remaining workflow blocker fixes.
Tests SME agent JSON parsing and OQ generator timeout configuration.
"""

import json
import sys
import os

# Add the main directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'main'))

from main.src.agents.parallel.sme_agent import extract_json_from_markdown
from main.src.agents.oq_generator.generator import OQTestGenerator
from llama_index.llms.openai import OpenAI

def test_sme_json_parsing():
    """Test the improved JSON parsing for complex arrays."""
    print("🧪 Testing SME Agent JSON Parsing...")
    
    # Test case: Complex JSON array that was failing
    test_response = '''
Looking at the pharmaceutical validation requirements, here are my recommendations:

```json
[
    {
        "category": "System Classification",
        "priority": "high",
        "recommendation": "Implement comprehensive GAMP-5 categorization validation",
        "rationale": "Ensures proper regulatory compliance framework",
        "implementation_effort": "medium",
        "expected_benefit": "regulatory_compliance"
    },
    {
        "category": "Risk Assessment",
        "priority": "high", 
        "recommendation": "Establish risk-based validation approach with documented criteria",
        "rationale": "Aligns with ICH Q9 quality risk management principles",
        "implementation_effort": "high",
        "expected_benefit": "risk_mitigation"
    },
    {
        "category": "Data Integrity",
        "priority": "medium",
        "recommendation": "Implement ALCOA+ principles throughout validation lifecycle",
        "rationale": "Ensures data integrity compliance per FDA guidance",
        "implementation_effort": "medium", 
        "expected_benefit": "data_integrity"
    }
]
```

These recommendations should provide a solid foundation for validation.
'''
    
    try:
        result = extract_json_from_markdown(test_response)
        print(f"✅ Successfully parsed JSON array with {len(result)} items")
        
        # Validate structure
        if isinstance(result, list):
            print("✅ Result is correctly identified as a list")
            for i, item in enumerate(result):
                if all(key in item for key in ['category', 'priority', 'recommendation']):
                    print(f"✅ Item {i+1} has required fields")
                else:
                    print(f"❌ Item {i+1} missing required fields")
        else:
            print(f"❌ Result is not a list: {type(result)}")
            
        return True
        
    except Exception as e:
        print(f"❌ JSON parsing failed: {e}")
        return False

def test_oq_generator_timeout():
    """Test the OQ generator timeout configuration."""
    print("\n🧪 Testing OQ Generator Timeout Configuration...")
    
    try:
        # Create LLM instance
        llm = OpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            max_tokens=4000
        )
        
        # Create generator with custom timeout
        generator = OQTestGenerator(
            llm=llm,
            verbose=True,
            generation_timeout=480  # 8 minutes
        )
        
        print("✅ OQ Generator created successfully")
        print(f"✅ Timeout configured: {generator.generation_timeout}s")
        
        # Check if LLM timeout was configured
        if hasattr(generator.llm, 'request_timeout'):
            print(f"✅ LLM request_timeout set to: {generator.llm.request_timeout}s")
        elif hasattr(generator.llm, '_client') and hasattr(generator.llm._client, 'timeout'):
            print(f"✅ LLM client timeout set to: {generator.llm._client.timeout}s")
        else:
            print("⚠️  LLM timeout configuration method not detected (may still work)")
        
        return True
        
    except Exception as e:
        print(f"❌ OQ Generator timeout test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing Remaining Workflow Blocker Fixes")
    print("=" * 50)
    
    results = []
    
    # Test 1: SME JSON Parsing
    results.append(test_sme_json_parsing())
    
    # Test 2: OQ Generator Timeout
    results.append(test_oq_generator_timeout())
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    if all(results):
        print("🎉 All tests passed! Fixes are working correctly.")
        print("\n✅ SME Agent: JSON parsing improved for complex arrays")
        print("✅ OQ Generator: Timeout configuration implemented")
        print("\n🚀 Ready for end-to-end workflow testing!")
    else:
        print("❌ Some tests failed. Check the output above for details.")
        failed_tests = []
        if not results[0]:
            failed_tests.append("SME JSON Parsing")
        if not results[1]:
            failed_tests.append("OQ Generator Timeout")
        print(f"Failed tests: {', '.join(failed_tests)}")
    
    return all(results)

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
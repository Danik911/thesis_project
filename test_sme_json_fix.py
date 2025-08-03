#!/usr/bin/env python3
"""
Test script for SME Agent JSON parsing fix.

This script tests the new balanced bracket parsing implementation
to ensure it handles the problematic cases identified in the research.
"""

import sys
import json
import logging
from pathlib import Path

# Add main source to path
main_path = Path(__file__).parent / "main" / "src"
sys.path.insert(0, str(main_path))

from agents.parallel.sme_agent import extract_json_from_markdown, clean_unicode_characters, find_balanced_json_array

# Set up basic logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_nested_array_parsing():
    """Test parsing of JSON array with nested objects containing arrays."""
    print("\n=== Testing Nested Array Parsing ===")
    
    # This is the type of response that was failing with non-greedy regex
    response_text = '''
    ```json
    [
        {
            "category": "System Categorization",
            "priority": "high",
            "recommendation": "Implement comprehensive test strategy",
            "rationale": "Based on GAMP-5 requirements for Category 4 systems",
            "implementation_effort": "medium", 
            "expected_benefit": "Regulatory compliance",
            "nested_array": ["item1", "item2"],
            "complex_object": {
                "sub_array": [1, 2, 3],
                "nested_data": {"key": "value"}
            }
        },
        {
            "category": "Validation Testing",
            "priority": "medium",
            "recommendation": "Establish test data management",
            "rationale": "Ensure data integrity throughout validation lifecycle",
            "implementation_effort": "low",
            "expected_benefit": "Data quality assurance"
        }
    ]
    ```
    '''
    
    try:
        result = extract_json_from_markdown(response_text)
        print(f"✅ SUCCESS: Parsed {type(result).__name__} with {len(result)} items")
        
        # Validate structure
        assert isinstance(result, list), f"Expected list, got {type(result)}"
        assert len(result) == 2, f"Expected 2 items, got {len(result)}"
        
        # Validate first item structure
        first_item = result[0]
        required_fields = ["category", "priority", "recommendation", "rationale", "implementation_effort", "expected_benefit"]
        for field in required_fields:
            assert field in first_item, f"Missing required field: {field}"
        
        # Validate nested structures
        assert "nested_array" in first_item, "Missing nested_array"
        assert isinstance(first_item["nested_array"], list), "nested_array should be a list"
        assert first_item["nested_array"] == ["item1", "item2"], "nested_array content mismatch"
        
        assert "complex_object" in first_item, "Missing complex_object"
        assert isinstance(first_item["complex_object"], dict), "complex_object should be a dict"
        assert "sub_array" in first_item["complex_object"], "Missing sub_array in complex_object"
        
        print("✅ All structure validations passed")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def test_unicode_character_handling():
    """Test handling of invisible Unicode characters."""
    print("\n=== Testing Unicode Character Handling ===")
    
    # JSON with various invisible characters
    contaminated_json = '\ufeff[\u200b{"category": "Test"}\u200b]\u200c'
    
    try:
        # Test cleaning function
        cleaned = clean_unicode_characters(contaminated_json)
        print(f"Original length: {len(contaminated_json)}, Cleaned length: {len(cleaned)}")
        
        # Test parsing
        result = extract_json_from_markdown(contaminated_json)
        print(f"✅ SUCCESS: Parsed contaminated JSON: {result}")
        
        assert isinstance(result, list), f"Expected list, got {type(result)}"
        assert len(result) == 1, f"Expected 1 item, got {len(result)}"
        assert result[0]["category"] == "Test", "Content validation failed"
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def test_raw_json_parsing():
    """Test parsing of raw JSON without code blocks."""
    print("\n=== Testing Raw JSON Parsing ===")
    
    # Raw JSON array (no markdown code blocks)
    raw_json = '''
    Here is the analysis result:
    [
        {
            "category": "Quality Assurance",
            "priority": "high",
            "recommendation": "Implement automated testing",
            "rationale": "Reduce manual testing effort",
            "implementation_effort": "high",
            "expected_benefit": "Improved efficiency"
        }
    ]
    
    This concludes the analysis.
    '''
    
    try:
        result = extract_json_from_markdown(raw_json)
        print(f"✅ SUCCESS: Parsed raw JSON: {type(result).__name__} with {len(result)} items")
        
        assert isinstance(result, list), f"Expected list, got {type(result)}"
        assert len(result) == 1, f"Expected 1 item, got {len(result)}"
        assert result[0]["category"] == "Quality Assurance", "Content validation failed"
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def test_malformed_json_explicit_failure():
    """Test that malformed JSON fails explicitly (no fallbacks)."""
    print("\n=== Testing Explicit Failure for Malformed JSON ===")
    
    malformed_json = '''
    ```json
    [
        {
            category: "Missing quotes",
            "priority": "high",
        }
    ]
    ```
    '''
    
    try:
        result = extract_json_from_markdown(malformed_json)
        print(f"❌ UNEXPECTED SUCCESS: Should have failed but got: {result}")
        return False
        
    except ValueError as e:
        print(f"✅ SUCCESS: Correctly failed with explicit error: {e}")
        # Verify error message contains diagnostic information
        assert "diagnostic" in str(e).lower() or "json" in str(e).lower(), "Error should contain diagnostic info"
        return True
        
    except Exception as e:
        print(f"❌ FAILED: Unexpected error type: {type(e).__name__}: {e}")
        return False

def test_balanced_array_function():
    """Test the balanced array parsing function directly."""
    print("\n=== Testing Balanced Array Function ===")
    
    test_cases = [
        # Simple array
        ('["a", "b", "c"]', True),
        # Nested arrays
        ('[["a", "b"], ["c", "d"]]', True), 
        # Array with objects containing arrays
        ('[{"data": ["x", "y"]}, {"more": [1, 2]}]', True),
        # Incomplete array
        ('[{"incomplete": "json"', False),
        # No array
        ('{"not": "an array"}', False),
    ]
    
    success_count = 0
    for test_input, should_succeed in test_cases:
        try:
            result = find_balanced_json_array(test_input)
            if should_succeed:
                if result and json.loads(result):
                    print(f"✅ '{test_input[:20]}...' -> SUCCESS")
                    success_count += 1
                else:
                    print(f"❌ '{test_input[:20]}...' -> Expected success but got None")
            else:
                if result is None:
                    print(f"✅ '{test_input[:20]}...' -> Correctly failed")
                    success_count += 1
                else:
                    print(f"❌ '{test_input[:20]}...' -> Expected failure but got result")
        except Exception as e:
            if not should_succeed:
                print(f"✅ '{test_input[:20]}...' -> Correctly failed with exception")
                success_count += 1
            else:
                print(f"❌ '{test_input[:20]}...' -> Unexpected error: {e}")
    
    print(f"Balanced array function: {success_count}/{len(test_cases)} tests passed")
    return success_count == len(test_cases)

def main():
    """Run all tests."""
    print("Testing SME Agent JSON Parsing Fix")
    print("=" * 50)
    
    tests = [
        ("Nested Array Parsing", test_nested_array_parsing),
        ("Unicode Character Handling", test_unicode_character_handling),
        ("Raw JSON Parsing", test_raw_json_parsing),
        ("Explicit Failure for Malformed JSON", test_malformed_json_explicit_failure),
        ("Balanced Array Function", test_balanced_array_function),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} CRASHED: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\nOverall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! The JSON parsing fix is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please review the implementation.")
        return 1

if __name__ == "__main__":
    exit(main())
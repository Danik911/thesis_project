#!/usr/bin/env python3
import json
import re
from typing import Optional, Union, Dict, Any, List

def find_balanced_json_array(text: str) -> Optional[str]:
    """Find a balanced JSON array using bracket counting."""
    start = text.find('[')
    if start == -1:
        return None
    
    bracket_count = 0
    in_string = False
    escape_next = False
    
    for i in range(start, len(text)):
        char = text[i]
        
        if escape_next:
            escape_next = False
            continue
            
        if char == '\\':
            escape_next = True
            continue
            
        if char == '"' and not escape_next:
            in_string = not in_string
            continue
            
        if not in_string:
            if char == '[':
                bracket_count += 1
            elif char == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    return text[start:i+1]
    
    return None

def find_balanced_json_object(text: str) -> Optional[str]:
    """Find a balanced JSON object using brace counting."""
    start = text.find('{')
    if start == -1:
        return None
    
    brace_count = 0
    in_string = False
    escape_next = False
    
    for i in range(start, len(text)):
        char = text[i]
        
        if escape_next:
            escape_next = False
            continue
            
        if char == '\\':
            escape_next = True
            continue
            
        if char == '"' and not escape_next:
            in_string = not in_string
            continue
            
        if not in_string:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    return text[start:i+1]
    
    return None

def extract_json_from_markdown(response_text: str) -> Union[Dict[str, Any], List[Any]]:
    """Extract JSON from markdown code blocks or raw responses."""
    # First try to extract from markdown code blocks
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
    
    # Try to find balanced JSON object (check objects before arrays)
    json_object = find_balanced_json_object(response_text)
    if json_object:
        try:
            return json.loads(json_object)
        except json.JSONDecodeError:
            pass
    
    # Try to find balanced JSON array
    json_array = find_balanced_json_array(response_text)
    if json_array:
        try:
            return json.loads(json_array)
        except json.JSONDecodeError:
            pass
    
    # Last resort: try to parse the entire text
    try:
        return json.loads(response_text.strip())
    except json.JSONDecodeError:
        raise ValueError(f"Could not extract valid JSON from response: {response_text[:200]}...")

# Test with the exact response from the error
test_response = """[
    {
        "category": "System Categorization",
        "priority": "high",
        "recommendation": "Perform a formal and thorough system categorization exercise to confirm the system's GAMP category 5 applicability, involving cross-functional teams including IT, QA, and validation experts.",
        "rationale": "Accurate GAMP classification is critical to define the appropriate validation scope and controls, preventing inadequate validation and regulatory non-compliance.",
        "implementation_effort": "medium",
        "expected_benefit": "Regulatory Compliance"
    }
]"""

print("Testing extract_json_from_markdown with raw array...")
print("Input text starts with '[': ", test_response.strip().startswith('['))

# Debug: Check what each method finds
print("\n1. Checking markdown extraction:")
json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', test_response, re.DOTALL)
print(f"   Markdown match found: {json_match is not None}")

print("\n2. Checking object extraction:")
json_object = find_balanced_json_object(test_response)
print(f"   Object found: {json_object is not None}")
if json_object:
    print(f"   Object preview: {json_object[:50]}...")

print("\n3. Checking array extraction:")
json_array = find_balanced_json_array(test_response)
print(f"   Array found: {json_array is not None}")
if json_array:
    print(f"   Array preview: {json_array[:50]}...")

print("\n4. Running full extraction:")
try:
    result = extract_json_from_markdown(test_response)
    print(f"Result type: {type(result)}")
    print(f"Is list: {isinstance(result, list)}")
    print(f"Length: {len(result) if isinstance(result, list) else 'N/A'}")
    if isinstance(result, list) and len(result) > 0:
        print(f"First item keys: {list(result[0].keys())}")
    elif isinstance(result, dict):
        print(f"Dict keys: {list(result.keys())}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
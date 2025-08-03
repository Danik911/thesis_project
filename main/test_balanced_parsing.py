#!/usr/bin/env python3
import re

def find_balanced_json_array(text: str):
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

# Test with the actual response
test_json = """[
    {
        "category": "System Categorization",
        "priority": "high",
        "recommendation": "Perform a formal and thorough system categorization exercise to confirm the system's GAMP category 5 applicability, involving cross-functional teams including IT, QA, and validation experts.",
        "rationale": "Accurate GAMP classification is critical to define the appropriate validation scope and controls, preventing inadequate validation and regulatory non-compliance.",
        "implementation_effort": "medium",
        "expected_benefit": "Regulatory Compliance"
    }
]"""

result = find_balanced_json_array(test_json)
print(f"Found array: {result is not None}")
if result:
    print(f"Length: {len(result)}")
    print(f"First 100 chars: {result[:100]}")
    print(f"Last 50 chars: {result[-50:]}")
    
    import json
    try:
        parsed = json.loads(result)
        print(f"Parse successful: {type(parsed)}")
        print(f"Is list: {isinstance(parsed, list)}")
    except Exception as e:
        print(f"Parse failed: {e}")
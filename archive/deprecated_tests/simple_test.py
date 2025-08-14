#!/usr/bin/env python3
"""
Simple test for the core balanced JSON array parsing function.
"""

def find_balanced_json_array(text: str):
    """
    Find a balanced JSON array using bracket counting.
    """
    start = text.find("[")
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

        if char == "\\":
            escape_next = True
            continue

        if char == '"' and not escape_next:
            in_string = not in_string
            continue

        if not in_string:
            if char == "[":
                bracket_count += 1
            elif char == "]":
                bracket_count -= 1
                if bracket_count == 0:
                    return text[start:i+1]

    return None

# Test the problematic case from the research
test_input = """[
    {
        "category": "System Categorization",
        "priority": "high",
        "nested_array": ["item1", "item2"]
    }
]"""

print("Testing balanced array parsing...")
print(f"Input: {test_input}")

result = find_balanced_json_array(test_input)
print(f"Result: {result}")

if result:
    import json
    try:
        parsed = json.loads(result)
        print(f"✅ SUCCESS: Parsed {type(parsed).__name__} with {len(parsed)} items")
        print(f"First item category: {parsed[0]['category']}")
        print(f"Nested array: {parsed[0]['nested_array']}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing failed: {e}")
else:
    print("❌ No balanced array found")

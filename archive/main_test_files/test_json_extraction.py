#!/usr/bin/env python3
import sys
sys.path.append('.')

from src.agents.parallel.sme_agent import extract_json_from_markdown

# Test with the actual response format from the error
test_response = """[
    {
        "category": "System Categorization",
        "priority": "high",
        "recommendation": "Perform a formal and detailed system categorization exercise to confirm the GAMP category 5 classification and define the appropriate validation scope.",
        "rationale": "Unclear GAMP category classification poses a high risk of inappropriate validation scope and insufficient technical controls, impacting compliance and system integrity.",
        "implementation_effort": "medium",
        "expected_benefit": "Clear validation scope and appropriate technical controls"
    }
]"""

try:
    result = extract_json_from_markdown(test_response)
    print(f"✅ Successfully parsed: {type(result)} with {len(result)} items")
    print(f"First item: {result[0]['category']}")
except Exception as e:
    print(f"❌ Failed to parse: {e}")
    import traceback
    traceback.print_exc()
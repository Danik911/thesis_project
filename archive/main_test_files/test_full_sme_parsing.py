#!/usr/bin/env python3
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agents.parallel.sme_agent import extract_json_from_markdown

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
try:
    result = extract_json_from_markdown(test_response)
    print(f"Result type: {type(result)}")
    print(f"Is list: {isinstance(result, list)}")
    print(f"Length: {len(result) if isinstance(result, list) else 'N/A'}")
    if isinstance(result, list) and len(result) > 0:
        print(f"First item keys: {list(result[0].keys())}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

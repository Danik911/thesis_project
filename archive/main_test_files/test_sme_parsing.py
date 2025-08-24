#!/usr/bin/env python3
import json

# The actual response from the error message
test_response = """```json
{
    "level": "high",
    "applicable_standards": [
        "21 CFR Part 11",
        "EU Annex 11",
        "GAMP 5 Guide",
        "ICH Q7",
        "FDA Guidance for Industry: Computerized Systems Used in Clinical Investigations"
    ],
    "compliance_gaps": [
        {
            "gap": "Unclear GAMP category classification leading to inadequate risk-based validation approach",
            "impact": "high",
            "recommendation": "Perform a thorough system categorization to confirm GAMP Category 5 applicability and tailor validation accordingly"
        }
    ],
    "required_controls": [
        "Robust supplier assessment and management",
        "Comprehensive risk assessment and mitigation strategies"
    ],
    "certainty_score": 0.6
}
```"""

# Simple test to verify parsing
import re

# Extract JSON from markdown
json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", test_response, re.DOTALL)
if json_match:
    json_str = json_match.group(1)
    print(f"Extracted JSON string length: {len(json_str)}")

    try:
        parsed = json.loads(json_str)
        print("SUCCESS: Successfully parsed JSON")
        print(f"Keys found: {list(parsed.keys())}")
        print(f"'level' field present: {'level' in parsed}")
        print(f"'level' value: {parsed.get('level')}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error: {e}")
else:
    print("❌ No JSON found in markdown")

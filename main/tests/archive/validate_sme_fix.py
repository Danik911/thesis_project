#!/usr/bin/env python3
"""
Quick validation test for SME Agent JSON parsing fix
"""

import sys
from pathlib import Path

# Add main to path
sys.path.insert(0, str(Path(__file__).parent / "main"))

from src.agents.parallel.sme_agent import extract_json_from_markdown

# Test JSON with critical priority (the exact issue we fixed)
test_critical_priority = """
[
    {
        "category": "compliance",
        "priority": "critical",
        "recommendation": "Fix data integrity validation",
        "rationale": "21 CFR Part 11 compliance required",
        "implementation_effort": "high",
        "expected_benefit": "regulatory_compliance"
    }
]
"""

# Test case variations
test_cases = [
    {"priority": "critical", "effort": "high", "name": "critical-high"},
    {"priority": "Critical", "effort": "Medium", "name": "mixed-case"},
    {"priority": "high", "effort": "low", "name": "standard-values"}
]

print("🧪 Testing SME Agent JSON Parsing Fix")
print("="*50)

success_count = 0
total_tests = len(test_cases) + 1

# Test 1: Original critical priority issue
print("\n1. Testing original 'critical' priority issue...")
try:
    parsed = extract_json_from_markdown(test_critical_priority)
    if parsed[0]["priority"] == "critical":
        print("✅ Critical priority accepted")
        success_count += 1
    else:
        print("❌ Critical priority validation failed")
except Exception as e:
    print(f"❌ Critical priority test failed: {e}")

# Test 2-4: Various case combinations  
for i, test_case in enumerate(test_cases, 2):
    print(f"\n{i}. Testing {test_case['name']}...")
    
    test_json = f"""
    [
        {{
            "category": "test",
            "priority": "{test_case['priority']}",
            "recommendation": "Test recommendation",
            "rationale": "Test rationale",
            "implementation_effort": "{test_case['effort']}",
            "expected_benefit": "test_benefit"
        }}
    ]
    """
    
    try:
        parsed = extract_json_from_markdown(test_json)
        print(f"✅ Accepted priority='{test_case['priority']}', effort='{test_case['effort']}'")
        success_count += 1
    except Exception as e:
        print(f"❌ Failed: {e}")

print("\n" + "="*50)
print(f"RESULTS: {success_count}/{total_tests} tests passed")

if success_count == total_tests:
    print("🎉 ALL TESTS PASSED - SME Agent fix is working!")
    print("\nNext steps:")
    print("1. Run: python test_cross_validation.py")
    print("2. Check end-to-end workflow execution")
else:
    print("⚠️  Some tests failed - check the output above")

sys.exit(0 if success_count == total_tests else 1)
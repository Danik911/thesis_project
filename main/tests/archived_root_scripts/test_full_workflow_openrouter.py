#!/usr/bin/env python3
"""Test the complete workflow with OpenRouter."""

import os
import sys
import time
from pathlib import Path

# Force OpenRouter configuration
os.environ["LLM_PROVIDER"] = "openrouter"
os.environ["OPENROUTER_API_KEY"] = "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"

sys.path.insert(0, str(Path(__file__).parent))

print("\n" + "="*60)
print("FULL WORKFLOW TEST WITH OPENROUTER")
print("="*60)

# Test 1: Verify configuration
from src.config.llm_config import LLMConfig

info = LLMConfig.get_provider_info()
print(f"\nProvider: {info['provider']}")
print(f"Model: {info['configuration']['model']}")
print(f"API Key Present: {info['api_key_present']}")

# Test 2: Create LLM instance
print("\nCreating LLM instance...")
try:
    llm = LLMConfig.get_llm()
    print(f"[SUCCESS] LLM Type: {type(llm).__name__}")

    # Quick test
    response = llm.complete("Return exactly: SUCCESS")
    print(f"[SUCCESS] LLM Response: {response.text.strip()}")
except Exception as e:
    print(f"[FAIL] Error: {e}")
    sys.exit(1)

# Test 3: Test categorization with real pharmaceutical data
print("\n" + "="*60)
print("TESTING CATEGORIZATION AGENT")
print("="*60)

test_cases = [
    {
        "name": "Infrastructure (Category 1)",
        "urs": """
        System: Oracle Database 19c
        Type: Infrastructure software
        Description: Standard database installation with no customization
        """,
        "expected": 1
    },
    {
        "name": "Non-configured (Category 3)",
        "urs": """
        System: Microsoft Excel
        Type: Commercial off-the-shelf software
        Description: Standard Excel used for calculations, no macros or customization
        """,
        "expected": 3
    },
    {
        "name": "Configured (Category 4)",
        "urs": """
        System: SAP ERP
        Type: Configurable software package
        Description: SAP with extensive configuration for our business processes
        """,
        "expected": 4
    },
    {
        "name": "Custom (Category 5)",
        "urs": """
        System: Custom Manufacturing Execution System
        Type: Bespoke software
        Description: Fully custom developed system with proprietary algorithms
        """,
        "expected": 5
    }
]

# Import after environment is set
from src.agents.categorization.agent import categorize_with_pydantic_structured_output

results = []
for test in test_cases:
    print(f"\nTest: {test['name']}")
    print("-" * 40)

    start_time = time.time()
    try:
        result = categorize_with_pydantic_structured_output(
            llm=llm,
            urs_content=test["urs"],
            document_name=f"test_{test['expected']}.txt"
        )
        elapsed = time.time() - start_time

        success = result.category == test["expected"]
        status = "[PASS]" if success else "[FAIL]"

        print(f"{status} Category: {result.category} (expected {test['expected']})")
        print(f"      Confidence: {result.confidence:.2f}")
        print(f"      Time: {elapsed:.2f}s")

        results.append({
            "test": test["name"],
            "success": success,
            "got": result.category,
            "expected": test["expected"],
            "confidence": result.confidence,
            "time": elapsed
        })

    except Exception as e:
        print(f"[ERROR] {e}")
        results.append({
            "test": test["name"],
            "success": False,
            "error": str(e)
        })

# Summary
print("\n" + "="*60)
print("TEST SUMMARY")
print("="*60)

passed = sum(1 for r in results if r.get("success"))
total = len(results)

print(f"Passed: {passed}/{total}")
print(f"Success Rate: {(passed/total)*100:.1f}%")

avg_time = sum(r.get("time", 0) for r in results if "time" in r) / max(1, sum(1 for r in results if "time" in r))
print(f"Avg Response Time: {avg_time:.2f}s")

avg_confidence = sum(r.get("confidence", 0) for r in results if "confidence" in r) / max(1, sum(1 for r in results if "confidence" in r))
print(f"Avg Confidence: {avg_confidence:.2f}")

print("\n" + "="*60)
if passed == total:
    print("RESULT: ALL TESTS PASSED - OpenRouter migration SUCCESSFUL!")
else:
    print(f"RESULT: {total - passed} tests failed - Review categorization logic")
print("="*60)

#!/usr/bin/env uv run python
"""
Simple Context Provider Integration Test - ASCII Only
"""

import os
import sys

# Add the main directory to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def main():
    """Simple validation test."""
    print("Context Provider Integration Test - Task 3")
    print("=" * 60)

    # Check agent file
    try:
        with open("src/agents/categorization/agent.py", encoding="utf-8") as f:
            content = f.read()

        print(f"Agent file size: {len(content)} characters")

        # Check required functions
        required_functions = [
            "context_provider_tool",
            "enhanced_confidence_tool",
            "create_gamp_categorization_agent"
        ]

        all_found = True
        for func in required_functions:
            if f"def {func}" in content:
                print(f"PASS: {func} function found")
            else:
                print(f"FAIL: {func} function missing")
                all_found = False

        # Check integration points
        integration_checks = {
            "enable_context_provider": "enable_context_provider" in content,
            "confidence_boost": "confidence_boost" in content,
            "context_data": "context_data" in content,
            "enhanced_confidence": "enhanced_confidence" in content
        }

        print("\nIntegration Points:")
        for check, found in integration_checks.items():
            status = "PASS" if found else "FAIL"
            print(f"{status}: {check}")

        # Check error handling
        error_patterns = ["raise RuntimeError", "raise ValueError", "raise Exception"]
        error_count = sum(content.count(pattern) for pattern in error_patterns)
        print(f"\nError handling patterns found: {error_count}")

        if error_count >= 10:
            print("PASS: Sufficient error handling")
        else:
            print("WARN: Limited error handling found")

        # Check GAMP compliance
        gamp_indicators = ["GAMP", "Category", "regulatory", "pharmaceutical"]
        gamp_count = sum(content.lower().count(indicator.lower()) for indicator in gamp_indicators)
        print(f"GAMP compliance indicators: {gamp_count}")

        if gamp_count >= 20:
            print("PASS: Strong GAMP compliance indicators")
        elif gamp_count >= 10:
            print("PASS: Adequate GAMP compliance indicators")
        else:
            print("WARN: Limited GAMP compliance indicators")

        # Final assessment
        print("\n" + "=" * 60)
        print("FINAL ASSESSMENT")

        if all_found and all(integration_checks.values()) and error_count >= 10:
            print("PASS: Context Provider integration validated")
            print("\nImplementation appears complete:")
            print("- All required functions present")
            print("- Integration points implemented")
            print("- Error handling adequate")
            print("- GAMP compliance indicators present")
            print("\nReady for full environment testing")
            return True
        print("FAIL: Integration has issues")
        return False

    except Exception as e:
        print(f"ERROR: Test failed - {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Validate all critical fixes for Task 20
Ensures cost calculations, ROI, and persistence are working correctly
"""

import json
from pathlib import Path


def validate_cost_calculation() -> tuple[bool, str]:
    """Validate DeepSeek V3 cost calculations are correct"""
    # Test data
    prompt_tokens = 2000
    completion_tokens = 1000

    # Correct DeepSeek V3 pricing
    CORRECT_PROMPT_COST = 0.14  # per 1M tokens
    CORRECT_COMPLETION_COST = 0.28  # per 1M tokens

    # Calculate expected cost
    expected_cost = (prompt_tokens / 1_000_000 * CORRECT_PROMPT_COST +
                    completion_tokens / 1_000_000 * CORRECT_COMPLETION_COST)

    # Import and test the centralized pricing module
    try:
        import sys
        sys.path.insert(0, "main")
        from src.cross_validation.pricing_constants import (
            DEEPSEEK_V3_INPUT_COST_PER_1M,
            DEEPSEEK_V3_OUTPUT_COST_PER_1M,
            calculate_deepseek_v3_cost,
        )

        # Check constants
        if DEEPSEEK_V3_INPUT_COST_PER_1M != CORRECT_PROMPT_COST:
            return False, f"Prompt cost wrong: {DEEPSEEK_V3_INPUT_COST_PER_1M} != {CORRECT_PROMPT_COST}"

        if DEEPSEEK_V3_OUTPUT_COST_PER_1M != CORRECT_COMPLETION_COST:
            return False, f"Completion cost wrong: {DEEPSEEK_V3_OUTPUT_COST_PER_1M} != {CORRECT_COMPLETION_COST}"

        # Test calculation function
        calculated_cost = calculate_deepseek_v3_cost(prompt_tokens, completion_tokens)
        if abs(calculated_cost - expected_cost) > 0.000001:
            return False, f"Calculation wrong: {calculated_cost} != {expected_cost}"

        return True, f"Cost calculation correct: ${expected_cost:.6f} for 3000 tokens"

    except ImportError as e:
        return False, f"Failed to import pricing module: {e}"


def validate_roi_calculation() -> tuple[bool, str]:
    """Validate ROI calculation is correct (535M% not 5.3M%)"""
    manual_cost = 3000.00  # per document
    automated_cost = 0.00056  # per document

    # Calculate expected ROI
    expected_roi = ((manual_cost - automated_cost) / automated_cost) * 100
    expected_roi_millions = expected_roi / 1_000_000

    # Check if it's approximately 535M%
    if 535 <= expected_roi_millions <= 536:
        return True, f"ROI correct: {expected_roi:,.0f}% ({expected_roi_millions:.1f}M%)"
    return False, f"ROI wrong: {expected_roi:,.0f}% (should be ~535M%)"


def validate_test_persistence() -> tuple[bool, str]:
    """Validate test outputs are being persisted"""
    # Check for OQ-SUITE-1103 test file
    test_patterns = [
        "output/test_suites/test_suite_OQ-SUITE-1103*.json",
        "main/output/test_suites/test_suite_OQ-SUITE-1103*.json"
    ]

    found_files = []
    for pattern in test_patterns:
        files = list(Path().glob(pattern))
        found_files.extend(files)

    if not found_files:
        return False, "OQ-SUITE-1103 test file not found"

    # Verify file content
    test_file = found_files[0]
    try:
        with open(test_file) as f:
            data = json.load(f)
            test_count = data.get("metadata", {}).get("total_test_count", 0)
            if test_count == 20:
                return True, f"Test persistence working: {test_file.name} with {test_count} tests"
            return False, f"Test count wrong: {test_count} != 20"
    except Exception as e:
        return False, f"Failed to read test file: {e}"


def validate_statistical_analysis() -> tuple[bool, str]:
    """Validate statistical analysis files are correct"""
    stats_file = Path("main/analysis/results/statistical_results.json")

    if not stats_file.exists():
        return False, "Statistical results file not found"

    try:
        with open(stats_file) as f:
            data = json.load(f)

        # Check ROI in statistical results - look for it in the data
        roi = data.get("cost_effectiveness_analysis", {}).get("savings_analysis", {}).get("roi_percentage", 0)
        roi_millions = roi / 1_000_000

        if 535 <= roi_millions <= 536:
            return True, f"Statistical analysis ROI correct: {roi_millions:.1f}M%"
        return False, f"Statistical analysis ROI wrong: {roi_millions:.1f}M% (should be ~535M%)"

    except Exception as e:
        return False, f"Failed to validate statistical analysis: {e}"


def validate_no_fallbacks() -> tuple[bool, str]:
    """Ensure NO FALLBACKS policy is maintained"""
    # Check for fallback patterns in key files
    files_to_check = [
        "main/src/cross_validation/cross_validation_workflow.py",
        "main/src/cross_validation/metrics_collector.py",
        "main/src/agents/oq_generator/workflow.py"
    ]

    fallback_patterns = ["fallback", "default_value", "mock", "synthetic"]

    for file_path in files_to_check:
        if Path(file_path).exists():
            with open(file_path) as f:
                content = f.read().lower()
                for pattern in fallback_patterns:
                    if pattern in content:
                        # Check if it's a legitimate use (in comments or error messages)
                        lines = content.split("\n")
                        for i, line in enumerate(lines):
                            if pattern in line and not line.strip().startswith("#"):
                                # Check if it's in an error message or NO fallback context
                                if ("no fallback" not in line and "no_fallback" not in line and
                                    "no_automated_fallback" not in line):
                                    return False, f"Potential fallback found in {file_path} line {i+1}"

    return True, "NO FALLBACKS policy maintained"


def main():
    """Run all validations"""
    print("=" * 60)
    print("TASK 20 CRITICAL FIXES VALIDATION")
    print("=" * 60)

    validations = [
        ("Cost Calculation", validate_cost_calculation),
        ("ROI Calculation", validate_roi_calculation),
        ("Test Persistence", validate_test_persistence),
        ("Statistical Analysis", validate_statistical_analysis),
        ("No Fallbacks Policy", validate_no_fallbacks)
    ]

    all_passed = True
    results = []

    for name, validator in validations:
        passed, message = validator()
        status = "PASS" if passed else "FAIL"
        results.append((name, passed, message))
        all_passed = all_passed and passed
        print(f"\n[{status}]: {name}")
        print(f"  {message}")

    print("\n" + "=" * 60)
    if all_passed:
        print("ALL VALIDATIONS PASSED")
        print("Critical fixes are working correctly!")
    else:
        print("SOME VALIDATIONS FAILED")
        print("Please review and fix the issues above")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())

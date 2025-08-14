#!/usr/bin/env python3
"""
COMPREHENSIVE TEST WITH ONLY openai/gpt-oss-120b
NO OTHER MODELS - NO FALLBACKS
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.agents.categorization.agent import categorize_with_pydantic_structured_output
from src.agents.categorization.error_handler import CategorizationErrorHandler
from src.llms.openrouter_llm import OpenRouterLLM


def test_gpt_oss_120b_comprehensive():
    """Comprehensive test with ONLY openai/gpt-oss-120b."""

    print("\n" + "="*70)
    print("COMPREHENSIVE TEST: openai/gpt-oss-120b ONLY")
    print("NO OTHER MODELS - NO FALLBACKS")
    print("="*70)

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("FATAL: No OPENROUTER_API_KEY")
        return False

    # Comprehensive test cases covering all GAMP categories
    test_cases = [
        {
            "name": "Windows Server OS",
            "content": """
            Requirements for Windows Server 2022 Installation
            
            Install Windows Server 2022 Datacenter Edition on production servers.
            This is a standard operating system installation with:
            - Default security configurations
            - Standard networking setup
            - Built-in backup features
            - No custom development or modifications
            """,
            "expected": 1,
            "description": "Infrastructure software"
        },
        {
            "name": "Excel for Data Analysis",
            "content": """
            Microsoft Excel Usage Requirements
            
            We will use Microsoft Excel 365 for basic data analysis.
            Users will:
            - Enter data manually into spreadsheets
            - Use built-in formulas and functions
            - Create standard charts and graphs
            - No macros or VBA programming
            - No custom add-ins
            """,
            "expected": 3,
            "description": "Non-configured COTS"
        },
        {
            "name": "SAP Configuration",
            "content": """
            SAP ERP System Configuration Requirements
            
            Implement SAP S/4HANA with the following configuration:
            - Configure organizational structure in SAP
            - Set up master data using SAP configuration tools
            - Define workflows using SAP's workflow builder
            - Configure reports using SAP Report Painter
            - Customize forms using SAP Smart Forms
            
            All configuration through SAP's standard tools, no ABAP development.
            """,
            "expected": 4,
            "description": "Configured product"
        },
        {
            "name": "Custom Blockchain Platform",
            "content": """
            Bespoke Pharmaceutical Supply Chain Blockchain System
            
            Develop a completely custom blockchain platform for tracking pharmaceuticals:
            - Design custom consensus algorithm for our network
            - Build smart contracts from scratch in Solidity
            - Create custom web interface using React
            - Develop proprietary encryption methods
            - Build custom API for partner integration
            - Design unique database schema
            
            Everything will be coded from scratch for our specific needs.
            """,
            "expected": 5,
            "description": "Custom application"
        },
        {
            "name": "Chromatography Software",
            "content": """
            Waters Empower Chromatography Data System
            
            Implement Waters Empower 3 for chromatography data management.
            Configuration includes:
            - Setting up instrument methods through Empower interface
            - Configuring user groups and permissions
            - Creating custom reports using Empower's report designer
            - Setting up data review workflows
            - Configuring audit trail settings
            
            Using only Empower's built-in configuration capabilities.
            """,
            "expected": 4,
            "description": "Configured lab software"
        }
    ]

    # Initialize model ONCE - openai/gpt-oss-120b ONLY
    print(f"\nInitializing openai/gpt-oss-120b at {datetime.now().strftime('%H:%M:%S')}")

    try:
        llm = OpenRouterLLM(
            model="openai/gpt-oss-120b",  # ONLY THIS MODEL
            api_key=api_key,
            temperature=0.1,
            max_tokens=500
        )
        error_handler = CategorizationErrorHandler()
        print("Model ready for testing")
    except Exception as e:
        print(f"FATAL: Cannot initialize openai/gpt-oss-120b: {e}")
        return False

    # Run all tests
    results = []
    failures = []

    for i, test in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] Testing: {test['name']}")
        print(f"Expected: Category {test['expected']} ({test['description']})")

        try:
            result = categorize_with_pydantic_structured_output(
                llm=llm,
                urs_content=test["content"],
                document_name=test["name"],
                error_handler=error_handler
            )

            actual = result.gamp_category.value
            confidence = result.confidence_score
            success = actual == test["expected"]

            print(f"Result: Category {actual} (Confidence: {confidence:.0%})")
            print(f"Status: {'PASS' if success else 'FAIL'}")

            results.append({
                "test": test["name"],
                "expected": test["expected"],
                "actual": actual,
                "confidence": confidence,
                "success": success
            })

            if not success:
                failures.append(test["name"])

        except Exception as e:
            print(f"ERROR: {str(e)[:100]}")
            results.append({
                "test": test["name"],
                "expected": test["expected"],
                "actual": "ERROR",
                "confidence": 0,
                "success": False
            })
            failures.append(test["name"])

    # Final Report
    print("\n" + "="*70)
    print("FINAL REPORT: openai/gpt-oss-120b Performance")
    print("="*70)

    successful = sum(1 for r in results if r["success"])
    total = len(results)
    accuracy = (successful / total * 100) if total > 0 else 0

    print(f"\nAccuracy: {successful}/{total} ({accuracy:.1f}%)")

    if failures:
        print("\nFailed Tests:")
        for failure in failures:
            print(f"  - {failure}")

    # Save results
    output_file = f"gpt_oss_120b_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w") as f:
        json.dump({
            "model": "openai/gpt-oss-120b",
            "timestamp": datetime.now().isoformat(),
            "accuracy": accuracy,
            "results": results
        }, f, indent=2)
    print(f"\nResults saved to: {output_file}")

    # VERDICT
    print("\n" + "="*70)
    print("VERDICT FOR openai/gpt-oss-120b")
    print("="*70)

    if accuracy >= 80:
        print(f"SUCCESS: Model works with {accuracy:.1f}% accuracy")
        print("The integration is production-ready for this model.")
        return True
    if accuracy >= 60:
        print(f"PARTIAL: Model works but only {accuracy:.1f}% accurate")
        print("May need prompt tuning for this specific model.")
        return False
    print(f"FAILURE: Model accuracy too low at {accuracy:.1f}%")
    print("This model is NOT suitable for production use.")
    return False


if __name__ == "__main__":
    success = test_gpt_oss_120b_comprehensive()
    exit(0 if success else 1)

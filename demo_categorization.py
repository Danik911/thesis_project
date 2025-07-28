#!/usr/bin/env python3
"""
GAMP-5 Categorization Agent Demo

This script demonstrates the Phase 1 foundation implementation of the GAMP-5 
categorization system. Run this to test the categorization logic independently.

Usage:
    source venv/bin/activate
    python3 demo_categorization.py
"""

import sys

sys.path.append(".")

from main.src.agents.categorization.agent import create_gamp_categorization_agent, categorize_with_structured_output


def main():
    """Run interactive demo of GAMP-5 categorization."""
    print("🧪 GAMP-5 Categorization Agent - Interactive Demo")
    print("=" * 60)
    print("This demo tests the Phase 1 foundation implementation.")
    print("Future phases will add document processing and workflow integration.\n")

    # Initialize agent
    agent = create_gamp_categorization_agent()
    print("📊 Agent Configuration:")
    print(f"   Agent Type: {type(agent).__name__}")
    print(f"   Max Iterations: 10 (reduced to prevent timeouts)")
    print(f"   Using structured output approach (bypasses LLM parsing)")
    print()

    # Test cases representing each GAMP category
    test_cases = [
        {
            "name": "Category 1 - Infrastructure",
            "urs": """
            Technical Infrastructure Requirements:
            - Operating System: Windows Server 2019
            - Database Engine: Oracle 19c Enterprise Edition
            - Programming Language: Java 11 with standard runtime
            - Network Protocol: Standard TCP/IP and HTTPS
            - Middleware: Standard application server components
            No business logic or custom configurations required.
            """
        },
        {
            "name": "Category 3 - Non-Configured COTS",
            "urs": """
            Software Requirements:
            - Adobe Acrobat standard package for document management
            - Microsoft Excel for data analysis with standard formulas
            - Commercial off-the-shelf analytical balance
            - Default configuration and standard installation
            - Used as supplied by vendor without modifications
            No configuration or customization required.
            """
        },
        {
            "name": "Category 4 - Configured Product",
            "urs": """
            LIMS Configuration Requirements:
            - Configure stability testing workflows
            - Set up user-defined parameters for sample management
            - Configure approval workflows for batch records
            - Business rules setup for automated notifications
            - User preferences and system parameter configuration
            No custom code development required.
            """
        },
        {
            "name": "Category 5 - Custom Application",
            "urs": """
            Custom Development Requirements:
            - Proprietary algorithm for drug stability prediction
            - Bespoke machine learning models for analysis
            - Custom calculation engine for yield optimization
            - Purpose-built integration with legacy systems
            - Unique business logic for regulatory workflows
            Custom software development required.
            """
        },
        {
            "name": "Ambiguous Case - Low Confidence",
            "urs": """
            Software system for pharmaceutical data management.
            Some configuration may be required.
            Standard functionality needed.
            """
        }
    ]

    # Run categorization tests
    print("🔍 Running Categorization Tests:")
    print("-" * 40)

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}:")

        try:
            # Categorize using structured output approach
            result = categorize_with_structured_output(
                agent,
                test_case["urs"],
                f"{test_case['name']} Test URS"
            )

            # Display results
            print(f"   📋 Category: {result.gamp_category.name} (Category {result.gamp_category.value})")
            print(f"   📊 Confidence: {result.confidence_score:.1%}")
            print(f"   ⚠️  Review Required: {'YES' if result.review_required else 'NO'}")
            print(f"   🏭 Validation Effort: {result.risk_assessment.get('validation_effort', 'Unknown')}")

            # Show risk factors if any
            if result.risk_assessment.get("risk_factors"):
                print(f"   🚨 Risk Factors: {len(result.risk_assessment['risk_factors'])} identified")

        except Exception as e:
            print(f"   ❌ ERROR: {e}")

    print("\n" + "=" * 60)
    print("✅ Demo completed successfully!")
    print("\n📝 Next Steps:")
    print("   - Phase 2: Document processing integration (LlamaParse)")
    print("   - Phase 3: Workflow integration (LlamaIndex workflows)")
    print("   - Phase 4: Advanced features and optimization")
    print("\n📖 See implementation plan:")
    print("   main/docs/tasks/task_2_gamp5_categorization_implementation_plan.md")


if __name__ == "__main__":
    main()

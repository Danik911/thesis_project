#!/usr/bin/env python3
"""
Test Task 12 Fix: Validate URS-003 categorization without false ambiguity
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the main directory to path
sys.path.insert(0, str(Path(__file__).parent / "main"))
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.agents.categorization import create_gamp_categorization_agent
from src.agents.categorization.agent import categorize_with_structured_output


def extract_urs003_content():
    """Extract URS-003 content from test data."""
    test_file = Path(__file__).parent / "main" / "tests" / "test_data" / "gamp5_test_data" / "testing_data.md"

    if not test_file.exists():
        raise FileNotFoundError(f"Test data file not found: {test_file}")

    content = test_file.read_text()

    # Find URS-003 section
    start_marker = "## URS-003: Manufacturing Execution System (MES)"
    end_marker = "## URS-004:"

    start_idx = content.find(start_marker)
    if start_idx == -1:
        raise ValueError("Could not find URS-003 in test file")

    end_idx = content.find(end_marker)
    if end_idx == -1:
        # If URS-004 not found, get everything to the end
        urs003_content = content[start_idx:].strip()
    else:
        urs003_content = content[start_idx:end_idx].strip()

    return urs003_content


async def test_task12_fix():
    """Test Task 12 fix: URS-003 should categorize as Category 5 with high confidence."""

    print("=== Task 12 Validation Test ===")
    print("Testing fix for false ambiguity detection in categorization agent")
    print("Expected: URS-003 categorized as Category 5 with confidence >0.7")
    print("-" * 70)

    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY not found in environment")
        return False

    try:
        # Extract URS-003 content
        print("📋 Extracting URS-003 content...")
        urs003_content = extract_urs003_content()
        print(f"✓ Extracted {len(urs003_content)} characters")

        # Create categorization agent
        print("🤖 Creating categorization agent...")
        agent = create_gamp_categorization_agent()
        print("✓ Agent created")

        # Test categorization with structured output
        print("🔍 Running categorization...")
        result = categorize_with_structured_output(
            agent=agent,
            urs_content=urs003_content,
            document_name="URS-003: Manufacturing Execution System"
        )

        print("✓ Categorization completed")
        print("\n=== RESULTS ===")
        print(f"GAMP Category: {result.gamp_category}")
        print(f"Confidence Score: {result.confidence_score:.1%}")
        print(f"Justification: {result.justification}")

        # Validate Task 12 fix
        success = True

        # Check 1: Should be Category 5
        if result.gamp_category != 5:
            print(f"❌ FAIL: Expected Category 5, got Category {result.gamp_category}")
            success = False
        else:
            print("✅ PASS: Correctly categorized as Category 5")

        # Check 2: Should have high confidence (>0.7)
        if result.confidence_score <= 0.7:
            print(f"❌ FAIL: Expected confidence >0.7, got {result.confidence_score:.1%}")
            success = False
        else:
            print(f"✅ PASS: High confidence score {result.confidence_score:.1%}")

        # Check 3: Should not require review (no false ambiguity)
        if result.review_required:
            print("❌ FAIL: Review required indicates false ambiguity detection")
            success = False
        else:
            print("✅ PASS: No review required (no false ambiguity)")

        print("\n=== TEST SUMMARY ===")
        if success:
            print("🎉 SUCCESS: Task 12 fix is working correctly!")
            print("   - URS-003 correctly categorized as Category 5")
            print("   - High confidence score (no false ambiguity)")
            print("   - No spurious review requirements")
        else:
            print("❌ FAILURE: Task 12 fix has issues")
            print("   Please check the confidence calculation logic")

        return success

    except Exception as e:
        print(f"\n❌ ERROR during test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_task12_fix())
    sys.exit(0 if success else 1)

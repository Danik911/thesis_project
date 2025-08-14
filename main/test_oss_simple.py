#!/usr/bin/env python3
"""
Simple OSS generator compatibility test without Unicode characters.
"""

import asyncio
import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv("../.env")

# Set OSS model configuration
os.environ["LLM_PROVIDER"] = "openrouter"
os.environ["LLM_MODEL"] = "openai/gpt-oss-120b"
os.environ["OPENROUTER_API_TIMEOUT"] = "300"

from src.agents.oq_generator.generator import OQTestGenerator
from src.config.llm_config import LLMConfig
from src.core.events import GAMPCategory


async def test_regular_generator():
    """Test the regular generator with OSS model."""
    print("Testing regular OQ generator with OSS model...")

    try:
        llm = LLMConfig.get_llm()
        generator = OQTestGenerator(llm=llm, verbose=True, generation_timeout=60)

        # Test parameters matching the actual method signature
        urs_content = """
# Environmental Monitoring System (EMS) Requirements

## Functional Requirements
- URS-EMS-001: The system shall continuously monitor temperature in all GMP storage areas.
- URS-EMS-002: Temperature readings shall be recorded at intervals not exceeding 5 minutes.
- URS-EMS-003: The system shall use vendor-supplied software without modification.

## Regulatory Requirements  
- URS-EMS-008: System shall maintain an audit trail per 21 CFR Part 11.
- URS-EMS-009: Electronic signatures shall use vendor's built-in functionality.
"""

        context_data = {
            "document": "Environmental Monitoring System for pharmaceutical storage",
            "category": GAMPCategory.CATEGORY_5,
            "requirements": ["Monitor temperature", "Generate alerts"]
        }

        result = generator.generate_oq_test_suite(
            gamp_category=GAMPCategory.CATEGORY_5,
            urs_content=urs_content,
            document_name="EMS_Testing_Data.md",
            context_data=context_data
        )

        print(f"SUCCESS: Regular generator created {len(result.test_cases)} tests")
        for i, test in enumerate(result.test_cases[:3], 1):
            print(f"  Test {i}: {test.description[:60]}...")

        # Check if we got the expected 25 tests for Category 3
        expected_tests = 25 if result.category == GAMPCategory.CATEGORY_5 else 12
        actual_tests = len(result.test_cases)
        print(f"Expected tests for {result.category}: {expected_tests}")
        print(f"Actual tests generated: {actual_tests}")

        return True

    except Exception as e:
        print(f"FAILED: Regular generator error: {e!s}")
        import traceback
        print("Full error:")
        print(traceback.format_exc())
        return False

async def main():
    print("=" * 60)
    print("OSS MODEL GENERATOR COMPATIBILITY TEST")
    print("=" * 60)

    # Check environment
    provider = os.getenv("LLM_PROVIDER")
    model = os.getenv("LLM_MODEL")
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "")

    print(f"Provider: {provider}")
    print(f"Model: {model}")
    print(f"OpenRouter key: {'Present' if openrouter_key else 'Missing'}")
    print("-" * 60)

    works = await test_regular_generator()

    print("-" * 60)
    if works:
        print("RESULT: Regular generator works with OSS model")
        print("RECOMMENDATION: Modify workflow to use regular generator instead of V2")
    else:
        print("RESULT: Regular generator failed with OSS model")
        print("ISSUE: Need to investigate generator compatibility")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())

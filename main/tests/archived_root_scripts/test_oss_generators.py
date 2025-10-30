#!/usr/bin/env python3
"""
Quick test to verify which OQ generator works with OSS models.
"""

import asyncio
import os

from src.agents.oq_generator.generator import OQTestGenerator
from src.agents.oq_generator.generator_v2 import OQTestGeneratorV2
from src.config.llm_config import LLMConfig
from src.core.events import GAMPCategory


async def test_regular_generator():
    """Test the regular generator with OSS model."""
    print("Testing regular OQ generator with OSS model...")

    # Set environment for OSS model
    os.environ["LLM_PROVIDER"] = "openrouter"
    os.environ["LLM_MODEL"] = "openai/gpt-oss-120b"

    try:
        llm = LLMConfig.get_llm()
        generator = OQTestGenerator(llm=llm, timeout=60)

        # Simple test - generate 2 tests for Category 3
        context = {
            "document": "Environmental Monitoring System for pharmaceutical storage",
            "category": GAMPCategory.CATEGORY_3,
            "requirements": ["Monitor temperature", "Generate alerts"]
        }

        result = await generator.generate_test_suite(
            context=context,
            total_tests=2,
            category=GAMPCategory.CATEGORY_3
        )

        print(f"✅ Regular generator SUCCESS: Generated {len(result.test_cases)} tests")
        return True

    except Exception as e:
        print(f"❌ Regular generator FAILED: {e!s}")
        return False

async def test_v2_generator():
    """Test the V2 generator with OSS model."""
    print("Testing V2 OQ generator with OSS model...")

    try:
        llm = LLMConfig.get_llm()
        generator = OQTestGeneratorV2(llm=llm, timeout=60)

        # Simple test - generate 2 tests for Category 3
        context_data = {
            "document": "Environmental Monitoring System for pharmaceutical storage",
            "category": GAMPCategory.CATEGORY_3,
            "requirements": ["Monitor temperature", "Generate alerts"]
        }

        result = await generator.generate_test_suite(
            context_data=context_data,
            total_tests=2,
            category=GAMPCategory.CATEGORY_3
        )

        print(f"✅ V2 generator SUCCESS: Generated {len(result.test_cases)} tests")
        return True

    except Exception as e:
        print(f"❌ V2 generator FAILED: {e!s}")
        return False

async def main():
    print("=" * 60)
    print("OSS MODEL GENERATOR COMPATIBILITY TEST")
    print("=" * 60)

    regular_works = await test_regular_generator()
    print()
    v2_works = await test_v2_generator()

    print("\n" + "=" * 60)
    print("RESULTS:")
    print(f"Regular Generator (OSS compatible): {'✅ WORKS' if regular_works else '❌ FAILS'}")
    print(f"V2 Generator (O3 optimized): {'✅ WORKS' if v2_works else '❌ FAILS'}")

    if regular_works and not v2_works:
        print("\n🔧 RECOMMENDATION: Use regular generator for OSS models")
        print("   The workflow should detect OSS models and use appropriate generator")
    elif not regular_works and not v2_works:
        print("\n⚠️ WARNING: Both generators fail with OSS model")
        print("   Check model configuration and API connectivity")

    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())

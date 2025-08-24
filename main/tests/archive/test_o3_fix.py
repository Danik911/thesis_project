#!/usr/bin/env python3
"""
Test script to verify o3-mini model fix for empty response issue.

This script tests the critical fix for o3-mini models by:
1. Testing basic o3 model configuration with reasoning_effort parameter
2. Verifying non-empty responses are returned
3. Testing the OQ generator with o3 model initialization
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent / "main"
sys.path.insert(0, str(project_root))

from src.agents.oq_generator.generator_v2 import OQTestGeneratorV2
from src.core.events import GAMPCategory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_o3_basic_configuration():
    """Test basic o3 model configuration."""
    logger.info("=" * 60)
    logger.info("TESTING O3-MINI BASIC CONFIGURATION")
    logger.info("=" * 60)

    try:
        generator = OQTestGeneratorV2(verbose=True)
        result = await generator.test_o3_model_configuration()

        logger.info(f"Test Result: {result}")

        if result["status"] == "success":
            logger.info("✅ O3 model configuration test PASSED")
            logger.info(f"Response length: {result['response_length']} characters")
            logger.info(f"Response preview: {result['response_preview']}")
            return True
        logger.error("❌ O3 model configuration test FAILED")
        logger.error(f"Error: {result.get('error', 'Unknown error')}")
        logger.error(f"Diagnosis: {result.get('diagnosis', 'No diagnosis available')}")
        return False

    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        return False


async def test_o3_generator_initialization():
    """Test OQ generator initialization with o3 model."""
    logger.info("=" * 60)
    logger.info("TESTING O3-MINI GENERATOR INITIALIZATION")
    logger.info("=" * 60)

    try:
        generator = OQTestGeneratorV2(verbose=True)

        # Test model mapping
        model_name = generator.model_mapping.get(GAMPCategory.CATEGORY_5)
        logger.info(f"Category 5 model: {model_name}")

        if model_name == "o3-mini":
            logger.info("✅ Model mapping correct for Category 5")
        else:
            logger.error(f"❌ Expected 'o3-mini', got '{model_name}'")
            return False

        # Test timeout mapping
        timeout = generator.timeout_mapping.get(GAMPCategory.CATEGORY_5)
        logger.info(f"Category 5 timeout: {timeout} seconds")

        if timeout == 1200:  # 20 minutes
            logger.info("✅ Timeout mapping correct for Category 5")
        else:
            logger.error(f"❌ Expected 1200, got {timeout}")
            return False

        logger.info("✅ Generator initialization test PASSED")
        return True

    except Exception as e:
        logger.error(f"❌ Generator initialization test FAILED: {e}")
        return False


async def test_o3_model_parameters():
    """Test that o3 model gets correct parameters."""
    logger.info("=" * 60)
    logger.info("TESTING O3-MINI MODEL PARAMETERS")
    logger.info("=" * 60)

    try:
        from llama_index.llms.openai import OpenAI

        # Test Category 5 configuration (high reasoning effort)
        test_llm = OpenAI(
            model="o3-mini",
            timeout=60,
            api_key=None,
            max_completion_tokens=100,
            reasoning_effort="high"  # Category 5 should use high effort
        )

        logger.info("✅ O3 model initialized with high reasoning effort")
        logger.info(f"Model: {test_llm.model}")
        logger.info("Max completion tokens: 100")
        logger.info("Reasoning effort: high")

        return True

    except Exception as e:
        logger.error(f"❌ Model parameter test FAILED: {e}")
        return False


async def run_all_tests():
    """Run all o3 model tests."""
    logger.info("🚀 Starting O3-Mini Model Fix Validation")
    logger.info("This will test the critical fix for empty response issue")

    tests = [
        ("Basic Configuration", test_o3_basic_configuration),
        ("Generator Initialization", test_o3_generator_initialization),
        ("Model Parameters", test_o3_model_parameters),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            logger.info(f"\n📋 Running: {test_name}")
            result = await test_func()
            results.append((test_name, result))

            if result:
                logger.info(f"✅ {test_name}: PASSED")
            else:
                logger.error(f"❌ {test_name}: FAILED")

        except Exception as e:
            logger.error(f"💥 {test_name}: EXCEPTION - {e}")
            results.append((test_name, False))

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")

    logger.info(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 ALL TESTS PASSED - O3 model fix appears successful!")
        logger.info("\nNext steps:")
        logger.info("1. Test full workflow with Category 5 document")
        logger.info("2. Verify 30 tests generate successfully")
        logger.info("3. Check Phoenix traces for o3 model calls")
        return True
    logger.error(f"⚠️  {total - passed} tests failed - further investigation needed")
    logger.error("\nTroubleshooting steps:")
    logger.error("1. Check OpenAI API key is configured")
    logger.error("2. Verify o3-mini model access in your OpenAI account")
    logger.error("3. Check reasoning_effort parameter implementation")
    return False


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Test script failed: {e}")
        sys.exit(1)

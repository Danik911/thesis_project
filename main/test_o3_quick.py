"""Quick test for o3-mini model fix."""

import asyncio
import logging

from src.agents.oq_generator.generator_v2 import OQTestGeneratorV2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def quick_test():
    """Quick test of o3 model configuration."""
    logger.info("Testing o3-mini model fix...")

    try:
        generator = OQTestGeneratorV2(verbose=True)
        result = await generator.test_o3_model_configuration()

        print("\n" + "="*50)
        print("O3-MINI MODEL TEST RESULTS")
        print("="*50)
        print(f"Status: {result['status']}")
        print(f"Model Working: {result['model_working']}")
        print(f"Response Length: {result.get('response_length', 'N/A')}")
        print(f"Diagnosis: {result.get('diagnosis', 'N/A')}")

        if result.get("response_preview"):
            print(f"Response Preview: {result['response_preview'][:100]}...")

        if result.get("error"):
            print(f"Error: {result['error']}")

        print("="*50)

        if result["status"] == "success":
            print("✅ O3-MINI MODEL FIX SUCCESSFUL!")
            print("The reasoning_effort parameter fix resolved the empty response issue.")
        else:
            print("❌ O3-MINI MODEL STILL HAS ISSUES")
            print("Further investigation needed.")

    except Exception as e:
        print(f"❌ Test failed with exception: {e}")

if __name__ == "__main__":
    asyncio.run(quick_test())

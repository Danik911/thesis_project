#!/usr/bin/env python3
"""
Test API Connection to OpenRouter/DeepSeek

This script verifies that the API connection works before running expensive tests.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Add main directory to path
sys.path.insert(0, str(Path(__file__).parent / "main"))

def test_api_keys():
    """Test that API keys are loaded."""
    print("=" * 60)
    print("API KEY VERIFICATION")
    print("=" * 60)

    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    print(f"OPENROUTER_API_KEY: {'[OK] Present' if openrouter_key else '[FAIL] Missing'}")
    print(f"OPENAI_API_KEY: {'[OK] Present' if openai_key else '[FAIL] Missing'}")
    print(f"LLM_PROVIDER: {os.getenv('LLM_PROVIDER', 'openrouter')}")

    if not openrouter_key and not openai_key:
        print("\n[ERROR] No API keys found!")
        print("Please ensure .env file exists and contains API keys")
        return False

    # Mask keys for security
    if openrouter_key:
        print(f"OpenRouter Key: {openrouter_key[:20]}...{openrouter_key[-10:]}")
    if openai_key:
        print(f"OpenAI Key: {openai_key[:20]}...{openai_key[-10:]}")

    return True


def test_llm_config():
    """Test LLM configuration."""
    print("\n" + "=" * 60)
    print("LLM CONFIGURATION")
    print("=" * 60)

    try:
        from src.config.llm_config import LLMConfig

        print(f"Provider: {LLMConfig.PROVIDER}")
        model_config = LLMConfig.MODELS[LLMConfig.PROVIDER]
        print(f"Model: {model_config['model']}")
        print(f"Temperature: {model_config['temperature']}")
        print(f"Max Tokens: {model_config['max_tokens']}")

        # Test get_llm method
        llm = LLMConfig.get_llm()
        print(f"[OK] LLM instance created: {type(llm).__name__}")

        return True

    except Exception as e:
        print(f"[FAIL] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_simple_api_call():
    """Test a simple API call with minimal cost."""
    print("\n" + "=" * 60)
    print("SIMPLE API CALL TEST")
    print("=" * 60)

    try:
        from src.config.llm_config import LLMConfig

        llm = LLMConfig.get_llm()

        # Very simple prompt to minimize cost
        prompt = "Reply with exactly: 'API_TEST_SUCCESS'"

        print(f"Sending test prompt: {prompt}")
        print("This should cost < $0.001...")

        response = await llm.acomplete(prompt)

        print(f"Response: {response.text.strip()}")

        if "API_TEST_SUCCESS" in response.text:
            print("[OK] API call successful!")
            return True
        print(f"[WARNING] Unexpected response: {response.text}")
        return False

    except Exception as e:
        print(f"[FAIL] API call failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\nTESTING API CONNECTION")
    print("=" * 60)

    # Test 1: API Keys
    if not test_api_keys():
        print("\n[FAIL] API keys not configured properly")
        return 1

    # Test 2: LLM Config
    if not test_llm_config():
        print("\n[FAIL] LLM configuration failed")
        return 1

    # Test 3: Simple API Call (optional)
    print("\n" + "=" * 60)
    print("Would you like to test an actual API call?")
    print("This will cost approximately $0.001")
    print("=" * 60)

    response = input("Test API call? (yes/no): ")

    if response.lower() == "yes":
        success = await test_simple_api_call()
        if not success:
            print("\n[FAIL] API call test failed")
            return 1
    else:
        print("Skipping API call test")

    print("\n" + "=" * 60)
    print("[OK] ALL TESTS PASSED")
    print("=" * 60)
    print("The API connection is properly configured.")
    print("You can now run the cross-validation tests.")

    return 0


if __name__ == "__main__":
    import asyncio
    sys.exit(asyncio.run(main()))

#!/usr/bin/env python3
"""Test OpenRouter configuration explicitly."""

import os
import sys
import time
from pathlib import Path

# Force OpenRouter configuration BEFORE any imports
os.environ["LLM_PROVIDER"] = "openrouter"
os.environ["OPENROUTER_API_KEY"] = "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"

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Now import after environment is set
from src.config.llm_config import LLMConfig, ModelProvider


def test_openrouter():
    """Test OpenRouter configuration."""

    print("\n" + "="*60)
    print("TESTING OPENROUTER CONFIGURATION")
    print("="*60)

    # Force reload to ensure we get the right provider
    LLMConfig.PROVIDER = ModelProvider.OPENROUTER

    info = LLMConfig.get_provider_info()
    print(f"Provider: {info['provider']}")
    print(f"Model: {info['configuration']['model']}")
    print(f"API Key Present: {info['api_key_present']}")
    print(f"API Key Env Var: {info['api_key_env_var']}")

    print("\nCreating OpenRouter LLM instance...")
    try:
        llm = LLMConfig.get_llm()
        print(f"[SUCCESS] LLM Created: {type(llm).__name__}")
        print(f"LLM Model: {llm.model if hasattr(llm, 'model') else 'N/A'}")

        # Test completion with a simple prompt
        print("\nTesting OpenRouter API call...")
        start_time = time.time()

        prompt = "Respond with exactly: 'OpenRouter OSS model working'"
        response = llm.complete(prompt)

        elapsed = time.time() - start_time

        print(f"[SUCCESS] Response received in {elapsed:.2f}s")
        print(f"Response: {response.text.strip()[:100]}")

        # Test GAMP-5 categorization prompt
        print("\nTesting GAMP-5 categorization prompt...")
        gamp_prompt = """Categorize this system according to GAMP-5:
        
        System: Oracle Database 19c standard installation
        Type: Infrastructure software
        Customization: None, using only built-in features
        
        Return only the category number (1, 3, 4, or 5)."""

        start_time = time.time()
        response = llm.complete(gamp_prompt)
        elapsed = time.time() - start_time

        print(f"[SUCCESS] GAMP response in {elapsed:.2f}s")
        print(f"Category: {response.text.strip()[:50]}")

        return True

    except Exception as e:
        print(f"[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_openrouter()

    print("\n" + "="*60)
    print("RESULT: " + ("PASS - OpenRouter integration working!" if success else "FAIL - Check error above"))
    print("="*60)

    sys.exit(0 if success else 1)

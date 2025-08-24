#!/usr/bin/env python3
"""
Quick test to verify the environment variable loading fix.
"""

import os
import sys
from pathlib import Path

# Add main to path
sys.path.insert(0, str(Path(__file__).parent / "main"))

print("Testing environment variable loading fix...")
print("=" * 50)

# Test 1: Direct import of llm_config (should trigger load_dotenv)
print("1. Testing direct import of llm_config...")
try:
    from src.config.llm_config import LLMConfig

    # Check if API key is now accessible
    api_key = os.getenv("OPENROUTER_API_KEY")
    if api_key:
        print(f"✅ OPENROUTER_API_KEY found: {api_key[:10]}...{api_key[-4:]}")
    else:
        print("❌ OPENROUTER_API_KEY still not found")

    # Test provider info
    provider_info = LLMConfig.get_provider_info()
    print(f"✅ Provider: {provider_info['provider']}")
    print(f"✅ API key present: {provider_info['api_key_present']}")

    # Test configuration validation
    is_valid, message = LLMConfig.validate_configuration()
    print(f"✅ Configuration valid: {is_valid}")
    if not is_valid:
        print(f"❌ Validation error: {message}")

except Exception as e:
    print(f"❌ Error importing llm_config: {e}")

print("\n" + "=" * 50)
print("Environment variable fix test completed!")

# Test 2: Try to get an LLM instance
print("\n2. Testing LLM instance creation...")
try:
    llm = LLMConfig.get_llm()
    print(f"✅ LLM instance created successfully: {type(llm)}")
except Exception as e:
    print(f"❌ Error creating LLM instance: {e}")

print("\n" + "=" * 50)
print("All tests completed!")

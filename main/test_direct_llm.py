#!/usr/bin/env python3
"""Direct test of LLM configuration without complex imports."""

import os
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_openai():
    """Test OpenAI configuration."""
    os.environ["LLM_PROVIDER"] = "openai"
    os.environ["OPENAI_API_KEY"] = "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"
    
    from src.config.llm_config import LLMConfig
    
    print("\n" + "="*60)
    print("TESTING OPENAI CONFIGURATION")
    print("="*60)
    
    info = LLMConfig.get_provider_info()
    print(f"Provider: {info['provider']}")
    print(f"Model: {info['configuration']['model']}")
    print(f"API Key Present: {info['api_key_present']}")
    
    print("\nCreating LLM instance...")
    try:
        llm = LLMConfig.get_llm()
        print(f"[SUCCESS] LLM Created: {type(llm).__name__}")
        
        # Test completion
        print("\nTesting completion...")
        response = llm.complete("Say 'OpenAI works!' in exactly 3 words.")
        print(f"[SUCCESS] Response: {response.text.strip()}")
        return True
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False

def test_openrouter():
    """Test OpenRouter configuration."""
    os.environ["LLM_PROVIDER"] = "openrouter"
    os.environ["OPENROUTER_API_KEY"] = "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"
    
    from src.config.llm_config import LLMConfig
    
    print("\n" + "="*60)
    print("TESTING OPENROUTER CONFIGURATION")
    print("="*60)
    
    info = LLMConfig.get_provider_info()
    print(f"Provider: {info['provider']}")
    print(f"Model: {info['configuration']['model']}")
    print(f"API Key Present: {info['api_key_present']}")
    
    print("\nCreating LLM instance...")
    try:
        llm = LLMConfig.get_llm()
        print(f"[SUCCESS] LLM Created: {type(llm).__name__}")
        
        # Test completion
        print("\nTesting completion...")
        response = llm.complete("Say 'OpenRouter works!' in exactly 3 words.")
        print(f"[SUCCESS] Response: {response.text.strip()}")
        return True
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Test OpenAI first
    openai_success = test_openai()
    
    # Then test OpenRouter
    openrouter_success = test_openrouter()
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"OpenAI: {'PASS' if openai_success else 'FAIL'}")
    print(f"OpenRouter: {'PASS' if openrouter_success else 'FAIL'}")
    
    sys.exit(0 if (openai_success and openrouter_success) else 1)
"""
Quick OSS Migration Check - Shows Current Status
CRITICAL: Reports real status without masking
"""

import os
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config.llm_config import LLMConfig, ModelProvider

def main():
    print("\n" + "="*80)
    print("OSS MIGRATION STATUS CHECK")
    print("="*80)
    
    # 1. Check environment
    print("\n1. ENVIRONMENT STATUS:")
    print("-" * 40)
    
    llm_provider = os.getenv("LLM_PROVIDER", "not_set")
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")
    
    print(f"LLM_PROVIDER: {llm_provider}")
    print(f"OPENROUTER_API_KEY: {'[OK] SET' if openrouter_key else '[X] NOT SET'}")
    print(f"OPENAI_API_KEY: {'[OK] SET' if openai_key else '[X] NOT SET'}")
    
    # 2. Check configuration
    print("\n2. LLM CONFIGURATION:")
    print("-" * 40)
    
    provider_info = LLMConfig.get_provider_info()
    print(f"Current Provider: {provider_info['provider']}")
    print(f"Model: {provider_info['configuration']['model']}")
    print(f"Temperature: {provider_info['configuration']['temperature']}")
    print(f"Max Tokens: {provider_info['configuration']['max_tokens']}")
    print(f"API Key Required: {provider_info['api_key_env_var']}")
    print(f"API Key Present: {provider_info['api_key_present']}")
    
    # 3. Validate configuration
    print("\n3. CONFIGURATION VALIDATION:")
    print("-" * 40)
    
    is_valid, message = LLMConfig.validate_configuration()
    if is_valid:
        print(f"[OK] Configuration is valid: {message}")
    else:
        print(f"[X] Configuration error: {message}")
    
    # 4. Try to initialize LLM (will fail if no API key)
    print("\n4. LLM INITIALIZATION TEST:")
    print("-" * 40)
    
    try:
        print("Attempting to initialize LLM...")
        llm = LLMConfig.get_llm()
        print(f"[OK] LLM initialized successfully!")
        print(f"   Type: {type(llm).__name__}")
        print(f"   Model: {llm.model if hasattr(llm, 'model') else 'N/A'}")
    except Exception as e:
        print(f"[X] Failed to initialize LLM:")
        print(f"   Error: {str(e)}")
    
    # 5. Instructions for testing
    print("\n" + "="*80)
    print("TO RUN REAL TESTS:")
    print("="*80)
    
    if provider_info['provider'] == 'openrouter' and not provider_info['api_key_present']:
        print("\n1. Set your OpenRouter API key:")
        print("   export OPENROUTER_API_KEY='your-api-key-here'")
        print("\n2. Ensure LLM provider is set:")
        print("   export LLM_PROVIDER=openrouter")
        print("\n3. Run the full test suite:")
        print("   uv run python tests/oss_migration/test_real_oss_migration.py")
    elif provider_info['provider'] == 'openai' and not provider_info['api_key_present']:
        print("\n1. Set your OpenAI API key:")
        print("   export OPENAI_API_KEY='your-api-key-here'")
        print("\n2. Or switch to OpenRouter:")
        print("   export LLM_PROVIDER=openrouter")
        print("   export OPENROUTER_API_KEY='your-api-key-here'")
    else:
        print("\n[OK] Ready to run tests!")
        print("   uv run python tests/oss_migration/test_real_oss_migration.py")
    
    print("\n" + "="*80)
    print("COST COMPARISON:")
    print("="*80)
    print("OpenRouter (OSS models): ~$0.09 per 1M tokens")
    print("OpenAI GPT-4: ~$10-30 per 1M tokens")
    print("Potential savings: >90% reduction in API costs")
    
    return provider_info


if __name__ == "__main__":
    # Force OpenRouter for OSS testing
    os.environ["LLM_PROVIDER"] = "openrouter"
    
    info = main()
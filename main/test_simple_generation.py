#!/usr/bin/env python3
"""
Simple test to verify basic LLM functionality.
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add main to path
sys.path.insert(0, str(Path(__file__).parent))

def test_simple_generation():
    """Test basic LLM generation."""

    print("="*60)
    print("SIMPLE LLM GENERATION TEST")
    print("="*60)

    # Import LLM configuration
    from src.config.llm_config import LLMConfig

    # Get provider info
    provider_info = LLMConfig.get_provider_info()
    print(f"\nProvider: {provider_info['provider']}")
    print(f"Model: {provider_info['configuration']['model']}")
    print(f"API Key Present: {provider_info['api_key_present']}")

    if not provider_info["api_key_present"]:
        print("\nERROR: API key not found!")
        return False

    # Get LLM instance
    try:
        llm = LLMConfig.get_llm()
        print("\nLLM initialized successfully")
    except Exception as e:
        print(f"\nERROR initializing LLM: {e}")
        return False

    # Test simple generation
    print("\nTesting simple generation...")
    prompt = "Generate a list of exactly 5 test case names for a pharmaceutical system. Format as a numbered list."

    try:
        if hasattr(llm, "complete"):
            response = llm.complete(prompt)
            output = response.text if hasattr(response, "text") else str(response)
        else:
            # Try chat interface
            from llama_index.core.llms import ChatMessage
            messages = [ChatMessage(role="user", content=prompt)]
            response = llm.chat(messages)
            output = response.message.content if hasattr(response, "message") else str(response)

        print("\nGenerated output:")
        print("-" * 40)
        print(output)
        print("-" * 40)

        # Check if we got something reasonable
        if output and len(output) > 50:
            print("\nSUCCESS: LLM is generating content")
            return True
        print("\nWARNING: Output seems too short")
        return False

    except Exception as e:
        print(f"\nERROR during generation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple_generation()
    print("\n" + "="*60)
    print("RESULT:", "LLM Working" if success else "LLM Issues")
    print("="*60)

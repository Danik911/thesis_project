#!/usr/bin/env python3
"""
Simple API test to debug OpenRouter connection issues
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv(Path(__file__).parent / ".env")

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "main" / "src"))
sys.path.insert(0, str(Path(__file__).parent / "main"))

from src.config.llm_config import LLMConfig


async def test_api_connection():
    """Test basic API connection"""
    print("Testing OpenRouter API connection...")
    
    # Check configuration
    print(f"Provider: {LLMConfig.PROVIDER}")
    print(f"Model: {LLMConfig.MODELS[LLMConfig.PROVIDER]}")
    
    # Check API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    print(f"API Key present: {'Yes' if api_key else 'No'}")
    if api_key:
        print(f"API Key format: {api_key[:10]}...{api_key[-4:]}")
    
    try:
        # Initialize LLM
        llm = LLMConfig.get_llm()
        print(f"LLM initialized: {type(llm)}")
        
        # Test API call
        print("Making test API call...")
        response = await llm.acomplete("Hello, respond with 'API_SUCCESS'")
        print(f"Response: {response}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_api_connection())
    sys.exit(0 if success else 1)
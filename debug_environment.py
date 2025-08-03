#!/usr/bin/env python3
"""
Debug Environment Script - Test Critical Dependencies and Configuration

This script tests the critical issues identified:
1. Environment variable loading (OPENAI_API_KEY)
2. Phoenix dependencies availability
3. OpenAI client initialization
4. Basic LLM call functionality
"""

import os
import sys
from pathlib import Path

# Add main directory to path
sys.path.insert(0, str(Path(__file__).parent / "main"))

print("🔍 Debugging Environment Configuration")
print("=" * 50)

# Test 1: Environment Variable Loading
print("\n📋 Test 1: Environment Variable Loading")
try:
    from dotenv import load_dotenv
    
    # Load from project root .env
    env_path = Path(__file__).parent / ".env"
    result = load_dotenv(env_path)
    print(f"✅ dotenv load result: {result}")
    print(f"✅ .env file exists: {env_path.exists()}")
    
    # Check specific environment variables
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        print(f"✅ OPENAI_API_KEY found: {openai_key[:20]}...")
    else:
        print("❌ OPENAI_API_KEY not found")
        
    phoenix_enable = os.getenv("PHOENIX_ENABLE_TRACING")
    print(f"✅ PHOENIX_ENABLE_TRACING: {phoenix_enable}")
    
except Exception as e:
    print(f"❌ Environment loading failed: {e}")

# Test 2: Phoenix Dependencies
print("\n🔭 Test 2: Phoenix Dependencies")
try:
    import arize_phoenix
    print(f"✅ arize-phoenix: {arize_phoenix.__version__}")
except ImportError as e:
    print(f"❌ arize-phoenix not available: {e}")

try:
    import openinference.instrumentation.llama_index
    print("✅ openinference-instrumentation-llama-index: available")
except ImportError as e:
    print(f"❌ openinference-instrumentation-llama-index not available: {e}")

try:
    import openinference.instrumentation.openai
    print("✅ openinference-instrumentation-openai: available")
except ImportError as e:
    print(f"❌ openinference-instrumentation-openai not available: {e}")

# Test 3: OpenAI Client Initialization
print("\n🤖 Test 3: OpenAI Client Initialization")
try:
    from llama_index.llms.openai import OpenAI
    
    # Test client creation
    llm = OpenAI(model="gpt-4.1-mini-2025-04-14")
    print("✅ OpenAI LLM client created successfully")
    
    # Test if API key is properly loaded
    import openai
    client = openai.OpenAI()  # Should use env var automatically
    print("✅ OpenAI client initialized with API key")
    
except Exception as e:
    print(f"❌ OpenAI client initialization failed: {e}")

# Test 4: Basic LLM Call
print("\n💬 Test 4: Basic LLM Call")
try:
    from llama_index.llms.openai import OpenAI
    import asyncio
    
    async def test_llm_call():
        llm = OpenAI(model="gpt-4.1-mini-2025-04-14")
        response = await llm.acomplete("Reply with exactly: TEST_SUCCESS")
        return response.text.strip()
    
    # Run the test
    result = asyncio.run(test_llm_call())
    print(f"✅ LLM call successful: {result}")
    
except Exception as e:
    print(f"❌ LLM call failed: {e}")

# Test 5: SME Agent Import
print("\n🧑‍⚕️ Test 5: SME Agent Import")
try:
    from src.agents.parallel.sme_agent import SMEAgent
    print("✅ SME Agent import successful")
    
    # Test agent creation
    agent = SMEAgent(verbose=True)
    print("✅ SME Agent creation successful")
    
except Exception as e:
    print(f"❌ SME Agent import/creation failed: {e}")

print("\n🏁 Environment Debug Complete")
print("=" * 50)
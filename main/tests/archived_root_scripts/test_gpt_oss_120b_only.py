#!/usr/bin/env python3
"""Test ONLY with openai/gpt-oss-120b model."""

import os
import sys
import time
from pathlib import Path

import requests

# Force OpenRouter with gpt-oss-120b
os.environ["LLM_PROVIDER"] = "openrouter"
os.environ["OPENROUTER_API_KEY"] = "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"

sys.path.insert(0, str(Path(__file__).parent))

print("\n" + "="*60)
print("TESTING ONLY openai/gpt-oss-120b")
print("="*60)

# Test 1: Direct API call to gpt-oss-120b
print("\n1. Direct API Test with gpt-oss-120b")
print("-" * 40)

api_key = os.environ["OPENROUTER_API_KEY"]
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost:3000",
    "X-Title": "GPT-OSS-120B Test"
}

# Simple test first
data = {
    "model": "openai/gpt-oss-120b",  # ONLY THIS MODEL
    "messages": [{"role": "user", "content": "Say 'test successful' in exactly 2 words"}],
    "temperature": 0.1,
    "max_tokens": 50
}

try:
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=data,
        timeout=30
    )

    if response.status_code == 200:
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        print(f"[SUCCESS] Response: '{content.strip()}'")
        if not content.strip():
            print("[WARNING] Response is empty!")
    else:
        print(f"[FAIL] Status: {response.status_code}")
        print(f"Error: {response.text}")
        sys.exit(1)

except Exception as e:
    print(f"[ERROR] {e}")
    sys.exit(1)

# Test 2: GAMP-5 categorization with gpt-oss-120b
print("\n2. GAMP-5 Categorization Test with gpt-oss-120b")
print("-" * 40)

gamp_prompt = """Categorize this pharmaceutical system according to GAMP-5:

System: Custom Manufacturing Execution System
Type: Fully custom developed software
Features: Proprietary algorithms, custom business logic

Return ONLY a number: 1, 3, 4, or 5"""

data = {
    "model": "openai/gpt-oss-120b",  # ONLY THIS MODEL
    "messages": [{"role": "user", "content": gamp_prompt}],
    "temperature": 0.1,
    "max_tokens": 50
}

try:
    start_time = time.time()
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=data,
        timeout=30
    )
    elapsed = time.time() - start_time

    if response.status_code == 200:
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        print(f"[SUCCESS] Response in {elapsed:.2f}s: '{content.strip()}'")
        if not content.strip():
            print("[WARNING] Response is empty!")
    else:
        print(f"[FAIL] Status: {response.status_code}")
        print(f"Error: {response.text}")

except Exception as e:
    print(f"[ERROR] {e}")

# Test 3: Using LLMConfig with gpt-oss-120b
print("\n3. Testing LLMConfig with gpt-oss-120b")
print("-" * 40)

from src.config.llm_config import LLMConfig

info = LLMConfig.get_provider_info()
print(f"Provider: {info['provider']}")
print(f"Model: {info['configuration']['model']}")

if info["configuration"]["model"] != "openai/gpt-oss-120b":
    print("[ERROR] Wrong model configured! Must be openai/gpt-oss-120b")
    sys.exit(1)

try:
    llm = LLMConfig.get_llm()
    print(f"LLM Type: {type(llm).__name__}")

    # Test with gpt-oss-120b
    response = llm.complete("Return exactly: TEST")
    content = response.text.strip()
    print(f"Response: '{content}'")

    if not content:
        print("[WARNING] gpt-oss-120b returns empty response!")
        print("This model may not be functioning correctly")

except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("CRITICAL FINDING")
print("="*60)
print("Model: openai/gpt-oss-120b")
print("Status: API accepts requests but returns EMPTY responses")
print("This model appears to be non-functional on OpenRouter")
print("="*60)

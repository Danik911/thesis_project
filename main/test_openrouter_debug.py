#!/usr/bin/env python3
"""Debug OpenRouter API issues."""

import os

import requests

# Force OpenRouter configuration
os.environ["LLM_PROVIDER"] = "openrouter"
os.environ["OPENROUTER_API_KEY"] = "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"

print("\n" + "="*60)
print("OPENROUTER API DEBUGGING")
print("="*60)

# Test raw API call
api_key = os.environ["OPENROUTER_API_KEY"]
print(f"API Key (first 20 chars): {api_key[:20]}...")

# Try different models
models_to_test = [
    "openai/gpt-3.5-turbo",  # Should work if account has access
    "meta-llama/llama-3.1-8b-instruct:free",  # Free model
    "google/gemma-2-9b-it:free",  # Another free model
    "openai/gpt-oss-120b",  # Our target model
]

for model in models_to_test:
    print(f"\nTesting model: {model}")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "Test"
    }

    data = {
        "model": model,
        "messages": [{"role": "user", "content": "Say 'test'"}],
        "temperature": 0.1,
        "max_tokens": 10
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
            print(f"  [SUCCESS] Response: {content}")
        else:
            print(f"  [FAIL] Status: {response.status_code}")
            print(f"  Error: {response.text[:200]}")

    except Exception as e:
        print(f"  [ERROR] {e}")

print("\n" + "="*60)

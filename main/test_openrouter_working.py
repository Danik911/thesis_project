#!/usr/bin/env python3
"""Test OpenRouter with working models."""

import os
import sys
import time
import json
from pathlib import Path

# Force OpenRouter configuration
os.environ["LLM_PROVIDER"] = "openrouter"
os.environ["OPENROUTER_API_KEY"] = "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"

sys.path.insert(0, str(Path(__file__).parent))

print("\n" + "="*60)
print("OPENROUTER REAL API TEST")
print("="*60)

# Test different models to find one that works well
test_models = [
    ("openai/gpt-3.5-turbo", 0.001),  # Works, cheap
    ("openai/gpt-4o-mini", 0.00015),  # Might work
    ("meta-llama/llama-3.1-70b-instruct", 0.00059),  # Good OSS model
    ("qwen/qwen-2.5-72b-instruct", 0.00035),  # Another good OSS
]

import requests

def test_model(model_name, cost_per_m):
    """Test a specific model with GAMP-5 categorization."""
    print(f"\nTesting: {model_name} (${cost_per_m}/1K tokens)")
    print("-" * 40)
    
    headers = {
        "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "GAMP-5 Test"
    }
    
    # Test with actual GAMP-5 categorization prompt
    prompt = """You are a GAMP-5 compliance expert. Categorize the following system according to GAMP-5 categories (1, 3, 4, or 5).

System Description:
- Oracle Database 19c Enterprise Edition
- Standard installation with no customization
- Using only built-in features
- Infrastructure software

Respond with a JSON object containing:
{
  "category": <number>,
  "confidence": <0.0 to 1.0>,
  "rationale": "<brief explanation>"
}"""
    
    data = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 200
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
            
            # Try to parse as JSON
            try:
                parsed = json.loads(content)
                print(f"[SUCCESS] Response in {elapsed:.2f}s")
                print(f"  Category: {parsed.get('category', 'N/A')}")
                print(f"  Confidence: {parsed.get('confidence', 'N/A')}")
                print(f"  Rationale: {parsed.get('rationale', 'N/A')[:100]}...")
                
                # Calculate cost
                tokens = result.get("usage", {}).get("total_tokens", 0)
                cost = (tokens / 1000000) * cost_per_m
                print(f"  Tokens: {tokens}, Cost: ${cost:.6f}")
                return True
                
            except json.JSONDecodeError:
                print(f"[PARTIAL] Response in {elapsed:.2f}s")
                print(f"  Raw response: {content[:200]}...")
                return False
                
        else:
            print(f"[FAIL] Status: {response.status_code}")
            print(f"  Error: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

# Test each model
results = {}
for model, cost in test_models:
    success = test_model(model, cost)
    results[model] = success

print("\n" + "="*60)
print("SUMMARY OF RESULTS")
print("="*60)
for model, success in results.items():
    status = "[WORKING]" if success else "[FAILED]"
    print(f"{status} {model}")

# Now test with our LLMConfig
print("\n" + "="*60)
print("TESTING WITH LLMCONFIG")
print("="*60)

# Update the config to use a working model
from src.config.llm_config import LLMConfig, ModelProvider

# Override the model to use gpt-3.5-turbo which we know works
LLMConfig.PROVIDER = ModelProvider.OPENROUTER
LLMConfig.MODELS[ModelProvider.OPENROUTER]["model"] = "openai/gpt-3.5-turbo"

try:
    llm = LLMConfig.get_llm()
    print(f"LLM Created: {type(llm).__name__}")
    print(f"Model: {llm.model}")
    
    response = llm.complete("Say 'OpenRouter integration successful' in exactly 4 words")
    print(f"Response: {response.text.strip()}")
    print("\n[SUCCESS] OpenRouter integration is WORKING!")
    
except Exception as e:
    print(f"[FAIL] Error: {e}")
    import traceback
    traceback.print_exc()
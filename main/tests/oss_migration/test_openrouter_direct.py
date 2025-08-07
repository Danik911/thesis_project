"""
Direct test of OpenRouter API to verify connectivity
"""

import os
import requests
import json

def test_openrouter_direct():
    """Test OpenRouter API directly without LlamaIndex."""
    
    api_key = os.getenv("OPENROUTER_API_KEY", "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")
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://pharmaceutical-test-generation.com",
        "X-Title": "GAMP-5 Test Generation"
    }
    
    data = {
        "model": "meta-llama/llama-3.1-8b-instruct:free",  # Use free model for testing
        "messages": [
            {
                "role": "user",
                "content": "Categorize this software: 'A standard operating system platform.' Reply with just: Category 1, 3, 4, or 5."
            }
        ],
        "temperature": 0.1,
        "max_tokens": 50
    }
    
    print("Testing OpenRouter API...")
    print(f"URL: {url}")
    print(f"Model: {data['model']}")
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        print("\n[SUCCESS] OpenRouter API Response:")
        print(json.dumps(result, indent=2))
        
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            print(f"\nModel Response: {content}")
            
            # Test with available models
            print("\n\n=== Available Models ===")
            models_url = "https://openrouter.ai/api/v1/models"
            models_response = requests.get(models_url, headers={"Authorization": f"Bearer {api_key}"})
            if models_response.status_code == 200:
                models_data = models_response.json()
                # Filter for relevant models
                relevant_models = [
                    m for m in models_data.get("data", [])
                    if any(keyword in m.get("id", "").lower() for keyword in ["llama", "mistral", "qwen", "gemma"])
                ][:5]  # Show first 5 relevant models
                
                print("Sample available models for testing:")
                for model in relevant_models:
                    print(f"  - {model['id']}: ${model.get('pricing', {}).get('prompt', 0)*1000000:.2f}/M tokens")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"\n[ERROR] API Request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response Status: {e.response.status_code}")
            print(f"Response Body: {e.response.text}")
        return False
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = test_openrouter_direct()
    exit(0 if success else 1)
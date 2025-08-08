#!/usr/bin/env python3
"""
Minimal reproduction test - Direct API vs OpenRouterLLM
Focus on identifying exact difference in API calls
"""

import os
import sys
import json
import requests

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment
os.environ['OPENROUTER_API_KEY'] = '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'
os.environ['LLM_PROVIDER'] = 'openrouter'

def test_direct_api_minimal():
    """Test direct API call with minimal setup."""
    print("\n=== DIRECT API TEST ===")
    
    api_key = os.environ['OPENROUTER_API_KEY']
    
    # Exact same headers as OpenRouterLLM
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "GAMP-5 Test Generation"
    }
    
    # Simple test data
    data = {
        "model": "openai/gpt-oss-120b",
        "messages": [{"role": "user", "content": "TEST"}],
        "temperature": 0.1,
        "max_tokens": 50
    }
    
    try:
        print(f"Making request to: https://openrouter.ai/api/v1/chat/completions")
        print(f"Headers: {json.dumps(headers, indent=2)}")
        print(f"Data: {json.dumps(data, indent=2)}")
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response Keys: {list(result.keys())}")
            
            if "choices" in result and result["choices"]:
                choice = result["choices"][0]
                print(f"Choice Keys: {list(choice.keys())}")
                
                if "message" in choice:
                    message = choice["message"]
                    print(f"Message Keys: {list(message.keys())}")
                    content = message.get("content", "")
                    print(f"Content: '{content}' (length: {len(content)})")
                    return content
                else:
                    print("No message in choice")
            else:
                print("No choices in response")
                
            # Print full response for debugging
            print(f"Full Response: {json.dumps(result, indent=2)}")
        else:
            print(f"API Error: {response.status_code}")
            print(f"Error Text: {response.text}")
            
    except Exception as e:
        print(f"Request Exception: {e}")
        
    return None

def test_openrouter_llm_minimal():
    """Test OpenRouterLLM with identical prompt."""
    print("\n=== OPENROUTER LLM TEST ===")
    
    try:
        from src.config.llm_config import LLMConfig
        
        llm = LLMConfig.get_llm()
        print(f"LLM Model: {llm.model}")
        
        response = llm.complete("TEST")
        content = response.text
        print(f"Content: '{content}' (length: {len(content)})")
        return content
        
    except Exception as e:
        print(f"LLM Exception: {e}")
        import traceback
        traceback.print_exc()
        
    return None

def main():
    """Run comparison test."""
    print("MINIMAL API DEBUG TEST")
    print("=====================")
    
    # Test both approaches with identical prompts
    direct_result = test_direct_api_minimal()
    llm_result = test_openrouter_llm_minimal()
    
    # Compare results
    print("\n=== COMPARISON ===")
    print(f"Direct API: '{direct_result}' (empty: {not direct_result})")
    print(f"OpenRouterLLM: '{llm_result}' (empty: {not llm_result})")
    
    if direct_result and llm_result:
        if direct_result.strip() == llm_result.strip():
            print("✅ Results are IDENTICAL")
        else:
            print("❌ Results are DIFFERENT")
    else:
        print("❌ One or both methods failed")
        
    # Determine root cause
    if not direct_result and llm_result:
        print("\n🔍 ROOT CAUSE: Direct API returns empty, LLM works")
        print("   Likely cause: Response parsing or API format issue")
    elif direct_result and not llm_result:
        print("\n🔍 ROOT CAUSE: LLM fails, Direct API works")  
        print("   Likely cause: LLM implementation issue")
    elif not direct_result and not llm_result:
        print("\n🔍 ROOT CAUSE: Both methods fail")
        print("   Likely cause: Authentication or model availability issue")
    else:
        print("\n✅ Both methods working correctly")

if __name__ == "__main__":
    main()
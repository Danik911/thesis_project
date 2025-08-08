#!/usr/bin/env python3
"""
Compare direct API calls vs OpenRouterLLM implementation for GPT-OSS-120B
to identify why direct calls return empty responses.
"""

import os
import sys
import json
import requests
import traceback
from datetime import datetime

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment
os.environ['OPENROUTER_API_KEY'] = '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'
os.environ['LLM_PROVIDER'] = 'openrouter'

def test_direct_api():
    """Test direct API call to OpenRouter."""
    print("\n" + "="*60)
    print("DIRECT API CALL TEST")
    print("="*60)
    
    api_key = os.environ['OPENROUTER_API_KEY']
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "GAMP-5 Test Generation"
    }
    
    data = {
        "model": "openai/gpt-oss-120b",
        "messages": [{"role": "user", "content": "Say 'TEST RESPONSE'"}],
        "temperature": 0.1,
        "max_tokens": 50
    }
    
    print(f"URL: https://openrouter.ai/api/v1/chat/completions")
    print(f"Headers: {headers}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Full Response JSON: {json.dumps(result, indent=2)}")
            
            # Extract content multiple ways
            try:
                content = result["choices"][0]["message"]["content"]
                print(f"Content: '{content}' (length: {len(content) if content else 0})")
                
                # Check for harmony format
                if hasattr(result["choices"][0]["message"], "channels"):
                    print("Harmony format detected - has channels")
                else:
                    print("Standard format - no channels detected")
                    
                return content
                
            except Exception as e:
                print(f"Content extraction error: {e}")
                print(f"Message structure: {result.get('choices', [{}])[0].get('message', {})}")
                
        else:
            print(f"API Error: {response.text[:500]}")
            
    except Exception as e:
        print(f"Request failed: {e}")
        traceback.print_exc()
        
    return None

def test_openrouter_llm():
    """Test OpenRouterLLM implementation."""
    print("\n" + "="*60)
    print("OPENROUTER LLM CLASS TEST")
    print("="*60)
    
    try:
        from src.config.llm_config import LLMConfig
        
        llm = LLMConfig.get_llm()
        print(f"LLM Model: {llm.model}")
        print(f"LLM Type: {type(llm)}")
        
        response = llm.complete("Say 'TEST RESPONSE'")
        print(f"Response Type: {type(response)}")
        print(f"Response Text: '{response.text}' (length: {len(response.text) if response.text else 0})")
        
        if hasattr(response, 'raw'):
            print(f"Raw Response: {json.dumps(response.raw, indent=2)}")
            
        return response.text
        
    except Exception as e:
        print(f"LLMConfig test failed: {e}")
        traceback.print_exc()
        
    return None

def detailed_response_analysis():
    """Perform detailed analysis of response differences."""
    print("\n" + "="*60)
    print("DETAILED RESPONSE ANALYSIS")  
    print("="*60)
    
    # Test with more complex prompt to see if harmony format is involved
    complex_prompt = "Analyze this request: What is 2+2? Provide reasoning."
    
    print(f"Testing with complex prompt: '{complex_prompt}'")
    
    # Direct API with complex prompt
    api_key = os.environ['OPENROUTER_API_KEY']
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000", 
        "X-Title": "GAMP-5 Test Generation"
    }
    
    data = {
        "model": "openai/gpt-oss-120b",
        "messages": [{"role": "user", "content": complex_prompt}],
        "temperature": 0.1,
        "max_tokens": 200
    }
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print("DIRECT API COMPLEX RESPONSE:")
            print(json.dumps(result, indent=2))
            
            # Try to find any content in different places
            message = result.get("choices", [{}])[0].get("message", {})
            content = message.get("content", "")
            
            # Check for harmony format fields
            if "channels" in message:
                print("Found harmony channels!")
                channels = message["channels"]
                for channel_name, channel_content in channels.items():
                    print(f"Channel '{channel_name}': {channel_content}")
                    
            print(f"Standard content field: '{content}'")
            
        else:
            print(f"Direct API failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Complex analysis failed: {e}")
        traceback.print_exc()

def main():
    """Run comprehensive comparison."""
    print("GPT-OSS-120B Empty Response Debug")
    print(f"Time: {datetime.now().isoformat()}")
    
    # Test both approaches
    direct_result = test_direct_api()
    llm_result = test_openrouter_llm()
    
    # Detailed analysis
    detailed_response_analysis()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    print(f"Direct API Result: '{direct_result}' (empty: {not direct_result})")
    print(f"LLM Class Result: '{llm_result}' (empty: {not llm_result})")
    
    if direct_result == llm_result:
        print("✅ Both methods return identical results")
    else:
        print("❌ Methods return different results - issue identified")
        print(f"Direct API length: {len(direct_result) if direct_result else 0}")
        print(f"LLM Class length: {len(llm_result) if llm_result else 0}")

if __name__ == "__main__":
    main()
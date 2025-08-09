#!/usr/bin/env python3
"""
Test direct OpenAI API call to debug timeout issues.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

def test_openai_direct():
    """Test direct OpenAI API call."""
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not found")
        return False
    
    print("Testing OpenAI API directly...")
    print(f"API Key present: {bool(api_key)}")
    
    try:
        client = OpenAI(api_key=api_key)
        
        # Simple test prompt
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a test generator."},
                {"role": "user", "content": "Generate a simple JSON with one test: {\"test\": \"example\"}"}
            ],
            max_tokens=100,
            temperature=0.1
        )
        
        result = response.choices[0].message.content
        print(f"Response: {result}")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_openai_direct()
    print(f"\nResult: {'SUCCESS' if success else 'FAILED'}")
"""Test o3 model with correct parameters."""
import asyncio
import os
from dotenv import load_dotenv
from llama_index.llms.openai import OpenAI

# Load environment variables
load_dotenv()

async def test_o3():
    # Test with correct parameters for o3
    llm = OpenAI(
        model="o3-2025-04-16",
        temperature=0.1,
        max_completion_tokens=100  # o3 requires this instead of max_tokens
    )
    
    try:
        response = await llm.acomplete("Generate a JSON object with one field 'status' set to 'success'")
        print(f"SUCCESS: o3 response: {response.text}")
        return True
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_o3())
    print(f"\nTest {'PASSED' if success else 'FAILED'}")
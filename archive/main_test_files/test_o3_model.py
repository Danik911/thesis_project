"""Quick test to verify o3 model availability."""
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()

try:
    # Test o3 model
    response = client.chat.completions.create(
        model="o3-2025-04-16",
        messages=[{"role": "user", "content": "Say 'Model works!'"}],
        max_tokens=10
    )
    print(f"SUCCESS: o3 model response: {response.choices[0].message.content}")
except Exception as e:
    print(f"ERROR with o3 model: {type(e).__name__}: {e}")

try:
    # Test o1 model as fallback
    response = client.chat.completions.create(
        model="o1-2025-04-16",
        messages=[{"role": "user", "content": "Say 'Model works!'"}],
        max_tokens=10
    )
    print(f"SUCCESS: o1 model response: {response.choices[0].message.content}")
except Exception as e:
    print(f"ERROR with o1 model: {type(e).__name__}: {e}")

# List available models
print("\nChecking available models...")
try:
    models = client.models.list()
    o_models = [m.id for m in models if m.id.startswith(("o1", "o3"))]
    print(f"Available o1/o3 models: {o_models}")
except Exception as e:
    print(f"Could not list models: {e}")

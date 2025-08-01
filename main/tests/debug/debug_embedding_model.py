#!/usr/bin/env uv run python
"""
Debug embedding model configuration and dimensions.
"""
import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "main"))

from src.agents.parallel.context_provider import ContextProviderAgent


async def debug_embedding_model():
    """Debug embedding model configuration."""
    print("🔍 Embedding Model Debug")
    print("=" * 30)

    try:
        # Initialize agent
        print("1️⃣ Testing default embedding model...")
        agent_default = ContextProviderAgent(enable_phoenix=True, verbose=True)
        print(f"   Model name: {agent_default.embedding_model_name}")

        # Test embedding dimensions
        test_text = "FDA Part 11 scope and definitions"
        embedding = await asyncio.to_thread(
            agent_default.embedding_model.get_text_embedding,
            test_text
        )
        print(f"   Embedding dimensions: {len(embedding)}")
        print(f"   First few values: {embedding[:5]}")

        print("\n2️⃣ Testing specific embedding model...")
        agent_specific = ContextProviderAgent(
            embedding_model="text-embedding-3-small",
            enable_phoenix=True,
            verbose=True
        )
        print(f"   Model name: {agent_specific.embedding_model_name}")

        # Test embedding dimensions
        embedding2 = await asyncio.to_thread(
            agent_specific.embedding_model.get_text_embedding,
            test_text
        )
        print(f"   Embedding dimensions: {len(embedding2)}")
        print(f"   First few values: {embedding2[:5]}")

        # Check if they're the same
        print("\n3️⃣ Comparison:")
        print(f"   Same dimensions: {len(embedding) == len(embedding2)}")
        print(f"   Same values: {embedding[:5] == embedding2[:5]}")

        # Test other OpenAI models
        print("\n4️⃣ Testing different OpenAI embedding models:")
        models = ["text-embedding-3-small", "text-embedding-3-large", "text-embedding-ada-002"]

        for model_name in models:
            try:
                test_agent = ContextProviderAgent(
                    embedding_model=model_name,
                    enable_phoenix=True
                )
                test_embedding = await asyncio.to_thread(
                    test_agent.embedding_model.get_text_embedding,
                    "test"
                )
                print(f"   {model_name}: {len(test_embedding)} dimensions")
            except Exception as e:
                print(f"   {model_name}: Error - {e}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_embedding_model())

#!/usr/bin/env python3
"""
Debug script to test context provider search operations.
"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
env_path = project_root / ".env"
load_dotenv(env_path)

from main.src.agents.parallel.context_provider import create_context_provider_agent


async def debug_search():
    """Debug the search functionality."""
    print("🔍 Debugging Context Provider Search Operations")
    print("=" * 50)
    
    # Initialize agent
    agent = create_context_provider_agent(verbose=True, enable_phoenix=False)
    
    # Test direct search method
    try:
        print("1️⃣ Testing direct search method...")
        
        # First ensure we have some documents
        collections_info = {}
        for collection_name in ["regulatory", "gamp5", "sops", "best_practices"]:
            try:
                collection = agent.chroma_client.get_collection(collection_name)
                count = collection.count()
                collections_info[collection_name] = count
                print(f"   Collection '{collection_name}': {count} documents")
            except Exception as e:
                collections_info[collection_name] = f"Error: {e}"
                print(f"   Collection '{collection_name}': Error - {e}")
        
        print()
        
        # Test search if we have documents
        if any(isinstance(count, int) and count > 0 for count in collections_info.values()):
            print("2️⃣ Testing search operations...")
            
            results = await agent._search_documents(
                query="electronic records FDA Part 11",
                collections=["regulatory"],
                max_results=5,
                metadata_filter={}
            )
            
            print(f"   Search returned {len(results)} results")
            for i, result in enumerate(results[:2]):  # Show first 2 results
                print(f"   Result {i+1}:")
                print(f"     Content preview: {result.text[:100]}...")
                print(f"     Score: {result.score}")
                print(f"     Metadata: {result.metadata}")
            
        else:
            print("❌ No documents found in any collection")
            
    except Exception as e:
        print(f"❌ Search test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_search())
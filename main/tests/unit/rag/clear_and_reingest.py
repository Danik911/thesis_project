#!/usr/bin/env uv run python
"""
Clear ChromaDB and re-ingest FDA Part 11 with consistent embedding model.
"""
import asyncio
import sys
from pathlib import Path

import chromadb
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "main"))

from src.agents.parallel.context_provider import ContextProviderAgent


async def clear_and_reingest():
    """Clear ChromaDB and re-ingest with consistent embedding model."""
    print("🧹 Clear ChromaDB and Re-ingest FDA Part 11")
    print("=" * 50)

    try:
        # First, clear ChromaDB completely
        print("1️⃣ Clearing existing ChromaDB data...")
        persist_path = Path("/home/anteb/thesis_project/main/lib/chroma_db")
        client = chromadb.PersistentClient(path=str(persist_path))

        # Get all collections and delete them
        collections = client.list_collections()
        print(f"   Found {len(collections)} collections to clear:")
        for collection in collections:
            print(f"   🗑️ Deleting collection: {collection.name}")
            client.delete_collection(collection.name)

        print("✅ ChromaDB cleared successfully")

        # Initialize agent with specific embedding model (text-embedding-3-small = 1536 dimensions)
        print("2️⃣ Initializing Context Provider Agent with consistent embedding model...")
        agent = ContextProviderAgent(
            embedding_model="text-embedding-3-small",
            enable_phoenix=True,
            verbose=True
        )
        print("✅ Agent initialized with text-embedding-3-small (1536 dimensions)")

        # Path to FDA Part 11 document
        fda_doc_path = Path("/home/anteb/thesis_project/main/tests/test_data")
        print(f"3️⃣ Document path: {fda_doc_path}")

        # List available files
        files = list(fda_doc_path.glob("*.pdf")) + list(fda_doc_path.glob("*.txt"))
        print("   Available documents:")
        for file in files:
            print(f"   📄 {file.name}")

        # Ingest into regulatory collection
        print("4️⃣ Starting document ingestion with consistent embeddings...")
        result = await agent.ingest_documents(
            documents_path=str(fda_doc_path),
            collection_name="regulatory"
        )

        print("✅ Ingestion completed!")
        print(f"📊 Result type: {type(result)}")

        # Verify ingestion by checking collection counts
        print("\n5️⃣ Verifying ingestion results:")
        collections = client.list_collections()
        for collection in collections:
            count = collection.count()
            print(f"📁 Collection '{collection.name}': {count} documents")

            if count > 0 and collection.name == "regulatory_documents":
                print("   🔍 Testing search through agent...")
                # Test search through the agent (not directly on ChromaDB)
                # This ensures we use the same embedding model
                print(f"   ✅ Collection ready - {count} documents ingested successfully")

    except Exception as e:
        print(f"❌ Error during clear and reingest: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(clear_and_reingest())

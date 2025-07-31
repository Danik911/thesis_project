#!/usr/bin/env python3
"""
Debug ChromaDB state to understand what collections and documents exist.
"""
import sys
from pathlib import Path

import chromadb

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "main"))

def debug_chromadb_state():
    """Debug ChromaDB collections and documents."""
    print("🔍 ChromaDB State Debug")
    print("=" * 40)

    try:
        # Connect to ChromaDB
        chroma_client = chromadb.HttpClient(host="localhost", port=8000)
        print("✅ Connected to ChromaDB at localhost:8000")

        # List all collections
        collections = chroma_client.list_collections()
        print(f"\n📚 Found {len(collections)} collections:")

        if not collections:
            print("   ❌ No collections found!")
            print("   💡 You may need to ingest documents first")
            return

        for collection in collections:
            print(f"\n📁 Collection: {collection.name}")
            try:
                # Get collection details
                count = collection.count()
                print(f"   📊 Document count: {count}")

                if count > 0:
                    # Get a few sample documents
                    sample_results = collection.peek(limit=3)
                    print("   📄 Sample documents:")

                    if sample_results and "ids" in sample_results:
                        for i, doc_id in enumerate(sample_results["ids"][:3]):
                            print(f"      🔖 ID: {doc_id}")

                            # Show metadata if available
                            if "metadatas" in sample_results and i < len(sample_results["metadatas"]):
                                metadata = sample_results["metadatas"][i] or {}
                                print(f"         📋 Metadata: {metadata}")

                            # Show document content preview
                            if "documents" in sample_results and i < len(sample_results["documents"]):
                                content = sample_results["documents"][i] or ""
                                preview = content[:150] + "..." if len(content) > 150 else content
                                print(f"         📖 Content: {preview}")

                    # Test a simple query
                    print("   🔍 Testing query 'FDA Part 11'...")
                    try:
                        query_results = collection.query(
                            query_texts=["FDA Part 11"],
                            n_results=2
                        )
                        if query_results and "ids" in query_results:
                            print(f"      ✅ Found {len(query_results['ids'][0])} matching documents")
                            for doc_id in query_results["ids"][0]:
                                print(f"         📄 {doc_id}")
                        else:
                            print("      ❌ No documents found for 'FDA Part 11'")
                    except Exception as query_error:
                        print(f"      ❌ Query error: {query_error}")

            except Exception as collection_error:
                print(f"   ❌ Error accessing collection: {collection_error}")

    except Exception as e:
        print(f"❌ ChromaDB connection error: {e}")
        print("💡 Make sure ChromaDB is running on localhost:8000")

        # Try alternate connection method
        print("\n🔄 Trying persistent client...")
        try:
            persist_path = Path("/home/anteb/thesis_project/main/lib/chroma_db")
            print(f"📁 Checking path: {persist_path}")

            if persist_path.exists():
                chroma_client = chromadb.PersistentClient(path=str(persist_path))
                collections = chroma_client.list_collections()
                print(f"✅ Found {len(collections)} collections in persistent storage")

                for collection in collections:
                    print(f"   📁 {collection.name}: {collection.count()} documents")
            else:
                print(f"❌ Persistent path does not exist: {persist_path}")

        except Exception as persist_error:
            print(f"❌ Persistent client error: {persist_error}")

if __name__ == "__main__":
    debug_chromadb_state()

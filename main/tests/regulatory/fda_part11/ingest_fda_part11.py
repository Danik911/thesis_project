#!/usr/bin/env python3
"""
Ingest FDA Part 11 document into ChromaDB for testing.
"""
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "main"))

from src.agents.parallel.context_provider import ContextProviderAgent

async def ingest_fda_document():
    """Ingest FDA Part 11 document into ChromaDB."""
    print("📥 Ingesting FDA Part 11 Document")
    print("=" * 40)
    
    try:
        # Initialize agent
        print("1️⃣ Initializing Context Provider Agent...")
        agent = ContextProviderAgent(enable_phoenix=True, verbose=True)
        print("✅ Agent initialized successfully")
        
        # Path to FDA Part 11 document
        fda_doc_path = Path("/home/anteb/thesis_project/main/tests/test_data")
        print(f"2️⃣ Document path: {fda_doc_path}")
        
        if not fda_doc_path.exists():
            print(f"❌ Document path does not exist: {fda_doc_path}")
            return
        
        # List files in the directory
        files = list(fda_doc_path.glob("*.md"))
        print(f"📄 Found {len(files)} markdown files:")
        for file in files:
            print(f"   📄 {file.name}")
        
        # Ingest into regulatory collection (valid collection name)
        print("3️⃣ Starting document ingestion...")
        result = await agent.ingest_documents(
            documents_path=str(fda_doc_path),
            collection_name="regulatory"
        )
        
        print(f"✅ Ingestion completed!")
        print(f"📊 Result: {result}")
        
        # Verify ingestion by checking collection count
        print("4️⃣ Verifying ingestion...")
        chroma_client = agent.chroma_client
        collections = chroma_client.list_collections()
        
        for collection in collections:
            count = collection.count()
            print(f"📁 Collection '{collection.name}': {count} documents")
            
            if count > 0 and collection.name == "regulatory":
                print("   🔍 Testing search...")
                try:
                    # Test search
                    sample_query = collection.query(
                        query_texts=["FDA Part 11"],
                        n_results=3
                    )
                    if sample_query and 'ids' in sample_query:
                        print(f"   ✅ Found {len(sample_query['ids'][0])} documents for 'FDA Part 11'")
                        for doc_id in sample_query['ids'][0]:
                            print(f"      📄 {doc_id}")
                    else:
                        print("   ❌ No search results")
                except Exception as search_error:
                    print(f"   ❌ Search error: {search_error}")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Run ingestion
    asyncio.run(ingest_fda_document())
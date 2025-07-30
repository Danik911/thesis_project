#!/usr/bin/env python3
"""
Debug ChromaDB state and collection contents.
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path  
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
env_path = project_root / ".env"
load_dotenv(env_path)

import chromadb
from main.src.agents.parallel.context_provider import create_context_provider_agent


async def debug_chromadb():
    """Debug ChromaDB state."""
    print("🔍 Debugging ChromaDB State")
    print("=" * 30)
    
    # Initialize agent
    agent = create_context_provider_agent(verbose=True, enable_phoenix=False)
    
    print(f"ChromaDB client type: {type(agent.chroma_client)}")
    print(f"ChromaDB persist directory: {getattr(agent.chroma_client, '_path', 'Not available')}")
    print()
    
    # List all collections
    try:
        collections = agent.chroma_client.list_collections()
        print(f"📂 Available collections ({len(collections)}):")
        for collection in collections:
            print(f"   • {collection.name} (id: {collection.id})")
            
            # Get collection details
            try:
                coll = agent.chroma_client.get_collection(collection.name)
                count = coll.count()
                print(f"     - Document count: {count}")
                
                if count > 0:
                    # Get a sample document
                    result = coll.get(limit=1, include=['documents', 'metadatas'])
                    if result['documents']:
                        doc_preview = result['documents'][0][:100] + "..." if len(result['documents'][0]) > 100 else result['documents'][0]
                        print(f"     - Sample doc: {doc_preview}")
                        print(f"     - Sample metadata: {result.get('metadatas', [{}])[0]}")
                        
            except Exception as e:
                print(f"     - Error getting details: {e}")
        
        print()
        
        # Test ingestion directly
        print("🔄 Testing fresh document ingestion...")
        fda_doc_path = Path("/home/anteb/thesis_project/main/tests/test_data/FDA Part-11--Electronic-Records--Electronic-Signatures---Scope-and-Application-(PDF).md")
        
        if fda_doc_path.exists():
            stats = await agent.ingest_documents(
                documents_path=str(fda_doc_path),
                collection_name="regulatory",
                force_reprocess=True
            )
            print(f"✅ Ingestion completed: {stats}")
            
            # Check collection again
            try:
                regulatory_coll = agent.chroma_client.get_collection("regulatory")
                count = regulatory_coll.count()
                print(f"📊 Regulatory collection now has {count} documents")
                
                if count > 0:
                    # Get first document
                    result = regulatory_coll.get(limit=1, include=['documents', 'metadatas'])
                    if result['documents']:
                        doc_preview = result['documents'][0][:200] + "..." if len(result['documents'][0]) > 200 else result['documents'][0]
                        print(f"📄 Sample content: {doc_preview}")
                        
            except Exception as e:
                print(f"❌ Error checking regulatory collection: {e}")
        else:
            print("❌ FDA document not found")
            
    except Exception as e:
        print(f"❌ Error listing collections: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_chromadb())
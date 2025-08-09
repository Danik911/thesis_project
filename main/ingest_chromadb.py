#!/usr/bin/env python3
"""
ChromaDB Document Ingestion for Context Agent
Ingests GAMP-5 and FDA regulatory documents into ChromaDB for context retrieval
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the main directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "."))

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
import chromadb
from chromadb.config import Settings as ChromaSettings

def ingest_documents():
    """Ingest regulatory documents into ChromaDB."""
    
    print("\n" + "="*80)
    print("ChromaDB Document Ingestion for Context Agent")
    print("="*80)
    
    # Document paths
    doc_paths = [
        r"C:\Users\anteb\Desktop\Courses\Projects\thesis_project\main\tests\test_data\ISPE - GAMP 5_ A Risk-Based Approach to Compliant GxP Computerized_short.md",
        r"C:\Users\anteb\Desktop\Courses\Projects\thesis_project\main\tests\test_data\FDA Part-11--Electronic-Records--Electronic-Signatures---Scope-and-Application-(PDF).md",
        r"C:\Users\anteb\Desktop\Courses\Projects\thesis_project\main\tests\test_data\ISPE Baseline® Guide Commissioning and Qualification_short.md"
    ]
    
    # Verify all documents exist
    print("\n1. Verifying documents...")
    for path in doc_paths:
        if os.path.exists(path):
            size = os.path.getsize(path) / 1024  # KB
            print(f"   FOUND: {os.path.basename(path)} ({size:.1f} KB)")
        else:
            print(f"   MISSING: {path}")
            return False
    
    # Initialize ChromaDB
    print("\n2. Initializing ChromaDB...")
    chroma_path = "./chroma_db"
    os.makedirs(chroma_path, exist_ok=True)
    
    chroma_client = chromadb.PersistentClient(
        path=chroma_path,
        settings=ChromaSettings(
            anonymized_telemetry=False,
            allow_reset=True
        )
    )
    
    # Delete existing collection if it exists
    try:
        chroma_client.delete_collection("pharmaceutical_regulations")
        print("   Deleted existing collection")
    except:
        pass
    
    # Create new collection
    collection = chroma_client.create_collection(
        name="pharmaceutical_regulations",
        metadata={"description": "GAMP-5 and FDA regulatory documents"}
    )
    print(f"   Created collection: pharmaceutical_regulations")
    
    # Initialize embeddings
    print("\n3. Initializing OpenAI embeddings...")
    embed_model = OpenAIEmbedding(
        model="text-embedding-3-small",
        api_key=os.getenv("OPENAI_API_KEY")
    )
    Settings.embed_model = embed_model
    
    # Create vector store
    vector_store = ChromaVectorStore(
        chroma_collection=collection
    )
    storage_context = StorageContext.from_defaults(
        vector_store=vector_store
    )
    
    # Load and index documents
    print("\n4. Loading and indexing documents...")
    documents = []
    for path in doc_paths:
        print(f"   Loading: {os.path.basename(path)}")
        reader = SimpleDirectoryReader(
            input_files=[path]
        )
        docs = reader.load_data()
        documents.extend(docs)
        print(f"      Loaded {len(docs)} document chunks")
    
    print(f"\n   Total documents to index: {len(documents)}")
    
    # Create index
    print("\n5. Creating vector index...")
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        show_progress=True
    )
    
    # Test retrieval
    print("\n6. Testing retrieval...")
    query_engine = index.as_query_engine()
    test_query = "What are the GAMP-5 categories for computerized systems?"
    response = query_engine.query(test_query)
    
    print(f"   Test query: {test_query}")
    print(f"   Response preview: {str(response)[:200]}...")
    
    # Verify collection stats
    print("\n7. Collection Statistics:")
    collection_data = collection.get()
    print(f"   Total embeddings: {len(collection_data['ids'])}")
    print(f"   Metadata keys: {list(collection_data['metadatas'][0].keys()) if collection_data['metadatas'] else 'None'}")
    
    print("\n" + "="*80)
    print("SUCCESS: ChromaDB ingestion complete!")
    print(f"Collection 'pharmaceutical_regulations' ready with {len(collection_data['ids'])} embeddings")
    print("="*80)
    
    return True

if __name__ == "__main__":
    success = ingest_documents()
    sys.exit(0 if success else 1)
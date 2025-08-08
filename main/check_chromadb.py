#!/usr/bin/env python3
"""
Check ChromaDB status for end-to-end testing
"""
import os
import sys
from pathlib import Path

# Load environment variables from .env file
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                # Remove quotes if present
                value = value.strip('"\'')
                os.environ[key] = value

# Verify API key is loaded
api_key = os.getenv('OPENROUTER_API_KEY')
if not api_key:
    print("ERROR: OPENROUTER_API_KEY not found in environment!")
    sys.exit(1)

print(f"SUCCESS: API Key loaded: {api_key[:20]}...")

# Check ChromaDB status directly
try:
    import chromadb
    
    # Connect to ChromaDB
    client = chromadb.PersistentClient(path="./lib/chroma_db")
    collections = client.list_collections()
    
    print(f"SUCCESS: Found {len(collections)} ChromaDB collections:")
    
    total_docs = 0
    for collection in collections:
        count = collection.count()
        total_docs += count
        print(f"  - {collection.name}: {count} documents")
    
    if total_docs == 0:
        print("WARNING: No documents found in ChromaDB - workflow will fail!")
        print("You need to run document embedding before testing.")
    else:
        print(f"SUCCESS: Total {total_docs} documents available for testing")
        
    # Test a simple query on the first collection
    if collections and collections[0].count() > 0:
        test_collection = collections[0]
        try:
            results = test_collection.query(
                query_texts=["GAMP-5 categories"],
                n_results=2
            )
            if results['documents'] and results['documents'][0]:
                print("Sample document content:")
                for i, doc in enumerate(results['documents'][0][:1]):
                    print(f"  Sample: {doc[:100]}...")
        except Exception as e:
            print(f"WARNING: Query test failed: {e}")
        
except Exception as e:
    print(f'ERROR: ChromaDB check failed: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
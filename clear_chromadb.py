#!/usr/bin/env python3
"""
Clear ChromaDB database to fix dimension conflicts.
Based on RAG_SYSTEM_ISSUES.md solution.
"""

import os
import shutil
import sys
from pathlib import Path

def clear_chromadb():
    """Clear existing ChromaDB database to resolve dimension conflicts."""
    
    # ChromaDB database path
    chroma_db_path = Path("main/lib/chroma_db")
    
    if chroma_db_path.exists():
        print(f"🗑️  Clearing corrupted ChromaDB database at: {chroma_db_path}")
        
        try:
            # Remove the entire directory
            shutil.rmtree(chroma_db_path)
            print(f"✅ Successfully cleared ChromaDB database")
            
            # Create empty directory for next ingestion
            chroma_db_path.mkdir(parents=True, exist_ok=True)
            print(f"📁 Created fresh ChromaDB directory")
            
        except Exception as e:
            print(f"❌ Error clearing ChromaDB: {e}")
            sys.exit(1)
    else:
        print(f"ℹ️  ChromaDB database not found at: {chroma_db_path}")
        print("   No clearing needed")

    # Also clear any embedding cache that might have mixed dimensions
    cache_files = [
        "main/lib/embedding_cache.pkl",
        "main/lib/ingestion_cache.json"
    ]
    
    for cache_file in cache_files:
        cache_path = Path(cache_file)
        if cache_path.exists():
            try:
                cache_path.unlink()
                print(f"🗑️  Cleared cache file: {cache_file}")
            except Exception as e:
                print(f"⚠️  Warning: Could not clear cache {cache_file}: {e}")
    
    print("\n✅ ChromaDB clearing complete!")
    print("💡 Next steps:")
    print("   1. Ensure consistent embedding model configuration")
    print("   2. Re-ingest documents with text-embedding-3-small")
    print("   3. Test Phoenix observability")

if __name__ == "__main__":
    clear_chromadb()
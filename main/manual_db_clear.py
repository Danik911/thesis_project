"""
Manual ChromaDB database clearing script.
Run this to clear dimension conflicts before testing.
"""

import os
import shutil
from pathlib import Path

def main():
    print("🗑️  Manual ChromaDB Database Clearing")
    print("=" * 40)
    
    # Define paths
    base_path = Path(__file__).parent
    chroma_path = base_path / "lib" / "chroma_db"
    
    print(f"Working directory: {base_path}")
    print(f"ChromaDB path: {chroma_path}")
    
    # Clear ChromaDB
    if chroma_path.exists():
        print(f"\n🗑️  Removing ChromaDB directory...")
        try:
            # Remove all contents first
            for item in chroma_path.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                    print(f"   Removed directory: {item.name}")
                else:
                    item.unlink()
                    print(f"   Removed file: {item.name}")
            
            # Remove the directory itself
            chroma_path.rmdir()
            print("   ✅ ChromaDB directory removed")
            
            # Recreate empty directory
            chroma_path.mkdir(parents=True, exist_ok=True)
            print("   📁 Created fresh ChromaDB directory")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    else:
        print("   ℹ️  ChromaDB directory not found")
    
    # Clear cache files
    cache_files = [
        base_path / "lib" / "embedding_cache.pkl",
        base_path / "lib" / "ingestion_cache.json"
    ]
    
    print(f"\n🗑️  Clearing cache files...")
    for cache_file in cache_files:
        if cache_file.exists():
            try:
                cache_file.unlink()
                print(f"   ✅ Removed: {cache_file.name}")
            except Exception as e:
                print(f"   ⚠️  Could not remove {cache_file.name}: {e}")
        else:
            print(f"   ℹ️  Not found: {cache_file.name}")
    
    print(f"\n✅ Database clearing complete!")
    print(f"💡 Next steps:")
    print(f"   1. Set EMBEDDING_MODEL=text-embedding-3-small")
    print(f"   2. Run workflow tests")
    print(f"   3. Validate Phoenix observability")

if __name__ == "__main__":
    main()
"""
Clear ChromaDB database to fix dimension conflicts
"""
import shutil
from pathlib import Path

# Clear ChromaDB
chroma_path = Path("lib/chroma_db")
if chroma_path.exists():
    print(f"Clearing ChromaDB at {chroma_path}")
    shutil.rmtree(chroma_path)
    chroma_path.mkdir(parents=True, exist_ok=True)
    print("✅ ChromaDB cleared")
else:
    print("ChromaDB path not found")

# Clear caches
cache_files = ["lib/embedding_cache.pkl", "lib/ingestion_cache.json"]
for cache_file in cache_files:
    cache_path = Path(cache_file)
    if cache_path.exists():
        cache_path.unlink()
        print(f"✅ Cleared {cache_file}")

print("Database clearing complete!")

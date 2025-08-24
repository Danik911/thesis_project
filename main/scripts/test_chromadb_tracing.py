#!/usr/bin/env python3
"""
Test ChromaDB tracing to verify instrumentation is working and traces are being captured.
"""

import sys
import time
from pathlib import Path

# Fix Windows Unicode
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Initialize Phoenix first
from src.monitoring.phoenix_config import setup_phoenix

phoenix_manager = setup_phoenix()

# Now import ChromaDB and test
import chromadb


def test_chromadb_operations():
    """Test ChromaDB operations to generate traces."""

    print("Testing ChromaDB Tracing")
    print("=" * 50)

    # Create a client
    print("\n1. Creating ChromaDB client...")
    client = chromadb.Client()

    # Create a collection
    print("\n2. Creating test collection...")
    collection_name = f"test_tracing_{int(time.time())}"
    collection = client.create_collection(
        name=collection_name,
        metadata={"purpose": "trace_testing", "pharmaceutical": True}
    )
    print(f"   ✅ Created collection: {collection_name}")

    # Add some documents
    print("\n3. Adding documents...")
    documents = [
        "GAMP-5 Category 3 software testing",
        "Category 5 custom application validation",
        "Pharmaceutical compliance requirements"
    ]

    collection.add(
        documents=documents,
        ids=["doc1", "doc2", "doc3"],
        metadatas=[
            {"type": "gamp", "category": 3},
            {"type": "gamp", "category": 5},
            {"type": "compliance", "standard": "21CFR11"}
        ]
    )
    print(f"   ✅ Added {len(documents)} documents")

    # Query the collection
    print("\n4. Querying collection...")
    results = collection.query(
        query_texts=["GAMP validation requirements"],
        n_results=2
    )
    print(f"   ✅ Query returned {len(results['ids'][0])} results")

    # Delete a document
    print("\n5. Deleting document...")
    collection.delete(ids=["doc3"])
    print("   ✅ Deleted document")

    # Clean up
    print("\n6. Cleaning up...")
    client.delete_collection(collection_name)
    print("   ✅ Deleted collection")

    print("\n" + "=" * 50)
    print("ChromaDB operations complete!")
    print("\nCheck Phoenix UI at http://localhost:6006 for traces")
    print("Look for spans with names like:")
    print("  - chromadb.query")
    print("  - chromadb.add")
    print("  - chromadb.delete")

    # Wait a moment for traces to be sent
    print("\nWaiting 5 seconds for traces to be sent...")
    time.sleep(5)

    # Try to export and check
    try:
        import phoenix as px
        client = px.Client()

        # Get recent spans
        print("\nChecking for ChromaDB spans...")
        all_spans = client.get_spans_dataframe()

        if all_spans is not None and not all_spans.empty:
            # Check for ChromaDB spans
            chromadb_spans = all_spans[
                all_spans["name"].str.contains("chromadb", case=False, na=False)
            ]

            if not chromadb_spans.empty:
                print(f"✅ Found {len(chromadb_spans)} ChromaDB spans!")
                print("\nChromaDB span names:")
                for name in chromadb_spans["name"].unique():
                    print(f"  - {name}")
            else:
                print("❌ No ChromaDB spans found in export")
                print("\nAll span names found:")
                for name in all_spans["name"].unique()[:10]:
                    print(f"  - {name}")
        else:
            print("❌ No spans found in Phoenix")

    except Exception as e:
        print(f"❌ Error checking spans: {e}")


if __name__ == "__main__":
    test_chromadb_operations()

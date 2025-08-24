#!/usr/bin/env python3
"""
Test script to verify custom span exporter captures ChromaDB operations.
"""

import json
import sys
from pathlib import Path

# Fix Windows Unicode
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import time

import chromadb
from src.monitoring.phoenix_config import setup_phoenix, shutdown_phoenix


def test_chromadb_span_capture():
    """Test that ChromaDB operations are captured by our custom exporter."""

    print("Testing Custom Span Export for ChromaDB")
    print("=" * 50)

    # 1. Setup Phoenix with custom exporter
    print("\n1. Setting up Phoenix with custom span exporter...")
    phoenix_manager = setup_phoenix()

    # 2. Initialize ChromaDB
    print("\n2. Creating ChromaDB client...")
    try:
        client = chromadb.Client()
        print("   ✅ ChromaDB client created")
    except Exception as e:
        print(f"   ❌ ChromaDB client creation failed: {e}")
        return

    # 3. Perform ChromaDB operations
    print("\n3. Performing ChromaDB operations...")

    # Create a test collection
    collection_name = f"test_span_export_{int(time.time())}"

    try:
        # Create collection
        print(f"   - Creating collection: {collection_name}")
        collection = client.create_collection(
            name=collection_name,
            metadata={"purpose": "span_export_test", "pharmaceutical": True}
        )

        # Add documents
        print("   - Adding test documents...")
        documents = [
            "GAMP-5 Category 3 software testing requirements",
            "Category 5 custom application validation procedures",
            "Pharmaceutical compliance and regulatory standards"
        ]
        ids = [f"doc_{i}" for i in range(len(documents))]
        metadatas = [{"type": "test", "index": i} for i in range(len(documents))]

        collection.add(
            documents=documents,
            ids=ids,
            metadatas=metadatas
        )

        # Query documents
        print("   - Querying documents...")
        results = collection.query(
            query_texts=["GAMP-5 pharmaceutical validation"],
            n_results=2
        )
        print(f"   - Found {len(results['documents'][0])} results")

        # Delete collection
        print("   - Cleaning up collection...")
        client.delete_collection(collection_name)

        print("   ✅ ChromaDB operations completed")

    except Exception as e:
        print(f"   ❌ ChromaDB operations failed: {e}")
        import traceback
        traceback.print_exc()

    # 4. Shutdown Phoenix to flush spans
    print("\n4. Shutting down Phoenix to flush spans...")
    shutdown_phoenix(timeout_seconds=10)

    # 5. Check for captured spans
    print("\n5. Checking captured spans...")

    # Find the latest trace files
    trace_dir = Path("logs/traces")
    if trace_dir.exists():
        trace_files = list(trace_dir.glob("all_spans_*.jsonl"))
        chromadb_files = list(trace_dir.glob("chromadb_spans_*.jsonl"))

        if trace_files:
            latest_trace = max(trace_files, key=lambda f: f.stat().st_mtime)
            print(f"\n   Latest trace file: {latest_trace}")

            # Count spans
            total_spans = 0
            chromadb_spans = 0
            span_types = {}

            with open(latest_trace, encoding="utf-8") as f:
                for line in f:
                    try:
                        span = json.loads(line)
                        total_spans += 1

                        # Check for ChromaDB spans
                        span_name = span.get("name", "").lower()
                        if any(keyword in span_name for keyword in ["chromadb", "vector", "collection"]):
                            chromadb_spans += 1

                        # Track span types
                        span_type = span.get("span_type", "unknown")
                        span_types[span_type] = span_types.get(span_type, 0) + 1

                    except:
                        pass

            print("\n   Span Analysis:")
            print(f"   - Total spans captured: {total_spans}")
            print(f"   - ChromaDB spans: {chromadb_spans}")
            print("\n   Span types:")
            for span_type, count in span_types.items():
                print(f"   - {span_type}: {count}")

        if chromadb_files:
            latest_chromadb = max(chromadb_files, key=lambda f: f.stat().st_mtime)
            print(f"\n   ChromaDB-specific file: {latest_chromadb}")

            # Show sample ChromaDB spans
            print("\n   Sample ChromaDB spans:")
            with open(latest_chromadb, encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if i >= 3:  # Show first 3
                        break
                    try:
                        span = json.loads(line)
                        print(f"\n   Span {i+1}:")
                        print(f"     - Name: {span.get('name')}")
                        print(f"     - Operation: {span.get('operation', 'N/A')}")
                        print(f"     - Duration: {span.get('duration_ns', 0) / 1_000_000:.2f} ms")
                        if "attributes" in span:
                            attrs = span["attributes"]
                            if "chromadb.query.result_count" in attrs:
                                print(f"     - Results: {attrs['chromadb.query.result_count']}")
                    except:
                        pass

        if chromadb_spans > 0:
            print("\n" + "=" * 50)
            print("✅ SUCCESS: ChromaDB spans are being captured!")
            print(f"   Found {chromadb_spans} ChromaDB operations in trace files")
        else:
            print("\n" + "=" * 50)
            print("❌ ISSUE: No ChromaDB spans found in trace files")
            print("   This might indicate the instrumentation is not working")
    else:
        print(f"   ❌ Trace directory not found: {trace_dir}")

    print("\n" + "=" * 50)
    print("Test complete!")


if __name__ == "__main__":
    test_chromadb_span_capture()

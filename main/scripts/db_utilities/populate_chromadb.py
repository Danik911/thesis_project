#!/usr/bin/env uv run python
"""
Populate ChromaDB with GAMP documentation for improved categorization.

This script ingests pharmaceutical compliance documentation into ChromaDB
to enhance the Context Provider's ability to provide regulatory context.
"""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
env_path = project_root / ".env"
load_dotenv(env_path)

# Verify OpenAI API key is loaded
if not os.getenv("OPENAI_API_KEY"):
    print("[ERROR] OPENAI_API_KEY not found in environment variables")
    print(f"[INFO] Attempted to load from: {env_path}")
    sys.exit(1)

from main.src.agents.parallel.context_provider import create_context_provider_agent


async def populate_chromadb():
    """Populate ChromaDB with GAMP documentation files."""
    print("Starting ChromaDB population with GAMP documentation...")

    # Create context provider agent
    context_provider = create_context_provider_agent(
        verbose=True,
        enable_phoenix=True,
        max_documents=50,
        quality_threshold=0.7
    )

    # Define documents to ingest
    documents = [
        {
            "path": r"C:\Users\anteb\Desktop\Courses\Projects\thesis_project\main\tests\test_data\ISPE - GAMP 5_ A Risk-Based Approach to Compliant GxP Computerized_short.md",
            "collection": "gamp5",
            "description": "ISPE GAMP 5 - Risk-Based Approach to GxP Computerized Systems"
        },
        {
            "path": r"C:\Users\anteb\Desktop\Courses\Projects\thesis_project\main\tests\test_data\ISPE Baseline® Guide Commissioning and Qualification_short.md",
            "collection": "gamp5",
            "description": "ISPE Baseline Guide - Commissioning and Qualification"
        },
        {
            "path": r"C:\Users\anteb\Desktop\Courses\Projects\thesis_project\main\tests\test_data\OQ_examples.md",
            "collection": "best_practices",
            "description": "Operational Qualification (OQ) Examples and Best Practices"
        }
    ]

    # Ingest each document
    for doc_info in documents:
        doc_path = Path(doc_info["path"])

        if not doc_path.exists():
            print(f"[ERROR] File not found: {doc_path}")
            continue

        print(f"\n[INFO] Ingesting: {doc_info['description']}")
        print(f"   Collection: {doc_info['collection']}")
        print(f"   File: {doc_path.name}")

        try:
            # Ingest document
            result = await context_provider.ingest_documents(
                documents_path=str(doc_path),
                collection_name=doc_info["collection"],
                force_reprocess=True  # Force reprocessing to ensure fresh ingestion
            )

            if result["status"] == "success":
                print(f"   [SUCCESS] {result['processed_documents']} documents, {result['processed_nodes']} chunks")
            else:
                print(f"   [WARNING] Status: {result['status']}")

        except Exception as e:
            print(f"   [ERROR] {e!s}")

    # Verify collection contents
    print("\n[INFO] Verifying ChromaDB collections:")
    for collection_name in ["gamp5", "regulatory", "sops", "best_practices"]:
        try:
            collection = context_provider.collections[collection_name]
            count = collection.count()
            print(f"   {collection_name}: {count} documents")
        except Exception as e:
            print(f"   {collection_name}: Error - {e!s}")

    print("\n[SUCCESS] ChromaDB population complete!")
    print("The Context Provider now has access to:")
    print("  - GAMP 5 risk-based approach guidance")
    print("  - ISPE commissioning and qualification baseline")
    print("  - OQ test examples and best practices")
    print("\nThis should improve categorization confidence by providing regulatory context.")


if __name__ == "__main__":
    # Run the population script
    asyncio.run(populate_chromadb())

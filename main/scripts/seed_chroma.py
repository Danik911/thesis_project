#!/usr/bin/env python3
"""
ChromaDB Seeding Script - Pharmaceutical Test Generation System

Purpose:
- Seed ChromaDB collections with pharmaceutical regulatory documents
- Idempotent operation (safe to re-run multiple times)
- ALCOA+ compliant audit logging
- Works in both local and Docker environments

Usage:
    Local:  python scripts/seed_chroma.py
    Docker: docker exec -it pharma-api-dev python scripts/seed_chroma.py

Collections:
- regulatory_documents: FDA, ISPE, ICH, ISO standards (5 documents)
- gamp5_documents: GAMP-5 specific guidance (subset of regulatory)
- best_practices: Industry methodologies (subset of regulatory)
- sop_documents: Standard Operating Procedures (future expansion)

NO FALLBACK LOGIC: Fails explicitly if any document missing or ingestion fails.
"""

import asyncio
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

# Add main module to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "main"))

from src.agents.parallel.context_provider import create_context_provider_agent


async def seed_all_collections(force_reseed: bool = False) -> None:
    """
    Seed all ChromaDB collections with pharmaceutical corpus.

    Args:
        force_reseed: If True, clear collections before re-seeding

    Raises:
        FileNotFoundError: If corpus documents missing
        RuntimeError: If ingestion fails
    """
    print("=" * 80)
    print("ChromaDB Seeding Script - Pharmaceutical Test Generation System")
    print("=" * 80)
    print(f"Started: {datetime.now(UTC).isoformat()}")
    print(f"Force reseed: {force_reseed}")
    print()

    # Validate environment
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "CRITICAL: OPENAI_API_KEY not set in environment.\n"
            "Required for generating document embeddings."
        )

    # Create context provider agent
    print("📊 Initializing Context Provider Agent...")
    agent = create_context_provider_agent(verbose=True)
    print("✓ Agent initialized")
    print()

    # Define collection mappings
    # Map: (source_path, collection_name, description)
    collection_mappings = [
        (
            "main/docs/regulatory_guides",
            "regulatory_documents",
            "FDA, ISPE, ICH, ISO regulatory standards"
        ),
        (
            "main/docs/regulatory_guides",  # Same source for GAMP-5 subset
            "gamp5_documents",
            "GAMP-5 validation and testing guidelines"
        ),
        (
            "main/docs/regulatory_guides",  # Same source for best practices
            "best_practices",
            "Industry best practices and methodologies"
        )
    ]

    # Ingestion summary
    total_documents = 0
    total_chunks = 0
    failed_collections = []

    # Seed each collection
    for source_path, collection_name, description in collection_mappings:
        print("-" * 80)
        print(f"📥 Collection: {collection_name}")
        print(f"   Description: {description}")
        print(f"   Source: {source_path}")
        print()

        try:
            # Check if already seeded (idempotency)
            current_count = agent.collections[collection_name].count()

            if current_count > 0 and not force_reseed:
                print(f"✓ Already seeded: {current_count} chunks (skipping)")
                total_chunks += current_count
                print()
                continue

            if current_count > 0 and force_reseed:
                print(f"⚠️  Force reseed: Clearing {current_count} existing chunks...")
                agent.chroma_client.delete_collection(collection_name)
                # Recreate collection
                agent.collections[collection_name] = agent.chroma_client.get_or_create_collection(
                    name=collection_name,
                    metadata={
                        "description": description,
                        "compliance_level": "regulatory",
                        "last_updated": datetime.now(UTC).isoformat()
                    }
                )
                print("✓ Collection cleared and recreated")

            # Validate source path exists
            full_source_path = Path(source_path)
            if not full_source_path.exists():
                raise FileNotFoundError(
                    f"CRITICAL: Source path does not exist: {full_source_path}\n"
                    f"Cannot seed collection without source documents."
                )

            # Count documents to ingest
            doc_files = list(full_source_path.glob("*.md"))
            if not doc_files:
                raise FileNotFoundError(
                    f"CRITICAL: No Markdown documents found in {full_source_path}\n"
                    f"Expected at least 1 document for ingestion."
                )

            print(f"📄 Found {len(doc_files)} documents to ingest")

            # Ingest documents
            print(f"🔨 Starting ingestion...")
            stats = await agent.ingest_documents(
                documents_path=str(full_source_path),
                collection_name=collection_name,
                force_reprocess=force_reseed
            )

            # Verify success
            if stats["status"] != "success":
                raise RuntimeError(
                    f"Ingestion failed with status: {stats['status']}"
                )

            final_count = agent.collections[collection_name].count()
            if final_count == 0:
                raise RuntimeError(
                    f"Ingestion reported success but collection is empty.\n"
                    f"Expected at least {len(doc_files)} chunks."
                )

            # Success
            print(f"✓ Ingestion complete:")
            print(f"   - Documents processed: {stats['processed_documents']}")
            print(f"   - Chunks created: {stats['processed_nodes']}")
            print(f"   - Cache hits: {stats['cache_hits']}")
            print(f"   - Final count: {final_count}")

            total_documents += stats['processed_documents']
            total_chunks += stats['processed_nodes']
            print()

        except Exception as e:
            print(f"❌ FAILED: {e}")
            failed_collections.append((collection_name, str(e)))
            print()

    # Final summary
    print("=" * 80)
    print("SEEDING SUMMARY")
    print("=" * 80)
    print(f"Completed: {datetime.now(UTC).isoformat()}")
    print(f"Total documents processed: {total_documents}")
    print(f"Total chunks created: {total_chunks}")
    print()

    if failed_collections:
        print("❌ FAILURES:")
        for collection_name, error in failed_collections:
            print(f"   - {collection_name}: {error}")
        print()
        raise RuntimeError(
            f"{len(failed_collections)} collection(s) failed to seed.\n"
            "Review errors above and fix before running workflow."
        )
    else:
        print("✅ ALL COLLECTIONS SEEDED SUCCESSFULLY")
        print()
        print("Next steps:")
        print("  1. Verify collections: python -c 'import chromadb; c=chromadb.PersistentClient(path=\"./lib/chroma_db\"); [print(f\"{col.name}: {col.count()}\") for col in c.list_collections()]'")
        print("  2. Run workflow: docker-compose -f docker-compose.dev.yml up")
        print("  3. Submit URS and monitor Langfuse trace for documents_retrieved > 0")

    print("=" * 80)


def main():
    """CLI entry point."""
    force_reseed = "--force" in sys.argv or "-f" in sys.argv

    try:
        asyncio.run(seed_all_collections(force_reseed=force_reseed))
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}\n", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

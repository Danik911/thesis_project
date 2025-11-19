#!/usr/bin/env python3
"""
Document ingestion script for ChromaDB with text chunking.

Loads regulatory documents into ChromaDB vector store for RAG retrieval.
Uses LlamaIndex's SimpleNodeParser to chunk large documents to fit within
embedding model's context window (8192 tokens for text-embedding-3-small).

Documents Ingested:
- GAMP-5 guidelines (ISPE Baseline Guide)
- 21 CFR Part 11 (FDA Electronic Records/Signatures)
- ICH Q9 (Quality Risk Management)
- ISO/IEC 27001 (Information Security)
- ISPE Commissioning & Qualification Guide

CRITICAL: NO FALLBACK LOGIC
- All errors must fail explicitly with diagnostic information
- Never proceed with empty/partial document ingestion
- Verify all documents loaded successfully before exiting
"""

import asyncio
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Regulatory document paths
REGULATORY_DOCS_DIR = Path("/app/main/docs/regulatory_guides")
REQUIRED_DOCUMENTS = [
    "ISPE - GAMP 5_ A Risk-Based Approach to Compliant GxP Computerized_short.md",
    "FDA Part-11--Electronic-Records--Electronic-Signatures---Scope-and-Application-(PDF).md",
    "ICH guideline Q9.md",
    "ISO IEC STANDARD 27001.md",
    "ISPE Baseline® Guide Commissioning and Qualification.md"
]


def validate_documents() -> list[Path]:
    """Validate that all required regulatory documents exist."""
    logger.info(f"Validating regulatory documents in: {REGULATORY_DOCS_DIR}")

    missing_docs = []
    valid_docs = []

    for doc_name in REQUIRED_DOCUMENTS:
        doc_path = REGULATORY_DOCS_DIR / doc_name
        if not doc_path.exists():
            missing_docs.append(doc_name)
            logger.error(f"MISSING: {doc_name}")
        else:
            valid_docs.append(doc_path)
            logger.info(f"FOUND: {doc_name} ({doc_path.stat().st_size:,} bytes)")

    if missing_docs:
        raise FileNotFoundError(
            f"CRITICAL: Missing {len(missing_docs)} required regulatory documents"
        )

    logger.info(f"All {len(valid_docs)} required documents validated successfully")
    return valid_docs


async def ingest_documents_to_chromadb(
    doc_paths: list[Path],
    persist_path: str = "/app/chroma_db",
    collection_name: str = "regulatory_documents"
) -> None:
    """
    Ingest documents into ChromaDB using LlamaIndex VectorStoreIndex.

    Uses SimpleNodeParser to chunk documents to fit within embedding model context window.
    """
    logger.info(
        f"Ingesting {len(doc_paths)} documents into ChromaDB\n"
        f"  Persist path: {persist_path}\n"
        f"  Collection: {collection_name}"
    )

    try:
        # Import here to avoid memory issues
        import chromadb
        from llama_index.core import Document, Settings, StorageContext, VectorStoreIndex
        from llama_index.core.node_parser import TokenTextSplitter  # NLTK-free alternative
        from llama_index.embeddings.openai import OpenAIEmbedding
        from llama_index.vector_stores.chroma import ChromaVectorStore

        # Initialize embedding model
        logger.info("Initializing OpenAI embedding model (text-embedding-3-small)...")
        embed_model = OpenAIEmbedding(model="text-embedding-3-small")
        Settings.embed_model = embed_model

        # Initialize token-based node parser (NO NLTK REQUIRED)
        # TokenTextSplitter uses tiktoken library only (production-safe)
        logger.info("Initializing TokenTextSplitter (chunk_size=1024, overlap=200)...")
        from llama_index.core.node_parser import TokenTextSplitter

        node_parser = TokenTextSplitter(
            chunk_size=1024,
            chunk_overlap=200,
            separator=" "  # Split on whitespace for pharmaceutical documents
        )

        # Initialize ChromaDB
        logger.info("Initializing ChromaDB client...")
        client = chromadb.PersistentClient(path=persist_path)
        collection = client.get_or_create_collection(collection_name)

        existing_count = collection.count()
        if existing_count > 0:
            logger.warning(f"Collection already contains {existing_count} documents")

        # Create ChromaDB vector store
        vector_store = ChromaVectorStore(chroma_collection=collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        # Load documents
        logger.info("Loading documents from filesystem...")
        documents = []
        for doc_path in doc_paths:
            logger.info(f"Loading: {doc_path.name}")
            content = doc_path.read_text(encoding="utf-8")

            if not content or not content.strip():
                raise RuntimeError(f"Document is empty: {doc_path}")

            logger.info(f"  Size: {len(content):,} characters")

            doc = Document(
                text=content,
                metadata={
                    "filename": doc_path.name,
                    "doc_type": "regulatory_guide",
                    "ingested_at": datetime.now(UTC).isoformat() + "Z",
                    "source": "local_filesystem",
                    "gamp_category": "5"
                },
                id_=doc_path.stem
            )
            documents.append(doc)

        logger.info(f"Loaded {len(documents)} documents successfully")

        # Create index with chunking (this embeds all chunks)
        logger.info("Creating vector store index (this may take 2-3 minutes)...")
        logger.info("Documents will be chunked automatically to fit embedding model context window")
        ingestion_start = datetime.now(UTC)

        index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            show_progress=True
        )

        ingestion_end = datetime.now(UTC)
        ingestion_duration = (ingestion_end - ingestion_start).total_seconds()

        # Verify ingestion
        final_count = collection.count()
        chunks_added = final_count - existing_count

        logger.info(
            f"Document ingestion completed successfully\n"
            f"  Documents processed: {len(documents)}\n"
            f"  Chunks created: {chunks_added}\n"
            f"  Total chunks in collection: {final_count}\n"
            f"  Ingestion duration: {ingestion_duration:.1f}s"
        )

        if chunks_added == 0:
            raise RuntimeError(
                f"CRITICAL: No chunks were added to ChromaDB\n"
                f"Expected at least 1 chunk per document"
            )

    except Exception as e:
        logger.exception(f"CRITICAL: ChromaDB ingestion failed: {e}")
        raise RuntimeError(
            f"CRITICAL: Failed to ingest documents into ChromaDB\n"
            f"Error: {e!s}"
        ) from e


async def main():
    """Main ingestion workflow."""
    logger.info("=== ChromaDB Regulatory Document Ingestion ===")

    try:
        # Step 1: Validate documents exist
        logger.info("\n[Step 1/2] Validating regulatory documents...")
        doc_paths = validate_documents()

        # Step 2: Ingest into ChromaDB
        logger.info("\n[Step 2/2] Ingesting documents into ChromaDB...")
        await ingest_documents_to_chromadb(doc_paths)

        logger.info("\n=== INGESTION COMPLETE ===")
        logger.info("ChromaDB is ready for pharmaceutical test generation workflow")
        return 0

    except Exception as e:
        logger.exception(f"INGESTION FAILED: {e}")
        logger.error("\n=== INGESTION FAILED ===")
        logger.error(
            "Regulatory knowledge base not populated. "
            "Workflow execution will fail without RAG context."
        )
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

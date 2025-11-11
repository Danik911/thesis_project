"""
Migration utility for migrating vector embeddings from ChromaDB to PostgreSQL pgvector.

Usage:
    python main/scripts/migrate_chromadb_to_pgvector.py

Features:
- Export all documents and embeddings from ChromaDB
- Import to PostgreSQL pgvector (Aurora Serverless)
- Validate migration with parity tests (80%+ top-5 overlap target)
- Pharmaceutical compliance: Preserve all metadata and audit trail
"""

import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "main"))

import chromadb
from llama_index.core import Document, Settings, StorageContext, VectorStoreIndex
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.vector_stores.postgres import PGVectorStore
from src.shared.config import get_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def export_from_chromadb(chroma_path: str, collection_name: str) -> list[dict]:
    """
    Export embeddings and metadata from ChromaDB.

    Args:
        chroma_path: Path to ChromaDB persistent storage
        collection_name: ChromaDB collection name

    Returns:
        List of dicts with keys: id, embedding, content, metadata

    Raises:
        RuntimeError: If export fails
    """
    try:
        logger.info(f"Exporting from ChromaDB: {chroma_path}/{collection_name}")

        client = chromadb.PersistentClient(path=chroma_path)
        collection = client.get_collection(collection_name)

        # Get all documents with embeddings
        results = collection.get(include=["embeddings", "documents", "metadatas"])

        if not results["ids"]:
            logger.warning("No documents found in ChromaDB collection")
            return []

        documents = []
        for i, doc_id in enumerate(results["ids"]):
            documents.append({
                "id": doc_id,
                "embedding": results["embeddings"][i] if results["embeddings"] else None,
                "content": results["documents"][i] if results["documents"] else "",
                "metadata": results["metadatas"][i] if results["metadatas"] else {}
            })

        logger.info(f"Exported {len(documents)} documents from ChromaDB")
        return documents

    except Exception as e:
        raise RuntimeError(
            f"CRITICAL: Failed to export from ChromaDB\n"
            f"Path: {chroma_path}\n"
            f"Collection: {collection_name}\n"
            f"Error: {e!s}"
        ) from e


def import_to_pgvector(
    documents: list[dict],
    connection_string: str,
    table_name: str = "rag_documents",
    embed_model: any = None
) -> None:
    """
    Import embeddings into PostgreSQL pgvector.

    Args:
        documents: List from export_from_chromadb()
        connection_string: PostgreSQL connection string
        table_name: Target table name
        embed_model: Cached embedding model (optional)

    Raises:
        RuntimeError: If import fails
    """
    try:
        logger.info(f"Importing {len(documents)} documents to pgvector: {table_name}")

        # Initialize pgvector store
        embed_dim = len(documents[0]["embedding"]) if documents and documents[0]["embedding"] else 1536

        vector_store = PGVectorStore.from_params(
            connection_string=connection_string,
            table_name=table_name,
            embed_dim=embed_dim
        )

        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        # Set embedding model if provided
        if embed_model:
            Settings.embed_model = embed_model

        # Convert to LlamaIndex Document objects
        llama_docs = []
        for doc in documents:
            llama_docs.append(
                Document(
                    text=doc["content"],
                    metadata=doc["metadata"],
                    doc_id=doc["id"]
                )
            )

        # Build index (this inserts into pgvector)
        index = VectorStoreIndex.from_documents(
            llama_docs,
            storage_context=storage_context
        )

        logger.info(f"Successfully imported {len(llama_docs)} documents to pgvector")

    except Exception as e:
        raise RuntimeError(
            f"CRITICAL: Failed to import to pgvector\n"
            f"Document count: {len(documents)}\n"
            f"Table: {table_name}\n"
            f"Error: {e!s}"
        ) from e


def validate_migration(
    chroma_path: str,
    chroma_collection: str,
    pg_connection: str,
    pg_table: str,
    test_queries: list[str],
    similarity_threshold: float = 0.8,
    embed_model: any = None
) -> bool:
    """
    Validate migration by comparing retrieval results.

    Args:
        chroma_path: ChromaDB path
        chroma_collection: ChromaDB collection name
        pg_connection: PostgreSQL connection string
        pg_table: PostgreSQL table name
        test_queries: List of test queries
        similarity_threshold: Minimum overlap percentage (default: 0.8 = 80%)
        embed_model: Cached embedding model (optional)

    Returns:
        True if top-5 retrieval overlap >= similarity_threshold

    Raises:
        RuntimeError: If validation fails
    """
    try:
        logger.info("Validating migration with parity tests...")

        # Set embedding model if provided
        if embed_model:
            Settings.embed_model = embed_model

        # ChromaDB index
        chroma_client = chromadb.PersistentClient(path=chroma_path)
        chroma_coll = chroma_client.get_collection(chroma_collection)
        chroma_store = ChromaVectorStore(chroma_collection=chroma_coll)
        chroma_context = StorageContext.from_defaults(vector_store=chroma_store)
        chroma_index = VectorStoreIndex.from_vector_store(
            chroma_store,
            storage_context=chroma_context
        )

        # pgvector index
        pg_store = PGVectorStore.from_params(
            connection_string=pg_connection,
            table_name=pg_table
        )
        pg_context = StorageContext.from_defaults(vector_store=pg_store)
        pg_index = VectorStoreIndex.from_vector_store(
            pg_store,
            storage_context=pg_context
        )

        overlaps = []
        for query in test_queries:
            logger.info(f"Testing query: '{query[:50]}...'")

            # Retrieve top-5 from both
            chroma_results = chroma_index.as_retriever(similarity_top_k=5).retrieve(query)
            pg_results = pg_index.as_retriever(similarity_top_k=5).retrieve(query)

            chroma_ids = {r.node.node_id for r in chroma_results}
            pg_ids = {r.node.node_id for r in pg_results}

            # Calculate overlap
            intersection = len(chroma_ids & pg_ids)
            overlap = intersection / 5.0  # top-5

            overlaps.append(overlap)
            logger.info(f"  Overlap: {overlap:.1%} ({intersection}/5)")

        avg_overlap = sum(overlaps) / len(overlaps) if overlaps else 0.0
        logger.info(f"\nAverage top-5 overlap: {avg_overlap:.1%}")

        if avg_overlap >= similarity_threshold:
            logger.info(f"✅ Migration validated successfully (>= {similarity_threshold:.0%} threshold)")
            return True
        logger.error(f"❌ Migration validation failed (< {similarity_threshold:.0%} threshold)")
        return False

    except Exception as e:
        raise RuntimeError(
            f"CRITICAL: Migration validation failed\n"
            f"Error: {e!s}"
        ) from e


def main():
    """Main migration workflow."""
    try:
        # Load configuration
        config = get_config()
        vector_config = config.vector_store

        # Cache embedding model
        embed_model = OpenAIEmbedding(
            model=vector_config.embedding_model,
            dimensions=vector_config.embedding_dimensions
        )

        # 1. Export from ChromaDB
        logger.info("=" * 80)
        logger.info("STEP 1: Export from ChromaDB")
        logger.info("=" * 80)

        docs = export_from_chromadb(
            chroma_path=vector_config.chroma_path,
            collection_name=vector_config.chroma_collection
        )

        if not docs:
            logger.error("No documents to migrate. Exiting.")
            return

        # 2. Import to pgvector
        logger.info("\n" + "=" * 80)
        logger.info("STEP 2: Import to pgvector")
        logger.info("=" * 80)

        if not vector_config.pg_connection_string:
            raise ValueError(
                "PostgreSQL connection string required for migration\n"
                "Set VECTOR_STORE_CONNECTION_STRING environment variable"
            )

        import_to_pgvector(
            documents=docs,
            connection_string=vector_config.pg_connection_string,
            table_name=vector_config.pg_table_name,
            embed_model=embed_model
        )

        # 3. Validate migration
        logger.info("\n" + "=" * 80)
        logger.info("STEP 3: Validate migration")
        logger.info("=" * 80)

        test_queries = [
            "GAMP-5 category 5 validation requirements",
            "OQ test execution procedures and documentation",
            "IQ installation qualification checklist items",
            "risk-based validation approach for pharmaceutical systems",
            "21 CFR Part 11 electronic signature requirements"
        ]

        success = validate_migration(
            chroma_path=vector_config.chroma_path,
            chroma_collection=vector_config.chroma_collection,
            pg_connection=vector_config.pg_connection_string,
            pg_table=vector_config.pg_table_name,
            test_queries=test_queries,
            similarity_threshold=0.8,  # 80% overlap target
            embed_model=embed_model
        )

        if success:
            logger.info("\n" + "=" * 80)
            logger.info("✅ MIGRATION COMPLETED SUCCESSFULLY")
            logger.info("=" * 80)
            logger.info(f"Documents migrated: {len(docs)}")
            logger.info(f"Source: ChromaDB ({vector_config.chroma_path})")
            logger.info(f"Target: pgvector ({vector_config.pg_table_name})")
        else:
            logger.error("\n" + "=" * 80)
            logger.error("❌ MIGRATION VALIDATION FAILED")
            logger.error("=" * 80)
            logger.error("Investigate retrieval discrepancies before using pgvector in production")

    except Exception as e:
        logger.error(f"\n{'=' * 80}")
        logger.error("❌ MIGRATION FAILED")
        logger.error("=" * 80)
        logger.error(f"Error: {e!s}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

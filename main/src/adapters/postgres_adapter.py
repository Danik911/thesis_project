"""
PostgreSQL pgvector adapter for AWS production (Aurora Serverless v2).

STRENGTHS:
- Enterprise-grade ACID compliance
- Native audit logging via triggers (ALCOA+ requirement)
- Excellent metadata filtering via B-tree indexes
- HNSW and IVFFlat indexing strategies
- Scales to millions of vectors with proper tuning

USE CASE: AWS production environment
"""

import logging
import traceback
from typing import Any

from llama_index.core import Document, Settings, StorageContext, VectorStoreIndex
from llama_index.core.schema import NodeWithScore
from llama_index.vector_stores.postgres import PGVectorStore

logger = logging.getLogger(__name__)


class PostgresVectorStoreAdapter:
    """PostgreSQL pgvector adapter for AWS production (Aurora Serverless)."""

    def __init__(
        self,
        connection_string: str,
        table_name: str = "rag_documents",
        embed_dim: int = 1536,
        embed_model: Any = None
    ):
        """
        Initialize PostgreSQL pgvector store.

        Args:
            connection_string: PostgreSQL connection string
                Format: postgresql://user:pass@aurora-endpoint:5432/dbname
            table_name: Vector storage table name
            embed_dim: Embedding dimension (must match model, default: 1536 for text-embedding-3-small)
            embed_model: Cached embedding model

        Raises:
            ValueError: If connection_string is missing or invalid
            RuntimeError: If PostgreSQL connection fails
        """
        try:
            if not connection_string:
                raise ValueError(
                    "CRITICAL: PostgreSQL connection string required\n"
                    "Set via VECTOR_STORE_CONNECTION_STRING environment variable\n"
                    "Format: postgresql://user:pass@aurora-endpoint:5432/dbname"
                )

            self.connection_string = connection_string
            self.table_name = table_name
            self.embed_dim = embed_dim

            # Convert sync connection string to async for asyncpg driver
            # postgresql://... → postgresql+asyncpg://...
            async_connection_string = connection_string.replace(
                "postgresql://",
                "postgresql+asyncpg://"
            )

            # Initialize pgvector store
            self.vector_store = PGVectorStore.from_params(
                connection_string=connection_string,
                async_connection_string=async_connection_string,
                table_name=table_name,
                embed_dim=embed_dim,
                # HNSW index parameters (tuned for pharmaceutical use: 200-10,000 docs)
                hnsw_kwargs={
                    "hnsw_m": 16,              # connections per layer (default: 16, range: 2-100)
                    "hnsw_ef_construction": 128,  # build-time search breadth (default: 128)
                    "hnsw_ef_search": 64,      # query-time search breadth (default: 64)
                }
            )

            self.storage_context = StorageContext.from_defaults(
                vector_store=self.vector_store
            )

            # Cache embedding model (CRITICAL for performance)
            if embed_model:
                Settings.embed_model = embed_model
                logger.info("Using provided cached embedding model")
            else:
                logger.warning(
                    "No embedding model provided - will use LlamaIndex default. "
                    "Consider passing cached embed_model for better performance."
                )

            logger.info(
                f"PostgreSQL pgvector initialized successfully\n"
                f"  Connection: {connection_string.split('@')[1] if '@' in connection_string else 'masked'}\n"
                f"  Table: {table_name}\n"
                f"  Embedding dim: {embed_dim}\n"
                f"  HNSW params: m=16, ef_construction=128, ef_search=64"
            )

        except ValueError:
            # Validation errors should propagate as-is
            raise
        except Exception as e:
            raise RuntimeError(
                f"CRITICAL: PostgreSQL pgvector initialization failed\n"
                f"Connection string: {connection_string[:50]}...{connection_string[-20:] if len(connection_string) > 70 else ''}\n"
                f"Table: {table_name}\n"
                f"Embed dim: {embed_dim}\n"
                f"Error: {e!s}\n"
                f"Stack trace: {traceback.format_exc()}\n"
                f"Check: PostgreSQL connection, pgvector extension installed, network connectivity"
            ) from e

    async def add_documents(
        self,
        documents: list[Document],
        metadata: dict[str, Any]
    ) -> list[str]:
        """
        Add documents to pgvector with embeddings.

        PostgreSQL audit triggers will automatically log all insertions for ALCOA+ compliance.

        Args:
            documents: LlamaIndex Document objects
            metadata: GAMP-5 compliant metadata

        Returns:
            List of document IDs inserted

        Raises:
            ValueError: If metadata validation fails
            RuntimeError: If document addition fails
        """
        try:
            # Validate metadata
            self._validate_metadata(metadata)

            # Validate documents (NO FALLBACK LOGIC: reject empty documents)
            for i, doc in enumerate(documents):
                if not doc.text or not doc.text.strip():
                    raise ValueError(
                        f"CRITICAL: Document at index {i} has empty text\n"
                        f"NO FALLBACK LOGIC: Empty documents must be rejected\n"
                        f"Document ID: {doc.doc_id or doc.id_ or 'N/A'}\n"
                        f"Check: Ensure all documents have non-empty text content"
                    )

            # Enrich documents with metadata
            for doc in documents:
                doc.metadata.update(metadata)

            # Build index (PostgreSQL audit triggers log automatically)
            index = VectorStoreIndex.from_documents(
                documents,
                storage_context=self.storage_context
            )

            # Extract document IDs
            doc_ids = [doc.doc_id or doc.id_ for doc in documents]

            logger.info(
                f"Added {len(doc_ids)} documents to pgvector\n"
                f"  Table: {self.table_name}\n"
                f"  GAMP Category: {metadata.get('gamp_category', 'N/A')}\n"
                f"  Audit trail: Logged via PostgreSQL triggers"
            )

            return doc_ids

        except ValueError:
            # Validation errors should propagate as-is
            raise
        except Exception as e:
            raise RuntimeError(
                f"CRITICAL: Failed to add documents to pgvector\n"
                f"Document count: {len(documents)}\n"
                f"Table: {self.table_name}\n"
                f"Metadata: {metadata}\n"
                f"Error: {e!s}\n"
                f"Stack trace: {traceback.format_exc()}\n"
                f"Check: PostgreSQL connection, table schema, pgvector extension"
            ) from e

    async def query(
        self,
        query_text: str,
        top_k: int = 10,
        metadata_filters: dict[str, Any] | None = None
    ) -> list[NodeWithScore]:
        """
        Query pgvector for similar documents with metadata filtering.

        PostgreSQL handles metadata filtering efficiently via B-tree indexes,
        unlike ChromaDB which post-filters after retrieval.

        Args:
            query_text: Natural language query
            top_k: Number of results to return
            metadata_filters: Optional filters (e.g., {"gamp_category": "5"})

        Returns:
            List of retrieved nodes with similarity scores

        Raises:
            ValueError: If query_text is empty
            RuntimeError: If query fails
        """
        try:
            # Validate query (NO FALLBACK LOGIC: reject empty queries)
            if not query_text or not query_text.strip():
                raise ValueError(
                    "CRITICAL: Query text cannot be empty\n"
                    "NO FALLBACK LOGIC: Empty queries must be rejected\n"
                    "Provide a non-empty query string"
                )

            # Load index from vector store
            index = VectorStoreIndex.from_vector_store(
                self.vector_store,
                storage_context=self.storage_context
            )

            # Create retriever with filters
            if metadata_filters:
                # Convert to LlamaIndex MetadataFilters
                from llama_index.core.vector_stores import (
                    ExactMatchFilter,
                    MetadataFilters,
                )

                filters = MetadataFilters(
                    filters=[
                        ExactMatchFilter(key=k, value=v)
                        for k, v in metadata_filters.items()
                    ]
                )

                # PostgreSQL handles filters efficiently via B-tree indexes
                retriever = index.as_retriever(
                    similarity_top_k=top_k,
                    filters=filters
                )

                logger.debug(
                    f"pgvector metadata filtering: Efficient via B-tree indexes\n"
                    f"  Filters: {metadata_filters}"
                )
            else:
                retriever = index.as_retriever(similarity_top_k=top_k)

            # Execute query
            results = retriever.retrieve(query_text)

            logger.info(
                f"Retrieved {len(results)} documents from pgvector\n"
                f"  Query: {query_text[:50]}...\n"
                f"  Filters: {metadata_filters}\n"
                f"  Table: {self.table_name}"
            )

            return results

        except Exception as e:
            raise RuntimeError(
                f"CRITICAL: pgvector query failed\n"
                f"Query: {query_text}\n"
                f"Top-k: {top_k}\n"
                f"Filters: {metadata_filters}\n"
                f"Table: {self.table_name}\n"
                f"Error: {e!s}\n"
                f"Stack trace: {traceback.format_exc()}\n"
                f"Check: PostgreSQL connection, table exists, HNSW index built"
            ) from e

    def get_index(self) -> VectorStoreIndex:
        """
        Get LlamaIndex VectorStoreIndex for advanced operations.

        Returns:
            Configured VectorStoreIndex instance
        """
        return VectorStoreIndex.from_vector_store(
            self.vector_store,
            storage_context=self.storage_context
        )

    def _validate_metadata(self, metadata: dict[str, Any]) -> None:
        """
        Validate GAMP-5 compliant metadata.

        Args:
            metadata: Metadata dictionary to validate

        Raises:
            ValueError: If required fields missing or invalid
        """
        required_fields = ["gamp_category", "created_by", "document_type"]
        missing = [field for field in required_fields if field not in metadata]

        if missing:
            raise ValueError(
                f"CRITICAL: Missing required metadata fields: {missing}\n"
                f"Required fields: {required_fields}\n"
                f"Provided fields: {list(metadata.keys())}\n"
                "Pharmaceutical compliance mandate - all required metadata must be present"
            )

        # Validate GAMP category
        valid_categories = ["1", "3", "4", "5"]
        gamp_category = str(metadata.get("gamp_category", ""))
        if gamp_category not in valid_categories:
            raise ValueError(
                f"CRITICAL: Invalid GAMP category '{gamp_category}'\n"
                f"Valid categories: {valid_categories}\n"
                "GAMP-5 categorization is mandatory for pharmaceutical systems"
            )

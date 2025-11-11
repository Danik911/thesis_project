"""
Core vector store provider protocol and factory for dual-mode vector storage.

Defines the contract for vector store providers and provides a factory for creating
appropriate adapters based on configuration.

Supports:
- ChromaDB (local development mode)
- PostgreSQL with pgvector extension (AWS production mode via Aurora Serverless)
"""

from typing import Any, Protocol

from llama_index.core import Document, VectorStoreIndex
from llama_index.core.schema import NodeWithScore


class VectorStoreProvider(Protocol):
    """
    Protocol defining contract for vector store providers.

    All implementations (ChromaDB, pgvector) must implement this interface
    to ensure consistent behavior across different backends.

    GAMP-5 Compliance:
    - All methods must preserve metadata for audit trail
    - All failures must raise explicit exceptions with diagnostic information

    NO FALLBACK LOGIC:
    - Never return success on failure
    - Never use default values to mask errors
    - Never silently catch exceptions
    """

    async def add_documents(
        self,
        documents: list[Document],
        metadata: dict[str, Any]
    ) -> list[str]:
        """
        Add documents to vector store with embeddings.

        Args:
            documents: LlamaIndex Document objects
            metadata: GAMP-5 compliant metadata (gamp_category, created_by, document_type)

        Returns:
            List of document IDs inserted

        Raises:
            ValueError: If metadata invalid or documents malformed
            RuntimeError: If vector store operation fails (with full diagnostics)

        CRITICAL: NO FALLBACK LOGIC - All errors must propagate with full context
        """
        ...

    async def query(
        self,
        query_text: str,
        top_k: int = 10,
        metadata_filters: dict[str, Any] | None = None
    ) -> list[NodeWithScore]:
        """
        Query vector store for similar documents.

        Args:
            query_text: Natural language query
            top_k: Number of results to return
            metadata_filters: Optional filters (e.g., {"gamp_category": "5"})

        Returns:
            List of retrieved nodes with similarity scores

        Raises:
            ValueError: If query parameters invalid
            RuntimeError: If retrieval operation fails (with full diagnostics)

        CRITICAL: NO FALLBACK LOGIC - Never return empty results to mask errors
        """
        ...

    def get_index(self) -> VectorStoreIndex:
        """
        Get LlamaIndex VectorStoreIndex for advanced operations.

        Returns:
            Configured VectorStoreIndex instance

        Raises:
            RuntimeError: If index not initialized or unavailable
        """
        ...


class VectorStoreFactory:
    """Factory for creating vector store providers based on configuration."""

    @staticmethod
    def create_provider(mode: str, **kwargs: Any) -> VectorStoreProvider:
        """
        Create vector store provider based on mode.

        Args:
            mode: "chromadb" or "pgvector"
            **kwargs: Configuration parameters
                For chromadb:
                    - persist_path: str (default: "./chroma_db")
                    - collection_name: str (default: "pharma_docs")
                    - embed_model: Any (optional, cached embedding model)
                For pgvector:
                    - connection_string: str (required)
                    - table_name: str (default: "rag_documents")
                    - embed_dim: int (default: 1536)
                    - embed_model: Any (optional, cached embedding model)

        Returns:
            Configured vector store provider

        Raises:
            ValueError: If mode invalid or required parameters missing

        CRITICAL: NO FALLBACK LOGIC - Never default to chromadb on pgvector failure
        """
        # Import here to avoid circular dependencies
        from src.adapters.chroma_adapter import ChromaVectorStoreAdapter
        from src.adapters.postgres_adapter import PostgresVectorStoreAdapter

        if mode == "chromadb":
            persist_path = kwargs.get("persist_path", "./chroma_db")
            collection_name = kwargs.get("collection_name", "pharma_docs")
            embed_model = kwargs.get("embed_model")

            return ChromaVectorStoreAdapter(
                persist_path=str(persist_path),
                collection_name=str(collection_name),
                embed_model=embed_model
            )

        if mode == "pgvector":
            connection_string = kwargs.get("connection_string")
            if not connection_string:
                raise ValueError(
                    "CRITICAL: pgvector mode requires 'connection_string' parameter\n"
                    "Set VECTOR_STORE_CONNECTION_STRING environment variable\n"
                    "Format: postgresql://user:pass@aurora-endpoint:5432/dbname"
                )

            table_name = kwargs.get("table_name", "rag_documents")
            embed_dim = kwargs.get("embed_dim", 1536)
            embed_model = kwargs.get("embed_model")

            return PostgresVectorStoreAdapter(
                connection_string=str(connection_string),
                table_name=str(table_name),
                embed_dim=int(embed_dim),
                embed_model=embed_model
            )

        raise ValueError(
            f"CRITICAL: Invalid vector store mode '{mode}'\n"
            f"Supported modes: 'chromadb', 'pgvector'\n"
            "Check RAG_MODE environment variable"
        )

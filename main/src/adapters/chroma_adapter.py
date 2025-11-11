"""
ChromaDB vector store adapter for local development.

LIMITATIONS:
- Metadata filtering performance degrades severely at scale (5+ minutes for 40K docs)
- No built-in audit logging or ACID compliance
- NOT suitable for production pharmaceutical use

USE CASE: Local development ONLY
"""

import logging
import traceback
from typing import Any

import chromadb
from llama_index.core import Document, Settings, StorageContext, VectorStoreIndex
from llama_index.core.schema import NodeWithScore
from llama_index.vector_stores.chroma import ChromaVectorStore

logger = logging.getLogger(__name__)


class ChromaVectorStoreAdapter:
    """ChromaDB vector store adapter for local development."""

    def __init__(
        self,
        persist_path: str = "./chroma_db",
        collection_name: str = "pharma_docs",
        embed_model: Any = None
    ):
        """
        Initialize ChromaDB vector store.

        Args:
            persist_path: Directory for persistent storage
            collection_name: ChromaDB collection name
            embed_model: Cached embedding model (reuse to avoid instantiation)

        Raises:
            RuntimeError: If ChromaDB initialization fails
        """
        try:
            # Initialize ChromaDB persistent client
            self.client = chromadb.PersistentClient(path=persist_path)
            self.collection = self.client.get_or_create_collection(collection_name)
            self.persist_path = persist_path
            self.collection_name = collection_name

            # Wrap in LlamaIndex abstraction
            self.vector_store = ChromaVectorStore(chroma_collection=self.collection)
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
                f"ChromaDB initialized successfully\n"
                f"  Persist path: {persist_path}\n"
                f"  Collection: {collection_name}"
            )

        except Exception as e:
            raise RuntimeError(
                f"CRITICAL: ChromaDB initialization failed\n"
                f"Persist path: {persist_path}\n"
                f"Collection: {collection_name}\n"
                f"Error: {e!s}\n"
                f"Stack trace: {traceback.format_exc()}"
            ) from e

    async def add_documents(
        self,
        documents: list[Document],
        metadata: dict[str, Any]
    ) -> list[str]:
        """
        Add documents to ChromaDB with embeddings.

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

            # Enrich documents with metadata
            for doc in documents:
                doc.metadata.update(metadata)

            # Build index (generates embeddings and stores)
            index = VectorStoreIndex.from_documents(
                documents,
                storage_context=self.storage_context
            )

            # Extract document IDs
            doc_ids = [doc.doc_id or doc.id_ for doc in documents]

            logger.info(
                f"Added {len(doc_ids)} documents to ChromaDB\n"
                f"  Collection: {self.collection_name}\n"
                f"  GAMP Category: {metadata.get('gamp_category', 'N/A')}"
            )

            return doc_ids

        except ValueError:
            # Validation errors should propagate as-is
            raise
        except Exception as e:
            raise RuntimeError(
                f"CRITICAL: Failed to add documents to ChromaDB\n"
                f"Document count: {len(documents)}\n"
                f"Collection: {self.collection_name}\n"
                f"Metadata: {metadata}\n"
                f"Error: {e!s}\n"
                f"Stack trace: {traceback.format_exc()}"
            ) from e

    async def query(
        self,
        query_text: str,
        top_k: int = 10,
        metadata_filters: dict[str, Any] | None = None
    ) -> list[NodeWithScore]:
        """
        Query ChromaDB for similar documents.

        WARNING: ChromaDB metadata filtering has poor performance at scale.
        Over-fetches results (2x top_k) to compensate for post-filtering.

        Args:
            query_text: Natural language query
            top_k: Number of results to return
            metadata_filters: Optional filters (e.g., {"gamp_category": "5"})

        Returns:
            List of retrieved nodes with similarity scores

        Raises:
            RuntimeError: If query fails
        """
        try:
            # Load index from vector store
            index = VectorStoreIndex.from_vector_store(
                self.vector_store,
                storage_context=self.storage_context
            )

            # Apply metadata filters if provided
            if metadata_filters:
                logger.warning(
                    "ChromaDB metadata filtering has poor performance at scale "
                    "(5+ minutes for 40K docs). Consider pre-filtering at application level "
                    "or using pgvector for production."
                )

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

                # Over-fetch to compensate for post-filtering
                retriever = index.as_retriever(
                    similarity_top_k=top_k * 2,
                    filters=filters
                )
            else:
                retriever = index.as_retriever(similarity_top_k=top_k)

            # Execute query
            results = retriever.retrieve(query_text)

            # Trim to top_k if over-fetched
            if len(results) > top_k:
                results = results[:top_k]

            logger.info(
                f"Retrieved {len(results)} documents from ChromaDB\n"
                f"  Query: {query_text[:50]}...\n"
                f"  Filters: {metadata_filters}\n"
                f"  Collection: {self.collection_name}"
            )

            return results

        except Exception as e:
            raise RuntimeError(
                f"CRITICAL: ChromaDB query failed\n"
                f"Query: {query_text}\n"
                f"Top-k: {top_k}\n"
                f"Filters: {metadata_filters}\n"
                f"Collection: {self.collection_name}\n"
                f"Error: {e!s}\n"
                f"Stack trace: {traceback.format_exc()}"
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
                "GAMP-5 compliance mandate - all required metadata must be present"
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

    def __del__(self) -> None:
        """Clean up ChromaDB client resources."""
        try:
            # ChromaDB doesn't have explicit close(), but delete client to trigger cleanup
            if hasattr(self, "client"):
                del self.client
                logger.debug("ChromaDB client cleaned up")
        except Exception as e:
            logger.warning(f"Error during ChromaDB cleanup: {e}")

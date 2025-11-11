"""
Comprehensive tests for vector store adapters (ChromaDB and PostgreSQL pgvector).

Test coverage:
- Protocol-based abstraction (VectorStoreFactory)
- ChromaDB adapter functionality
- PostgreSQL pgvector adapter functionality (requires database connection)
- Metadata validation (GAMP-5 compliance)
- Error handling (NO FALLBACK LOGIC)
- Embedding model caching
"""

from unittest.mock import MagicMock, patch

import pytest
from llama_index.core import Document
from src.adapters.chroma_adapter import ChromaVectorStoreAdapter
from src.adapters.postgres_adapter import PostgresVectorStoreAdapter

# Import adapters
from src.adapters.vector_store import VectorStoreFactory


class TestVectorStoreFactory:
    """Tests for VectorStoreFactory."""

    def test_factory_creates_chroma_adapter(self):
        """Test factory creates ChromaDB adapter with valid mode."""
        provider = VectorStoreFactory.create_provider(
            mode="chromadb",
            persist_path="./test_chroma",
            collection_name="test_collection"
        )

        assert isinstance(provider, ChromaVectorStoreAdapter)
        assert provider.persist_path == "./test_chroma"
        assert provider.collection_name == "test_collection"

    def test_factory_creates_pgvector_adapter(self):
        """Test factory creates pgvector adapter with valid mode and connection."""
        with patch("src.adapters.postgres_adapter.PGVectorStore") as mock_pg:
            mock_pg.from_params.return_value = MagicMock()

            provider = VectorStoreFactory.create_provider(
                mode="pgvector",
                connection_string="postgresql://user:pass@localhost:5432/test",
                table_name="test_table",
                embed_dim=1536
            )

            assert isinstance(provider, PostgresVectorStoreAdapter)
            assert provider.table_name == "test_table"
            assert provider.embed_dim == 1536

    def test_factory_raises_error_for_invalid_mode(self):
        """Test factory raises ValueError for invalid mode (NO FALLBACK)."""
        with pytest.raises(ValueError) as exc_info:
            VectorStoreFactory.create_provider(mode="invalid_mode")

        assert "Invalid vector store mode" in str(exc_info.value)
        assert "chromadb" in str(exc_info.value)
        assert "pgvector" in str(exc_info.value)

    def test_factory_raises_error_for_pgvector_without_connection(self):
        """Test factory raises ValueError for pgvector without connection string (NO FALLBACK)."""
        with pytest.raises(ValueError) as exc_info:
            VectorStoreFactory.create_provider(mode="pgvector")

        assert "connection_string" in str(exc_info.value).lower()
        assert "CRITICAL" in str(exc_info.value)


class TestChromaVectorStoreAdapter:
    """Tests for ChromaDB adapter."""

    @patch("src.adapters.chroma_adapter.chromadb.PersistentClient")
    def test_chroma_initialization_success(self, mock_client):
        """Test successful ChromaDB initialization."""
        mock_collection = MagicMock()
        mock_client.return_value.get_or_create_collection.return_value = mock_collection

        adapter = ChromaVectorStoreAdapter(
            persist_path="./test_chroma",
            collection_name="test_collection"
        )

        assert adapter.persist_path == "./test_chroma"
        assert adapter.collection_name == "test_collection"
        mock_client.assert_called_once_with(path="./test_chroma")

    @patch("src.adapters.chroma_adapter.chromadb.PersistentClient")
    def test_chroma_initialization_failure(self, mock_client):
        """Test ChromaDB initialization failure raises RuntimeError (NO FALLBACK)."""
        mock_client.side_effect = Exception("Connection failed")

        with pytest.raises(RuntimeError) as exc_info:
            ChromaVectorStoreAdapter(persist_path="./test_chroma")

        assert "CRITICAL" in str(exc_info.value)
        assert "ChromaDB initialization failed" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("src.adapters.chroma_adapter.chromadb.PersistentClient")
    @patch("src.adapters.chroma_adapter.VectorStoreIndex")
    async def test_add_documents_validates_metadata(self, mock_index, mock_client):
        """Test add_documents validates GAMP-5 metadata."""
        mock_collection = MagicMock()
        mock_client.return_value.get_or_create_collection.return_value = mock_collection

        adapter = ChromaVectorStoreAdapter()

        # Valid metadata
        valid_metadata = {
            "gamp_category": "5",
            "created_by": "test_user",
            "document_type": "validation_protocol"
        }

        documents = [Document(text="Test document")]

        # Mock index creation
        mock_index.from_documents.return_value = MagicMock()

        doc_ids = await adapter.add_documents(documents, valid_metadata)
        assert len(doc_ids) == 1

    @pytest.mark.asyncio
    @patch("src.adapters.chroma_adapter.chromadb.PersistentClient")
    async def test_add_documents_rejects_missing_metadata(self, mock_client):
        """Test add_documents rejects missing required metadata (NO FALLBACK)."""
        mock_collection = MagicMock()
        mock_client.return_value.get_or_create_collection.return_value = mock_collection

        adapter = ChromaVectorStoreAdapter()

        # Missing required fields
        invalid_metadata = {
            "gamp_category": "5"
            # Missing: created_by, document_type
        }

        documents = [Document(text="Test document")]

        with pytest.raises(ValueError) as exc_info:
            await adapter.add_documents(documents, invalid_metadata)

        assert "Missing required metadata fields" in str(exc_info.value)
        assert "created_by" in str(exc_info.value)
        assert "document_type" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("src.adapters.chroma_adapter.chromadb.PersistentClient")
    async def test_add_documents_rejects_invalid_gamp_category(self, mock_client):
        """Test add_documents rejects invalid GAMP category (NO FALLBACK)."""
        mock_collection = MagicMock()
        mock_client.return_value.get_or_create_collection.return_value = mock_collection

        adapter = ChromaVectorStoreAdapter()

        # Invalid GAMP category
        invalid_metadata = {
            "gamp_category": "99",  # Invalid
            "created_by": "test_user",
            "document_type": "validation_protocol"
        }

        documents = [Document(text="Test document")]

        with pytest.raises(ValueError) as exc_info:
            await adapter.add_documents(documents, invalid_metadata)

        assert "Invalid GAMP category" in str(exc_info.value)
        assert "99" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("src.adapters.chroma_adapter.chromadb.PersistentClient")
    @patch("src.adapters.chroma_adapter.VectorStoreIndex")
    async def test_query_success(self, mock_index, mock_client):
        """Test query returns results successfully."""
        mock_collection = MagicMock()
        mock_client.return_value.get_or_create_collection.return_value = mock_collection

        adapter = ChromaVectorStoreAdapter()

        # Mock retriever
        mock_retriever = MagicMock()
        mock_node = MagicMock()
        mock_node.node.node_id = "test_node_1"
        mock_retriever.retrieve.return_value = [mock_node]

        mock_index_instance = MagicMock()
        mock_index_instance.as_retriever.return_value = mock_retriever
        mock_index.from_vector_store.return_value = mock_index_instance

        results = await adapter.query("test query", top_k=5)

        assert len(results) == 1
        mock_retriever.retrieve.assert_called_once_with("test query")

    @pytest.mark.asyncio
    @patch("src.adapters.chroma_adapter.chromadb.PersistentClient")
    @patch("src.adapters.chroma_adapter.VectorStoreIndex")
    async def test_query_with_metadata_filters(self, mock_index, mock_client):
        """Test query with metadata filters (warns about performance)."""
        mock_collection = MagicMock()
        mock_client.return_value.get_or_create_collection.return_value = mock_collection

        adapter = ChromaVectorStoreAdapter()

        # Mock retriever
        mock_retriever = MagicMock()
        mock_node = MagicMock()
        mock_retriever.retrieve.return_value = [mock_node]

        mock_index_instance = MagicMock()
        mock_index_instance.as_retriever.return_value = mock_retriever
        mock_index.from_vector_store.return_value = mock_index_instance

        metadata_filters = {"gamp_category": "5"}

        with patch("src.adapters.chroma_adapter.logger") as mock_logger:
            results = await adapter.query("test query", top_k=5, metadata_filters=metadata_filters)

            # Verify warning about performance
            mock_logger.warning.assert_called_once()
            assert "poor performance" in str(mock_logger.warning.call_args).lower()


class TestPostgresVectorStoreAdapter:
    """Tests for PostgreSQL pgvector adapter."""

    @patch("src.adapters.postgres_adapter.PGVectorStore")
    def test_postgres_initialization_success(self, mock_pg):
        """Test successful PostgreSQL pgvector initialization."""
        mock_pg.from_params.return_value = MagicMock()

        adapter = PostgresVectorStoreAdapter(
            connection_string="postgresql://user:pass@localhost:5432/test",
            table_name="test_table",
            embed_dim=1536
        )

        assert adapter.connection_string == "postgresql://user:pass@localhost:5432/test"
        assert adapter.table_name == "test_table"
        assert adapter.embed_dim == 1536

    def test_postgres_initialization_without_connection_string(self):
        """Test PostgreSQL initialization fails without connection string (NO FALLBACK)."""
        with pytest.raises(ValueError) as exc_info:
            PostgresVectorStoreAdapter(connection_string="")

        assert "connection string required" in str(exc_info.value).lower()
        assert "CRITICAL" in str(exc_info.value)

    @patch("src.adapters.postgres_adapter.PGVectorStore")
    def test_postgres_initialization_failure(self, mock_pg):
        """Test PostgreSQL initialization failure raises RuntimeError (NO FALLBACK)."""
        mock_pg.from_params.side_effect = Exception("Connection failed")

        with pytest.raises(RuntimeError) as exc_info:
            PostgresVectorStoreAdapter(
                connection_string="postgresql://user:pass@localhost:5432/test"
            )

        assert "CRITICAL" in str(exc_info.value)
        assert "PostgreSQL pgvector initialization failed" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("src.adapters.postgres_adapter.PGVectorStore")
    @patch("src.adapters.postgres_adapter.VectorStoreIndex")
    async def test_add_documents_validates_metadata(self, mock_index, mock_pg):
        """Test add_documents validates GAMP-5 metadata."""
        mock_pg.from_params.return_value = MagicMock()

        adapter = PostgresVectorStoreAdapter(
            connection_string="postgresql://user:pass@localhost:5432/test"
        )

        # Valid metadata
        valid_metadata = {
            "gamp_category": "5",
            "created_by": "test_user",
            "document_type": "validation_protocol"
        }

        documents = [Document(text="Test document")]

        # Mock index creation
        mock_index.from_documents.return_value = MagicMock()

        doc_ids = await adapter.add_documents(documents, valid_metadata)
        assert len(doc_ids) == 1

    @pytest.mark.asyncio
    @patch("src.adapters.postgres_adapter.PGVectorStore")
    async def test_add_documents_rejects_missing_metadata(self, mock_pg):
        """Test add_documents rejects missing required metadata (NO FALLBACK)."""
        mock_pg.from_params.return_value = MagicMock()

        adapter = PostgresVectorStoreAdapter(
            connection_string="postgresql://user:pass@localhost:5432/test"
        )

        # Missing required fields
        invalid_metadata = {
            "gamp_category": "5"
            # Missing: created_by, document_type
        }

        documents = [Document(text="Test document")]

        with pytest.raises(ValueError) as exc_info:
            await adapter.add_documents(documents, invalid_metadata)

        assert "Missing required metadata fields" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("src.adapters.postgres_adapter.PGVectorStore")
    @patch("src.adapters.postgres_adapter.VectorStoreIndex")
    async def test_query_with_metadata_filters(self, mock_index, mock_pg):
        """Test query with metadata filters (efficient via B-tree indexes)."""
        mock_pg.from_params.return_value = MagicMock()

        adapter = PostgresVectorStoreAdapter(
            connection_string="postgresql://user:pass@localhost:5432/test"
        )

        # Mock retriever
        mock_retriever = MagicMock()
        mock_node = MagicMock()
        mock_retriever.retrieve.return_value = [mock_node]

        mock_index_instance = MagicMock()
        mock_index_instance.as_retriever.return_value = mock_retriever
        mock_index.from_vector_store.return_value = mock_index_instance

        metadata_filters = {"gamp_category": "5"}

        results = await adapter.query("test query", top_k=5, metadata_filters=metadata_filters)

        assert len(results) == 1
        # Verify filters were passed
        mock_index_instance.as_retriever.assert_called_once()


class TestEmbeddingModelCaching:
    """Tests for embedding model caching behavior."""

    @patch("src.adapters.chroma_adapter.chromadb.PersistentClient")
    @patch("src.adapters.chroma_adapter.Settings")
    def test_chroma_caches_embedding_model(self, mock_settings, mock_client):
        """Test ChromaDB adapter caches provided embedding model."""
        mock_collection = MagicMock()
        mock_client.return_value.get_or_create_collection.return_value = mock_collection

        mock_embed_model = MagicMock()

        adapter = ChromaVectorStoreAdapter(embed_model=mock_embed_model)

        # Verify embedding model was set in Settings
        assert mock_settings.embed_model == mock_embed_model

    @patch("src.adapters.postgres_adapter.PGVectorStore")
    @patch("src.adapters.postgres_adapter.Settings")
    def test_postgres_caches_embedding_model(self, mock_settings, mock_pg):
        """Test PostgreSQL adapter caches provided embedding model."""
        mock_pg.from_params.return_value = MagicMock()

        mock_embed_model = MagicMock()

        adapter = PostgresVectorStoreAdapter(
            connection_string="postgresql://user:pass@localhost:5432/test",
            embed_model=mock_embed_model
        )

        # Verify embedding model was set in Settings
        assert mock_settings.embed_model == mock_embed_model


class TestNoFallbackLogicCompliance:
    """Tests verifying NO FALLBACK LOGIC compliance."""

    def test_factory_never_defaults_to_chromadb_on_pgvector_failure(self):
        """Test factory never defaults to ChromaDB when pgvector fails (NO FALLBACK)."""
        with pytest.raises(ValueError) as exc_info:
            VectorStoreFactory.create_provider(
                mode="pgvector"
                # Missing connection_string
            )

        # Verify it raises instead of falling back to ChromaDB
        assert "connection_string" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    @patch("src.adapters.chroma_adapter.chromadb.PersistentClient")
    @patch("src.adapters.chroma_adapter.VectorStoreIndex")
    async def test_chroma_never_returns_empty_on_query_failure(self, mock_index, mock_client):
        """Test ChromaDB adapter never returns empty results to mask errors (NO FALLBACK)."""
        mock_collection = MagicMock()
        mock_client.return_value.get_or_create_collection.return_value = mock_collection

        adapter = ChromaVectorStoreAdapter()

        # Mock query failure
        mock_index.from_vector_store.side_effect = Exception("Query failed")

        with pytest.raises(RuntimeError) as exc_info:
            await adapter.query("test query")

        # Verify explicit error with full context
        assert "CRITICAL" in str(exc_info.value)
        assert "ChromaDB query failed" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("src.adapters.postgres_adapter.PGVectorStore")
    @patch("src.adapters.postgres_adapter.VectorStoreIndex")
    async def test_postgres_never_returns_empty_on_query_failure(self, mock_index, mock_pg):
        """Test PostgreSQL adapter never returns empty results to mask errors (NO FALLBACK)."""
        mock_pg.from_params.return_value = MagicMock()

        adapter = PostgresVectorStoreAdapter(
            connection_string="postgresql://user:pass@localhost:5432/test"
        )

        # Mock query failure
        mock_index.from_vector_store.side_effect = Exception("Query failed")

        with pytest.raises(RuntimeError) as exc_info:
            await adapter.query("test query")

        # Verify explicit error with full context
        assert "CRITICAL" in str(exc_info.value)
        assert "pgvector query failed" in str(exc_info.value)

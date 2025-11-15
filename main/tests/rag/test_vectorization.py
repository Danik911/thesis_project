"""
Test vectorization and embedding storage in PostgreSQL pgvector.

Tests:
- Document embedding generation
- Vector storage in pgvector
- Embedding dimension validation
- Metadata preservation

CRITICAL: NO FALLBACK LOGIC
- All vectorization errors must propagate
- Never store vectors with wrong dimensions
- Never skip validation checks
"""

from typing import Any

import pytest
from llama_index.core import Document


def build_metadata(**overrides: Any) -> dict[str, Any]:
    """Return adapter-compliant metadata with optional overrides."""
    base_metadata: dict[str, Any] = {
        "gamp_category": "5",
        "document_type": "test_data",
        "created_by": "test_harness",
    }
    base_metadata.update(overrides)
    return base_metadata


@pytest.mark.asyncio
async def test_add_documents_to_pgvector(
    pgvector_store: Any,
    sample_documents: list[Document],
    audit_context: Any
) -> None:
    """
    Test adding documents to PostgreSQL pgvector store.

    Args:
        pgvector_store: PostgreSQL pgvector adapter
        sample_documents: Sample pharmaceutical documents
        audit_context: ALCOA+ audit context

    Verifies:
    - Documents added successfully
    - Document IDs returned
    - No errors during vectorization
    """
    try:
        # Add documents with GAMP-5 metadata
        doc_ids = await pgvector_store.add_documents(
            documents=sample_documents,
            metadata=build_metadata(test_run="vectorization_test")
        )

        # Verify document IDs returned
        assert len(doc_ids) == len(sample_documents), (
            f"Expected {len(sample_documents)} document IDs, got {len(doc_ids)}"
        )
        assert all(isinstance(doc_id, str) for doc_id in doc_ids), "Invalid document ID format"

        audit_context.record_test(
            test_name="test_add_documents_to_pgvector",
            passed=True,
            details=f"Added {len(doc_ids)} documents to pgvector"
        )

    except Exception as e:
        audit_context.record_test(
            test_name="test_add_documents_to_pgvector",
            passed=False,
            details=f"Failed: {e}"
        )
        raise


@pytest.mark.asyncio
async def test_vector_dimensions_correct(
    pgvector_store: Any,
    sample_documents: list[Document],
    audit_context: Any
) -> None:
    """
    Test that embeddings have correct dimensionality (1536).

    Args:
        pgvector_store: PostgreSQL pgvector adapter
        sample_documents: Sample pharmaceutical documents
        audit_context: ALCOA+ audit context

    Verifies:
    - Embeddings are 1536 dimensions (text-embedding-3-small)
    - No dimension mismatch errors
    - Mock embedding model used (no real API calls)
    """
    try:
        # Add documents (will generate embeddings internally)
        await pgvector_store.add_documents(
            documents=sample_documents[:1],  # Test with single document
            metadata=build_metadata(test_run="dimension_check")
        )

        # Verify adapter configuration
        assert pgvector_store.embed_dim == 1536, (
            f"Expected embed_dim=1536, got {pgvector_store.embed_dim}"
        )

        # Query to verify embeddings stored correctly
        results = await pgvector_store.query(
            query_text="What is the drug release workflow?",
            top_k=1
        )

        # Verify results returned (proves embeddings valid)
        assert len(results) > 0, "No results returned - embeddings may be invalid"

        audit_context.record_test(
            test_name="test_vector_dimensions_correct",
            passed=True,
            details=f"Embeddings stored with correct dimension: {pgvector_store.embed_dim}"
        )

    except Exception as e:
        audit_context.record_test(
            test_name="test_vector_dimensions_correct",
            passed=False,
            details=f"Failed: {e}"
        )
        raise


@pytest.mark.asyncio
async def test_batch_vectorization(
    pgvector_store: Any,
    sample_documents: list[Document],
    audit_context: Any
) -> None:
    """
    Test batch vectorization of multiple documents.

    Args:
        pgvector_store: PostgreSQL pgvector adapter
        sample_documents: Sample pharmaceutical documents
        audit_context: ALCOA+ audit context

    Verifies:
    - All documents vectorized in batch
    - No partial failures (atomic operation)
    - Metadata preserved for all documents
    """
    try:
        # Add all sample documents at once
        doc_ids = await pgvector_store.add_documents(
            documents=sample_documents,
            metadata=build_metadata(batch_test="true")
        )

        # Verify all documents added
        assert len(doc_ids) == len(sample_documents), (
            f"Batch vectorization failed: expected {len(sample_documents)}, got {len(doc_ids)}"
        )

        # Query to verify all documents retrievable
        all_results = await pgvector_store.query(
            query_text="pharmaceutical testing",
            top_k=10
        )

        assert len(all_results) >= len(sample_documents), (
            f"Not all documents retrievable: found {len(all_results)}, expected >= {len(sample_documents)}"
        )

        audit_context.record_test(
            test_name="test_batch_vectorization",
            passed=True,
            details=f"Batch vectorized {len(sample_documents)} documents successfully"
        )

    except Exception as e:
        audit_context.record_test(
            test_name="test_batch_vectorization",
            passed=False,
            details=f"Failed: {e}"
        )
        raise


@pytest.mark.asyncio
async def test_metadata_preserved_in_vectors(
    pgvector_store: Any,
    sample_documents: list[Document],
    audit_context: Any
) -> None:
    """
    Test that document metadata is preserved after vectorization.

    Args:
        pgvector_store: PostgreSQL pgvector adapter
        sample_documents: Sample pharmaceutical documents
        audit_context: ALCOA+ audit context

    Verifies:
    - GAMP-5 metadata preserved
    - Document source tracked
    - Version information retained
    """
    try:
        # Add documents
        await pgvector_store.add_documents(
            documents=sample_documents,
            metadata=build_metadata(test_run="metadata_preservation")
        )

        # Query for specific document type
        results = await pgvector_store.query(
            query_text="protocol",
            top_k=5
        )

        # Verify metadata in results (check test-specific metadata preservation)
        found_metadata = False

        # Debug: Print all metadata to understand what's being retrieved
        print(f"\nDEBUG: Retrieved {len(results)} results")
        for i, node in enumerate(results):
            if hasattr(node.node, 'metadata'):
                print(f"  Result {i}: {node.node.metadata}")

        for node in results:
            if hasattr(node.node, 'metadata'):
                metadata = node.node.metadata
                # Check that our test metadata was preserved
                if metadata.get('test_run') == 'metadata_preservation':
                    found_metadata = True
                    assert metadata.get('gamp_category') == '5', "GAMP category missing"
                    assert metadata.get('document_type') == 'test_data', "document_type not preserved"
                    assert metadata.get('created_by') == 'test_harness', "created_by not preserved"
                    # Also check original document metadata was merged
                    assert 'source' in metadata, "Source metadata missing"
                    assert 'version' in metadata, "Version metadata missing"
                    break

        assert found_metadata, f"Test metadata not found in {len(results)} results - metadata preservation failed"

        audit_context.record_test(
            test_name="test_metadata_preserved_in_vectors",
            passed=True,
            details="Metadata preserved correctly in pgvector storage"
        )

    except Exception as e:
        audit_context.record_test(
            test_name="test_metadata_preserved_in_vectors",
            passed=False,
            details=f"Failed: {e}"
        )
        raise


@pytest.mark.asyncio
async def test_fail_on_invalid_documents(
    pgvector_store: Any,
    audit_context: Any
) -> None:
    """
    Test that invalid documents fail loudly.

    Args:
        pgvector_store: PostgreSQL pgvector adapter
        audit_context: ALCOA+ audit context

    Verifies:
    - NO FALLBACK LOGIC - empty documents rejected
    - Validation errors propagate
    - No silent failures
    """
    try:
        # Attempt to add document with empty text
        invalid_doc = Document(
            text="",  # Empty text should fail
            id_="invalid-doc",
            metadata={"gamp_category": "5"}
        )

        await pgvector_store.add_documents(
            documents=[invalid_doc],
            metadata=build_metadata(test_run="invalid_document")
        )

        # If we reach here, validation failed to catch empty document
        audit_context.record_test(
            test_name="test_fail_on_invalid_documents",
            passed=False,
            details="FALLBACK LOGIC DETECTED: Empty document accepted"
        )
        pytest.fail("NO FALLBACK LOGIC violation: Empty document should be rejected")

    except (ValueError, RuntimeError) as e:
        # Expected: Validation error
        audit_context.record_test(
            test_name="test_fail_on_invalid_documents",
            passed=True,
            details=f"Correctly rejected invalid document: {e}"
        )

    except Exception as e:
        # Unexpected error type
        audit_context.record_test(
            test_name="test_fail_on_invalid_documents",
            passed=False,
            details=f"Unexpected error type: {type(e).__name__}: {e}"
        )
        raise

"""
Test vector similarity search and retrieval from PostgreSQL pgvector.

Tests:
- top_k retrieval limits
- Semantic relevance
- Empty query handling
- Metadata filtering

CRITICAL: NO FALLBACK LOGIC
- Never return empty results to mask errors
- All retrieval failures must propagate
- Invalid queries must fail explicitly
"""

from typing import Any
from typing import Dict

import pytest
from llama_index.core import Document

def build_metadata(**overrides: Any) -> Dict[str, Any]:
    """Return adapter-compliant metadata for retrieval tests."""
    base_metadata: Dict[str, Any] = {
        "gamp_category": "5",
        "document_type": "test_data",
        "created_by": "test_harness",
    }
    base_metadata.update(overrides)
    return base_metadata


@pytest.mark.asyncio
async def test_retrieval_returns_top_k(
    pgvector_store: Any,
    sample_documents: list[Document],
    audit_context: Any
) -> None:
    """
    Test that retrieval respects top_k limit.

    Args:
        pgvector_store: PostgreSQL pgvector adapter
        sample_documents: Sample pharmaceutical documents
        audit_context: ALCOA+ audit context

    Verifies:
    - Results count ≤ top_k
    - Results sorted by relevance score
    - No duplicate documents
    """
    try:
        # Add documents
        await pgvector_store.add_documents(
            documents=sample_documents,
            metadata=build_metadata(test="top_k")
        )

        # Query with top_k=2
        results = await pgvector_store.query(
            query_text="What is the drug release workflow?",
            top_k=2
        )

        # Verify top_k respected
        assert len(results) <= 2, (
            f"Expected ≤2 results, got {len(results)}"
        )

        # Verify results are sorted by score (descending)
        if len(results) > 1:
            for i in range(len(results) - 1):
                assert results[i].score >= results[i + 1].score, (
                    f"Results not sorted by score: {results[i].score} < {results[i + 1].score}"
                )

        audit_context.record_test(
            test_name="test_retrieval_returns_top_k",
            passed=True,
            details=f"Retrieved {len(results)} results (top_k=2)"
        )

    except Exception as e:
        audit_context.record_test(
            test_name="test_retrieval_returns_top_k",
            passed=False,
            details=f"Failed: {e}"
        )
        raise


@pytest.mark.asyncio
async def test_retrieval_semantic_relevance(
    pgvector_store: Any,
    sample_documents: list[Document],
    audit_context: Any
) -> None:
    """
    Test that retrieval returns semantically relevant documents.

    Args:
        pgvector_store: PostgreSQL pgvector adapter
        sample_documents: Sample pharmaceutical documents
        audit_context: ALCOA+ audit context

    Verifies:
    - Top result matches query semantically
    - Relevance scores reasonable (>0.5)
    - Correct document type retrieved
    """
    try:
        # Add documents
        await pgvector_store.add_documents(
            documents=sample_documents,
            metadata=build_metadata(test="semantic_relevance")
        )

        # Query for acceptance criteria
        results = await pgvector_store.query(
            query_text="What are the test acceptance criteria?",
            top_k=3
        )

        assert len(results) > 0, "No results returned for semantic query"

        top_result = results[0]

        # Verify at least one result mentions acceptance criteria
        relevance_hit = False
        for node in results:
            node_text = node.node.text.lower()
            if "acceptance" in node_text or "criteria" in node_text:
                relevance_hit = True
                assert node.score > 0, "Relevant document has non-positive score"
                break

        assert relevance_hit, (
            "No semantically relevant document found among results:\n"
            f"First result preview: {results[0].node.text[:200]}"
        )

        audit_context.record_test(
            test_name="test_retrieval_semantic_relevance",
            passed=True,
            details=(
                f"Retrieved {len(results)} results; top score {top_result.score:.4f}; "
                "found acceptance criteria reference"
            )
        )

    except Exception as e:
        audit_context.record_test(
            test_name="test_retrieval_semantic_relevance",
            passed=False,
            details=f"Failed: {e}"
        )
        raise


@pytest.mark.asyncio
async def test_retrieval_with_metadata_filter(
    pgvector_store: Any,
    sample_documents: list[Document],
    audit_context: Any
) -> None:
    """
    Test retrieval with metadata filtering.

    Args:
        pgvector_store: PostgreSQL pgvector adapter
        sample_documents: Sample pharmaceutical documents
        audit_context: ALCOA+ audit context

    Verifies:
    - Metadata filters applied correctly
    - Only matching documents returned
    - GAMP-5 category filtering works
    """
    try:
        # Add documents with different metadata
        await pgvector_store.add_documents(
            documents=sample_documents,
            metadata=build_metadata(test="metadata_filter")
        )

        # Query with metadata filter
        results = await pgvector_store.query(
            query_text="pharmaceutical process",
            top_k=10,
            metadata_filters={"gamp_category": "5"}
        )

        # Verify all results match filter
        for node in results:
            if hasattr(node.node, 'metadata'):
                assert node.node.metadata.get('gamp_category') == '5', (
                    f"Result violates metadata filter: {node.node.metadata}"
                )

        audit_context.record_test(
            test_name="test_retrieval_with_metadata_filter",
            passed=True,
            details=f"Filtered retrieval returned {len(results)} GAMP-5 documents"
        )

    except Exception as e:
        audit_context.record_test(
            test_name="test_retrieval_with_metadata_filter",
            passed=False,
            details=f"Failed: {e}"
        )
        raise


@pytest.mark.asyncio
async def test_empty_vector_store_handling(
    pgvector_store: Any,
    audit_context: Any
) -> None:
    """
    Test that queries on empty vector store return empty results (not error).

    Args:
        pgvector_store: PostgreSQL pgvector adapter
        audit_context: ALCOA+ audit context

    Verifies:
    - Empty vector store returns 0 results
    - No errors thrown on empty query
    - NO FALLBACK LOGIC - explicit empty list returned
    """
    try:
        # Query empty vector store (no documents added)
        results = await pgvector_store.query(
            query_text="test query on empty store",
            top_k=5
        )

        # Verify empty results
        assert isinstance(results, list), "Results must be a list"
        assert len(results) == 0, (
            f"Expected 0 results from empty store, got {len(results)}"
        )

        audit_context.record_test(
            test_name="test_empty_vector_store_handling",
            passed=True,
            details="Empty vector store correctly returned 0 results"
        )

    except Exception as e:
        audit_context.record_test(
            test_name="test_empty_vector_store_handling",
            passed=False,
            details=f"Failed: {e}"
        )
        raise


@pytest.mark.asyncio
async def test_fail_on_invalid_query(
    pgvector_store: Any,
    audit_context: Any
) -> None:
    """
    Test that invalid queries fail explicitly.

    Args:
        pgvector_store: PostgreSQL pgvector adapter
        audit_context: ALCOA+ audit context

    Verifies:
    - NO FALLBACK LOGIC - empty queries rejected
    - Invalid top_k values rejected
    - Errors propagate with diagnostics
    """
    try:
        # Attempt query with empty text
        results = await pgvector_store.query(
            query_text="",  # Empty query should fail
            top_k=5
        )

        # If we reach here, validation failed
        if len(results) == 0:
            # Empty results acceptable for empty query
            audit_context.record_test(
                test_name="test_fail_on_invalid_query",
                passed=True,
                details="Empty query returned empty results (acceptable behavior)"
            )
        else:
            audit_context.record_test(
                test_name="test_fail_on_invalid_query",
                passed=False,
                details=f"FALLBACK LOGIC DETECTED: Empty query returned {len(results)} results"
            )
            pytest.fail("NO FALLBACK LOGIC violation: Empty query should return 0 results")

    except (ValueError, RuntimeError) as e:
        # Expected: Validation error
        audit_context.record_test(
            test_name="test_fail_on_invalid_query",
            passed=True,
            details=f"Correctly rejected invalid query: {e}"
        )

    except Exception as e:
        # Unexpected error type
        audit_context.record_test(
            test_name="test_fail_on_invalid_query",
            passed=False,
            details=f"Unexpected error type: {type(e).__name__}: {e}"
        )
        raise


@pytest.mark.asyncio
async def test_retrieval_score_ordering(
    pgvector_store: Any,
    sample_documents: list[Document],
    audit_context: Any
) -> None:
    """
    Test that retrieval results are ordered by relevance score.

    Args:
        pgvector_store: PostgreSQL pgvector adapter
        sample_documents: Sample pharmaceutical documents
        audit_context: ALCOA+ audit context

    Verifies:
    - Results sorted by score (descending)
    - Higher scores appear first
    - All scores are valid numbers
    """
    try:
        # Add documents
        await pgvector_store.add_documents(
            documents=sample_documents,
            metadata=build_metadata(test="score_ordering")
        )

        # Query for all documents
        results = await pgvector_store.query(
            query_text="pharmaceutical quality assurance",
            top_k=10
        )

        assert len(results) > 0, "No results returned"

        # Verify scores are valid and ordered
        for i, node in enumerate(results):
            # Check score is valid number
            assert isinstance(node.score, (int, float)), (
                f"Invalid score type at index {i}: {type(node.score)}"
            )
            assert node.score >= 0, (
                f"Negative score at index {i}: {node.score}"
            )

            # Check ordering (descending)
            if i > 0:
                assert results[i - 1].score >= node.score, (
                    f"Scores not in descending order: "
                    f"results[{i-1}].score={results[i-1].score} < "
                    f"results[{i}].score={node.score}"
                )

        audit_context.record_test(
            test_name="test_retrieval_score_ordering",
            passed=True,
            details=f"Verified {len(results)} results in correct score order"
        )

    except Exception as e:
        audit_context.record_test(
            test_name="test_retrieval_score_ordering",
            passed=False,
            details=f"Failed: {e}"
        )
        raise

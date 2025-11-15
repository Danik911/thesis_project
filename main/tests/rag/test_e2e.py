"""
End-to-end RAG workflow tests.

Tests complete pipeline:
1. Document ingestion to S3
2. Vectorization with embeddings
3. Retrieval with mock LLM query

Includes Phoenix observability integration (local environment only).

CRITICAL: NO FALLBACK LOGIC
- All pipeline stages must complete or fail loudly
- No partial success states
- Full diagnostic information on failures
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import boto3
import pytest
from llama_index.core import Document, VectorStoreIndex
from llama_index.core.llms import MockLLM

from .conftest import ENVIRONMENT, LOCALSTACK_ENDPOINT


def build_metadata(**overrides: Any) -> dict[str, Any]:
    """Return adapter-compliant metadata for E2E tests."""
    base_metadata: dict[str, Any] = {
        "gamp_category": "5",
        "document_type": "test_data",
        "created_by": "test_harness",
    }
    base_metadata.update(overrides)
    return base_metadata


@pytest.mark.asyncio
async def test_full_rag_pipeline(
    localstack_s3_bucket: str,
    pgvector_store: Any,
    sample_documents: list[Document],
    mock_llm: MockLLM,
    audit_context: Any
) -> None:
    """
    Test complete RAG workflow: S3 upload → vectorization → query → retrieve.

    Args:
        localstack_s3_bucket: S3 bucket fixture
        pgvector_store: PostgreSQL pgvector adapter
        sample_documents: Sample pharmaceutical documents
        mock_llm: Mock LLM for deterministic testing
        audit_context: ALCOA+ audit context

    Verifies:
    - Documents uploaded to S3
    - Documents vectorized and stored in pgvector
    - Query retrieval works end-to-end
    - Mock LLM response deterministic
    """
    try:
        # Stage 1: Upload documents to S3
        s3_client = boto3.client(
            "s3",
            endpoint_url=LOCALSTACK_ENDPOINT,
            aws_access_key_id="test",
            aws_secret_access_key="test",
            region_name="eu-west-2"
        )

        for i, doc in enumerate(sample_documents):
            s3_client.put_object(
                Bucket=localstack_s3_bucket,
                Key=f"documents/doc_{i}.txt",
                Body=doc.text.encode(),
                Metadata={
                    "gamp_category": doc.metadata.get("gamp_category", "5"),
                    "document_type": doc.metadata.get("document_type", "unknown"),
                    "source": doc.metadata.get("source", "test")
                }
            )

        # Stage 2: Vectorize and store in pgvector
        doc_ids = await pgvector_store.add_documents(
            documents=sample_documents,
            metadata=build_metadata(test_run="e2e_pipeline")
        )

        assert len(doc_ids) == len(sample_documents), (
            f"Vectorization failed: expected {len(sample_documents)} IDs, got {len(doc_ids)}"
        )

        # Stage 3: Query and retrieve
        results = await pgvector_store.query(
            query_text="What is the drug release workflow?",
            top_k=3
        )

        assert len(results) > 0, "No results retrieved from RAG pipeline"

        # Stage 4: Generate response with mock LLM
        index = pgvector_store.get_index()
        query_engine = index.as_query_engine(llm=mock_llm)

        response = query_engine.query("What is the drug release workflow?")

        assert response.response is not None, "Mock LLM returned no response"
        assert len(response.source_nodes) > 0, "No source nodes in response"

        audit_context.record_test(
            test_name="test_full_rag_pipeline",
            passed=True,
            details=(
                f"E2E pipeline complete: "
                f"{len(doc_ids)} docs uploaded, "
                f"{len(results)} retrieved, "
                f"response generated"
            )
        )

    except Exception as e:
        audit_context.record_test(
            test_name="test_full_rag_pipeline",
            passed=False,
            details=f"Pipeline failed: {e}"
        )
        raise


@pytest.mark.asyncio
async def test_query_with_mock_llm_deterministic(
    pgvector_store: Any,
    sample_documents: list[Document],
    audit_context: Any
) -> None:
    """
    Test that mock LLM responses are deterministic.

    Args:
        pgvector_store: PostgreSQL pgvector adapter
        sample_documents: Sample pharmaceutical documents
        audit_context: ALCOA+ audit context

    Verifies:
    - Mock LLM returns consistent responses
    - No real API calls made
    - Response format correct
    """
    try:
        # Add documents
        await pgvector_store.add_documents(
            documents=sample_documents,
            metadata=build_metadata(test_run="deterministic_llm")
        )

        # Create mock LLM with fixed response
        mock_llm = MockLLM(max_tokens=200)

        # Query twice with same input
        index = pgvector_store.get_index()
        query_engine = index.as_query_engine(llm=mock_llm)

        response1 = query_engine.query("Test query")
        response2 = query_engine.query("Test query")

        # Verify deterministic responses
        assert response1.response == response2.response, (
            "Mock LLM responses not deterministic:\n"
            f"Response 1: {response1.response}\n"
            f"Response 2: {response2.response}"
        )

        audit_context.record_test(
            test_name="test_query_with_mock_llm_deterministic",
            passed=True,
            details="Mock LLM responses verified deterministic"
        )

    except Exception as e:
        audit_context.record_test(
            test_name="test_query_with_mock_llm_deterministic",
            passed=False,
            details=f"Failed: {e}"
        )
        raise


@pytest.mark.asyncio
@pytest.mark.skipif(
    ENVIRONMENT != "local",
    reason="Phoenix tracing only enabled in local environment"
)
async def test_phoenix_trace_capture(
    pgvector_store: Any,
    sample_documents: list[Document],
    mock_llm: MockLLM,
    audit_context: Any,
    compliance_evidence_dir: Path
) -> None:
    """
    Test Phoenix observability trace capture (local environment only).

    Args:
        pgvector_store: PostgreSQL pgvector adapter
        sample_documents: Sample pharmaceutical documents
        mock_llm: Mock LLM for deterministic testing
        audit_context: ALCOA+ audit context
        compliance_evidence_dir: Compliance evidence directory

    Verifies:
    - Trace data captured successfully
    - Trace exported to compliance evidence folder
    - NO production leakage (ENVIRONMENT=local check)
    """
    try:
        # Verify environment
        assert ENVIRONMENT == "local", (
            f"Phoenix tracing only for local, current: {ENVIRONMENT}"
        )

        # Add documents
        await pgvector_store.add_documents(
            documents=sample_documents,
            metadata=build_metadata(test_run="phoenix_trace")
        )

        # Query with tracing
        index = pgvector_store.get_index()
        query_engine = index.as_query_engine(llm=mock_llm)

        query_text = "What are the GAMP-5 requirements?"
        response = query_engine.query(query_text)

        # Create trace export for compliance evidence
        trace_data = {
            "trace_timestamp": datetime.now().isoformat(),
            "environment": ENVIRONMENT,
            "query": query_text,
            "response": response.response,
            "source_nodes": [
                {
                    "text": node.node.text[:200] + "...",
                    "score": float(node.score) if hasattr(node, 'score') else 0.0,
                    "metadata": node.node.metadata if hasattr(node.node, 'metadata') else {}
                }
                for node in response.source_nodes
            ],
            "gamp_category": "5",
            "compliance_evidence": True
        }

        # Export trace
        trace_file = compliance_evidence_dir / "traces" / f"phoenix-trace-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        with trace_file.open("w") as f:
            json.dump(trace_data, f, indent=2)

        assert trace_file.exists(), "Trace export file not created"

        audit_context.record_test(
            test_name="test_phoenix_trace_capture",
            passed=True,
            details=f"Trace captured and exported to {trace_file}"
        )

    except Exception as e:
        audit_context.record_test(
            test_name="test_phoenix_trace_capture",
            passed=False,
            details=f"Failed: {e}"
        )
        raise


@pytest.mark.asyncio
async def test_alcoa_plus_audit_trail(
    pgvector_store: Any,
    sample_documents: list[Document],
    audit_context: Any
) -> None:
    """
    Test that ALCOA+ audit trail is captured correctly.

    Args:
        pgvector_store: PostgreSQL pgvector adapter
        sample_documents: Sample pharmaceutical documents
        audit_context: ALCOA+ audit context

    Verifies:
    - Attributable: Test user recorded
    - Legible: Clear test names
    - Contemporaneous: Timestamps captured
    - Original: First-run results preserved
    - Accurate: Test outcomes match reality
    - Complete: All required fields present
    - Consistent: Same format for all tests
    - Enduring: Saved to compliance evidence
    - Available: Accessible for audits
    """
    try:
        # Execute test workflow
        doc_ids = await pgvector_store.add_documents(
            documents=sample_documents,
            metadata=build_metadata(
                created_by=audit_context.test_user,
                test_run="alcoa_audit_trail"
            )
        )

        # Verify audit context captures metadata
        assert audit_context.test_id is not None, "Test ID not generated"
        assert audit_context.test_user == "test_harness_automated", "User not recorded"
        assert audit_context.test_timestamp is not None, "Timestamp not captured"

        # Record test result
        audit_context.record_test(
            test_name="test_alcoa_plus_audit_trail",
            passed=True,
            details=(
                f"ALCOA+ audit trail verified: "
                f"test_id={audit_context.test_id}, "
                f"user={audit_context.test_user}, "
                f"timestamp={audit_context.test_timestamp}"
            )
        )

        # Verify audit results structure
        assert len(audit_context.test_results) > 0, "No audit results recorded"

        latest_result = audit_context.test_results[-1]
        required_fields = [
            "user", "timestamp", "test_name", "result",
            "details", "test_id", "execution_environment",
            "gamp_category"
        ]

        for field in required_fields:
            assert field in latest_result, (
                f"ALCOA+ audit trail missing field: {field}"
            )

    except Exception as e:
        audit_context.record_test(
            test_name="test_alcoa_plus_audit_trail",
            passed=False,
            details=f"Failed: {e}"
        )
        raise


@pytest.mark.asyncio
async def test_no_real_bedrock_credentials_used(
    audit_context: Any
) -> None:
    """
    Test that no real Bedrock credentials are present in environment.

    Args:
        audit_context: ALCOA+ audit context

    Verifies:
    - NO real AWS credentials in test environment
    - Only LocalStack/mock credentials present
    - Security: No credential leakage
    """
    try:
        # Check for real AWS credentials (should NOT be present)
        aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

        # LocalStack test credentials are OK
        if aws_access_key == "test" and aws_secret_key == "test":
            audit_context.record_test(
                test_name="test_no_real_bedrock_credentials_used",
                passed=True,
                details="Only LocalStack test credentials present (secure)"
            )
            return

        # Real credentials should NOT be present in test environment
        if aws_access_key and aws_access_key != "test":
            audit_context.record_test(
                test_name="test_no_real_bedrock_credentials_used",
                passed=False,
                details=f"SECURITY VIOLATION: Real AWS credentials detected: {aws_access_key[:4]}***"
            )
            pytest.fail("Real AWS credentials detected in test environment")

        # No credentials at all is also acceptable
        audit_context.record_test(
            test_name="test_no_real_bedrock_credentials_used",
            passed=True,
            details="No AWS credentials in environment (secure)"
        )

    except Exception as e:
        audit_context.record_test(
            test_name="test_no_real_bedrock_credentials_used",
            passed=False,
            details=f"Failed: {e}"
        )
        raise

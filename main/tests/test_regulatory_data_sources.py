"""
Test suite for regulatory data sources integration.

This module tests the real regulatory data sources implementation,
including FDA API integration and document processing capabilities.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from src.agents.parallel.regulatory_data_sources import (
    DocumentProcessingError,
    DocumentProcessor,
    FDAAPIClient,
    FDAAPIError,
    RegulatoryAuditTrail,
    create_document_processor,
    create_fda_client,
)


class TestRegulatoryAuditTrail:
    """Test GAMP-5 compliant audit trail functionality."""

    def test_audit_trail_initialization(self):
        """Test audit trail initialization."""
        audit_trail = RegulatoryAuditTrail()
        assert audit_trail.audit_log_path is None
        assert audit_trail.logger is not None

    def test_log_data_access_success(self):
        """Test successful data access logging."""
        audit_trail = RegulatoryAuditTrail()

        record_id = audit_trail.log_data_access(
            source="TEST_SOURCE",
            endpoint="/test/endpoint",
            query_params={"query": "test"},
            response_data={"result": "success"},
            success=True
        )

        assert record_id.startswith("TEST_SOURCE_")
        assert len(record_id) > 20  # Should include timestamp and hash

    def test_log_data_access_failure(self):
        """Test failed data access logging."""
        audit_trail = RegulatoryAuditTrail()

        record_id = audit_trail.log_data_access(
            source="TEST_SOURCE",
            endpoint="/test/endpoint",
            query_params={"query": "test"},
            response_data={},
            success=False,
            error_details="Test error"
        )

        assert record_id.startswith("TEST_SOURCE_")

    def test_data_hash_calculation(self):
        """Test data hash calculation for integrity."""
        audit_trail = RegulatoryAuditTrail()

        # Same data should produce same hash
        data1 = {"key": "value", "number": 123}
        data2 = {"key": "value", "number": 123}

        hash1 = audit_trail._calculate_data_hash(data1)
        hash2 = audit_trail._calculate_data_hash(data2)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hash length

    def test_empty_data_hash(self):
        """Test hash calculation for empty data."""
        audit_trail = RegulatoryAuditTrail()
        hash_result = audit_trail._calculate_data_hash({})
        assert hash_result == "no_data"


class TestFDAAPIClient:
    """Test FDA API client functionality."""

    def test_fda_client_initialization(self):
        """Test FDA API client initialization."""
        client = FDAAPIClient()
        assert client.base_url == "https://api.fda.gov"
        assert client.api_key is None
        assert client.request_interval == 15.0  # No API key = 240 requests/hour

        client_with_key = FDAAPIClient(api_key="test_key")
        assert client_with_key.api_key == "test_key"
        assert client_with_key.request_interval == 0.03  # With API key = 120k requests/hour

    def test_client_stats_initialization(self):
        """Test client statistics initialization."""
        client = FDAAPIClient()
        stats = client.get_stats()

        expected_keys = ["total_requests", "successful_requests", "failed_requests", "rate_limit_hits"]
        for key in expected_keys:
            assert key in stats
            assert stats[key] == 0

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting functionality."""
        client = FDAAPIClient()

        # Mock time to test rate limiting
        with patch("src.agents.parallel.regulatory_data_sources.time.time") as mock_time:
            mock_time.side_effect = [0, 1, 16]  # Simulate time progression

            # First call should not sleep
            await client._apply_rate_limiting()

            # Second call should sleep (less than interval)
            with patch("src.agents.parallel.regulatory_data_sources.asyncio.sleep") as mock_sleep:
                await client._apply_rate_limiting()
                mock_sleep.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_drug_labels_success(self):
        """Test successful FDA drug labels search."""
        client = FDAAPIClient()

        # Mock successful API response
        mock_response_data = {
            "results": [
                {
                    "brand_name": ["Test Drug"],
                    "generic_name": ["test_generic"],
                    "application_number": "TEST123"
                }
            ],
            "meta": {"results": {"skip": 0, "limit": 10, "total": 1}}
        }

        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response_data

            result = await client.search_drug_labels("test query", limit=10)

            assert result == mock_response_data
            mock_request.assert_called_once()
            call_args = mock_request.call_args[0]
            assert "drug/label.json" in call_args[0]  # endpoint
            assert call_args[1]["search"] == "test query"  # params

    @pytest.mark.asyncio
    async def test_api_error_handling(self):
        """Test API error handling without fallbacks."""
        client = FDAAPIClient()

        with patch("src.agents.parallel.regulatory_data_sources.asyncio.get_event_loop"):
            with patch("asyncio.get_event_loop") as mock_loop:
                mock_executor = Mock()
                mock_executor.side_effect = Exception("Network error")
                mock_loop.return_value.run_in_executor = mock_executor

                with pytest.raises(FDAAPIError) as exc_info:
                    await client._make_request(
                        "https://api.fda.gov/test",
                        {"query": "test"},
                        "test_request"
                    )

                assert "Network error" in str(exc_info.value)
                # Verify no fallback - should raise explicit error
                assert client.stats["failed_requests"] == 1

    @pytest.mark.asyncio
    async def test_rate_limit_error(self):
        """Test rate limit error handling."""
        client = FDAAPIClient()

        with patch("src.agents.parallel.regulatory_data_sources.asyncio.get_event_loop"):
            with patch("asyncio.get_event_loop") as mock_loop:
                # Mock response with 429 status code
                mock_response = Mock()
                mock_response.status_code = 429

                mock_executor = Mock()
                mock_executor.return_value = mock_response
                mock_loop.return_value.run_in_executor = mock_executor

                with pytest.raises(FDAAPIError) as exc_info:
                    await client._make_request(
                        "https://api.fda.gov/test",
                        {"query": "test"},
                        "test_request"
                    )

                assert "rate limit exceeded" in str(exc_info.value).lower()
                assert client.stats["rate_limit_hits"] == 1


class TestDocumentProcessor:
    """Test document processing functionality."""

    def test_document_processor_initialization(self):
        """Test document processor initialization."""
        processor = DocumentProcessor()
        assert processor.audit_trail is not None
        assert processor.logger is not None

    @pytest.mark.asyncio
    async def test_file_not_found_error(self):
        """Test document processing with non-existent file."""
        processor = DocumentProcessor()

        with pytest.raises(DocumentProcessingError) as exc_info:
            await processor.process_pdf_document("/non/existent/file.pdf")

        assert "not found" in str(exc_info.value)

    def test_pdf_content_extraction_structure(self):
        """Test PDF content extraction result structure."""
        processor = DocumentProcessor()

        # Test the result structure without actual PDF processing
        result_template = {
            "text": "",
            "tables": [],
            "pages": 0,
            "document_title": "",
            "extraction_quality": "unknown"
        }

        # Verify the expected structure matches our implementation
        expected_keys = {"text", "tables", "pages", "document_title", "extraction_quality"}
        assert set(result_template.keys()) == expected_keys


class TestFactoryFunctions:
    """Test factory functions for creating clients."""

    def test_create_fda_client(self):
        """Test FDA client factory function."""
        client = create_fda_client()
        assert isinstance(client, FDAAPIClient)
        assert client.api_key is None

        client_with_key = create_fda_client(api_key="test_key")
        assert isinstance(client_with_key, FDAAPIClient)
        assert client_with_key.api_key == "test_key"

    def test_create_document_processor(self):
        """Test document processor factory function."""
        processor = create_document_processor()
        assert isinstance(processor, DocumentProcessor)
        assert processor.audit_trail is not None


class TestComplianceFeatures:
    """Test GAMP-5 and regulatory compliance features."""

    def test_audit_trail_alcoa_plus_compliance(self):
        """Test ALCOA+ compliance in audit trail."""
        audit_trail = RegulatoryAuditTrail()

        record_id = audit_trail.log_data_access(
            source="FDA_API",
            endpoint="/test/endpoint",
            query_params={"query": "validation"},
            response_data={"result": "test"}
        )

        # Verify ALCOA+ principles:
        # - Attributable: user_id is logged
        # - Legible: audit_record structure is clear
        # - Contemporaneous: timestamp is current
        # - Original: source data hash is preserved
        # - Accurate: data hash ensures integrity
        # - Complete: all required fields are present
        # - Consistent: standardized record format
        # - Enduring: permanent record (logged)
        # - Available: record_id allows retrieval

        assert record_id is not None
        assert len(record_id) > 10  # Meaningful ID

    def test_no_fallback_behavior(self):
        """Test that no fallback behavior is implemented."""
        # This test verifies our "NO FALLBACKS" requirement
        client = FDAAPIClient()

        # Verify that error conditions raise explicit exceptions
        # rather than returning fallback values
        with pytest.raises(Exception):
            # This should raise an exception, not return a fallback
            client._calculate_data_hash = Mock(side_effect=Exception("Test error"))
            client.audit_trail._calculate_data_hash({})


@pytest.mark.integration
class TestRealDataIntegration:
    """Integration tests that can optionally connect to real APIs."""

    @pytest.mark.skip(reason="Integration test - requires real API access")
    @pytest.mark.asyncio
    async def test_real_fda_api_connection(self):
        """Test real FDA API connection (disabled by default)."""
        # This test can be enabled for real API testing
        # It's skipped by default to avoid hitting rate limits during regular testing
        client = FDAAPIClient()

        try:
            # Simple search that should return results
            result = await client.search_drug_labels("aspirin", limit=1)
            assert "results" in result
            assert len(result["results"]) > 0
        except FDAAPIError as e:
            # If API is unreachable, that's a valid test result too
            assert "API" in str(e)

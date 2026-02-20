"""Tests for LIMS API router endpoints."""

import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from main.api.lims_router import router as lims_router
from main.src.lims.job_store import _jobs


@pytest.fixture(autouse=True)
def clear_job_store():
    """Clear the in-memory job store between router tests."""
    _jobs.clear()
    yield
    _jobs.clear()


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(lims_router, prefix="/lims")

    @app.get("/health")
    async def health() -> dict:
        return {"status": "healthy"}

    return TestClient(app)


@pytest.fixture
def mock_lims_config() -> MagicMock:
    """Mock LIMSConfig with required attributes."""
    config = MagicMock()
    config.llamaextract_api_key = "test-key"
    config.extraction_mode = "balanced"
    config.openrouter_api_key = ""  # No OpenRouter key -> skip MDA generation
    config.openrouter_model = "test/model"
    config.chromadb_path = "./chroma_db_lims"
    config.upload_dir = "./uploads/lims"
    config.output_dir = "./output/lims"
    config.standards_collection = "lims_standards"
    config.calculations_collection = "calculation_patterns"
    config.classification_mode = "hybrid"
    config.classification_confidence_threshold = 0.6
    return config


@pytest.fixture
def mock_pipeline_result():
    """Mock result from TwoLayerPipeline.run()."""
    return {
        "classification": {
            "test_type": "IDENTITY",
            "confidence": 0.95,
            "method": "filename_pattern",
            "matched_keywords": [],
        },
        "mda_template": {
            "analyses": [{"name": "SITE_IDENTITY", "analysis_type": "ID"}],
            "components": [],
            "calc_variables": [],
            "calculations": [],
        },
        "provenance": {"fields": {}},
        "conflicts": [],
        "stage_details": [
            {"stage": "CLASSIFY", "duration_ms": 10, "summary": "test", "details": {}},
        ],
        "pipeline_type": "two_layer",
        "test_type": "IDENTITY",
        "extraction_trace": {"model": "test"},
        "raw_extraction": {},
        "validated": True,
        "validation_error": None,
    }


class TestExtractEndpoint:
    def test_rejects_non_pdf(self, client: TestClient):
        response = client.post(
            "/lims/extract",
            files={"file": ("test.txt", b"not a pdf", "text/plain")},
        )
        assert response.status_code == 400
        assert "PDF" in response.json()["detail"]

    def test_rejects_empty_file(self, client: TestClient):
        response = client.post(
            "/lims/extract",
            files={"file": ("test.pdf", b"", "application/pdf")},
        )
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    def test_rejects_oversized_file(self, client: TestClient):
        big_content = b"x" * (51 * 1024 * 1024)  # 51 MB
        response = client.post(
            "/lims/extract",
            files={"file": ("big.pdf", big_content, "application/pdf")},
        )
        assert response.status_code == 400
        assert "large" in response.json()["detail"].lower()

    @patch("main.src.lims.pipeline.TwoLayerPipeline.run", new_callable=AsyncMock)
    @patch("main.src.lims.config.get_lims_config")
    def test_extract_uses_pipeline(
        self,
        mock_get_config,
        mock_pipeline_run: AsyncMock,
        client: TestClient,
        mock_lims_config,
        mock_pipeline_result,
    ):
        """POST /extract now uses TwoLayerPipeline instead of direct extraction."""
        mock_get_config.return_value = mock_lims_config
        mock_pipeline_run.return_value = mock_pipeline_result

        response = client.post(
            "/lims/extract",
            files={"file": ("AND_ACS_DYE.pdf", b"%PDF-1.4 fake", "application/pdf")},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["filename"] == "AND_ACS_DYE.pdf"
        assert payload["job_id"] is not None
        assert payload["pipeline_type"] == "two_layer"
        assert payload["test_type"] == "IDENTITY"
        assert payload["classification"]["test_type"] == "IDENTITY"
        assert "provenance" in payload

    @patch("main.src.lims.pipeline.TwoLayerPipeline.run", new_callable=AsyncMock)
    @patch("main.src.lims.config.get_lims_config")
    def test_extract_pipeline_error(
        self,
        mock_get_config,
        mock_pipeline_run: AsyncMock,
        client: TestClient,
        mock_lims_config,
    ):
        """Pipeline error returns 500 with diagnostic detail."""
        mock_get_config.return_value = mock_lims_config
        mock_pipeline_run.side_effect = ValueError("LlamaExtract API unavailable")

        response = client.post(
            "/lims/extract",
            files={"file": ("test.pdf", b"%PDF-1.4 fake", "application/pdf")},
        )
        assert response.status_code == 500
        assert "Pipeline failed" in response.json()["detail"]
        assert "LlamaExtract API unavailable" in response.json()["detail"]


class TestClassifyEndpoint:
    def test_rejects_non_pdf(self, client: TestClient):
        response = client.post(
            "/lims/classify",
            files={"file": ("test.txt", b"not a pdf", "text/plain")},
        )
        assert response.status_code == 400
        assert "PDF" in response.json()["detail"]

    def test_rejects_empty_file(self, client: TestClient):
        response = client.post(
            "/lims/classify",
            files={"file": ("test.pdf", b"", "application/pdf")},
        )
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    @patch("main.src.lims.focused_extractor.extract_text_from_pdf")
    def test_classify_returns_result(
        self,
        mock_extract_text,
        client: TestClient,
    ):
        """POST /classify returns classification result."""
        mock_extract_text.return_value = (
            "ACS Dye-Binding Identity Test Method\n"
            "Visual Inspection procedures\n"
        )

        response = client.post(
            "/lims/classify",
            files={
                "file": (
                    "AND_ACS_DYE.pdf",
                    b"%PDF-1.4 fake",
                    "application/pdf",
                )
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert "test_type" in payload
        assert "confidence" in payload
        assert "method" in payload
        assert payload["test_type"] == "IDENTITY"

    @patch("main.src.lims.focused_extractor.extract_text_from_pdf")
    def test_classify_text_extraction_failure(
        self,
        mock_extract_text,
        client: TestClient,
    ):
        """PDF text extraction failure -> 400."""
        mock_extract_text.side_effect = ValueError("No extractable text")

        response = client.post(
            "/lims/classify",
            files={"file": ("bad.pdf", b"%PDF corrupt", "application/pdf")},
        )
        assert response.status_code == 400
        assert "text extraction failed" in response.json()["detail"].lower()


class TestTemplateEndpoint:
    def test_get_identity_template(self, client: TestClient):
        """GET /template/IDENTITY returns template skeleton."""
        response = client.get("/lims/template/IDENTITY")
        assert response.status_code == 200
        payload = response.json()
        assert payload["test_type"] == "IDENTITY"
        assert "mda_template" in payload
        assert "variable_fields" in payload
        assert "fixed_fields" in payload
        assert payload["analysis_count"] == 3
        assert payload["component_count"] == 25

    def test_get_template_case_insensitive(self, client: TestClient):
        """Test type is case-insensitive."""
        response = client.get("/lims/template/identity")
        assert response.status_code == 200
        assert response.json()["test_type"] == "IDENTITY"

    def test_get_template_invalid_type(self, client: TestClient):
        """Invalid test type returns 400."""
        response = client.get("/lims/template/INVALID")
        assert response.status_code == 400
        assert "Invalid test type" in response.json()["detail"]

    def test_get_template_other_rejected(self, client: TestClient):
        """TestType.OTHER has no template -> 400."""
        response = client.get("/lims/template/OTHER")
        assert response.status_code == 400
        assert "no curated template" in response.json()["detail"].lower()


class TestHealthEndpoint:
    def test_health_check(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200


@pytest.mark.integration
class TestExtractIntegration:
    def test_extract_real_pdf(self, client: TestClient):
        """Integration test — requires LIMS_LLAMAEXTRACT_API_KEY."""
        if not os.getenv("LIMS_LLAMAEXTRACT_API_KEY"):
            pytest.skip("LIMS_LLAMAEXTRACT_API_KEY not set")

        pdf_path = Path("demo_data/AND_ACS_AQ126-LAB-2349.pdf")
        if not pdf_path.exists():
            pytest.skip("demo PDF not found")

        with pdf_path.open("rb") as f:
            response = client.post(
                "/lims/extract",
                files={"file": ("test.pdf", f, "application/pdf")},
            )

        assert response.status_code == 200
        data = response.json()
        assert "pipeline_type" in data
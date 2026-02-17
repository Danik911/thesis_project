"""Tests for LIMS API router endpoints."""

import os
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from main.api.lims_router import router as lims_router


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(lims_router, prefix="/lims")

    @app.get("/health")
    async def health() -> dict:
        return {"status": "healthy"}

    return TestClient(app)


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

    @patch(
        "main.api.lims_router.asyncio.to_thread",
        new_callable=AsyncMock,
    )
    @patch("main.src.lims.config.get_lims_config")
    def test_extract_returns_result(
        self,
        mock_get_config,
        mock_to_thread: AsyncMock,
        client: TestClient,
        mock_extraction_result,
    ):
        mock_get_config.return_value = object()
        mock_to_thread.return_value = {
            "raw_extraction": mock_extraction_result,
            "validated": False,
            "validation_error": "test",
            "mda_template": None,
        }

        response = client.post(
            "/lims/extract",
            files={"file": ("test.pdf", b"%PDF-1.4 fake", "application/pdf")},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["filename"] == "test.pdf"
        assert payload["raw_extraction"]["analyses"][0]["name"] == "AND_ACS_DYE"


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
        assert "raw_extraction" in data
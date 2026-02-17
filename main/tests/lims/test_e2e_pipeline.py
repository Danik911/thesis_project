"""End-to-end pipeline tests for LIMS mandatory HITL flow.

These integration tests require real API keys and are skipped by default
when credentials are not present.
"""

from pathlib import Path

import os
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from main.api.lims_router import router as lims_router
from main.src.lims.job_store import _jobs


@pytest.fixture(autouse=True)
def clear_job_store() -> None:
    """Clear in-memory LIMS jobs between tests."""
    _jobs.clear()
    yield
    _jobs.clear()


@pytest.fixture
def client() -> TestClient:
    """Create a minimal FastAPI app with LIMS routes for integration tests."""
    app = FastAPI()
    app.include_router(lims_router, prefix="/lims")

    @app.get("/health")
    async def health() -> dict:
        return {"status": "healthy"}

    return TestClient(app)


def _require_lims_keys() -> None:
    """Skip integration tests when required API keys are missing."""
    if not os.getenv("LIMS_LLAMAEXTRACT_API_KEY"):
        pytest.skip("LIMS_LLAMAEXTRACT_API_KEY not set")
    if not os.getenv("LIMS_OPENROUTER_API_KEY"):
        pytest.skip("LIMS_OPENROUTER_API_KEY not set")


@pytest.mark.integration
class TestLIMSPipelineE2E:
    """Full pipeline: extract -> status -> chat -> approve -> export."""

    def test_full_pipeline(self, client: TestClient) -> None:
        _require_lims_keys()

        pdf_path = Path("demo_data/AND_ACS_DYE-LAB-2499.pdf")
        if not pdf_path.exists():
            pytest.skip(f"Demo PDF not found: {pdf_path}")

        with pdf_path.open("rb") as pdf_file:
            extract_response = client.post(
                "/lims/extract",
                files={"file": (pdf_path.name, pdf_file, "application/pdf")},
            )

        assert extract_response.status_code == 200
        extract_data = extract_response.json()
        job_id = extract_data["job_id"]
        assert job_id

        status_response = client.get(f"/lims/status/{job_id}")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["status"] == "PENDING_REVIEW"
        assert status_data["mda_template"] is not None

        chat_response = client.post(
            "/lims/chat",
            json={
                "job_id": job_id,
                "message": "Summarize the analyses in this MDA.",
            },
        )
        assert chat_response.status_code == 200
        chat_data = chat_response.json()
        assert "response" in chat_data
        assert len(chat_data["response"]) > 0

        export_before_approval = client.get(f"/lims/export/{job_id}")
        assert export_before_approval.status_code == 403
        assert "APPROVED" in export_before_approval.json()["detail"]

        approve_response = client.post(f"/lims/approve/{job_id}")
        assert approve_response.status_code == 200
        assert approve_response.json()["status"] == "APPROVED"

        export_after_approval = client.get(f"/lims/export/{job_id}")
        assert export_after_approval.status_code == 200
        assert "spreadsheetml" in export_after_approval.headers.get("content-type", "")
        assert len(export_after_approval.content) > 100


@pytest.mark.integration
class TestExportWithoutApprovalBlocked:
    """Verify no path exists to export without explicit human approval."""

    def test_fresh_job_cannot_export(self, client: TestClient) -> None:
        _require_lims_keys()

        pdf_path = Path("demo_data/AND_ACS_AQ126-LAB-2349.pdf")
        if not pdf_path.exists():
            pytest.skip(f"Demo PDF not found: {pdf_path}")

        with pdf_path.open("rb") as pdf_file:
            extract_response = client.post(
                "/lims/extract",
                files={"file": (pdf_path.name, pdf_file, "application/pdf")},
            )

        assert extract_response.status_code == 200
        job_id = extract_response.json()["job_id"]

        export_response = client.get(f"/lims/export/{job_id}")
        assert export_response.status_code == 403

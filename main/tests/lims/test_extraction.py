"""Tests for LIMS PDF extraction wrapper."""

import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from main.src.lims.config import LIMSConfig
from main.src.lims.pdf_extractor import _build_staging_payload, _compute_extraction_quality_metrics, extract_mda_from_pdf
from main.tests.lims.path_helpers import resolve_demo_pdf


def _install_fake_llama_modules(monkeypatch: pytest.MonkeyPatch, payload: dict) -> None:
    class FakeExtractConfig:
        pass

    class FakeRun:
        def __init__(self, data: dict) -> None:
            self.data = data
            self.id = "run_test_123"
            self.status = "completed"

    class FakeAgent:
        def __init__(self, data: dict) -> None:
            self._data = data

        def extract(self, file_path: str) -> FakeRun:
            assert Path(file_path).exists()
            return FakeRun(self._data)

    class FakeLlamaExtract:
        def __init__(self, api_key: str) -> None:
            self.api_key = api_key

        def create_agent(self, name: str, data_schema: object, config: object) -> FakeAgent:
            assert name.startswith("mda-")
            assert data_schema is not None
            assert config is not None
            return FakeAgent(payload)

    monkeypatch.setitem(
        sys.modules,
        "llama_cloud_services",
        SimpleNamespace(LlamaExtract=FakeLlamaExtract),
    )
    monkeypatch.setitem(
        sys.modules,
        "llama_cloud",
        SimpleNamespace(ExtractConfig=FakeExtractConfig),
    )


class TestExtractionWrapper:
    def test_staging_payload_fills_defaults_for_null_fields(self) -> None:
        raw_payload = {
            "analyses": [
                {
                    "name": "AND_ACS_DYE",
                    "analysis_type": "ID",
                    "group_name": None,
                }
            ],
            "components": [
                {
                    "analysis": "AND_ACS_DYE",
                    "component_name": "TEST_COMPONENT",
                    "order_number": 1,
                    "result_type": None,
                    "uses_instrument": None,
                    "auto_calc": None,
                    "reportable": None,
                    "optional": None,
                    "allow_out_of_range": None,
                }
            ],
            "calc_variables": None,
            "calculations": None,
        }

        staged = _build_staging_payload(raw_payload)
        metrics = _compute_extraction_quality_metrics(staged)

        assert staged["analyses"][0]["group_name"] == ""
        assert staged["components"][0]["uses_instrument"] is False
        assert staged["components"][0]["auto_calc"] is False
        assert staged["components"][0]["reportable"] is True
        assert staged["calc_variables"] == []
        assert staged["calculations"] == []
        assert metrics["critical_fields_scanned"] > 0
        assert metrics["critical_null_ratio"] < 1.0

    def test_extract_returns_validated_template(
        self,
        monkeypatch: pytest.MonkeyPatch,
        sample_mda_template,
    ) -> None:
        payload = sample_mda_template.model_dump()
        _install_fake_llama_modules(monkeypatch, payload)

        result = extract_mda_from_pdf(
            pdf_content=b"%PDF-1.4 fake",
            filename="AND_ACS_DYE-LAB-2499.pdf",
            config=LIMSConfig(llamaextract_api_key="test-key", extraction_mode="balanced"),
        )

        assert result["validated"] is True
        assert result["validation_error"] is None
        assert result["mda_template"] is not None
        assert result["normalized_extraction"] is not None
        assert result["extraction_trace"]["provider"] == "llama_cloud_services"
        assert result["extraction_trace"]["run_id"] == "run_test_123"
        assert result["extraction_trace"]["run_status"] == "completed"
        assert result["extraction_trace"]["pdf_size_bytes"] == len(b"%PDF-1.4 fake")
        assert result["raw_extraction"]["analyses"][0]["name"] == "AND_ACS_DYE"

    def test_extract_preserves_raw_on_validation_failure(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        invalid_payload = {
            "analyses": [],
            "components": [
                {
                    "analysis": "AND_MISSING",
                    "component_name": "BAD_REF",
                    "order_number": 1,
                    "result_type": "N",
                }
            ],
            "calc_variables": [],
            "calculations": [],
        }
        _install_fake_llama_modules(monkeypatch, invalid_payload)

        result = extract_mda_from_pdf(
            pdf_content=b"%PDF-1.4 fake",
            filename="bad.pdf",
            config=LIMSConfig(llamaextract_api_key="test-key", extraction_mode="balanced"),
        )

        assert result["validated"] is False
        assert result["validation_error"] is not None
        assert result["mda_template"] is None
        assert result["normalized_extraction"] is not None
        assert result["extraction_trace"]["client"] == "LlamaExtract"
        assert result["extraction_trace"]["agent_name"].startswith("mda-")
        assert result["raw_extraction"]["components"][0]["component_name"] == "BAD_REF"

    def test_extract_rejects_unimplemented_extraction_api(self) -> None:
        with pytest.raises(NotImplementedError):
            extract_mda_from_pdf(
                pdf_content=b"%PDF-1.4 fake",
                filename="AND_ACS_DYE-LAB-2499.pdf",
                config=LIMSConfig(
                    llamaextract_api_key="test-key",
                    extraction_mode="balanced",
                    extraction_api="llamaparse_v2",
                ),
            )


@pytest.mark.integration
def test_extract_real_pdf_integration() -> None:
    """Integration test — requires LIMS_LLAMAEXTRACT_API_KEY."""
    api_key = os.getenv("LIMS_LLAMAEXTRACT_API_KEY")
    if not api_key:
        pytest.skip("LIMS_LLAMAEXTRACT_API_KEY not set")

    pdf_path = resolve_demo_pdf("AND_ACS_AQ126-LAB-2349.pdf")
    if pdf_path is None:
        pytest.skip("demo PDF not found in demo_data/testing_data_ground_truth or demo_data/data")

    result = extract_mda_from_pdf(
        pdf_content=pdf_path.read_bytes(),
        filename=pdf_path.name,
        config=LIMSConfig(llamaextract_api_key=api_key, extraction_mode="balanced"),
    )

    assert "raw_extraction" in result
    assert isinstance(result["raw_extraction"], dict)
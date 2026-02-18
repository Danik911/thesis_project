"""Tests for LIMS PDF extraction wrapper."""

import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from main.src.lims.config import LIMSConfig
from main.src.lims.pdf_extractor import extract_mda_from_pdf


def _install_fake_llama_modules(monkeypatch: pytest.MonkeyPatch, payload: dict) -> None:
    class FakeExtractConfig:
        pass

    class FakeRun:
        def __init__(self, data: dict) -> None:
            self.data = data

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

    pdf_path = Path("demo_data/AND_ACS_AQ126-LAB-2349.pdf")
    if not pdf_path.exists():
        pytest.skip("demo PDF not found")

    result = extract_mda_from_pdf(
        pdf_content=pdf_path.read_bytes(),
        filename=pdf_path.name,
        config=LIMSConfig(llamaextract_api_key=api_key, extraction_mode="balanced"),
    )

    assert "raw_extraction" in result
    assert isinstance(result["raw_extraction"], dict)
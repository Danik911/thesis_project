"""Tests for LIMS configuration loading and validation."""

import pytest

from main.src.lims.config import LIMSConfig, get_lims_config


def test_lims_config_l10_defaults() -> None:
    config = LIMSConfig(llamaextract_api_key="test-key")
    assert config.classification_mode == "hybrid"
    assert config.classification_confidence_threshold == 0.8
    assert config.standards_collection == "lims_standards"
    assert config.calculations_collection == "calculation_patterns"


def test_lims_config_rejects_invalid_classification_mode() -> None:
    with pytest.raises(ValueError, match="LIMS_CLASSIFICATION_MODE"):
        LIMSConfig(
            llamaextract_api_key="test-key",
            classification_mode="invalid_mode",
        )


@pytest.mark.parametrize("threshold", [-0.1, 1.1])
def test_lims_config_rejects_out_of_range_threshold(threshold: float) -> None:
    with pytest.raises(ValueError, match="LIMS_CLASSIFICATION_CONFIDENCE_THRESHOLD"):
        LIMSConfig(
            llamaextract_api_key="test-key",
            classification_confidence_threshold=threshold,
        )


def test_get_lims_config_reads_new_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LIMS_LLAMAEXTRACT_API_KEY", "test-key")
    monkeypatch.setenv("LIMS_CLASSIFICATION_MODE", "rules")
    monkeypatch.setenv("LIMS_CLASSIFICATION_CONFIDENCE_THRESHOLD", "0.9")
    monkeypatch.setenv("LIMS_STANDARDS_COLLECTION", "standards_custom")
    monkeypatch.setenv("LIMS_CALCULATIONS_COLLECTION", "calc_custom")

    config = get_lims_config()

    assert config.classification_mode == "rules"
    assert config.classification_confidence_threshold == 0.9
    assert config.standards_collection == "standards_custom"
    assert config.calculations_collection == "calc_custom"
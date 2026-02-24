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
    monkeypatch.setenv("LIMS_QUERY_AUGMENTATION_ENABLED", "true")
    monkeypatch.setenv("LIMS_QUERY_AUGMENTATION_MAX_QUERIES", "5")
    monkeypatch.setenv("LIMS_METADATA_BOOST_ENABLED", "true")
    monkeypatch.setenv("LIMS_PRIORITY_SHEET_BOOST", "0.25")
    monkeypatch.setenv("LIMS_TOKEN_MATCH_BOOST", "0.3")
    monkeypatch.setenv("LIMS_RETRIEVAL_QUALITY_GATE_ENABLED", "true")
    monkeypatch.setenv("LIMS_RETRIEVAL_MIN_RESULTS", "3")
    monkeypatch.setenv("LIMS_RETRIEVAL_MAX_DISTANCE", "1.1")
    monkeypatch.setenv("LIMS_RETRIEVAL_MIN_AVG_TOKEN_OVERLAP", "2.0")
    monkeypatch.setenv("LIMS_RETRIEVAL_MIN_METHOD_MATCH_RATIO", "0.6")
    monkeypatch.setenv("LIMS_LOW_CONFIDENCE_REVIEW_THRESHOLD", "0.8")

    config = get_lims_config()

    assert config.classification_mode == "rules"
    assert config.classification_confidence_threshold == 0.9
    assert config.standards_collection == "standards_custom"
    assert config.calculations_collection == "calc_custom"
    assert config.query_augmentation_enabled is True
    assert config.query_augmentation_max_queries == 5
    assert config.metadata_boost_enabled is True
    assert config.priority_sheet_boost == 0.25
    assert config.token_match_boost == 0.3
    assert config.retrieval_quality_gate_enabled is True
    assert config.retrieval_min_results == 3
    assert config.retrieval_max_distance == 1.1
    assert config.retrieval_min_avg_token_overlap == 2.0
    assert config.retrieval_min_method_match_ratio == 0.6
    assert config.low_confidence_review_threshold == 0.8
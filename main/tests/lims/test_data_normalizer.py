"""Unit tests for LIMS extraction normalization."""

import copy

import pytest

from main.src.lims.data_normalizer import (
    apply_lims_defaults,
    coerce_boolean_strings,
    coerce_numeric_strings,
    normalize_analysis_names,
    normalize_component_name,
    normalize_extraction,
    normalize_symbols,
)


def test_normalize_symbols_replaces_unicode_variants() -> None:
    text = "\u00b5L \u2265 10\u00b0C \u00b1 2\u00b0C"
    normalized = normalize_symbols(text)
    assert "uL" in normalized
    assert ">=" in normalized
    assert "deg C" in normalized
    assert "+/-" in normalized


def test_normalize_component_name_applies_lims_convention() -> None:
    assert normalize_component_name(" Absorbance-595.1 ") == "ABSORBANCE_595_1"


def test_normalize_analysis_names_uppercases_and_underscores() -> None:
    analyses = [{"name": "and acs-dye meta"}]
    normalized = normalize_analysis_names(analyses)
    assert normalized[0]["name"] == "AND_ACS_DYE_META"


def test_numeric_and_boolean_coercion() -> None:
    record = {
        "minimum": "0.50",
        "places": "2",
        "auto_calc": "Y",
        "reportable": "false",
    }

    coerced = coerce_numeric_strings(record)
    coerced = coerce_boolean_strings(coerced)

    assert coerced["minimum"] == 0.5
    assert coerced["places"] == 2
    assert coerced["auto_calc"] is True
    assert coerced["reportable"] is False


def test_apply_lims_defaults_for_k_and_units() -> None:
    payload = {
        "components": [
            {
                "analysis": "AND_ACS_DYE",
                "component_name": "DYE_VOLUME_EXPECTED",
                "result_type": "K",
                "units": None,
            }
        ]
    }

    updated = apply_lims_defaults(payload)
    component = updated["components"][0]
    assert component["auto_calc"] is True
    assert component["units"] == ""


def test_normalize_extraction_does_not_mutate_input() -> None:
    raw = {
        "analyses": [{"name": "and acs dye"}],
        "components": [
            {
                "analysis": "and acs dye",
                "component_name": "Absorbance 595",
                "result_type": "N",
                "minimum": "0.5",
                "uses_instrument": "True",
                "units": "\u00b5L",
            }
        ],
        "calc_variables": [],
        "calculations": [],
    }
    raw_before = copy.deepcopy(raw)

    normalized = normalize_extraction(raw)

    assert raw == raw_before
    component = normalized["components"][0]
    assert normalized["analyses"][0]["name"] == "AND_ACS_DYE"
    assert component["component_name"] == "ABSORBANCE_595"
    assert component["minimum"] == 0.5
    assert component["uses_instrument"] is True
    assert component["units"] == "uL"


def test_normalize_extraction_rejects_non_dict() -> None:
    with pytest.raises(TypeError):
        normalize_extraction(["not", "a", "dict"])  # type: ignore[arg-type]

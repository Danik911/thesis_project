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
from main.src.lims.mda_schema import MDATemplate


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


def test_normalize_semantic_aliases_make_payload_valid() -> None:
    raw = {
        "analyses": [
            {
                "name": "Dye-Binding Identity Test for Absorbable Collagen Sponge (ACS)",
                "version": 12,
                "group_name": "Quality Control Analytical",
                "active": None,
                "reported_name": None,
                "common_name": None,
                "analysis_type": "identity test",
                "description": "Example",
            }
        ],
        "components": [
            {
                "analysis": "Dye-Binding Identity Test for Absorbable Collagen Sponge (ACS)",
                "component_name": "Package and Label",
                "order_number": None,
                "result_type": "visual inspection",
                "units": None,
                "auto_calc": False,
                "uses_instrument": False,
                "reportable": True,
                "optional": False,
                "allow_out_of_range": False,
            },
            {
                "analysis": "Dye-Binding Identity Test for Absorbable Collagen Sponge (ACS)",
                "component_name": "Absorbance at 540 nm",
                "order_number": None,
                "result_type": "measurement",
                "units": "AU",
                "auto_calc": False,
                "uses_instrument": True,
                "instrument_group": "UV_VIS_SPEC",
                "reportable": True,
                "optional": False,
                "allow_out_of_range": False,
            },
            {
                "analysis": "Dye-Binding Identity Test for Absorbable Collagen Sponge (ACS)",
                "component_name": "Dye Concentration (mM)",
                "order_number": None,
                "result_type": "calculated",
                "units": "NONE",
                "auto_calc": False,
                "uses_instrument": False,
                "reportable": True,
                "optional": False,
                "allow_out_of_range": False,
            },
        ],
        "calc_variables": [
            {
                "analysis": "Dye-Binding Identity Test for Absorbable Collagen Sponge (ACS)",
                "component": "Dye Concentration (mM)",
                "name": "V_ABS",
                "reference_type": None,
                "return_value": "concentration (mM)",
                "scope": "per reagent preparation",
                "function": "Calculate using absorbance",
                "reference_component": "Absorbance at 540 nm",
            }
        ],
        "calculations": [
            {
                "analysis": "Dye-Binding Identity Test for Absorbable Collagen Sponge (ACS)",
                "component": "Dye Concentration (mM)",
                "description": "Calculate concentration",
                "source_code": "RESULT = (V_ABS / 37600) × 1000 × 100",
                "calculation_type": "concentration calculation",
                "variables_used": ["V_ABS"],
            }
        ],
    }

    normalized = normalize_extraction(raw)
    validated = MDATemplate.model_validate(normalized)

    assert validated.analyses[0].analysis_type == "ID"
    assert validated.components[0].result_type == "L"
    assert validated.components[0].list_key in {"YES_NO_2", "CONFORM"}
    assert validated.components[1].result_type == "N"
    assert validated.components[2].result_type == "K"
    assert validated.calc_variables[0].reference_type == "C"
    assert validated.calc_variables[0].return_value == "S"
    assert validated.calc_variables[0].scope == "CR"
    assert validated.calc_variables[0].function == "ENTRY"
    assert validated.calculations[0].calculation_type == "FORMULA"

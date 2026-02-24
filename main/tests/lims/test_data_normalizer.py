"""Unit tests for LIMS extraction normalization."""

import copy

import pytest

from main.src.lims.data_normalizer import (
    _build_analysis_name_map,
    _infer_analysis_type_from_name,
    _normalize_analysis_refs,
    _resolve_analysis_name,
    apply_lims_defaults,
    coerce_boolean_strings,
    coerce_numeric_strings,
    normalize_analysis_names,
    normalize_component_name,
    normalize_extraction,
    normalize_symbols,
    sanitize_component_numeric_bounds,
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


def test_sanitize_component_numeric_bounds_clears_pass_for_qualitative_types() -> None:
    components = [
        {"component_name": "VISUAL_CHECK", "result_type": "L", "minimum": "Pass", "maximum": "N/A"},
        {"component_name": "COMMENT", "result_type": "T", "minimum": "--", "maximum": ""},
        {"component_name": "DATE_FIELD", "result_type": "D", "minimum": "Pass", "maximum": "Fail"},
    ]

    sanitize_component_numeric_bounds(components)

    for component in components:
        assert component["minimum"] is None
        assert component["maximum"] is None


def test_sanitize_component_numeric_bounds_does_not_mask_numeric_types() -> None:
    components = [
        {"component_name": "ABSORBANCE", "result_type": "N", "minimum": "Pass", "maximum": "2.0"},
        {"component_name": "CALC_VALUE", "result_type": "K", "minimum": "N/A", "maximum": "Fail"},
    ]

    sanitize_component_numeric_bounds(components)

    assert components[0]["minimum"] == "Pass"
    assert components[1]["minimum"] == "N/A"


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


# ---------------------------------------------------------------------------
# _resolve_analysis_name: deterministic exact-match tests
# ---------------------------------------------------------------------------

class TestResolveAnalysisName:
    """Tests for deterministic exact-match analysis name resolution."""

    def _make_map(self, names: list[str]) -> dict[str, str]:
        """Build analysis_name_map from a list of canonical names."""
        analyses = [{"name": n} for n in names]
        return _build_analysis_name_map(analyses)

    def test_exact_match(self) -> None:
        name_map = self._make_map(["SITE_IDENTITY_CTL", "SITE_IDENTITY_META"])
        assert _resolve_analysis_name("SITE_IDENTITY_CTL", name_map) == "SITE_IDENTITY_CTL"

    def test_prefix_single_match_returns_none(self) -> None:
        name_map = self._make_map(["DYE_BINDING_TEST", "SOMETHING_ELSE"])
        assert _resolve_analysis_name("DYE_BINDING", name_map) is None

    def test_prefix_multiple_matches_returns_none(self) -> None:
        name_map = self._make_map(["SITE_IDENTITY_CTL", "SITE_IDENTITY_META"])
        result = _resolve_analysis_name("SITE_IDENTITY", name_map)
        assert result is None

    def test_substring_single_match_returns_none(self) -> None:
        name_map = self._make_map([
            "DYE_BINDING_IDENTITY_TEST_FOR_ABSORBABLE_COLLAGEN_SPONGE_(ACS)"
        ])
        result = _resolve_analysis_name("IDENTITY_TEST_FOR_ABSORBABLE", name_map)
        assert result is None

    def test_no_match_returns_none(self) -> None:
        name_map = self._make_map(["SITE_IDENTITY_CTL", "SITE_IDENTITY_META"])
        assert _resolve_analysis_name("COMPLETELY_DIFFERENT", name_map) is None

    def test_case_insensitive_exact_match_via_alias_map(self) -> None:
        name_map = self._make_map(["SITE_IDENTITY_CTL"])
        result = _resolve_analysis_name("site_identity_ctl", name_map)
        assert result == "SITE_IDENTITY_CTL"


class TestNormalizeAnalysisRefsDeterministic:
    """Integration tests for deterministic exact-match normalization."""

    def test_truncated_site_identity_is_not_resolved(self) -> None:
        """Truncated refs remain unchanged under exact-match-only policy."""
        analyses = [
            {
                "name": "DYE_BINDING_IDENTITY_TEST_FOR_ABSORBABLE_COLLAGEN_SPONGE_(ACS)",
                "version": 12,
                "analysis_type": "ID",
                "active": True,
            },
            {
                "name": "SITE_IDENTITY_CTL",
                "version": 1,
                "analysis_type": "QC_SAMPLES",
                "active": True,
            },
            {
                "name": "SITE_IDENTITY_META",
                "version": 1,
                "analysis_type": "QC_SAMPLES",
                "active": True,
            },
        ]
        components = [
            {
                "analysis": "SITE_IDENTITY",
                "component_name": "PACKAGE_DOUBLE_LAYERED_AND_SEALED",
                "order_number": 1,
                "result_type": "L",
                "reportable": True,
            },
            {
                "analysis": "DYE_BINDING_IDENTITY_TEST_FOR_ABSORBABLE_COLLAGEN_SPONGE_(ACS)",
                "component_name": "ABSORBANCE_540",
                "order_number": 2,
                "result_type": "N",
                "reportable": True,
            },
        ]

        analysis_name_map = _build_analysis_name_map(analyses)
        _normalize_analysis_refs(components, analysis_name_map)

        # The truncated ref should remain unchanged (deterministic exact-match only)
        assert components[0]["analysis"] == "SITE_IDENTITY"
        # The already-valid ref should remain unchanged
        assert components[1]["analysis"] == (
            "DYE_BINDING_IDENTITY_TEST_FOR_ABSORBABLE_COLLAGEN_SPONGE_(ACS)"
        )

    def test_full_pipeline_with_truncated_ref_fails_validation(self) -> None:
        """End-to-end: unresolved truncated ref should fail validation loudly."""
        raw = {
            "analyses": [
                {
                    "name": "Site Identity CTL",
                    "version": 1,
                    "analysis_type": "control",
                    "active": True,
                },
                {
                    "name": "Site Identity META",
                    "version": 1,
                    "analysis_type": "metadata",
                    "active": True,
                },
            ],
            "components": [
                {
                    "analysis": "Site Identity",
                    "component_name": "Package: Double layered and sealed?",
                    "order_number": 1,
                    "result_type": "list",
                    "reportable": True,
                },
            ],
            "calc_variables": [],
            "calculations": [],
        }

        normalized = normalize_extraction(raw)

        with pytest.raises(Exception):
            MDATemplate.model_validate(normalized)


# ---------------------------------------------------------------------------
# _infer_analysis_type_from_name: type inference from analysis name
# ---------------------------------------------------------------------------


class TestInferAnalysisTypeFromName:
    """Tests for inferring analysis_type from keywords in the analysis name."""

    def test_identity_keyword(self) -> None:
        assert _infer_analysis_type_from_name("SITE_IDENTITY") == "ID"

    def test_dye_binding_keyword(self) -> None:
        result = _infer_analysis_type_from_name(
            "DYE_BINDING_IDENTITY_TEST_FOR_ABSORBABLE_COLLAGEN_SPONGE_(ACS)"
        )
        assert result == "ID"

    def test_ctl_suffix(self) -> None:
        assert _infer_analysis_type_from_name("SITE_IDENTITY_CTL") == "QC_SAMPLES"

    def test_meta_suffix(self) -> None:
        assert _infer_analysis_type_from_name("SITE_IDENTITY_META") == "QC_SAMPLES"

    def test_assay_keyword(self) -> None:
        assert _infer_analysis_type_from_name("POTENCY_ASSAY") == "ASY"

    def test_impurity_keyword(self) -> None:
        assert _infer_analysis_type_from_name("RELATED_IMPURITIES") == "IMP"

    def test_physical_keyword(self) -> None:
        assert _infer_analysis_type_from_name("PHYSICAL_APPEARANCE") == "PHYS"

    def test_no_keyword_returns_none(self) -> None:
        assert _infer_analysis_type_from_name("RANDOM_TEST_XYZ") is None

    def test_empty_string_returns_none(self) -> None:
        assert _infer_analysis_type_from_name("") is None

    def test_normalize_analysis_type_uses_inference_when_none(self) -> None:
        """When analysis_type is None but name contains keywords, type is inferred."""
        analyses = [
            {
                "name": "Dye-Binding Identity Test for ACS",
                "analysis_type": None,
            }
        ]
        normalized = normalize_analysis_names(analyses)
        assert normalized[0]["analysis_type"] == "ID"

    def test_normalize_analysis_type_none_no_keyword_stays_none(self) -> None:
        """When analysis_type is None and no keywords match, stays None."""
        analyses = [
            {
                "name": "RANDOM_TEST_XYZ",
                "analysis_type": None,
            }
        ]
        normalized = normalize_analysis_names(analyses)
        assert normalized[0]["analysis_type"] is None

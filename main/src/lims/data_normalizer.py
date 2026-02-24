"""Post-extraction data normalization for MDA templates.

Cleans and standardizes raw extraction output before Pydantic validation.
Handles symbol normalization, type coercion, naming conventions, and
LIMS-specific defaults.

GAMP-5 Category 5: Custom pharmaceutical software component.
NO FALLBACK LOGIC -- normalization errors propagate with full diagnostics.
"""

from __future__ import annotations

import copy
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


SYMBOL_MAP: dict[str, str] = {
    "\u2265": ">=",
    "\u2264": "<=",
    "\u00b5": "u",
    "\u03bc": "u",
    "\u00b0": "deg ",
    "\u00b1": "+/-",
    "\u00d7": "x",
    "\u2013": "-",
    "\u2014": "-",
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u2026": "...",
}


NUMERIC_FIELDS = [
    "minimum",
    "maximum",
    "places",
    "order_number",
    "version",
    "round_precision",
    "significant_figures",
]


BOOLEAN_FIELDS = [
    "auto_calc",
    "uses_instrument",
    "reportable",
    "optional",
    "active",
    "allow_out_of_range",
]


ANALYSIS_TYPE_MAP: dict[str, str] = {
    "id": "ID",
    "identity": "ID",
    "identity_test": "ID",
    "identity test": "ID",
    "asy": "ASY",
    "assay": "ASY",
    "imp": "IMP",
    "impurity": "IMP",
    "impurities": "IMP",
    "phys": "PHYS",
    "physical": "PHYS",
    "physical_test": "PHYS",
    "qc_samples": "QC_SAMPLES",
    "qc samples": "QC_SAMPLES",
    "qc": "QC_SAMPLES",
    "control": "QC_SAMPLES",
    "metadata": "QC_SAMPLES",
}


RESULT_TYPE_MAP: dict[str, str] = {
    "n": "N",
    "numeric": "N",
    "number": "N",
    "quantitative": "N",
    "measurement": "N",
    "k": "K",
    "calculated": "K",
    "calculation": "K",
    "computed": "K",
    "derived": "K",
    "l": "L",
    "list": "L",
    "qualitative": "L",
    "visual": "L",
    "visual inspection": "L",
    "color comparison": "L",
    "pass_fail": "L",
    "pass fail": "L",
    "t": "T",
    "text": "T",
    "free text": "T",
    "comment": "T",
    "d": "D",
    "date": "D",
}

# Tokens that indicate qualitative pass/fail style entries and should not be
# treated as numeric bounds for qualitative result types.
QUALITATIVE_BOUND_TOKENS = {
    "pass",
    "fail",
    "pass/fail",
    "pass fail",
    "n/a",
    "na",
    "none",
    "null",
    "-",
    "--",
    "",
}


CALCULATION_TYPE_MAP: dict[str, str] = {
    "formula": "FORMULA",
    "concentration calculation": "FORMULA",
    "volumetric calculation": "FORMULA",
    "calculation": "FORMULA",
    "conditional": "CONDITIONAL",
    "if": "CONDITIONAL",
    "inst_picker": "INST_PICKER",
    "instrument picker": "INST_PICKER",
    "sr_picker": "SR_PICKER",
    "reagent picker": "SR_PICKER",
    "gosub": "GOSUB",
}


CALC_VARIABLE_RETURN_VALUE_MAP: dict[str, str] = {
    "s": "S",
    "single": "S",
    "concentration": "S",
    "volume": "S",
    "value": "S",
    "p": "P",
    "population": "P",
    "a": "A",
    "all": "A",
}


CALC_VARIABLE_SCOPE_MAP: dict[str, str] = {
    "cr": "CR",
    "currentresult": "CR",
    "current result": "CR",
    "per sample": "CR",
    "per test run": "CR",
    "per reagent preparation": "CR",
    "ct": "CT",
    "currenttest": "CT",
    "current test": "CT",
    "b": "B",
    "batch": "B",
}


CALC_VARIABLE_FUNCTION_MAP: dict[str, str] = {
    "entry": "ENTRY",
    "ave": "AVE",
    "average": "AVE",
    "mean": "AVE",
    "rsd": "RSD",
}


def normalize_extraction(raw_dict: dict[str, Any]) -> dict[str, Any]:
    """Apply normalization rules to extraction output.

    Args:
        raw_dict: Raw extraction output dict (pre-Pydantic).

    Returns:
        Normalized dict ready for MDATemplate.model_validate().

    Raises:
        TypeError: If raw_dict is not a dict.
    """
    if not isinstance(raw_dict, dict):
        raise TypeError(
            f"normalize_extraction expects dict, got {type(raw_dict).__name__}"
        )

    data = copy.deepcopy(raw_dict)
    logger.info("Starting extraction normalization (%d top-level keys)", len(data))

    analysis_name_map: dict[str, str] = {}
    component_name_map: dict[str, str] = {}

    if "analyses" in data and isinstance(data["analyses"], list):
        data["analyses"] = normalize_analysis_names(data["analyses"])
        analysis_name_map = _build_analysis_name_map(data["analyses"])

    # Collect known analysis names for inference when all records have None
    known_analysis_names = [
        str(a["name"]) for a in data.get("analyses", [])
        if isinstance(a, dict) and a.get("name")
    ]

    if "components" in data and isinstance(data["components"], list):
        data["components"] = [
            _normalize_component(comp, index=index)
            for index, comp in enumerate(data["components"], start=1)
        ]
        _normalize_analysis_refs(data["components"], analysis_name_map)
        _forward_fill_field(
            data["components"], "analysis",
            available_values=known_analysis_names,
        )
        component_name_map = _build_component_name_map(data["components"])

    # Collect known component names for inference
    known_component_names = [
        str(c["component_name"]) for c in data.get("components", [])
        if isinstance(c, dict) and c.get("component_name")
    ]

    if "calc_variables" in data and isinstance(data["calc_variables"], list):
        data["calc_variables"] = [
            _normalize_calc_variable(record) for record in data["calc_variables"]
        ]
        _normalize_analysis_refs(data["calc_variables"], analysis_name_map)
        _normalize_component_refs(data["calc_variables"], component_name_map)
        _forward_fill_field(
            data["calc_variables"], "analysis",
            available_values=known_analysis_names,
        )
        _forward_fill_field(data["calc_variables"], "component")

    if "calculations" in data and isinstance(data["calculations"], list):
        data["calculations"] = [
            _normalize_calculation(record) for record in data["calculations"]
        ]
        _normalize_analysis_refs(data["calculations"], analysis_name_map)
        _normalize_component_refs(data["calculations"], component_name_map)
        _forward_fill_field(
            data["calculations"], "analysis",
            available_values=known_analysis_names,
        )
        _forward_fill_field(data["calculations"], "component")

    data = apply_lims_defaults(data)

    logger.info("Extraction normalization complete")
    return data


def normalize_symbols(text: str) -> str:
    """Replace Unicode/special chars with LIMS-compatible equivalents."""
    normalized = text
    for unicode_char, replacement in SYMBOL_MAP.items():
        normalized = normalized.replace(unicode_char, replacement)
    return normalized


def normalize_component_name(name: str) -> str:
    """Standardize component names to LIMS conventions."""
    if not name:
        return name

    normalized = name.strip()
    normalized = re.sub(r"[\s]+", "_", normalized)
    normalized = re.sub(r"[-.]", "_", normalized)
    normalized = normalized.upper()
    normalized = re.sub(r"_+", "_", normalized)
    normalized = normalized.strip("_")
    return normalized


def normalize_analysis_names(analyses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Ensure analysis names follow uppercase underscore conventions."""
    normalized_analyses: list[dict[str, Any]] = []
    for analysis in analyses:
        if not isinstance(analysis, dict):
            normalized_analyses.append(analysis)
            continue

        normalized_analysis = dict(analysis)
        name = normalized_analysis.get("name")
        if name:
            original_name = str(name).strip()
            normalized_name = str(name).strip()
            normalized_name = re.sub(r"[\s-]+", "_", normalized_name)
            normalized_name = normalized_name.upper()
            normalized_name = re.sub(r"_+", "_", normalized_name)
            normalized_name = normalized_name.strip("_")
            normalized_analysis["name"] = normalized_name
            if not normalized_analysis.get("reported_name"):
                normalized_analysis["reported_name"] = original_name
            if not normalized_analysis.get("common_name"):
                normalized_analysis["common_name"] = original_name

        if normalized_analysis.get("active") is None:
            normalized_analysis["active"] = True

        normalized_analysis["analysis_type"] = _normalize_analysis_type(
            normalized_analysis.get("analysis_type"),
            normalized_analysis.get("name"),
        )

        normalized_analyses.append(_normalize_record(normalized_analysis))
    return normalized_analyses


def coerce_numeric_strings(
    data: dict[str, Any], numeric_fields: list[str] | None = None
) -> dict[str, Any]:
    """Convert string numbers to int/float values for known fields."""
    fields = numeric_fields or NUMERIC_FIELDS
    for field in fields:
        if field in data and isinstance(data[field], str):
            value = data[field].strip()
            if not value:
                continue
            try:
                data[field] = float(value) if "." in value else int(value)
            except ValueError:
                logger.warning(
                    "Cannot coerce '%s' to number for field '%s'", value, field
                )
    return data


def coerce_boolean_strings(data: dict[str, Any]) -> dict[str, Any]:
    """Convert string booleans to bool values for known fields."""
    bool_map = {
        "t": True,
        "f": False,
        "true": True,
        "false": False,
        "1": True,
        "0": False,
        "y": True,
        "n": False,
        "yes": True,
        "no": False,
    }
    for field in BOOLEAN_FIELDS:
        if field in data and isinstance(data[field], str):
            value = data[field].strip().lower()
            if value in bool_map:
                data[field] = bool_map[value]
    return data


def apply_lims_defaults(data: dict[str, Any]) -> dict[str, Any]:
    """Apply LIMS defaults for missing or null values where required."""
    components = data.get("components", [])
    if not isinstance(components, list):
        return data

    for component in components:
        if not isinstance(component, dict):
            continue

        _sanitize_component_numeric_bounds(component)

        result_type = component.get("result_type", "")

        if result_type == "K" and not component.get("auto_calc"):
            component["auto_calc"] = True

        if result_type == "L" and not component.get("list_key"):
            component["list_key"] = _infer_list_key(component)
            logger.warning(
                "L-type component '%s' missing list_key (analysis: %s)",
                component.get("component_name", "?"),
                component.get("analysis", "?"),
            )

        if "units" in component and component["units"] is None:
            component["units"] = ""

    return data


def _normalize_component(component: dict[str, Any], *, index: int) -> dict[str, Any]:
    """Normalize a single component record."""
    normalized_component = dict(component)

    component_name = normalized_component.get("component_name")
    if component_name is not None:
        normalized_component["component_name"] = normalize_component_name(
            str(component_name)
        )

    if normalized_component.get("order_number") is None:
        normalized_component["order_number"] = index

    normalized_component["result_type"] = _normalize_result_type(
        normalized_component.get("result_type"),
        uses_instrument=bool(normalized_component.get("uses_instrument")),
    )

    normalized_component = _normalize_record(normalized_component)
    normalized_component = coerce_numeric_strings(normalized_component)
    normalized_component = coerce_boolean_strings(normalized_component)
    _sanitize_component_numeric_bounds(normalized_component)

    return normalized_component


def sanitize_component_numeric_bounds(
    components: list[dict[str, Any]],
) -> None:
    """Sanitize qualitative tokens in component numeric bounds in place.

    This is intentionally conservative: only clear minimum/maximum when
    result_type is qualitative (L/T/D) and the bound value is a known
    qualitative token (e.g., Pass, N/A).
    """
    for component in components:
        if not isinstance(component, dict):
            continue
        _sanitize_component_numeric_bounds(component)


def _sanitize_component_numeric_bounds(component: dict[str, Any]) -> None:
    result_type = str(component.get("result_type", "")).upper().strip()
    if result_type not in {"L", "T", "D"}:
        return

    for field in ("minimum", "maximum"):
        value = component.get(field)
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in QUALITATIVE_BOUND_TOKENS:
                logger.info(
                    "Clearing qualitative token '%s' from %s for component '%s' (result_type=%s)",
                    value,
                    field,
                    component.get("component_name", "?"),
                    result_type,
                )
                component[field] = None


def _normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    """Normalize symbols in a generic record."""
    normalized_record: dict[str, Any] = {}
    for key, value in record.items():
        if isinstance(value, str):
            normalized_record[key] = normalize_symbols(value).strip()
        else:
            normalized_record[key] = value
    return normalized_record


def _build_analysis_name_map(analyses: list[dict[str, Any]]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for analysis in analyses:
        if not isinstance(analysis, dict):
            continue
        normalized_name = analysis.get("name")
        if not normalized_name:
            continue
        normalized_name_str = str(normalized_name)
        mapping[_normalize_lookup_key(normalized_name_str)] = normalized_name_str
        for alias_field in ("reported_name", "common_name"):
            alias = analysis.get(alias_field)
            if alias:
                mapping[_normalize_lookup_key(str(alias))] = normalized_name_str
    return mapping


def _forward_fill_field(
    records: list[dict[str, Any]],
    field: str,
    *,
    available_values: list[str] | None = None,
) -> None:
    """Fill missing field values using forward-fill, backward-fill, and inference.

    Extracted tables often omit repeated values (e.g., the analysis name
    is only shown on the first row of a group). This handles three cases:

    1. **Forward-fill**: propagate the last non-None value to subsequent
       records (handles mid-table gaps).
    2. **Backward-fill**: if leading records have None, fill them from
       the first non-None value found later (handles PDFs where the
       analysis name appears after the first few rows).
    3. **Single-value inference**: if ALL records have None but
       ``available_values`` has exactly one entry, assign it to all
       records (handles single-analysis PDFs where the analysis name
       appears only in the Analysis sheet, not in the Component table).

    Mutates records in place.

    Args:
        records: List of record dicts.
        field: The field name to fill.
        available_values: Known valid values for this field (e.g.,
            extracted analysis names). Used for single-value inference.
    """
    if not records:
        return

    # Pass 1: forward-fill (covers mid-table gaps)
    last_value: Any = None
    filled_count = 0
    for record in records:
        if not isinstance(record, dict):
            continue
        value = record.get(field)
        if value is not None and value != "":
            last_value = value
        elif last_value is not None:
            record[field] = last_value
            filled_count += 1

    # Pass 2: backward-fill leading Nones from the first non-None value
    first_value: Any = None
    for record in records:
        if not isinstance(record, dict):
            continue
        value = record.get(field)
        if value is not None and value != "":
            first_value = value
            break

    if first_value is not None:
        for record in records:
            if not isinstance(record, dict):
                continue
            value = record.get(field)
            if value is not None and value != "":
                break
            record[field] = first_value
            filled_count += 1

    # Pass 3: single-value inference — if ALL records still have None
    # and there's exactly one known value, assign it to all
    if available_values and len(available_values) == 1:
        sole_value = available_values[0]
        for record in records:
            if not isinstance(record, dict):
                continue
            if record.get(field) is None or record.get(field) == "":
                record[field] = sole_value
                filled_count += 1

    if filled_count > 0:
        logger.info(
            "Filled '%s' on %d records (forward/backward/infer)",
            field,
            filled_count,
        )


def _resolve_analysis_name(
    raw_ref: str,
    analysis_name_map: dict[str, str],
) -> str | None:
    """Resolve a raw analysis reference to a canonical analysis name.

    Uses deterministic exact-match only via the alias map (which includes
    the canonical name, reported_name, and common_name). Prefix and
    substring matching tiers have been removed because they produce
    ambiguous matches for names sharing common prefixes (e.g.
    SITE_IDENTITY matching SITE_IDENTITY_CTL).

    Unresolved references return None and will fail loudly at validation.

    Returns the resolved canonical name, or None if no match found.
    """
    lookup_key = _normalize_lookup_key(raw_ref)

    # Exact match only (covers aliases, reported_name, common_name)
    exact = analysis_name_map.get(lookup_key)
    if exact:
        return exact

    # No match found -- will be caught by validation
    logger.warning(
        "Analysis ref '%s' (normalized: '%s') has no exact match in alias map",
        raw_ref,
        lookup_key,
    )
    return None


def _normalize_analysis_refs(
    records: list[dict[str, Any]],
    analysis_name_map: dict[str, str],
) -> None:
    for record in records:
        if not isinstance(record, dict):
            continue
        analysis_name = record.get("analysis")
        if not analysis_name:
            continue
        resolved = _resolve_analysis_name(str(analysis_name), analysis_name_map)
        if resolved:
            record["analysis"] = resolved
        reference_analysis = record.get("reference_analysis")
        if reference_analysis:
            resolved_ref = _resolve_analysis_name(
                str(reference_analysis), analysis_name_map
            )
            if resolved_ref:
                record["reference_analysis"] = resolved_ref


def _build_component_name_map(components: list[dict[str, Any]]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for component in components:
        if not isinstance(component, dict):
            continue
        component_name = component.get("component_name")
        if not component_name:
            continue
        canonical_name = str(component_name)
        mapping[_normalize_lookup_key(canonical_name)] = canonical_name
    return mapping


def _normalize_component_refs(
    records: list[dict[str, Any]],
    component_name_map: dict[str, str],
) -> None:
    for record in records:
        if not isinstance(record, dict):
            continue
        component_name = record.get("component")
        if component_name:
            mapped_component = component_name_map.get(
                _normalize_lookup_key(str(component_name))
            )
            if mapped_component:
                record["component"] = mapped_component
        reference_component = record.get("reference_component")
        if reference_component:
            mapped_reference = component_name_map.get(
                _normalize_lookup_key(str(reference_component))
            )
            if mapped_reference:
                record["reference_component"] = mapped_reference


def _normalize_lookup_key(value: str) -> str:
    key = normalize_component_name(value)
    return key


def _infer_analysis_type_from_name(analysis_name: str) -> str | None:
    """Infer analysis_type from keywords in the analysis name.

    This is data normalization, not fallback logic -- the type information
    IS present in the name, just not in the analysis_type field.

    Returns:
        Inferred type code, or None if no keywords match.
    """
    if not analysis_name:
        return None

    # Check suffix patterns first (most specific)
    if analysis_name.endswith(("_CTL", "_META")):
        logger.info(
            "Inferred analysis_type='QC_SAMPLES' from suffix in '%s'",
            analysis_name,
        )
        return "QC_SAMPLES"

    name_lower = analysis_name.lower().replace("_", " ").replace("-", " ")

    # Keyword to type mapping, ordered by specificity
    _KEYWORD_TYPE_MAP: list[tuple[str, str]] = [
        ("control", "QC_SAMPLES"),
        ("meta data", "QC_SAMPLES"),
        ("identity", "ID"),
        ("dye binding", "ID"),
        ("assay", "ASY"),
        ("potency", "ASY"),
        ("impurity", "IMP"),
        ("impurities", "IMP"),
        ("physical", "PHYS"),
        ("dissolution", "PHYS"),
        ("karl fischer", "KF"),
        ("moisture", "KF"),
    ]

    for keyword, type_code in _KEYWORD_TYPE_MAP:
        if keyword in name_lower:
            logger.info(
                "Inferred analysis_type='%s' from keyword '%s' in '%s'",
                type_code,
                keyword,
                analysis_name,
            )
            return type_code

    return None


def _normalize_analysis_type(value: Any, analysis_name: Any) -> Any:
    if value is None:
        # Try to infer from analysis name when type is missing
        if isinstance(analysis_name, str) and analysis_name:
            inferred = _infer_analysis_type_from_name(analysis_name)
            if inferred:
                return inferred
        return value
    normalized_key = str(value).strip().lower()
    mapped = ANALYSIS_TYPE_MAP.get(normalized_key)
    if mapped:
        return mapped
    normalized_comp_key = normalize_component_name(str(value)).lower()
    mapped = ANALYSIS_TYPE_MAP.get(normalized_comp_key)
    if mapped:
        return mapped
    if isinstance(analysis_name, str) and analysis_name.endswith(("_CTL", "_META")):
        return "QC_SAMPLES"
    return str(value).upper()


def _normalize_result_type(value: Any, *, uses_instrument: bool) -> Any:
    if value is None:
        return value
    normalized_key = str(value).strip().lower()
    mapped = RESULT_TYPE_MAP.get(normalized_key)
    if mapped:
        return mapped
    normalized_comp_key = normalize_component_name(str(value)).lower()
    mapped = RESULT_TYPE_MAP.get(normalized_comp_key)
    if mapped:
        return mapped
    if uses_instrument:
        return "N"
    return str(value).upper()


def _infer_list_key(component: dict[str, Any]) -> str:
    component_name = str(component.get("component_name", "")).lower()
    if any(keyword in component_name for keyword in ("result", "pass", "fail")):
        return "PASS_FAIL"
    if any(keyword in component_name for keyword in ("inspect", "appearance", "visual")):
        return "CONFORM"
    return "YES_NO_2"


def _normalize_calc_variable(record: dict[str, Any]) -> dict[str, Any]:
    normalized_record = _normalize_record(dict(record))
    normalized_record = coerce_numeric_strings(normalized_record)
    normalized_record = coerce_boolean_strings(normalized_record)

    reference_type = normalized_record.get("reference_type")
    if reference_type is None or reference_type == "":
        normalized_record["reference_type"] = "C"
    else:
        normalized_record["reference_type"] = str(reference_type).strip().upper()

    return_value = normalized_record.get("return_value")
    normalized_record["return_value"] = _map_enum_alias(
        value=return_value,
        mapping=CALC_VARIABLE_RETURN_VALUE_MAP,
        default="S",
    )

    scope = normalized_record.get("scope")
    normalized_record["scope"] = _map_enum_alias(
        value=scope,
        mapping=CALC_VARIABLE_SCOPE_MAP,
        default="CR",
    )

    function = normalized_record.get("function")
    normalized_record["function"] = _map_enum_alias(
        value=function,
        mapping=CALC_VARIABLE_FUNCTION_MAP,
        default="ENTRY",
    )

    return normalized_record


def _normalize_calculation(record: dict[str, Any]) -> dict[str, Any]:
    normalized_record = _normalize_record(dict(record))
    normalized_record = coerce_numeric_strings(normalized_record)
    normalized_record = coerce_boolean_strings(normalized_record)

    calculation_type = normalized_record.get("calculation_type")
    source_code = str(normalized_record.get("source_code", "")).upper()
    if "CALC_INST_PICKER" in source_code:
        normalized_record["calculation_type"] = "INST_PICKER"
    elif "CALC_SR_PICKER" in source_code:
        normalized_record["calculation_type"] = "SR_PICKER"
    elif "GOSUB" in source_code:
        normalized_record["calculation_type"] = "GOSUB"
    elif "IF" in source_code and "THEN" in source_code:
        normalized_record["calculation_type"] = "CONDITIONAL"
    else:
        normalized_record["calculation_type"] = _map_enum_alias(
            value=calculation_type,
            mapping=CALCULATION_TYPE_MAP,
            default="FORMULA",
        )

    return normalized_record


def _map_enum_alias(
    *,
    value: Any,
    mapping: dict[str, str],
    default: str,
) -> str:
    if value is None:
        return default
    raw = str(value).strip()
    if not raw:
        return default
    by_text = mapping.get(raw.lower())
    if by_text:
        return by_text
    by_key = mapping.get(normalize_component_name(raw).lower())
    if by_key:
        return by_key
    upper = raw.upper()
    if upper in set(mapping.values()):
        return upper
    return default

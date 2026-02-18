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

    if "analyses" in data and isinstance(data["analyses"], list):
        data["analyses"] = normalize_analysis_names(data["analyses"])

    if "components" in data and isinstance(data["components"], list):
        data["components"] = [_normalize_component(comp) for comp in data["components"]]

    if "calc_variables" in data and isinstance(data["calc_variables"], list):
        data["calc_variables"] = [
            _normalize_record(record) for record in data["calc_variables"]
        ]

    if "calculations" in data and isinstance(data["calculations"], list):
        data["calculations"] = [
            _normalize_record(record) for record in data["calculations"]
        ]

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
            normalized_name = str(name).strip()
            normalized_name = re.sub(r"[\s-]+", "_", normalized_name)
            normalized_name = normalized_name.upper()
            normalized_name = re.sub(r"_+", "_", normalized_name)
            normalized_name = normalized_name.strip("_")
            normalized_analysis["name"] = normalized_name

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

        result_type = component.get("result_type", "")

        if result_type == "K" and "auto_calc" not in component:
            component["auto_calc"] = True

        if result_type == "L" and not component.get("list_key"):
            logger.warning(
                "L-type component '%s' missing list_key (analysis: %s)",
                component.get("component_name", "?"),
                component.get("analysis", "?"),
            )

        if "units" in component and component["units"] is None:
            component["units"] = ""

    return data


def _normalize_component(component: dict[str, Any]) -> dict[str, Any]:
    """Normalize a single component record."""
    normalized_component = dict(component)

    component_name = normalized_component.get("component_name")
    if component_name is not None:
        normalized_component["component_name"] = normalize_component_name(
            str(component_name)
        )

    normalized_component = _normalize_record(normalized_component)
    normalized_component = coerce_numeric_strings(normalized_component)
    normalized_component = coerce_boolean_strings(normalized_component)

    return normalized_component


def _normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    """Normalize symbols in a generic record."""
    normalized_record: dict[str, Any] = {}
    for key, value in record.items():
        if isinstance(value, str):
            normalized_record[key] = normalize_symbols(value).strip()
        else:
            normalized_record[key] = value
    return normalized_record

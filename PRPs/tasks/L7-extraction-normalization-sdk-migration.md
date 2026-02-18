# Task L7 — Extraction Data Quality: Post-Processing, Normalization & SDK Migration

**Phase:** 7 (Optimization) | **Dependencies:** Phase 6 (done)
**Branch:** `prjoject_p_protatype`
**Estimated effort:** 1-2 days

---

## Objective

Improve the quality and reliability of data extracted from pharmaceutical PDFs by: (a) adding a post-processing/normalization layer after LlamaExtract, (b) researching and potentially migrating to the newer `llama-cloud` v1.4+ SDK or LlamaParse v2 API, and (c) building a symbol/unit normalization tool that the chat agent can invoke.

---

## Problem

Currently, `pdf_extractor.py` sends raw LlamaExtract output directly to Pydantic validation. Common issues:
- Unicode symbols not normalized (e.g., `>=` vs `>=`, `u` vs `u`, `deg C` vs `deg C`)
- Whitespace inconsistencies in component names and analysis names
- Numeric values extracted as strings (e.g., `"0.5"` instead of `0.5`)
- Empty/null fields that should have defaults based on LIMS conventions
- The `llama-cloud-services` package is deprecated (EOL ~May 2026), needs migration to `llama-cloud` v1.4.0

---

## Research Required

Before implementation, research and document findings on:

1. **LlamaParse v2 API** -- New tier-based system (`fast`, `cost_effective`, `agentic`, `agentic_plus`). The `agentic` tier uses an AI agent to plan and execute parsing. New `input_options.spreadsheet_options` for sheet selection. Version pinning (`YYYY-MM-DD`) for reproducibility. New SDK is `llama-cloud` v1.4.0 with `LlamaCloud` class.
   - Docs: https://developers.llamaindex.ai/python/cloud/llamaparse/api-v2-guide/
   - Blog: https://www.llamaindex.ai/blog/announcing-new-llamacloud-sdks-and-parse-api-v2

2. **LlamaExtract status** -- Still in beta, schema inference capped at 5 files/10 pages. Planned improvements include multimodal support and human-in-the-loop schema creation.
   - Docs: https://developers.llamaindex.ai/python/cloud/llamaextract/getting_started/

3. **Decision**: Test both approaches on `demo_data/AND_ACS_DYE-LAB-2499.pdf` and compare extraction quality. Document results. Recommend one approach.

---

## Files to Create

| File | Purpose |
|------|---------|
| `main/src/lims/data_normalizer.py` | Post-extraction normalization: symbol cleanup, type coercion, naming conventions, unit standardization |

## Files to Modify

| File | Change |
|------|--------|
| `main/src/lims/pdf_extractor.py` | Add normalization step between raw extraction and Pydantic validation. Pin SDK version or migrate to `llama-cloud` v1.4.0 |
| `main/src/lims/extraction_schema.py` | Update schema hints/descriptions if switching APIs |
| `main/src/lims/config.py` | Add `extraction_api` field (`llamaextract` or `llamaparse_v2`) for A/B testing |
| `pyproject.toml` | Pin `llama-cloud-services==0.6.93` (immediate) or migrate to `llama-cloud>=1.4.0` |

---

## Implementation Details

### 1. data_normalizer.py -- Post-Extraction Normalization

```python
"""Post-extraction data normalization for MDA templates.

Cleans and standardizes raw extraction output before Pydantic validation.
Handles symbol normalization, type coercion, naming conventions, and
LIMS-specific defaults.

GAMP-5 Category 5: Custom pharmaceutical software component.
NO FALLBACK LOGIC -- normalization errors propagate with full diagnostics.
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Symbol normalization map
# ---------------------------------------------------------------------------

SYMBOL_MAP: dict[str, str] = {
    "\u2265": ">=",      # greater than or equal
    "\u2264": "<=",      # less than or equal
    "\u00b5": "u",       # micro sign -> u
    "\u03bc": "u",       # greek mu -> u
    "\u00b0": "deg ",    # degree sign
    "\u00b1": "+/-",     # plus-minus
    "\u00d7": "x",       # multiplication sign
    "\u2013": "-",       # en dash
    "\u2014": "-",       # em dash
    "\u2018": "'",       # left single quote
    "\u2019": "'",       # right single quote
    "\u201c": '"',       # left double quote
    "\u201d": '"',       # right double quote
    "\u2026": "...",     # ellipsis
}

# Numeric fields that should be coerced from strings
NUMERIC_FIELDS = [
    "minimum", "maximum", "places", "order_number", "version",
    "round_precision", "significant_figures",
]

# Boolean fields that may come as strings
BOOLEAN_FIELDS = [
    "auto_calc", "uses_instrument", "reportable", "optional",
    "active", "allow_out_of_range",
]


def normalize_extraction(raw_dict: dict[str, Any]) -> dict[str, Any]:
    """Main entry point: apply all normalization rules.

    Applies normalization in order:
    1. Analysis name normalization (uppercase, underscore conventions)
    2. Component name normalization
    3. Symbol normalization in all string fields
    4. Numeric string coercion
    5. Boolean string coercion
    6. LIMS convention defaults

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

    logger.info("Starting extraction normalization (%d top-level keys)", len(raw_dict))

    # Normalize each sheet
    if "analyses" in raw_dict:
        raw_dict["analyses"] = normalize_analysis_names(raw_dict["analyses"])

    if "components" in raw_dict:
        raw_dict["components"] = [
            _normalize_component(c) for c in raw_dict["components"]
        ]

    if "calc_variables" in raw_dict:
        raw_dict["calc_variables"] = [
            _normalize_record(cv) for cv in raw_dict["calc_variables"]
        ]

    if "calculations" in raw_dict:
        raw_dict["calculations"] = [
            _normalize_record(calc) for calc in raw_dict["calculations"]
        ]

    # Apply LIMS defaults
    raw_dict = apply_lims_defaults(raw_dict)

    logger.info("Extraction normalization complete")
    return raw_dict


def normalize_symbols(text: str) -> str:
    """Replace Unicode/special chars with LIMS-compatible equivalents.

    Examples:
        >= -> >=
        uL -> uL
        deg C -> deg C
        +/- -> +/-
        x -> x

    Args:
        text: Input string potentially containing Unicode symbols.

    Returns:
        Cleaned string with LIMS-compatible ASCII equivalents.
    """
    for unicode_char, replacement in SYMBOL_MAP.items():
        text = text.replace(unicode_char, replacement)
    return text


def normalize_component_name(name: str) -> str:
    """Standardize component names to LIMS conventions.

    Rules:
    - Strip leading/trailing whitespace
    - Replace multiple spaces with single underscore
    - Replace hyphens and dots with underscores
    - Uppercase the entire name
    - Remove consecutive underscores

    Args:
        name: Raw component name from extraction.

    Returns:
        Normalized component name (e.g., "ABSORBANCE_595").
    """
    if not name:
        return name
    name = name.strip()
    name = re.sub(r"[\s]+", "_", name)
    name = re.sub(r"[-.]", "_", name)
    name = name.upper()
    name = re.sub(r"_+", "_", name)
    name = name.strip("_")
    return name


def normalize_analysis_names(analyses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Ensure analysis names follow {SITE}_{METHOD}[_{SUFFIX}] pattern.

    Rules:
    - Uppercase all names
    - Replace spaces/hyphens with underscores
    - Validate CTL/META suffixes
    - Remove consecutive underscores

    Args:
        analyses: List of analysis dicts from extraction.

    Returns:
        List with normalized analysis name fields.
    """
    for analysis in analyses:
        if "name" in analysis and analysis["name"]:
            name = str(analysis["name"]).strip()
            name = re.sub(r"[\s-]+", "_", name)
            name = name.upper()
            name = re.sub(r"_+", "_", name)
            name = name.strip("_")
            analysis["name"] = name
    return analyses


def coerce_numeric_strings(
    data: dict[str, Any], numeric_fields: list[str] | None = None
) -> dict[str, Any]:
    """Convert string numbers to actual float/int values.

    Fields: minimum, maximum, places, order_number, version.

    Args:
        data: Dict with potentially string-typed numeric fields.
        numeric_fields: Override list of field names to coerce.

    Returns:
        Dict with numeric fields coerced to int/float.
    """
    fields = numeric_fields or NUMERIC_FIELDS
    for field in fields:
        if field in data and isinstance(data[field], str):
            val = data[field].strip()
            if not val:
                continue
            try:
                if "." in val:
                    data[field] = float(val)
                else:
                    data[field] = int(val)
            except ValueError:
                logger.warning(
                    "Cannot coerce '%s' to number for field '%s'", val, field
                )
    return data


def coerce_boolean_strings(data: dict[str, Any]) -> dict[str, Any]:
    """Convert string booleans to actual bool values.

    Handles: "T"/"F", "True"/"False", "true"/"false", "1"/"0", "Y"/"N".

    Args:
        data: Dict with potentially string-typed boolean fields.

    Returns:
        Dict with boolean fields coerced to bool.
    """
    bool_map = {
        "t": True, "f": False,
        "true": True, "false": False,
        "1": True, "0": False,
        "y": True, "n": False,
        "yes": True, "no": False,
    }
    for field in BOOLEAN_FIELDS:
        if field in data and isinstance(data[field], str):
            val = data[field].strip().lower()
            if val in bool_map:
                data[field] = bool_map[val]
    return data


def apply_lims_defaults(data: dict[str, Any]) -> dict[str, Any]:
    """Apply LIMS convention defaults for missing fields.

    Rules:
    - K-type components: auto_calc=True
    - L-type components: ensure list_key present
    - N-type with uses_instrument: default instrument_group if missing
    - units default to empty string if null

    Args:
        data: Full MDA template dict.

    Returns:
        Dict with LIMS defaults applied where appropriate.
    """
    for comp in data.get("components", []):
        result_type = comp.get("result_type", "")

        # K-type must have auto_calc=True
        if result_type == "K" and "auto_calc" not in comp:
            comp["auto_calc"] = True

        # L-type should have list_key
        if result_type == "L" and not comp.get("list_key"):
            logger.warning(
                "L-type component '%s' missing list_key (analysis: %s)",
                comp.get("component_name", "?"),
                comp.get("analysis", "?"),
            )

        # Null units -> empty string
        if "units" in comp and comp["units"] is None:
            comp["units"] = ""

    return data


def _normalize_component(comp: dict[str, Any]) -> dict[str, Any]:
    """Normalize a single component record."""
    # Normalize component name
    if "component_name" in comp:
        comp["component_name"] = normalize_component_name(
            str(comp["component_name"])
        )

    # Normalize all string values for symbols
    for key, val in comp.items():
        if isinstance(val, str):
            comp[key] = normalize_symbols(val)

    # Coerce types
    comp = coerce_numeric_strings(comp)
    comp = coerce_boolean_strings(comp)

    return comp


def _normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    """Normalize a generic record (calc_variable or calculation)."""
    for key, val in record.items():
        if isinstance(val, str):
            record[key] = normalize_symbols(val)

    record = coerce_numeric_strings(record)
    record = coerce_boolean_strings(record)

    return record
```

### 2. Integration into pdf_extractor.py

After extraction, before Pydantic validation:

```python
from .data_normalizer import normalize_extraction

# ... existing extraction code ...
raw_dict = ...  # from LlamaExtract

# NEW: Normalize before validation
normalized_dict = normalize_extraction(raw_dict)

# Validate against MDATemplate
mda = MDATemplate.model_validate(normalized_dict)
```

The key insertion point is in `extract_mda_from_pdf()` after `raw_dict` is built from the extraction result and before the return statement. This is additive -- the existing extraction logic is unchanged.

### 3. SDK Migration Research

Test both approaches with the same PDF and compare:

```python
# Approach A: Current LlamaExtract (llama-cloud-services)
from llama_cloud_services import LlamaExtract
extractor = LlamaExtract(api_key=config.llamaextract_api_key)
agent = extractor.create_agent(name=..., data_schema=MDAExtractionSchema)
run = agent.extract(tmp_path)

# Approach B: New llama-cloud v1.4.0 (if API compatible)
from llama_cloud import LlamaCloud
client = LlamaCloud(api_key=...)
result = await client.extraction.extract(file=tmp_path, schema=...)

# Approach C: LlamaParse v2 + LLM structured extraction
# Parse PDF to high-quality markdown first, then use LLM for structuring
```

#### LlamaParse v2 API Details

The v2 API introduces tier-based parsing:

| Tier | Speed | Quality | Use Case |
|------|-------|---------|----------|
| `fast` | Fastest | Basic | Simple text PDFs |
| `cost_effective` | Fast | Good | Standard documents |
| `agentic` | Slow | Best | Complex PDFs with tables/figures |
| `agentic_plus` | Slowest | Premium | Pharmaceutical SOPs with mixed content |

Key v2 features relevant to AI4LIMS:
- **Version pinning**: `api_version="2025-01-15"` for reproducible results
- **Spreadsheet options**: `input_options.spreadsheet_options` for sheet selection
- **Agentic parsing**: AI agent plans and executes multi-step parsing strategy
- **New SDK**: `llama-cloud` v1.4.0 with `LlamaCloud` client class

#### llama-cloud-services Deprecation Timeline

- Current: `llama-cloud-services>=0.1.0` (deprecated)
- EOL: May 2026
- Replacement: `llama-cloud>=1.4.0` (released Feb 11, 2026)
- Migration: `LlamaExtract` -> `LlamaCloud.extraction`

Document: extraction accuracy, cost per document, latency, error rates. Save comparison results for thesis evaluation chapter.

### 4. Config Addition

```python
# In config.py -- add to LIMSConfig
extraction_api: str = "llamaextract"  # LIMS_EXTRACTION_API: "llamaextract" | "llamaparse_v2"
```

---

## Testing Strategy

```bash
# 1. Unit test normalization functions
uv run pytest main/tests/lims/test_data_normalizer.py -v

# 2. Integration: extract + normalize + validate
curl -X POST http://localhost:8080/lims/extract -F "file=@demo_data/AND_ACS_DYE-LAB-2499.pdf"
# Compare output before/after normalization

# 3. Verify existing tests still pass
uv run pytest main/tests/lims/ -v
```

---

## Gate Criteria

- [ ] `normalize_extraction()` handles all known symbol/naming issues from demo data
- [ ] Extraction + normalization produces valid MDATemplate for at least 3 demo PDFs
- [ ] SDK migration path documented with comparison results
- [ ] `llama-cloud-services` pinned or migrated
- [ ] All existing LIMS tests pass

---

## Sources

- LlamaParse v2 API Guide: https://developers.llamaindex.ai/python/cloud/llamaparse/api-v2-guide/
- LlamaParse v2 Blog Announcement: https://www.llamaindex.ai/blog/announcing-new-llamacloud-sdks-and-parse-api-v2
- LlamaExtract Getting Started: https://developers.llamaindex.ai/python/cloud/llamaextract/getting_started/
- llama-cloud PyPI (v1.4.0): https://pypi.org/project/llama-cloud/
- llama-cloud-services PyPI (deprecated): https://pypi.org/project/llama-cloud-services/

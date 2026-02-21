"""Focused extraction: text extraction + narrowed-scope PDF extraction.

Extracts raw text from PDF for classification, then runs full LlamaExtract
extraction. The "focusing" happens at the merge stage where only variable
field values from extraction are used.

GAMP-5 Category 5: Custom pharmaceutical software component.
NO FALLBACK LOGIC.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from langfuse import observe

from main.src.lims.config import LIMSConfig
from main.src.lims.templates.base import TestTypeTemplate

logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_content: bytes) -> str:
    """Extract raw text from PDF bytes using PyMuPDF.

    Used by the classifier to determine test type before structured extraction.

    Args:
        pdf_content: Raw PDF file bytes.

    Returns:
        Concatenated text from all pages.

    Raises:
        ValueError: If no text could be extracted (scanned PDF without OCR,
            encrypted, or corrupt).
    """
    import fitz  # PyMuPDF

    doc = fitz.open(stream=pdf_content, filetype="pdf")
    try:
        page_count = len(doc)
        if page_count == 0:
            raise ValueError(
                f"PDF has 0 pages ({len(pdf_content)} bytes). "
                "Cannot extract text from empty PDF."
            )

        text_parts: list[str] = []
        for page_num in range(page_count):
            page = doc[page_num]
            page_text = page.get_text("text")
            if page_text:
                text_parts.append(page_text)

        full_text = "\n".join(text_parts)

        if not full_text.strip():
            raise ValueError(
                f"PDF has {page_count} pages but no extractable text "
                f"({len(pdf_content)} bytes). This may be a scanned PDF "
                "without OCR or an encrypted document."
            )

        logger.info(
            "Extracted text from PDF: %d pages, %d characters",
            page_count,
            len(full_text),
        )
        return full_text
    finally:
        doc.close()


def build_variable_field_set(template: TestTypeTemplate) -> set[str]:
    """Return the set of field paths that need PDF extraction.

    These are the fields marked ``is_variable=True`` in the template.
    The merger uses this to know which extracted values to overlay.

    Args:
        template: A test-type-specific template instance.

    Returns:
        Set of field path strings (e.g., ``{"components[4].minimum", ...}``).
    """
    return set(template.get_variable_fields())


def build_focused_schema(template: TestTypeTemplate) -> dict[str, Any]:
    """Build a reduced extraction schema describing which fields per sheet need extraction.

    Analyzes the template's variable fields (``get_variable_fields()``) and groups
    them by sheet, returning field names and full paths.

    Args:
        template: A test-type-specific template instance.

    Returns:
        Dict with per-sheet field name lists and the full variable field paths::

            {
                "analyses_fields": ["description"],
                "components_fields": ["minimum", "maximum"],
                "variable_field_paths": ["analyses[0].description", ...],
            }
    """
    import re

    variable_paths = template.get_variable_fields()

    sheet_fields: dict[str, set[str]] = {}
    for path in variable_paths:
        # Parse "sheet[index].field_name" pattern
        match = re.match(r"^(\w+)\[\d+\]\.(\w+)$", path)
        if match:
            sheet, field_name = match.group(1), match.group(2)
            sheet_fields.setdefault(sheet, set()).add(field_name)

    result: dict[str, Any] = {}
    for sheet, fields in sheet_fields.items():
        result[f"{sheet}_fields"] = sorted(fields)
    result["variable_field_paths"] = variable_paths

    logger.info(
        "Built focused schema: %s",
        {k: v for k, v in result.items() if k != "variable_field_paths"},
    )
    return result


# Identity fields per sheet — kept during filtering so items can still be matched.
_IDENTITY_KEYS: dict[str, set[str]] = {
    "analyses": {"name", "analysis_type"},
    "components": {"analysis", "component_name"},
    "calc_variables": {"analysis", "component", "name"},
    "calculations": {"analysis", "component"},
}


def _filter_to_variable_fields(
    extraction_data: dict[str, Any],
    focused_schema: dict[str, Any],
) -> dict[str, Any]:
    """Strip non-variable fields from extraction data.

    For each sheet present in extraction_data, keeps only:
    - Identity/key fields (name, analysis, component_name, etc.)
    - Fields listed in the focused schema for that sheet

    Args:
        extraction_data: Full extraction result dict with sheet keys.
        focused_schema: Output of ``build_focused_schema()``.

    Returns:
        New dict with the same structure but only variable + identity fields.
    """
    import copy

    narrowed = copy.deepcopy(extraction_data)

    for sheet_key in ("analyses", "components", "calc_variables", "calculations"):
        items = narrowed.get(sheet_key)
        if not items or not isinstance(items, list):
            continue

        variable_fields = set(focused_schema.get(f"{sheet_key}_fields", []))
        identity_keys = _IDENTITY_KEYS.get(sheet_key, set())
        keep_keys = variable_fields | identity_keys

        narrowed_items: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                narrowed_items.append(item)
                continue
            narrowed_item = {k: v for k, v in item.items() if k in keep_keys}
            narrowed_items.append(narrowed_item)

        narrowed[sheet_key] = narrowed_items

    return narrowed


@observe(name="lims-focused-extract")
async def focused_extract(
    pdf_content: bytes,
    filename: str,
    template: TestTypeTemplate,
    config: LIMSConfig,
) -> dict[str, Any]:
    """Run full LlamaExtract extraction, then narrow results to variable fields.

    Calls the existing ``extract_mda_from_pdf`` via ``asyncio.to_thread()``
    (since the LlamaExtract SDK is synchronous), then filters the extraction
    output to keep only variable fields + identity keys so the merger only
    sees data relevant to the test-type template.

    Args:
        pdf_content: Raw PDF bytes.
        filename: Original PDF filename.
        template: The test-type template (used to identify variable fields).
        config: LIMS configuration with API keys and mode.

    Returns:
        Dict with all keys from ``extract_mda_from_pdf`` plus:
        - ``variable_fields``: list of field paths needing extraction.
        - ``focused_schema``: the schema used for narrowing.
        The ``mda_template`` and ``normalized_extraction`` keys are
        narrowed to only variable + identity fields.

    Raises:
        Exception: If LlamaExtract API call fails (no fallback).
    """
    from main.src.lims.pdf_extractor import extract_mda_from_pdf

    variable_fields = template.get_variable_fields()
    focused_schema = build_focused_schema(template)

    logger.info(
        "Running focused extraction for '%s' (test_type=%s, variable_fields=%d)",
        filename,
        template.test_type.value,
        len(variable_fields),
    )

    result = await asyncio.to_thread(
        extract_mda_from_pdf,
        pdf_content=pdf_content,
        filename=filename,
        config=config,
    )

    # Narrow extraction output to variable fields only
    for key in ("mda_template", "normalized_extraction"):
        if key in result and isinstance(result[key], dict):
            result[key] = _filter_to_variable_fields(result[key], focused_schema)

    result["variable_fields"] = variable_fields
    result["focused_schema"] = focused_schema

    logger.info(
        "Focused extraction complete for '%s': validated=%s, variable_fields=%d",
        filename,
        result.get("validated"),
        len(variable_fields),
    )

    return result

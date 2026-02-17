"""LlamaExtract wrapper for MDA PDF extraction.

Extracts structured data from pharmaceutical test method PDFs using
LlamaExtract Cloud API with the MDATemplate Pydantic schema.

SDK v0.6+ uses a 2-step API: create_agent(schema) -> agent.extract(file).
"""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Any

from .config import LIMSConfig
from .extraction_schema import MDAExtractionSchema
from .mda_schema import MDATemplate

logger = logging.getLogger(__name__)


def _get_extract_config() -> Any:
    """Create default ExtractConfig."""
    from llama_cloud import ExtractConfig

    return ExtractConfig()


def extract_mda_from_pdf(
    pdf_content: bytes,
    filename: str,
    config: LIMSConfig,
) -> dict[str, Any]:
    """Extract MDA data from a PDF using LlamaExtract.

    The SDK requires a file path, so we write to a temp file and clean up.

    SDK v0.6+ flow:
      1. Create an extraction agent with MDATemplate schema
      2. Call agent.extract(filepath) which returns ExtractRun
      3. Parse result.data into dict

    Args:
        pdf_content: Raw PDF bytes.
        filename: Original filename (for logging).
        config: LIMS configuration with API key and mode.

    Returns:
        dict with keys:
            - raw_extraction: The raw extracted data dict.
            - validated: Whether Pydantic validation passed.
            - validation_error: Error message if validation failed, else None.
            - mda_template: Validated MDATemplate dict if validation passed, else None.

    Raises:
        Exception: If LlamaExtract API call fails (no fallback).
    """
    from llama_cloud_services import LlamaExtract

    extractor = LlamaExtract(api_key=config.llamaextract_api_key)
    extract_config = _get_extract_config()

    # SDK needs a file path — write to temp file
    tmp_path: str | None = None
    try:
        suffix = Path(filename).suffix or ".pdf"
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=suffix, prefix="lims_extract_"
        ) as tmp:
            tmp.write(pdf_content)
            tmp_path = tmp.name

        logger.info(
            f"Extracting MDA from '{filename}' ({len(pdf_content)} bytes) "
            f"mode={config.extraction_mode}"
        )

        # Step 1: Create extraction agent with simplified schema
        # (LlamaExtract can't handle enums/validators from full MDATemplate)
        agent_name = f"mda-{Path(filename).stem[:30]}"
        agent = extractor.create_agent(
            name=agent_name,
            data_schema=MDAExtractionSchema,
            config=extract_config,
        )
        logger.info(f"Created extraction agent '{agent_name}'")

        # Step 2: Extract data from the PDF file
        run = agent.extract(tmp_path)

        # Step 3: Parse the result
        raw_data = run.data if hasattr(run, "data") else run

        # Convert to dict if it's a Pydantic model
        if hasattr(raw_data, "model_dump"):
            raw_dict = raw_data.model_dump()
        elif isinstance(raw_data, dict):
            raw_dict = raw_data
        else:
            raw_dict = {"raw": str(raw_data)}

        logger.info(f"Extraction complete for '{filename}': {list(raw_dict.keys())}")

    finally:
        # Clean up temp file (Windows-compatible: delete=False + manual removal)
        if tmp_path:
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except OSError as e:
                logger.warning(f"Failed to clean up temp file {tmp_path}: {e}")

    # Attempt Pydantic validation against MDATemplate
    validated = False
    validation_error: str | None = None
    mda_template_dict: dict[str, Any] | None = None

    try:
        mda = MDATemplate.model_validate(raw_dict)
        mda_template_dict = mda.model_dump()
        validated = True
        logger.info(
            f"Pydantic validation passed for '{filename}': "
            f"{len(mda.analyses)} analyses, {len(mda.components)} components"
        )
    except Exception as e:
        validation_error = str(e)
        logger.warning(
            f"Pydantic validation failed for '{filename}' (raw data still available): {e}"
        )

    return {
        "raw_extraction": raw_dict,
        "validated": validated,
        "validation_error": validation_error,
        "mda_template": mda_template_dict,
    }

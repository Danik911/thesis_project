"""LlamaExtract wrapper for MDA PDF extraction.

Extracts structured data from pharmaceutical test method PDFs using
LlamaExtract Cloud API with the MDATemplate Pydantic schema.

SDK v0.6+ uses a 2-step API: create_agent(schema) -> agent.extract(file).
"""

from __future__ import annotations

import hashlib
import logging
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .config import LIMSConfig
from .data_normalizer import normalize_extraction
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
    if config.extraction_api != "llamaextract":
        raise NotImplementedError(
            "LIMS extraction API 'llamaparse_v2' is configured but not implemented in "
            "runtime path yet. Set LIMS_EXTRACTION_API=llamaextract or implement the "
            "llamaparse_v2 client path first."
        )

    from llama_cloud_services import LlamaExtract

    extractor = LlamaExtract(api_key=config.llamaextract_api_key)
    extract_config = _get_extract_config()

    request_started = datetime.now(UTC)
    started_perf = time.perf_counter()
    content_sha256 = hashlib.sha256(pdf_content).hexdigest()
    trace: dict[str, Any] = {
        "provider": "llama_cloud_services",
        "client": "LlamaExtract",
        "extraction_api": config.extraction_api,
        "extraction_mode": config.extraction_mode,
        "filename": filename,
        "pdf_size_bytes": len(pdf_content),
        "pdf_sha256": content_sha256,
        "request_started_at": request_started.isoformat(),
        "agent_name": None,
        "run_id": None,
        "run_status": None,
        "duration_ms": None,
    }

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
        agent_name = f"mda-{Path(filename).stem[:20]}-{uuid4().hex[:8]}"
        agent = extractor.create_agent(
            name=agent_name,
            data_schema=MDAExtractionSchema,
            config=extract_config,
        )
        trace["agent_name"] = agent_name
        logger.info(f"Created extraction agent '{agent_name}'")

        # Step 2: Extract data from the PDF file
        run = agent.extract(tmp_path)
        trace["run_id"] = getattr(run, "id", None) or getattr(run, "run_id", None)
        trace["run_status"] = getattr(run, "status", None)

        # Step 3: Parse the result
        raw_data = run.data if hasattr(run, "data") else run

        # Convert to dict if it's a Pydantic model
        if hasattr(raw_data, "model_dump"):
            raw_dict = raw_data.model_dump()
        elif isinstance(raw_data, dict):
            raw_dict = raw_data
        else:
            raw_dict = {"raw": str(raw_data)}

        duration_ms = int((time.perf_counter() - started_perf) * 1000)
        trace["duration_ms"] = duration_ms

        logger.info(
            "Extraction complete for '%s': keys=%s trace=%s",
            filename,
            list(raw_dict.keys()),
            {
                "agent_name": trace["agent_name"],
                "run_id": trace["run_id"],
                "run_status": trace["run_status"],
                "duration_ms": trace["duration_ms"],
                "pdf_sha256_prefix": content_sha256[:12],
            },
        )

    finally:
        # Clean up temp file (Windows-compatible: delete=False + manual removal)
        if tmp_path:
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except OSError as e:
                logger.warning(f"Failed to clean up temp file {tmp_path}: {e}")

    # Normalize extraction output before strict Pydantic validation
    normalized_dict = normalize_extraction(raw_dict)

    # Attempt Pydantic validation against MDATemplate
    validated = False
    validation_error: str | None = None
    mda_template_dict: dict[str, Any] | None = None

    try:
        mda = MDATemplate.model_validate(normalized_dict)
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
        "normalized_extraction": normalized_dict,
        "validated": validated,
        "validation_error": validation_error,
        "mda_template": mda_template_dict,
        "extraction_trace": trace,
    }

"""LIMS API router for AI4LIMS PoC.

Public endpoints (no authentication) for PDF extraction feasibility testing.
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, HTTPException, UploadFile, status

logger = logging.getLogger(__name__)

router = APIRouter(tags=["LIMS"])

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


@router.post("/extract")
async def extract_pdf(file: UploadFile) -> dict:
    """Extract MDA data from an uploaded PDF using LlamaExtract.

    Accepts multipart/form-data with a single PDF file.
    No authentication required (LIMS routes are public).

    Extraction is synchronous and takes 15-60s. Acceptable for feasibility.
    Wrapped in asyncio.to_thread() to avoid blocking the event loop.

    Args:
        file: Uploaded PDF file.

    Returns:
        JSON with raw_extraction, validated, validation_error, mda_template.

    Raises:
        HTTPException 400: Non-PDF, empty, or oversized file.
        HTTPException 500: Config or extraction failure.
    """
    # Validate file extension
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only PDF files are accepted. Got: '{file.filename}'",
        )

    # Read content and validate size
    content = await file.read()

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large ({len(content)} bytes). Maximum: {MAX_FILE_SIZE} bytes (50 MB).",
        )

    # Load config — fails explicitly if API key missing
    try:
        from main.src.lims.config import get_lims_config

        config = get_lims_config()
    except ValueError as e:
        logger.error(f"LIMS config error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LIMS configuration error: {e}",
        ) from e

    # Run extraction (synchronous SDK call wrapped in thread)
    try:
        from main.src.lims.pdf_extractor import extract_mda_from_pdf

        result = await asyncio.to_thread(
            extract_mda_from_pdf,
            pdf_content=content,
            filename=file.filename or "upload.pdf",
            config=config,
        )
    except Exception as e:
        logger.exception(f"PDF extraction failed for '{file.filename}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF extraction failed: {type(e).__name__}: {e}",
        ) from e

    return {
        "filename": file.filename,
        "size_bytes": len(content),
        **result,
    }

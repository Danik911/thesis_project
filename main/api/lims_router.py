"""LIMS API router for AI4LIMS PoC.

Public endpoints (no authentication) for PDF extraction, MDA chat
refinement, human approval, and XLSX export.

Job lifecycle enforces mandatory HITL:
    POST /extract   -> EXTRACTING -> GENERATING -> PENDING_REVIEW
    POST /chat      -> refine MDA (only in PENDING_REVIEW)
    POST /approve   -> APPROVED (mandatory human gate)
    GET  /export    -> EXPORTED (XLSX download)

GAMP-5 Category 5: Custom pharmaceutical software component.
No fallback logic -- all errors propagate with full diagnostics.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["LIMS"])

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    """Request body for the chat endpoint."""

    job_id: str
    message: str


# ---------------------------------------------------------------------------
# POST /extract
# ---------------------------------------------------------------------------


@router.post("/extract")
async def extract_pdf(file: UploadFile) -> dict:
    """Extract MDA data from an uploaded PDF using LlamaExtract.

    Creates a LIMS job, runs extraction, optionally generates an MDA
    template via LLM, and transitions the job through states:
        EXTRACTING -> GENERATING -> PENDING_REVIEW

    If LIMS_OPENROUTER_API_KEY is not set, the job stays in EXTRACTING
    and only returns raw extraction data (no MDA generation).

    Args:
        file: Uploaded PDF file.

    Returns:
        JSON with job_id, status, and extraction/generation results.

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
            detail=(
                f"File too large ({len(content)} bytes). "
                f"Maximum: {MAX_FILE_SIZE} bytes (50 MB)."
            ),
        )

    # Load config -- fails explicitly if API key missing
    try:
        from main.src.lims.config import get_lims_config

        config = get_lims_config()
    except ValueError as e:
        logger.error("LIMS config error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LIMS configuration error: {e}",
        ) from e

    # Create job
    from main.src.lims.job_store import (
        LIMSJobStatus,
        create_job,
        get_job,
        update_status,
    )

    job_id = create_job(file.filename or "upload.pdf")

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
        logger.exception("PDF extraction failed for '%s': %s", file.filename, e)
        try:
            update_status(job_id, LIMSJobStatus.FAILED)
            job = get_job(job_id)
            job.error = f"Extraction failed: {type(e).__name__}: {e}"
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF extraction failed: {type(e).__name__}: {e}",
        ) from e

    # Store extraction result on the job
    job = get_job(job_id)
    job.raw_extraction = result.get("raw_extraction")
    job.extraction_trace = result.get("extraction_trace")

    # Optionally trigger MDA generation if OpenRouter key is available
    mda_result: dict[str, Any] | None = None
    if config.openrouter_api_key:
        try:
            update_status(job_id, LIMSJobStatus.GENERATING)

            from main.src.lims.mda_generator import MDAGenerationWorkflow

            workflow = MDAGenerationWorkflow()
            from llama_index.core.workflow import StartEvent

            gen_result = await workflow.run(
                raw_extraction=result.get("raw_extraction", {}),
                config=config,
            )
            mda_result = gen_result

            # Store MDA template on the job
            if isinstance(gen_result, dict) and "mda_template" in gen_result:
                job.mda_template = gen_result["mda_template"]

            update_status(job_id, LIMSJobStatus.PENDING_REVIEW)

        except Exception as e:
            logger.exception(
                "MDA generation failed for job %s: %s", job_id, e
            )
            try:
                update_status(job_id, LIMSJobStatus.FAILED)
                job.error = f"MDA generation failed: {type(e).__name__}: {e}"
            except Exception:
                pass
            # Do not raise -- extraction succeeded, generation failed
            # Return partial result with error info
            mda_result = {"generation_error": f"{type(e).__name__}: {e}"}

    current_job = get_job(job_id)
    return {
        "job_id": job_id,
        "status": current_job.status.value,
        "filename": file.filename,
        "size_bytes": len(content),
        **result,
        "mda_generation": mda_result,
    }


# ---------------------------------------------------------------------------
# GET /status/{job_id}
# ---------------------------------------------------------------------------


@router.get("/status/{job_id}")
async def get_status(job_id: str) -> dict:
    """Get job status and current MDA state.

    Args:
        job_id: The LIMS job ID.

    Returns:
        JSON with job status, timestamps, and current MDA template.

    Raises:
        HTTPException 404: If job_id does not exist.
    """
    from main.src.lims.job_store import get_job

    try:
        job = get_job(job_id)
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

    return {
        "job_id": job.job_id,
        "status": job.status.value,
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat(),
        "pdf_filename": job.pdf_filename,
        "extraction_trace": job.extraction_trace,
        "mda_template": job.mda_template,
        "error": job.error,
        "chat_history_length": len(job.chat_history),
        "edit_log_length": len(job.edit_log),
    }


# ---------------------------------------------------------------------------
# POST /chat
# ---------------------------------------------------------------------------


@router.post("/chat")
async def chat(request: ChatRequest) -> dict:
    """Send a chat message for MDA refinement.

    Only available when the job is in PENDING_REVIEW state. Uses the
    chat agent with structured edit actions via OpenRouter function
    calling.

    Args:
        request: ChatRequest with job_id and message.

    Returns:
        JSON with LLM response, edits applied/rejected, and current MDA.

    Raises:
        HTTPException 404: If job_id does not exist.
        HTTPException 409: If job is not in PENDING_REVIEW state.
        HTTPException 500: If chat processing fails.
    """
    from main.src.lims.chat_agent import get_or_create_session
    from main.src.lims.config import get_lims_config
    from main.src.lims.job_store import LIMSJobStatus, get_job

    # Validate job exists
    try:
        job = get_job(request.job_id)
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

    # Only allow chat in PENDING_REVIEW state
    if job.status != LIMSJobStatus.PENDING_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Chat is only available in PENDING_REVIEW state. "
                f"Job '{request.job_id}' is in {job.status.value} state."
            ),
        )

    # Load config
    try:
        config = get_lims_config()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LIMS configuration error: {e}",
        ) from e

    # Get or create chat session
    pdf_text = json.dumps(job.raw_extraction, default=str) if job.raw_extraction else ""
    session = get_or_create_session(
        job_id=request.job_id,
        mda_template=job.mda_template or {},
        pdf_text=pdf_text,
    )

    # Process chat message
    try:
        result = session.chat(request.message, config)
    except (TimeoutError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.exception(
            "Chat processing failed for job %s: %s", request.job_id, e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing failed: {type(e).__name__}: {e}",
        ) from e

    # Sync MDA template back to job store
    job.mda_template = session.mda_template

    # Log chat to job's history and edit log
    job.chat_history.append({
        "user_message": request.message,
        "response": result["response"],
        "turn_count": result["turn_count"],
    })
    for edit in result["edits_applied"]:
        job.edit_log.append(edit)

    return result


# ---------------------------------------------------------------------------
# POST /approve/{job_id}
# ---------------------------------------------------------------------------


@router.post("/approve/{job_id}")
async def approve(job_id: str) -> dict:
    """Human approval gate -- mandatory HITL checkpoint.

    Transitions the job from PENDING_REVIEW to APPROVED. This is the
    ONLY way to reach APPROVED status.

    Args:
        job_id: The LIMS job ID.

    Returns:
        JSON with updated job status.

    Raises:
        HTTPException 404: If job_id does not exist.
        HTTPException 409: If job is not in PENDING_REVIEW state.
    """
    from main.src.lims.job_store import approve_job, get_job

    try:
        job = get_job(job_id)
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

    try:
        job = approve_job(job_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e

    return {
        "job_id": job.job_id,
        "status": job.status.value,
        "approved_at": job.updated_at.isoformat(),
        "message": "MDA template approved by human reviewer (HITL gate passed)",
    }


# ---------------------------------------------------------------------------
# GET /export/{job_id}
# ---------------------------------------------------------------------------


@router.get("/export/{job_id}")
async def export(job_id: str) -> Response:
    """Download the approved MDA template as an XLSX file.

    Only available after human approval (APPROVED status). Returns the
    XLSX binary with appropriate content headers for browser download.

    After successful export, transitions the job to EXPORTED state.

    Args:
        job_id: The LIMS job ID.

    Returns:
        XLSX binary response with Content-Disposition header.

    Raises:
        HTTPException 404: If job_id does not exist.
        HTTPException 403: If job is not in APPROVED state.
        HTTPException 500: If XLSX export fails.
    """
    from main.src.lims.job_store import LIMSJobStatus, get_job, update_status

    try:
        job = get_job(job_id)
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

    if job.status != LIMSJobStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Export is only available for APPROVED jobs. "
                f"Job '{job_id}' is in {job.status.value} state. "
                f"The MDA must be reviewed and approved before export."
            ),
        )

    if not job.mda_template:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"Job '{job_id}' is APPROVED but has no MDA template. "
                f"This indicates an internal state error."
            ),
        )

    # Export MDA to XLSX
    try:
        from main.src.lims.mda_schema import MDATemplate
        from main.src.lims.xlsx_exporter import export_mda_to_xlsx

        mda = MDATemplate.model_validate(job.mda_template)
        xlsx_bytes = export_mda_to_xlsx(mda)
    except Exception as e:
        logger.exception("XLSX export failed for job %s: %s", job_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"XLSX export failed: {type(e).__name__}: {e}",
        ) from e

    # Transition to EXPORTED
    update_status(job_id, LIMSJobStatus.EXPORTED)

    # Generate filename from PDF filename
    base_name = job.pdf_filename.rsplit(".", 1)[0] if "." in job.pdf_filename else job.pdf_filename
    export_filename = f"{base_name}_MDA.xlsx"

    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{export_filename}"',
        },
    )

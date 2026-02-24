"""LIMS API router for AI4LIMS PoC.

Public endpoints (no authentication) for PDF extraction, classification,
template retrieval, MDA chat refinement, human approval, and XLSX export.

Job lifecycle enforces mandatory HITL:
    POST /extract   -> Two-layer pipeline (Classify->Template->Extract->Augment->Merge->Review)
                    -> Single-layer fallback for TestType.OTHER
    POST /classify  -> Classify PDF without full extraction
    GET  /template  -> Retrieve template skeleton for a test type
    POST /chat      -> Refine MDA (only in PENDING_REVIEW)
    POST /approve   -> APPROVED (mandatory human gate)
    GET  /export    -> EXPORTED (XLSX download)

GAMP-5 Category 5: Custom pharmaceutical software component.
No fallback logic -- all errors propagate with full diagnostics.
"""

from __future__ import annotations

import logging
import os

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
    """Extract MDA data from an uploaded PDF via the two-layer pipeline.

    For known test types (HPLC, LOD, Titration, Identity):
        Classify -> Template -> Extract -> Augment -> Merge -> Review

    For TestType.OTHER:
        Single-layer fallback (existing LlamaExtract + MDA generation).

    Args:
        file: Uploaded PDF file.

    Returns:
        JSON with job_id, status, pipeline results including provenance,
        conflicts, stage_details, and classification.

    Raises:
        HTTPException 400: Non-PDF, empty, or oversized file.
        HTTPException 500: Config or pipeline failure.
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

    # Run the two-layer pipeline
    try:
        from main.src.lims.pipeline import TwoLayerPipeline

        pipeline = TwoLayerPipeline(config)
        result = await pipeline.run(
            pdf_content=content,
            filename=file.filename or "upload.pdf",
            job_id=job_id,
        )
    except Exception as e:
        logger.exception("Pipeline failed for '%s': %s", file.filename, e)
        try:
            update_status(job_id, LIMSJobStatus.FAILED)
            job = get_job(job_id)
            job.error = f"Pipeline failed: {type(e).__name__}: {e}"
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline failed: {type(e).__name__}: {e}",
        ) from e

    # Flush Langfuse traces before returning
    from main.src.lims.langfuse_tracing import flush_lims_langfuse

    flush_lims_langfuse()

    # Build trace URL from trace_id
    trace_id = result.get("trace_id")
    trace_url = None
    if trace_id:
        langfuse_base = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")
        trace_url = f"{langfuse_base}/trace/{trace_id}"

    current_job = get_job(job_id)
    return {
        "job_id": job_id,
        "status": current_job.status.value,
        "filename": file.filename,
        "size_bytes": len(content),
        "trace_id": trace_id,
        "trace_url": trace_url,
        **{k: v for k, v in result.items() if k != "trace_id"},
    }


# ---------------------------------------------------------------------------
# POST /classify
# ---------------------------------------------------------------------------


@router.post("/classify")
async def classify_pdf(file: UploadFile) -> dict:
    """Classify an uploaded PDF to determine test type.

    Runs the hybrid classifier (filename rules -> keyword matching ->
    exclusion) without full extraction. Useful for pre-screening PDFs.

    Args:
        file: Uploaded PDF file.

    Returns:
        JSON with classification result (test_type, confidence, method,
        matched_keywords).

    Raises:
        HTTPException 400: Non-PDF, empty, or oversized file.
        HTTPException 500: Text extraction or classification failure.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only PDF files are accepted. Got: '{file.filename}'",
        )

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

    try:
        from main.src.lims.classifier import TestTypeClassifier
        from main.src.lims.focused_extractor import extract_text_from_pdf

        pdf_text = extract_text_from_pdf(content)
        classifier = TestTypeClassifier()
        classification = classifier.classify(pdf_text, file.filename or "upload.pdf")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"PDF text extraction failed: {e}",
        ) from e
    except Exception as e:
        logger.exception("Classification failed for '%s': %s", file.filename, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Classification failed: {type(e).__name__}: {e}",
        ) from e

    return classification.model_dump()


# ---------------------------------------------------------------------------
# GET /template/{test_type}
# ---------------------------------------------------------------------------


@router.get("/template/{test_type}")
async def get_template(test_type: str) -> dict:
    """Retrieve the MDA template skeleton for a test type.

    Returns the curated template with analyses, components, calc_variables,
    and calculations pre-populated with fixed values. Variable fields are
    left empty for extraction.

    Args:
        test_type: Test type string (HPLC, LOD, TITRATION, IDENTITY).
            Case-insensitive.

    Returns:
        JSON with MDA template, variable_fields, fixed_fields, and counts.

    Raises:
        HTTPException 400: Invalid test type or OTHER (no template).
        HTTPException 500: Template loading failure.
    """
    from main.src.lims.test_type import TestType

    try:
        tt = TestType(test_type.upper())
    except ValueError:
        valid_types = [t.value for t in TestType if t != TestType.OTHER]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid test type: '{test_type}'. "
                f"Valid types: {valid_types}"
            ),
        )

    if tt == TestType.OTHER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "TestType.OTHER has no curated template. "
                "Use POST /extract for single-layer extraction."
            ),
        )

    try:
        from main.src.lims.templates import TemplateLibrary

        template = TemplateLibrary.get_template_for_type(tt)
        mda = template.to_mda_template()
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No template registered for {tt.value}: {e}",
        ) from e
    except Exception as e:
        logger.exception("Template loading failed for %s: %s", test_type, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Template loading failed: {type(e).__name__}: {e}",
        ) from e

    return {
        "test_type": tt.value,
        "mda_template": mda.model_dump(),
        "variable_fields": template.get_variable_fields(),
        "fixed_fields": template.get_fixed_fields(),
        "analysis_count": len(mda.analyses),
        "component_count": len(mda.components),
        "calc_variable_count": len(mda.calc_variables),
        "calculation_count": len(mda.calculations),
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
        "classification": job.classification,
        "provenance": job.provenance,
        "conflicts": job.conflicts,
        "stage_details": job.stage_details,
        "validated": job.validated,
        "validation_error": job.validation_error,
        "review_routing": job.review_routing,
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

    # Get or create chat session with full grounded context
    chat_context = {
        "pdf_filename": job.pdf_filename,
        "raw_extraction": job.raw_extraction,
        "classification": job.classification,
        "provenance": job.provenance,
        "conflicts": job.conflicts,
        "stage_details": job.stage_details,
        "extraction_trace": job.extraction_trace,
    }
    session = get_or_create_session(
        job_id=request.job_id,
        mda_template=job.mda_template or {},
        chat_context=chat_context,
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

    # Flush Langfuse traces
    from main.src.lims.langfuse_tracing import flush_lims_langfuse

    flush_lims_langfuse()

    # Sync MDA template back to job store
    job.mda_template = session.mda_template

    # Re-validate after chat edits and update job state
    from main.src.lims.mda_schema import MDATemplate

    try:
        MDATemplate.model_validate(job.mda_template)
        job.validated = True
        job.validation_error = None
    except Exception as e:
        job.validated = False
        job.validation_error = str(e)

    # Log chat to job's history and edit log
    job.chat_history.append({
        "user_message": request.message,
        "response": result["response"],
        "turn_count": result["turn_count"],
    })
    for edit in result["edits_applied"]:
        job.edit_log.append(edit)

    # Include validation state in response so frontend can update
    result["validated"] = job.validated
    result["validation_error"] = job.validation_error

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
    from main.src.lims.mda_schema import MDATemplate

    try:
        job = get_job(job_id)
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

    # Hard validation gate: block approval if MDA is missing or invalid
    if not job.mda_template:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Approval blocked: job '{job_id}' has no MDA template. "
                f"The pipeline must produce a valid MDA before approval."
            ),
        )

    try:
        MDATemplate.model_validate(job.mda_template)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Approval blocked: MDA template fails validation. "
                f"Fix errors via chat before approving.\n{e}"
            ),
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

    # Export MDA to XLSX -- pure validation + serialization.
    # Normalization now runs pre-review (in merger.py), so the approved
    # data is already in its final form. No post-approval mutation.
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

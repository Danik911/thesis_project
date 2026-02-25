"""BI API router for MES Agentic BI upload + grid foundation."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query, UploadFile, status
from pydantic import BaseModel

from main.src.bi.config import get_bi_config
from main.src.bi.data_parser import parse_file
from main.src.bi.filter_engine import get_filter_engine
from main.src.bi.session_store import create_session, get_session

logger = logging.getLogger(__name__)

router = APIRouter(tags=["BI"])


class BIFilterItem(BaseModel):
    column: str
    operator: str
    value: Any = None


class BIFilterRequest(BaseModel):
    filters: list[BIFilterItem]


@router.post("/upload")
async def upload_file(file: UploadFile) -> dict:
    """Upload XLSX/CSV data and initialize a BI session."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must include a filename",
        )

    config = get_bi_config()
    max_size_bytes = config.max_upload_size_mb * 1024 * 1024
    content = await file.read()

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )

    if len(content) > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"File too large ({len(content)} bytes). "
                f"Maximum allowed size is {max_size_bytes} bytes ({config.max_upload_size_mb} MB)."
            ),
        )

    try:
        dataframe = parse_file(content, file.filename)
        session_id = create_session(file.filename, dataframe)
        session = get_session(session_id)
        preview = get_filter_engine(session_id).get_page(page=1, page_size=100)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("BI upload failed for '%s': %s", file.filename, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"BI upload failed: {type(exc).__name__}: {exc}",
        ) from exc

    return {
        "session_id": session.session_id,
        "filename": session.filename,
        "total_rows": session.total_rows,
        "total_columns": session.total_columns,
        "columns": [column.model_dump() for column in session.columns],
        "preview": preview,
    }


@router.get("/data/{session_id}")
async def get_data_page(
    session_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=50000),
) -> dict:
    """Fetch paginated session data for grid rendering."""
    try:
        return get_filter_engine(session_id).get_page(page=page, page_size=page_size)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/schema/{session_id}")
async def get_schema(session_id: str) -> dict:
    """Fetch session schema metadata for sidebar display."""
    try:
        session = get_session(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return {
        "session_id": session.session_id,
        "filename": session.filename,
        "total_rows": session.total_rows,
        "total_columns": session.total_columns,
        "columns": [column.model_dump() for column in session.columns],
    }


@router.post("/filter/{session_id}")
async def apply_filters(session_id: str, request: BIFilterRequest) -> dict:
    """Apply full filter set for a BI session and return updated preview."""
    try:
        get_session(session_id)
        engine = get_filter_engine(session_id)
        normalized_filters = [item.model_dump() for item in request.filters]
        total_filtered_rows = engine.set_filters(normalized_filters)
        preview = engine.get_page(page=1, page_size=100)
        return {
            "total_filtered_rows": total_filtered_rows,
            "active_filters": engine.get_active_filters(),
            "preview": preview,
        }
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

"""BI API router for MES Agentic BI upload + grid foundation."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.bi.auth import get_current_user, get_optional_user
from src.bi.auth_models import BIUser, UserRole
from src.bi.chart_engine import get_chart_data, recommend_charts
from src.bi.config import get_bi_config
from src.bi.copilot import chat as copilot_chat
from src.bi.data_parser import parse_file
from src.bi.excel_exporter import export_excel
from src.bi.filter_engine import get_filter_engine
from src.bi.pdf_exporter import export_pdf
from src.bi.session_store import create_session, get_session
from src.bi.snowflake_connector import (
    fetch_stage_file as sf_fetch_stage_file,
    fetch_table as sf_fetch_table,
    list_stage_files as sf_list_stage_files,
    list_tables as sf_list_tables,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["BI"])


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------


def _get_user_dep():
    """Return appropriate auth dependency based on BI_AUTH_ENABLED."""
    config = get_bi_config()
    if config.auth_enabled:
        return get_current_user
    return get_optional_user


def _apply_site_filter(dataframe: pd.DataFrame, user: BIUser | None) -> pd.DataFrame:
    """Filter DataFrame to user's site if they are an Operator.

    Returns the full DataFrame for Admins or when auth is disabled.
    Returns EMPTY DataFrame if the site column is missing (never leak data).
    """
    if user is None or user.role != UserRole.OPERATOR or not user.site:
        return dataframe

    config = get_bi_config()
    site_col = config.site_column_name

    if site_col not in dataframe.columns:
        logger.warning(
            "Site column '%s' not found in data columns %s for operator %s. "
            "Returning EMPTY DataFrame to enforce RBAC.",
            site_col,
            list(dataframe.columns),
            user.email,
        )
        return dataframe.head(0)

    filtered = dataframe[dataframe[site_col].astype(str) == user.site]
    logger.info(
        "Site filter applied: user=%s site=%s rows=%d->%d",
        user.email,
        user.site,
        len(dataframe),
        len(filtered),
    )
    return filtered


def _validate_session_access(session_id: str, user: BIUser | None) -> None:
    """Validate that the user has access to the given session.

    Admins can access all sessions. Operators can only access their own.
    """
    if user is None:
        return  # Auth disabled
    if user.role == UserRole.ADMIN:
        return  # Admins can access all
    session = get_session(session_id)
    if session.user_id and session.user_id != user.sub:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: session belongs to another user",
        )


def _require_admin_when_auth_enabled(user: BIUser | None) -> None:
    """Require Admin role when BI auth is enabled.

    This hardens server-side authorization for sensitive endpoints even if the UI hides them.
    """
    config = get_bi_config()
    if not config.auth_enabled:
        return
    if user is None or user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required for Snowflake operations",
        )


class BIFilterItem(BaseModel):
    column: str
    operator: str
    value: Any = None


class BIFilterRequest(BaseModel):
    filters: list[BIFilterItem]


class BIChatRequest(BaseModel):
    message: str


class BIChartDataRequest(BaseModel):
    chart_type: str
    x_column: str
    y_column: str | None = None
    aggregation: str | None = None
    group_by: str | None = None
    bins: int = 20
    limit: int = 50


class SnowflakeConnectRequest(BaseModel):
    account: str
    user: str
    password: str
    warehouse: str
    database: str
    schema_name: str


class SnowflakeLoadTableRequest(SnowflakeConnectRequest):
    table_name: str


class SnowflakeLoadStageFileRequest(SnowflakeConnectRequest):
    stage_name: str
    file_path: str


def _snowflake_error_detail(prefix: str, exc: Exception) -> str:
    return f"{prefix}: {type(exc).__name__}: {exc}"


@router.get("/me")
async def get_current_user_info(
    user: BIUser | None = Depends(get_optional_user),
) -> dict:
    """Return current user information (role, site, groups)."""
    config = get_bi_config()
    if user is None:
        return {"authenticated": False, "auth_enabled": config.auth_enabled}
    return {
        "authenticated": True,
        "auth_enabled": config.auth_enabled,
        "sub": user.sub,
        "email": user.email,
        "role": user.role.value,
        "site": user.site,
        "groups": user.groups,
        "username": user.username,
    }


@router.post("/upload")
async def upload_file(
    file: UploadFile,
    user: BIUser | None = Depends(_get_user_dep()),
) -> dict:
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
        dataframe = _apply_site_filter(dataframe, user)
        session_id = create_session(
            file.filename,
            dataframe,
            user_id=user.sub if user else None,
            user_role=user.role.value if user else None,
            user_site=user.site if user else None,
        )
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
    user: BIUser | None = Depends(_get_user_dep()),
) -> dict:
    """Fetch paginated session data for grid rendering."""
    try:
        _validate_session_access(session_id, user)
        return get_filter_engine(session_id).get_page(page=page, page_size=page_size)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/schema/{session_id}")
async def get_schema(
    session_id: str,
    user: BIUser | None = Depends(_get_user_dep()),
) -> dict:
    """Fetch session schema metadata for sidebar display."""
    try:
        _validate_session_access(session_id, user)
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
async def apply_filters(
    session_id: str,
    request: BIFilterRequest,
    user: BIUser | None = Depends(_get_user_dep()),
) -> dict:
    """Apply full filter set for a BI session and return updated preview."""
    try:
        _validate_session_access(session_id, user)
        get_session(session_id)
        engine = get_filter_engine(session_id)
        normalized_filters = [item.model_dump() for item in request.filters]
        total_filtered_rows = engine.set_filters(normalized_filters)
        preview = engine.get_page(page=1, page_size=100)
        return {
            "total_filtered_rows": total_filtered_rows,
            "active_filters": engine.get_active_filters(),
            "preview": preview,
            "filtered_columns": engine.get_filtered_column_metadata(),
        }
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/export/excel/{session_id}")
async def export_filtered_excel(
    session_id: str,
    user: BIUser | None = Depends(_get_user_dep()),
) -> StreamingResponse:
    """Download filtered BI data as an Excel file."""
    try:
        _validate_session_access(session_id, user)
        session = get_session(session_id)
        file_buffer = export_excel(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("BI Excel export failed for session '%s': %s", session_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"BI Excel export failed: {type(exc).__name__}: {exc}",
        ) from exc

    export_stem = Path(session.filename).stem or "bi_export"

    return StreamingResponse(
        content=file_buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{export_stem}_filtered.xlsx"'
        },
    )


@router.get("/export/pdf/{session_id}")
async def export_filtered_pdf(
    session_id: str,
    user: BIUser | None = Depends(_get_user_dep()),
) -> StreamingResponse:
    """Download filtered BI data as a PDF file."""
    try:
        _validate_session_access(session_id, user)
        session = get_session(session_id)
        file_buffer = export_pdf(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("BI PDF export failed for session '%s': %s", session_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"BI PDF export failed: {type(exc).__name__}: {exc}",
        ) from exc

    export_stem = Path(session.filename).stem or "bi_export"

    return StreamingResponse(
        content=file_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{export_stem}_filtered.pdf"'},
    )


@router.post("/chat/{session_id}")
async def chat_with_copilot(
    session_id: str,
    request: BIChatRequest,
    user: BIUser | None = Depends(_get_user_dep()),
) -> dict:
    """Send a message to the BI copilot and receive an AI-generated response."""
    if not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chat message must not be empty",
        )
    try:
        _validate_session_access(session_id, user)
        get_session(session_id)  # Validate session exists
        result = copilot_chat(session_id, request.message, user=user)
        return result
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("BI chat failed for session '%s': %s", session_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"BI chat failed: {type(exc).__name__}: {exc}",
        ) from exc


# ---------------------------------------------------------------------------
# Chart endpoints
# ---------------------------------------------------------------------------


@router.get("/charts/recommend/{session_id}")
async def recommend_session_charts(
    session_id: str,
    user: BIUser | None = Depends(_get_user_dep()),
) -> dict:
    """Analyze session schema and return recommended chart configurations."""
    try:
        _validate_session_access(session_id, user)
        get_session(session_id)
        return recommend_charts(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Chart recommendation failed for session '%s': %s", session_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chart recommendation failed: {type(exc).__name__}: {exc}",
        ) from exc


@router.post("/charts/data/{session_id}")
async def get_session_chart_data(
    session_id: str,
    request: BIChartDataRequest,
    user: BIUser | None = Depends(_get_user_dep()),
) -> dict:
    """Compute aggregated data for a specific chart configuration."""
    try:
        _validate_session_access(session_id, user)
        get_session(session_id)
        return get_chart_data(
            session_id,
            chart_type=request.chart_type,
            x_column=request.x_column,
            y_column=request.y_column,
            aggregation=request.aggregation,
            group_by=request.group_by,
            bins=request.bins,
            limit=request.limit,
        )
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Chart data failed for session '%s': %s", session_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chart data failed: {type(exc).__name__}: {exc}",
        ) from exc


# ---------------------------------------------------------------------------
# Snowflake data source endpoints
# ---------------------------------------------------------------------------


@router.post("/snowflake/tables")
async def list_snowflake_tables(
    request: SnowflakeConnectRequest,
    user: BIUser | None = Depends(_get_user_dep()),
) -> dict:
    """List tables/views in a Snowflake schema."""
    try:
        _require_admin_when_auth_enabled(user)
        tables = sf_list_tables(
            account=request.account,
            user=request.user,
            password=request.password,
            warehouse=request.warehouse,
            database=request.database,
            schema=request.schema_name,
        )
        return {
            "tables": tables,
            "database": request.database,
            "schema": request.schema_name,
        }
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Snowflake list_tables failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_snowflake_error_detail("Snowflake connection failed", exc),
        ) from exc


@router.post("/snowflake/stages/{stage_name}/files")
async def list_snowflake_stage_files(
    stage_name: str,
    request: SnowflakeConnectRequest,
    user: BIUser | None = Depends(_get_user_dep()),
) -> dict:
    """List files in a named Snowflake stage."""
    try:
        _require_admin_when_auth_enabled(user)
        files = sf_list_stage_files(
            account=request.account,
            user=request.user,
            password=request.password,
            warehouse=request.warehouse,
            database=request.database,
            schema=request.schema_name,
            stage_name=stage_name,
        )
        return {
            "files": files,
            "stage": stage_name,
        }
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Snowflake list_stage_files failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_snowflake_error_detail("Snowflake stage listing failed", exc),
        ) from exc


@router.post("/snowflake/load/table")
async def load_snowflake_table(
    request: SnowflakeLoadTableRequest,
    user: BIUser | None = Depends(_get_user_dep()),
) -> dict:
    """Load a Snowflake table into a BI session."""
    try:
        _require_admin_when_auth_enabled(user)
        dataframe = sf_fetch_table(
            account=request.account,
            user=request.user,
            password=request.password,
            warehouse=request.warehouse,
            database=request.database,
            schema=request.schema_name,
            table_name=request.table_name,
        )

        dataframe = _apply_site_filter(dataframe, user)
        source_name = f"sf://{request.database}.{request.schema_name}.{request.table_name}"
        session_id = create_session(
            source_name,
            dataframe,
            user_id=user.sub if user else None,
            user_role=user.role.value if user else None,
            user_site=user.site if user else None,
        )
        session = get_session(session_id)
        preview = get_filter_engine(session_id).get_page(page=1, page_size=100)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Snowflake load_table failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_snowflake_error_detail("Snowflake load failed", exc),
        ) from exc

    return {
        "session_id": session.session_id,
        "filename": session.filename,
        "total_rows": session.total_rows,
        "total_columns": session.total_columns,
        "columns": [column.model_dump() for column in session.columns],
        "preview": preview,
    }


@router.post("/snowflake/load/stage-file")
async def load_snowflake_stage_file(
    request: SnowflakeLoadStageFileRequest,
    user: BIUser | None = Depends(_get_user_dep()),
) -> dict:
    """Download a stage file, parse it, and load into a BI session."""
    try:
        _require_admin_when_auth_enabled(user)
        dataframe = sf_fetch_stage_file(
            account=request.account,
            user=request.user,
            password=request.password,
            warehouse=request.warehouse,
            database=request.database,
            schema=request.schema_name,
            stage_name=request.stage_name,
            file_path=request.file_path,
        )

        dataframe = _apply_site_filter(dataframe, user)
        source_name = f"sf://@{request.stage_name}/{request.file_path}"
        session_id = create_session(
            source_name,
            dataframe,
            user_id=user.sub if user else None,
            user_role=user.role.value if user else None,
            user_site=user.site if user else None,
        )
        session = get_session(session_id)
        preview = get_filter_engine(session_id).get_page(page=1, page_size=100)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Snowflake load_stage_file failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_snowflake_error_detail("Snowflake stage file load failed", exc),
        ) from exc

    return {
        "session_id": session.session_id,
        "filename": session.filename,
        "total_rows": session.total_rows,
        "total_columns": session.total_columns,
        "columns": [column.model_dump() for column in session.columns],
        "preview": preview,
    }

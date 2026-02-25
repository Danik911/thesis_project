"""In-memory session store for BI DataFrames with TTL and LRU eviction."""

from __future__ import annotations

from collections import OrderedDict
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import pandas as pd
from pydantic import BaseModel

from .config import get_bi_config
from .data_parser import get_column_metadata


class BIColumn(BaseModel):
    """Column metadata for a BI upload session."""

    name: str
    dtype: str
    unique_count: int
    null_count: int
    sample_values: list[Any]


class BISession(BaseModel):
    """Session metadata for uploaded BI datasets."""

    session_id: str
    filename: str
    created_at: datetime
    updated_at: datetime
    total_rows: int
    total_columns: int
    columns: list[BIColumn]


_sessions: dict[str, BISession] = {}
_dataframes: dict[str, pd.DataFrame] = {}
_lru_order: OrderedDict[str, None] = OrderedDict()


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _remove_session(session_id: str) -> None:
    _sessions.pop(session_id, None)
    _dataframes.pop(session_id, None)
    _lru_order.pop(session_id, None)


def _cleanup_expired_sessions() -> None:
    ttl_seconds = get_bi_config().session_ttl_seconds
    now = _now_utc()

    for session_id, session in list(_sessions.items()):
        age_seconds = (now - session.updated_at).total_seconds()
        if age_seconds > ttl_seconds:
            _remove_session(session_id)


def _touch_session(session_id: str) -> None:
    if session_id not in _sessions:
        return

    session = _sessions[session_id]
    session.updated_at = _now_utc()

    if session_id in _lru_order:
        _lru_order.move_to_end(session_id)
    else:
        _lru_order[session_id] = None


def _evict_if_needed() -> None:
    max_sessions = get_bi_config().max_sessions
    while len(_sessions) >= max_sessions and _lru_order:
        oldest_session_id, _ = _lru_order.popitem(last=False)
        _remove_session(oldest_session_id)


def create_session(filename: str, dataframe: pd.DataFrame) -> str:
    """Create a BI session and store DataFrame + schema metadata."""
    if not filename.strip():
        raise ValueError("filename must not be empty")

    _cleanup_expired_sessions()
    _evict_if_needed()

    session_id = uuid4().hex
    now = _now_utc()

    column_metadata = [BIColumn.model_validate(item) for item in get_column_metadata(dataframe)]

    session = BISession(
        session_id=session_id,
        filename=filename,
        created_at=now,
        updated_at=now,
        total_rows=int(len(dataframe)),
        total_columns=int(len(dataframe.columns)),
        columns=column_metadata,
    )

    _sessions[session_id] = session
    _dataframes[session_id] = dataframe
    _lru_order[session_id] = None

    return session_id


def get_session(session_id: str) -> BISession:
    """Return session metadata by ID."""
    _cleanup_expired_sessions()
    if session_id not in _sessions:
        raise KeyError(f"BI session '{session_id}' not found")

    _touch_session(session_id)
    return _sessions[session_id]


def get_dataframe(session_id: str) -> pd.DataFrame:
    """Return raw DataFrame for a session."""
    _cleanup_expired_sessions()
    if session_id not in _dataframes:
        raise KeyError(f"BI session '{session_id}' not found")

    _touch_session(session_id)
    return _dataframes[session_id]


def get_page(session_id: str, page: int = 1, page_size: int = 100) -> dict[str, Any]:
    """Return paginated rows for a BI session."""
    if page < 1:
        raise ValueError("page must be >= 1")
    if page_size < 1:
        raise ValueError("page_size must be >= 1")

    dataframe = get_dataframe(session_id)
    total_rows = int(len(dataframe))
    start = (page - 1) * page_size
    end = start + page_size

    rows = dataframe.iloc[start:end].replace({pd.NA: None}).to_dict(orient="records")
    total_pages = max((total_rows + page_size - 1) // page_size, 1)

    return {
        "rows": rows,
        "total_rows": total_rows,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }

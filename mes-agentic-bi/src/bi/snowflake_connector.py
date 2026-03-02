"""Snowflake data source connector for MES Agentic BI."""

from __future__ import annotations

import pathlib
import tempfile
from typing import Any

import pandas as pd

from .config import get_bi_config


def _require_non_empty(value: str, name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{name} is required")
    return normalized


def _validate_stage_name(stage_name: str) -> str:
    normalized = _require_non_empty(stage_name, "stage_name")
    if ";" in normalized or "\n" in normalized or "\r" in normalized:
        raise ValueError("stage_name contains unsupported characters")
    return normalized


def _safe_identifier(name: str) -> str:
    normalized = _require_non_empty(name, "table_name")
    if ";" in normalized or "\n" in normalized or "\r" in normalized:
        raise ValueError("table_name contains unsupported characters")
    return f'"{normalized.replace('"', '""')}"'


def _get_connection(
    account: str,
    user: str,
    password: str,
    warehouse: str,
    database: str,
    schema: str,
) -> Any:
    """Open a Snowflake connection. Raises on failure."""
    try:
        import snowflake.connector
    except ImportError as exc:
        raise RuntimeError(
            "snowflake-connector-python is not installed. "
            "Install dependencies with: uv sync"
        ) from exc

    return snowflake.connector.connect(
        account=_require_non_empty(account, "account"),
        user=_require_non_empty(user, "user"),
        password=_require_non_empty(password, "password"),
        warehouse=_require_non_empty(warehouse, "warehouse"),
        database=_require_non_empty(database, "database"),
        schema=_require_non_empty(schema, "schema_name"),
        client_session_keep_alive=False,
    )


def list_tables(
    account: str,
    user: str,
    password: str,
    warehouse: str,
    database: str,
    schema: str,
) -> list[dict[str, Any]]:
    """Return list of tables/views in the given schema."""
    conn = _get_connection(account, user, password, warehouse, database, schema)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT TABLE_NAME, TABLE_TYPE, ROW_COUNT "
            "FROM INFORMATION_SCHEMA.TABLES "
            "WHERE TABLE_SCHEMA = %s "
            "ORDER BY TABLE_NAME",
            (_require_non_empty(schema, "schema_name").upper(),),
        )
        rows = cur.fetchall()
        return [
            {
                "name": row[0],
                "kind": row[1],
                "row_count": int(row[2]) if row[2] is not None else None,
            }
            for row in rows
        ]
    finally:
        conn.close()


def list_stage_files(
    account: str,
    user: str,
    password: str,
    warehouse: str,
    database: str,
    schema: str,
    stage_name: str,
) -> list[dict[str, Any]]:
    """Return list of files in a Snowflake stage."""
    validated_stage = _validate_stage_name(stage_name)
    conn = _get_connection(account, user, password, warehouse, database, schema)
    try:
        cur = conn.cursor()
        cur.execute(f"LIST @{validated_stage}")
        rows = cur.fetchall()
        return [
            {
                "name": row[0],
                "size": int(row[1]) if len(row) > 1 and row[1] is not None else 0,
                "last_modified": str(row[3]) if len(row) > 3 and row[3] is not None else "",
            }
            for row in rows
        ]
    finally:
        conn.close()


def fetch_table(
    account: str,
    user: str,
    password: str,
    warehouse: str,
    database: str,
    schema: str,
    table_name: str,
    limit: int | None = None,
) -> pd.DataFrame:
    """Fetch a Snowflake table/view as a pandas DataFrame."""
    config = get_bi_config()
    effective_limit = limit if limit is not None else config.max_rows

    conn = _get_connection(account, user, password, warehouse, database, schema)
    try:
        cur = conn.cursor()
        safe_table_name = _safe_identifier(table_name)
        cur.execute(f"SELECT * FROM {safe_table_name} LIMIT {int(effective_limit)}")
        dataframe = cur.fetch_pandas_all()
    finally:
        conn.close()

    dataframe = dataframe.convert_dtypes()

    if dataframe.empty:
        raise ValueError(f"Snowflake table '{table_name}' returned no rows")

    if len(dataframe) > config.max_rows:
        raise ValueError(
            f"Snowflake table '{table_name}' has {len(dataframe)} rows, "
            f"which exceeds BI_MAX_ROWS={config.max_rows}"
        )

    return dataframe


def fetch_stage_file(
    account: str,
    user: str,
    password: str,
    warehouse: str,
    database: str,
    schema: str,
    stage_name: str,
    file_path: str,
) -> pd.DataFrame:
    """Download a file from a Snowflake stage and parse as a DataFrame."""
    from .data_parser import parse_file

    validated_stage = _validate_stage_name(stage_name)
    normalized_file_path = _require_non_empty(file_path, "file_path")
    if ";" in normalized_file_path or "\n" in normalized_file_path or "\r" in normalized_file_path:
        raise ValueError("file_path contains unsupported characters")

    conn = _get_connection(account, user, password, warehouse, database, schema)
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            cur = conn.cursor()
            cur.execute(f"GET @{validated_stage}/{normalized_file_path} file://{tmp_dir}/")

            tmp_path = pathlib.Path(tmp_dir)
            downloaded = [path for path in tmp_path.iterdir() if path.is_file()]
            if not downloaded:
                raise ValueError(
                    f"No files were downloaded from stage '{validated_stage}' for path '{normalized_file_path}'"
                )

            local_file = downloaded[0]
            content = local_file.read_bytes()
            filename = pathlib.Path(normalized_file_path).name
            dataframe = parse_file(content, filename)
    finally:
        conn.close()

    return dataframe

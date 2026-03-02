"""File parsing and schema metadata extraction for BI uploads."""

from __future__ import annotations

import io
from typing import Any

import pandas as pd

from .config import get_bi_config


def _to_python_value(value: Any) -> Any:
    """Convert pandas/numpy values into JSON-serializable Python values."""
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    return value


def parse_file(content: bytes, filename: str) -> pd.DataFrame:
    """Parse XLSX/CSV content into a pandas DataFrame.

    Args:
        content: Raw uploaded file bytes.
        filename: Original file name.

    Returns:
        Parsed DataFrame with inferred column dtypes.

    Raises:
        ValueError: For unsupported formats, empty files, parse errors, or row limit violations.
    """
    if not filename:
        raise ValueError("Filename is required for BI file parsing")

    if not content:
        raise ValueError("Uploaded file is empty")

    normalized = filename.lower()
    buffer = io.BytesIO(content)

    try:
        if normalized.endswith(".xlsx"):
            dataframe = pd.read_excel(buffer)
        elif normalized.endswith(".csv"):
            dataframe = pd.read_csv(buffer, low_memory=False)
        else:
            raise ValueError(f"Unsupported file type: '{filename}'. Only .xlsx and .csv are accepted.")
    except Exception as exc:
        raise ValueError(f"Failed to parse uploaded file '{filename}': {type(exc).__name__}: {exc}") from exc

    dataframe = dataframe.convert_dtypes()

    if dataframe.empty:
        raise ValueError(f"Parsed file '{filename}' contains no rows")

    config = get_bi_config()
    if len(dataframe) > config.max_rows:
        raise ValueError(
            f"Uploaded file has {len(dataframe)} rows, which exceeds BI_MAX_ROWS={config.max_rows}"
        )

    return dataframe


def get_column_metadata(
    dataframe: pd.DataFrame,
    sample_size: int = 50,
    include_value_counts: bool = False,
) -> list[dict[str, Any]]:
    """Build per-column metadata for schema sidebar and API responses."""
    columns: list[dict[str, Any]] = []

    for column_name in dataframe.columns:
        series = dataframe[column_name]
        non_null_unique = series.dropna().drop_duplicates().head(sample_size)
        sample_values = [_to_python_value(value) for value in non_null_unique.tolist()]

        col_meta: dict[str, Any] = {
            "name": str(column_name),
            "dtype": str(series.dtype),
            "unique_count": int(series.nunique(dropna=True)),
            "null_count": int(series.isna().sum()),
            "sample_values": sample_values,
        }

        if include_value_counts:
            vc = series.dropna().value_counts().head(sample_size)
            col_meta["value_counts"] = {
                _to_python_value(k): int(v) for k, v in vc.items()
            }

        columns.append(col_meta)

    return columns

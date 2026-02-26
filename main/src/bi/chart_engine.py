"""Chart recommendation and data aggregation engine for MES Agentic BI."""

from __future__ import annotations

import logging
import math
import re
from typing import Any

import numpy as np
import pandas as pd

from .filter_engine import get_filter_engine
from .session_store import BIColumn, get_session

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Column classification
# ---------------------------------------------------------------------------

def _classify_column(col: BIColumn, series: pd.Series) -> str:
    """Classify a column as numeric, categorical, temporal, or text."""
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    dtype_str = str(series.dtype).lower()
    if "datetime" in dtype_str:
        return "temporal"
    if _looks_temporal(col.name, col.sample_values):
        return "temporal"
    if col.unique_count <= 50:
        return "categorical"
    return "text"


def _looks_temporal(name: str, samples: list[Any]) -> bool:
    """Heuristic: check if column name/values suggest temporal data."""
    name_lower = name.lower()
    if any(kw in name_lower for kw in ("date", "month", "year", "time", "period", "quarter")):
        date_pattern = re.compile(r"^\d{4}[-/]\d{2}([-/]\d{2})?$")
        matches = sum(1 for s in samples if s and date_pattern.match(str(s)))
        return matches >= min(3, len(samples))
    return False


def _safe_float(val: Any) -> float | None:
    """Safely convert a value to float, returning None for NaN/Inf."""
    if val is None:
        return None
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return round(f, 4)
    except (TypeError, ValueError):
        return None


def _to_json_safe(val: Any) -> Any:
    """Convert numpy/pandas types to JSON-serializable Python types."""
    if val is None:
        return None
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (np.floating,)):
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return round(f, 4)
    if isinstance(val, (np.bool_,)):
        return bool(val)
    if isinstance(val, (np.ndarray,)):
        return val.tolist()
    if isinstance(val, pd.Timestamp):
        return str(val)
    return val


# ---------------------------------------------------------------------------
# Chart recommendation
# ---------------------------------------------------------------------------

def recommend_charts(session_id: str) -> dict[str, Any]:
    """Analyze session schema and return recommended chart configurations."""
    session = get_session(session_id)
    engine = get_filter_engine(session_id)
    df = engine.get_filtered_dataframe()
    filtered_count = len(df)

    # Classify columns
    classifications: dict[str, str] = {}
    for col in session.columns:
        if col.name in df.columns:
            classifications[col.name] = _classify_column(col, df[col.name])

    numerics = [c for c, t in classifications.items() if t == "numeric"]
    categoricals = [c for c, t in classifications.items() if t == "categorical"]
    temporals = [c for c, t in classifications.items() if t == "temporal"]

    # KPI cards for all numeric columns
    kpi_cards = []
    for col_name in numerics:
        series = df[col_name].dropna()
        is_pct = any(kw in col_name.lower() for kw in ("percent", "pct", "rate", "ratio"))
        kpi_cards.append({
            "column": col_name,
            "dtype": "numeric",
            "count": int(series.count()),
            "mean": _safe_float(series.mean()),
            "min": _safe_float(series.min()),
            "max": _safe_float(series.max()),
            "sum": _safe_float(series.sum()) if not is_pct else None,
        })

    # Build recommendations
    charts: list[dict[str, Any]] = []

    # R1: categorical x numeric -> bar
    sorted_cats = sorted(
        categoricals,
        key=lambda c: next(
            (col.unique_count for col in session.columns if col.name == c), 999
        ),
    )
    for cat in sorted_cats[:3]:
        for num in numerics[:3]:
            charts.append({
                "chart_id": f"bar_{cat}_{num}",
                "chart_type": "bar",
                "title": f"{num} by {cat}",
                "x_column": cat,
                "y_column": num,
                "aggregation": "mean",
                "reason": "categorical x numeric",
            })

    # R2: temporal x numeric -> line
    for temp in temporals:
        for num in numerics[:2]:
            charts.append({
                "chart_id": f"line_{temp}_{num}",
                "chart_type": "line",
                "title": f"{num} over {temp}",
                "x_column": temp,
                "y_column": num,
                "aggregation": "mean",
                "reason": "temporal x numeric",
            })

    # R3: numeric x numeric -> scatter
    if len(numerics) >= 2:
        for i in range(min(len(numerics) - 1, 2)):
            charts.append({
                "chart_id": f"scatter_{numerics[i]}_{numerics[i + 1]}",
                "chart_type": "scatter",
                "title": f"{numerics[i]} vs {numerics[i + 1]}",
                "x_column": numerics[i],
                "y_column": numerics[i + 1],
                "aggregation": None,
                "reason": "numeric x numeric",
            })

    # R4: numeric -> histogram
    for num in numerics[:3]:
        charts.append({
            "chart_id": f"histogram_{num}",
            "chart_type": "histogram",
            "title": f"Distribution of {num}",
            "x_column": num,
            "y_column": None,
            "aggregation": None,
            "reason": "numeric distribution",
        })

    # R5: 2 categoricals + numeric -> heatmap
    low_card_cats = [
        c for c in categoricals
        if next((col.unique_count for col in session.columns if col.name == c), 999) <= 10
    ]
    if len(low_card_cats) >= 2 and numerics:
        charts.append({
            "chart_id": f"heatmap_{low_card_cats[0]}_{low_card_cats[1]}_{numerics[0]}",
            "chart_type": "heatmap",
            "title": f"{numerics[0]} by {low_card_cats[0]} and {low_card_cats[1]}",
            "x_column": low_card_cats[0],
            "y_column": low_card_cats[1],
            "value_column": numerics[0],
            "aggregation": "mean",
            "reason": "2 categoricals + 1 numeric",
        })

    # Cap at 8 recommendations
    charts = charts[:8]

    return {
        "session_id": session_id,
        "filtered_row_count": filtered_count,
        "kpi_cards": kpi_cards,
        "recommended_charts": charts,
    }


# ---------------------------------------------------------------------------
# Chart data aggregation
# ---------------------------------------------------------------------------

_VALID_AGGS = {"sum", "mean", "median", "count", "min", "max"}


def get_chart_data(
    session_id: str,
    chart_type: str,
    x_column: str,
    y_column: str | None = None,
    aggregation: str | None = None,
    group_by: str | None = None,
    bins: int = 20,
    limit: int = 50,
) -> dict[str, Any]:
    """Compute aggregated data for a specific chart configuration."""
    engine = get_filter_engine(session_id)
    df = engine.get_filtered_dataframe()

    if x_column not in df.columns:
        raise ValueError(f"Column '{x_column}' not found in dataset")
    if y_column and y_column not in df.columns:
        raise ValueError(f"Column '{y_column}' not found in dataset")
    if group_by and group_by not in df.columns:
        raise ValueError(f"Column '{group_by}' not found in dataset")
    if aggregation and aggregation not in _VALID_AGGS:
        raise ValueError(f"Invalid aggregation '{aggregation}'. Must be one of: {_VALID_AGGS}")

    if chart_type == "bar":
        return _compute_bar(df, x_column, y_column, aggregation or "mean", group_by, limit)
    if chart_type == "line":
        return _compute_line(df, x_column, y_column, aggregation or "mean", group_by, limit)
    if chart_type == "scatter":
        return _compute_scatter(df, x_column, y_column)
    if chart_type == "histogram":
        return _compute_histogram(df, x_column, bins)
    if chart_type == "heatmap":
        return _compute_heatmap(df, x_column, y_column, aggregation or "mean")

    raise ValueError(f"Unknown chart_type '{chart_type}'. Must be: bar, line, scatter, histogram, heatmap")


def _compute_bar(
    df: pd.DataFrame,
    x_col: str,
    y_col: str | None,
    agg: str,
    group_by: str | None,
    limit: int,
) -> dict[str, Any]:
    """Compute bar chart data with optional grouping."""
    if not y_col:
        raise ValueError("y_column is required for bar charts")

    if group_by:
        pivot = df.groupby([x_col, group_by])[y_col].agg(agg).reset_index()
        groups = sorted(pivot[group_by].unique().tolist())
        # Pivot to wide format: each group becomes a column
        wide = pivot.pivot_table(index=x_col, columns=group_by, values=y_col, aggfunc="first").reset_index()
        data = []
        for _, row in wide.head(limit).iterrows():
            point: dict[str, Any] = {"x": _to_json_safe(row[x_col])}
            for g in groups:
                point[str(g)] = _to_json_safe(row.get(g))
            data.append(point)
        return {
            "chart_type": "bar",
            "x_column": x_col,
            "y_column": y_col,
            "aggregation": agg,
            "group_by": group_by,
            "groups": [str(g) for g in groups],
            "data": data,
            "data_points": len(data),
        }

    grouped = df.groupby(x_col)[y_col].agg(agg).reset_index()
    grouped.columns = ["x", "y"]
    data = [
        {"x": _to_json_safe(row["x"]), "y": _to_json_safe(row["y"])}
        for _, row in grouped.head(limit).iterrows()
    ]
    return {
        "chart_type": "bar",
        "x_column": x_col,
        "y_column": y_col,
        "aggregation": agg,
        "data": data,
        "data_points": len(data),
    }


def _compute_line(
    df: pd.DataFrame,
    x_col: str,
    y_col: str | None,
    agg: str,
    group_by: str | None,
    limit: int,
) -> dict[str, Any]:
    """Compute line chart data sorted by x-axis, with optional grouping."""
    if not y_col:
        raise ValueError("y_column is required for line charts")

    if group_by:
        pivot = df.groupby([x_col, group_by])[y_col].agg(agg).reset_index()
        groups = sorted(pivot[group_by].unique().tolist())
        wide = pivot.pivot_table(index=x_col, columns=group_by, values=y_col, aggfunc="first")
        wide = wide.sort_index().reset_index()
        data = []
        for _, row in wide.head(limit).iterrows():
            point: dict[str, Any] = {"x": _to_json_safe(row[x_col])}
            for g in groups:
                point[str(g)] = _to_json_safe(row.get(g))
            data.append(point)
        return {
            "chart_type": "line",
            "x_column": x_col,
            "y_column": y_col,
            "aggregation": agg,
            "group_by": group_by,
            "groups": [str(g) for g in groups],
            "data": data,
            "data_points": len(data),
        }

    grouped = df.groupby(x_col)[y_col].agg(agg).reset_index()
    grouped.columns = ["x", "y"]
    grouped = grouped.sort_values("x")
    data = [
        {"x": _to_json_safe(row["x"]), "y": _to_json_safe(row["y"])}
        for _, row in grouped.head(limit).iterrows()
    ]
    return {
        "chart_type": "line",
        "x_column": x_col,
        "y_column": y_col,
        "aggregation": agg,
        "data": data,
        "data_points": len(data),
    }


def _compute_scatter(
    df: pd.DataFrame,
    x_col: str,
    y_col: str | None,
) -> dict[str, Any]:
    """Compute scatter plot data, sampling if too many rows."""
    if not y_col:
        raise ValueError("y_column is required for scatter charts")

    MAX_POINTS = 500
    subset = df[[x_col, y_col]].dropna()
    sampled = len(subset) > MAX_POINTS
    if sampled:
        subset = subset.sample(n=MAX_POINTS, random_state=42)

    data = [
        {"x": _to_json_safe(row[x_col]), "y": _to_json_safe(row[y_col])}
        for _, row in subset.iterrows()
    ]
    result: dict[str, Any] = {
        "chart_type": "scatter",
        "x_column": x_col,
        "y_column": y_col,
        "data": data,
        "data_points": len(data),
    }
    if sampled:
        result["sampled"] = True
        result["sample_size"] = MAX_POINTS
    return result


def _compute_histogram(
    df: pd.DataFrame,
    x_col: str,
    bins: int,
) -> dict[str, Any]:
    """Compute histogram bins using numpy."""
    series = df[x_col].dropna()
    if not pd.api.types.is_numeric_dtype(series):
        raise ValueError(f"Column '{x_col}' is not numeric — cannot create histogram")

    counts, bin_edges = np.histogram(series.values, bins=bins)
    data = [
        {
            "bin_start": _to_json_safe(bin_edges[i]),
            "bin_end": _to_json_safe(bin_edges[i + 1]),
            "count": int(counts[i]),
        }
        for i in range(len(counts))
    ]
    return {
        "chart_type": "histogram",
        "x_column": x_col,
        "bins": bins,
        "data": data,
        "data_points": len(data),
    }


def _compute_heatmap(
    df: pd.DataFrame,
    x_col: str,
    y_col: str | None,
    agg: str,
) -> dict[str, Any]:
    """Compute heatmap data from 2 categoricals + 1 numeric."""
    if not y_col:
        raise ValueError("y_column is required for heatmap charts")

    # Find the first numeric column that isn't x or y
    numeric_cols = [
        c for c in df.columns
        if c not in (x_col, y_col) and pd.api.types.is_numeric_dtype(df[c])
    ]
    if not numeric_cols:
        raise ValueError("No numeric column found for heatmap value")

    value_col = numeric_cols[0]
    pivot = df.groupby([x_col, y_col])[value_col].agg(agg).reset_index()
    data = [
        {
            "x": _to_json_safe(row[x_col]),
            "y": _to_json_safe(row[y_col]),
            "value": _to_json_safe(row[value_col]),
        }
        for _, row in pivot.iterrows()
    ]
    return {
        "chart_type": "heatmap",
        "x_column": x_col,
        "y_column": y_col,
        "value_column": value_col,
        "aggregation": agg,
        "data": data,
        "data_points": len(data),
    }

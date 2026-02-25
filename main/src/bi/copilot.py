"""AI copilot for MES Agentic BI — agentic loop with 5 data tools via OpenRouter."""

from __future__ import annotations

import json
import logging
import math
import os
from typing import Any

import pandas as pd
from openai import OpenAI

from langfuse import observe

from .config import get_bi_config
from .filter_engine import get_filter_engine
from .session_store import get_session

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Per-session chat history (system prompt is NOT stored — it is rebuilt each
# call so that filter state and row counts are always current).
# Format matches the OpenAI messages API: list of role/content dicts.
# ---------------------------------------------------------------------------
_chat_histories: dict[str, list[dict[str, Any]]] = {}


# ---------------------------------------------------------------------------
# OpenAI function-calling tool definitions
# ---------------------------------------------------------------------------

TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "apply_filter",
            "description": (
                "Apply a filter to a column in the dataset. "
                "Only one filter per column is active at a time — applying a new filter "
                "to the same column replaces the previous one. "
                "Returns the number of rows that match all active filters."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "column": {
                        "type": "string",
                        "description": "The exact column name to filter on.",
                    },
                    "operator": {
                        "type": "string",
                        "enum": [
                            "equals",
                            "not_equals",
                            "contains",
                            "greater_than",
                            "less_than",
                            "greater_equal",
                            "less_equal",
                            "between",
                            "in",
                            "is_null",
                            "is_not_null",
                        ],
                        "description": "The filter operator to apply.",
                    },
                    "value": {
                        "description": (
                            "The filter value. "
                            "Use a list [min, max] for 'between'. "
                            "Use a list of values for 'in'. "
                            "Omit (or pass null) for 'is_null' / 'is_not_null'."
                        ),
                    },
                },
                "required": ["column", "operator"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "remove_filter",
            "description": (
                "Remove an active filter from a column. "
                "Pass '__all__' as the column name to clear all active filters."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "column": {
                        "type": "string",
                        "description": "Column name to remove filter from, or '__all__' to clear all.",
                    },
                },
                "required": ["column"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_data",
            "description": (
                "Full-text search across one or more columns in the currently filtered dataset. "
                "Returns up to 50 matching rows. "
                "Use this to find specific records before summarising or answering questions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The text string to search for (case-insensitive).",
                    },
                    "columns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Optional list of column names to search within. "
                            "If omitted, all string/object columns are searched."
                        ),
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "summarize_column",
            "description": (
                "Compute descriptive statistics for a single column in the currently filtered dataset. "
                "For numeric columns returns count/mean/std/min/max/quartiles. "
                "For categorical columns returns top-20 value counts."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "column": {
                        "type": "string",
                        "description": "The exact column name to summarise.",
                    },
                },
                "required": ["column"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "answer_question",
            "description": (
                "Perform structured analytical operations on the currently filtered dataset "
                "and return results for the AI to interpret. "
                "Use this for counts, group-by aggregations, trend detection, outlier detection, "
                "comparisons, and general pandas queries."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "analysis_type": {
                        "type": "string",
                        "enum": ["count", "group_by", "trend", "outliers", "comparison", "general"],
                        "description": "The type of analysis to perform.",
                    },
                    "columns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Columns involved in the analysis. "
                            "For 'group_by' the first column is the grouping key and the second "
                            "(if provided) is the value column. "
                            "For 'comparison' provide exactly two columns. "
                            "For 'count' / 'general' / 'trend' / 'outliers' any relevant columns."
                        ),
                    },
                    "conditions": {
                        "type": "string",
                        "description": (
                            "Optional free-text description of any additional conditions or "
                            "context the analysis should respect."
                        ),
                    },
                },
                "required": ["analysis_type", "columns"],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# JSON-safe type conversion helper
# ---------------------------------------------------------------------------

def _to_json_safe(obj: Any) -> Any:
    """Recursively convert numpy/pandas types to Python-native JSON-serialisable types."""
    import numpy as np  # local import to avoid hard dependency at module level

    if isinstance(obj, dict):
        return {k: _to_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_json_safe(item) for item in obj]
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        val = float(obj)
        if math.isnan(val) or math.isinf(val):
            return None
        return val
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return _to_json_safe(obj.tolist())
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    if obj is pd.NaT:
        return None
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    return obj


# ---------------------------------------------------------------------------
# System prompt builder
# ---------------------------------------------------------------------------

def _build_system_prompt(session_id: str) -> str:
    """Build a system prompt with current dataset metadata and filter state."""
    session = get_session(session_id)
    engine = get_filter_engine(session_id)
    active_filters = engine.get_active_filters()
    filtered_count = engine.filtered_count()

    column_lines: list[str] = []
    for col in session.columns:
        samples = ", ".join(str(s) for s in col.sample_values[:5]) if col.sample_values else "—"
        column_lines.append(
            f"  - {col.name!r} (dtype={col.dtype}, "
            f"unique={col.unique_count}, nulls={col.null_count}, "
            f"samples=[{samples}])"
        )

    columns_block = "\n".join(column_lines)

    filter_block: str
    if active_filters:
        filter_lines = [
            f"  - {f['column']!r} {f['operator']} {f.get('value')!r}"
            for f in active_filters
        ]
        filter_block = "Active filters:\n" + "\n".join(filter_lines)
    else:
        filter_block = "Active filters: none"

    return (
        "You are an expert data analyst AI copilot for a pharmaceutical MES "
        "(Manufacturing Execution System) Agentic BI platform.\n\n"
        f"Dataset: {session.filename!r}\n"
        f"Total rows: {session.total_rows} | Filtered rows: {filtered_count} | "
        f"Columns: {session.total_columns}\n\n"
        f"Column schema:\n{columns_block}\n\n"
        f"{filter_block}\n\n"
        "Guidelines:\n"
        "1. ALWAYS use the provided tools to perform data operations — never guess or invent "
        "   data values from memory.\n"
        "2. Use apply_filter / remove_filter to modify the visible dataset before analysis.\n"
        "3. Use search_data to locate specific records.\n"
        "4. Use summarize_column for statistical summaries of individual columns.\n"
        "5. Use answer_question for aggregations, group-bys, trend analysis, and comparisons.\n"
        "6. After calling a tool, interpret the returned data clearly and concisely.\n"
        "7. If a tool returns an error, explain what went wrong and suggest corrections.\n"
        "8. Maintain pharmaceutical data integrity: be precise, cite row counts, "
        "   and never speculate beyond what the data shows.\n"
    )


# ---------------------------------------------------------------------------
# Tool executor functions
# ---------------------------------------------------------------------------

def _tool_apply_filter(session_id: str, column: str, operator: str, value: Any) -> dict[str, Any]:
    """Execute the apply_filter tool."""
    engine = get_filter_engine(session_id)
    filtered_rows = engine.apply_filter(column, operator, value)
    active_filters = engine.get_active_filters()
    logger.info(
        "apply_filter: session=%s column=%r operator=%s value=%r -> %d rows",
        session_id, column, operator, value, filtered_rows,
    )
    return {
        "status": "ok",
        "filtered_rows": filtered_rows,
        "active_filters": active_filters,
    }


def _tool_remove_filter(session_id: str, column: str) -> dict[str, Any]:
    """Execute the remove_filter tool."""
    engine = get_filter_engine(session_id)
    filtered_rows = engine.remove_filter(column)
    active_filters = engine.get_active_filters()
    logger.info(
        "remove_filter: session=%s column=%r -> %d rows",
        session_id, column, filtered_rows,
    )
    return {
        "status": "ok",
        "filtered_rows": filtered_rows,
        "active_filters": active_filters,
    }


def _tool_search_data(
    session_id: str,
    query: str,
    columns: list[str] | None = None,
) -> dict[str, Any]:
    """Execute the search_data tool against the currently filtered DataFrame."""
    engine = get_filter_engine(session_id)
    dataframe = engine.get_filtered_dataframe()

    if columns:
        # Validate requested columns exist
        missing = [c for c in columns if c not in dataframe.columns]
        if missing:
            raise ValueError(f"Unknown columns for search: {missing}")
        search_cols = columns
    else:
        # Default: search all string/object columns
        search_cols = [
            col for col in dataframe.columns
            if dataframe[col].dtype == object or pd.api.types.is_string_dtype(dataframe[col])
        ]

    if not search_cols:
        return {"status": "ok", "matches": [], "match_count": 0, "searched_columns": []}

    mask = pd.Series([False] * len(dataframe), index=dataframe.index)
    for col in search_cols:
        mask = mask | dataframe[col].astype(str).str.contains(query, case=False, na=False, regex=False)

    matches_df = dataframe[mask].head(50)
    rows = _to_json_safe(matches_df.replace({pd.NA: None}).to_dict(orient="records"))

    logger.info(
        "search_data: session=%s query=%r cols=%s -> %d matches",
        session_id, query, search_cols, len(rows),
    )
    return {
        "status": "ok",
        "matches": rows,
        "match_count": int(mask.sum()),
        "searched_columns": search_cols,
        "truncated_to": 50 if int(mask.sum()) > 50 else None,
    }


def _tool_summarize_column(session_id: str, column: str) -> dict[str, Any]:
    """Execute the summarize_column tool on the currently filtered DataFrame."""
    engine = get_filter_engine(session_id)
    dataframe = engine.get_filtered_dataframe()

    if column not in dataframe.columns:
        raise ValueError(f"Unknown column '{column}'")

    series = dataframe[column]
    result: dict[str, Any] = {
        "status": "ok",
        "column": column,
        "dtype": str(series.dtype),
        "total_values": int(len(series)),
        "null_count": int(series.isna().sum()),
        "unique_count": int(series.nunique()),
    }

    if pd.api.types.is_numeric_dtype(series):
        desc = series.describe()
        result["summary_type"] = "numeric"
        result["statistics"] = _to_json_safe(desc.to_dict())
    else:
        vc = series.value_counts().head(20)
        result["summary_type"] = "categorical"
        result["top_values"] = _to_json_safe(vc.to_dict())

    logger.info("summarize_column: session=%s column=%r dtype=%s", session_id, column, series.dtype)
    return result


def _tool_answer_question(
    session_id: str,
    analysis_type: str,
    columns: list[str],
    conditions: str | None = None,
) -> dict[str, Any]:
    """Execute the answer_question tool on the currently filtered DataFrame."""
    engine = get_filter_engine(session_id)
    dataframe = engine.get_filtered_dataframe()

    missing = [c for c in columns if c not in dataframe.columns]
    if missing:
        raise ValueError(f"Unknown columns: {missing}")

    result: dict[str, Any] = {
        "status": "ok",
        "analysis_type": analysis_type,
        "columns": columns,
        "filtered_row_count": int(len(dataframe)),
    }
    if conditions:
        result["conditions_note"] = conditions

    if analysis_type == "count":
        if columns:
            counts = {col: int(dataframe[col].count()) for col in columns}
            result["counts"] = counts
        else:
            result["total_rows"] = int(len(dataframe))

    elif analysis_type == "group_by":
        if not columns:
            raise ValueError("group_by requires at least one column")
        group_col = columns[0]
        if len(columns) >= 2:
            value_col = columns[1]
            grouped = dataframe.groupby(group_col)[value_col].agg(["count", "sum", "mean"])
            result["group_by"] = _to_json_safe(grouped.reset_index().to_dict(orient="records"))
        else:
            grouped = dataframe[group_col].value_counts().head(50)
            result["group_by"] = _to_json_safe(grouped.to_dict())

    elif analysis_type == "trend":
        if len(columns) < 2:
            raise ValueError("trend requires at least two columns (x-axis and y-axis)")
        x_col, y_col = columns[0], columns[1]
        trend_data = dataframe[[x_col, y_col]].dropna().sort_values(x_col)
        result["trend_data"] = _to_json_safe(trend_data.head(200).to_dict(orient="records"))
        result["data_points"] = int(len(trend_data))

    elif analysis_type == "outliers":
        numeric_cols = [c for c in columns if pd.api.types.is_numeric_dtype(dataframe[c])]
        if not numeric_cols:
            raise ValueError(f"No numeric columns among: {columns}")
        outlier_results: dict[str, Any] = {}
        for col in numeric_cols:
            series = dataframe[col].dropna()
            q1 = float(series.quantile(0.25))
            q3 = float(series.quantile(0.75))
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            outlier_mask = (dataframe[col] < lower) | (dataframe[col] > upper)
            outlier_rows = dataframe[outlier_mask][columns].head(50)
            outlier_results[col] = {
                "lower_fence": lower,
                "upper_fence": upper,
                "outlier_count": int(outlier_mask.sum()),
                "sample_outliers": _to_json_safe(outlier_rows.to_dict(orient="records")),
            }
        result["outliers"] = outlier_results

    elif analysis_type == "comparison":
        if len(columns) < 2:
            raise ValueError("comparison requires exactly two columns")
        col_a, col_b = columns[0], columns[1]
        result["comparison"] = {
            col_a: _to_json_safe(dataframe[col_a].describe().to_dict()),
            col_b: _to_json_safe(dataframe[col_b].describe().to_dict()),
            "correlation": (
                _to_json_safe(float(dataframe[[col_a, col_b]].corr().iloc[0, 1]))
                if (pd.api.types.is_numeric_dtype(dataframe[col_a])
                    and pd.api.types.is_numeric_dtype(dataframe[col_b]))
                else None
            ),
        }

    elif analysis_type == "general":
        summaries: dict[str, Any] = {}
        for col in columns:
            series = dataframe[col]
            if pd.api.types.is_numeric_dtype(series):
                summaries[col] = _to_json_safe(series.describe().to_dict())
            else:
                summaries[col] = {
                    "unique_count": int(series.nunique()),
                    "null_count": int(series.isna().sum()),
                    "top_5": _to_json_safe(series.value_counts().head(5).to_dict()),
                }
        result["general_summary"] = summaries

    else:
        raise ValueError(f"Unknown analysis_type: '{analysis_type}'")

    logger.info(
        "answer_question: session=%s type=%s cols=%s",
        session_id, analysis_type, columns,
    )
    return result


# ---------------------------------------------------------------------------
# Tool dispatch
# ---------------------------------------------------------------------------

def _dispatch_tool(session_id: str, tool_name: str, tool_args: dict[str, Any]) -> dict[str, Any]:
    """Dispatch a tool call by name and return its result dict.

    Any exception raised by the tool executor is caught here and returned as
    an error dict so the LLM can observe and react to it rather than the
    request failing completely.
    """
    try:
        if tool_name == "apply_filter":
            return _tool_apply_filter(
                session_id,
                column=tool_args["column"],
                operator=tool_args["operator"],
                value=tool_args.get("value"),
            )
        if tool_name == "remove_filter":
            return _tool_remove_filter(
                session_id,
                column=tool_args["column"],
            )
        if tool_name == "search_data":
            return _tool_search_data(
                session_id,
                query=tool_args["query"],
                columns=tool_args.get("columns"),
            )
        if tool_name == "summarize_column":
            return _tool_summarize_column(
                session_id,
                column=tool_args["column"],
            )
        if tool_name == "answer_question":
            return _tool_answer_question(
                session_id,
                analysis_type=tool_args["analysis_type"],
                columns=tool_args["columns"],
                conditions=tool_args.get("conditions"),
            )
        raise ValueError(f"Unknown tool '{tool_name}'")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Tool '%s' raised %s: %s", tool_name, type(exc).__name__, exc)
        return {"status": "error", "error": f"{type(exc).__name__}: {exc}"}


# ---------------------------------------------------------------------------
# Main agentic chat function
# ---------------------------------------------------------------------------

@observe(name="bi-copilot-chat")
def chat(session_id: str, user_message: str) -> dict[str, Any]:
    """Run one turn of the copilot agentic loop for the given session.

    Returns a dict with keys:
      response          — final text response from the LLM
      tool_calls        — list of tool invocations made during this turn
      filters_changed   — True if apply_filter / remove_filter was called
      active_filters    — current active filter list after the turn
      filtered_row_count — filtered row count after the turn
    """
    if not user_message.strip():
        raise ValueError("user_message must not be empty")

    config = get_bi_config()
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. "
            "Set the environment variable before using the BI copilot."
        )

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=openrouter_api_key,
    )

    # Retrieve or initialise the per-session history (no system prompt stored).
    history = _chat_histories.setdefault(session_id, [])

    # Append the new user message.
    history.append({"role": "user", "content": user_message})

    # Rebuild system prompt with current filter / data state.
    system_prompt = _build_system_prompt(session_id)

    # Compose the full messages list: system first, then the stored history.
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        *history,
    ]

    tool_calls_made: list[dict[str, Any]] = []
    filters_changed = False
    final_text = ""

    # Agentic loop — maximum 5 iterations to prevent run-away tool calling.
    for iteration in range(5):
        logger.debug(
            "copilot loop iteration=%d session=%s messages=%d",
            iteration, session_id, len(messages),
        )

        response = client.chat.completions.create(
            model=config.copilot_model,
            messages=messages,  # type: ignore[arg-type]
            tools=TOOLS,  # type: ignore[arg-type]
        )

        choice = response.choices[0]
        finish_reason = choice.finish_reason
        assistant_message = choice.message

        # Append raw assistant turn to the running message list.
        assistant_dict: dict[str, Any] = {
            "role": "assistant",
            "content": assistant_message.content or "",
        }
        if assistant_message.tool_calls:
            assistant_dict["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in assistant_message.tool_calls
            ]
        messages.append(assistant_dict)

        if finish_reason == "stop" or not assistant_message.tool_calls:
            final_text = assistant_message.content or ""
            break

        # Process each tool call.
        for tool_call in assistant_message.tool_calls:
            fn_name = tool_call.function.name
            try:
                fn_args: dict[str, Any] = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError as exc:
                fn_args = {}
                logger.error("Failed to parse tool arguments for '%s': %s", fn_name, exc)

            tool_result = _dispatch_tool(session_id, fn_name, fn_args)

            if fn_name in {"apply_filter", "remove_filter"}:
                filters_changed = True

            tool_calls_made.append({
                "tool": fn_name,
                "input": fn_args,
                "result": tool_result,
                "status": tool_result.get("status", "error"),
            })

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(_to_json_safe(tool_result)),
            })

        logger.debug(
            "copilot tools executed iteration=%d count=%d",
            iteration, len(tool_calls_made),
        )

    else:
        # Loop exhausted without a stop signal — use whatever the last assistant text was.
        final_text = assistant_message.content or ""  # type: ignore[possibly-undefined]
        logger.warning(
            "copilot agentic loop reached max iterations for session=%s", session_id
        )

    # Persist only the turns AFTER the original user message back into history
    # (history already has the user turn; append all new assistant + tool turns).
    # The messages list is: [system, ...old_history, user, ...new_turns].
    # We need to persist starting from the assistant turn onward (skip system + old history + user).
    new_turn_start = 1 + len(history)  # 1 for system, then len includes the user we just appended
    for msg in messages[new_turn_start:]:
        history.append(msg)

    engine = get_filter_engine(session_id)
    return {
        "response": final_text,
        "tool_calls": tool_calls_made,
        "filters_changed": filters_changed,
        "active_filters": engine.get_active_filters(),
        "filtered_row_count": engine.filtered_count(),
    }

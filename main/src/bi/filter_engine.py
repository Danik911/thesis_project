"""Server-side filtering engine for BI sessions."""

from __future__ import annotations

from typing import Any

import pandas as pd

from .session_store import get_dataframe


SUPPORTED_OPERATORS = {
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
}


class FilterEngine:
    """In-memory filter state and pandas filter execution for one BI session."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self._filters: list[dict[str, Any]] = []

    def apply_filter(self, column: str, operator: str, value: Any) -> int:
        if operator not in SUPPORTED_OPERATORS:
            raise ValueError(
                f"Unsupported operator '{operator}'. Supported operators: {sorted(SUPPORTED_OPERATORS)}"
            )

        dataframe = get_dataframe(self.session_id)
        if column not in dataframe.columns:
            raise ValueError(f"Unknown column '{column}' for session '{self.session_id}'")

        self._filters = [item for item in self._filters if item["column"] != column]
        self._filters.append({"column": column, "operator": operator, "value": value})
        return self.filtered_count()

    def remove_filter(self, column: str) -> int:
        if column == "__all__":
            self.clear_filters()
            return self.filtered_count()

        self._filters = [item for item in self._filters if item["column"] != column]
        return self.filtered_count()

    def clear_filters(self) -> None:
        self._filters = []

    def set_filters(self, filters: list[dict[str, Any]]) -> int:
        self.clear_filters()
        for item in filters:
            self.apply_filter(item["column"], item["operator"], item.get("value"))
        return self.filtered_count()

    def get_active_filters(self) -> list[dict[str, Any]]:
        return [dict(item) for item in self._filters]

    def filtered_count(self) -> int:
        dataframe = get_dataframe(self.session_id)
        filtered = self._apply_all_filters(dataframe)
        return int(len(filtered))

    def get_page(self, page: int, page_size: int) -> dict[str, Any]:
        if page < 1:
            raise ValueError("page must be >= 1")
        if page_size < 1:
            raise ValueError("page_size must be >= 1")

        dataframe = get_dataframe(self.session_id)
        total_rows = int(len(dataframe))
        filtered = self._apply_all_filters(dataframe)
        total_filtered_rows = int(len(filtered))

        start = (page - 1) * page_size
        end = start + page_size
        rows = filtered.iloc[start:end].replace({pd.NA: None}).to_dict(orient="records")
        total_pages = max((total_filtered_rows + page_size - 1) // page_size, 1)

        return {
            "rows": rows,
            "total_rows": total_rows,
            "total_filtered_rows": total_filtered_rows,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "active_filters": self.get_active_filters(),
        }

    def _apply_all_filters(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        filtered = dataframe
        for item in self._filters:
            filtered = self._apply_single_filter(filtered, item["column"], item["operator"], item.get("value"))
        return filtered

    def _apply_single_filter(
        self,
        dataframe: pd.DataFrame,
        column: str,
        operator: str,
        value: Any,
    ) -> pd.DataFrame:
        series = dataframe[column]

        if operator == "equals":
            return dataframe[series == value]
        if operator == "not_equals":
            return dataframe[series != value]
        if operator == "contains":
            if value is None:
                raise ValueError(f"Operator 'contains' requires a non-null value for column '{column}'")
            return dataframe[
                series.astype(str).str.contains(str(value), case=False, na=False, regex=False)
            ]
        if operator == "in":
            if not isinstance(value, list):
                raise ValueError(f"Operator 'in' requires a list value for column '{column}'")
            return dataframe[series.isin(value)]
        if operator == "is_null":
            return dataframe[series.isna()]
        if operator == "is_not_null":
            return dataframe[series.notna()]

        if operator in {"greater_than", "less_than", "greater_equal", "less_equal", "between"}:
            numeric = pd.to_numeric(series, errors="coerce")

            if operator == "between":
                if not isinstance(value, list) or len(value) != 2:
                    raise ValueError(
                        f"Operator 'between' requires [min, max] list value for column '{column}'"
                    )
                min_val = pd.to_numeric(pd.Series([value[0]]), errors="coerce").iloc[0]
                max_val = pd.to_numeric(pd.Series([value[1]]), errors="coerce").iloc[0]
                if pd.isna(min_val) or pd.isna(max_val):
                    raise ValueError(
                        f"Operator 'between' requires numeric min/max values for column '{column}'"
                    )
                return dataframe[numeric.between(min_val, max_val)]

            parsed_value = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
            if pd.isna(parsed_value):
                raise ValueError(f"Operator '{operator}' requires numeric value for column '{column}'")

            if operator == "greater_than":
                return dataframe[numeric > parsed_value]
            if operator == "less_than":
                return dataframe[numeric < parsed_value]
            if operator == "greater_equal":
                return dataframe[numeric >= parsed_value]
            if operator == "less_equal":
                return dataframe[numeric <= parsed_value]

        raise ValueError(f"Unsupported operator '{operator}'")


_engines: dict[str, FilterEngine] = {}


def get_filter_engine(session_id: str) -> FilterEngine:
    engine = _engines.get(session_id)
    if engine is None:
        engine = FilterEngine(session_id=session_id)
        _engines[session_id] = engine
    return engine

"""Clean HTML tables from PP-Structure output.

Removes empty rows/cells, extracts plain-text representations,
and preserves table context (page number, section association).

Uses only stdlib html.parser — no lxml or beautifulsoup.

NO FALLBACK LOGIC.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Any


@dataclass
class TableCell:
    """A single cell in a cleaned table."""

    text: str
    colspan: int = 1
    rowspan: int = 1
    is_header: bool = False


@dataclass
class CleanedTable:
    """A cleaned table with both structured and plain-text representations."""

    page: int
    table_index: int
    rows: list[list[TableCell]]
    html_cleaned: str
    plain_text: str
    original_html: str
    empty_rows_removed: int = 0
    empty_cells_removed: int = 0


class _HTMLTableParser(HTMLParser):
    """Minimal HTML table parser using stdlib."""

    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[TableCell]] = []
        self._current_row: list[TableCell] | None = None
        self._current_cell_text: list[str] = []
        self._in_cell = False
        self._is_header = False
        self._colspan = 1
        self._rowspan = 1
        self._in_thead = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "thead":
            self._in_thead = True
        elif tag == "tr":
            self._current_row = []
        elif tag in ("td", "th"):
            self._in_cell = True
            self._is_header = tag == "th" or self._in_thead
            self._current_cell_text = []
            self._colspan = 1
            self._rowspan = 1
            for name, value in attrs:
                if name == "colspan" and value:
                    try:
                        self._colspan = int(value)
                    except ValueError:
                        pass
                elif name == "rowspan" and value:
                    try:
                        self._rowspan = int(value)
                    except ValueError:
                        pass

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "thead":
            self._in_thead = False
        elif tag == "tr" and self._current_row is not None:
            self.rows.append(self._current_row)
            self._current_row = None
        elif tag in ("td", "th") and self._in_cell:
            cell_text = " ".join(self._current_cell_text).strip()
            cell = TableCell(
                text=cell_text,
                colspan=self._colspan,
                rowspan=self._rowspan,
                is_header=self._is_header,
            )
            if self._current_row is not None:
                self._current_row.append(cell)
            self._in_cell = False

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            text = data.strip()
            if text:
                self._current_cell_text.append(text)


def parse_html_table(html: str) -> list[list[TableCell]]:
    """Parse HTML table into structured rows."""
    parser = _HTMLTableParser()
    parser.feed(html)
    return parser.rows


def _is_empty_row(row: list[TableCell]) -> bool:
    """Check if all cells in a row are empty."""
    return all(not cell.text.strip() for cell in row)


def _is_empty_cell(cell: TableCell) -> bool:
    """Check if a cell is empty."""
    return not cell.text.strip()


def remove_empty_rows(rows: list[list[TableCell]]) -> tuple[list[list[TableCell]], int]:
    """Remove rows where all cells are empty.

    Returns:
        Tuple of (cleaned_rows, count_removed).
    """
    cleaned = [row for row in rows if not _is_empty_row(row)]
    return cleaned, len(rows) - len(cleaned)


def rows_to_plain_text(rows: list[list[TableCell]]) -> str:
    """Convert table rows to a plain-text representation.

    Uses pipe-delimited format for readability.
    """
    if not rows:
        return ""

    lines: list[str] = []
    for row in rows:
        cells_text = [cell.text if cell.text else "" for cell in row]
        line = " | ".join(cells_text)
        lines.append(line)

    return "\n".join(lines)


def rows_to_clean_html(rows: list[list[TableCell]]) -> str:
    """Rebuild clean HTML from structured rows."""
    if not rows:
        return ""

    parts = ["<table>"]
    for row in rows:
        parts.append("  <tr>")
        for cell in row:
            tag = "th" if cell.is_header else "td"
            attrs = ""
            if cell.colspan > 1:
                attrs += f' colspan="{cell.colspan}"'
            if cell.rowspan > 1:
                attrs += f' rowspan="{cell.rowspan}"'
            text = cell.text if cell.text else ""
            # Escape HTML entities in text
            text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            parts.append(f"    <{tag}{attrs}>{text}</{tag}>")
        parts.append("  </tr>")
    parts.append("</table>")
    return "\n".join(parts)


def clean_table(
    table_data: dict[str, Any],
    page: int,
    table_index: int,
) -> CleanedTable | None:
    """Clean a single table from PP-Structure output.

    Args:
        table_data: Dict with 'html' key from PP-Structure.
        page: Page number the table appears on.
        table_index: Index of table on this page.

    Returns:
        CleanedTable or None if table has no usable content.
    """
    html = table_data.get("html", "")
    if not html or not isinstance(html, str):
        return None

    rows = parse_html_table(html)
    if not rows:
        return None

    cleaned_rows, empty_removed = remove_empty_rows(rows)
    if not cleaned_rows:
        return None

    # Count empty cells in remaining rows
    empty_cells = sum(
        1 for row in cleaned_rows for cell in row if _is_empty_cell(cell)
    )

    return CleanedTable(
        page=page,
        table_index=table_index,
        rows=cleaned_rows,
        html_cleaned=rows_to_clean_html(cleaned_rows),
        plain_text=rows_to_plain_text(cleaned_rows),
        original_html=html,
        empty_rows_removed=empty_removed,
        empty_cells_removed=empty_cells,
    )


def clean_page_tables(page_data: dict[str, Any]) -> list[CleanedTable]:
    """Clean all tables from a single page.

    Args:
        page_data: Parsed page JSON with 'tables' list.

    Returns:
        List of cleaned tables.
    """
    page_num = page_data.get("page")
    if page_num is None:
        raise ValueError(f"Page data missing 'page' field: {list(page_data.keys())}")

    tables = page_data.get("tables", [])
    if not isinstance(tables, list):
        return []

    cleaned: list[CleanedTable] = []
    for idx, table_data in enumerate(tables, start=1):
        if not isinstance(table_data, dict):
            continue
        result = clean_table(table_data, page_num, idx)
        if result is not None:
            cleaned.append(result)
    return cleaned


def clean_document_tables(pages: list[dict[str, Any]]) -> list[CleanedTable]:
    """Clean all tables across all pages of a document."""
    all_tables: list[CleanedTable] = []
    for page_data in pages:
        all_tables.extend(clean_page_tables(page_data))
    return all_tables


def tables_to_json(tables: list[CleanedTable]) -> list[dict[str, Any]]:
    """Serialize cleaned tables to JSON-compatible dicts."""
    return [
        {
            "page": t.page,
            "table_index": t.table_index,
            "html_cleaned": t.html_cleaned,
            "plain_text": t.plain_text,
            "row_count": len(t.rows),
            "empty_rows_removed": t.empty_rows_removed,
        }
        for t in tables
    ]

"""PDF export for BI filtered datasets."""

from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO

from fpdf import FPDF

from .filter_engine import get_filter_engine
from .session_store import get_session


PDF_MAX_ROWS = 1000


def _format_filter(filter_item: dict) -> str:
    column = str(filter_item.get("column", ""))
    operator = str(filter_item.get("operator", ""))
    value = filter_item.get("value")
    return f"{column} {operator} {value}"


def _safe_cell_text(value: object, max_len: int = 28) -> str:
    if value is None:
        return ""

    text = str(value).replace("\n", " ").replace("\r", " ").strip()
    if len(text) <= max_len:
        return text
    return f"{text[: max_len - 1]}…"


def export_pdf(session_id: str) -> BytesIO:
    """Export filtered BI data to a landscape A4 PDF."""
    session = get_session(session_id)
    engine = get_filter_engine(session_id)

    filtered_df = engine.get_filtered_dataframe()
    filtered_count = int(len(filtered_df))
    was_truncated = filtered_count > PDF_MAX_ROWS
    export_df = filtered_df.head(PDF_MAX_ROWS)

    pdf = FPDF(orientation="L", format="A4")
    pdf.set_auto_page_break(auto=True, margin=8)
    pdf.set_margins(left=8, top=8, right=8)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 7, f"MES Agentic BI - {session.filename}", ln=True)

    pdf.set_font("Helvetica", size=8)
    pdf.cell(
        0,
        5,
        (
            f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')} | "
            f"Showing {len(export_df)} of {filtered_count} filtered rows (from {session.total_rows} total)"
        ),
        ln=True,
    )

    active_filters = engine.get_active_filters()
    if active_filters:
        filter_summary = "; ".join(_format_filter(item) for item in active_filters)
        pdf.multi_cell(0, 5, f"Filters: {_safe_cell_text(filter_summary, max_len=220)}")
    else:
        pdf.cell(0, 5, "Filters: none", ln=True)

    if was_truncated:
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(
            0,
            5,
            f"Warning: PDF export is capped at {PDF_MAX_ROWS} rows. Use Excel export for full dataset.",
            ln=True,
        )
        pdf.set_font("Helvetica", size=8)

    pdf.ln(2)

    if export_df.empty:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 8, "No rows match the current filters.", ln=True)
        buffer = BytesIO()
        pdf.output(buffer)
        buffer.seek(0)
        return buffer

    columns = [str(column) for column in export_df.columns]
    col_count = max(len(columns), 1)
    available_width = pdf.w - pdf.l_margin - pdf.r_margin
    min_width = 18.0

    width_weights = [max(8, min(28, len(column))) for column in columns]
    total_weight = float(sum(width_weights))
    raw_widths = [(available_width * weight / total_weight) for weight in width_weights]
    col_widths = [max(min_width, width) for width in raw_widths]

    current_total = sum(col_widths)
    if current_total > 0:
        scale = available_width / current_total
        col_widths = [width * scale for width in col_widths]

    pdf.set_font("Helvetica", "B", 7)
    for idx, column in enumerate(columns):
        pdf.cell(col_widths[idx], 6, _safe_cell_text(column, max_len=24), border=1)
    pdf.ln()

    pdf.set_font("Helvetica", size=6)
    row_height = 5
    for _, row in export_df.iterrows():
        for idx, value in enumerate(row):
            pdf.cell(col_widths[idx], row_height, _safe_cell_text(value), border=1)
        pdf.ln()

    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

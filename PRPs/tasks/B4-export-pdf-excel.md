# Task B4 — Export: PDF + Excel

**Phase:** 4 (Export) | **Day:** 4
**Dependencies:** B2 (Filters — needs filtered data)
**Branch:** `feature/mes-agentic-bi`
**Status:** NOT STARTED
**Estimated effort:** 1 day

---

## Objective

Implement PDF and Excel export of filtered data. PDF uses fpdf2 (landscape, max 1000 rows, filter summary header). Excel uses openpyxl (full filtered dataset with "Filters Applied" metadata sheet). Frontend export buttons in the top bar matching the screenshot layout.

---

## Files to Create

| File | Purpose |
|------|---------|
| `main/src/bi/pdf_exporter.py` | `export_pdf(session_id) -> BytesIO`. Landscape A4, table headers in bold, auto-sized columns, max 1000 rows with warning. Filter summary in header. Uses fpdf2. |
| `main/src/bi/excel_exporter.py` | `export_excel(session_id) -> BytesIO`. Sheet 1: filtered data with formatted headers. Sheet 2: "Filters Applied" metadata (filter column, operator, value, timestamp). Uses openpyxl. |
| `main/frontend/components/bi/ExportButtons.tsx` | Top-right button group: "Columns (N/M)" toggle, "Excel" button, "PDF" button. Shows filtered row count. Triggers browser download via `window.open()`. |

## Files to Modify

| File | Change |
|------|--------|
| `main/api/bi_router.py` | Add `GET /bi/export/excel/{session_id}` and `GET /bi/export/pdf/{session_id}`. Return `StreamingResponse` with correct Content-Disposition header. |
| `main/frontend/pages/agentic-bi.tsx` | Add ExportButtons to top bar area. |

---

## Implementation Details

### 1. pdf_exporter.py

```python
from fpdf import FPDF
from io import BytesIO

def export_pdf(session_id: str) -> BytesIO:
    session = get_session(session_id)
    df = get_filtered_dataframe(session_id)

    if len(df) > 1000:
        df = df.head(1000)  # Cap at 1000 rows

    pdf = FPDF(orientation='L', format='A4')
    pdf.add_page()
    pdf.set_font("Helvetica", size=8)

    # Filter summary header
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, f"MES Agentic BI - {session.filename}", ln=True)
    pdf.set_font("Helvetica", size=8)
    pdf.cell(0, 6, f"Showing {len(df)} of {session.total_rows} rows", ln=True)
    if session.active_filters:
        pdf.cell(0, 6, f"Filters: {', '.join(f['column'] + ' ' + f['operator'] + ' ' + str(f['value']) for f in session.active_filters)}", ln=True)
    pdf.ln(4)

    # Table headers
    col_widths = [max(30, min(60, len(str(col)) * 3)) for col in df.columns]
    pdf.set_font("Helvetica", "B", 7)
    for i, col in enumerate(df.columns):
        pdf.cell(col_widths[i], 6, str(col)[:20], border=1)
    pdf.ln()

    # Table rows
    pdf.set_font("Helvetica", size=6)
    for _, row in df.iterrows():
        for i, val in enumerate(row):
            pdf.cell(col_widths[i], 5, str(val)[:25], border=1)
        pdf.ln()

    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer
```

### 2. excel_exporter.py

```python
import openpyxl
from io import BytesIO

def export_excel(session_id: str) -> BytesIO:
    session = get_session(session_id)
    df = get_filtered_dataframe(session_id)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Data"

    # Headers
    for col_idx, col_name in enumerate(df.columns, 1):
        cell = ws.cell(row=1, column=col_idx, value=col_name)
        cell.font = openpyxl.styles.Font(bold=True)

    # Data rows
    for row_idx, row in enumerate(df.itertuples(index=False), 2):
        for col_idx, value in enumerate(row, 1):
            ws.cell(row=row_idx, column=col_idx, value=value)

    # Filters metadata sheet
    if session.active_filters:
        ws_filters = wb.create_sheet("Filters Applied")
        ws_filters.append(["Column", "Operator", "Value"])
        for f in session.active_filters:
            ws_filters.append([f["column"], f["operator"], str(f["value"])])

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer
```

---

## Testing Strategy

```bash
# 1. Test Excel export
curl -o test_export.xlsx http://localhost:8080/bi/export/excel/{session_id}
# Open in Excel -> verify filtered rows + Filters Applied sheet

# 2. Test PDF export
curl -o test_export.pdf http://localhost:8080/bi/export/pdf/{session_id}
# Open in PDF viewer -> verify table format, filter summary, max 1000 rows

# 3. Frontend: click Excel button -> browser download
# 4. Frontend: click PDF button -> browser download
```

---

## Gate Criteria (Pass/Fail)

- [ ] Excel export contains only filtered rows (not full dataset)
- [ ] Excel export has "Filters Applied" metadata sheet when filters active
- [ ] PDF export is landscape A4 with readable table
- [ ] PDF export caps at 1000 rows with warning in header
- [ ] PDF header shows filename and filter summary
- [ ] Export buttons show in top-right bar matching screenshot layout
- [ ] Export buttons show filtered row count (e.g., "Exporting 847 rows")
- [ ] `window.open()` triggers browser native download

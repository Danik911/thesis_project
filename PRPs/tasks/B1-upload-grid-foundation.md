# Task B1 — Upload + Grid Foundation

**Phase:** 1 (Foundation) | **Day:** 1
**Dependencies:** Pre-requisites complete (deps installed, env vars set)
**Branch:** `feature/mes-agentic-bi`
**Status:** NOT STARTED
**Estimated effort:** 1 day

---

## Objective

Build the core data upload and grid display pipeline. User uploads an XLSX/CSV file, backend parses it with pandas into a session-stored DataFrame, and the frontend displays it in a TanStack Table grid with a sidebar showing data source info and field names.

---

## Files to Create

| File | Purpose |
|------|---------|
| `main/src/bi/__init__.py` | Package init |
| `main/src/bi/config.py` | `BI_*` env var loading (follow `main/src/lims/config.py`) |
| `main/src/bi/session_store.py` | In-memory DataFrame sessions: `create_session()`, `get_session()`, `get_dataframe()`. Max 20 sessions, 1hr TTL, LRU eviction. Follow `main/src/lims/job_store.py`. |
| `main/src/bi/data_parser.py` | `parse_file(content, filename) -> pd.DataFrame`. Support `.xlsx` (pd.read_excel), `.csv` (pd.read_csv). Auto-detect column types. Return column metadata (name, dtype, unique_count, null_count, sample_values). |
| `main/api/bi_router.py` | FastAPI router with `APIRouter(tags=["BI"])`. Endpoints: `POST /bi/upload`, `GET /bi/data/{session_id}`, `GET /bi/schema/{session_id}`. Follow `main/api/lims_router.py`. |
| `main/frontend/pages/agentic-bi.tsx` | Main page. States: idle (upload dropzone), loaded (grid + sidebar). useState hooks, raw fetch with `getApiBaseUrl()`. Follow `main/frontend/pages/lims.tsx` DnD pattern (lines 671-706). |
| `main/frontend/components/bi/Sidebar.tsx` | Left sidebar: app title "MES Agentic BI for PPRS", DATA SOURCE section (file chip with remove), FIELDS section (bullet list of column names). |
| `main/frontend/components/bi/DataGrid.tsx` | TanStack Table v8 rendering data. Props: `columns`, `data`, `totalRows`. Tailwind dark theme: `bg-slate-900`, `border-slate-700/50`, sticky thead. Pagination controls (100 rows/page). |
| `main/frontend/types/bi.ts` | TypeScript interfaces: `BISession`, `BIColumn`, `BIDataResponse`, `BIFilterDef`. |

## Files to Modify

| File | Change |
|------|--------|
| `main/api/app.py` (after line 1491) | Add `from .bi_router import router as bi_router` and `app.include_router(bi_router, prefix="/bi")` |
| `pyproject.toml` | Add `"fpdf2>=2.7.0"` to dependencies |

---

## Implementation Details

### 1. config.py — BI Configuration

```python
import os

class BIConfig:
    bedrock_region: str = os.getenv("BI_BEDROCK_REGION", "us-east-1")
    bedrock_model_id: str = os.getenv("BI_BEDROCK_MODEL_ID", "us.anthropic.claude-3-5-sonnet-20241022-v2:0")
    max_upload_size_mb: int = int(os.getenv("BI_MAX_UPLOAD_SIZE_MB", "50"))
    max_rows: int = int(os.getenv("BI_MAX_ROWS", "100000"))
    session_ttl_seconds: int = int(os.getenv("BI_SESSION_TTL_SECONDS", "3600"))
    max_sessions: int = int(os.getenv("BI_MAX_SESSIONS", "20"))
```

### 2. session_store.py — Session Pattern

Follow `job_store.py` pattern: module-level `_sessions` dict, UUID keys, Pydantic `BISession` model. Store DataFrame separately in `_dataframes` dict (not JSON-serializable). Column metadata pre-computed at upload time.

### 3. bi_router.py — Upload Endpoint

```python
@router.post("/upload")
async def upload_file(file: UploadFile):
    content = await file.read()
    df = parse_file(content, file.filename)
    session_id = create_session(file.filename, df)
    session = get_session(session_id)
    preview = get_page(session_id, page=1, page_size=100)
    return {"session_id": session_id, "filename": session.filename,
            "total_rows": session.total_rows, "total_columns": session.total_columns,
            "columns": session.columns, "preview": preview}
```

---

## Testing Strategy

```bash
# 1. Start API
uv run uvicorn main.api.app:app --port 8080 --reload

# 2. Test upload
curl -X POST http://localhost:8080/bi/upload -F "file=@sample_data.xlsx"
# Expect: { session_id, filename, total_rows, columns: [...] }

# 3. Test paginated data
curl http://localhost:8080/bi/data/{session_id}?page=1&page_size=100
# Expect: { rows: [...100 items], total_rows, page }

# 4. Test frontend
cd main/frontend && npm run dev
# Navigate to http://localhost:3000/agentic-bi
# Upload file -> see data in grid
```

---

## Gate Criteria (Pass/Fail)

- [ ] `POST /bi/upload` with XLSX returns session_id + column metadata
- [ ] `POST /bi/upload` with CSV returns session_id + column metadata
- [ ] `GET /bi/data/{session_id}?page=1` returns 100 rows
- [ ] `GET /bi/schema/{session_id}` returns column names, types, sample values
- [ ] Frontend shows uploaded data in TanStack Table at `/agentic-bi`
- [ ] Sidebar shows filename, field count, and field names
- [ ] Thesis pages (`/generate`, `/history`, `/lims`) still accessible

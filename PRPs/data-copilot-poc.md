# MES Agentic BI for PPRS - Production Readiness Plan (PRP)

**Owner:** Platform Engineering (AI Systems)
**Date:** 2026-02-25
**Version:** 1.0
**Scope:** 5-day Proof of Concept — AI-powered data exploration copilot for pharmaceutical Plant Performance Reporting System (PPRS), with natural language filtering, search, and PDF/Excel export.
**Branch:** `feature/mes-agentic-bi`
**Architecture Plan:** `.claude/plans/foamy-noodling-kay.md`

---

## Executive Summary

This PRP outlines a 5-day Proof of Concept for "MES Agentic BI" — a data copilot for PPRS (Plant Performance Reporting System). Users upload XLSX/CSV files exported from Snowflake (~15K rows, dynamic schemas), explore data via a virtual-scrolling grid with sidebar filters, interact with an AI copilot (AWS Bedrock Claude 3.5 Sonnet) that applies filters/searches/answers questions via tool use, and download filtered data as PDF or Excel.

The system reuses the existing `thesis_project` infrastructure (Next.js, FastAPI, Docker) with a strict **additive-only** strategy.

**What the PoC must demonstrate:**
1. Upload XLSX/CSV file with dynamic column schemas
2. Data grid with virtual scrolling (15K rows), column visibility toggle
3. Per-field sidebar filters (categorical dropdowns, numeric ranges)
4. AI copilot chat that applies filters, searches data, answers questions via tool use
5. Export filtered data as PDF (max 1000 rows) and Excel (full filtered dataset)

**Key Decisions:**
- **Data Grid:** TanStack Table v8 + @tanstack/react-virtual — headless, Tailwind-native, ~20KB
- **Copilot LLM:** AWS Bedrock Converse API (Claude 3.5 Sonnet v2, us-east-1)
- **Data Processing:** pandas DataFrame in-memory per session (15K rows = ~30MB)
- **PDF Export:** fpdf2 — lightweight, pure Python
- **Excel Export:** openpyxl (already in project)
- **Color Accent:** `cyan-*` / `teal-*` (distinct from thesis `blue` and LIMS `emerald`)
- **Auth:** None (PoC) — `NEXT_PUBLIC_AUTH_ENABLED=false`
- **Docker:** `docker-compose.bi.yml` — minimal stack (frontend + API only)
- **Migration:** Additive only — never modify thesis or LIMS files

---

## 1. Architecture Overview

### 1.1 Local Development Stack

```
+-----------------------------------------------------------------+
|                MES Agentic BI - LOCAL DEVELOPMENT                |
+-----------------------------------------------------------------+
|                                                                   |
|  +---------------+      +------------------+                     |
|  |   Next.js     |----->|   FastAPI         |                    |
|  |   Frontend    |      |   Backend         |                    |
|  |  (Port 3000)  |      |  (Port 8080)      |                   |
|  |               |      |                    |                   |
|  |  pages/       |      |  /bi/upload        |                   |
|  |  agentic-bi   |      |  /bi/data/:id      |                   |
|  |  .tsx         |      |  /bi/filter/:id    |                   |
|  |               |      |  /bi/chat/:id      |                   |
|  |  components/  |      |  /bi/export/*      |                   |
|  |    bi/*       |      |                    |                   |
|  +---------------+      +--------+-----------+                   |
|                                  |                               |
|                    +-------------+-------------+                 |
|                    |             |             |                  |
|                    v             v             v                  |
|             +----------+  +-----------+  +----------+            |
|             | pandas   |  | Bedrock   |  | fpdf2 /  |            |
|             | DataFrame|  | Converse  |  | openpyxl |            |
|             | (memory) |  | us-east-1 |  | (export) |            |
|             +----------+  +-----------+  +----------+            |
|                                                                   |
|  Config: .env.local (BI_* prefixed)                              |
+-----------------------------------------------------------------+
```

### 1.2 Data Flow

```
XLSX/CSV Upload
    |
    v
[1. PARSE] -- pandas read_excel/read_csv -> DataFrame + column metadata
    |
    v
[2. STORE] -- In-memory session (session_id -> DataFrame, filters, chat history)
    |
    v
[3. EXPLORE] -- Paginated data API (100 rows/page, server-side sort)
    |
    v
[4. FILTER] -- Sidebar filters OR copilot tool calls -> pandas query
    |
    v
[5. CHAT] -- Bedrock Converse with tools -> apply_filter/search/summarize
    |
    v
[6. EXPORT] -- Filtered data -> PDF (fpdf2) or Excel (openpyxl)
```

### 1.3 Copilot Agentic Loop

```
User Message
    |
    v
[Build System Prompt] -- Column schema, data types, sample values,
    |                     active filters, row counts
    v
[Bedrock Converse] -- Claude 3.5 Sonnet with 5 tools
    |
    +-- tool_use? --YES--> [Execute pandas operation]
    |                           |
    |                           v
    |                      [Feed tool result back to Bedrock]
    |                           |
    |                           v
    |                      [Natural language summary]
    |
    +-- no tools --------> [Direct text response]
    |
    v
[Return response + filters_changed flag + active_filters]
```

### 1.4 Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Data Grid** | TanStack Table v8 + react-virtual | Headless (Tailwind-native), ~20KB vs AG Grid 1.5MB. 15K rows via virtual scroll. |
| **LLM** | Bedrock Converse (Claude 3.5 Sonnet v2) | Best tool use accuracy. Native AWS. Fallback: OpenRouter. |
| **Data Handling** | pandas in-memory per session | 15K x 50 cols = ~30MB. 20-session cap + 1hr TTL. |
| **Schema Detection** | Dynamic (auto-detect from file) | Varying Snowflake exports. Column metadata computed at upload. |
| **Filtering** | Server-side pandas | Complex filters on 15K rows handled server-side. Frontend syncs state. |
| **PDF Export** | fpdf2 (max 1000 rows) | Lightweight. Full export via Excel. |

---

## 2. Tech Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **UI** | Next.js 14 (reuse from thesis_project) | Existing: 3D effects, Framer Motion, dark theme, bold design. |
| **Data Grid** | TanStack Table v8 + @tanstack/react-virtual | Headless, Tailwind-native, virtual scroll for 15K rows. |
| **Copilot LLM** | AWS Bedrock Converse API (Claude 3.5 Sonnet v2) | Best tool use accuracy, native AWS integration. |
| **Data Processing** | pandas + openpyxl | DataFrame operations, XLSX parsing, Excel export. |
| **PDF Generation** | fpdf2 | Lightweight, pure Python tabular PDF. |
| **Observability** | Langfuse Cloud (EU) | `@observe` on chat calls only. Reuse existing credentials. |
| **Docker** | `docker-compose.bi.yml` (minimal: frontend + API) | Same pattern as LIMS PoC. |

---

## 3. API Endpoints

All BI endpoints are mounted under `/bi/*` via a separate `bi_router.py`. Existing thesis and LIMS routes are untouched.

| Endpoint | Method | Purpose | Request | Response |
|----------|--------|---------|---------|----------|
| `/bi/upload` | POST | Upload file, parse, create session | `multipart/form-data` (XLSX/CSV) | `{ session_id, filename, total_rows, total_columns, columns, preview }` |
| `/bi/data/{session_id}` | GET | Paginated filtered data | `?page=1&page_size=100&sort_column=&sort_dir=asc` | `{ rows, total_rows, total_filtered_rows, page, active_filters }` |
| `/bi/schema/{session_id}` | GET | Column metadata | - | `{ columns: [{name, dtype, unique_count, null_count, sample_values}] }` |
| `/bi/filter/{session_id}` | POST | Apply/update filters | `{ filters: [{column, operator, value}] }` | `{ total_filtered_rows, active_filters, preview }` |
| `/bi/chat/{session_id}` | POST | Chat with copilot | `{ message }` | `{ response, tool_calls, filters_changed, active_filters, filtered_row_count }` |
| `/bi/export/excel/{session_id}` | GET | Download filtered Excel | - | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `/bi/export/pdf/{session_id}` | GET | Download filtered PDF | - | `application/pdf` (max 1000 rows) |

---

## 4. Copilot Tool Definitions

System prompt context: column names, data types, sample values (up to 50 for categorical), active filters, total/filtered row counts.

| Tool | Parameters | Backend Action |
|------|-----------|----------------|
| `apply_filter` | `column`, `operator` (equals/not_equals/contains/greater_than/less_than/between/in/is_null), `value` | `filter_engine.apply_filter()` -> pandas query |
| `remove_filter` | `column` (or `__all__` to clear all) | `filter_engine.remove_filter()` |
| `search_data` | `query`, `columns` (optional) | `df[cols].str.contains(query)` -> return top 50 matches |
| `summarize_column` | `column` | `df[col].describe()` for numeric, `value_counts()` for categorical |
| `answer_question` | `analysis_type` (count/group_by/trend/outliers/comparison/general), `columns`, `conditions` | pandas groupby/agg operations |

---

## 5. Migration Strategy: Additive Only

### 5.1 Files to Modify (MINIMAL)

| File | Change | Risk |
|------|--------|------|
| `main/api/app.py` | Mount bi_router: `app.include_router(bi_router, prefix="/bi")` | LOW |
| `pyproject.toml` | Add `fpdf2>=2.7.0` | LOW |
| `main/frontend/package.json` | Add `@tanstack/react-table`, `@tanstack/react-virtual` | LOW |

### 5.2 Files to Create (NEW)

```
thesis_project/
+-- docker-compose.bi.yml               # NEW: Minimal Docker stack
+-- main/
|   +-- api/
|   |   +-- bi_router.py                # NEW: BI API endpoints (/bi/*)
|   +-- src/
|   |   +-- bi/                         # NEW: All BI logic
|   |       +-- __init__.py
|   |       +-- config.py               # BI_* env vars
|   |       +-- session_store.py        # In-memory DataFrame sessions
|   |       +-- data_parser.py          # XLSX/CSV -> pandas DataFrame
|   |       +-- filter_engine.py        # Server-side pandas filtering
|   |       +-- copilot.py              # Bedrock Converse + tool use
|   |       +-- pdf_exporter.py         # fpdf2 PDF generation
|   |       +-- excel_exporter.py       # openpyxl filtered export
|   +-- frontend/
|       +-- pages/
|       |   +-- agentic-bi.tsx          # NEW: Main BI page
|       +-- components/
|       |   +-- bi/
|       |       +-- Sidebar.tsx         # Data source + fields + filters
|       |       +-- DataGrid.tsx        # TanStack Table + virtual scroll
|       |       +-- ChatDrawer.tsx      # Bottom expandable chat drawer
|       |       +-- ColumnSelector.tsx  # Column visibility toggle
|       |       +-- ExportButtons.tsx   # Excel/PDF download buttons
|       +-- types/
|           +-- bi.ts                   # TypeScript types
+-- docs/
    +-- project_p/
        +-- LIMS-XXX-data-copilot-setup.md  # Documentation
```

### 5.3 Files Untouched (ZERO changes)

- `main/frontend/pages/lims.tsx`, `generate.tsx`, `history.tsx` — all existing pages preserved
- `docker-compose.dev.yml`, `docker-compose.lims.yml` — existing stacks preserved
- `main/src/lims/` — all LIMS code preserved
- `main/src/agents/`, `main/src/core/` — thesis code preserved

---

## 6. Reusable Components from thesis_project

| Component | Source | How to Reuse |
|-----------|--------|--------------|
| Next.js UI shell | `main/frontend/` (fonts, dark theme, 3D effects) | Direct reuse |
| Drag-and-drop upload | `main/frontend/pages/lims.tsx` (lines 671-706) | Copy DnD pattern, change file filter |
| Chat message UI | `main/frontend/components/ChatInterface.tsx` | Adapt message bubbles, suggestion chips |
| API base URL helper | `main/frontend/lib/authenticatedFetch.ts` (`getApiBaseUrl()`) | Direct import |
| Session/job store | `main/src/lims/job_store.py` | Follow pattern (UUID keys, Pydantic model, module-level dict) |
| FastAPI router pattern | `main/api/lims_router.py` | Follow `APIRouter(tags=["BI"])` pattern |
| Docker compose pattern | `docker-compose.lims.yml` | Copy and adapt (2-service: API + Frontend) |
| Framer Motion transitions | `lims.tsx` FADE constant | Reuse `AnimatePresence` pattern |

---

## 7. Delivery Structure & Phase Gates (5 Days)

### Day 1: Upload + Grid Foundation

**Backend:** `config.py`, `session_store.py`, `data_parser.py`, `bi_router.py` (upload, data, schema endpoints)
**Frontend:** `agentic-bi.tsx` scaffold, `Sidebar.tsx` (data source + fields list), `DataGrid.tsx` (basic TanStack Table)
**Modify:** `app.py` (register bi_router)

**Gate Criteria:**
- [ ] `POST /bi/upload` with XLSX returns session_id + column metadata
- [ ] `GET /bi/data/{session_id}?page=1` returns paginated rows
- [ ] Frontend shows uploaded data in table at `/agentic-bi`

---

### Day 2: Filters + Virtual Scroll

**Backend:** `filter_engine.py`, filter endpoint in router
**Frontend:** Sidebar filter controls (per-column expandable), `ColumnSelector.tsx`, add virtual scrolling to DataGrid

**Gate Criteria:**
- [ ] `POST /bi/filter/{session_id}` with filters returns filtered row count
- [ ] Sidebar filters update table in real-time
- [ ] Virtual scroll renders 15K rows smoothly (only ~30 DOM elements)
- [ ] Column visibility toggle hides/shows columns

---

### Day 3: Copilot Chat (Highest Risk)

**Backend:** `copilot.py` (Bedrock Converse + 5 tools + agentic loop), chat endpoint
**Frontend:** `ChatDrawer.tsx` (bottom drawer, messages, suggestion chips, filter action badges)

**Gate Criteria:**
- [ ] Chat "Show data where Country = India" applies filter automatically
- [ ] Chat "How many records have Death Rate > 100?" returns correct answer
- [ ] Chat "Summarize the Year column" returns statistics
- [ ] Filter changes from chat sync to sidebar
- [ ] Bedrock Converse API responds within 5 seconds

**Kill Criterion:** If Bedrock model access not available by Day 3, switch to OpenRouter (same tool definitions, different client).

---

### Day 4: Export + Reports

**Backend:** `pdf_exporter.py` (fpdf2), `excel_exporter.py` (openpyxl), export endpoints
**Frontend:** `ExportButtons.tsx`, summary table via copilot

**Gate Criteria:**
- [ ] Excel export downloads filtered data with correct columns/rows
- [ ] PDF export downloads formatted table (landscape, headers, max 1000 rows)
- [ ] Export buttons show filtered row count
- [ ] Chat "Generate a summary table" produces summary

---

### Day 5: Polish + Deploy

**Design:** Bold typography (Space Grotesk), cyan accent palette, Framer Motion transitions, loading skeletons
**Infra:** `docker-compose.bi.yml`, Terraform update (Bedrock IAM on API role)
**Testing:** E2E with sample data, edge cases
**Docs:** Documentation + PRP update

**Gate Criteria:**
- [ ] Full flow: Upload -> Filter -> Chat -> Export works end-to-end
- [ ] Docker compose starts and works
- [ ] Bold design passes visual review
- [ ] Documentation updated

---

## 8. Environment Configuration

```bash
# .env.local (BI-specific additions)
# AWS Bedrock
BI_BEDROCK_REGION=us-east-1
BI_BEDROCK_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0

# Session limits
BI_MAX_UPLOAD_SIZE_MB=50
BI_MAX_ROWS=100000
BI_SESSION_TTL_SECONDS=3600
BI_MAX_SESSIONS=20

# Langfuse (reuse existing)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

---

## 9. Pre-Requisites (Before Day 1)

1. **Enable Bedrock model access**: AWS Console -> Bedrock -> Model access -> Request `us.anthropic.claude-3-5-sonnet-20241022-v2:0` in `us-east-1` (0-24 hours)
2. **Sample data file**: XLSX or CSV with ~15K rows for testing
3. **Install npm packages**: `cd main/frontend && npm install @tanstack/react-table @tanstack/react-virtual`
4. **Install Python package**: Add `fpdf2>=2.7.0` to `pyproject.toml` and `uv sync`

---

## 10. Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Bedrock model access not enabled | High | Pre-req: enable in AWS console. Fallback: OpenRouter (working in LIMS). |
| TanStack virtual scroll complexity | Medium | Day 1 basic table works without it. Add virtual on Day 2. |
| PDF export for wide tables | Medium | Cap at 1000 rows + landscape mode. Excel for full export. |
| Day 3 copilot integration | High | Test with hardcoded queries first. Fallback: text-only chat. |
| Session memory pressure | Low | 20-session cap with LRU eviction. 15K rows = ~30MB per session. |

---

## 11. Task Files

| Task | File | Day | Description |
|------|------|-----|-------------|
| B1 | `PRPs/tasks/B1-upload-grid-foundation.md` | 1 | Upload XLSX/CSV, parse with pandas, session store, TanStack Table grid, sidebar |
| B2 | `PRPs/tasks/B2-filters-virtual-scroll.md` | 2 | Server-side pandas filtering, sidebar filter controls, virtual scroll for 15K rows |
| B3 | `PRPs/tasks/B3-copilot-chat-bedrock.md` | 3 | AWS Bedrock Converse + 5 tools, agentic loop, bottom chat drawer |
| B4 | `PRPs/tasks/B4-export-pdf-excel.md` | 4 | PDF export (fpdf2, max 1000 rows), Excel export (openpyxl), export buttons |
| B5 | `PRPs/tasks/B5-polish-deploy.md` | 5 | Bold design, Docker compose, E2E testing, documentation |

Task prefix `B` avoids collision with thesis tasks (0.x-5.x) and LIMS tasks (Lx).

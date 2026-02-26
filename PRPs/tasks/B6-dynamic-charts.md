# Task B6 — Dynamic Charts & Visualization

**Phase:** 6 (Visualization) | **Day:** 6
**Dependencies:** B2 (Filters), B4 (Export — shares session/filter architecture)
**Branch:** `feature/mes-agentic-bi`
**Status:** IN PROGRESS
**Estimated effort:** 1 day

---

## Objective

Add a dynamic graph/visualization feature to MES Agentic BI. A "Charts" button on the main grid page navigates to a dedicated charts page that auto-detects column types (numeric, categorical, temporal) and recommends appropriate visualizations (bar, line, scatter, histogram, heatmap). Includes KPI summary cards and a custom chart builder. Must work with any uploaded dataset schema.

---

## Files to Create

| File | Purpose |
|------|---------|
| `main/src/bi/chart_engine.py` | Column classifier, chart recommendation engine, pandas aggregation (bar, line, scatter, histogram, heatmap) |
| `main/frontend/pages/bi-charts.tsx` | Charts page shell — reads `?session=xxx`, renders ChartPage |
| `main/frontend/components/bi/charts/ChartPage.tsx` | Orchestrator — fetches recommendations, renders KPI cards + chart grid + custom builder |
| `main/frontend/components/bi/charts/KPICards.tsx` | Summary cards for numeric columns (count, mean, min, max) |
| `main/frontend/components/bi/charts/ChartCard.tsx` | Single chart container with loading state, aggregation selector |
| `main/frontend/components/bi/charts/BarChartView.tsx` | Recharts BarChart wrapper with grouped bar support |
| `main/frontend/components/bi/charts/LineChartView.tsx` | Recharts LineChart wrapper with multi-line support |
| `main/frontend/components/bi/charts/ScatterChartView.tsx` | Recharts ScatterChart wrapper with sampling |
| `main/frontend/components/bi/charts/HistogramView.tsx` | Recharts BarChart in histogram mode |
| `main/frontend/components/bi/charts/HeatmapView.tsx` | CSS grid heatmap with cyan color scale |
| `main/frontend/components/bi/charts/ChartBuilder.tsx` | Custom chart builder UI (x/y column, group-by, aggregation, chart type) |

## Files to Modify

| File | Change |
|------|--------|
| `main/api/bi_router.py` | Add `GET /bi/charts/recommend/{session_id}` and `POST /bi/charts/data/{session_id}` |
| `main/src/bi/__init__.py` | Export `recommend_charts`, `get_chart_data` |
| `main/frontend/pages/agentic-bi.tsx` | Add `useRouter` + "Charts" button in header bar |
| `main/frontend/types/bi.ts` | Add chart-related TypeScript interfaces |
| `main/frontend/package.json` | Add `recharts` dependency |

---

## Implementation Details

### Backend: Chart Engine (`chart_engine.py`)

**Column Classification:**
- `pd.api.types.is_numeric_dtype()` → `"numeric"`
- Datetime dtype or name heuristic (date/month/year) + YYYY-MM pattern → `"temporal"`
- `unique_count <= 50` → `"categorical"`
- Else → `"text"` (excluded)

**Recommendation Rules (capped at 8):**
| Rule | Condition | Chart |
|------|-----------|-------|
| R1 | categorical + numeric | Bar (mean) |
| R2 | temporal + numeric | Line (mean) |
| R3 | 2 numerics | Scatter (sampled 500) |
| R4 | 1 numeric | Histogram (20 bins) |
| R5 | 2 categoricals (<=10 unique) + numeric | Heatmap (mean) |

**Aggregation:** Server-side pandas groupby. Supports sum, mean, median, count, min, max.

### Frontend: Recharts

Library: `recharts` v2.15+ (~45KB gzipped, native React components).
Color palette: cyan-500 (#06b6d4), teal-500 (#14b8a6), cyan-300 (#67e8f9).

---

## Testing Strategy

```bash
# 1. Start backend
cd main && uv run uvicorn api.main:app --reload --port 8080

# 2. Start frontend
cd main/frontend && npm run dev

# 3. Upload demo CSV via UI → verify session created
# 4. Click "Charts" button → verify /bi-charts?session=xxx loads
# 5. Verify KPI cards render for Downtime_Minutes and OEE_Percent
# 6. Verify auto-recommended bar, line, scatter, histogram charts
# 7. Change aggregation on a bar chart (mean → sum)
# 8. Use ChartBuilder to create custom grouped bar chart
# 9. Apply filters on grid page → navigate to charts → verify filtered data
# 10. Click "Back to Grid" → verify navigation
```

---

## Gate Criteria (Pass/Fail)

- [ ] `GET /bi/charts/recommend/{session_id}` returns KPI cards + >= 3 recommended charts
- [ ] `POST /bi/charts/data/{session_id}` returns correct aggregated data for all 5 chart types
- [ ] Chart data respects active filters
- [ ] Charts page renders at `/bi-charts?session=xxx`
- [ ] KPI cards show count, mean, min, max for numeric columns
- [ ] ChartBuilder allows custom chart creation (x, y, group-by, aggregation, type)
- [ ] "Charts" button on grid page navigates to charts page
- [ ] "Back to Grid" navigates back
- [ ] Cyan/teal color palette consistent with BI theme
- [ ] Works with any uploaded CSV/XLSX (dynamic schema)

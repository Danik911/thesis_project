# Task B2 — Filters + Virtual Scroll

**Phase:** 2 (Interaction) | **Day:** 2
**Dependencies:** B1 (Upload + Grid Foundation)
**Branch:** `feature/mes-agentic-bi`
**Status:** NOT STARTED
**Estimated effort:** 1 day

---

## Objective

Add server-side filtering engine and sidebar filter controls. Implement virtual scrolling with `@tanstack/react-virtual` so 15K rows render smoothly. Add column visibility toggle. Filters applied via sidebar should update the grid in real-time via API calls.

---

## Files to Create

| File | Purpose |
|------|---------|
| `main/src/bi/filter_engine.py` | `FilterEngine(session_id)` class. Methods: `apply_filter(column, operator, value)`, `remove_filter(column)`, `clear_filters()`, `get_page(page, page_size)`, `get_active_filters()`, `filtered_count()`. Operators: equals, not_equals, contains, greater_than, less_than, greater_equal, less_equal, between, in, is_null, is_not_null. |
| `main/frontend/components/bi/ColumnSelector.tsx` | Dropdown/popover with checkboxes for each column. Toggle column visibility in the TanStack Table. Shows "Columns (N/M)" count. |

## Files to Modify

| File | Change |
|------|--------|
| `main/api/bi_router.py` | Add `POST /bi/filter/{session_id}` endpoint. Request: `{ filters: [{column, operator, value}] }`. Response: `{ total_filtered_rows, active_filters, preview }`. |
| `main/frontend/components/bi/Sidebar.tsx` | Add FIELD FILTERS section below FIELDS. Each field is expandable (`>` chevron). Categorical fields: multi-select checkboxes from `sample_values`. Numeric fields: min/max range inputs. |
| `main/frontend/components/bi/DataGrid.tsx` | Replace basic table body with `@tanstack/react-virtual` virtualizer. Only render ~30 visible rows + buffer. Container height: `calc(100vh - header - chat bar)`. |
| `main/frontend/pages/agentic-bi.tsx` | Add `activeFilters` state. Sidebar filter changes -> `POST /bi/filter` -> update grid data. Show "Showing X of Y rows" footer. |

---

## Implementation Details

### 1. filter_engine.py — Pandas Filtering

```python
class FilterEngine:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self._filters: list[dict] = []

    def apply_filter(self, column: str, operator: str, value) -> int:
        self._filters = [f for f in self._filters if f["column"] != column]
        self._filters.append({"column": column, "operator": operator, "value": value})
        return self.filtered_count()

    def _apply_all_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        for f in self._filters:
            col, op, val = f["column"], f["operator"], f["value"]
            if op == "equals": df = df[df[col] == val]
            elif op == "contains": df = df[df[col].astype(str).str.contains(str(val), case=False, na=False)]
            elif op == "greater_than": df = df[df[col] > val]
            elif op == "between": df = df[df[col].between(val[0], val[1])]
            elif op == "in": df = df[df[col].isin(val)]
            # ... etc
        return df
```

### 2. Virtual Scroll (DataGrid.tsx)

```tsx
import { useVirtualizer } from '@tanstack/react-virtual';

const rowVirtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 35,  // row height in px
    overscan: 10,
});
```

---

## Testing Strategy

```bash
# 1. Test filter API
curl -X POST http://localhost:8080/bi/filter/{session_id} \
  -H "Content-Type: application/json" \
  -d '{"filters": [{"column": "Country Name", "operator": "equals", "value": "India"}]}'
# Expect: { total_filtered_rows: ~800, active_filters: [...] }

# 2. Test clear filters
curl -X POST http://localhost:8080/bi/filter/{session_id} \
  -H "Content-Type: application/json" \
  -d '{"filters": []}'
# Expect: { total_filtered_rows: 15000 }

# 3. Frontend: apply filter via sidebar -> grid updates
# 4. Frontend: scroll through 15K rows -> smooth, no lag
```

---

## Gate Criteria (Pass/Fail)

- [ ] `POST /bi/filter` with equals filter returns correct filtered count
- [ ] `POST /bi/filter` with contains filter works on text columns
- [ ] `POST /bi/filter` with greater_than works on numeric columns
- [ ] Sidebar filter controls render per-column (expandable)
- [ ] Applying sidebar filter updates grid data in real-time
- [ ] Virtual scroll renders 15K rows with only ~30 DOM elements
- [ ] Column selector shows/hides columns in the grid
- [ ] "Showing X of Y rows" footer updates after filtering

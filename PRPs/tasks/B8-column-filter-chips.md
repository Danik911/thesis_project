# Task B8 — Column Filter Chips

**Phase:** 8 (UX Enhancement) | **Day:** 7
**Dependencies:** B2 (Filters)
**Branch:** `feature/mes-agentic-bi`
**Status:** DONE
**Estimated effort:** 0.5 day

---

## Objective

Display removable filter chips directly below each column header in the DataGrid, so users can see at a glance which filters are active per column. Each chip represents a single filter value (for categorical "in" filters) or the full operator expression (for numeric/copilot filters). Clicking the × on a chip removes that specific value and refreshes the grid. The chips stay in sync with the sidebar filters since both share the same `activeFilters` state in `agentic-bi.tsx`.

---

## Files to Create

None — frontend-only modification of existing components.

## Files to Modify

| File | Change |
|------|--------|
| `main/frontend/components/bi/DataGrid.tsx` | Add `activeFilters` and `onFilterRemove` props. Add `getChipsForColumn()` utility function. Add `FilterChipRow` inline component. Change column `header` from plain string to custom render function with chips. Adjust `<th>` CSS to allow chip wrapping. Add `filtersByColumn` memo. Import `BIFilterDef`. |
| `main/frontend/pages/agentic-bi.tsx` | Add `useCallback` import. Create `handleFilterRemove` callback that removes a single value from "in" array filters or removes an entire filter. Pass `activeFilters` and `onFilterRemove={handleFilterRemove}` to `<DataGrid>`. |

---

## Implementation Details

### DataGrid: Filter Chip Rendering

**New props on `DataGridProps`:**
```typescript
activeFilters: BIFilterDef[];
onFilterRemove: (column: string, value?: string | number) => void;
```

**Chip formatting (`getChipsForColumn`):**

| Operator | Value Shape | Chip Label(s) | Example |
|----------|-------------|---------------|---------|
| `in` | `["Running", "Stopped"]` | One chip per value: `Running ×`, `Stopped ×` | Sidebar categorical |
| `equals` | `"India"` | `= India ×` | Copilot equals |
| `not_equals` | `"China"` | `≠ China ×` | Copilot exclusion |
| `contains` | `"maint"` | `"maint" ×` | Copilot substring |
| `greater_equal` | `100` | `≥ 100 ×` | Sidebar min-only |
| `less_equal` | `200` | `≤ 200 ×` | Sidebar max-only |
| `greater_than` | `100` | `> 100 ×` | Copilot numeric |
| `less_than` | `50` | `< 50 ×` | Copilot numeric |
| `between` | `[100, 200]` | `100–200 ×` (single chip, en-dash) | Sidebar full range |
| `is_null` | `null` | `is null ×` | Copilot null check |
| `is_not_null` | `null` | `is not null ×` | Copilot not-null check |

**Chip styling:**
- `bg-cyan-500/15 text-cyan-300 border border-cyan-500/25` — consistent with BI cyan theme
- `text-[10px]` — smaller than header text (`text-xs` = 12px)
- `truncate max-w-[80px]` on label — prevents long values from blowing out column width
- `flex-wrap gap-1 mt-1` — chips wrap within the column, tiny gap below column name

**Column header change:**
Replace `header: column` (plain string) with a function returning `<div>` containing the column name `<span>` and `<FilterChipRow>` component. Move `whitespace-nowrap overflow-hidden text-ellipsis` from `<th>` to the column name `<span>` so the chip row can wrap freely.

### Parent Page: Filter Removal Handler

`handleFilterRemove(column, value?)` in `agentic-bi.tsx`:
- If `value` provided (categorical "in" chip): remove that value from the filter's array. If array becomes empty, remove the filter entirely.
- If `value` omitted (numeric/single-value chip): remove the entire filter for that column.
- Calls existing `handleFiltersChange(nextFilters)` which POSTs to `/bi/filter/{sessionId}` and refreshes the grid.

**Removal chain:**
```
Chip × click → onFilterRemove(column, value?) → handleFilterRemove →
  compute nextFilters → handleFiltersChange(nextFilters) →
  POST /bi/filter/{sessionId} → setActiveFilters → loadPage(1) →
  DataGrid re-renders (chips update) + Sidebar re-renders (checkboxes update)
```

---

## Testing Strategy

```bash
# 1. Start backend
cd main && uv run uvicorn api.main:app --reload --port 8080

# 2. Start frontend
cd main/frontend && npm run dev

# 3. Upload demo CSV with mixed column types (categorical + numeric)
# 4. Apply categorical filter via sidebar (check 2+ values) → verify chips appear under that column header
# 5. Click × on one chip → verify that value removed, other chips remain, sidebar checkbox unchecked
# 6. Click × on last remaining chip → verify filter fully removed, no chips shown, sidebar cleared
# 7. Apply numeric range filter (both min and max) → verify single "100–200" chip appears
# 8. Apply min-only filter → verify "≥ 100" chip
# 9. Remove numeric chip via × → verify filter removed
# 10. Use copilot: "Show rows where Country equals India" → verify "= India" chip appears
# 11. Use copilot: "Show rows containing 'maint'" → verify contains chip appears
# 12. Verify sticky header still works (scroll down, header stays pinned with chips)
# 13. Verify virtual scroll still smooth with 15K rows
# 14. Test with many filter values (8+ categorical) → verify chips wrap, don't break layout
```

---

## Gate Criteria (Pass/Fail)

- [x] DataGrid renders cyan-themed filter chips below column headers for active filters
- [x] Categorical "in" filters show one chip per selected value
- [x] Numeric range "between" filters show a single "min–max" chip
- [x] Numeric single-bound filters show operator symbol + value (e.g., "≥ 100")
- [x] Copilot-applied filters (equals, contains, is_null, etc.) render correct chip labels
- [x] Clicking × on a chip removes that specific filter value and refreshes the grid
- [x] Removing one value from a multi-value "in" filter keeps the remaining values active
- [x] Removing the last value from a multi-value "in" filter removes the filter entirely
- [x] Sidebar checkboxes update in sync when a chip is removed from the column header
- [x] Columns without filters show no chips (no layout change from current behavior)
- [x] Chips do not break virtual scroll or sticky header behavior
- [x] Long filter values are truncated with ellipsis in chips
- [x] Works with any uploaded CSV/XLSX schema (dynamic columns)

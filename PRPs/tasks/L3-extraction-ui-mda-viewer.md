# Task L3 — Extraction UI: MDAViewer Component + Progress Indicators

**Phase:** 3 (Extraction UI) | **PRP Tasks Merged:** L3.1, L3.2, L3.3
**Dependencies:** Task L2 (Foundation)
**Branch:** `prjoject_p_protatype`

---

## Objective

Replace the raw JSON `<pre>` display in `lims.tsx` with a professional tabbed table viewer showing all 4 MDA sheets, and add extraction progress stage indicators during loading.

---

## Files to Create

| File | Purpose |
|------|---------|
| `main/frontend/components/MDAViewer.tsx` | 4-tab table viewer (Analysis, Components, CalcVariables, Calculations) with emerald color scheme |

## Files to Modify

| File | Change |
|------|--------|
| `main/frontend/pages/lims.tsx` | Replace `<pre>` JSON block (lines ~250-265) with `<MDAViewer>`, add extraction stage indicators during loading |

---

## Implementation Details

### 1. MDAViewer.tsx — Tabbed Table Viewer

A reusable component that displays MDA data in 4 tabs with column definitions per sheet.

```tsx
import { useState } from 'react';

interface MDAViewerProps {
  data: {
    analyses?: Array<Record<string, unknown>>;
    components?: Array<Record<string, unknown>>;
    calc_variables?: Array<Record<string, unknown>>;
    calculations?: Array<Record<string, unknown>>;
  };
  validated: boolean;
}

const TABS = [
  { key: 'analyses', label: 'Analysis', icon: '🧪' },
  { key: 'components', label: 'Components', icon: '🔩' },
  { key: 'calc_variables', label: 'Calc Variables', icon: '📐' },
  { key: 'calculations', label: 'Calculations', icon: '💻' },
] as const;

// Column definitions per sheet (key columns — not all fields)
const COLUMN_DEFS: Record<string, string[]> = {
  analyses: ['name', 'analysis_type', 'reported_name', 'common_name', 'description', 'active'],
  components: [
    'analysis', 'component_name', 'order_number', 'result_type',
    'units', 'uses_instrument', 'auto_calc', 'list_key', 'reportable',
  ],
  calc_variables: [
    'analysis', 'component', 'name', 'reference_type',
    'reference_analysis', 'scope', 'function',
  ],
  calculations: ['analysis', 'component', 'calculation_type', 'description', 'source_code'],
};

export default function MDAViewer({ data, validated }: MDAViewerProps) {
  const [activeTab, setActiveTab] = useState<string>('analyses');

  const rows = (data as Record<string, unknown[]>)[activeTab] ?? [];
  const columns = COLUMN_DEFS[activeTab] ?? [];

  return (
    <div className="rounded-xl bg-slate-800/50 border border-slate-700/50 overflow-hidden">
      {/* Tab Bar */}
      <div className="flex border-b border-slate-700/50 bg-slate-800/80 overflow-x-auto">
        {TABS.map(tab => {
          const count = ((data as Record<string, unknown[]>)[tab.key] ?? []).length;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-3 text-sm font-medium transition-all flex items-center gap-2 whitespace-nowrap ${
                activeTab === tab.key
                  ? 'text-emerald-400 border-b-2 border-emerald-400 bg-emerald-500/5'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <span>{tab.icon}</span>
              {tab.label}
              <span className="text-xs px-1.5 py-0.5 rounded bg-slate-700 text-slate-300">
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Table */}
      {rows.length === 0 ? (
        <div className="p-8 text-center text-slate-500">
          No {activeTab.replace(/_/g, ' ')} data extracted.
        </div>
      ) : (
        <div className="overflow-x-auto max-h-[500px] overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-slate-800 z-10">
              <tr>
                {columns.map(col => (
                  <th key={col} className="px-3 py-2 text-left text-xs font-medium text-slate-400 uppercase tracking-wider border-b border-slate-700">
                    {col.replace(/_/g, ' ')}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {rows.map((row, idx) => (
                <tr key={idx} className="hover:bg-slate-700/30 transition-colors">
                  {columns.map(col => (
                    <td key={col} className="px-3 py-2 text-slate-300 font-mono text-xs whitespace-nowrap">
                      {formatCell((row as Record<string, unknown>)[col])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function formatCell(value: unknown): string {
  if (value === null || value === undefined) return '--';
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  if (Array.isArray(value)) return value.join(', ');
  return String(value);
}
```

### 2. lims.tsx Changes

**Replace** the raw JSON `<pre>` block (lines ~250-265) with `MDAViewer`:

```tsx
import MDAViewer from '@/components/MDAViewer';

// In the results section, replace the <pre> block:
<MDAViewer
  data={result.validated && result.mda_template
    ? result.mda_template
    : result.raw_extraction}
  validated={result.validated}
/>
```

**Add** extraction stage indicators during loading:

```tsx
import { useEffect } from 'react';

// New state for extraction stages
const EXTRACTION_STAGES = [
  'Uploading PDF...',
  'Extracting with LlamaExtract...',
  'Validating schema...',
];
const [extractionStage, setExtractionStage] = useState(0);

// Timer-based stage advancement
useEffect(() => {
  if (!loading) {
    setExtractionStage(0);
    return;
  }
  const timers = [
    setTimeout(() => setExtractionStage(1), 2000),
    setTimeout(() => setExtractionStage(2), 30000),
  ];
  return () => timers.forEach(clearTimeout);
}, [loading]);

// Replace the button loading text:
{loading ? (
  <span className="flex items-center gap-2">
    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
    {EXTRACTION_STAGES[extractionStage]}
  </span>
) : (
  'Extract MDA Data'
)}
```

---

## Reusable Patterns

- **Emerald color scheme**: Already established in `lims.tsx` (bg-emerald-600/20, text-emerald-400, border-emerald-500/30)
- **Table styling**: Follows thesis component patterns (slate-800 backgrounds, slate-700 borders, monospace data cells)
- **Tab pattern**: Similar to how thesis uses stage-based views in `JobProgress.tsx`

---

## Testing Strategy

```bash
# 1. Start local API + frontend
uv run uvicorn main.api.app:app --port 8080
# In another terminal:
cd main/frontend && npm run dev

# 2. Open http://localhost:3000/lims
# 3. Upload demo PDF
# 4. Verify:
#    - Loading shows stage progression (Uploading -> Extracting -> Validating)
#    - Result shows 4-tab table (not raw JSON)
#    - Each tab displays correct columns
#    - Empty tabs show "No data" message
#    - Tab counts match number of items

# 5. Verify thesis pages still work:
#    - http://localhost:3000/generate
#    - http://localhost:3000/history
```

---

## Gate Criteria (Pass/Fail)

- [ ] Upload PDF at `localhost:3000/lims` -> see 4-tab MDA table (not raw JSON)
- [ ] Each tab shows correct column headers and data rows
- [ ] Empty sheets show "No data" message
- [ ] Loading state shows extraction stages
- [ ] Thesis pages (`/generate`, `/history`) still accessible

---

## Sources

- [React useState/useEffect](https://react.dev/reference/react/useState)
- [Next.js Pages Router](https://nextjs.org/docs/pages)
- [Tailwind CSS](https://tailwindcss.com/docs)

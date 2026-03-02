uv run uvicorn api.app:app --port 8080 --reloadimport { useState } from 'react';
import ProvenanceBadge from '@/components/ProvenanceBadge';
import type { ProvenanceBadgeProps } from '@/components/ProvenanceBadge';

interface MDAViewerProps {
  data: {
    analyses?: Array<Record<string, unknown>>;
    components?: Array<Record<string, unknown>>;
    calc_variables?: Array<Record<string, unknown>>;
    calculations?: Array<Record<string, unknown>>;
  };
  validated: boolean;
  highlightedCells?: Set<string>;
  title?: string;
  provenanceMap?: Record<string, { source: ProvenanceBadgeProps['source']; confidence?: number; detail?: string }>;
}

const TABS = [
  { key: 'analyses', label: 'Analysis', icon: '🧪' },
  { key: 'components', label: 'Components', icon: '🔩' },
  { key: 'calc_variables', label: 'Calc Variables', icon: '📐' },
  { key: 'calculations', label: 'Calculations', icon: '💻' },
] as const;

const COLUMN_DEFS: Record<string, string[]> = {
  analyses: ['name', 'analysis_type', 'reported_name', 'common_name', 'description', 'active'],
  components: [
    'analysis',
    'component_name',
    'order_number',
    'result_type',
    'units',
    'uses_instrument',
    'auto_calc',
    'list_key',
    'reportable',
  ],
  calc_variables: [
    'analysis',
    'component',
    'name',
    'reference_type',
    'reference_analysis',
    'scope',
    'function',
  ],
  calculations: ['analysis', 'component', 'calculation_type', 'description', 'source_code'],
};

export default function MDAViewer({ data, validated, highlightedCells, title, provenanceMap }: MDAViewerProps) {
  const [activeTab, setActiveTab] = useState<string>('analyses');

  const rows = (data as Record<string, unknown[]>)[activeTab] ?? [];
  const columns = COLUMN_DEFS[activeTab] ?? [];

  return (
    <div className="rounded-xl bg-slate-800/50 border border-slate-700/50 overflow-hidden">
      <div className="px-4 py-3 bg-slate-800/80 border-b border-slate-700/50">
        <h3 className="text-sm font-medium text-slate-300">
          {title ?? (validated ? 'Validated MDA Template' : 'Raw Extraction Data')}
        </h3>
      </div>

      <div className="flex border-b border-slate-700/50 bg-slate-800/80 overflow-x-auto">
        {TABS.map((tab) => {
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
              <span className="text-xs px-1.5 py-0.5 rounded bg-slate-700 text-slate-300">{count}</span>
            </button>
          );
        })}
      </div>

      {rows.length === 0 ? (
        <div className="p-8 text-center text-slate-500">No {activeTab.replace(/_/g, ' ')} data extracted.</div>
      ) : (
        <div className="overflow-x-auto max-h-[500px] overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-slate-800 z-10">
              <tr>
                {columns.map((col) => (
                  <th
                    key={col}
                    className="px-3 py-2 text-left text-xs font-medium text-slate-400 uppercase tracking-wider border-b border-slate-700"
                  >
                    {col.replace(/_/g, ' ')}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {rows.map((row, idx) => (
                <tr key={idx} className="hover:bg-slate-700/30 transition-colors">
                  {columns.map((col) => {
                    const cellKey = `${activeTab}.${idx}.${col}`;
                    const isHighlighted = highlightedCells?.has(cellKey);
                    return (
                      <td
                        key={col}
                        className={`px-3 py-2 font-mono text-xs whitespace-nowrap ${
                          isHighlighted
                            ? 'text-emerald-300 bg-emerald-500/10 ring-1 ring-inset ring-emerald-500/30'
                            : 'text-slate-300'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <span>{formatCell((row as Record<string, unknown>)[col])}</span>
                          {provenanceMap?.[cellKey] && (
                            <ProvenanceBadge
                              source={provenanceMap[cellKey].source}
                              confidence={provenanceMap[cellKey].confidence}
                              detail={provenanceMap[cellKey].detail}
                            />
                          )}
                        </div>
                      </td>
                    );
                  })}
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
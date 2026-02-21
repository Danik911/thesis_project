import { useMemo, useState } from 'react';

type ConflictResolution = 'template' | 'extracted' | 'custom';

interface MergeConflict {
  id: string;
  field: string;
  templateValue: string;
  extractedValue: string;
}

interface MergeConflictPanelProps {
  conflicts: MergeConflict[];
  onResolve: (resolved: Array<{ id: string; resolution: ConflictResolution; value: string }>) => void;
}

export default function MergeConflictPanel({ conflicts, onResolve }: MergeConflictPanelProps) {
  const [resolutions, setResolutions] = useState<Record<string, { mode: ConflictResolution; customValue: string }>>({});

  const currentResolutions = useMemo(
    () =>
      conflicts.map((conflict) => {
        const existing = resolutions[conflict.id] ?? { mode: 'template' as ConflictResolution, customValue: '' };
        const value =
          existing.mode === 'template'
            ? conflict.templateValue
            : existing.mode === 'extracted'
              ? conflict.extractedValue
              : existing.customValue;

        return { id: conflict.id, resolution: existing.mode, value };
      }),
    [conflicts, resolutions]
  );

  function setAll(mode: ConflictResolution) {
    const next: Record<string, { mode: ConflictResolution; customValue: string }> = {};
    for (const conflict of conflicts) {
      next[conflict.id] = { mode, customValue: '' };
    }
    setResolutions(next);
  }

  return (
    <div className="rounded-xl bg-slate-800/50 border border-slate-700/50 p-5 space-y-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-wide text-slate-500">Merge Stage</p>
          <h3 className="text-lg font-semibold text-slate-100 mt-1">Conflict Resolution</h3>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setAll('template')} className="px-3 py-1.5 rounded-lg text-xs border border-slate-600 text-slate-300 hover:bg-slate-700/50">Accept All Template</button>
          <button onClick={() => setAll('extracted')} className="px-3 py-1.5 rounded-lg text-xs border border-slate-600 text-slate-300 hover:bg-slate-700/50">Accept All Extracted</button>
        </div>
      </div>

      <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-500/5 border border-blue-500/15">
        <svg className="w-4 h-4 text-blue-400/70 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
        <p className="text-xs text-blue-400/70">
          You decide. AI proposes merge resolutions — final authority is yours.
        </p>
      </div>

      {conflicts.length === 0 ? (
        <p className="text-sm text-slate-400">No merge conflicts available from backend payload.</p>
      ) : (
        <div className="space-y-3">
          {conflicts.map((conflict) => {
            const current = resolutions[conflict.id] ?? { mode: 'template' as ConflictResolution, customValue: '' };
            return (
              <div key={conflict.id} className="rounded-lg border border-slate-700 p-3 space-y-3">
                <p className="text-sm text-slate-200 font-medium">{conflict.field}</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div className="rounded-lg bg-slate-900 border border-slate-700 p-2 max-h-24 overflow-y-auto">
                    <p className="text-[11px] uppercase tracking-wide text-slate-500">Template</p>
                    <p className="text-sm text-slate-200 mt-1 break-words">{conflict.templateValue}</p>
                  </div>
                  <div className="rounded-lg bg-slate-900 border border-slate-700 p-2 max-h-24 overflow-y-auto">
                    <p className="text-[11px] uppercase tracking-wide text-slate-500">Extracted</p>
                    <p className="text-sm text-slate-200 mt-1 break-words">{conflict.extractedValue}</p>
                  </div>
                </div>

                <div className="flex flex-wrap gap-4 text-sm text-slate-300">
                  <label className="inline-flex items-center gap-1.5">
                    <input
                      type="radio"
                      name={`resolution-${conflict.id}`}
                      checked={current.mode === 'template'}
                      onChange={() => setResolutions((prev) => ({ ...prev, [conflict.id]: { ...prev[conflict.id], mode: 'template', customValue: prev[conflict.id]?.customValue ?? '' } }))}
                    />
                    Use Template
                  </label>
                  <label className="inline-flex items-center gap-1.5">
                    <input
                      type="radio"
                      name={`resolution-${conflict.id}`}
                      checked={current.mode === 'extracted'}
                      onChange={() => setResolutions((prev) => ({ ...prev, [conflict.id]: { ...prev[conflict.id], mode: 'extracted', customValue: prev[conflict.id]?.customValue ?? '' } }))}
                    />
                    Use Extracted
                  </label>
                  <label className="inline-flex items-center gap-1.5">
                    <input
                      type="radio"
                      name={`resolution-${conflict.id}`}
                      checked={current.mode === 'custom'}
                      onChange={() => setResolutions((prev) => ({ ...prev, [conflict.id]: { ...prev[conflict.id], mode: 'custom', customValue: prev[conflict.id]?.customValue ?? '' } }))}
                    />
                    Enter Custom
                  </label>
                </div>

                {current.mode === 'custom' && (
                  <input
                    value={current.customValue}
                    onChange={(e) =>
                      setResolutions((prev) => ({
                        ...prev,
                        [conflict.id]: { mode: 'custom', customValue: e.target.value },
                      }))
                    }
                    className="w-full rounded-lg border border-slate-600 bg-slate-900 text-slate-200 text-sm px-3 py-2"
                    placeholder="Enter custom value"
                  />
                )}
              </div>
            );
          })}
        </div>
      )}

      <div className="flex justify-end">
        <button
          onClick={() => onResolve(currentResolutions)}
          className="px-4 py-2 rounded-lg text-sm font-medium bg-emerald-600 hover:bg-emerald-500 text-white transition-all"
        >
          Apply Merge Decisions
        </button>
      </div>
    </div>
  );
}

export type { MergeConflictPanelProps, MergeConflict, ConflictResolution };
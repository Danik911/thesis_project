import { useMemo, useState } from 'react';

interface ColumnSelectorProps {
  columns: string[];
  visibleColumns: string[];
  onChange: (columns: string[]) => void;
}

export default function ColumnSelector({ columns, visibleColumns, onChange }: ColumnSelectorProps) {
  const [open, setOpen] = useState(false);

  const visibleSet = useMemo(() => new Set(visibleColumns), [visibleColumns]);

  const toggleColumn = (column: string) => {
    const next = visibleSet.has(column)
      ? visibleColumns.filter((item) => item !== column)
      : [...visibleColumns, column];

    if (next.length === 0) {
      return;
    }

    const ordered = columns.filter((item) => next.includes(item));
    onChange(ordered);
  };

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((current) => !current)}
        className="px-3 py-1.5 text-xs rounded-md border border-slate-700 text-slate-300 hover:border-slate-600"
      >
        Columns ({visibleColumns.length}/{columns.length})
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-64 max-h-80 overflow-auto rounded-xl border border-slate-700 bg-slate-900 p-3 shadow-xl z-20">
          <div className="space-y-2">
            {columns.map((column) => (
              <label key={column} className="flex items-center gap-2 text-xs text-slate-200">
                <input
                  type="checkbox"
                  checked={visibleSet.has(column)}
                  onChange={() => toggleColumn(column)}
                  className="rounded border-slate-600 bg-slate-800 text-cyan-500 focus:ring-cyan-500"
                />
                <span className="break-all">{column}</span>
              </label>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

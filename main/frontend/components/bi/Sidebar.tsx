import type { BIColumn } from '@/types/bi';

interface SidebarProps {
  filename: string;
  fields: BIColumn[];
  onRemove: () => void;
}

export default function Sidebar({ filename, fields, onRemove }: SidebarProps) {
  return (
    <aside className="w-full lg:w-80 rounded-2xl border border-slate-700/50 bg-slate-900 p-5">
      <div className="mb-6">
        <h2 className="text-sm font-semibold text-cyan-300" style={{ fontFamily: 'var(--font-display)' }}>
          MES Agentic BI for PPRS
        </h2>
      </div>

      <div className="mb-6">
        <p className="text-xs uppercase tracking-wide text-slate-400 mb-2">Data Source</p>
        <div className="rounded-xl border border-slate-700/50 bg-slate-800/60 p-3">
          <div className="flex items-start justify-between gap-2">
            <p className="text-sm text-slate-200 break-all">{filename}</p>
            <button
              type="button"
              onClick={onRemove}
              className="text-xs px-2 py-1 rounded-md border border-slate-600 text-slate-300 hover:text-slate-100 hover:border-slate-500"
            >
              Remove
            </button>
          </div>
        </div>
      </div>

      <div>
        <p className="text-xs uppercase tracking-wide text-slate-400 mb-2">Fields ({fields.length})</p>
        <ul className="space-y-1 max-h-[420px] overflow-auto pr-2">
          {fields.map((field) => (
            <li key={field.name} className="text-sm text-slate-300 flex items-start gap-2">
              <span className="mt-[7px] inline-block h-1.5 w-1.5 rounded-full bg-cyan-400" />
              <span className="break-all">{field.name}</span>
            </li>
          ))}
        </ul>
      </div>
    </aside>
  );
}

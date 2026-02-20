import { useMemo, useState } from 'react';

interface ClassificationPanelProps {
  detectedType: string;
  confidence: number;
  method: string;
  evidence: string[];
  options: string[];
  onConfirm: (selectedType: string) => void;
  onOverride: (selectedType: string) => void;
}

export default function ClassificationPanel({
  detectedType,
  confidence,
  method,
  evidence,
  options,
  onConfirm,
  onOverride,
}: ClassificationPanelProps) {
  const normalizedConfidence = Math.min(1, Math.max(0, confidence));
  const [selectedType, setSelectedType] = useState<string>(detectedType);

  const confidenceLabel = useMemo(() => {
    if (normalizedConfidence >= 0.8) return 'High confidence';
    if (normalizedConfidence >= 0.5) return 'Moderate confidence';
    return 'Low confidence';
  }, [normalizedConfidence]);

  const typeIcon = useMemo(() => {
    if (detectedType.includes('HPLC')) return '🧪';
    if (detectedType.includes('LOD')) return '⚖️';
    if (detectedType.includes('TITRATION')) return '🧫';
    if (detectedType.includes('IDENTITY')) return '🧬';
    return '📄';
  }, [detectedType]);

  return (
    <div className="rounded-xl bg-slate-800/50 border border-slate-700/50 p-5 space-y-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-wide text-slate-500">Deterministic Classification</p>
          <h3 className="text-lg font-semibold text-slate-100 mt-1 flex items-center gap-2">
            <span>{typeIcon}</span>
            <span>{detectedType}</span>
          </h3>
          <p className="text-sm text-slate-400 mt-1">Method: {method}</p>
          <p className="text-xs text-slate-500 mt-2">
            Hybrid rules + ML classifier detects your test type with transparent evidence.
          </p>
        </div>
        <span className="px-2.5 py-1 rounded-full text-xs font-medium border bg-blue-500/15 border-blue-500/25 text-blue-400">
          {confidenceLabel}
        </span>
      </div>

      <div>
        <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
          <span>Confidence</span>
          <span>{Math.round(normalizedConfidence * 100)}%</span>
        </div>
        <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
          <div className="h-full bg-blue-500" style={{ width: `${Math.round(normalizedConfidence * 100)}%` }} />
        </div>
      </div>

      <div>
        <p className="text-xs uppercase tracking-wide text-slate-500 mb-2">Override (optional)</p>
        <select
          value={selectedType}
          onChange={(e) => setSelectedType(e.target.value)}
          className="w-full rounded-lg border border-slate-600 bg-slate-900 text-slate-200 text-sm px-3 py-2"
        >
          {options.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </div>

      <div>
        <p className="text-xs uppercase tracking-wide text-slate-500 mb-2">Evidence</p>
        {evidence.length === 0 ? (
          <p className="text-sm text-slate-400">No evidence provided by the backend yet.</p>
        ) : (
          <ul className="space-y-1.5">
            {evidence.map((item, index) => (
              <li key={`${item}-${index}`} className="text-sm text-slate-300">
                • {item}
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="flex justify-end gap-2">
        <button
          onClick={() => onConfirm(detectedType)}
          className="px-4 py-2 rounded-lg text-sm font-medium border border-slate-600 text-slate-200 hover:bg-slate-700/40 transition-all"
        >
          Confirm
        </button>
        <button
          onClick={() => onOverride(selectedType)}
          disabled={selectedType === detectedType}
          className="px-4 py-2 rounded-lg text-sm font-medium bg-emerald-600 hover:bg-emerald-500 text-white transition-all"
        >
          Override
        </button>
      </div>
    </div>
  );
}

export type { ClassificationPanelProps };
import { useState } from 'react';

interface StageDetail {
  key: string;
  title: string;
  summary: string;
  bullets: string[];
}

interface PipelineStageDetailProps {
  stages: StageDetail[];
}

const STAGE_RESPONSIBILITY_TAGS: Record<string, { label: string; color: string }> = {
  classify: { label: 'ML', color: 'bg-blue-500/15 border-blue-500/25 text-blue-400' },
  template: { label: 'Template', color: 'bg-emerald-500/15 border-emerald-500/25 text-emerald-400' },
  extract: { label: 'AI', color: 'bg-violet-500/15 border-violet-500/25 text-violet-400' },
  augment: { label: 'RAG', color: 'bg-cyan-500/15 border-cyan-500/25 text-cyan-400' },
  merge: { label: 'ML + Human', color: 'bg-amber-500/15 border-amber-500/25 text-amber-400' },
  review: { label: 'HITL', color: 'bg-emerald-500/15 border-emerald-500/25 text-emerald-400' },
};

export default function PipelineStageDetail({ stages }: PipelineStageDetailProps) {
  const [openKey, setOpenKey] = useState<string | null>(stages[0]?.key ?? null);

  return (
    <div className="rounded-xl bg-slate-800/50 border border-slate-700/50 p-4 space-y-2">
      <p className="text-xs uppercase tracking-wide text-slate-500">Pipeline Reasoning</p>
      {stages.map((stage) => {
        const isOpen = openKey === stage.key;
        return (
          <div key={stage.key} className="rounded-lg border border-slate-700 overflow-hidden">
            <button
              onClick={() => setOpenKey(isOpen ? null : stage.key)}
              className="w-full px-3 py-2 flex items-center justify-between bg-slate-900/70 hover:bg-slate-900 text-left"
            >
              <div>
                <div className="flex items-center gap-2">
                  <p className="text-sm text-slate-100 font-medium">{stage.title}</p>
                  {STAGE_RESPONSIBILITY_TAGS[stage.key] && (
                    <span className={`inline-flex px-1.5 py-0.5 rounded text-[9px] font-medium border ${STAGE_RESPONSIBILITY_TAGS[stage.key].color}`}>
                      {STAGE_RESPONSIBILITY_TAGS[stage.key].label}
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-400">{stage.summary}</p>
              </div>
              <span className="text-slate-400 text-xs">{isOpen ? 'Hide' : 'Show'}</span>
            </button>
            {isOpen && (
              <div className="px-3 py-3 bg-slate-900/40">
                {stage.bullets.length === 0 ? (
                  <p className="text-sm text-slate-400">No stage details provided yet.</p>
                ) : (
                  <ul className="space-y-1.5">
                    {stage.bullets.map((bullet, index) => (
                      <li key={`${stage.key}-${index}`} className="text-sm text-slate-300">
                        • {bullet}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

export type { PipelineStageDetailProps, StageDetail };
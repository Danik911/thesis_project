import {
  DocumentTextIcon,
  CpuChipIcon,
  ChatBubbleLeftRightIcon,
  CheckCircleIcon,
  ArrowDownTrayIcon,
  CheckIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline';
import type { ComponentType, SVGProps } from 'react';

interface LIMSStepIndicatorProps {
  currentStatus: string;
}

type HeroIcon = ComponentType<SVGProps<SVGSVGElement>>;

interface Stage {
  key: string;
  label: string;
  subtitle: string;
  icon: HeroIcon;
}

const STAGES: Stage[] = [
  { key: 'CLASSIFY', label: 'Classify', subtitle: 'Deterministic ML', icon: DocumentTextIcon },
  { key: 'TEMPLATE', label: 'Template', subtitle: 'Method Contract', icon: CpuChipIcon },
  { key: 'EXTRACT', label: 'Extract', subtitle: 'Focused AI', icon: CpuChipIcon },
  { key: 'MERGE', label: 'Merge', subtitle: 'Provenance Track', icon: ChatBubbleLeftRightIcon },
  { key: 'REVIEW', label: 'Review', subtitle: 'Human Authority', icon: CheckCircleIcon },
  { key: 'EXPORT', label: 'Export', subtitle: 'Audit-Ready', icon: ArrowDownTrayIcon },
];

const STATUS_ORDER: Record<string, number> = {
  UPLOADING: 0,
  CLASSIFYING: 0,
  LOADING_TEMPLATE: 1,
  TEMPLATE_PREVIEW: 1,
  EXTRACTING: 2,
  GENERATING: 2,
  AUGMENTING: 2,
  MERGING: 3,
  PENDING_REVIEW: 4,
  REVIEW: 4,
  APPROVED: 4,
  EXPORTING: 5,
  DONE: 5,
  EXPORTED: 5,
  CLASSIFY: 0,
  TEMPLATE: 1,
  EXTRACT: 2,
  MERGE: 3,
  EXPORT: 5,
};

export default function LIMSStepIndicator({ currentStatus }: LIMSStepIndicatorProps) {
  const isFailed = currentStatus === 'FAILED';
  const activeIndex = isFailed ? -1 : (STATUS_ORDER[currentStatus] ?? -1);

  function getStageState(index: number): 'completed' | 'active' | 'failed' | 'pending' {
    if (isFailed) {
      return index === 0 ? 'failed' : 'pending';
    }
    if (index < activeIndex) return 'completed';
    if (index === activeIndex) return 'active';
    return 'pending';
  }

  const isProcessing = ['UPLOADING', 'CLASSIFYING', 'EXTRACTING', 'MERGING', 'EXPORTING'].includes(currentStatus);

  return (
    <div className="glass-panel py-5 px-6">
      <div className="flex items-center justify-between">
        {STAGES.map((stage, index) => {
          const state = getStageState(index);
          const isPending = state === 'pending';
          const isActive = state === 'active';
          const isCompleted = state === 'completed';

          const iconBubbleClasses: Record<string, string> = {
            completed:
              'bg-emerald-500/10 border-emerald-500/30 text-emerald-400 shadow-[0_0_10px_rgba(16,185,129,0.3)]',
            active:
              'bg-blue-500/10 border-blue-400/50 text-blue-400 shadow-[0_0_20px_rgba(59,130,246,0.5)] scale-110',
            failed:
              'bg-red-500/10 border-red-500/30 text-red-400 shadow-[0_0_15px_rgba(239,68,68,0.4)]',
            pending:
              'bg-slate-900 border-slate-700/60 text-slate-600',
          };

          const labelClasses: Record<string, string> = {
            completed: 'text-emerald-400',
            active: 'text-white',
            failed: 'text-red-400',
            pending: 'text-slate-600',
          };

          const subtitleClasses: Record<string, string> = {
            completed: 'text-emerald-400/50',
            active: 'text-blue-400/70',
            failed: 'text-red-400/50',
            pending: 'text-slate-700',
          };

          const IconComponent = isCompleted
            ? CheckIcon
            : state === 'failed'
              ? XCircleIcon
              : stage.icon;

          return (
            <div
              key={stage.key}
              className={`flex items-center flex-1 last:flex-none transition-all duration-500 ${
                isPending ? 'opacity-40 blur-[0.3px]' : 'opacity-100'
              }`}
            >
              {/* Stage icon + labels */}
              <div className="flex flex-col items-center gap-1.5">
                <div
                  className={`relative w-11 h-11 rounded-xl border flex items-center justify-center transition-all duration-500 ${iconBubbleClasses[state]}`}
                >
                  {/* Ping dot for active processing */}
                  {isActive && isProcessing && (
                    <span className="absolute -top-0.5 -right-0.5 flex h-2.5 w-2.5">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75" />
                      <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-blue-500" />
                    </span>
                  )}
                  <IconComponent className={`w-5 h-5 ${isActive && isProcessing ? 'animate-pulse' : ''}`} />
                </div>
                <span className={`text-[11px] font-display font-semibold whitespace-nowrap tracking-wide ${labelClasses[state]}`}>
                  {stage.label}
                </span>
                <span className={`text-[9px] whitespace-nowrap ${subtitleClasses[state]}`}>
                  {stage.subtitle}
                </span>
              </div>

              {/* Connector line */}
              {index < STAGES.length - 1 && (
                <div className="flex-1 mx-3 mb-7">
                  <div
                    className={`h-px transition-all duration-500 ${
                      index < activeIndex
                        ? 'bg-gradient-to-r from-emerald-500/50 to-emerald-500/20'
                        : index === activeIndex
                          ? 'bg-gradient-to-r from-blue-500/40 to-slate-700/50'
                          : 'bg-slate-800'
                    }`}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

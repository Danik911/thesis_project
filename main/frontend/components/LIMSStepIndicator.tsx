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
  icon: HeroIcon;
}

const STAGES: Stage[] = [
  { key: 'EXTRACTING', label: 'Extracting', icon: DocumentTextIcon },
  { key: 'GENERATING', label: 'Generating MDA', icon: CpuChipIcon },
  { key: 'PENDING_REVIEW', label: 'Review & Chat', icon: ChatBubbleLeftRightIcon },
  { key: 'APPROVED', label: 'Approved', icon: CheckCircleIcon },
  { key: 'EXPORTED', label: 'Exported', icon: ArrowDownTrayIcon },
];

const STATUS_ORDER: Record<string, number> = {
  EXTRACTING: 0,
  GENERATING: 1,
  PENDING_REVIEW: 2,
  APPROVED: 3,
  EXPORTED: 4,
};

export default function LIMSStepIndicator({ currentStatus }: LIMSStepIndicatorProps) {
  const isFailed = currentStatus === 'FAILED';
  const activeIndex = isFailed ? -1 : (STATUS_ORDER[currentStatus] ?? -1);

  function getStageState(index: number): 'completed' | 'active' | 'failed' | 'pending' {
    if (isFailed) {
      // FAILED: all stages render as pending except none is active;
      // the first stage shows as the failure point
      return index === 0 ? 'failed' : 'pending';
    }
    if (index < activeIndex) return 'completed';
    if (index === activeIndex) return 'active';
    return 'pending';
  }

  const shouldPulse = currentStatus === 'EXTRACTING' || currentStatus === 'GENERATING';

  return (
    <div className="rounded-xl bg-slate-800/50 border border-slate-700/50 py-4 px-4">
      <div className="flex items-center justify-between">
        {STAGES.map((stage, index) => {
          const state = getStageState(index);

          const circleClasses: Record<string, string> = {
            completed:
              'bg-emerald-500/15 border-emerald-500/25 text-emerald-400',
            active:
              'bg-blue-500/15 border-blue-500/40 text-blue-400 shadow-lg shadow-blue-500/10',
            failed:
              'bg-red-500/15 border-red-500/25 text-red-400',
            pending:
              'bg-slate-800 border-slate-700 text-slate-500',
          };

          const labelClasses: Record<string, string> = {
            completed: 'text-emerald-400',
            active: 'text-blue-400',
            failed: 'text-red-400',
            pending: 'text-slate-500',
          };

          const IconComponent = state === 'completed'
            ? CheckIcon
            : state === 'failed'
              ? XCircleIcon
              : stage.icon;

          const pulse = state === 'active' && shouldPulse;

          return (
            <div key={stage.key} className="flex items-center flex-1 last:flex-none">
              {/* Stage circle + label */}
              <div className="flex flex-col items-center gap-1.5">
                <div
                  className={`w-10 h-10 rounded-full border flex items-center justify-center transition-all ${circleClasses[state]} ${pulse ? 'animate-pulse' : ''}`}
                >
                  <IconComponent className="w-5 h-5" />
                </div>
                <span className={`text-xs font-medium whitespace-nowrap ${labelClasses[state]}`}>
                  {stage.label}
                </span>
              </div>

              {/* Connector line (not after last stage) */}
              {index < STAGES.length - 1 && (
                <div
                  className={`flex-1 h-px mx-3 mb-6 ${
                    index < activeIndex
                      ? 'bg-emerald-500/40'
                      : 'bg-slate-700'
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

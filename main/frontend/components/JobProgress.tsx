import {
  CheckCircleIcon,
  ClockIcon,
  DocumentTextIcon,
  TagIcon,
  UserIcon,
  LightBulbIcon,
  CpuChipIcon,
  CommandLineIcon,
  CheckIcon
} from '@heroicons/react/24/outline';

/**
 * Human-readable labels for workflow stages.
 * Maps backend stage identifiers to user-friendly text.
 */
const STAGE_LABELS: Record<string, string> = {
  queued: "Queued",
  ingestion: "Loading Document",
  categorization: "GAMP-5 Classification",
  hil_waiting: "Awaiting Human Approval",
  planning: "Planning Test Strategy",
  agent_execution: "Executing AI Agents",
  oq_generation: "Generating Test Cases",
  completion: "Finalizing Results"
};

/**
 * Stage icons for visual indicator
 */
const STAGE_ICONS: Record<string, any> = {
  queued: ClockIcon,
  ingestion: DocumentTextIcon,
  categorization: TagIcon,
  hil_waiting: UserIcon,
  planning: LightBulbIcon,
  agent_execution: CpuChipIcon,
  oq_generation: CommandLineIcon,
  completion: CheckIcon
};

/**
 * Ordered list of stages for the timeline
 */
const STAGE_ORDER = [
  'queued',
  'ingestion',
  'categorization',
  'hil_waiting',
  'planning',
  'agent_execution',
  'oq_generation',
  'completion'
];

interface JobProgressProps {
  status: string;
  logs: string[];
  startTime?: number | null;
  jobId?: string;
  // Backend-driven progress fields
  currentStage?: string | null;
  currentStageLabel?: string | null;
  progressPercentage?: number | null;
  // Persisted display progress - what the animation actually reached before navigation
  initialDisplayProgress?: number;
  // Callback to report current display progress to parent (for persistence)
  onProgressChange?: (progress: number) => void;
}

export default function JobProgress({
  status,
  logs,
  startTime,
  jobId,
  currentStage,
  currentStageLabel,
  progressPercentage,
  initialDisplayProgress = 0,
  onProgressChange
}: JobProgressProps) {
  // Determine the index of the current stage
  const currentStageIndex = currentStage ? STAGE_ORDER.indexOf(currentStage) : -1;

  // If status is COMPLETED, treat as if we are at the end
  const effectiveStageIndex = status === 'COMPLETED' ? STAGE_ORDER.length - 1 : currentStageIndex;

  // Determine progress bar color based on status
  const getStatusColor = (stageKey: string, index: number) => {
    if (status === 'FAILED' || status === 'REJECTED') {
      if (index === effectiveStageIndex) return 'text-red-500 border-red-500 shadow-[0_0_15px_rgba(239,68,68,0.4)]';
      if (index < effectiveStageIndex) return 'text-emerald-500 border-emerald-500'; // Completed stages still green
      return 'text-slate-600 border-slate-700';
    }
    if (index < effectiveStageIndex) return 'text-emerald-500 border-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.3)]';
    if (index === effectiveStageIndex) {
      if (stageKey === 'hil_waiting' && status === 'AWAITING_APPROVAL') return 'text-amber-500 border-amber-500 shadow-[0_0_20px_rgba(245,158,11,0.5)]';
      return 'text-blue-400 border-blue-400 shadow-[0_0_20px_rgba(59,130,246,0.6)]';
    }
    return 'text-slate-700 border-slate-800';
  };

  const getIconBg = (stageKey: string, index: number) => {
    if (status === 'FAILED' || status === 'REJECTED') {
      if (index === effectiveStageIndex) return 'bg-red-500/10';
      if (index < effectiveStageIndex) return 'bg-emerald-500/10';
      return 'bg-slate-900';
    }
    if (index < effectiveStageIndex) return 'bg-emerald-500/10';
    if (index === effectiveStageIndex) {
      if (stageKey === 'hil_waiting' && status === 'AWAITING_APPROVAL') return 'bg-amber-500/10';
      return 'bg-blue-500/10';
    }
    return 'bg-slate-900';
  };

  return (
    <div className="w-full">
      {/* Main Status Panel */}
      <div className="glass-panel p-6 border-blue-500/10 bg-slate-900/40 backdrop-blur-xl">
        <div className="flex justify-between items-center mb-8 pb-4 border-b border-slate-800/50">
          <h3 className="text-lg font-display font-medium text-slate-200 flex items-center gap-3">
            <span className="relative flex h-3 w-3">
              {(status === 'PROCESSING' || status === 'AWAITING_APPROVAL') && (
                <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${status === 'AWAITING_APPROVAL' ? 'bg-amber-400' : 'bg-blue-400'}`}></span>
              )}
              <span className={`relative inline-flex rounded-full h-3 w-3 ${status === 'COMPLETED' ? 'bg-emerald-500' :
                status === 'FAILED' || status === 'REJECTED' ? 'bg-red-500' :
                  status === 'AWAITING_APPROVAL' ? 'bg-amber-500' :
                    'bg-blue-500'
                }`}></span>
            </span>
            <span className="tracking-wide text-sm uppercase text-slate-400">Status</span>
            <span className={`font-mono font-bold ${status === 'COMPLETED' ? 'text-emerald-400' :
              status === 'FAILED' || status === 'REJECTED' ? 'text-red-400' :
                status === 'AWAITING_APPROVAL' ? 'text-amber-400' :
                  'text-blue-400'
              }`}>{status}</span>
          </h3>
          {progressPercentage !== null && (
            <div className="flex items-center gap-2">
              <div className="h-1.5 w-24 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500 transition-all duration-500 ease-out"
                  style={{ width: `${progressPercentage}%` }}
                ></div>
              </div>
              <span className="text-sm font-mono text-blue-400 font-bold">
                {progressPercentage}%
              </span>
            </div>
          )}
        </div>

        {/* Stage Timeline */}
        <div className="relative pl-2">
          {/* Vertical Line */}
          <div className="absolute left-8 top-4 bottom-4 w-px bg-gradient-to-b from-blue-500/50 via-slate-800 to-slate-800" aria-hidden="true"></div>

          <div className="space-y-8 relative">
            {STAGE_ORDER.map((stageKey, index) => {
              // Use CheckCircleIcon as generic fallback if icon missing
              const Icon = STAGE_ICONS[stageKey] || CheckCircleIcon;
              const isCompleted = index < effectiveStageIndex;
              const isCurrent = index === effectiveStageIndex;
              const isPending = index > effectiveStageIndex;
              const label = STAGE_LABELS[stageKey];

              return (
                <div key={stageKey} className={`group flex items-start gap-6 transition-all duration-500 ${isPending ? 'opacity-40 blur-[0.5px]' : 'opacity-100'}`}>
                  {/* Icon Bubble */}
                  <div className={`relative z-10 flex items-center justify-center w-12 h-12 rounded-xl border transition-all duration-500 ${getStatusColor(stageKey, index)} ${getIconBg(stageKey, index)} ${isCurrent ? 'scale-110' : 'scale-100'}`}>
                    {isCompleted ? (
                      <CheckIcon className="w-6 h-6" />
                    ) : (
                      <Icon className={`w-6 h-6 ${isCurrent && status === 'PROCESSING' ? 'animate-pulse' : ''}`} />
                    )}
                  </div>

                  {/* Content */}
                  <div className="flex-1 pt-2">
                    <div className="flex justify-between items-center">
                      <h4 className={`text-lg font-display font-medium transition-colors ${isCurrent ? 'text-white' : 'text-slate-400'}`}>
                        {label}
                      </h4>
                      {isCurrent && (status === 'PROCESSING' || status === 'AWAITING_APPROVAL') && (
                        <span className="text-xs font-mono text-blue-400 animate-pulse border border-blue-500/30 px-2 py-0.5 rounded bg-blue-500/10">
                          {stageKey === 'agent_execution' ? 'PROCESSING' :
                            stageKey === 'hil_waiting' ? 'ACTION REQUIRED' : 'IN PROGRESS'}
                        </span>
                      )}
                    </div>

                    {/* Contextual Description / Indeterminate Bar for Active Stage */}
                    {isCurrent && status !== 'FAILED' && status !== 'REJECTED' && (
                      <div className="mt-3 animate-fade-in">
                        {stageKey === 'agent_execution' && (
                          <div className="space-y-3">
                            <p className="text-sm text-slate-400 font-light">
                              AI agents are analyzing the document and generating test scenarios. This typically takes 4-6 minutes.
                            </p>
                            {/* Indeterminate Loading Bar */}
                            <div className="w-full h-1 bg-slate-800 rounded-full overflow-hidden">
                              <div className="h-full bg-blue-400 w-1/3 animate-[shimmer_2s_infinite_linear] bg-[linear-gradient(90deg,transparent,rgba(96,165,250,0.8),transparent)]"></div>
                            </div>
                          </div>
                        )}
                        {stageKey === 'hil_waiting' && (
                          <p className="text-sm text-amber-400 border-l-2 border-amber-500 pl-3">
                            Please review the GAMP-5 categorization in the modal to proceed.
                          </p>
                        )}
                        {stageKey === 'oq_generation' && (
                          <div className="space-y-3">
                            <p className="text-sm text-slate-400 font-light">
                              Formatting final test cases...
                            </p>
                            <div className="w-full h-1 bg-slate-800 rounded-full overflow-hidden">
                              <div className="h-full bg-blue-400 w-1/3 animate-[shimmer_1.5s_infinite_linear] bg-[linear-gradient(90deg,transparent,rgba(96,165,250,0.8),transparent)]"></div>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Completion Message */}
        {status === 'COMPLETED' && (
          <div className="mt-8 p-4 bg-emerald-500/5 border border-emerald-500/20 rounded-xl flex items-center gap-4 animate-fade-in">
            <div className="p-2 bg-emerald-500/10 rounded-lg">
              <CheckCircleIcon className="w-6 h-6 text-emerald-400" />
            </div>
            <div>
              <h4 className="text-base font-medium text-emerald-400">Generation Complete</h4>
              <p className="text-sm text-emerald-400/70">Your test suite is ready for review.</p>
            </div>
          </div>
        )}

        {/* Failure Message */}
        {(status === 'FAILED' || status === 'REJECTED') && (
          <div className="mt-8 p-4 bg-red-500/5 border border-red-500/20 rounded-xl animate-fade-in">
            <h4 className="text-base font-medium text-red-400 flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-red-500"></span>
              {status === 'REJECTED' ? 'Job Rejected' : 'Generation Failed'}
            </h4>
            <p className="text-sm text-red-400/70 mt-2 font-mono bg-red-950/30 p-2 rounded">
              {logs[logs.length - 1] || 'An error occurred during processing.'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}


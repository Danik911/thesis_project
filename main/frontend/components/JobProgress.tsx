import { useEffect, useState, useRef } from 'react';
import InteractiveQuiz from './quiz/InteractiveQuiz';

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
const STAGE_ICONS: Record<string, string> = {
  queued: "clock",
  ingestion: "document",
  categorization: "tag",
  hil_waiting: "user",
  planning: "lightbulb",
  agent_execution: "cpu",
  oq_generation: "code",
  completion: "check"
};

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
  // Target progress from backend (what we're animating toward)
  // Initialize from parent's persisted value so we don't regress below it
  const [targetProgress, setTargetProgress] = useState(initialDisplayProgress);
  // Displayed progress (what the user sees, animates smoothly)
  // Initialize from parent's persisted value to prevent reset on remount
  const [displayProgress, setDisplayProgress] = useState(initialDisplayProgress);
  // Track if we've initialized - on first render with progress, jump to that value
  const hasInitialized = useRef(initialDisplayProgress > 0);

  // Update target when backend progress changes
  useEffect(() => {
    let newTarget = 0;

    // Priority 1: Use backend-provided progress percentage if available
    if (progressPercentage !== null && progressPercentage !== undefined) {
      newTarget = progressPercentage;
    } else {
      // Priority 2: Fall back to status-based progress
      if (status === 'PENDING') {
        newTarget = 5;
      } else if (status === 'PROCESSING') {
        newTarget = 10;
      } else if (status === 'AWAITING_APPROVAL') {
        newTarget = 30;
      } else if (status === 'APPROVED') {
        newTarget = 35;
      } else if (status === 'COMPLETED') {
        newTarget = 100;
      } else if (status === 'FAILED' || status === 'REJECTED') {
        newTarget = 100;
      }
    }

    // On first render with progress > 0, jump immediately (no animation from 0)
    // This handles navigation back to the page with existing progress
    if (!hasInitialized.current && newTarget > 0) {
      hasInitialized.current = true;
      setTargetProgress(newTarget);
      setDisplayProgress(newTarget);
      return;
    }

    // After initialization, only update target (never decrease)
    // Animation effect will handle smooth transitions
    setTargetProgress(prev => Math.max(prev, newTarget));
  }, [status, progressPercentage]);

  // Very slow animation: bar grows steadily over minutes, not seconds
  // Designed for ~6-9 minute workflows
  useEffect(() => {
    // If we're already at or past target, no animation needed
    if (displayProgress >= targetProgress) {
      return;
    }

    // Slow growth calibrated for 15-minute workflows
    // 0.022% per 200ms = 100% in ~15 minutes
    const baseInterval = 200; // ms between increments
    const increment = 0.022; // 100% in 15 minutes

    const animationInterval = setInterval(() => {
      setDisplayProgress(prev => {
        const next = prev + increment;
        if (next >= targetProgress) {
          clearInterval(animationInterval);
          return targetProgress;
        }
        return next;
      });
    }, baseInterval);

    return () => clearInterval(animationInterval);
  }, [targetProgress, displayProgress]);

  // Report display progress changes to parent for persistence
  // This allows parent to save what the user actually saw
  useEffect(() => {
    if (onProgressChange && displayProgress > 0) {
      onProgressChange(displayProgress);
    }
  }, [displayProgress, onProgressChange]);

  // Determine stage label to display
  const stageLabel = currentStageLabel || (currentStage ? STAGE_LABELS[currentStage] : null);

  // Determine progress bar color based on status
  const getProgressBarColor = () => {
    if (status === 'FAILED' || status === 'REJECTED') return 'bg-red-500';
    if (status === 'COMPLETED') return 'bg-emerald-500';
    if (status === 'AWAITING_APPROVAL') return 'bg-amber-500';
    return 'bg-blue-600';
  };

  // Determine status indicator color
  const getStatusIndicatorColor = () => {
    if (status === 'COMPLETED') return 'bg-emerald-500';
    if (status === 'FAILED' || status === 'REJECTED') return 'bg-red-500';
    if (status === 'AWAITING_APPROVAL') return 'bg-amber-500';
    return 'bg-blue-500';
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      {/* Status Bar */}
      <div className="glass-panel p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-slate-200 flex items-center gap-2">
            <span className="relative flex h-3 w-3">
              {(status === 'PROCESSING' || status === 'AWAITING_APPROVAL') && (
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
              )}
              <span className={`relative inline-flex rounded-full h-3 w-3 ${getStatusIndicatorColor()}`}></span>
            </span>
            Generation Status: <span className="text-blue-400 font-mono">{status}</span>
          </h3>
          <span className="text-sm font-mono text-slate-400">{Math.round(displayProgress)}%</span>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-slate-800 rounded-full h-2.5 overflow-hidden">
          <div
            className={`h-2.5 rounded-full transition-all duration-500 ease-out ${getProgressBarColor()} ${status === 'PROCESSING' ? 'relative overflow-hidden' : ''}`}
            style={{ width: `${displayProgress}%` }}
          >
            {status === 'PROCESSING' && (
              <div className="absolute top-0 left-0 bottom-0 right-0 bg-[linear-gradient(45deg,rgba(255,255,255,0.15)_25%,transparent_25%,transparent_50%,rgba(255,255,255,0.15)_50%,rgba(255,255,255,0.15)_75%,transparent_75%,transparent)] bg-[length:1rem_1rem] animate-[progress-bar-stripes_1s_linear_infinite]"></div>
            )}
          </div>
        </div>

        {/* Stage Label - Detailed Display */}
        {stageLabel && (status === 'PROCESSING' || status === 'AWAITING_APPROVAL' || status === 'APPROVED') && (
          <div className="mt-4 flex items-center gap-2">
            <span className="text-sm text-slate-400">Current Stage:</span>
            <span className="text-sm font-medium text-blue-400 bg-slate-800/50 px-3 py-1 rounded-full">
              {stageLabel}
            </span>
            {status === 'AWAITING_APPROVAL' && (
              <span className="text-xs text-amber-400 ml-2 animate-pulse">
                Waiting for human review...
              </span>
            )}
          </div>
        )}

        {/* Completion Message */}
        {status === 'COMPLETED' && (
          <div className="mt-4 flex items-center gap-2">
            <span className="text-sm text-emerald-400 font-medium">
              Test suite generation complete!
            </span>
          </div>
        )}

        {/* Failure Message */}
        {(status === 'FAILED' || status === 'REJECTED') && (
          <div className="mt-4 flex items-center gap-2">
            <span className="text-sm text-red-400 font-medium">
              {status === 'REJECTED' ? 'Job was rejected or timed out' : 'Generation failed'}
            </span>
          </div>
        )}
      </div>

      {/* Interactive Compliance Quiz */}
      <div className="mt-8">
        <InteractiveQuiz />
      </div>
    </div>
  );
}

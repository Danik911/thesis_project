import { useEffect, useState } from 'react';
import InteractiveQuiz from './quiz/InteractiveQuiz';

interface JobProgressProps {
  status: string;
  logs: string[];
  startTime?: number | null;
  jobId?: string;
}

export default function JobProgress({ status, logs, startTime, jobId }: JobProgressProps) {
  const [progress, setProgress] = useState(0);

  // Simulate progress based on status or logs
  useEffect(() => {
    let interval: NodeJS.Timeout;

    if (status === 'PENDING') {
      setProgress(10);
    } else if (status === 'PROCESSING') {
      // Calculate initial progress based on elapsed time if startTime is available
      let initialProgress = 10;
      if (startTime) {
        const elapsedSeconds = (Date.now() - startTime) / 1000;
        // Target: 90% in 480 seconds (8 mins)
        // Rate: (90 - 10) / 480 = ~0.167% per second
        const calculatedProgress = 10 + (elapsedSeconds * 0.167);
        initialProgress = Math.min(90, Math.max(10, calculatedProgress));
      }

      setProgress(initialProgress);

      // Gradually increase progress up to 90%
      // Workflow takes 6-9 minutes (360-540 seconds)
      // We want to reach 90% in about 8 minutes (480 seconds)
      // Update every 1 second (1000ms)
      interval = setInterval(() => {
        setProgress(prev => {
          // Cap at 90% until actually completed
          if (prev >= 90) return 90;

          // Calculate increment to reach 90% in ~480 seconds
          // (90 - 10) / 480 = ~0.16 per second
          // Add some randomness to make it look natural
          const increment = 0.1 + Math.random() * 0.1;
          return Math.min(90, prev + increment);
        });
      }, 1000);
    } else if (status === 'COMPLETED') {
      setProgress(100);
    } else if (status === 'FAILED') {
      setProgress(100);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [status, startTime]);

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      {/* Status Bar */}
      <div className="glass-panel p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-slate-200 flex items-center gap-2">
            <span className="relative flex h-3 w-3">
              {status === 'PROCESSING' && (
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
              )}
              <span className={`relative inline-flex rounded-full h-3 w-3 ${status === 'COMPLETED' ? 'bg-emerald-500' :
                status === 'FAILED' ? 'bg-red-500' :
                  'bg-blue-500'
                }`}></span>
            </span>
            Generation Status: <span className="text-blue-400 font-mono">{status}</span>
          </h3>
          <span className="text-sm font-mono text-slate-400">{Math.round(progress)}%</span>
        </div>

        <div className="w-full bg-slate-800 rounded-full h-2.5 overflow-hidden">
          <div
            className={`h-2.5 rounded-full transition-all duration-1000 ease-out ${status === 'FAILED' ? 'bg-red-500' :
              status === 'COMPLETED' ? 'bg-emerald-500' :
                'bg-blue-600 relative overflow-hidden'
              }`}
            style={{ width: `${progress}%` }}
          >
            {status === 'PROCESSING' && (
              <div className="absolute top-0 left-0 bottom-0 right-0 bg-[linear-gradient(45deg,rgba(255,255,255,0.15)_25%,transparent_25%,transparent_50%,rgba(255,255,255,0.15)_50%,rgba(255,255,255,0.15)_75%,transparent_75%,transparent)] bg-[length:1rem_1rem] animate-[progress-bar-stripes_1s_linear_infinite]"></div>
            )}
          </div>
        </div>
      </div>

      {/* Interactive Compliance Quiz */}
      <div className="mt-8">
        <InteractiveQuiz />
      </div>
    </div>
  );
}

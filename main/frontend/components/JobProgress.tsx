import { useEffect, useState } from 'react';

interface JobProgressProps {
  status: string;
  logs: string[];
}

export default function JobProgress({ status, logs }: JobProgressProps) {
  const [progress, setProgress] = useState(0);

  // Simulate progress based on status or logs
  useEffect(() => {
    if (status === 'PENDING') setProgress(10);
    else if (status === 'PROCESSING') setProgress(45);
    else if (status === 'COMPLETED') setProgress(100);
    else if (status === 'FAILED') setProgress(100);
  }, [status]);

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
              <span className={`relative inline-flex rounded-full h-3 w-3 ${
                status === 'COMPLETED' ? 'bg-emerald-500' : 
                status === 'FAILED' ? 'bg-red-500' : 
                'bg-blue-500'
              }`}></span>
            </span>
            Generation Status: <span className="text-blue-400 font-mono">{status}</span>
          </h3>
          <span className="text-sm font-mono text-slate-400">{progress}%</span>
        </div>
        
        <div className="w-full bg-slate-800 rounded-full h-2.5 overflow-hidden">
          <div 
            className={`h-2.5 rounded-full transition-all duration-1000 ease-out ${
              status === 'FAILED' ? 'bg-red-500' : 
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

      {/* Logs Console */}
      <div className="glass-panel p-0 overflow-hidden flex flex-col h-96">
        <div className="bg-slate-900/80 px-4 py-2 border-b border-slate-700/50 flex justify-between items-center">
          <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">System Logs</span>
          <div className="flex gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-slate-700"></div>
            <div className="w-2.5 h-2.5 rounded-full bg-slate-700"></div>
            <div className="w-2.5 h-2.5 rounded-full bg-slate-700"></div>
          </div>
        </div>
        <div className="flex-1 p-4 overflow-y-auto font-mono text-sm space-y-1 custom-scrollbar bg-slate-950/50">
          {logs.length === 0 ? (
            <div className="text-slate-600 italic">Waiting for process to start...</div>
          ) : (
            logs.map((log, index) => (
              <div key={index} className="flex gap-3 text-slate-300 animate-fade-in">
                <span className="text-slate-600 select-none">{(index + 1).toString().padStart(3, '0')}</span>
                <span className={
                  log.includes('ERROR') ? 'text-red-400' :
                  log.includes('SUCCESS') ? 'text-emerald-400' :
                  log.includes('WARNING') ? 'text-amber-400' :
                  'text-slate-300'
                }>
                  <span className="opacity-50 mr-2">[{new Date().toLocaleTimeString()}]</span>
                  {log}
                </span>
              </div>
            ))
          )}
          {status === 'PROCESSING' && (
            <div className="flex gap-3 text-blue-400 animate-pulse">
              <span className="text-slate-600 select-none">...</span>
              <span>_</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

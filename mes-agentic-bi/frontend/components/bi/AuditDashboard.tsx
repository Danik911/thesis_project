import LangfuseTraceDashboard from '@/components/bi/LangfuseTraceDashboard';

interface AuditDashboardProps {
  sessionId: string;
  traceIds: string[];
}

export default function AuditDashboard({ sessionId, traceIds }: AuditDashboardProps) {
  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-cyan-900/50 bg-slate-900/70 p-4">
        <h3 className="text-base font-semibold text-cyan-300">ALCOA+ Audit Summary</h3>
        <div className="mt-3 flex flex-wrap gap-2 text-xs">
          <span className="rounded-md border border-cyan-700/50 bg-cyan-500/15 px-2 py-1 text-cyan-300">Attributable</span>
          <span className="rounded-md border border-cyan-700/50 bg-cyan-500/15 px-2 py-1 text-cyan-300">Contemporaneous</span>
          <span className="rounded-md border border-cyan-700/50 bg-cyan-500/15 px-2 py-1 text-cyan-300">Original (SHA-512)</span>
          <span className="rounded-md border border-cyan-700/50 bg-cyan-500/15 px-2 py-1 text-cyan-300">Accurate</span>
          <span className="rounded-md border border-cyan-700/50 bg-cyan-500/15 px-2 py-1 text-cyan-300">Complete</span>
          <span className="rounded-md border border-cyan-700/50 bg-cyan-500/15 px-2 py-1 text-cyan-300">Enduring</span>
          <span className="rounded-md border border-cyan-700/50 bg-cyan-500/15 px-2 py-1 text-cyan-300">Available</span>
        </div>
        <p className="mt-3 text-xs text-slate-400">
          Session <span className="text-cyan-300">{sessionId}</span> • Captured trace links <span className="text-teal-300">{traceIds.length}</span>
        </p>
      </div>

      <LangfuseTraceDashboard sessionId={sessionId} traceIds={traceIds} />
    </div>
  );
}

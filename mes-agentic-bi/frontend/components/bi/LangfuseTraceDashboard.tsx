import { useEffect, useMemo, useState } from 'react';

interface LangfuseObservation {
  id: string;
  name?: string | null;
  type: string;
  status?: string | null;
  startTime?: string | null;
  endTime?: string | null;
  model?: string | null;
  parentObservationId?: string | null;
  totalCost?: number | string | null;
  inputUsage?: number | string | null;
  outputUsage?: number | string | null;
  totalUsage?: number | string | null;
  metadata?: Record<string, unknown> | string | null;
}

interface LangfuseTracePayload {
  id: string;
  timestamp?: string;
  name?: string | null;
  userId?: string | null;
  environment?: string | null;
  htmlPath?: string;
  totalCost?: number | null;
  latency?: number | null;
  observations?: LangfuseObservation[];
}

interface SummaryMetric {
  date: string;
  countTraces: number;
  totalCost: number;
  usage: Array<{ model: string; totalUsage: number }>;
}

interface Node {
  observation: LangfuseObservation;
  children: Node[];
}

interface Props {
  sessionId: string;
  traceIds: string[];
}

const toNumber = (value: unknown): number => {
  if (value === null || value === undefined) return 0;
  const parsed = Number(typeof value === 'string' ? value.trim() : value);
  return Number.isFinite(parsed) ? parsed : 0;
};

const fmtMs = (start?: string | null, end?: string | null): string => {
  if (!start) return 'N/A';
  const s = new Date(start).getTime();
  const e = end ? new Date(end).getTime() : s;
  if (Number.isNaN(s) || Number.isNaN(e)) return 'N/A';
  const diff = Math.max(0, e - s);
  if (diff >= 1000) return `${(diff / 1000).toFixed(2)}s`;
  return `${diff}ms`;
};

const buildTree = (observations: LangfuseObservation[]): Node[] => {
  const byId = new Map<string, Node>();
  const roots: Node[] = [];

  observations.forEach((obs) => byId.set(obs.id, { observation: obs, children: [] }));
  observations.forEach((obs) => {
    const node = byId.get(obs.id);
    if (!node) return;
    const parentId = obs.parentObservationId;
    if (parentId && byId.has(parentId)) {
      byId.get(parentId)!.children.push(node);
      return;
    }
    roots.push(node);
  });

  return roots;
};

function Tree({ nodes, depth = 0 }: { nodes: Node[]; depth?: number }) {
  return (
    <div className="space-y-2">
      {nodes.map((node) => (
        <div key={node.observation.id} className="rounded-lg border border-cyan-900/50 bg-slate-900/60 p-2">
          <div className="flex items-center justify-between gap-2">
            <div className="min-w-0 text-sm text-cyan-100">
              <span className="text-cyan-400">{depth > 0 ? '↳ ' : ''}</span>
              {node.observation.name || 'Unnamed observation'}
            </div>
            <span className="text-xs text-teal-300">{fmtMs(node.observation.startTime, node.observation.endTime)}</span>
          </div>
          <div className="mt-1 text-xs text-slate-400">
            {node.observation.type} • {node.observation.status || 'unknown'}
          </div>
          {node.children.length > 0 && (
            <div className="mt-2 ml-3 border-l border-cyan-900/50 pl-2">
              <Tree nodes={node.children} depth={depth + 1} />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

export default function LangfuseTraceDashboard({ sessionId, traceIds }: Props) {
  const [selectedTraceId, setSelectedTraceId] = useState<string | null>(traceIds.at(-1) ?? null);
  const [trace, setTrace] = useState<LangfuseTracePayload | null>(null);
  const [summary, setSummary] = useState<SummaryMetric[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedObservation, setSelectedObservation] = useState<LangfuseObservation | null>(null);

  useEffect(() => {
    setSelectedTraceId(traceIds.at(-1) ?? null);
  }, [traceIds]);

  useEffect(() => {
    let active = true;
    const fetchSummary = async () => {
      try {
        const res = await fetch('/api/langfuse/summary');
        const payload = await res.json();
        if (!active) return;
        if (!res.ok || !payload.success) {
          throw new Error(payload.details || payload.error || 'Failed to load summary');
        }
        setSummary(payload.data || []);
      } catch (e) {
        if (!active) return;
        setError(e instanceof Error ? e.message : 'Failed to load summary');
      }
    };

    fetchSummary();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!selectedTraceId) {
      setTrace(null);
      return;
    }

    let active = true;
    const fetchTrace = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`/api/langfuse/trace?traceId=${encodeURIComponent(selectedTraceId)}`);
        const payload = await res.json();
        if (!active) return;
        if (!res.ok || !payload.success) {
          throw new Error(payload.details || payload.error || 'Failed to load trace');
        }
        setTrace(payload.data as LangfuseTracePayload);
      } catch (e) {
        if (!active) return;
        setError(e instanceof Error ? e.message : 'Failed to load trace');
      } finally {
        if (active) setLoading(false);
      }
    };

    fetchTrace();
    return () => {
      active = false;
    };
  }, [selectedTraceId]);

  const observations = trace?.observations || [];
  const tree = useMemo(() => buildTree(observations), [observations]);

  const tokens = useMemo(
    () =>
      observations.reduce(
        (acc, observation) => {
          acc.input += toNumber(observation.inputUsage);
          acc.output += toNumber(observation.outputUsage);
          acc.total += toNumber(observation.totalUsage) || toNumber(observation.inputUsage) + toNumber(observation.outputUsage);
          acc.cost += toNumber(observation.totalCost);
          return acc;
        },
        { input: 0, output: 0, total: 0, cost: 0 }
      ),
    [observations]
  );

  const sevenDayTraces = summary.reduce((acc, item) => acc + item.countTraces, 0);
  const sevenDayCost = summary.reduce((acc, item) => acc + item.totalCost, 0);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <div className="rounded-xl border border-cyan-900/50 bg-slate-900/70 p-3">
          <div className="text-xs text-slate-400">7d Traces</div>
          <div className="mt-1 text-xl font-semibold text-cyan-300">{sevenDayTraces}</div>
        </div>
        <div className="rounded-xl border border-cyan-900/50 bg-slate-900/70 p-3">
          <div className="text-xs text-slate-400">7d Cost</div>
          <div className="mt-1 text-xl font-semibold text-cyan-300">${sevenDayCost.toFixed(4)}</div>
        </div>
        <div className="rounded-xl border border-cyan-900/50 bg-slate-900/70 p-3">
          <div className="text-xs text-slate-400">Trace Tokens</div>
          <div className="mt-1 text-xl font-semibold text-teal-300">{Math.round(tokens.total)}</div>
        </div>
        <div className="rounded-xl border border-cyan-900/50 bg-slate-900/70 p-3">
          <div className="text-xs text-slate-400">Observations</div>
          <div className="mt-1 text-xl font-semibold text-teal-300">{observations.length}</div>
        </div>
      </div>

      <div className="rounded-xl border border-cyan-900/50 bg-slate-900/70 p-4">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <label className="text-xs text-slate-400">Session</label>
          <span className="rounded-md bg-cyan-500/15 px-2 py-1 text-xs text-cyan-300">{sessionId}</span>
          <label className="ml-2 text-xs text-slate-400">Trace</label>
          <select
            value={selectedTraceId ?? ''}
            onChange={(e) => setSelectedTraceId(e.target.value || null)}
            className="rounded-md border border-cyan-900/60 bg-slate-950 px-2 py-1 text-xs text-slate-200"
          >
            <option value="">No trace</option>
            {traceIds.map((traceId) => (
              <option key={traceId} value={traceId}>
                {traceId}
              </option>
            ))}
          </select>
          {trace?.id && (
            <a
              href={`${process.env.NEXT_PUBLIC_LANGFUSE_HOST || 'https://cloud.langfuse.com'}/trace/${trace.id}`}
              target="_blank"
              rel="noreferrer"
              className="ml-auto inline-flex items-center gap-1 rounded-md border border-teal-600/50 px-2 py-1 text-xs text-teal-300 hover:bg-teal-500/10"
            >
              ↗ Open in Langfuse
            </a>
          )}
        </div>

        {loading && <p className="text-sm text-slate-400">Loading trace…</p>}
        {error && <p className="text-sm text-rose-300">{error}</p>}

        {!loading && !error && (
          <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
            <div>
              <h4 className="mb-2 text-sm font-semibold text-cyan-300">Observation Tree</h4>
              <Tree nodes={tree} />
            </div>
            <div>
              <h4 className="mb-2 text-sm font-semibold text-cyan-300">Timeline</h4>
              <div className="space-y-2">
                {observations.map((observation) => (
                  <div key={observation.id} className="rounded-lg border border-cyan-900/50 bg-slate-950/70 p-2">
                    <div className="text-sm text-slate-200">{observation.name || observation.type}</div>
                    <div className="text-xs text-slate-400">
                      {observation.startTime || '—'} → {observation.endTime || '—'} ({fmtMs(observation.startTime, observation.endTime)})
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="rounded-xl border border-cyan-900/50 bg-slate-900/70 p-4">
        <h4 className="mb-2 text-sm font-semibold text-cyan-300">Observations Table</h4>
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-xs text-slate-200">
            <thead className="text-slate-400">
              <tr>
                <th className="px-2 py-1">Name</th>
                <th className="px-2 py-1">Type</th>
                <th className="px-2 py-1">Status</th>
                <th className="px-2 py-1">Duration</th>
                <th className="px-2 py-1">Cost</th>
              </tr>
            </thead>
            <tbody>
              {observations.map((observation) => (
                <tr
                  key={observation.id}
                  className="cursor-pointer border-t border-cyan-950/60 hover:bg-cyan-500/5"
                  onClick={() => setSelectedObservation(observation)}
                >
                  <td className="px-2 py-1">{observation.name || 'Unnamed observation'}</td>
                  <td className="px-2 py-1">{observation.type}</td>
                  <td className="px-2 py-1">{observation.status || 'unknown'}</td>
                  <td className="px-2 py-1">{fmtMs(observation.startTime, observation.endTime)}</td>
                  <td className="px-2 py-1">${toNumber(observation.totalCost).toFixed(6)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {selectedObservation && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div className="w-full max-w-2xl rounded-2xl border border-cyan-900/50 bg-slate-900 p-4 text-slate-200">
            <div className="mb-3 flex items-center justify-between">
              <h4 className="text-sm font-semibold text-cyan-300">Observation Details</h4>
              <button
                type="button"
                onClick={() => setSelectedObservation(null)}
                className="rounded-md border border-slate-700 px-2 py-1 text-xs text-slate-300 hover:border-slate-500"
              >
                Close
              </button>
            </div>
            <pre className="max-h-[60vh] overflow-auto rounded-lg bg-slate-950 p-3 text-xs text-teal-200">
              {JSON.stringify(selectedObservation, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}

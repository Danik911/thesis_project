import { Fragment, useEffect, useMemo, useState } from 'react';
import { Dialog, DialogPanel, DialogTitle, Transition, TransitionChild } from '@headlessui/react';
import { XMarkIcon, ArrowsPointingOutIcon } from '@heroicons/react/24/outline';
import { useAuth } from '@clerk/nextjs';
import { authenticatedFetch } from '@/lib/authenticatedFetch';

interface LangfuseUsage {
  inputTokens?: number | string | null;
  outputTokens?: number | string | null;
  totalTokens?: number | string | null;
}

interface LangfuseUsageDetails {
  input?: number | string | null;
  output?: number | string | null;
  total?: number | string | null;
}

interface LangfuseObservation {
  id: string;
  name?: string | null;
  type: string;
  startTime?: string | null;
  endTime?: string | null;
  level?: string | null;
  status?: string | null;
  model?: string | null;
  parentObservationId?: string | null;
  metadata?: Record<string, unknown> | string | null;
  usage?: LangfuseUsage | null;
  usageDetails?: LangfuseUsageDetails | null;
  totalCost?: number | string | null;
  inputUsage?: number | string | null;
  outputUsage?: number | string | null;
  totalUsage?: number | string | null;
}

interface LangfuseTracePayload {
  id: string;
  name?: string | null;
  timestamp?: string;
  userId?: string | null;
  environment?: string | null;
  tags?: string[] | null;
  totalCost?: number | null;
  latency?: number | null;
  htmlPath?: string;
  observations?: LangfuseObservation[];
}

interface ApiSuccess {
  success: true;
  data: LangfuseTracePayload;
  metadata?: {
    fetchedAt: string;
    traceId: string;
    cacheHit: boolean;
  };
}

interface ApiError {
  success: false;
  error: string;
  details?: string;
}

type ApiResponse = ApiSuccess | ApiError;

interface LangfuseTraceDashboardProps {
  traceId?: string | null;
  traceUrl?: string | null;
  jobId: string;
}

interface ObservationNode {
  observation: LangfuseObservation;
  children: ObservationNode[];
}

const numberFromUnknown = (value: unknown): number => {
  if (value === null || value === undefined) {
    return 0;
  }
  if (typeof value === 'number') {
    return Number.isFinite(value) ? value : 0;
  }
  if (typeof value === 'string') {
    const parsed = Number(value.trim());
    return Number.isFinite(parsed) ? parsed : 0;
  }
  return 0;
};

const hasUsageData = (value?: LangfuseUsage | LangfuseUsageDetails | null): boolean => {
  if (!value) return false;
  const candidate = value as Partial<Record<string, unknown>>;
  return ['input', 'output', 'total', 'inputTokens', 'outputTokens', 'totalTokens'].some(
    (key) => candidate[key] !== undefined && candidate[key] !== null
  );
};

const getTokenCounts = (observation: LangfuseObservation): { input: number; output: number; total: number } => {
  const normalize = (input: number, output: number, total: number) => {
    const calculableTotal = total || (input + output);
    return {
      input,
      output,
      total: calculableTotal,
    };
  };

  if (hasUsageData(observation.usageDetails)) {
    return normalize(
      numberFromUnknown(observation.usageDetails?.input),
      numberFromUnknown(observation.usageDetails?.output),
      numberFromUnknown(observation.usageDetails?.total)
    );
  }

  if (hasUsageData(observation.usage)) {
    return normalize(
      numberFromUnknown(observation.usage?.inputTokens),
      numberFromUnknown(observation.usage?.outputTokens),
      numberFromUnknown(observation.usage?.totalTokens)
    );
  }

  if (
    observation.inputUsage !== undefined ||
    observation.outputUsage !== undefined ||
    observation.totalUsage !== undefined
  ) {
    return normalize(
      numberFromUnknown(observation.inputUsage),
      numberFromUnknown(observation.outputUsage),
      numberFromUnknown(observation.totalUsage)
    );
  }

  return normalize(0, 0, 0);
};

const formatDateTime = (value?: string | null): string => {
  if (!value) return 'Unknown timestamp';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
};

const formatDuration = (start?: string | null, end?: string | null): string => {
  if (!start) return 'N/A';
  const startMs = new Date(start).getTime();
  const endMs = end ? new Date(end).getTime() : startMs;
  if (Number.isNaN(startMs) || Number.isNaN(endMs)) return 'N/A';
  const diff = Math.max(0, endMs - startMs);
  if (diff >= 60_000) {
    const minutes = Math.floor(diff / 60_000);
    const seconds = Math.round((diff % 60_000) / 1000);
    return `${minutes}m ${seconds}s`;
  }
  if (diff >= 1000) {
    return `${(diff / 1000).toFixed(1)}s`;
  }
  return `${diff}ms`;
};

const buildObservationTree = (observations: LangfuseObservation[]): ObservationNode[] => {
  const nodeMap = new Map<string, ObservationNode>();
  const roots: ObservationNode[] = [];

  const sorted = [...observations].sort((a, b) => {
    const aStart = a.startTime ? new Date(a.startTime).getTime() : Number.NEGATIVE_INFINITY;
    const bStart = b.startTime ? new Date(b.startTime).getTime() : Number.NEGATIVE_INFINITY;
    return aStart - bStart;
  });

  sorted.forEach((obs) => {
    nodeMap.set(obs.id, { observation: obs, children: [] });
  });

  sorted.forEach((obs) => {
    const node = nodeMap.get(obs.id);
    if (!node) return;
    const parentId = obs.parentObservationId;
    if (parentId && nodeMap.has(parentId)) {
      nodeMap.get(parentId)!.children.push(node);
    } else {
      roots.push(node);
    }
  });

  return roots;
};

// Status colors for simplified tree view
const TREE_STATUS_COLORS: Record<string, { bg: string; text: string; icon: string }> = {
  completed: { bg: 'bg-emerald-500/20', text: 'text-emerald-400', icon: '✓' },
  success: { bg: 'bg-emerald-500/20', text: 'text-emerald-400', icon: '✓' },
  running: { bg: 'bg-blue-500/20', text: 'text-blue-400', icon: '◉' },
  pending: { bg: 'bg-slate-500/20', text: 'text-slate-400', icon: '○' },
  failed: { bg: 'bg-red-500/20', text: 'text-red-400', icon: '✕' },
  error: { bg: 'bg-red-500/20', text: 'text-red-400', icon: '✕' },
  waiting: { bg: 'bg-amber-500/20', text: 'text-amber-400', icon: '⏳' },
  default: { bg: 'bg-slate-600/20', text: 'text-slate-400', icon: '•' },
};

const getStatusStyle = (status?: string | null) => {
  if (!status) return TREE_STATUS_COLORS.default;
  const lower = status.toLowerCase();
  if (lower.includes('success') || lower.includes('completed') || lower.includes('done')) return TREE_STATUS_COLORS.completed;
  if (lower.includes('running') || lower.includes('processing')) return TREE_STATUS_COLORS.running;
  if (lower.includes('pending') || lower.includes('queued')) return TREE_STATUS_COLORS.pending;
  if (lower.includes('fail') || lower.includes('error')) return TREE_STATUS_COLORS.failed;
  if (lower.includes('wait') || lower.includes('approval')) return TREE_STATUS_COLORS.waiting;
  return TREE_STATUS_COLORS.default;
};

const truncateObsName = (name: string, maxLen: number = 28): string => {
  if (name.length <= maxLen) return name;
  return name.slice(0, maxLen - 1) + '…';
};

const ObservationTreeView = ({ nodes, depth = 0, maxRootNodes = 4 }: { nodes: ObservationNode[]; depth?: number; maxRootNodes?: number }) => {
  const [showAll, setShowAll] = useState(false);
  const isRoot = depth === 0;
  const visibleNodes = isRoot && !showAll ? nodes.slice(0, maxRootNodes) : nodes;
  const hiddenCount = isRoot ? nodes.length - maxRootNodes : 0;

  return (
    <div className="space-y-2">
      {visibleNodes.map((node) => {
        const statusStyle = getStatusStyle(node.observation.status);
        const fullName = node.observation.name || 'Unnamed observation';
        const duration = formatDuration(node.observation.startTime, node.observation.endTime);

        return (
          <div
            key={node.observation.id}
            className={`rounded-lg ${statusStyle.bg} border border-slate-700/40 p-2.5 transition-all hover:border-slate-600/60`}
            title={`${fullName}\nType: ${node.observation.type}\nStatus: ${node.observation.status || 'unknown'}\nDuration: ${duration}`}
          >
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2 min-w-0 flex-1">
                <span className={`text-sm font-bold ${statusStyle.text}`}>{statusStyle.icon}</span>
                <span className="text-sm text-white font-medium truncate" title={fullName}>
                  {truncateObsName(fullName)}
                </span>
              </div>
              <span className="text-xs text-slate-400 whitespace-nowrap font-mono">{duration}</span>
            </div>
            {node.children.length > 0 && (
              <div className="mt-2 ml-4 border-l-2 border-slate-700/50 pl-3">
                <ObservationTreeView nodes={node.children} depth={depth + 1} />
              </div>
            )}
          </div>
        );
      })}
      {isRoot && hiddenCount > 0 && !showAll && (
        <button
          onClick={() => setShowAll(true)}
          className="w-full py-2 text-sm text-blue-400 hover:text-blue-300 bg-slate-800/50 rounded-lg border border-slate-700/40 hover:border-blue-500/30 transition-colors"
        >
          + {hiddenCount} more observation{hiddenCount !== 1 ? 's' : ''}
        </button>
      )}
      {isRoot && showAll && nodes.length > maxRootNodes && (
        <button
          onClick={() => setShowAll(false)}
          className="w-full py-2 text-sm text-slate-400 hover:text-slate-300 bg-slate-800/50 rounded-lg border border-slate-700/40 transition-colors"
        >
          Show less
        </button>
      )}
    </div>
  );
};

const ObservationTimeline = ({ observations }: { observations: LangfuseObservation[] }) => {
  const timeline = useMemo(() => {
    if (!observations.length) return null;
    const entries = observations
      .filter((obs) => obs.startTime)
      .map((obs) => {
        const start = obs.startTime ? new Date(obs.startTime).getTime() : 0;
        const end = obs.endTime ? new Date(obs.endTime).getTime() : start;
        return { obs, start, end, duration: Math.max(1, end - start) };
      });

    if (!entries.length) return null;
    const minStart = Math.min(...entries.map((entry) => entry.start));
    const maxEnd = Math.max(...entries.map((entry) => entry.end));
    const totalWindow = Math.max(1, maxEnd - minStart);

    return entries
      .sort((a, b) => a.start - b.start)
      .map((entry) => ({
        ...entry,
        offsetPct: ((entry.start - minStart) / totalWindow) * 100,
        widthPct: (entry.duration / totalWindow) * 100,
      }));
  }, [observations]);

  if (!timeline) {
    return <p className="text-sm text-slate-400">No timed observations available.</p>;
  }

  return (
    <div className="space-y-3">
      {timeline.map((entry) => (
        <div key={entry.obs.id}>
          <div className="flex justify-between text-xs text-slate-400 mb-1">
            <span className="truncate pr-2">{entry.obs.name || entry.obs.type}</span>
            <span>{formatDuration(entry.obs.startTime, entry.obs.endTime)}</span>
          </div>
          <div className="relative h-2 rounded bg-slate-800/80">
            <span
              className="absolute inset-y-0 rounded bg-gradient-to-r from-blue-500/80 via-indigo-400/80 to-emerald-400/80 shadow-[0_0_12px_rgba(56,189,248,0.5)]"
              style={{ left: `${entry.offsetPct}%`, width: `${Math.max(1, entry.widthPct)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
};

const ObservationsTable = ({ observations }: { observations: LangfuseObservation[] }) => {
  const [showAll, setShowAll] = useState(false);
  const ordered = useMemo(
    () => [...observations].sort((a, b) => {
      const aStart = a.startTime ? new Date(a.startTime).getTime() : 0;
      const bStart = b.startTime ? new Date(b.startTime).getTime() : 0;
      return bStart - aStart;
    }),
    [observations]
  );
  const visible = showAll ? ordered : ordered.slice(0, 12);

  return (
    <div className="space-y-3">
      <div className="overflow-x-auto rounded-lg border border-slate-700/60">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-900/60 text-xs uppercase text-slate-400">
            <tr>
              <th className="px-4 py-2 text-left">Observation</th>
              <th className="px-4 py-2 text-left">Type</th>
              <th className="px-4 py-2 text-left">Duration</th>
              <th className="px-4 py-2 text-left">Tokens</th>
              <th className="px-4 py-2 text-left">Cost</th>
            </tr>
          </thead>
          <tbody>
            {visible.map((obs) => {
              const usageTotals = getTokenCounts(obs);
              return (
                <tr key={obs.id} className="border-t border-slate-800/60">
                <td className="px-4 py-2 text-slate-100">
                  <div className="font-medium">{obs.name || 'Untitled observation'}</div>
                  <div className="text-xs text-slate-500">{obs.id}</div>
                </td>
                <td className="px-4 py-2 text-slate-300">
                  <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800/80 border border-slate-700/60">
                    {obs.type}
                  </span>
                </td>
                <td className="px-4 py-2 text-slate-300">{formatDuration(obs.startTime, obs.endTime)}</td>
                <td className="px-4 py-2 text-slate-300">
                  {usageTotals.total.toLocaleString()}
                  <span className="text-slate-500"> tokens</span>
                </td>
                <td className="px-4 py-2 text-slate-300">
                  ${numberFromUnknown(obs.totalCost).toFixed(4)}
                </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {observations.length > 12 && (
        <button
          type="button"
          className="text-sm text-blue-400 hover:text-blue-300"
          onClick={() => setShowAll((prev) => !prev)}
        >
          {showAll ? 'Collapse observation list' : `Show all ${observations.length} observations`}
        </button>
      )}
    </div>
  );
};

export default function LangfuseTraceDashboard({ traceId, traceUrl, jobId }: LangfuseTraceDashboardProps) {
  const { getToken } = useAuth();
  const [data, setData] = useState<LangfuseTracePayload | null>(null);
  const [metadata, setMetadata] = useState<ApiSuccess['metadata']>();
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [refreshCounter, setRefreshCounter] = useState(0);
  const [showExpandedTree, setShowExpandedTree] = useState(false);

  useEffect(() => {
    if (!traceId || traceId === 'unknown') {
      setError('Langfuse trace ID is not available for this job. Run the workflow again to capture observability data.');
      setData(null);
      return;
    }

    const controller = new AbortController();
    const fetchTrace = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await authenticatedFetch(
          `/api/langfuse/trace?traceId=${encodeURIComponent(traceId)}`,
          getToken,
          {},
          controller.signal
        );
        const payload = (await response.json()) as ApiResponse;
        if (!payload.success) {
          throw new Error(payload.details || payload.error || 'Unknown Langfuse error');
        }
        setData(payload.data);
        setMetadata(payload.metadata);
      } catch (err) {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : 'Failed to load Langfuse trace');
        setData(null);
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      }
    };

    fetchTrace();
    return () => controller.abort();
  }, [traceId, refreshCounter, getToken]);

  const observations = useMemo(() => data?.observations ?? [], [data]);
  const observationTree = useMemo(() => buildObservationTree(observations), [observations]);

  const summary = useMemo(() => {
    if (!data) return null;
    const totalTokens = observations.reduce((acc, obs) => acc + getTokenCounts(obs).total, 0);
    const totalCost = typeof data.totalCost === 'number' ? data.totalCost : Number(data.totalCost ?? 0);
    const earliest = observations.reduce((min, obs) => {
      const ts = obs.startTime ? new Date(obs.startTime).getTime() : Number.POSITIVE_INFINITY;
      return Math.min(min, ts);
    }, Number.POSITIVE_INFINITY);
    const latest = observations.reduce((max, obs) => {
      const ts = obs.endTime ? new Date(obs.endTime).getTime() : obs.startTime ? new Date(obs.startTime).getTime() : 0;
      return Math.max(max, ts);
    }, 0);
    const totalDurationMs = latest > earliest ? latest - earliest : 0;
    const models = new Set(
      observations
        .map((obs) => obs.model)
        .filter((model): model is string => Boolean(model))
    );

    return {
      totalTokens,
      totalCost,
      totalDurationLabel: totalDurationMs ? formatDuration(new Date(earliest).toISOString(), new Date(latest).toISOString()) : 'N/A',
      models: Array.from(models),
    };
  }, [data, observations]);

  return (
    <div className="space-y-4 rounded-2xl border border-blue-500/30 bg-slate-900/70 p-6 shadow-inner shadow-blue-900/40">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-widest text-blue-400">Langfuse Trace Dashboard</p>
          <h3 className="text-xl font-semibold text-white mt-1">
            {data?.name || `Trace ${traceId ?? 'Unavailable'}`}
          </h3>
          <p className="text-sm text-slate-400">
            Job {jobId} · Captured {data?.timestamp ? formatDateTime(data.timestamp) : 'N/A'} · {data?.environment || 'default environment'}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className="btn-secondary"
            onClick={() => setRefreshCounter((prev) => prev + 1)}
            disabled={isLoading}
          >
            {isLoading ? 'Refreshing…' : 'Refresh data'}
          </button>
          {traceUrl && (
            <a
              href={traceUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary"
            >
              Open in Langfuse
            </a>
          )}
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-300">
          {error}
        </div>
      )}

      {isLoading && !data && !error && (
        <div className="text-sm text-slate-400">Loading trace observations…</div>
      )}

      {data && summary && (
        <>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
            <div className="card border-l-4 border-blue-500">
              <p className="text-xs uppercase text-slate-400 tracking-wider">Observations</p>
              <p className="text-3xl font-bold text-white">{observations.length}</p>
              <p className="text-xs text-slate-500">Total Langfuse operations</p>
            </div>
            <div className="card border-l-4 border-emerald-500">
              <p className="text-xs uppercase text-slate-400 tracking-wider">Total Tokens</p>
              <p className="text-3xl font-bold text-white">{summary.totalTokens.toLocaleString()}</p>
              <p className="text-xs text-slate-500">Across all observations</p>
            </div>
            <div className="card border-l-4 border-purple-500">
              <p className="text-xs uppercase text-slate-400 tracking-wider">Trace Cost</p>
              <p className="text-3xl font-bold text-white">${summary.totalCost.toFixed(4)}</p>
              <p className="text-xs text-slate-500">USD reported by Langfuse</p>
            </div>
            <div className="card border-l-4 border-amber-500">
              <p className="text-xs uppercase text-slate-400 tracking-wider">Span Duration</p>
              <p className="text-3xl font-bold text-white">{summary.totalDurationLabel}</p>
              <p className="text-xs text-slate-500">Earliest start → latest end</p>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <div className="rounded-xl border border-slate-800/60 bg-slate-900/60 p-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-white font-semibold">Timeline Diagram</h4>
                <p className="text-xs text-slate-500">Visualizes relative spans</p>
              </div>
              <ObservationTimeline observations={observations} />
            </div>
            <div className="rounded-xl border border-slate-800/60 bg-slate-900/60 p-4 max-h-[460px] overflow-y-auto">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <h4 className="text-white font-semibold">Observation Tree</h4>
                  <button
                    onClick={() => setShowExpandedTree(true)}
                    className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-lg transition-colors"
                    title="Expand to fullscreen"
                  >
                    <ArrowsPointingOutIcon className="w-4 h-4" />
                  </button>
                </div>
                <p className="text-xs text-slate-500">Parent/child call graph</p>
              </div>
              {observationTree.length ? (
                <ObservationTreeView nodes={observationTree} />
              ) : (
                <p className="text-sm text-slate-400">No hierarchical data found for this trace.</p>
              )}
            </div>
          </div>

          <div className="rounded-xl border border-slate-800/60 bg-slate-900/60 p-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-white font-semibold">Observation Log</h4>
              <div className="text-xs text-slate-500">
                Last synced {metadata?.fetchedAt ? formatDateTime(metadata.fetchedAt) : 'just now'}
              </div>
            </div>
            <ObservationsTable observations={observations} />
          </div>

          {/* Expanded Tree Modal */}
          <Transition appear show={showExpandedTree} as={Fragment}>
            <Dialog as="div" className="relative z-50" onClose={() => setShowExpandedTree(false)}>
              {/* Backdrop */}
              <TransitionChild
                as={Fragment}
                enter="ease-out duration-300"
                enterFrom="opacity-0"
                enterTo="opacity-100"
                leave="ease-in duration-200"
                leaveFrom="opacity-100"
                leaveTo="opacity-0"
              >
                <div className="fixed inset-0 bg-black/80 backdrop-blur-sm" />
              </TransitionChild>

              {/* Modal panel */}
              <div className="fixed inset-0 overflow-y-auto">
                <div className="flex min-h-full items-center justify-center p-4">
                  <TransitionChild
                    as={Fragment}
                    enter="ease-out duration-300"
                    enterFrom="opacity-0 scale-95"
                    enterTo="opacity-100 scale-100"
                    leave="ease-in duration-200"
                    leaveFrom="opacity-100 scale-100"
                    leaveTo="opacity-0 scale-95"
                  >
                    <DialogPanel className="w-full max-w-4xl max-h-[85vh] transform overflow-hidden rounded-2xl bg-slate-900 border border-slate-700 shadow-2xl transition-all flex flex-col">
                      {/* Header */}
                      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700 bg-slate-800/50 flex-shrink-0">
                        <div>
                          <DialogTitle className="text-lg font-semibold text-white">
                            Workflow Observation Tree
                          </DialogTitle>
                          <p className="text-sm text-slate-400 mt-0.5">
                            {data?.name || 'Trace'} • {observations.length} observation{observations.length !== 1 ? 's' : ''}
                          </p>
                        </div>
                        <div className="flex items-center gap-3">
                          {traceUrl && (
                            <a
                              href={traceUrl}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-sm text-blue-400 hover:text-blue-300 underline"
                            >
                              Open in Langfuse
                            </a>
                          )}
                          <button
                            onClick={() => setShowExpandedTree(false)}
                            className="rounded-lg p-2 text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
                            aria-label="Close dialog"
                          >
                            <XMarkIcon className="h-6 w-6" />
                          </button>
                        </div>
                      </div>

                      {/* Scrollable content */}
                      <div className="flex-1 overflow-y-auto p-6">
                        {observationTree.length ? (
                          <ObservationTreeView nodes={observationTree} maxRootNodes={100} />
                        ) : (
                          <p className="text-sm text-slate-400">No hierarchical data found for this trace.</p>
                        )}
                      </div>

                      {/* Footer legend */}
                      <div className="px-6 py-3 border-t border-slate-700 bg-slate-800/50 flex-shrink-0">
                        <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400">
                          <span className="font-medium text-slate-300">Status:</span>
                          <div className="flex items-center gap-1.5">
                            <span className="text-emerald-400">✓</span>
                            <span>Completed</span>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <span className="text-blue-400">◉</span>
                            <span>Running</span>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <span className="text-slate-400">○</span>
                            <span>Pending</span>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <span className="text-red-400">✕</span>
                            <span>Failed</span>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <span className="text-amber-400">⏳</span>
                            <span>Waiting</span>
                          </div>
                        </div>
                      </div>
                    </DialogPanel>
                  </TransitionChild>
                </div>
              </div>
            </Dialog>
          </Transition>
        </>
      )}
    </div>
  );
}

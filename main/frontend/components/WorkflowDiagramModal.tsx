'use client';

import { Fragment, useCallback, useEffect, useMemo } from 'react';
import { Dialog, DialogPanel, DialogTitle, Transition, TransitionChild } from '@headlessui/react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import {
  ReactFlow,
  Node,
  Edge,
  Controls,
  MiniMap,
  Background,
  BackgroundVariant,
  useNodesState,
  useEdgesState,
  Handle,
  Position,
  NodeProps,
} from '@xyflow/react';
import dagre from 'dagre';
import '@xyflow/react/dist/style.css';

// ============================================================================
// Types
// ============================================================================

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
  usage?: {
    inputTokens?: number | string | null;
    outputTokens?: number | string | null;
    totalTokens?: number | string | null;
  } | null;
  usageDetails?: {
    input?: number | string | null;
    output?: number | string | null;
    total?: number | string | null;
  } | null;
}

interface WorkflowDiagramModalProps {
  isOpen: boolean;
  onClose: () => void;
  observations: LangfuseObservation[];
  traceName?: string | null;
  traceUrl?: string | null;
}

interface CustomNodeData extends Record<string, unknown> {
  label: string;
  fullName: string;
  type: string;
  status: string;
  duration: string;
  tokens: number;
  model: string;
  timestamp: string;
}

// ============================================================================
// Constants
// ============================================================================

const STATUS_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  completed: { bg: '#10b981', border: '#059669', text: '#ffffff' },
  success: { bg: '#10b981', border: '#059669', text: '#ffffff' },
  running: { bg: '#2563eb', border: '#1d4ed8', text: '#ffffff' },
  pending: { bg: '#64748b', border: '#475569', text: '#ffffff' },
  failed: { bg: '#ef4444', border: '#dc2626', text: '#ffffff' },
  error: { bg: '#ef4444', border: '#dc2626', text: '#ffffff' },
  waiting: { bg: '#f59e0b', border: '#d97706', text: '#000000' },
  default: { bg: '#334155', border: '#475569', text: '#ffffff' },
};

const STATUS_ICONS: Record<string, string> = {
  completed: '✓',
  success: '✓',
  running: '◉',
  pending: '○',
  failed: '✕',
  error: '✕',
  waiting: '⏳',
  default: '•',
};

const NODE_WIDTH = 200;
const NODE_HEIGHT = 70;

// ============================================================================
// Helpers
// ============================================================================

const getStatusKey = (status?: string | null): string => {
  if (!status) return 'default';
  const lower = status.toLowerCase();
  if (lower.includes('success') || lower.includes('completed') || lower.includes('done')) return 'completed';
  if (lower.includes('running') || lower.includes('processing')) return 'running';
  if (lower.includes('pending') || lower.includes('queued')) return 'pending';
  if (lower.includes('fail') || lower.includes('error')) return 'failed';
  if (lower.includes('wait') || lower.includes('approval')) return 'waiting';
  return 'default';
};

const formatDuration = (start?: string | null, end?: string | null): string => {
  if (!start) return 'N/A';
  const startMs = new Date(start).getTime();
  const endMs = end ? new Date(end).getTime() : Date.now();
  if (Number.isNaN(startMs) || Number.isNaN(endMs)) return 'N/A';
  const diff = Math.max(0, endMs - startMs);
  if (diff >= 60_000) {
    const minutes = Math.floor(diff / 60_000);
    const seconds = Math.round((diff % 60_000) / 1000);
    return `${minutes}m ${seconds}s`;
  }
  if (diff >= 1000) return `${(diff / 1000).toFixed(1)}s`;
  return `${diff}ms`;
};

const getTokenCount = (obs: LangfuseObservation): number => {
  if (obs.usageDetails?.total !== undefined && obs.usageDetails.total !== null) {
    return typeof obs.usageDetails.total === 'number' ? obs.usageDetails.total : Number(obs.usageDetails.total) || 0;
  }
  if (obs.usage?.totalTokens !== undefined && obs.usage.totalTokens !== null) {
    return typeof obs.usage.totalTokens === 'number' ? obs.usage.totalTokens : Number(obs.usage.totalTokens) || 0;
  }
  return 0;
};

const truncateName = (name: string, maxLen: number = 22): string => {
  if (name.length <= maxLen) return name;
  return name.slice(0, maxLen - 1) + '…';
};

// ============================================================================
// Custom Node Component
// ============================================================================

function WorkflowNode({ data }: NodeProps<Node<CustomNodeData>>) {
  const statusKey = getStatusKey(data.status);
  const colors = STATUS_COLORS[statusKey] || STATUS_COLORS.default;
  const icon = STATUS_ICONS[statusKey] || STATUS_ICONS.default;

  return (
    <div
      className="group relative rounded-lg shadow-lg transition-all duration-200 hover:scale-105 hover:shadow-xl"
      style={{
        backgroundColor: colors.bg,
        borderColor: colors.border,
        borderWidth: 2,
        borderStyle: 'solid',
        width: NODE_WIDTH,
        minHeight: NODE_HEIGHT,
        color: colors.text,
      }}
      title={`${data.fullName}\nStatus: ${data.status}\nDuration: ${data.duration}\nTokens: ${data.tokens.toLocaleString()}\nModel: ${data.model}`}
    >
      <Handle type="target" position={Position.Top} className="!bg-slate-400 !w-3 !h-3" />

      {/* Main content */}
      <div className="p-3">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-lg font-bold">{icon}</span>
          <span className="font-medium text-sm truncate flex-1">{data.label}</span>
        </div>
        <div className="text-xs opacity-80 flex items-center justify-between">
          <span>{data.duration}</span>
          <span>•</span>
          <span>{data.tokens > 0 ? `${data.tokens.toLocaleString()} tok` : 'N/A'}</span>
        </div>
      </div>

      {/* Tooltip on hover - positioned above */}
      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-50 pointer-events-none">
        <div className="bg-slate-900 border border-slate-700 rounded-lg shadow-xl p-3 text-white text-xs min-w-[220px] max-w-[280px]">
          <div className="font-semibold mb-2 break-words">{data.fullName}</div>
          <div className="space-y-1 text-slate-300">
            <div className="flex justify-between">
              <span>Status:</span>
              <span className="font-mono">{data.status || 'unknown'}</span>
            </div>
            <div className="flex justify-between">
              <span>Duration:</span>
              <span className="font-mono">{data.duration}</span>
            </div>
            <div className="flex justify-between">
              <span>Tokens:</span>
              <span className="font-mono">{data.tokens.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span>Model:</span>
              <span className="font-mono truncate max-w-[120px]">{data.model}</span>
            </div>
            <div className="flex justify-between">
              <span>Time:</span>
              <span className="font-mono text-[10px]">{data.timestamp}</span>
            </div>
          </div>
        </div>
        {/* Arrow */}
        <div className="absolute top-full left-1/2 -translate-x-1/2 w-0 h-0 border-l-8 border-r-8 border-t-8 border-l-transparent border-r-transparent border-t-slate-900" />
      </div>

      <Handle type="source" position={Position.Bottom} className="!bg-slate-400 !w-3 !h-3" />
    </div>
  );
}

const nodeTypes = { workflow: WorkflowNode };

// ============================================================================
// Layout with Dagre
// ============================================================================

const getLayoutedElements = (
  nodes: Node<CustomNodeData>[],
  edges: Edge[],
  direction: 'TB' | 'LR' = 'TB'
): { nodes: Node<CustomNodeData>[]; edges: Edge[] } => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));

  const isHorizontal = direction === 'LR';
  dagreGraph.setGraph({ rankdir: direction, nodesep: 50, ranksep: 80 });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - NODE_WIDTH / 2,
        y: nodeWithPosition.y - NODE_HEIGHT / 2,
      },
      targetPosition: isHorizontal ? Position.Left : Position.Top,
      sourcePosition: isHorizontal ? Position.Right : Position.Bottom,
    };
  });

  return { nodes: layoutedNodes, edges };
};

// ============================================================================
// Main Component
// ============================================================================

export default function WorkflowDiagramModal({
  isOpen,
  onClose,
  observations,
  traceName,
  traceUrl,
}: WorkflowDiagramModalProps) {
  // Convert observations to React Flow nodes and edges
  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => {
    const nodeList: Node<CustomNodeData>[] = [];
    const edgeList: Edge[] = [];

    observations.forEach((obs, idx) => {
      const name = obs.name || `Observation ${idx + 1}`;
      const node: Node<CustomNodeData> = {
        id: obs.id,
        type: 'workflow',
        position: { x: 0, y: 0 }, // Will be set by dagre
        data: {
          label: truncateName(name),
          fullName: name,
          type: obs.type,
          status: obs.status || 'unknown',
          duration: formatDuration(obs.startTime, obs.endTime),
          tokens: getTokenCount(obs),
          model: obs.model || 'N/A',
          timestamp: obs.startTime
            ? new Date(obs.startTime).toLocaleTimeString()
            : 'N/A',
        },
      };
      nodeList.push(node);

      // Create edge from parent to child
      if (obs.parentObservationId) {
        edgeList.push({
          id: `edge-${obs.parentObservationId}-${obs.id}`,
          source: obs.parentObservationId,
          target: obs.id,
          animated: false,
          style: { stroke: '#64748b', strokeWidth: 2 },
          type: 'smoothstep',
        });
      }
    });

    return getLayoutedElements(nodeList, edgeList);
  }, [observations]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Reset layout when observations change
  useEffect(() => {
    const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
      initialNodes,
      initialEdges
    );
    setNodes(layoutedNodes);
    setEdges(layoutedEdges);
  }, [initialNodes, initialEdges, setNodes, setEdges]);

  // Handle ESC key
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    },
    [onClose]
  );

  useEffect(() => {
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen, handleKeyDown]);

  if (observations.length === 0) {
    return null;
  }

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
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
              enterFrom="opacity-0 scale-95 translate-y-4"
              enterTo="opacity-100 scale-100 translate-y-0"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100 translate-y-0"
              leaveTo="opacity-0 scale-95 translate-y-4"
            >
              <DialogPanel className="w-full max-w-6xl h-[80vh] transform overflow-hidden rounded-2xl bg-slate-900 border border-slate-700 shadow-2xl transition-all flex flex-col">
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700 bg-slate-800/50">
                  <div>
                    <DialogTitle className="text-lg font-semibold text-white">
                      Workflow Diagram
                    </DialogTitle>
                    <p className="text-sm text-slate-400 mt-0.5">
                      {traceName || 'Trace'} • {observations.length} observation
                      {observations.length !== 1 ? 's' : ''}
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
                      onClick={onClose}
                      className="rounded-lg p-2 text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
                      aria-label="Close dialog"
                    >
                      <XMarkIcon className="h-6 w-6" />
                    </button>
                  </div>
                </div>

                {/* React Flow canvas */}
                <div className="flex-1 bg-slate-950">
                  <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    nodeTypes={nodeTypes}
                    fitView
                    fitViewOptions={{ padding: 0.2 }}
                    minZoom={0.1}
                    maxZoom={2}
                    attributionPosition="bottom-left"
                  >
                    <Controls
                      className="!bg-slate-800 !border-slate-700 !rounded-lg !shadow-lg"
                      showInteractive={false}
                    />
                    <MiniMap
                      className="!bg-slate-800 !border-slate-700 !rounded-lg"
                      nodeColor={(node) => {
                        const statusKey = getStatusKey((node.data as CustomNodeData)?.status);
                        return STATUS_COLORS[statusKey]?.bg || STATUS_COLORS.default.bg;
                      }}
                      maskColor="rgba(0, 0, 0, 0.7)"
                    />
                    <Background
                      variant={BackgroundVariant.Dots}
                      gap={20}
                      size={1}
                      color="#334155"
                    />
                  </ReactFlow>
                </div>

                {/* Footer legend */}
                <div className="px-6 py-3 border-t border-slate-700 bg-slate-800/50">
                  <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400">
                    <span className="font-medium text-slate-300">Status:</span>
                    {Object.entries(STATUS_COLORS)
                      .filter(([key]) => key !== 'default')
                      .map(([key, colors]) => (
                        <div key={key} className="flex items-center gap-1.5">
                          <span
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: colors.bg }}
                          />
                          <span className="capitalize">{key}</span>
                        </div>
                      ))}
                  </div>
                </div>
              </DialogPanel>
            </TransitionChild>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}

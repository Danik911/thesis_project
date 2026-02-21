import Head from 'next/head';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { getApiBaseUrl } from '@/lib/authenticatedFetch';
import MDAViewer from '@/components/MDAViewer';
import LIMSStepIndicator from '@/components/LIMSStepIndicator';
import ChatInterface from '@/components/ChatInterface';
import ClassificationPanel from '@/components/ClassificationPanel';
import TemplatePreview from '@/components/TemplatePreview';
import MergeConflictPanel from '@/components/MergeConflictPanel';
import PipelineStageDetail from '@/components/PipelineStageDetail';
import type { StageDetail } from '@/components/PipelineStageDetail';
import PlatformPillars from '@/components/PlatformPillars';
import TrustBanner from '@/components/TrustBanner';
import type { TemplateField } from '@/components/TemplatePreview';
import type { MergeConflict } from '@/components/MergeConflictPanel';
import type { ProvenanceBadgeProps } from '@/components/ProvenanceBadge';
import type {
  ClassificationResult,
  ExtractResponse,
  MergeConflictResponse,
  PipelineStageDetailResponse,
  ProvenancePayload,
  StatusResponse,
  TemplateResponse,
} from '@/types/lims';

type WorkflowView =
  | 'idle'
  | 'uploading'
  | 'classifying'
  | 'template_preview'
  | 'extracting'
  | 'merging'
  | 'review'
  | 'exporting'
  | 'done'
  | 'failed';

interface ClassificationViewModel {
  detectedType: string;
  confidence: number;
  method: string;
  evidence: string[];
  options: string[];
}

type ProvenanceCellMap = Record<string, { source: ProvenanceBadgeProps['source']; confidence?: number; detail?: string }>;

const CLASSIFICATION_OPTIONS: ClassificationResult['test_type'][] = ['HPLC', 'LOD', 'TITRATION', 'IDENTITY', 'OTHER'];

const STAGE_LABELS: Record<string, string> = {
  CLASSIFY: 'Classify',
  TEMPLATE: 'Template',
  EXTRACT: 'Extract',
  AUGMENT: 'Augment',
  MERGE: 'Merge',
  REVIEW: 'Review',
};

const EXTRACTION_STAGES = [
  'Uploading PDF...',
  'Classifying test type...',
  'Running pipeline extraction...',
  'Preparing merge review...',
] as const;

const FADE = { initial: { opacity: 0, y: 16 }, animate: { opacity: 1, y: 0 }, exit: { opacity: 0, y: -8 } };

const DEFAULT_STAGE_DETAILS: StageDetail[] = [
  { key: 'classify', title: 'Classify', summary: 'Awaiting stage details.', bullets: [] },
  { key: 'template', title: 'Template', summary: 'Awaiting stage details.', bullets: [] },
  { key: 'extract', title: 'Extract', summary: 'Awaiting stage details.', bullets: [] },
  { key: 'augment', title: 'Augment', summary: 'Awaiting stage details.', bullets: [] },
  { key: 'merge', title: 'Merge', summary: 'Awaiting stage details.', bullets: [] },
  { key: 'review', title: 'Review', summary: 'Awaiting stage details.', bullets: [] },
];

function mapBackendStatusToWorkflow(status: string): WorkflowView {
  switch (status) {
    case 'FAILED':
      return 'failed';
    case 'EXPORTED':
      return 'done';
    case 'APPROVED':
    case 'PENDING_REVIEW':
      return 'review';
    case 'MERGING':
      return 'merging';
    case 'CLASSIFYING':
      return 'classifying';
    case 'LOADING_TEMPLATE':
      return 'template_preview';
    case 'EXTRACTING':
    case 'GENERATING':
    case 'AUGMENTING':
      return 'extracting';
    default:
      return 'idle';
  }
}

function toIndicatorStatus(workflowView: WorkflowView, backendStatus: string): string {
  if (workflowView === 'review' && backendStatus === 'PENDING_REVIEW') return 'PENDING_REVIEW';
  if (workflowView === 'review' && backendStatus === 'APPROVED') return 'APPROVED';
  if (workflowView === 'done') return 'DONE';
  if (workflowView === 'failed') return 'FAILED';
  if (workflowView === 'template_preview') return 'TEMPLATE_PREVIEW';
  if (workflowView === 'exporting') return 'EXPORTING';
  if (workflowView === 'uploading') return 'UPLOADING';
  return backendStatus || 'CLASSIFYING';
}

function normalizePath(path: string): string {
  return path.replace(/\[(\d+)\]/g, '.$1');
}

function toCellProvenanceMap(provenance?: ProvenancePayload): ProvenanceCellMap {
  const mapped: ProvenanceCellMap = {};
  if (!provenance?.fields) return mapped;

  for (const [rawPath, entry] of Object.entries(provenance.fields)) {
    const key = normalizePath(rawPath);
    mapped[key] = {
      source: entry.source,
      confidence: entry.confidence,
      detail: entry.source_detail,
    };
  }

  return mapped;
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return '--';
  if (typeof value === 'string') return value;
  if (typeof value === 'number' || typeof value === 'boolean') return String(value);
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

function summarizeValidationError(value: unknown): string {
  const raw = formatValue(value);
  if (!raw || raw === '--') return raw;

  const firstLine = raw.split('\n')[0] ?? raw;
  const match = firstLine.match(/(\d+)\s+validation\s+errors?/i);
  if (match) {
    return `${match[1]} validation errors (details available in review Validation Details panel)`;
  }

  if (firstLine.length > 160) {
    return `${firstLine.slice(0, 160)}...`;
  }

  return firstLine;
}

function summarizeExtractionTrace(value: unknown): string {
  if (!value || typeof value !== 'object') {
    return formatValue(value);
  }

  const trace = value as Record<string, unknown>;
  const summary = {
    provider: trace.provider,
    run_id: trace.run_id,
    run_status: trace.run_status,
    duration_ms: trace.duration_ms,
    extraction_mode: trace.extraction_mode,
    extraction_target: trace.extraction_target,
  };

  return formatValue(summary);
}

function toMergeConflicts(conflicts?: MergeConflictResponse[]): MergeConflict[] {
  if (!conflicts) return [];
  return conflicts.map((conflict, index) => ({
    id: `${conflict.field_path}-${index}`,
    field: conflict.field_path,
    templateValue: formatValue(conflict.template_value),
    extractedValue: formatValue(conflict.extracted_value),
  }));
}

function toStageDetails(stageDetails?: PipelineStageDetailResponse[]): StageDetail[] {
  if (!stageDetails || stageDetails.length === 0) {
    return DEFAULT_STAGE_DETAILS;
  }

  return stageDetails.map((item) => {
    const key = item.stage.toLowerCase();

    const detailsEntries = Object.entries(item.details || {}).map(([detailKey, value]) => {
      if (item.stage === 'EXTRACT' && detailKey === 'validation_error') {
        return `${detailKey}: ${summarizeValidationError(value)}`;
      }

      if (item.stage === 'EXTRACT' && detailKey === 'extraction_trace') {
        return `${detailKey}: ${summarizeExtractionTrace(value)}`;
      }

      return `${detailKey}: ${formatValue(value)}`;
    });

    const extractNote =
      item.stage === 'EXTRACT'
        ? ['note: Extract validation is pre-merge and informational; approval is gated by review validation.']
        : [];

    return {
      key,
      title: STAGE_LABELS[item.stage] ?? item.stage,
      summary: item.summary,
      bullets: [`duration_ms: ${item.duration_ms}`, ...extractNote, ...detailsEntries],
    };
  });
}

function toClassificationViewModel(classification: ClassificationResult): ClassificationViewModel {
  return {
    detectedType: classification.test_type,
    confidence: classification.confidence,
    method: classification.method,
    evidence: classification.evidence,
    options: CLASSIFICATION_OPTIONS,
  };
}

function toTemplateFields(template: TemplateResponse): TemplateField[] {
  const fixed = template.fixed_fields.map((path) => ({
    key: `fixed.${path}`,
    label: path,
    kind: 'fixed' as const,
    value: 'Template fixed value',
  }));

  const variable = template.variable_fields.map((path) => ({
    key: `variable.${path}`,
    label: path,
    kind: 'variable' as const,
  }));

  return [...fixed, ...variable];
}

export default function LimsPage() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [backendStatus, setBackendStatus] = useState<string>('IDLE');
  const [workflowView, setWorkflowView] = useState<WorkflowView>('idle');
  const [pdfFilename, setPdfFilename] = useState<string | null>(null);
  const [sizeBytes, setSizeBytes] = useState<number>(0);

  const [mdaData, setMdaData] = useState<Record<string, unknown> | null>(null);
  const [validated, setValidated] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [provenanceMap, setProvenanceMap] = useState<ProvenanceCellMap>({});

  const [classification, setClassification] = useState<ClassificationViewModel>({
    detectedType: 'OTHER',
    confidence: 0,
    method: 'unclassified',
    evidence: [],
    options: CLASSIFICATION_OPTIONS,
  });

  const [templateFields, setTemplateFields] = useState<TemplateField[]>([]);
  const [mergeConflicts, setMergeConflicts] = useState<MergeConflict[]>([]);
  const [stageDetails, setStageDetails] = useState<StageDetail[]>(DEFAULT_STAGE_DETAILS);

  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [loading, setLoading] = useState(false);
  const [extractionStage, setExtractionStage] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [approveLoading, setApproveLoading] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const indicatorStatus = useMemo(
    () => toIndicatorStatus(workflowView, backendStatus),
    [workflowView, backendStatus]
  );

  useEffect(() => {
    if (!loading) {
      setExtractionStage(0);
      return;
    }
    const timers = [
      setTimeout(() => setExtractionStage(1), 1200),
      setTimeout(() => setExtractionStage(2), 4200),
      setTimeout(() => setExtractionStage(3), 8200),
    ];
    return () => timers.forEach(clearTimeout);
  }, [loading]);

  useEffect(() => {
    const inProgressStatuses = ['EXTRACTING', 'CLASSIFYING', 'LOADING_TEMPLATE', 'GENERATING', 'AUGMENTING', 'MERGING'];
    if (!jobId || !inProgressStatuses.includes(backendStatus)) {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
      return;
    }

    pollRef.current = setInterval(async () => {
      try {
        const baseUrl = getApiBaseUrl();
        const res = await fetch(`${baseUrl}/lims/status/${jobId}`);
        if (!res.ok) return;

        const data: StatusResponse = await res.json();
        setBackendStatus(data.status);

        if (data.status === 'FAILED') {
          setError(data.error ?? 'Pipeline failed.');
          setWorkflowView('failed');
          return;
        }

        if (data.classification) {
          setClassification(toClassificationViewModel(data.classification));
        }

        if (data.mda_template) {
          setMdaData(data.mda_template);
        }

        setProvenanceMap(toCellProvenanceMap(data.provenance));
        setMergeConflicts(toMergeConflicts(data.conflicts));
        setStageDetails(toStageDetails(data.stage_details));

        if (data.validated !== undefined) {
          setValidated(data.validated);
        }
        if (data.validation_error !== undefined) {
          setValidationError(data.validation_error ?? null);
        }

        const view = mapBackendStatusToWorkflow(data.status);
        setWorkflowView(view);
      } catch {
        // Polling intentionally silent.
      }
    }, 3000);

    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [jobId, backendStatus]);

  const handleFile = useCallback((selectedFile: File) => {
    if (!selectedFile.name.toLowerCase().endsWith('.pdf')) {
      setError('Only PDF files are accepted.');
      return;
    }
    setFile(selectedFile);
    setError(null);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile) handleFile(droppedFile);
    },
    [handleFile]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  }, []);

  const handleDropzoneKeyDown = useCallback((e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      fileInputRef.current?.click();
    }
  }, []);

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const selected = e.target.files?.[0];
      if (selected) handleFile(selected);
    },
    [handleFile]
  );

  const runExtractPipeline = useCallback(async () => {
    if (!file) return;

    setWorkflowView('extracting');
    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const baseUrl = getApiBaseUrl();
      const response = await fetch(`${baseUrl}/lims/extract`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const body = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(body.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      const data: ExtractResponse = await response.json();

      setJobId(data.job_id);
      setPdfFilename(data.filename);
      setSizeBytes(data.size_bytes);
      setBackendStatus(data.status);
      setValidated(data.validated);
      setValidationError(data.validation_error ?? null);
      setClassification(toClassificationViewModel(data.classification));

      const mda = data.mda_template ?? data.raw_extraction ?? null;
      setMdaData(mda);
      setProvenanceMap(toCellProvenanceMap(data.provenance));
      const mappedConflicts = toMergeConflicts(data.conflicts);
      setMergeConflicts(mappedConflicts);
      setStageDetails(toStageDetails(data.stage_details));

      if (data.status === 'FAILED') {
        setWorkflowView('failed');
      } else if (mappedConflicts.length > 0) {
        setWorkflowView('merging');
      } else {
        setWorkflowView('review');
      }

      if (data.mda_generation && 'generation_error' in data.mda_generation) {
        const generationError = String((data.mda_generation as Record<string, unknown>).generation_error ?? 'Unknown generation error');
        setError(`MDA generation warning: ${generationError}`);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message);
      setWorkflowView('failed');
      setBackendStatus('FAILED');
    } finally {
      setLoading(false);
    }
  }, [file]);

  const handleStartPipeline = useCallback(async () => {
    if (!file) return;

    setLoading(true);
    setError(null);
    setWorkflowView('uploading');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const baseUrl = getApiBaseUrl();
      const response = await fetch(`${baseUrl}/lims/classify`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const body = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(body.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      const data: ClassificationResult = await response.json();
      setClassification(toClassificationViewModel(data));
      setWorkflowView('classifying');
      setBackendStatus('CLASSIFYING');
      setPdfFilename(file.name);
      setSizeBytes(file.size);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message);
      setWorkflowView('failed');
      setBackendStatus('FAILED');
    } finally {
      setLoading(false);
    }
  }, [file]);

  const moveToTemplatePreview = useCallback(async (selectedType: string) => {
    setClassification((previous) => ({ ...previous, detectedType: selectedType }));

    if (selectedType === 'OTHER') {
      setTemplateFields([]);
      await runExtractPipeline();
      return;
    }

    try {
      setLoading(true);
      setBackendStatus('LOADING_TEMPLATE');
      const baseUrl = getApiBaseUrl();
      const response = await fetch(`${baseUrl}/lims/template/${selectedType}`);

      if (!response.ok) {
        const body = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(body.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      const template: TemplateResponse = await response.json();
      setTemplateFields(toTemplateFields(template));
      setWorkflowView('template_preview');
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message);
      setWorkflowView('failed');
      setBackendStatus('FAILED');
    } finally {
      setLoading(false);
    }
  }, [runExtractPipeline]);

  const handleApprove = useCallback(async () => {
    if (!jobId) return;

    setApproveLoading(true);
    setError(null);

    try {
      const baseUrl = getApiBaseUrl();
      const response = await fetch(`${baseUrl}/lims/approve/${jobId}`, { method: 'POST' });

      if (!response.ok) {
        const body = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(body.detail || `HTTP ${response.status}`);
      }

      const data = (await response.json()) as { status?: string };
      if (data.status) {
        setBackendStatus(data.status);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message);
    } finally {
      setApproveLoading(false);
    }
  }, [jobId]);

  const handleExport = useCallback(() => {
    if (!jobId) return;

    setWorkflowView('exporting');
    const baseUrl = getApiBaseUrl();
    window.open(`${baseUrl}/lims/export/${jobId}`, '_blank');
    setBackendStatus('EXPORTED');
    setWorkflowView('done');
  }, [jobId]);

  const handleMDAUpdate = useCallback((updatedMDA: Record<string, unknown>) => {
    setMdaData(updatedMDA);
  }, []);

  const handleValidationUpdate = useCallback((isValid: boolean, valError: string | null) => {
    setValidated(isValid);
    setValidationError(valError);
  }, []);

  const handleStartOver = useCallback(() => {
    setFile(null);
    setJobId(null);
    setBackendStatus('IDLE');
    setWorkflowView('idle');
    setMdaData(null);
    setValidated(false);
    setValidationError(null);
    setError(null);
    setPdfFilename(null);
    setSizeBytes(0);
    setApproveLoading(false);
    setTemplateFields([]);
    setMergeConflicts([]);
    setProvenanceMap({});
    setStageDetails(DEFAULT_STAGE_DETAILS);

    if (fileInputRef.current) fileInputRef.current.value = '';
    if (pollRef.current) clearInterval(pollRef.current);
  }, []);

  return (
    <>
      <Head>
        <title>LabAI Method Copilot | AI4LIMS</title>
      </Head>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-8 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 bg-emerald-600/20 rounded-xl flex items-center justify-center border border-emerald-500/30">
                <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 to-teal-300" style={{ fontFamily: 'var(--font-display)' }}>
                  LabAI Method Copilot
                </h1>
                <p className="text-sm text-slate-400">Deterministic Intelligence for Method Lifecycle</p>
              </div>
            </div>
            {workflowView === 'idle' && (
              <p className="text-slate-400 text-sm max-w-2xl">
                Upload a pharmaceutical method PDF. AI classifies, extracts, and structures your data — you review, approve, and export. Every decision is yours.
              </p>
            )}
          </div>

          {workflowView !== 'idle' && !loading && (
            <button
              onClick={handleStartOver}
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium text-slate-400 hover:text-slate-200 border border-slate-700 hover:border-slate-600 transition-all"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Start Over
            </button>
          )}
        </div>

        {workflowView !== 'idle' && (
          <>
            <div className="mb-4 flex items-center justify-between px-4 py-2.5 rounded-xl bg-slate-800/30 border border-slate-700/30">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-emerald-400" style={{ fontFamily: 'var(--font-display)' }}>LabAI</span>
                <span className="text-slate-600 text-xs">|</span>
                <span className="text-xs text-slate-400">{STAGE_LABELS[backendStatus] ?? backendStatus}</span>
              </div>
              <PlatformPillars variant="compact" />
            </div>
            <div className="mb-8">
              <LIMSStepIndicator currentStatus={indicatorStatus} />
            </div>
          </>
        )}

        <AnimatePresence mode="wait">
          {workflowView === 'idle' && !loading && (
            <motion.div key="upload" {...FADE}>
              <div className="mb-8">
                <PlatformPillars variant="full" />
              </div>

              <div className="mb-6">
                <TrustBanner />
              </div>

              <div
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onClick={() => fileInputRef.current?.click()}
                onKeyDown={handleDropzoneKeyDown}
                role="button"
                tabIndex={0}
                className={`relative border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all ${
                  dragOver
                    ? 'border-emerald-400 bg-emerald-500/10'
                    : file
                    ? 'border-emerald-500/40 bg-emerald-500/5'
                    : 'border-slate-600 hover:border-emerald-500/50 hover:bg-slate-800/50'
                }`}
              >
                <input ref={fileInputRef} type="file" accept=".pdf" onChange={handleFileInput} className="hidden" />

                {file ? (
                  <div className="space-y-2">
                    <svg className="w-12 h-12 mx-auto text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="text-emerald-300 font-medium">{file.name}</p>
                    <p className="text-slate-500 text-sm">{(file.size / 1024).toFixed(1)} KB</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <svg className="w-12 h-12 mx-auto text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    <p className="text-slate-300">Drop a PDF here or click to browse</p>
                    <p className="text-slate-500 text-xs">Pharmaceutical test method PDFs only. Max 50 MB.</p>
                  </div>
                )}
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={handleStartPipeline}
                  disabled={!file || loading}
                  className={`px-6 py-3 rounded-xl font-medium text-sm transition-all ${
                    !file || loading
                      ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                      : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/20'
                  }`}
                >
                  Start Pipeline
                </button>

                {file && (
                  <button
                    onClick={() => {
                      setFile(null);
                      setError(null);
                      if (fileInputRef.current) fileInputRef.current.value = '';
                    }}
                    className="px-6 py-3 rounded-xl font-medium text-sm text-slate-400 hover:text-slate-200 border border-slate-700 hover:border-slate-600 transition-all"
                  >
                    Clear
                  </button>
                )}
              </div>
            </motion.div>
          )}

          {loading && (
            <motion.div key="loading" {...FADE}>
              <div className="max-w-lg mx-auto text-center p-12 rounded-2xl bg-slate-800/50 border border-slate-700/50">
                <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center">
                  <svg className="w-8 h-8 text-emerald-400 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                </div>
                <p className="text-emerald-300 text-lg font-medium">{EXTRACTION_STAGES[extractionStage]}</p>
                <p className="text-slate-500 text-sm mt-2">This may take 30-60 seconds...</p>
                <div className="mt-6 w-full h-1 bg-slate-700 rounded-full overflow-hidden">
                  <div className="h-full w-1/3 bg-emerald-400 rounded-full animate-pulse" />
                </div>
              </div>
            </motion.div>
          )}

          {workflowView === 'classifying' && !loading && (
            <motion.div key="classifying" {...FADE}>
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2">
                  <ClassificationPanel
                    detectedType={classification.detectedType}
                    confidence={classification.confidence}
                    method={classification.method}
                    evidence={classification.evidence}
                    options={classification.options}
                    onConfirm={moveToTemplatePreview}
                    onOverride={moveToTemplatePreview}
                  />
                </div>
                <PipelineStageDetail stages={stageDetails} />
              </div>
            </motion.div>
          )}

          {workflowView === 'template_preview' && !loading && (
            <motion.div key="template_preview" {...FADE}>
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2">
                  <TemplatePreview fields={templateFields} onContinue={runExtractPipeline} />
                </div>
                <PipelineStageDetail stages={stageDetails} />
              </div>
            </motion.div>
          )}

          {workflowView === 'merging' && !loading && (
            <motion.div key="merging" {...FADE}>
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2">
                  <MergeConflictPanel
                    conflicts={mergeConflicts}
                    onResolve={() => {
                      setWorkflowView('review');
                    }}
                  />
                </div>
                <PipelineStageDetail stages={stageDetails} />
              </div>
            </motion.div>
          )}

          {workflowView === 'review' && !loading && mdaData && (
            <motion.div key="review" {...FADE}>
              <div className="flex flex-wrap items-center gap-4 p-4 mb-6 rounded-xl bg-slate-800/50 border border-slate-700/50">
                <span className="text-slate-300 text-sm">
                  <span className="text-slate-500">File:</span> {pdfFilename}
                </span>
                <span className="text-slate-600">|</span>
                <span className="text-slate-300 text-sm">
                  <span className="text-slate-500">Size:</span> {(sizeBytes / 1024).toFixed(1)} KB
                </span>
                <span className="text-slate-600">|</span>
                {validated ? (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/15 text-emerald-400 border border-emerald-500/25">
                    Schema Validated
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-amber-500/15 text-amber-400 border border-amber-500/25">
                    Validation Warning
                  </span>
                )}
              </div>

              {validationError && (
                <div className="mb-6 p-4 rounded-xl bg-amber-500/10 border border-amber-500/20">
                  <p className="text-amber-400 text-sm font-medium mb-1">Validation Details</p>
                  <div className="max-h-48 overflow-y-auto">
                    <p className="text-amber-300/80 text-xs font-mono whitespace-pre-wrap">{validationError}</p>
                  </div>
                </div>
              )}

              <div className="mb-4 flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-500/5 border border-emerald-500/15">
                <svg className="w-4 h-4 text-emerald-400/70 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
                <p className="text-xs text-emerald-400/70">
                  AI structured this data from your PDF. Review each field, then approve or request changes. Final authority is yours.
                </p>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
                <div className="lg:col-span-3 space-y-4">
                  <MDAViewer data={mdaData} validated={validated} title="MDA Template (Review Mode)" provenanceMap={provenanceMap} />

                  {backendStatus !== 'APPROVED' ? (
                    <>
                      {!validated && (
                        <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/25">
                          <p className="text-red-400 text-sm font-medium">
                            Approval blocked: fix validation errors via chat before approving.
                          </p>
                        </div>
                      )}
                      <button
                        onClick={handleApprove}
                        disabled={approveLoading || !validated}
                        className="w-full px-6 py-3 rounded-xl font-medium text-sm bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/20 transition-all disabled:bg-slate-700 disabled:text-slate-500 disabled:cursor-not-allowed"
                      >
                        {approveLoading ? 'Approving...' : 'Approve MDA Template'}
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={handleExport}
                      className="w-full px-6 py-3 rounded-xl font-medium text-sm bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/20 transition-all"
                    >
                      Export XLSX
                    </button>
                  )}
                </div>

                <div className="lg:col-span-2 space-y-4">
                  <PipelineStageDetail stages={stageDetails} />
                  {jobId && <ChatInterface jobId={jobId} onMDAUpdate={handleMDAUpdate} onValidationUpdate={handleValidationUpdate} disabled={false} />}
                </div>
              </div>
            </motion.div>
          )}

          {workflowView === 'done' && !loading && (
            <motion.div key="done" {...FADE}>
              <div className="mb-6 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center gap-4">
                <div className="p-2 bg-emerald-500/20 rounded-lg">
                  <svg className="w-6 h-6 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div>
                  <h4 className="text-emerald-400 font-medium">Pipeline Export Complete</h4>
                  <p className="text-emerald-400/70 text-sm">{pdfFilename?.replace('.pdf', '_MDA.xlsx')} downloaded.</p>
                </div>
              </div>

              {mdaData && <MDAViewer data={mdaData} validated={validated} title="Exported MDA Template" provenanceMap={provenanceMap} />}
            </motion.div>
          )}

          {workflowView === 'failed' && !loading && (
            <motion.div key="failed" {...FADE}>
              <div className="p-6 rounded-xl bg-red-500/10 border border-red-500/30">
                <p className="text-red-400 text-sm font-medium">Pipeline Error</p>
                <p className="text-red-300 text-sm mt-1 font-mono whitespace-pre-wrap">{error}</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {error && workflowView !== 'failed' && workflowView !== 'idle' && !loading && (
          <div className="mt-6 p-4 rounded-xl bg-amber-500/10 border border-amber-500/30">
            <p className="text-amber-400 text-sm font-medium">Warning</p>
            <p className="text-amber-300 text-sm mt-1">{error}</p>
          </div>
        )}

        {error && workflowView === 'idle' && (
          <div className="mt-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30">
            <p className="text-red-400 text-sm font-medium">Error</p>
            <p className="text-red-300 text-sm mt-1">{error}</p>
          </div>
        )}
      </div>
    </>
  );
}

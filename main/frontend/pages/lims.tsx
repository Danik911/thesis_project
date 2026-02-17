import Head from 'next/head';
import { useCallback, useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { getApiBaseUrl } from '@/lib/authenticatedFetch';
import MDAViewer from '@/components/MDAViewer';
import LIMSStepIndicator from '@/components/LIMSStepIndicator';
import ChatInterface from '@/components/ChatInterface';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ExtractResponse {
  job_id: string;
  status: string;
  filename: string;
  size_bytes: number;
  raw_extraction: Record<string, unknown>;
  validated: boolean;
  validation_error?: string | null;
  mda_template: Record<string, unknown> | null;
  mda_generation: Record<string, unknown> | null;
}

type LIMSStatus =
  | 'IDLE'
  | 'EXTRACTING'
  | 'GENERATING'
  | 'PENDING_REVIEW'
  | 'APPROVED'
  | 'EXPORTED'
  | 'FAILED';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const EXTRACTION_STAGES = [
  'Uploading PDF...',
  'Extracting with LlamaExtract...',
  'Validating schema...',
  'Generating MDA template...',
] as const;

const FADE = { initial: { opacity: 0, y: 16 }, animate: { opacity: 1, y: 0 }, exit: { opacity: 0, y: -8 } };

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function LimsPage() {
  // Job tracking
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<LIMSStatus>('IDLE');
  const [pdfFilename, setPdfFilename] = useState<string | null>(null);
  const [sizeBytes, setSizeBytes] = useState<number>(0);

  // MDA data
  const [mdaData, setMdaData] = useState<Record<string, unknown> | null>(null);
  const [validated, setValidated] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  // UI state
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [loading, setLoading] = useState(false);
  const [extractionStage, setExtractionStage] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [approveLoading, setApproveLoading] = useState(false);

  // Refs
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ---------------------------------------------------------------------------
  // Animated extraction stages (during synchronous POST)
  // ---------------------------------------------------------------------------

  useEffect(() => {
    if (!loading) {
      setExtractionStage(0);
      return;
    }
    const timers = [
      setTimeout(() => setExtractionStage(1), 2000),
      setTimeout(() => setExtractionStage(2), 30000),
      setTimeout(() => setExtractionStage(3), 45000),
    ];
    return () => timers.forEach(clearTimeout);
  }, [loading]);

  // ---------------------------------------------------------------------------
  // Defensive status polling (for EXTRACTING/GENERATING robustness)
  // ---------------------------------------------------------------------------

  useEffect(() => {
    if (!jobId || !['EXTRACTING', 'GENERATING'].includes(jobStatus)) {
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
        const data = await res.json();
        setJobStatus(data.status as LIMSStatus);
        if (data.mda_template) setMdaData(data.mda_template);
        if (data.error) setError(data.error);
      } catch {
        // Silent for polling
      }
    }, 3000);

    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [jobId, jobStatus]);

  // ---------------------------------------------------------------------------
  // File handlers (preserved from original)
  // ---------------------------------------------------------------------------

  const handleFile = useCallback((f: File) => {
    if (!f.name.toLowerCase().endsWith('.pdf')) {
      setError('Only PDF files are accepted.');
      return;
    }
    setFile(f);
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

  // ---------------------------------------------------------------------------
  // Extract handler
  // ---------------------------------------------------------------------------

  const handleExtract = useCallback(async () => {
    if (!file) return;

    setLoading(true);
    setError(null);
    setJobId(null);
    setMdaData(null);
    setJobStatus('EXTRACTING');

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
      setValidated(data.validated);
      setValidationError(data.validation_error ?? null);

      // Use validated MDA if available, otherwise raw extraction
      const mda = data.mda_template ?? data.raw_extraction;
      setMdaData(mda as Record<string, unknown>);
      setJobStatus(data.status as LIMSStatus);

      // Warn if generation failed but extraction succeeded
      if (data.mda_generation && 'generation_error' in data.mda_generation) {
        setError(`MDA generation warning: ${(data.mda_generation as Record<string, string>).generation_error}`);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message);
      setJobStatus('FAILED');
    } finally {
      setLoading(false);
    }
  }, [file]);

  // ---------------------------------------------------------------------------
  // Approve handler
  // ---------------------------------------------------------------------------

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

      const data = await response.json();
      setJobStatus(data.status as LIMSStatus);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message);
    } finally {
      setApproveLoading(false);
    }
  }, [jobId]);

  // ---------------------------------------------------------------------------
  // Export handler
  // ---------------------------------------------------------------------------

  const handleExport = useCallback(() => {
    if (!jobId) return;
    const baseUrl = getApiBaseUrl();
    window.open(`${baseUrl}/lims/export/${jobId}`, '_blank');
    setJobStatus('EXPORTED');
  }, [jobId]);

  // ---------------------------------------------------------------------------
  // MDA update handler (from ChatInterface edits)
  // ---------------------------------------------------------------------------

  const handleMDAUpdate = useCallback((updatedMDA: Record<string, unknown>) => {
    setMdaData(updatedMDA);
  }, []);

  // ---------------------------------------------------------------------------
  // Start over
  // ---------------------------------------------------------------------------

  const handleStartOver = useCallback(() => {
    setFile(null);
    setJobId(null);
    setJobStatus('IDLE');
    setMdaData(null);
    setValidated(false);
    setValidationError(null);
    setError(null);
    setPdfFilename(null);
    setSizeBytes(0);
    setApproveLoading(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
    if (pollRef.current) clearInterval(pollRef.current);
  }, []);

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <>
      <Head>
        <title>LIMS - MDA Extraction | AI4LIMS</title>
      </Head>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="mb-8 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 bg-emerald-600/20 rounded-xl flex items-center justify-center border border-emerald-500/30">
                <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 to-teal-300">
                  MDA Extraction
                </h1>
                <p className="text-sm text-slate-400">AI4LIMS PoC</p>
              </div>
            </div>
            <p className="text-slate-400 text-sm max-w-2xl">
              Upload a pharmaceutical test method PDF to extract structured MDA data, review with AI chat, approve, and export as XLSX.
            </p>
          </div>

          {jobStatus !== 'IDLE' && !loading && (
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

        {/* Step indicator (visible when job exists) */}
        {jobStatus !== 'IDLE' && (
          <div className="mb-8">
            <LIMSStepIndicator currentStatus={loading ? (extractionStage >= 3 ? 'GENERATING' : 'EXTRACTING') : jobStatus} />
          </div>
        )}

        <AnimatePresence mode="wait">
          {/* ================================================================
              VIEW 1: Upload area (IDLE)
              ================================================================ */}
          {jobStatus === 'IDLE' && !loading && (
            <motion.div key="upload" {...FADE}>
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
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf"
                  onChange={handleFileInput}
                  className="hidden"
                />

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

              {/* Action buttons */}
              <div className="flex gap-3 mt-6">
                <button
                  onClick={handleExtract}
                  disabled={!file || loading}
                  className={`px-6 py-3 rounded-xl font-medium text-sm transition-all ${
                    !file || loading
                      ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                      : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/20'
                  }`}
                >
                  Extract MDA Data
                </button>

                {file && (
                  <button
                    onClick={() => { setFile(null); setError(null); if (fileInputRef.current) fileInputRef.current.value = ''; }}
                    className="px-6 py-3 rounded-xl font-medium text-sm text-slate-400 hover:text-slate-200 border border-slate-700 hover:border-slate-600 transition-all"
                  >
                    Clear
                  </button>
                )}
              </div>
            </motion.div>
          )}

          {/* ================================================================
              VIEW 2: Loading animation (during extract POST)
              ================================================================ */}
          {loading && (
            <motion.div key="loading" {...FADE}>
              <div className="max-w-lg mx-auto text-center p-12 rounded-2xl bg-slate-800/50 border border-slate-700/50">
                <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center">
                  <svg className="w-8 h-8 text-emerald-400 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                </div>
                <p className="text-emerald-300 text-lg font-medium">
                  {EXTRACTION_STAGES[extractionStage]}
                </p>
                <p className="text-slate-500 text-sm mt-2">
                  This may take 30-60 seconds...
                </p>
                <div className="mt-6 w-full h-1 bg-slate-700 rounded-full overflow-hidden">
                  <div className="h-full w-1/3 bg-emerald-400 rounded-full animate-pulse" />
                </div>
              </div>
            </motion.div>
          )}

          {/* ================================================================
              VIEW 3: Review & Chat (PENDING_REVIEW)
              ================================================================ */}
          {jobStatus === 'PENDING_REVIEW' && !loading && mdaData && (
            <motion.div key="review" {...FADE}>
              {/* Summary bar */}
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
                    <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    Schema Validated
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-amber-500/15 text-amber-400 border border-amber-500/25">
                    <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    Validation Warning
                  </span>
                )}
              </div>

              {validationError && (
                <div className="mb-6 p-4 rounded-xl bg-amber-500/10 border border-amber-500/20">
                  <p className="text-amber-400 text-sm font-medium mb-1">Validation Details</p>
                  <p className="text-amber-300/80 text-xs font-mono whitespace-pre-wrap">{validationError}</p>
                </div>
              )}

              {/* Two-column layout: MDA viewer (left) + Chat (right) */}
              <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
                {/* Left column: MDA Table + Approve */}
                <div className="lg:col-span-3 space-y-4">
                  <MDAViewer
                    data={mdaData}
                    validated={validated}
                    title="MDA Template (Review Mode)"
                  />

                  <button
                    onClick={handleApprove}
                    disabled={approveLoading}
                    className="w-full px-6 py-3 rounded-xl font-medium text-sm bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/20 transition-all disabled:bg-slate-700 disabled:text-slate-500 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {approveLoading ? (
                      <>
                        <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                        Approving...
                      </>
                    ) : (
                      <>
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        Approve MDA Template
                      </>
                    )}
                  </button>

                  <p className="text-xs text-slate-500 text-center">
                    Review the MDA table and chat with AI before approving. This action cannot be undone.
                  </p>
                </div>

                {/* Right column: Chat Interface */}
                <div className="lg:col-span-2">
                  <ChatInterface
                    jobId={jobId!}
                    onMDAUpdate={handleMDAUpdate}
                    disabled={false}
                  />
                </div>
              </div>
            </motion.div>
          )}

          {/* ================================================================
              VIEW 4: Approved (APPROVED)
              ================================================================ */}
          {jobStatus === 'APPROVED' && !loading && (
            <motion.div key="approved" {...FADE}>
              <div className="mb-6 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center gap-4">
                <div className="p-2 bg-emerald-500/20 rounded-lg">
                  <svg className="w-6 h-6 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <h4 className="text-emerald-400 font-medium">MDA Template Approved</h4>
                  <p className="text-emerald-400/70 text-sm">Human review completed. Ready for XLSX export.</p>
                </div>
              </div>

              {mdaData && (
                <MDAViewer data={mdaData} validated={validated} title="Approved MDA Template" />
              )}

              <div className="mt-6 flex justify-center">
                <button
                  onClick={handleExport}
                  className="px-8 py-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl font-medium text-sm transition-all shadow-lg shadow-emerald-600/20 flex items-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Download XLSX
                </button>
              </div>
            </motion.div>
          )}

          {/* ================================================================
              VIEW 5: Exported (EXPORTED)
              ================================================================ */}
          {jobStatus === 'EXPORTED' && !loading && (
            <motion.div key="exported" {...FADE}>
              <div className="mb-6 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center gap-4">
                <div className="p-2 bg-emerald-500/20 rounded-lg">
                  <svg className="w-6 h-6 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div>
                  <h4 className="text-emerald-400 font-medium">XLSX Exported Successfully</h4>
                  <p className="text-emerald-400/70 text-sm">
                    {pdfFilename?.replace('.pdf', '_MDA.xlsx')} has been downloaded.
                  </p>
                </div>
              </div>

              {mdaData && (
                <MDAViewer data={mdaData} validated={validated} title="Exported MDA Template" />
              )}

              <div className="mt-6 flex justify-center gap-3">
                <button
                  onClick={handleExport}
                  className="px-6 py-3 rounded-xl font-medium text-sm text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/10 transition-all flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  Download Again
                </button>
              </div>
            </motion.div>
          )}

          {/* ================================================================
              VIEW 6: Failed (FAILED)
              ================================================================ */}
          {jobStatus === 'FAILED' && !loading && (
            <motion.div key="failed" {...FADE}>
              <div className="p-6 rounded-xl bg-red-500/10 border border-red-500/30">
                <p className="text-red-400 text-sm font-medium">Extraction Error</p>
                <p className="text-red-300 text-sm mt-1 font-mono whitespace-pre-wrap">{error}</p>
                <p className="text-red-200/80 text-xs mt-2">
                  Confirm the API is reachable at port 8080 and that your LIMS extraction keys are present in
                  <span className="font-mono"> .env.local</span>.
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Non-fatal error/warning display (visible in any non-FAILED state) */}
        {error && jobStatus !== 'FAILED' && jobStatus !== 'IDLE' && !loading && (
          <div className="mt-6 p-4 rounded-xl bg-amber-500/10 border border-amber-500/30">
            <p className="text-amber-400 text-sm font-medium">Warning</p>
            <p className="text-amber-300 text-sm mt-1">{error}</p>
          </div>
        )}

        {/* IDLE error display */}
        {error && jobStatus === 'IDLE' && (
          <div className="mt-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30">
            <p className="text-red-400 text-sm font-medium">Error</p>
            <p className="text-red-300 text-sm mt-1">{error}</p>
          </div>
        )}
      </div>
    </>
  );
}

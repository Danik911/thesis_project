import Head from 'next/head';
import { useCallback, useEffect, useRef, useState } from 'react';
import { getApiBaseUrl } from '@/lib/authenticatedFetch';
import MDAViewer from '@/components/MDAViewer';

interface ExtractionResult {
  filename: string;
  size_bytes: number;
  raw_extraction: Record<string, unknown>;
  validated: boolean;
  validation_error: string | null;
  mda_template: Record<string, unknown> | null;
}

const EXTRACTION_STAGES = [
  'Uploading PDF...',
  'Extracting with LlamaExtract...',
  'Validating schema...',
] as const;

export default function LimsPage() {
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [loading, setLoading] = useState(false);
  const [extractionStage, setExtractionStage] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ExtractionResult | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!loading) {
      setExtractionStage(0);
      return;
    }

    const timers = [
      setTimeout(() => setExtractionStage(1), 2000),
      setTimeout(() => setExtractionStage(2), 30000),
    ];

    return () => timers.forEach(clearTimeout);
  }, [loading]);

  const handleFile = useCallback((f: File) => {
    if (!f.name.toLowerCase().endsWith('.pdf')) {
      setError('Only PDF files are accepted.');
      return;
    }
    setFile(f);
    setError(null);
    setResult(null);
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

  const handleExtract = useCallback(async () => {
    if (!file) return;

    setLoading(true);
    setError(null);
    setResult(null);

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

      const data: ExtractionResult = await response.json();
      setResult(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [file]);

  const handleClear = useCallback(() => {
    setFile(null);
    setError(null);
    setResult(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  }, []);

  return (
    <>
      <Head>
        <title>LIMS - MDA Extraction | AI4LIMS</title>
      </Head>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="mb-10">
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
            Upload a pharmaceutical test method PDF to extract structured MDA (Method Definition and Analysis) data
            using LlamaExtract. The extracted data is validated against the 4-sheet MDA schema.
          </p>
        </div>

        {/* Upload area */}
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
            {loading ? (
              <span className="flex items-center gap-2">
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                {EXTRACTION_STAGES[extractionStage]}
              </span>
            ) : (
              'Extract MDA Data'
            )}
          </button>

          {(file || result) && (
            <button
              onClick={handleClear}
              disabled={loading}
              className="px-6 py-3 rounded-xl font-medium text-sm text-slate-400 hover:text-slate-200 border border-slate-700 hover:border-slate-600 transition-all"
            >
              Clear
            </button>
          )}
        </div>

        {/* Error display */}
        {error && (
          <div className="mt-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30">
            <p className="text-red-400 text-sm font-medium">Extraction Error</p>
            <p className="text-red-300 text-sm mt-1 font-mono whitespace-pre-wrap">{error}</p>
            <p className="text-red-200/80 text-xs mt-2">
              Confirm the API is reachable at port 8080 and that your LIMS extraction keys are present in
              <span className="font-mono"> .env.local</span>.
            </p>
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="mt-8 space-y-6">
            {/* Summary bar */}
            <div className="flex items-center gap-4 p-4 rounded-xl bg-slate-800/50 border border-slate-700/50">
              <span className="text-slate-300 text-sm">
                <span className="text-slate-500">File:</span> {result.filename}
              </span>
              <span className="text-slate-600">|</span>
              <span className="text-slate-300 text-sm">
                <span className="text-slate-500">Size:</span> {(result.size_bytes / 1024).toFixed(1)} KB
              </span>
              <span className="text-slate-600">|</span>
              {result.validated ? (
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
                  Validation Failed
                </span>
              )}
            </div>

            {/* Validation error detail */}
            {result.validation_error && (
              <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20">
                <p className="text-amber-400 text-sm font-medium mb-1">Validation Details</p>
                <p className="text-amber-300/80 text-xs font-mono whitespace-pre-wrap">{result.validation_error}</p>
              </div>
            )}

            <MDAViewer
              data={
                result.validated && result.mda_template
                  ? result.mda_template
                  : result.raw_extraction
              }
              validated={result.validated}
            />
          </div>
        )}
      </div>
    </>
  );
}

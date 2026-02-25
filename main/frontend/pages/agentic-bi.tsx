import Head from 'next/head';
import { useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';

import DataGrid from '@/components/bi/DataGrid';
import Sidebar from '@/components/bi/Sidebar';
import { getApiBaseUrl } from '@/lib/authenticatedFetch';
import type { BIColumn, BIDataResponse, BIFilterDef, BIFilterResponse, BIUploadResponse } from '@/types/bi';

const PAGE_SIZE = 15000;
const FADE = { initial: { opacity: 0, y: 16 }, animate: { opacity: 1, y: 0 }, exit: { opacity: 0, y: -8 } };

export default function AgenticBIPage() {
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [sessionId, setSessionId] = useState<string | null>(null);
  const [filename, setFilename] = useState('');
  const [columns, setColumns] = useState<BIColumn[]>([]);
  const [rows, setRows] = useState<Array<Record<string, unknown>>>([]);
  const [totalRows, setTotalRows] = useState(0);
  const [totalFilteredRows, setTotalFilteredRows] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [activeFilters, setActiveFilters] = useState<BIFilterDef[]>([]);
  const [visibleColumns, setVisibleColumns] = useState<string[]>([]);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const resetToIdle = () => {
    setFile(null);
    setSessionId(null);
    setFilename('');
    setColumns([]);
    setRows([]);
    setTotalRows(0);
    setTotalFilteredRows(0);
    setPage(1);
    setTotalPages(1);
    setActiveFilters([]);
    setVisibleColumns([]);
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const loadPage = async (targetPage: number, targetSessionId?: string) => {
    const activeSessionId = targetSessionId ?? sessionId;
    if (!activeSessionId) return;

    const response = await fetch(
      `${getApiBaseUrl()}/bi/data/${activeSessionId}?page=${targetPage}&page_size=${PAGE_SIZE}`
    );

    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body?.detail ?? `Failed to fetch data page (${response.status})`);
    }

    const payload: BIDataResponse = await response.json();
    setRows(payload.rows);
    setTotalRows(payload.total_rows);
    setTotalFilteredRows(payload.total_filtered_rows);
    setPage(payload.page);
    setTotalPages(payload.total_pages);
    setActiveFilters(payload.active_filters ?? []);
  };

  const handleUpload = async () => {
    if (!file) return;

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${getApiBaseUrl()}/bi/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body?.detail ?? `Upload failed (${response.status})`);
      }

      const payload: BIUploadResponse = await response.json();

      setSessionId(payload.session_id);
      setFilename(payload.filename);
      setColumns(payload.columns);
      setVisibleColumns(payload.columns.map((column) => column.name));
      setRows(payload.preview.rows);
      setTotalRows(payload.total_rows);
      setTotalFilteredRows(payload.preview.total_filtered_rows);
      setPage(payload.preview.page);
      setTotalPages(payload.preview.total_pages);
      setActiveFilters(payload.preview.active_filters ?? []);
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : 'Upload failed');
    } finally {
      setLoading(false);
    }
  };

  const handleFileInput = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files?.[0];
    if (!selected) return;
    setFile(selected);
    setError(null);
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragOver(false);

    const dropped = event.dataTransfer.files?.[0];
    if (!dropped) return;

    setFile(dropped);
    setError(null);
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragOver(false);
  };

  const handleDropzoneKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      fileInputRef.current?.click();
    }
  };

  const isLoaded = Boolean(sessionId);

  const handleFiltersChange = async (filters: BIFilterDef[]) => {
    if (!sessionId) return;

    setError(null);

    try {
      const response = await fetch(`${getApiBaseUrl()}/bi/filter/${sessionId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ filters }),
      });

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body?.detail ?? `Failed to apply filters (${response.status})`);
      }

      const payload: BIFilterResponse = await response.json();
      setActiveFilters(payload.active_filters);
      await loadPage(1);
    } catch (filterError) {
      setError(filterError instanceof Error ? filterError.message : 'Failed to apply filters');
    }
  };

  return (
    <>
      <Head>
        <title>MES Agentic BI</title>
      </Head>

      <div className="min-h-screen bg-slate-950 text-slate-100 px-6 py-10">
        <div className="max-w-7xl mx-auto">
          <div className="mb-8 flex items-end justify-between gap-4">
            <div>
              <h1 className="text-3xl md:text-4xl font-bold text-cyan-300" style={{ fontFamily: 'var(--font-display)' }}>
                MES Agentic BI for PPRS
              </h1>
              <p className="text-sm text-slate-400 mt-2">Upload XLSX/CSV data and explore it in the BI grid.</p>
            </div>

            {isLoaded && (
              <button
                type="button"
                onClick={resetToIdle}
                className="px-4 py-2 rounded-xl text-sm font-medium text-slate-300 border border-slate-700 hover:border-slate-600"
              >
                Start Over
              </button>
            )}
          </div>

          <AnimatePresence mode="wait">
            {!isLoaded ? (
              <motion.div key="upload" {...FADE}>
                <div
                  onDrop={handleDrop}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onClick={() => fileInputRef.current?.click()}
                  onKeyDown={handleDropzoneKeyDown}
                  role="button"
                  tabIndex={0}
                  className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all ${
                    dragOver
                      ? 'border-cyan-400 bg-cyan-500/10'
                      : file
                        ? 'border-cyan-500/40 bg-cyan-500/5'
                        : 'border-slate-600 hover:border-cyan-500/50 hover:bg-slate-900'
                  }`}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".xlsx,.csv"
                    onChange={handleFileInput}
                    className="hidden"
                  />

                  {file ? (
                    <div className="space-y-2">
                      <p className="text-cyan-300 font-medium">{file.name}</p>
                      <p className="text-slate-500 text-sm">{(file.size / 1024).toFixed(1)} KB</p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <p className="text-slate-300">Drop an XLSX/CSV file here or click to browse</p>
                      <p className="text-slate-500 text-xs">Supports dynamic schemas up to configured upload limits.</p>
                    </div>
                  )}
                </div>

                <div className="mt-6 flex items-center gap-3">
                  <button
                    type="button"
                    onClick={handleUpload}
                    disabled={!file || loading}
                    className={`px-6 py-3 rounded-xl text-sm font-medium transition-all ${
                      !file || loading
                        ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                        : 'bg-cyan-600 hover:bg-cyan-500 text-white'
                    }`}
                  >
                    {loading ? 'Uploading...' : 'Upload and Load Grid'}
                  </button>

                  {file && (
                    <button
                      type="button"
                      onClick={resetToIdle}
                      className="px-6 py-3 rounded-xl text-sm font-medium text-slate-300 border border-slate-700 hover:border-slate-600"
                    >
                      Clear
                    </button>
                  )}
                </div>
              </motion.div>
            ) : (
              <motion.div key="grid" {...FADE}>
                <div className="grid grid-cols-1 lg:grid-cols-[320px_minmax(0,1fr)] gap-6">
                  <Sidebar
                    filename={filename}
                    fields={columns}
                    activeFilters={activeFilters}
                    onFiltersChange={handleFiltersChange}
                    onRemove={resetToIdle}
                  />

                  <DataGrid
                    columns={columns.map((column) => column.name)}
                    visibleColumns={visibleColumns}
                    onVisibleColumnsChange={setVisibleColumns}
                    data={rows}
                    totalRows={totalRows}
                    totalFilteredRows={totalFilteredRows}
                    page={page}
                    pageSize={PAGE_SIZE}
                    totalPages={totalPages}
                    onPageChange={(nextPage) => {
                      if (nextPage < 1 || nextPage > totalPages) return;
                      loadPage(nextPage).catch((pageError) => {
                        setError(pageError instanceof Error ? pageError.message : 'Failed to fetch page');
                      });
                    }}
                  />
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {error && (
            <div className="mt-6 rounded-xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
              {error}
            </div>
          )}
        </div>
      </div>
    </>
  );
}

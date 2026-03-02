import { useState } from 'react';

import ColumnSelector from '@/components/bi/ColumnSelector';
import { authenticatedFetch } from '@/lib/authenticatedFetch';

interface ExportButtonsProps {
  sessionId: string;
  columns: string[];
  visibleColumns: string[];
  onVisibleColumnsChange: (columns: string[]) => void;
  totalFilteredRows: number;
  getAccessToken: () => Promise<string | null>;
}

export default function ExportButtons({
  sessionId,
  columns,
  visibleColumns,
  onVisibleColumnsChange,
  totalFilteredRows,
  getAccessToken,
}: ExportButtonsProps) {
  const [exporting, setExporting] = useState<string | null>(null);

  const handleExport = async (format: 'excel' | 'pdf') => {
    setExporting(format);
    try {
      const response = await authenticatedFetch(
        `/bi/export/${format}/${sessionId}`,
        getAccessToken,
      );

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error((body as { detail?: string }).detail || `Export failed (${response.status})`);
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `export.${format === 'excel' ? 'xlsx' : 'pdf'}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export failed:', err);
    } finally {
      setExporting(null);
    }
  };

  return (
    <div className="flex flex-wrap items-center justify-end gap-2">
      <p className="text-xs text-slate-400 mr-1">Exporting {totalFilteredRows} rows</p>

      <ColumnSelector columns={columns} visibleColumns={visibleColumns} onChange={onVisibleColumnsChange} />

      <button
        type="button"
        onClick={() => handleExport('excel')}
        disabled={exporting !== null}
        className="px-3 py-1.5 text-xs rounded-md border border-slate-700 text-slate-200 hover:border-slate-600 disabled:opacity-50"
      >
        {exporting === 'excel' ? 'Exporting...' : 'Excel'}
      </button>

      <button
        type="button"
        onClick={() => handleExport('pdf')}
        disabled={exporting !== null}
        className="px-3 py-1.5 text-xs rounded-md border border-slate-700 text-slate-200 hover:border-slate-600 disabled:opacity-50"
      >
        {exporting === 'pdf' ? 'Exporting...' : 'PDF'}
      </button>
    </div>
  );
}

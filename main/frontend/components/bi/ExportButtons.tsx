import ColumnSelector from '@/components/bi/ColumnSelector';
import { getApiBaseUrl } from '@/lib/authenticatedFetch';

interface ExportButtonsProps {
  sessionId: string;
  columns: string[];
  visibleColumns: string[];
  onVisibleColumnsChange: (columns: string[]) => void;
  totalFilteredRows: number;
}

export default function ExportButtons({
  sessionId,
  columns,
  visibleColumns,
  onVisibleColumnsChange,
  totalFilteredRows,
}: ExportButtonsProps) {
  const openExport = (format: 'excel' | 'pdf') => {
    const url = `${getApiBaseUrl()}/bi/export/${format}/${sessionId}`;
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  return (
    <div className="flex flex-wrap items-center justify-end gap-2">
      <p className="text-xs text-slate-400 mr-1">Exporting {totalFilteredRows} rows</p>

      <ColumnSelector columns={columns} visibleColumns={visibleColumns} onChange={onVisibleColumnsChange} />

      <button
        type="button"
        onClick={() => openExport('excel')}
        className="px-3 py-1.5 text-xs rounded-md border border-slate-700 text-slate-200 hover:border-slate-600"
      >
        Excel
      </button>

      <button
        type="button"
        onClick={() => openExport('pdf')}
        className="px-3 py-1.5 text-xs rounded-md border border-slate-700 text-slate-200 hover:border-slate-600"
      >
        PDF
      </button>
    </div>
  );
}

import { useMemo } from 'react';
import {
  flexRender,
  getCoreRowModel,
  useReactTable,
  type ColumnDef,
} from '@tanstack/react-table';

interface DataGridProps {
  columns: string[];
  data: Array<Record<string, unknown>>;
  totalRows: number;
  page: number;
  pageSize: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export default function DataGrid({
  columns,
  data,
  totalRows,
  page,
  pageSize,
  totalPages,
  onPageChange,
}: DataGridProps) {
  const tableColumns = useMemo<ColumnDef<Record<string, unknown>>[]>(
    () =>
      columns.map((column) => ({
        accessorKey: column,
        header: column,
        cell: (info) => {
          const value = info.getValue();
          if (value === null || value === undefined) return '—';
          return String(value);
        },
      })),
    [columns]
  );

  const table = useReactTable({
    data,
    columns: tableColumns,
    getCoreRowModel: getCoreRowModel(),
  });

  const start = totalRows === 0 ? 0 : (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, totalRows);

  return (
    <div className="rounded-2xl border border-slate-700/50 bg-slate-900 overflow-hidden">
      <div className="overflow-auto max-h-[72vh]">
        <table className="min-w-full text-sm">
          <thead className="sticky top-0 z-10 bg-slate-900 border-b border-slate-700/50">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    className="px-3 py-2 text-left text-xs uppercase tracking-wide text-slate-300 whitespace-nowrap"
                  >
                    {header.isPlaceholder
                      ? null
                      : flexRender(header.column.columnDef.header, header.getContext())}
                  </th>
                ))}
              </tr>
            ))}
          </thead>

          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr key={row.id} className="border-b border-slate-800/80 hover:bg-slate-800/50">
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-3 py-2 text-slate-200 whitespace-nowrap">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}

            {data.length === 0 && (
              <tr>
                <td className="px-3 py-8 text-center text-slate-400" colSpan={Math.max(columns.length, 1)}>
                  No rows to display.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between px-4 py-3 border-t border-slate-700/50 bg-slate-900">
        <p className="text-xs text-slate-400">
          Showing {start}-{end} of {totalRows} rows
        </p>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            className="px-3 py-1.5 text-xs rounded-md border border-slate-700 text-slate-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          <span className="text-xs text-slate-300">
            Page {page} / {Math.max(totalPages, 1)}
          </span>
          <button
            type="button"
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
            className="px-3 py-1.5 text-xs rounded-md border border-slate-700 text-slate-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}

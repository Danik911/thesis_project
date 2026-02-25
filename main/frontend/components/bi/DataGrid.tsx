import { useMemo, useRef } from 'react';
import {
  flexRender,
  getCoreRowModel,
  type VisibilityState,
  useReactTable,
  type ColumnDef,
} from '@tanstack/react-table';
import { useVirtualizer } from '@tanstack/react-virtual';

interface DataGridProps {
  columns: string[];
  visibleColumns: string[];
  onVisibleColumnsChange: (columns: string[]) => void;
  data: Array<Record<string, unknown>>;
  totalRows: number;
  totalFilteredRows: number;
  page: number;
  pageSize: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export default function DataGrid({
  columns,
  visibleColumns,
  onVisibleColumnsChange,
  data,
  totalRows,
  totalFilteredRows,
  page,
  pageSize,
  totalPages,
  onPageChange,
}: DataGridProps) {
  const parentRef = useRef<HTMLDivElement>(null);

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

  const columnVisibility = useMemo<VisibilityState>(() => {
    const visible = new Set(visibleColumns);
    return Object.fromEntries(columns.map((column) => [column, visible.has(column)]));
  }, [columns, visibleColumns]);

  const table = useReactTable({
    data,
    columns: tableColumns,
    state: {
      columnVisibility,
    },
    onColumnVisibilityChange: (updater) => {
      const current: VisibilityState = { ...columnVisibility };
      const next = typeof updater === 'function' ? updater(current) : updater;
      const orderedVisible = columns.filter((column) => next[column] !== false);
      if (orderedVisible.length > 0) {
        onVisibleColumnsChange(orderedVisible);
      }
    },
    getCoreRowModel: getCoreRowModel(),
  });

  const tableRows = table.getRowModel().rows;

  const rowVirtualizer = useVirtualizer({
    count: tableRows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 36,
    overscan: 10,
  });

  const virtualRows = rowVirtualizer.getVirtualItems();

  const start = totalFilteredRows === 0 ? 0 : (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, totalFilteredRows);

  return (
    <div className="rounded-2xl border border-slate-700/50 bg-slate-900 overflow-hidden">
      <div ref={parentRef} className="overflow-auto" style={{ height: 'calc(100vh - 270px)' }}>
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

          <tbody className="relative block" style={{ height: `${rowVirtualizer.getTotalSize()}px` }}>
            {virtualRows.map((virtualRow) => {
              const row = tableRows[virtualRow.index];
              if (!row) return null;

              return (
                <tr
                  key={row.id}
                  className="absolute left-0 w-full border-b border-slate-800/80 hover:bg-slate-800/50"
                  style={{ transform: `translateY(${virtualRow.start}px)` }}
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-3 py-2 text-slate-200 whitespace-nowrap">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              );
            })}

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
          Showing {start}-{end} of {totalFilteredRows} rows (from {totalRows})
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

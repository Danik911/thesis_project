import { useMemo, useRef, useState } from 'react';
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
  const [search, setSearch] = useState('');

  const filteredData = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return data;
    return data.filter((row) =>
      Object.values(row).some((val) => val != null && String(val).toLowerCase().includes(query))
    );
  }, [data, search]);

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
    data: filteredData,
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

  const visibleColumnCount = table.getVisibleLeafColumns().length;
  const colWidth = visibleColumnCount > 0 ? `${100 / visibleColumnCount}%` : 'auto';

  const start = totalFilteredRows === 0 ? 0 : (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, totalFilteredRows);

  return (
    <div className="rounded-2xl border border-slate-700/50 bg-slate-900 overflow-hidden">
      {/* Quick search bar */}
      <div className="px-4 py-2 border-b border-slate-700/50 flex items-center gap-2">
        <svg className="w-4 h-4 text-slate-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Quick search across all columns..."
          className="flex-1 bg-transparent text-sm text-slate-200 placeholder-slate-500 focus:outline-none"
        />
        {search && (
          <button
            type="button"
            onClick={() => setSearch('')}
            className="text-xs text-slate-500 hover:text-slate-300"
          >
            Clear
          </button>
        )}
      </div>
      <div ref={parentRef} className="overflow-auto" style={{ height: 'calc(100vh - 230px)' }}>
        <table className="min-w-full text-sm">
          <thead className="sticky top-0 z-10 bg-slate-900 border-b border-slate-700/50 block">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id} className="flex w-full">
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    className="px-3 py-2 text-left text-xs uppercase tracking-wide text-slate-300 whitespace-nowrap overflow-hidden text-ellipsis border-r border-slate-700/30 last:border-r-0"
                    style={{ width: colWidth, minWidth: 0 }}
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
                  className="absolute left-0 w-full flex border-b border-slate-800/80 hover:bg-slate-800/50"
                  style={{ transform: `translateY(${virtualRow.start}px)` }}
                >
                  {row.getVisibleCells().map((cell) => (
                    <td
                      key={cell.id}
                      className="px-3 py-2 text-slate-200 whitespace-nowrap overflow-hidden text-ellipsis border-r border-slate-700/30 last:border-r-0"
                      style={{ width: colWidth, minWidth: 0 }}
                    >
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              );
            })}

            {filteredData.length === 0 && (
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
          {search.trim()
            ? `Search: ${filteredData.length} matches in ${totalFilteredRows} rows`
            : `Showing ${start}-${end} of ${totalFilteredRows} rows (from ${totalRows})`}
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

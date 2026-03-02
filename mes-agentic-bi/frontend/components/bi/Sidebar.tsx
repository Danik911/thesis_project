import { useMemo, useState } from 'react';

import type { BIColumn } from '@/types/bi';
import type { BIFilterDef } from '@/types/bi';

interface SidebarProps {
  filename: string;
  fields: BIColumn[];
  activeFilters: BIFilterDef[];
  onFiltersChange: (filters: BIFilterDef[]) => void;
  onRemove: () => void;
}

function isNumericField(field: BIColumn): boolean {
  const dtype = field.dtype.toLowerCase();
  return (
    dtype.includes('int') ||
    dtype.includes('float') ||
    dtype.includes('double') ||
    dtype.includes('decimal') ||
    dtype.includes('number')
  );
}

export default function Sidebar({ filename, fields, activeFilters, onFiltersChange, onRemove }: SidebarProps) {
  const [expandedField, setExpandedField] = useState<string | null>(null);

  const filtersByColumn = useMemo(() => {
    const next = new Map<string, BIFilterDef>();
    for (const filter of activeFilters) {
      next.set(filter.column, filter);
    }
    return next;
  }, [activeFilters]);

  const upsertFilter = (filter: BIFilterDef) => {
    const next = activeFilters.filter((item) => item.column !== filter.column);
    next.push(filter);
    onFiltersChange(next);
  };

  const removeFilter = (column: string) => {
    onFiltersChange(activeFilters.filter((item) => item.column !== column));
  };

  const updateCategoricalFilter = (column: string, value: string | number | boolean | null, checked: boolean) => {
    const existing = filtersByColumn.get(column);
    let current: Array<string | number> = [];
    if (existing) {
      if (existing.operator === 'in' && Array.isArray(existing.value)) {
        current = existing.value;
      } else if (existing.operator === 'equals' && existing.value != null) {
        current = [String(existing.value)];
      }
    }

    const normalizedValue = value === null ? 'null' : String(value);
    const currentValues = current.map((item) => String(item));
    const nextValues = checked
      ? Array.from(new Set([...currentValues, normalizedValue]))
      : currentValues.filter((item) => item !== normalizedValue);

    if (nextValues.length === 0) {
      removeFilter(column);
      return;
    }

    upsertFilter({
      column,
      operator: 'in',
      value: nextValues,
    });
  };

  const updateNumericFilter = (column: string, minRaw: string, maxRaw: string) => {
    const minVal = minRaw.trim();
    const maxVal = maxRaw.trim();

    if (!minVal && !maxVal) {
      removeFilter(column);
      return;
    }

    if (minVal && maxVal) {
      upsertFilter({
        column,
        operator: 'between',
        value: [Number(minVal), Number(maxVal)],
      });
      return;
    }

    if (minVal) {
      upsertFilter({
        column,
        operator: 'greater_equal',
        value: Number(minVal),
      });
      return;
    }

    upsertFilter({
      column,
      operator: 'less_equal',
      value: Number(maxVal),
    });
  };

  return (
    <aside className="w-full lg:w-72 rounded-2xl border border-slate-700/50 bg-slate-900 p-4">
      <div className="mb-4">
        <div className="rounded-lg border border-slate-700/50 bg-slate-800/60 px-3 py-2">
          <p className="text-xs text-slate-400 truncate">{filename}</p>
        </div>
      </div>

      <div>
        <p className="text-xs uppercase tracking-wide text-slate-400 mb-2">Filters</p>
        <div className="space-y-1.5 max-h-[calc(100vh-180px)] overflow-auto pr-2">
          {fields.map((field) => {
            const isExpanded = expandedField === field.name;
            const activeFilter = filtersByColumn.get(field.name);
            const numeric = isNumericField(field);
            const minValue =
              activeFilter?.operator === 'between' && Array.isArray(activeFilter.value)
                ? String(activeFilter.value[0] ?? '')
                : activeFilter?.operator === 'greater_equal'
                  ? String(activeFilter.value ?? '')
                  : '';
            const maxValue =
              activeFilter?.operator === 'between' && Array.isArray(activeFilter.value)
                ? String(activeFilter.value[1] ?? '')
                : activeFilter?.operator === 'less_equal'
                  ? String(activeFilter.value ?? '')
                  : '';

            return (
              <div key={field.name} className="rounded-lg border border-slate-600/80 bg-slate-800/40">
                <button
                  type="button"
                  onClick={() => setExpandedField((current) => (current === field.name ? null : field.name))}
                  className="w-full px-3 py-2 flex items-center justify-between text-left"
                >
                  <span className="text-xs text-slate-200 break-all pr-2 flex items-center gap-2">
                    {activeFilter && (
                      <span className="inline-block h-2 w-2 rounded-full bg-cyan-400 flex-shrink-0" />
                    )}
                    {field.name}
                  </span>
                  <span className="text-xs text-slate-400">{isExpanded ? '▾' : '▸'}</span>
                </button>

                {isExpanded && (
                  <div className="px-3 pb-3">
                    {numeric ? (
                      <div className="space-y-2">
                        <div className="grid grid-cols-2 gap-2">
                          <input
                            type="number"
                            placeholder="Min"
                            defaultValue={minValue}
                            onBlur={(event) => {
                              const nextMin = event.currentTarget.value;
                              const maxInput = event.currentTarget.parentElement?.querySelector(
                                'input[data-max-input="true"]'
                              ) as HTMLInputElement | null;
                              updateNumericFilter(field.name, nextMin, maxInput?.value ?? '');
                            }}
                            className="w-full rounded-md border border-slate-600 bg-slate-900 px-2 py-1.5 text-sm text-slate-100"
                          />
                          <input
                            type="number"
                            data-max-input="true"
                            placeholder="Max"
                            defaultValue={maxValue}
                            onBlur={(event) => {
                              const nextMax = event.currentTarget.value;
                              const minInput = event.currentTarget.parentElement?.querySelector(
                                'input:not([data-max-input="true"])'
                              ) as HTMLInputElement | null;
                              updateNumericFilter(field.name, minInput?.value ?? '', nextMax);
                            }}
                            className="w-full rounded-md border border-slate-600 bg-slate-900 px-2 py-1.5 text-sm text-slate-100"
                          />
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-2 max-h-52 overflow-auto pr-1">
                        {(() => {
                          // Merge sample values with any actively-filtered values so copilot filters always appear
                          const sampleNormalized = new Set(
                            field.sample_values.map((v) => (v === null ? 'null' : String(v)))
                          );
                          const extraValues: Array<string | number | boolean | null> = [];
                          if (activeFilter) {
                            if (activeFilter.operator === 'equals' && activeFilter.value != null) {
                              const fv = String(activeFilter.value);
                              if (!sampleNormalized.has(fv)) extraValues.push(activeFilter.value as string);
                            } else if (activeFilter.operator === 'in' && Array.isArray(activeFilter.value)) {
                              for (const v of activeFilter.value) {
                                if (!sampleNormalized.has(String(v))) extraValues.push(v);
                              }
                            }
                          }
                          const allValues = [...field.sample_values, ...extraValues];

                          return allValues.map((value) => {
                            const normalizedValue = value === null ? 'null' : String(value);
                            const selected =
                              (activeFilter?.operator === 'in' &&
                                Array.isArray(activeFilter.value) &&
                                activeFilter.value.map((item) => String(item)).includes(normalizedValue)) ||
                              (activeFilter?.operator === 'equals' &&
                                String(activeFilter.value) === normalizedValue) ||
                              (activeFilter?.operator === 'contains' &&
                                normalizedValue.toLowerCase().includes(String(activeFilter.value).toLowerCase()));
                            const count = field.value_counts?.[normalizedValue];
                            const isZeroMatch = selected && count === 0;

                            return (
                              <label
                                key={normalizedValue}
                                className={`flex items-center gap-3 text-sm cursor-pointer ${
                                  isZeroMatch ? 'text-slate-500 line-through' : 'text-slate-200'
                                }`}
                              >
                                <input
                                  type="checkbox"
                                  checked={Boolean(selected)}
                                  onChange={(event) =>
                                    updateCategoricalFilter(field.name, value, event.currentTarget.checked)
                                  }
                                  className="h-4 w-4 rounded border-slate-600 bg-slate-900 text-cyan-500 focus:ring-cyan-500"
                                />
                                <span className="break-all">
                                  {normalizedValue}
                                  {count !== undefined && (
                                    <span className="text-slate-500 ml-1">({count})</span>
                                  )}
                                </span>
                              </label>
                            );
                          });
                        })()}
                        {field.sample_values.length === 0 && !activeFilter && (
                          <p className="text-[11px] text-slate-500">No sample values available.</p>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </aside>
  );
}

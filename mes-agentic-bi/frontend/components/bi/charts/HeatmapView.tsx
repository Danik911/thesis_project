import { useMemo } from 'react';

import type { BIHeatmapCell } from '@/types/bi';

interface HeatmapViewProps {
  data: BIHeatmapCell[];
  xLabel: string;
  yLabel: string;
  valueLabel: string;
}

function interpolateColor(value: number, min: number, max: number): string {
  if (max === min) return 'rgb(6, 182, 212)'; // cyan-500
  const t = (value - min) / (max - min);
  // Interpolate from slate-700 (#334155) to cyan-400 (#22d3ee)
  const r = Math.round(51 + t * (34 - 51));
  const g = Math.round(65 + t * (211 - 65));
  const b = Math.round(85 + t * (238 - 85));
  return `rgb(${r}, ${g}, ${b})`;
}

export default function HeatmapView({ data, xLabel, yLabel, valueLabel }: HeatmapViewProps) {
  const { xValues, yValues, cellMap, minVal, maxVal } = useMemo(() => {
    const xs = [...new Set(data.map((d) => d.x))].sort();
    const ys = [...new Set(data.map((d) => d.y))].sort();
    const map = new Map<string, number>();
    let min = Infinity;
    let max = -Infinity;
    for (const cell of data) {
      const key = `${cell.x}|${cell.y}`;
      map.set(key, cell.value);
      if (cell.value < min) min = cell.value;
      if (cell.value > max) max = cell.value;
    }
    return { xValues: xs, yValues: ys, cellMap: map, minVal: min, maxVal: max };
  }, [data]);

  return (
    <div className="overflow-x-auto">
      <div className="inline-block min-w-full">
        {/* Header row */}
        <div className="flex">
          <div className="w-24 shrink-0 flex items-end justify-end pr-2 pb-1">
            <span className="text-xs text-slate-500">{yLabel} \ {xLabel}</span>
          </div>
          {xValues.map((x) => (
            <div key={x} className="flex-1 min-w-[60px] text-center pb-1">
              <span className="text-xs text-slate-400 font-medium">{x}</span>
            </div>
          ))}
        </div>

        {/* Data rows */}
        {yValues.map((y) => (
          <div key={y} className="flex">
            <div className="w-24 shrink-0 flex items-center justify-end pr-2">
              <span className="text-xs text-slate-400 font-medium">{y}</span>
            </div>
            {xValues.map((x) => {
              const key = `${x}|${y}`;
              const value = cellMap.get(key);
              const hasValue = value !== undefined;
              return (
                <div
                  key={key}
                  className="flex-1 min-w-[60px] h-12 m-0.5 rounded flex items-center justify-center relative group"
                  style={{
                    backgroundColor: hasValue ? interpolateColor(value, minVal, maxVal) : '#1e293b',
                  }}
                >
                  <span className="text-xs font-medium text-white/90">
                    {hasValue ? value.toFixed(1) : '-'}
                  </span>
                  {/* Tooltip on hover */}
                  <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 hidden group-hover:block z-10">
                    <div className="bg-slate-800 border border-slate-600 rounded px-2 py-1 text-xs text-slate-200 whitespace-nowrap">
                      {xLabel}: {x} | {yLabel}: {y} | {valueLabel}: {hasValue ? value.toFixed(2) : 'N/A'}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ))}

        {/* Color legend */}
        <div className="flex items-center gap-2 mt-3 pl-24">
          <span className="text-xs text-slate-500">{minVal.toFixed(1)}</span>
          <div
            className="h-3 flex-1 max-w-[200px] rounded"
            style={{
              background: `linear-gradient(to right, ${interpolateColor(minVal, minVal, maxVal)}, ${interpolateColor(maxVal, minVal, maxVal)})`,
            }}
          />
          <span className="text-xs text-slate-500">{maxVal.toFixed(1)}</span>
          <span className="text-xs text-slate-500 ml-1">({valueLabel})</span>
        </div>
      </div>
    </div>
  );
}

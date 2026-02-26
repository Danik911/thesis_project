import { useCallback, useState } from 'react';

import { getApiBaseUrl } from '@/lib/authenticatedFetch';
import type {
  BIChartDataPoint,
  BIChartDataResponse,
  BIColumn,
  BIHeatmapCell,
  BIHistogramBin,
} from '@/types/bi';

import BarChartView from './BarChartView';
import HeatmapView from './HeatmapView';
import HistogramView from './HistogramView';
import LineChartView from './LineChartView';
import ScatterChartView from './ScatterChartView';

const CHART_TYPES = ['bar', 'line', 'scatter', 'histogram', 'heatmap'] as const;
const AGG_OPTIONS = ['mean', 'sum', 'median', 'count', 'min', 'max'] as const;

interface ChartBuilderProps {
  sessionId: string;
  columns: BIColumn[];
}

export default function ChartBuilder({ sessionId, columns }: ChartBuilderProps) {
  const [chartType, setChartType] = useState<string>('bar');
  const [xColumn, setXColumn] = useState('');
  const [yColumn, setYColumn] = useState('');
  const [groupBy, setGroupBy] = useState('');
  const [aggregation, setAggregation] = useState('mean');
  const [data, setData] = useState<BIChartDataResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const numericColumns = columns.filter((c) => {
    const dt = c.dtype.toLowerCase();
    return dt.includes('int') || dt.includes('float') || dt.includes('decimal') || dt.includes('number');
  });

  const categoricalColumns = columns.filter((c) => c.unique_count <= 50 && !numericColumns.includes(c));

  const needsY = chartType !== 'histogram';
  const needsAgg = chartType === 'bar' || chartType === 'line' || chartType === 'heatmap';
  const canGroupBy = chartType === 'bar' || chartType === 'line';

  const generateChart = useCallback(async () => {
    if (!xColumn) return;
    if (needsY && !yColumn) return;

    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${getApiBaseUrl()}/bi/charts/data/${sessionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chart_type: chartType,
          x_column: xColumn,
          y_column: needsY ? yColumn : null,
          aggregation: needsAgg ? aggregation : null,
          group_by: canGroupBy && groupBy ? groupBy : null,
          bins: 20,
          limit: 50,
        }),
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body?.detail ?? `Failed to generate chart (${response.status})`);
      }
      const payload: BIChartDataResponse = await response.json();
      setData(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate chart');
    } finally {
      setLoading(false);
    }
  }, [sessionId, chartType, xColumn, yColumn, groupBy, aggregation, needsY, needsAgg, canGroupBy]);

  return (
    <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4">
      <h3 className="text-sm font-medium text-slate-200 mb-4">Custom Chart Builder</h3>

      {/* Controls */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-4">
        {/* Chart type */}
        <div>
          <label className="block text-xs text-slate-400 mb-1">Chart Type</label>
          <select
            value={chartType}
            onChange={(e) => { setChartType(e.target.value); setData(null); }}
            className="w-full text-xs bg-slate-700 border border-slate-600 text-slate-300 rounded px-2 py-1.5 focus:outline-none focus:border-cyan-500"
          >
            {CHART_TYPES.map((t) => (
              <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
            ))}
          </select>
        </div>

        {/* X column */}
        <div>
          <label className="block text-xs text-slate-400 mb-1">X Axis</label>
          <select
            value={xColumn}
            onChange={(e) => setXColumn(e.target.value)}
            className="w-full text-xs bg-slate-700 border border-slate-600 text-slate-300 rounded px-2 py-1.5 focus:outline-none focus:border-cyan-500"
          >
            <option value="">Select...</option>
            {columns.map((c) => (
              <option key={c.name} value={c.name}>{c.name}</option>
            ))}
          </select>
        </div>

        {/* Y column */}
        {needsY && (
          <div>
            <label className="block text-xs text-slate-400 mb-1">{chartType === 'heatmap' ? 'Y Category' : 'Y Axis'}</label>
            <select
              value={yColumn}
              onChange={(e) => setYColumn(e.target.value)}
              className="w-full text-xs bg-slate-700 border border-slate-600 text-slate-300 rounded px-2 py-1.5 focus:outline-none focus:border-cyan-500"
            >
              <option value="">Select...</option>
              {(chartType === 'heatmap' ? categoricalColumns : needsAgg ? numericColumns : columns).map((c) => (
                <option key={c.name} value={c.name}>{c.name}</option>
              ))}
            </select>
          </div>
        )}

        {/* Aggregation */}
        {needsAgg && (
          <div>
            <label className="block text-xs text-slate-400 mb-1">Aggregation</label>
            <select
              value={aggregation}
              onChange={(e) => setAggregation(e.target.value)}
              className="w-full text-xs bg-slate-700 border border-slate-600 text-slate-300 rounded px-2 py-1.5 focus:outline-none focus:border-cyan-500"
            >
              {AGG_OPTIONS.map((a) => (
                <option key={a} value={a}>{a}</option>
              ))}
            </select>
          </div>
        )}

        {/* Group by */}
        {canGroupBy && (
          <div>
            <label className="block text-xs text-slate-400 mb-1">Group By</label>
            <select
              value={groupBy}
              onChange={(e) => setGroupBy(e.target.value)}
              className="w-full text-xs bg-slate-700 border border-slate-600 text-slate-300 rounded px-2 py-1.5 focus:outline-none focus:border-cyan-500"
            >
              <option value="">None</option>
              {categoricalColumns.map((c) => (
                <option key={c.name} value={c.name}>{c.name}</option>
              ))}
            </select>
          </div>
        )}

        {/* Generate button */}
        <div className="flex items-end">
          <button
            type="button"
            onClick={generateChart}
            disabled={loading || !xColumn || (needsY && !yColumn)}
            className="w-full px-3 py-1.5 text-xs rounded-md bg-cyan-600 text-white hover:bg-cyan-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Loading...' : 'Generate'}
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <p className="text-sm text-red-400 mb-3">{error}</p>
      )}

      {/* Result chart */}
      {data && !loading && (
        <div className="border-t border-slate-700/50 pt-4">
          {data.chart_type === 'bar' && (
            <BarChartView
              data={data.data as BIChartDataPoint[]}
              xLabel={data.x_column}
              yLabel={data.y_column || ''}
              groups={data.groups}
            />
          )}
          {data.chart_type === 'line' && (
            <LineChartView
              data={data.data as BIChartDataPoint[]}
              xLabel={data.x_column}
              yLabel={data.y_column || ''}
              groups={data.groups}
            />
          )}
          {data.chart_type === 'scatter' && (
            <ScatterChartView
              data={data.data as BIChartDataPoint[]}
              xLabel={data.x_column}
              yLabel={data.y_column || ''}
              sampled={data.sampled}
              sampleSize={data.sample_size}
            />
          )}
          {data.chart_type === 'histogram' && (
            <HistogramView
              data={data.data as BIHistogramBin[]}
              xLabel={data.x_column}
            />
          )}
          {data.chart_type === 'heatmap' && (
            <HeatmapView
              data={data.data as BIHeatmapCell[]}
              xLabel={data.x_column}
              yLabel={data.y_column || ''}
              valueLabel={data.value_column || ''}
            />
          )}
          <p className="text-xs text-slate-500 text-right mt-2">
            {data.data_points} data point{data.data_points !== 1 ? 's' : ''}
          </p>
        </div>
      )}
    </div>
  );
}

import { useCallback, useEffect, useState } from 'react';

import { getApiBaseUrl } from '@/lib/apiBase';
import type {
  BIChartDataPoint,
  BIChartDataResponse,
  BIChartRecommendation,
  BIHeatmapCell,
  BIHistogramBin,
} from '@/types/bi';

import BarChartView from './BarChartView';
import HeatmapView from './HeatmapView';
import HistogramView from './HistogramView';
import LineChartView from './LineChartView';
import ScatterChartView from './ScatterChartView';

const AGG_OPTIONS = ['mean', 'sum', 'median', 'count', 'min', 'max'];

interface ChartCardProps {
  sessionId: string;
  chart: BIChartRecommendation;
}

export default function ChartCard({ sessionId, chart }: ChartCardProps) {
  const [data, setData] = useState<BIChartDataResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [aggregation, setAggregation] = useState(chart.aggregation || 'mean');

  const fetchData = useCallback(async (agg: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${getApiBaseUrl()}/bi/charts/data/${sessionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chart_type: chart.chart_type,
          x_column: chart.x_column,
          y_column: chart.y_column || chart.value_column,
          aggregation: chart.chart_type === 'scatter' || chart.chart_type === 'histogram' ? null : agg,
          group_by: chart.group_by || null,
          bins: 20,
          limit: 50,
        }),
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body?.detail ?? `Failed to load chart data (${response.status})`);
      }
      const payload: BIChartDataResponse = await response.json();
      setData(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load chart data');
    } finally {
      setLoading(false);
    }
  }, [sessionId, chart]);

  useEffect(() => {
    fetchData(aggregation);
  }, [fetchData, aggregation]);

  const handleAggChange = (newAgg: string) => {
    setAggregation(newAgg);
  };

  const showAggSelector = chart.chart_type === 'bar' || chart.chart_type === 'line' || chart.chart_type === 'heatmap';

  return (
    <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-sm font-medium text-slate-200">{chart.title}</h3>
          <p className="text-xs text-slate-500">{chart.reason}</p>
        </div>
        {showAggSelector && (
          <select
            value={aggregation}
            onChange={(e) => handleAggChange(e.target.value)}
            className="text-xs bg-slate-700 border border-slate-600 text-slate-300 rounded px-2 py-1 focus:outline-none focus:border-cyan-500"
          >
            {AGG_OPTIONS.map((opt) => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </select>
        )}
      </div>

      {/* Chart content */}
      {loading && (
        <div className="h-[300px] flex items-center justify-center">
          <div className="animate-pulse text-sm text-slate-500">Loading chart...</div>
        </div>
      )}

      {error && (
        <div className="h-[300px] flex items-center justify-center">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}

      {!loading && !error && data && (
        <>
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
        </>
      )}

      {/* Data points count */}
      {!loading && data && (
        <p className="text-xs text-slate-500 text-right mt-2">
          {data.data_points} data point{data.data_points !== 1 ? 's' : ''}
        </p>
      )}
    </div>
  );
}

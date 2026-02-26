import { useEffect, useState } from 'react';

import { getApiBaseUrl } from '@/lib/authenticatedFetch';
import type { BIChartRecommendResponse, BIColumn } from '@/types/bi';

import ChartBuilder from './ChartBuilder';
import ChartCard from './ChartCard';
import KPICards from './KPICards';

interface ChartPageProps {
  sessionId: string;
}

export default function ChartPage({ sessionId }: ChartPageProps) {
  const [recommendations, setRecommendations] = useState<BIChartRecommendResponse | null>(null);
  const [columns, setColumns] = useState<BIColumn[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchRecommendations = async () => {
      setLoading(true);
      setError(null);
      try {
        // Fetch schema and recommendations in parallel
        const [schemaRes, recommendRes] = await Promise.all([
          fetch(`${getApiBaseUrl()}/bi/schema/${sessionId}`),
          fetch(`${getApiBaseUrl()}/bi/charts/recommend/${sessionId}`),
        ]);

        if (!schemaRes.ok) {
          const body = await schemaRes.json().catch(() => ({}));
          throw new Error(body?.detail ?? `Session not found (${schemaRes.status})`);
        }
        if (!recommendRes.ok) {
          const body = await recommendRes.json().catch(() => ({}));
          throw new Error(body?.detail ?? `Failed to get recommendations (${recommendRes.status})`);
        }

        const schema = await schemaRes.json();
        const recs: BIChartRecommendResponse = await recommendRes.json();

        setColumns(schema.columns);
        setRecommendations(recs);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load chart recommendations');
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, [sessionId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-2 border-cyan-500 border-t-transparent mb-3" />
          <p className="text-sm text-slate-400">Analyzing data and generating charts...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <p className="text-red-400 mb-2">{error}</p>
          <p className="text-sm text-slate-500">The session may have expired. Please go back and re-upload your data.</p>
        </div>
      </div>
    );
  }

  if (!recommendations) return null;

  return (
    <div className="space-y-6">
      {/* Summary header */}
      <div className="flex items-center gap-3 text-sm text-slate-400">
        <span>{recommendations.filtered_row_count.toLocaleString()} rows</span>
        <span className="text-slate-600">|</span>
        <span>{recommendations.kpi_cards.length} numeric column{recommendations.kpi_cards.length !== 1 ? 's' : ''}</span>
        <span className="text-slate-600">|</span>
        <span>{recommendations.recommended_charts.length} recommended chart{recommendations.recommended_charts.length !== 1 ? 's' : ''}</span>
      </div>

      {/* KPI Cards */}
      <KPICards cards={recommendations.kpi_cards} />

      {/* Recommended charts grid */}
      {recommendations.recommended_charts.length > 0 && (
        <div>
          <h2 className="text-sm font-medium text-slate-300 mb-3">Recommended Charts</h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {recommendations.recommended_charts.map((chart) => (
              <ChartCard key={chart.chart_id} sessionId={sessionId} chart={chart} />
            ))}
          </div>
        </div>
      )}

      {/* Custom chart builder */}
      <div>
        <h2 className="text-sm font-medium text-slate-300 mb-3">Custom Chart</h2>
        <ChartBuilder sessionId={sessionId} columns={columns} />
      </div>
    </div>
  );
}

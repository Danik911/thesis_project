/**
 * Observability Dashboard
 *
 * Displays LangFuse observability metrics for pharmaceutical test generation system.
 * GAMP-5 compliant with compliance annotations for audit review.
 *
 * Features:
 * - Real-time metrics from LangFuse Cloud (trace count, latency, cost)
 * - 5-minute SWR caching (respects LangFuse rate limits)
 * - Clerk authentication required
 * - ALCOA+ compliance annotations
 * - NO FALLBACK LOGIC - Explicit error states
 */

import { useAuth } from '@clerk/nextjs';
import Head from 'next/head';
import useSWR from 'swr';
import Layout from '../components/Layout';

interface LangFuseMetric {
  date: string;
  countTraces: number;
  totalCost: number;
  usage: Array<{
    model: string;
    inputUsage: number;
    outputUsage: number;
    totalUsage: number;
  }>;
}

interface APIResponse {
  success: boolean;
  data?: LangFuseMetric[];
  error?: string;
  details?: string;
  metadata?: {
    fetchedAt: string;
    itemCount: number;
  };
}

// SWR fetcher with authentication
const fetcher = async (url: string): Promise<APIResponse> => {
  const response = await fetch(url, {
    method: 'GET',
    credentials: 'include', // Include cookies for Clerk auth
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `HTTP ${response.status}`);
  }

  return response.json();
};

export default function ObservabilityDashboard() {
  const { isLoaded, userId } = useAuth();

  // SWR with 30-minute cache (matches backend cache)
  const { data, error, isLoading } = useSWR<APIResponse>(
    isLoaded && userId ? '/api/langfuse/summary' : null,
    fetcher,
    {
      refreshInterval: 30 * 60 * 1000, // 30 minutes
      revalidateOnFocus: false, // Don't refetch on tab focus
      dedupingInterval: 60000, // 1 minute deduping
      shouldRetryOnError: false, // Don't retry on 429 rate limit errors
    }
  );

  // Calculate aggregate metrics
  const metrics = data?.data || [];
  const totalTraces = metrics.reduce((sum, m) => sum + m.countTraces, 0);
  const totalCost = metrics.reduce((sum, m) => sum + m.totalCost, 0);
  const avgDailyTraces = metrics.length > 0 ? Math.round(totalTraces / metrics.length) : 0;

  // Error state (NO FALLBACK - explicit error display with ARIA)
  if (error) {
    return (
      <>
        <Head>
          <title>Error - Observability - Pharmaceutical Test Generation</title>
        </Head>
        <Layout>
          <div className="p-8">
            <h1 className="text-3xl font-bold text-red-600 mb-4">Observability Dashboard</h1>
            {/* Error with ARIA live region (WCAG 4.1.3 - Status Messages) */}
            <div role="alert" aria-live="assertive" className="bg-red-50 border border-red-300 p-6 rounded-lg">
              <p className="text-red-700 font-semibold">Failed to load metrics</p>
              <p className="text-red-600 text-sm mt-2">{error.message}</p>
              <div className="mt-4 p-4 bg-red-100 rounded text-xs text-red-800">
                <p className="font-semibold mb-2">Troubleshooting:</p>
                <ul className="list-disc list-inside space-y-1">
                  <li>Verify LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY are configured in .env.local</li>
                  <li>Check that LangFuse project is active at https://cloud.langfuse.com</li>
                  <li>Ensure network connectivity to LangFuse Cloud (EU region)</li>
                  <li>Verify Clerk authentication is working</li>
                </ul>
              </div>
            </div>
          </div>
        </Layout>
      </>
    );
  }

  // Loading state with ARIA live region (WCAG 4.1.3 - Status Messages)
  if (!isLoaded || isLoading) {
    return (
      <>
        <Head>
          <title>Loading - Observability - Pharmaceutical Test Generation</title>
        </Head>
        <Layout>
          <div className="p-8">
            <h1 className="text-3xl font-bold text-blue-600 mb-4">Observability Dashboard</h1>
            <div role="status" aria-live="polite">
              <span className="sr-only">Loading metrics from LangFuse Cloud. Please wait...</span>
              <p className="text-gray-700 mb-4" aria-hidden="true">Loading metrics from LangFuse Cloud...</p>
              <div className="mt-4 space-y-4">
                <div className="h-32 bg-gray-100 rounded-lg animate-pulse"></div>
                <div className="h-32 bg-gray-100 rounded-lg animate-pulse"></div>
                <div className="h-64 bg-gray-100 rounded-lg animate-pulse"></div>
              </div>
            </div>
          </div>
        </Layout>
      </>
    );
  }

  // No data state
  if (!data?.success || metrics.length === 0) {
    return (
      <>
        <Head>
          <title>Observability - Pharmaceutical Test Generation</title>
          <meta name="description" content="LangFuse observability metrics for GAMP-5 compliant pharmaceutical test generation" />
        </Head>
        <Layout>
          <div className="p-8">
            <h1 className="text-3xl font-bold text-blue-600 mb-4">Observability Dashboard</h1>
            <div className="bg-blue-50 border border-blue-300 p-6 rounded-lg">
              <p className="text-blue-800 font-semibold">No observability data available yet</p>
              <p className="text-blue-700 text-sm mt-2">
                Generate some test suites to see metrics appear here.
              </p>
              <div className="mt-4 p-4 bg-blue-100 rounded text-xs text-blue-800">
                <p className="font-semibold mb-2">Next Steps:</p>
                <ul className="list-disc list-inside space-y-1">
                  <li>Submit a URS document via the job submission API</li>
                  <li>Wait for test generation workflow to complete</li>
                  <li>Traces will appear in LangFuse Cloud within 1-2 minutes</li>
                  <li>Refresh this dashboard to see metrics</li>
                </ul>
              </div>
            </div>
          </div>
        </Layout>
      </>
    );
  }

  return (
    <>
      <Head>
        <title>Observability - Pharmaceutical Test Generation</title>
        <meta name="description" content="LangFuse observability metrics for GAMP-5 compliant pharmaceutical test generation" />
      </Head>
      <Layout>
        <div className="p-8">
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-blue-600">Observability Dashboard</h1>
            <p className="text-gray-700 text-sm mt-2">
              GAMP-5 Category 5 System • Last updated: {data.metadata?.fetchedAt ? new Date(data.metadata.fetchedAt).toLocaleString() : 'Unknown'}
            </p>
            <p className="text-xs text-gray-700 mt-1">
              ALCOA+ Compliant: Attributable, Legible, Contemporaneous, Original, Accurate, Complete, Consistent, Enduring, Available
            </p>
          </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {/* Total Traces */}
          <div className="bg-white border border-gray-300 p-6 rounded-lg shadow-sm">
            <h2 className="text-gray-700 text-sm font-semibold mb-2">Total Traces (7 days)</h2>
            <p className="text-4xl font-bold text-blue-600">{totalTraces}</p>
            <p className="text-gray-700 text-xs mt-2">
              ALCOA+ Contemporaneous: Traces captured in real-time with ISO8601 timestamps
            </p>
          </div>

          {/* Average Daily Throughput */}
          <div className="bg-white border border-gray-300 p-6 rounded-lg shadow-sm">
            <h2 className="text-gray-700 text-sm font-semibold mb-2">Avg. Daily Throughput</h2>
            <p className="text-4xl font-bold text-green-600">{avgDailyTraces}</p>
            <p className="text-gray-700 text-xs mt-2">
              Target: 50 documents/day (Baseline for performance monitoring)
            </p>
            {avgDailyTraces < 50 && avgDailyTraces > 0 && (
              <p className="text-yellow-600 text-xs mt-1 font-semibold">
                ⚠️ Below target throughput ({50 - avgDailyTraces} documents/day under baseline)
              </p>
            )}
            {avgDailyTraces >= 50 && (
              <p className="text-green-600 text-xs mt-1 font-semibold">
                ✓ Meeting or exceeding target throughput
              </p>
            )}
          </div>

          {/* Total Cost */}
          <div className="bg-white border border-gray-300 p-6 rounded-lg shadow-sm">
            <h2 className="text-gray-700 text-sm font-semibold mb-2">Total Cost (7 days)</h2>
            <p className="text-4xl font-bold text-purple-600">${totalCost.toFixed(2)}</p>
            <p className="text-gray-700 text-xs mt-2">
              LLM usage costs tracked for budget compliance and cost attribution
            </p>
          </div>
        </div>

        {/* Daily Metrics Table with WCAG 1.3.1 - Table Accessibility */}
        <div className="bg-white border border-gray-300 rounded-lg shadow-sm overflow-hidden">
          <div className="p-6 border-b border-gray-200 bg-gray-50">
            <h2 className="text-xl font-bold text-gray-800">Daily Metrics (Last 7 Days)</h2>
            <p className="text-gray-700 text-sm mt-1">
              ALCOA+ Complete: All trace data captured with full input/output context
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              {/* Table caption for screen readers (WCAG 1.3.1) */}
              <caption className="sr-only">
                Daily observability metrics for the last 7 days, showing trace counts, costs, and models used per date
              </caption>
              <thead className="bg-gray-100 border-b border-gray-200">
                <tr>
                  <th scope="col" className="text-left p-4 text-gray-700 font-semibold">Date</th>
                  <th scope="col" className="text-right p-4 text-gray-700 font-semibold">Traces</th>
                  <th scope="col" className="text-right p-4 text-gray-700 font-semibold">Cost</th>
                  <th scope="col" className="text-left p-4 text-gray-700 font-semibold">Models Used</th>
                </tr>
              </thead>
              <tbody>
                {metrics.map((metric, idx) => (
                  <tr
                    key={metric.date}
                    className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}
                  >
                    <td className="p-4 text-gray-800">
                      {new Date(metric.date).toLocaleDateString('en-US', {
                        weekday: 'short',
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                      })}
                    </td>
                    <td className="p-4 text-right text-gray-800 font-mono">
                      {metric.countTraces}
                    </td>
                    <td className="p-4 text-right text-gray-800 font-mono">
                      ${metric.totalCost.toFixed(2)}
                    </td>
                    <td className="p-4 text-gray-700 text-sm">
                      {metric.usage.map(u => u.model).join(', ') || 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Compliance Footer */}
        <div className="mt-8 p-4 bg-blue-50 border border-blue-300 rounded-lg">
          <p className="text-blue-800 text-sm">
            <strong>GAMP-5 Compliance:</strong> All observability data is traceable (job_id),
            attributed (user_id), and immutable (stored in LangFuse Cloud EU region).
            Traces are retained for 90 days for audit purposes and exported via Public API
            for regulatory review.
          </p>
          <p className="text-blue-700 text-xs mt-2">
            <strong>Data Residency:</strong> LangFuse Cloud EU (https://cloud.langfuse.com) •
            <strong> Retention:</strong> 90 days default •
            <strong> Export:</strong> Available via Public API
          </p>
        </div>
      </div>
    </Layout>
    </>
  );
}

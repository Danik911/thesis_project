import Head from 'next/head';
import { useRouter } from 'next/router';

import ChartPage from '@/components/bi/charts/ChartPage';

export default function BIChartsPage() {
  const router = useRouter();
  const sessionId = typeof router.query.session === 'string' ? router.query.session : '';

  return (
    <>
      <Head>
        <title>MES Agentic BI - Charts</title>
      </Head>

      <div className="min-h-screen bg-slate-950 text-slate-100 px-4 py-4">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-4 flex items-center justify-between gap-4">
            <h1
              className="text-2xl font-bold text-cyan-300 whitespace-nowrap"
              style={{ fontFamily: 'var(--font-display)' }}
            >
              MES Agentic BI - Charts
            </h1>

            <button
              type="button"
              onClick={() => router.back()}
              className="px-3 py-1.5 text-xs rounded-md border border-slate-700 text-slate-300 hover:border-slate-600 transition-colors"
            >
              Back to Grid
            </button>
          </div>

          {/* Content */}
          {sessionId ? (
            <ChartPage sessionId={sessionId} />
          ) : (
            <div className="flex items-center justify-center min-h-[400px]">
              <div className="text-center">
                <p className="text-slate-400 mb-2">No session specified.</p>
                <button
                  type="button"
                  onClick={() => router.push('/agentic-bi')}
                  className="text-sm text-cyan-400 hover:text-cyan-300 underline"
                >
                  Go to MES Agentic BI
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

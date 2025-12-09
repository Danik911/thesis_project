import { useState } from 'react';
import LangfuseTraceDashboard from './LangfuseTraceDashboard';

interface ComplianceDashboardProps {
  results: any; // Replace with proper type
  onDownload: () => void;
  onExport?: (format: 'html' | 'json') => void;
  onView?: () => void;
}

// Format duration in minutes to human-readable format (e.g., "20h 55m" or "45m")
function formatDuration(minutes: number): string {
  if (minutes >= 60) {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
  }
  return `${minutes}m`;
}

export default function ComplianceDashboard({ results, onDownload, onExport, onView }: ComplianceDashboardProps) {
  const [activeTab, setActiveTab] = useState('overview');
  const [showTracePanel, setShowTracePanel] = useState(false);

  const traceId = (results.trace_id || results.traceId) as string | undefined;
  const traceUrl = (results.trace_url || results.traceUrl) as string | undefined;
  const traceAvailable = Boolean(traceId && traceId !== 'unknown');
  const generatedAt = results.generation_timestamp || results.timestamp || null;

  return (
    <div className="w-full max-w-6xl mx-auto space-y-8 animate-fade-in-up">
      {/* Header & Actions */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white mb-1">Validation Results</h2>
          <p className="text-slate-400 text-sm">Job ID: {results.job_id || 'N/A'}</p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => traceAvailable && setShowTracePanel((prev) => !prev)}
            disabled={!traceAvailable}
            className={`btn-secondary flex items-center gap-2 ${!traceAvailable ? 'opacity-60 cursor-not-allowed' : ''}`}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12c0 4.97-4.03 9-9 9s-9-4.03-9-9 4.03-9 9-9 9 4.03 9 9z" />
            </svg>
            {traceAvailable ? (showTracePanel ? 'Hide Langfuse trace' : 'Langfuse trace dashboard') : 'Langfuse trace unavailable'}
          </button>
          <button
            onClick={onDownload}
            className="btn-primary flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Download YAML
          </button>
          {onExport && (
            <>
              {onView && (
                <button
                  onClick={onView}
                  className="btn-secondary flex items-center gap-2"
                  title="View HTML Report"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                  View
                </button>
              )}
              <button
                onClick={() => onExport('html')}
                className="btn-secondary flex items-center gap-2"
                title="Export as HTML"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                HTML
              </button>
              <button
                onClick={() => onExport('json')}
                className="btn-secondary flex items-center gap-2"
                title="Export as JSON"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                </svg>
                JSON
              </button>
            </>
          )}
        </div>
      </div>

      {showTracePanel && traceAvailable && (
        <LangfuseTraceDashboard traceId={traceId} traceUrl={traceUrl} jobId={results.job_id} />
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card border-l-4 border-l-blue-500">
          <div className="text-slate-400 text-xs uppercase tracking-wider mb-1">Total Tests</div>
          <div className="text-3xl font-bold text-white">{results.total_test_count || 0}</div>
        </div>
        <div className="card border-l-4 border-l-emerald-500">
          <div className="text-slate-400 text-xs uppercase tracking-wider mb-1">GAMP Category</div>
          <div className="text-3xl font-bold text-white">{results.gamp_category || 'N/A'}</div>
        </div>
        <div className="card border-l-4 border-l-purple-500">
          <div className="text-slate-400 text-xs uppercase tracking-wider mb-1">Risk Level</div>
          <div className="text-3xl font-bold text-white">Medium</div> {/* Placeholder */}
        </div>
        <div className="card border-l-4 border-l-amber-500">
          <div className="text-slate-400 text-xs uppercase tracking-wider mb-1">Est. Total Test Time</div>
          <div className="text-3xl font-bold text-white">{formatDuration(results.estimated_execution_time || 0)}</div>
          <p className="text-xs text-slate-500 mt-1">{results.total_test_count || 0} tests (sequential)</p>
        </div>
      </div>

      {/* Main Content Tabs */}
      <div className="glass-panel overflow-hidden">
        <div className="flex border-b border-slate-700/50">
          {['overview', 'compliance', 'tests'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-6 py-4 text-sm font-medium transition-colors relative ${activeTab === tab
                ? 'text-blue-400 bg-slate-800/50'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/30'
                }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
              {activeTab === tab && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]"></div>
              )}
            </button>
          ))}
        </div>

        <div className="p-6">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-lg font-medium text-white mb-4">Validation Summary</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between py-2 border-b border-slate-700/50">
                      <span className="text-slate-400">Document Name</span>
                      <span className="text-slate-200">{results.document_name}</span>
                    </div>
                    <div className="flex justify-between py-2 border-b border-slate-700/50">
                      <span className="text-slate-400">Generated At</span>
                      <span className="text-slate-200">{generatedAt ? new Date(generatedAt).toLocaleString() : 'N/A'}</span>
                    </div>
                    <div className="flex justify-between py-2 border-b border-slate-700/50">
                      <span className="text-slate-400">Workflow Session</span>
                      <span className="text-slate-200 font-mono text-xs">{results.workflow_session_id}</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-medium text-white mb-4">Requirements Coverage</h3>
                  <div className="space-y-2">
                    {Object.entries(results.requirements_coverage || {}).map(([req, tests]: [string, any]) => (
                      <div key={req} className="bg-slate-800/50 rounded-lg p-3 flex justify-between items-center">
                        <span className="text-sm font-medium text-slate-300">{req}</span>
                        <div className="flex gap-1">
                          {tests.length > 0 ? (
                            tests.map((testId: string) => (
                              <span key={testId} className="text-xs bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded border border-blue-500/30">
                                {testId}
                              </span>
                            ))
                          ) : (
                            <span className="text-xs bg-red-500/20 text-red-300 px-2 py-0.5 rounded border border-red-500/30">
                              No Coverage
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'compliance' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <h3 className="text-lg font-medium text-white">Regulatory Compliance</h3>
                <div className="space-y-3">
                  <ComplianceItem
                    label="GAMP 5 Compliant"
                    status={results.pharmaceutical_compliance?.gamp5_compliant}
                    description="Software category and validation approach aligned with GAMP 5 guidelines."
                  />
                  <ComplianceItem
                    label="21 CFR Part 11"
                    status={results.pharmaceutical_compliance?.cfr_part_11_compliant}
                    description="Electronic records and signatures requirements met."
                  />
                  <ComplianceItem
                    label="ALCOA+ Principles"
                    status={results.pharmaceutical_compliance?.alcoa_plus_compliant}
                    description="Data is Attributable, Legible, Contemporaneous, Original, and Accurate."
                  />
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-lg font-medium text-white">Data Integrity</h3>
                <div className="space-y-3">
                  <ComplianceItem
                    label="Audit Trail Verified"
                    status={results.pharmaceutical_compliance?.audit_trail_verified}
                    description="Complete history of actions and changes recorded."
                  />
                  <ComplianceItem
                    label="Data Integrity Assured"
                    status={results.pharmaceutical_compliance?.data_integrity_assured}
                    description="End-to-end data consistency checks passed."
                  />
                </div>
              </div>
            </div>
          )}

          {activeTab === 'tests' && (
            <div className="space-y-4">
              {results.test_cases?.map((test: any) => (
                <div key={test.test_id} className="bg-slate-800/30 rounded-lg border border-slate-700/50 p-4 hover:bg-slate-800/50 transition-colors">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-blue-400 font-mono font-bold">{test.test_id}</span>
                        <span className="text-xs px-2 py-0.5 rounded-full bg-slate-700 text-slate-300 border border-slate-600">
                          {test.test_category}
                        </span>
                      </div>
                      <h4 className="text-white font-medium mt-1">{test.test_name}</h4>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded border ${test.risk_level === 'critical' ? 'bg-red-500/10 text-red-400 border-red-500/30' :
                      test.risk_level === 'high' ? 'bg-orange-500/10 text-orange-400 border-orange-500/30' :
                        'bg-blue-500/10 text-blue-400 border-blue-500/30'
                      }`}>
                      {test.risk_level?.toUpperCase()} RISK
                    </span>
                  </div>
                  <p className="text-sm text-slate-400 mb-3">{test.objective}</p>
                  <div className="grid grid-cols-2 gap-4 text-xs text-slate-400">
                    <div>
                      <span className="block text-slate-400 mb-1">Prerequisites:</span>
                      <ul className="list-disc list-inside">
                        {test.prerequisites?.slice(0, 2).map((p: string, i: number) => (
                          <li key={i} className="truncate">{p}</li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <span className="block text-slate-400 mb-1">Acceptance Criteria:</span>
                      <ul className="list-disc list-inside">
                        {test.acceptance_criteria?.slice(0, 2).map((c: string, i: number) => (
                          <li key={i} className="truncate">{c}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ComplianceItem({ label, status, description }: { label: string, status: boolean, description: string }) {
  return (
    <div className="flex items-start gap-3 p-3 rounded-lg bg-slate-800/30 border border-slate-700/30">
      <div className={`mt-1 w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 ${status ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
        }`}>
        {status ? (
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
          </svg>
        ) : (
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
          </svg>
        )}
      </div>
      <div>
        <div className="text-sm font-medium text-slate-200">{label}</div>
        <div className="text-xs text-slate-400 mt-0.5">{description}</div>
      </div>
    </div>
  );
}

import { useAuth } from '@clerk/nextjs';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import Layout from '../../components/Layout';
import ComplianceDashboard from '../../components/ComplianceDashboard';
import { authenticatedFetch, getApiBaseUrl } from '../../lib/authenticatedFetch';

interface Job {
    job_id: string;
    status: string;
    created_at: string;
    started_at?: string;
    completed_at?: string;
    urs_filename: string;
    result_uri?: string;
    error_message?: string;
    trace_id?: string;
    trace_url?: string;
}

interface LangfuseObservation {
    id: string;
    startTime?: string | null;
    endTime?: string | null;
}

interface LangfuseTracePayload {
    id: string;
    observations?: LangfuseObservation[];
    totalCost?: number | string | null;
    latency?: number | null;
}

interface LangfuseApiSuccess {
    success: true;
    data: LangfuseTracePayload;
}

interface LangfuseApiError {
    success: false;
    error: string;
    details?: string;
}

type LangfuseApiResponse = LangfuseApiSuccess | LangfuseApiError;

export default function JobDetails() {
    const { isLoaded, userId, getToken } = useAuth();
    const router = useRouter();
    const { id } = router.query;
    const [job, setJob] = useState<Job | null>(null);
    const [results, setResults] = useState<any>(null);
    const [activeTab, setActiveTab] = useState<'overview' | 'observability'>('overview');
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [traceSummary, setTraceSummary] = useState<LangfuseTracePayload | null>(null);
    const [isTraceLoading, setIsTraceLoading] = useState(false);
    const [traceError, setTraceError] = useState<string | null>(null);

    useEffect(() => {
        const fetchJobDetails = async () => {
            if (!isLoaded || !userId || !id) return;

            try {
                const apiUrl = getApiBaseUrl();

                // Fetch Job Status - authenticatedFetch handles 401 retry
                const jobRes = await authenticatedFetch(`${apiUrl}/jobs/${id}`, getToken);

                if (!jobRes.ok) {
                    if (jobRes.status === 404) {
                        throw new Error('Job not found');
                    }
                    throw new Error('Failed to fetch job details');
                }

                const jobData = await jobRes.json();
                setJob(jobData);

                // If completed, fetch results
                if (jobData.status.toUpperCase() === 'COMPLETED') {
                    const resultRes = await authenticatedFetch(`${apiUrl}/jobs/${id}/result`, getToken);
                    if (resultRes.ok) {
                        const resultData = await resultRes.json();
                        setResults(resultData);
                    }
                }

            } catch (err) {
                setError(err instanceof Error ? err.message : 'Unknown error');
            } finally {
                setIsLoading(false);
            }
        };

        fetchJobDetails();
    }, [isLoaded, userId, id, getToken]);

    const handleDownload = async () => {
        if (!job) return;
        try {
            const apiUrl = getApiBaseUrl();
            const response = await authenticatedFetch(`${apiUrl}/jobs/${job.job_id}/download`, getToken);

            if (!response.ok) throw new Error('Download failed');

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `test_suite_${job.job_id}.yaml`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (e) {
            alert('Failed to download file');
        }
    };

    const calculateDuration = () => {
        if (!job?.started_at) return 'N/A';
        const start = new Date(job.started_at).getTime();
        const end = job.completed_at ? new Date(job.completed_at).getTime() : Date.now();
        const diff = end - start;

        const hours = Math.floor(diff / 3600000);
        const minutes = Math.floor((diff % 3600000) / 60000);
        const seconds = Math.floor((diff % 60000) / 1000);

        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    };

    useEffect(() => {
        if (!job?.trace_id || job.trace_id === 'unknown') {
            setTraceSummary(null);
            setTraceError(job ? 'Langfuse trace not captured for this job.' : null);
            return;
        }

        const controller = new AbortController();
        const fetchTrace = async () => {
            setIsTraceLoading(true);
            setTraceError(null);
            try {
                const response = await fetch(`/api/langfuse/trace?traceId=${encodeURIComponent(job.trace_id!)}`, {
                    signal: controller.signal,
                });
                const payload = await response.json() as LangfuseApiResponse;
                if (!payload.success) {
                    throw new Error(payload.details || payload.error || 'Failed to load Langfuse trace');
                }
                setTraceSummary(payload.data);
            } catch (err) {
                if (!controller.signal.aborted) {
                    setTraceSummary(null);
                    setTraceError(err instanceof Error ? err.message : 'Unable to load Langfuse trace');
                }
            } finally {
                if (!controller.signal.aborted) {
                    setIsTraceLoading(false);
                }
            }
        };

        fetchTrace();
        return () => controller.abort();
    }, [job?.trace_id, job]);

    const observationCount = traceSummary?.observations?.length ?? 0;
    const formattedCostValue = (() => {
        if (!traceSummary || traceSummary.totalCost === undefined || traceSummary.totalCost === null) {
            return 0;
        }
        const numeric = typeof traceSummary.totalCost === 'number'
            ? traceSummary.totalCost
            : Number(traceSummary.totalCost);
        return Number.isFinite(numeric) ? numeric : 0;
    })();

    if (!isLoaded || isLoading) {
        return (
            <Layout>
                <div className="flex items-center justify-center min-h-[60vh]">
                    <div className="animate-pulse text-slate-400">Loading job details...</div>
                </div>
            </Layout>
        );
    }

    if (error || !job) {
        return (
            <Layout>
                <div className="p-8 text-center">
                    <h1 className="text-2xl text-red-400 mb-4">Error</h1>
                    <p className="text-slate-400">{error || 'Job not found'}</p>
                    <button onClick={() => router.push('/history')} className="mt-4 btn-primary">Back to History</button>
                </div>
            </Layout>
        );
    }

    return (
        <>
            <Head>
                <title>Job {job.job_id.substring(0, 8)} - PharmaGen AI</title>
            </Head>
            <Layout>
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <div className="flex items-center justify-between mb-8">
                        <div>
                            <div className="flex items-center gap-4 mb-2">
                                <button onClick={() => router.push('/history')} className="text-slate-400 hover:text-white transition-colors">
                                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                                    </svg>
                                </button>
                                <h1 className="text-3xl font-bold text-white">Job Details</h1>
                            </div>
                            <p className="text-slate-400 font-mono text-sm ml-10">ID: {job.job_id}</p>
                        </div>
                        <div className="flex gap-4">
                            <span className={`px-3 py-1 rounded-full text-sm font-medium ${job.status.toUpperCase() === 'COMPLETED' ? 'bg-emerald-500/10 text-emerald-400' :
                                job.status.toUpperCase() === 'FAILED' ? 'bg-red-500/10 text-red-400' :
                                    'bg-blue-500/10 text-blue-400'
                                }`}>
                                {job.status.toUpperCase()}
                            </span>
                        </div>
                    </div>

                    {/* Tabs */}
                    <div className="flex border-b border-slate-700 mb-8">
                        <button
                            onClick={() => setActiveTab('overview')}
                            className={`px-6 py-3 text-sm font-medium transition-colors border-b-2 ${activeTab === 'overview'
                                ? 'border-blue-500 text-blue-400'
                                : 'border-transparent text-slate-400 hover:text-slate-200'
                                }`}
                        >
                            Overview & Results
                        </button>
                        <button
                            onClick={() => setActiveTab('observability')}
                            className={`px-6 py-3 text-sm font-medium transition-colors border-b-2 ${activeTab === 'observability'
                                ? 'border-blue-500 text-blue-400'
                                : 'border-transparent text-slate-400 hover:text-slate-200'
                                }`}
                        >
                            Observability
                        </button>
                    </div>

                    {/* Content */}
                    {activeTab === 'overview' && (
                        <div className="animate-fade-in">
                            {job.status.toUpperCase() === 'COMPLETED' && results ? (
                                <ComplianceDashboard
                                    results={{
                                        ...results,
                                        job_id: job.job_id,
                                        trace_id: job.trace_id,
                                        trace_url: job.trace_url,
                                    }}
                                    onDownload={handleDownload}
                                />
                            ) : (
                                <div className="bg-slate-800/50 rounded-xl p-8 text-center border border-slate-700">
                                    <p className="text-slate-400">
                                        {job.status.toUpperCase() === 'FAILED'
                                            ? `Job Failed: ${job.error_message || 'Unknown error'}`
                                            : 'Job is processing... Results will appear here when complete.'}
                                    </p>
                                </div>
                            )}
                        </div>
                    )}

                    {activeTab === 'observability' && (
                        <div className="animate-fade-in grid grid-cols-1 md:grid-cols-3 gap-6">
                            <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg shadow-sm">
                                <h2 className="text-slate-400 text-sm font-semibold mb-2">Job Duration</h2>
                                <p className="text-4xl font-bold text-emerald-400">{calculateDuration()}</p>
                                <p className="text-slate-500 text-xs mt-2">Total execution time</p>
                            </div>

                            <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg shadow-sm">
                                <h2 className="text-slate-400 text-sm font-semibold mb-2">Langfuse Observations</h2>
                                <p className="text-4xl font-bold text-blue-400">
                                    {isTraceLoading ? '…' : traceSummary ? observationCount : traceError ? 'N/A' : '0'}
                                </p>
                                <p className="text-slate-500 text-xs mt-2">Observations captured across the workflow</p>
                            </div>

                            <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg shadow-sm">
                                <h2 className="text-slate-400 text-sm font-semibold mb-2">Total Cost</h2>
                                <p className="text-4xl font-bold text-purple-400">
                                    {isTraceLoading ? '…' : traceSummary ? `$${formattedCostValue.toFixed(4)}` : traceError ? 'N/A' : '$0.0000'}
                                </p>
                                <p className="text-slate-500 text-xs mt-2">Estimated LLM cost from Langfuse</p>
                            </div>

                            {traceError && (
                                <div className="md:col-span-3 bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-sm text-red-200">
                                    Unable to load Langfuse trace data: {traceError}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </Layout>
        </>
    );
}

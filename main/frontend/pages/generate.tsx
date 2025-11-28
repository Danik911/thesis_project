import { useState, useEffect, useRef, useCallback } from 'react';
import { useUser, useAuth } from '@clerk/nextjs';
import Layout from '@/components/Layout';
import Head from 'next/head';
import FileUpload from '@/components/FileUpload';
import JobProgress from '@/components/JobProgress';
import ComplianceDashboard from '@/components/ComplianceDashboard';
import ApprovalModal from '@/components/ApprovalModal';
import { useJobStatusPolling } from '@/hooks/useJobStatusPolling';
import { authenticatedFetch, getApiBaseUrl } from '@/lib/authenticatedFetch';

type JobStatus = 'IDLE' | 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'EXPIRED' | 'AWAITING_APPROVAL';

export default function Generate() {
    const { user, isLoaded } = useUser();
    const { getToken } = useAuth();

    // Lazy initialization: Read from localStorage BEFORE any useEffect runs
    // Check for browser environment to avoid SSR errors
    const [jobId, setJobId] = useState<string | null>(() => {
        if (typeof window === 'undefined') return null;
        return localStorage.getItem('activeJobId');
    });
    const [status, setStatus] = useState<JobStatus>(() => {
        if (typeof window === 'undefined') return 'IDLE';
        const savedStatus = localStorage.getItem('activeJobStatus') as JobStatus;
        return savedStatus || 'IDLE';
    });
    const [logs, setLogs] = useState<string[]>(() => {
        if (typeof window === 'undefined') return [];
        const savedLogs = localStorage.getItem('jobLogs');
        if (savedLogs) {
            try {
                return JSON.parse(savedLogs);
            } catch (e) {
                console.error("Failed to parse saved logs", e);
                return [];
            }
        }
        return [];
    });
    const [jobStartTime, setJobStartTime] = useState<number | null>(() => {
        if (typeof window === 'undefined') return null;
        const savedStartTime = localStorage.getItem('jobStartTime');
        return savedStartTime ? parseInt(savedStartTime, 10) : null;
    });

    const [results, setResults] = useState<any>(null);
    const [jobs, setJobs] = useState<any[]>([]);
    const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

    // Track if a poll request is in-flight to prevent retry storms during token refresh
    const isPollingInFlight = useRef<boolean>(false);

    // Approval modal state
    const [showApprovalModal, setShowApprovalModal] = useState(false);

    // Poll for approval status separately (5-second interval)
    const { data: approvalStatus, refetch: refetchApprovalStatus } = useJobStatusPolling(jobId, 5000);

    // Derive display name
    const displayName = user?.fullName ??
        user?.firstName ??
        user?.primaryEmailAddress?.emailAddress ??
        'User';

    const [selectedFile, setSelectedFile] = useState<File | null>(null);

    const handleFileSelect = (file: File) => {
        setSelectedFile(file);
    };

    const fetchJobs = useCallback(async () => {
        if (!isLoaded || !user) return;
        try {
            const apiUrl = getApiBaseUrl();
            const response = await authenticatedFetch(`${apiUrl}/jobs`, getToken);
            if (response.ok) {
                const data = await response.json();
                setJobs(data);
            }
        } catch (error) {
            console.error("Failed to fetch jobs:", error);
        }
    }, [isLoaded, user, getToken]);

    // Cleanup polling on unmount
    useEffect(() => {
        return () => {
            if (pollIntervalRef.current) {
                clearInterval(pollIntervalRef.current);
            }
        };
    }, []);

    // Detect when approval is required
    useEffect(() => {
        if (approvalStatus?.requires_approval && approvalStatus.status.toUpperCase() === 'AWAITING_APPROVAL') {
            setStatus('AWAITING_APPROVAL');
            setShowApprovalModal(true);
        }
    }, [approvalStatus]);

    useEffect(() => {
        fetchJobs();
    }, [fetchJobs]);

    // Load state from localStorage on mount


    // Save state to localStorage whenever it changes
    useEffect(() => {
        if (jobId) {
            localStorage.setItem('activeJobId', jobId);
        } else {
            localStorage.removeItem('activeJobId');
        }
    }, [jobId]);

    useEffect(() => {
        if (status) {
            localStorage.setItem('activeJobStatus', status);
        } else {
            localStorage.removeItem('activeJobStatus');
        }
    }, [status]);

    useEffect(() => {
        if (logs.length > 0) {
            localStorage.setItem('jobLogs', JSON.stringify(logs));
        } else {
            localStorage.removeItem('jobLogs');
        }
    }, [logs]);

    useEffect(() => {
        if (jobStartTime) {
            localStorage.setItem('jobStartTime', jobStartTime.toString());
        } else {
            localStorage.removeItem('jobStartTime');
        }
    }, [jobStartTime]);



    // Persistence Logic
    const handleGenerate = async () => {
        if (!selectedFile) return;

        // CRITICAL FIX: Prevent submitting new job while another is active
        // This prevents the race condition where approval modal gets lost
        if (status === 'PENDING' || status === 'PROCESSING' || status === 'AWAITING_APPROVAL') {
            console.warn('[DEBUG] Blocking new job submission - another job is active');
            setLogs(prev => [...prev, `WARNING: A job is already in progress (${status}). Please wait or reset.`]);
            return;
        }

        console.log('[DEBUG] handleGenerate called');
        console.log(`[DEBUG] Selected file: ${selectedFile.name} (${selectedFile.size} bytes)`);

        setStatus('PENDING');
        setLogs(['Initializing upload...', 'Validating file format...', 'Checking GAMP-5 compliance requirements...']);

        try {
            const formData = new FormData();
            formData.append('file', selectedFile);

            const apiUrl = getApiBaseUrl();
            console.log(`[DEBUG] API URL: ${apiUrl}`);

            setLogs(prev => [...prev, `Connecting to secure API at ${apiUrl}...`]);

            console.log('[DEBUG] Sending POST /jobs request with authenticated fetch...');
            const response = await authenticatedFetch(`${apiUrl}/jobs`, getToken, {
                method: 'POST',
                body: formData
            });
            console.log(`[DEBUG] POST /jobs response: ${response.status} ${response.statusText}`);

            if (!response.ok) {
                const errorText = await response.text();
                console.error(`[DEBUG] POST /jobs error response: ${errorText}`);
                let errorDetail = `API Error: ${response.statusText}`;
                try {
                    const errorData = JSON.parse(errorText);
                    errorDetail = errorData.detail || errorDetail;
                } catch {
                    // Not JSON - use raw text
                    errorDetail = errorText || errorDetail;
                }
                throw new Error(errorDetail);
            }

            const data = await response.json();
            console.log(`[DEBUG] Job created: ${data.job_id}`);

            setJobId(data.job_id);
            setStatus('PROCESSING');
            setJobStartTime(Date.now()); // Set start time
            setLogs(prev => [...prev, `Job submitted successfully (ID: ${data.job_id}). Starting processing...`]);

            // Start polling
            pollJobStatus(data.job_id, apiUrl);

        } catch (error) {
            console.error('[DEBUG] Upload failed:', error);
            setStatus('FAILED');
            setLogs(prev => [...prev, `ERROR: ${error instanceof Error ? error.message : 'Upload failed'}`]);
        }
    };

    const pollJobStatus = useCallback((id: string, apiUrl: string) => {
        if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);

        // Track consecutive failures to expose errors after multiple attempts
        let consecutiveFailures = 0;
        const MAX_CONSECUTIVE_FAILURES = 5;

        console.log(`[DEBUG] Starting poll for job ${id} at ${apiUrl}`);

        pollIntervalRef.current = setInterval(async () => {
            // Skip this poll cycle if a previous request is still in-flight (prevents retry storms)
            if (isPollingInFlight.current) {
                console.log('[DEBUG] Skipping poll - previous request still in flight');
                return;
            }
            isPollingInFlight.current = true;

            try {
                console.log(`[DEBUG] Polling job status: GET ${apiUrl}/jobs/${id}`);
                // Use authenticatedFetch which handles 401 retry internally
                const response = await authenticatedFetch(`${apiUrl}/jobs/${id}`, getToken);

                if (!response.ok) {
                    if (response.status === 404) {
                        if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
                        setStatus('EXPIRED');
                        setLogs(prev => [...prev, 'ERROR: Job session expired. The server may have restarted.']);
                        return;
                    }
                    consecutiveFailures++;
                    console.error(`[DEBUG] Polling HTTP error ${response.status} (failure ${consecutiveFailures}/${MAX_CONSECUTIVE_FAILURES})`);
                    if (consecutiveFailures >= MAX_CONSECUTIVE_FAILURES) {
                        if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);

                        // CRITICAL FIX: Before showing FAILED, do one final check if job actually completed
                        // The backend worker runs independently - job may have completed despite polling 401s
                        console.log(`[DEBUG] Max failures reached. Performing final job status check...`);
                        try {
                            const finalCheckResponse = await authenticatedFetch(`${apiUrl}/jobs/${id}`, getToken);
                            if (finalCheckResponse.ok) {
                                const finalData = await finalCheckResponse.json();
                                const finalStatus = finalData.status.toUpperCase();
                                console.log(`[DEBUG] Final check: job status is ${finalStatus}`);

                                if (finalStatus === 'COMPLETED') {
                                    // Job actually completed! Fetch results instead of showing error
                                    setLogs(prev => [...prev, 'Job completed (recovered from polling errors). Retrieving results...']);
                                    const resultResponse = await authenticatedFetch(`${apiUrl}/jobs/${id}/result`, getToken);
                                    if (resultResponse.ok) {
                                        const resultData = await resultResponse.json();
                                        setResults(resultData);
                                        setStatus('COMPLETED');
                                        fetchJobs();
                                        return;
                                    }
                                }
                            }
                        } catch (finalCheckError) {
                            console.error('[DEBUG] Final check failed:', finalCheckError);
                        }

                        // Only show FAILED if the final check didn't recover
                        setStatus('FAILED');
                        setLogs(prev => [...prev, `ERROR: Server communication failed after ${MAX_CONSECUTIVE_FAILURES} attempts (${response.status})`]);
                    }
                    return;
                }

                // Reset failure counter on success
                consecutiveFailures = 0;

                const data = await response.json();

                // Normalize status to uppercase for comparison
                const normalizedStatus = data.status.toUpperCase();
                console.log(`[DEBUG] Job ${id} status: ${normalizedStatus}`);

                if (normalizedStatus === 'COMPLETED') {
                    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);

                    setLogs(prev => [...prev, 'Job completed. Retrieving results...']);

                    // Fetch the JSON result for dashboard
                    try {
                        const resultResponse = await authenticatedFetch(`${apiUrl}/jobs/${id}/result`, getToken);

                        if (resultResponse.ok) {
                            const resultData = await resultResponse.json();
                            setResults(resultData);
                            setLogs(prev => [...prev, 'Results retrieved successfully.']);
                        } else {
                            console.warn("Failed to retrieve JSON results, using fallback.");
                            // Fallback result object to allow download button to appear
                            setResults({
                                job_id: id,
                                total_test_count: 0,
                                gamp_category: 'Unknown (JSON Missing)',
                                estimated_execution_time: 0,
                                document_name: 'Unknown',
                                timestamp: new Date().toISOString(),
                                workflow_session_id: 'N/A',
                                requirements_coverage: {},
                                pharmaceutical_compliance: {},
                                test_cases: []
                            });
                            setLogs(prev => [...prev, 'WARNING: Could not retrieve detailed results JSON. You can still try downloading the test suite.']);
                        }

                        // Always set status to COMPLETED if the backend says so
                        setStatus('COMPLETED');
                        fetchJobs(); // Refresh history

                    } catch (err) {
                        console.error("Error fetching results:", err);
                        // Even on error, set COMPLETED with fallback so user can try to download
                        setStatus('COMPLETED');
                        setResults({
                            job_id: id,
                            total_test_count: 0,
                            gamp_category: 'Error Loading Results',
                            estimated_execution_time: 0,
                            document_name: 'Unknown',
                            timestamp: new Date().toISOString(),
                            workflow_session_id: 'N/A',
                            requirements_coverage: {},
                            pharmaceutical_compliance: {},
                            test_cases: []
                        });
                        setLogs(prev => [...prev, 'ERROR: Failed to retrieve result data. Download may still be available.']);
                    }

                } else if (normalizedStatus === 'FAILED') {
                    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
                    setStatus('FAILED');
                    setLogs(prev => [...prev, `Job failed: ${data.error_message || 'Unknown error'}`]);
                } else if (normalizedStatus === 'AWAITING_APPROVAL') {
                    // Detected HIL status - update local state AND show modal immediately
                    // CRITICAL FIX: Don't rely on separate approval poll - show modal now to prevent
                    // race condition where user submits new job before modal appears
                    console.log(`[DEBUG] Job ${id} awaiting human approval - triggering modal`);
                    setStatus('AWAITING_APPROVAL');
                    setShowApprovalModal(true);  // Show modal immediately!
                    // Keep polling to get updated timeout countdown
                } else {
                    // Still processing (PENDING or PROCESSING)
                    // We can add "heartbeat" logs occasionally or just wait
                    // setLogs(prev => [...prev, `Processing... (${new Date().toLocaleTimeString()})`]);
                }

            } catch (e) {
                consecutiveFailures++;
                console.error(`[DEBUG] Polling exception (failure ${consecutiveFailures}/${MAX_CONSECUTIVE_FAILURES}):`, e);

                // Expose error to user after multiple failures (NO FALLBACK LOGIC)
                if (consecutiveFailures >= MAX_CONSECUTIVE_FAILURES) {
                    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
                    setStatus('FAILED');
                    setLogs(prev => [...prev, `ERROR: Lost connection to server after ${MAX_CONSECUTIVE_FAILURES} attempts. ${e instanceof Error ? e.message : 'Unknown error'}`]);
                }
            } finally {
                // Always reset in-flight flag so next poll cycle can proceed
                isPollingInFlight.current = false;
            }
        }, 2000);
    }, [getToken, fetchJobs]);

    // Resume async operations on mount (state already initialized via lazy init)
    // CRITICAL: Validate that localStorage job still exists on server before trusting it
    useEffect(() => {
        if (!isLoaded) return;

        // State is already restored from localStorage via lazy initialization
        // But we MUST validate the job exists on server - localStorage may be stale
        // (e.g., server restarted and in-memory jobs were lost)
        const validateAndResume = async () => {
            if (!jobId || !status) {
                console.log('[DEBUG] No localStorage state to restore');
                return;
            }

            const apiUrl = getApiBaseUrl();
            console.log(`[DEBUG] Validating localStorage job ${jobId} (status: ${status})`);

            // CRITICAL: Validate job exists on server BEFORE trusting localStorage
            if (status === 'PENDING' || status === 'PROCESSING' || status === 'AWAITING_APPROVAL') {
                try {
                    console.log(`[DEBUG] Fetching job status from ${apiUrl}/jobs/${jobId}`);
                    const response = await authenticatedFetch(`${apiUrl}/jobs/${jobId}`, getToken);

                    if (response.status === 404) {
                        // Job doesn't exist on server - localStorage is stale
                        console.warn(`[DEBUG] Job ${jobId} not found on server (404) - clearing stale localStorage`);
                        resetDashboard();
                        setLogs(['Previous job session expired (server may have restarted). Please submit a new job.']);
                        return;
                    }

                    if (!response.ok) {
                        // Other error - log but don't clear state yet
                        console.error(`[DEBUG] Job validation failed: ${response.status} ${response.statusText}`);
                        const errorText = await response.text();
                        console.error(`[DEBUG] Error details: ${errorText}`);
                        // Show error but keep state - might be temporary network issue
                        setLogs(prev => [...prev, `Warning: Could not validate job status (${response.status})`]);
                    } else {
                        // Job exists - get current status from server (source of truth)
                        const jobData = await response.json();
                        const serverStatus = jobData.status.toUpperCase();
                        console.log(`[DEBUG] Server reports job status: ${serverStatus}`);

                        // Update local status to match server
                        if (serverStatus !== status) {
                            console.log(`[DEBUG] Updating local status from ${status} to ${serverStatus}`);
                            setStatus(serverStatus as JobStatus);
                        }

                        // Resume polling if still active
                        if (serverStatus === 'PENDING' || serverStatus === 'PROCESSING') {
                            console.log(`[DEBUG] Job is active, resuming polling`);
                            pollJobStatus(jobId, apiUrl);
                        } else if (serverStatus === 'COMPLETED' && !results) {
                            // Fetch results for completed job
                            console.log(`[DEBUG] Job completed, fetching results`);
                            const resultResponse = await authenticatedFetch(`${apiUrl}/jobs/${jobId}/result`, getToken);
                            if (resultResponse.ok) {
                                const resultData = await resultResponse.json();
                                setResults(resultData);
                            }
                        } else if (serverStatus === 'AWAITING_APPROVAL') {
                            console.log(`[DEBUG] Job awaiting approval`);
                            setShowApprovalModal(true);
                        } else if (serverStatus === 'FAILED') {
                            console.log(`[DEBUG] Job failed on server`);
                            setLogs(prev => [...prev, `Job failed: ${jobData.error_message || 'Unknown error'}`]);
                        }
                    }
                } catch (e) {
                    console.error('[DEBUG] Failed to validate job:', e);
                    // Network error - keep state but warn user
                    setLogs(prev => [...prev, `Warning: Network error validating job. Will retry...`]);
                    // Try to resume polling anyway - might recover
                    pollJobStatus(jobId, apiUrl);
                }
            } else if (status === 'COMPLETED' && !results) {
                // Fetch results for completed job
                try {
                    const resultResponse = await authenticatedFetch(`${apiUrl}/jobs/${jobId}/result`, getToken);
                    if (resultResponse.ok) {
                        const resultData = await resultResponse.json();
                        setResults(resultData);
                    } else if (resultResponse.status === 404) {
                        // Job doesn't exist - clear stale state
                        resetDashboard();
                    }
                } catch (e) {
                    console.error("Failed to restore completed job results", e);
                }
            }
        };

        validateAndResume();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isLoaded]); // Only run when Clerk finishes loading (other deps intentionally excluded)

    const handleDownload = async () => {
        if (!jobId) return;
        const apiUrl = getApiBaseUrl();
        const url = `${apiUrl}/jobs/${jobId}/download`;

        try {
            const response = await authenticatedFetch(url, getToken);

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Download failed: ${response.status} ${response.statusText} - ${errorText}`);
            }

            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = `test_suite_${jobId}.yaml`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(downloadUrl);
            document.body.removeChild(a);
        } catch (e) {
            console.error("Download error:", e);
            alert(`Failed to download file: ${e instanceof Error ? e.message : 'Unknown error'}`);
        }
    };

    const handleHistoryDownload = async (job: any) => {
        const apiUrl = getApiBaseUrl();
        const url = `${apiUrl}/jobs/${job.job_id}/download`;

        try {
            const response = await authenticatedFetch(url, getToken);

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Download failed: ${response.status} ${response.statusText} - ${errorText}`);
            }

            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = `test_suite_${job.job_id}.yaml`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(downloadUrl);
            document.body.removeChild(a);
        } catch (e) {
            console.error("Download error:", e);
            alert(`Failed to download file: ${e instanceof Error ? e.message : 'Unknown error'}`);
        }
    };

    const resetDashboard = () => {
        setStatus('IDLE');
        setJobId(null);
        setLogs([]);
        setResults(null);
        setSelectedFile(null);
        setJobStartTime(null); // Reset start time
        setShowApprovalModal(false);
    };

    const handleApprovalSubmitted = () => {
        // Approval submitted - refetch status and close modal
        setShowApprovalModal(false);
        refetchApprovalStatus();
        setLogs(prev => [...prev, 'Human approval decision submitted. Resuming workflow...']);
        setStatus('PROCESSING');
    };

    if (!isLoaded) {
        return (
            <Layout>
                <div className="flex items-center justify-center min-h-[60vh]">
                    <div className="animate-pulse flex flex-col items-center">
                        <div className="h-12 w-12 bg-blue-600/20 rounded-full mb-4 animate-ping"></div>
                        <div className="text-slate-400">Loading secure environment...</div>
                    </div>
                </div>
            </Layout>
        );
    }

    return (
        <>
            <Head>
                <title>Generate Test Suite - PharmaGen AI</title>
                <meta name="description" content="GAMP-5 compliant pharmaceutical test generation dashboard" />
            </Head>
            <Layout>
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">

                    {/* Welcome Section */}
                    <div className="flex justify-between items-end">
                        <div>
                            <h1 className="text-3xl font-bold text-white">
                                Welcome, <span className="text-blue-400">{displayName}</span>
                            </h1>
                            <p className="mt-2 text-slate-400">
                                Manage your pharmaceutical test generation workflows
                            </p>
                        </div>
                        {status !== 'IDLE' && (
                            <button
                                onClick={resetDashboard}
                                className="text-sm text-slate-400 hover:text-white transition-colors flex items-center gap-2"
                            >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                </svg>
                                Start New Job
                            </button>
                        )}
                    </div>

                    {/* Approval Modal */}
                    {approvalStatus?.categorization_result && (
                        <ApprovalModal
                            isOpen={showApprovalModal}
                            onClose={() => setShowApprovalModal(false)}
                            jobId={jobId!}
                            categorizationResult={approvalStatus.categorization_result}
                            timeoutRemainingSeconds={approvalStatus.timeout_remaining_seconds}
                            onApprovalSubmitted={handleApprovalSubmitted}
                        />
                    )}

                    {/* Main Content Area */}
                    <div className="min-h-[500px]">
                        {status === 'AWAITING_APPROVAL' && (
                            <div className="animate-fade-in">
                                <div className="max-w-3xl mx-auto">
                                    <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-8 text-center space-y-6">
                                        <div className="w-16 h-16 bg-amber-500/20 rounded-full flex items-center justify-center mx-auto">
                                            <svg className="w-8 h-8 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                            </svg>
                                        </div>
                                        <div>
                                            <h3 className="text-2xl font-bold text-amber-400 mb-2">Awaiting Human Approval</h3>
                                            <p className="text-slate-300 text-lg mb-2">
                                                {approvalStatus?.approval_reason || 'AI detected ambiguity in categorization'}
                                            </p>
                                            {approvalStatus?.categorization_result && (
                                                <div className="mt-4 p-4 bg-slate-800/50 rounded-lg border border-slate-700">
                                                    <p className="text-sm text-slate-400 mb-1">AI Recommendation</p>
                                                    <p className="text-xl font-bold text-blue-400 mb-2">
                                                        Category {approvalStatus.categorization_result.gamp_category}
                                                    </p>
                                                    <p className="text-sm text-slate-300">
                                                        Confidence: <span className="font-bold">
                                                            {(approvalStatus.categorization_result.confidence_score * 100).toFixed(0)}%
                                                        </span>
                                                    </p>
                                                </div>
                                            )}
                                            {approvalStatus?.timeout_remaining_seconds != null && (
                                                <p className="text-sm text-amber-300 mt-4">
                                                    Time remaining: {Math.floor(approvalStatus.timeout_remaining_seconds / 60)}:{String(approvalStatus.timeout_remaining_seconds % 60).padStart(2, '0')}
                                                </p>
                                            )}
                                        </div>
                                        <button
                                            onClick={() => setShowApprovalModal(true)}
                                            className="btn-primary bg-amber-600 hover:bg-amber-700"
                                        >
                                            Review Approval Request
                                        </button>
                                    </div>
                                </div>
                            </div>
                        )}

                        {status === 'IDLE' && (
                            <div className="animate-fade-in space-y-8">
                                {!selectedFile ? (
                                    <FileUpload onFileSelect={handleFileSelect} isUploading={false} />
                                ) : (
                                    <div className="max-w-2xl mx-auto">
                                        <div className="bg-slate-800/50 border border-blue-500/30 rounded-xl p-8 text-center space-y-6">
                                            <div className="w-16 h-16 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto">
                                                <svg className="w-8 h-8 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                                </svg>
                                            </div>
                                            <div>
                                                <h3 className="text-xl font-medium text-white mb-2">Ready to Generate</h3>
                                                <p className="text-slate-400">
                                                    Selected file: <span className="text-blue-400 font-mono">{selectedFile.name}</span>
                                                </p>
                                                <p className="text-xs text-slate-400 mt-2">
                                                    {(selectedFile.size / 1024).toFixed(2)} KB
                                                </p>
                                            </div>

                                            <div className="flex gap-4 justify-center">
                                                <button
                                                    onClick={() => setSelectedFile(null)}
                                                    className="px-6 py-3 rounded-lg border border-slate-600 text-slate-300 hover:bg-slate-800 transition-colors"
                                                >
                                                    Cancel
                                                </button>
                                                <button
                                                    onClick={handleGenerate}
                                                    className="btn-primary flex items-center gap-2"
                                                >
                                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                                    </svg>
                                                    Generate Test Suite
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
                                    <FeatureCard
                                        title="GAMP-5 Compliant"
                                        description="Automated categorization and validation logic aligned with ISPE GAMP 5 guidelines."
                                        icon="shield"
                                    />
                                    <FeatureCard
                                        title="AI-Powered Analysis"
                                        description="Advanced LLM processing to extract requirements and generate precise test cases."
                                        icon="chip"
                                    />
                                    <FeatureCard
                                        title="Audit Ready"
                                        description="Full ALCOA+ traceability with immutable logs and user attribution."
                                        icon="document"
                                    />
                                </div>
                            </div>
                        )}

                        {(status === 'PENDING' || status === 'PROCESSING') && (
                            <div className="animate-fade-in">
                                <JobProgress status={status} logs={logs} startTime={jobStartTime} jobId={jobId || undefined} />
                            </div>
                        )}

                        {status === 'COMPLETED' && results && (
                            <ComplianceDashboard results={results} onDownload={handleDownload} />
                        )}

                        {status === 'FAILED' && (
                            <div className="text-center py-12 animate-fade-in">
                                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-500/10 mb-4">
                                    <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                </div>
                                <h3 className="text-xl font-medium text-white mb-2">Generation Failed</h3>
                                <p className="text-slate-400 mb-6">An error occurred while processing your request.</p>
                                <button onClick={resetDashboard} className="btn-primary">Try Again</button>

                                <div className="mt-8 max-w-2xl mx-auto text-left">
                                    <div className="bg-slate-900/50 rounded-lg p-4 border border-red-500/20 font-mono text-sm text-red-400">
                                        {logs[logs.length - 1]}
                                    </div>
                                </div>
                            </div>
                        )}

                        {status === 'EXPIRED' && (
                            <div className="text-center py-12 animate-fade-in">
                                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-amber-500/10 mb-4">
                                    <svg className="w-8 h-8 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                </div>
                                <h3 className="text-xl font-medium text-white mb-2">Session Expired</h3>
                                <p className="text-slate-400 mb-6">The job session is no longer available (server may have restarted).</p>
                                <button onClick={resetDashboard} className="btn-primary bg-amber-600 hover:bg-amber-700">Start New Job</button>
                            </div>
                        )}
                    </div>
                </div>
            </Layout>
        </>
    );
}

function FeatureCard({ title, description, icon }: { title: string, description: string, icon: string }) {
    return (
        <div className="card hover:bg-slate-800/80 transition-colors group">
            <div className="w-12 h-12 bg-blue-500/10 rounded-lg flex items-center justify-center mb-4 group-hover:bg-blue-500/20 transition-colors">
                {icon === 'shield' && (
                    <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                    </svg>
                )}
                {icon === 'chip' && (
                    <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                    </svg>
                )}
                {icon === 'document' && (
                    <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                )}
            </div>
            <h3 className="text-lg font-medium text-white mb-2">{title}</h3>
            <p className="text-slate-400 text-sm">{description}</p>
        </div>
    );
}

import { useState, useEffect, useRef, useCallback } from 'react';
import { useUser, useAuth } from '@clerk/nextjs';
import Layout from '@/components/Layout';
import Head from 'next/head';
import FileUpload from '@/components/FileUpload';
import JobProgress from '@/components/JobProgress';
import ComplianceDashboard from '@/components/ComplianceDashboard';
import ApprovalModal from '@/components/ApprovalModal';
import TemplateSelector from '@/components/TemplateSelector';
import TemplateEditor from '@/components/TemplateEditor';
import { useJobStatusPolling } from '@/hooks/useJobStatusPolling';
import { authenticatedFetch, getApiBaseUrl } from '@/lib/authenticatedFetch';
import { URSTemplate, URSTemplateData, cloneTemplateData } from '@/lib/templates';
import { motion, AnimatePresence } from 'framer-motion';
import Background3D from '@/components/Background3D';
import InteractiveQuiz from '@/components/quiz/InteractiveQuiz';

type JobStatus = 'IDLE' | 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'EXPIRED' | 'AWAITING_APPROVAL' | 'APPROVED' | 'REJECTED';

const STAGE_PROGRESS_MAP: Record<string, number> = {
    queued: 0,
    ingestion: 10,
    categorization: 25,
    hil_waiting: 30,
    planning: 45,
    agent_execution: 65,
    oq_generation: 85,
    completion: 100
};

const STAGE_LABEL_MAP: Record<string, string> = {
    queued: 'Queued',
    ingestion: 'Loading Document',
    categorization: 'GAMP-5 Classification',
    hil_waiting: 'Awaiting Human Approval',
    planning: 'Planning Test Strategy',
    agent_execution: 'Executing AI Agents',
    oq_generation: 'Generating Test Cases',
    completion: 'Finalizing Results'
};

const STAGE_ORDER_MAP: Record<string, number> = {
    queued: 0,
    ingestion: 1,
    categorization: 2,
    hil_waiting: 3,
    planning: 4,
    agent_execution: 5,
    oq_generation: 6,
    completion: 7
};

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
        const savedJobId = localStorage.getItem('activeJobId');
        const savedStatus = localStorage.getItem('activeJobStatus') as JobStatus;
        // Only restore non-IDLE status if jobId exists (prevents orphaned status)
        if (savedJobId && savedStatus && savedStatus !== 'IDLE') {
            return savedStatus;
        }
        return 'IDLE';
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

    // CRITICAL: Use ref for getToken to prevent stale closure in polling
    // Clerk refreshes JWT tokens every 60s, but setInterval captures old getToken
    // Without this ref, polling would use stale tokens causing 401 errors
    const getTokenRef = useRef(getToken);

    // Progress tracking from backend - restored from localStorage on navigation
    const [currentStage, setCurrentStage] = useState<string | null>(() => {
        if (typeof window === 'undefined') return null;
        return localStorage.getItem('currentStage');
    });
    const [currentStageLabel, setCurrentStageLabel] = useState<string | null>(() => {
        if (typeof window === 'undefined') return null;
        return localStorage.getItem('currentStageLabel');
    });
    const [progressPercentage, setProgressPercentage] = useState<number | null>(() => {
        if (typeof window === 'undefined') return null;
        const saved = localStorage.getItem('progressPercentage');
        return saved ? parseInt(saved, 10) : null;
    });

    // Displayed progress - tracks what the user actually SAW, not backend progress
    // This is what the animation reached before navigation
    const [displayedProgress, setDisplayedProgress] = useState<number>(() => {
        if (typeof window === 'undefined') return 0;
        const saved = localStorage.getItem('displayedProgress');
        return saved ? parseFloat(saved) : 0;
    });

    const lastStageTimestampRef = useRef<number | null>(null);
    const lastStageOrderRef = useRef<number>(-1);
    const progressJobRef = useRef<string | null>(null);

    const resetProgressGuards = useCallback(() => {
        lastStageTimestampRef.current = null;
        lastStageOrderRef.current = -1;
        progressJobRef.current = null;
    }, []);

    // Validation state - prevents rendering stale job UI before server validation
    // Starts true if there's a saved job that needs checking
    const [isValidating, setIsValidating] = useState<boolean>(() => {
        if (typeof window === 'undefined') return false;
        const savedJobId = localStorage.getItem('activeJobId');
        const savedStatus = localStorage.getItem('activeJobStatus');
        return !!(savedJobId && savedStatus && savedStatus !== 'IDLE');
    });

    // AbortController for cancelling poll requests on unmount/navigation
    const pollAbortControllerRef = useRef<AbortController | null>(null);

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

    // Template mode state
    type InputMode = 'select' | 'edit' | 'upload';
    const [inputMode, setInputMode] = useState<InputMode>('select');
    const [selectedTemplate, setSelectedTemplate] = useState<URSTemplate | null>(null);
    const [templateData, setTemplateData] = useState<URSTemplateData | null>(null);

    const handleFileSelect = (file: File) => {
        setSelectedFile(file);
    };

    // Template selection handler
    const handleTemplateSelect = (template: URSTemplate) => {
        setSelectedTemplate(template);
        setTemplateData(cloneTemplateData(template.data));
        setInputMode('edit');
    };

    // Template submission handler - converts to File and uses existing flow
    const handleTemplateSubmit = (markdown: string) => {
        // Convert markdown to File object
        const blob = new Blob([markdown], { type: 'text/markdown' });
        const filename = `${selectedTemplate?.id || 'template'}.md`;
        const file = new File([blob], filename, { type: 'text/markdown' });

        // Set as selected file
        setSelectedFile(file);

        // Reset template state
        setInputMode('select');
        setSelectedTemplate(null);
        setTemplateData(null);

        // Trigger generation after a brief delay for state to update
        setTimeout(() => {
            // The file is now set, so handleGenerate will use it
            const generateBtn = document.querySelector('[data-generate-trigger]') as HTMLButtonElement;
            if (generateBtn) {
                generateBtn.click();
            }
        }, 100);
    };

    // Back to template selector
    const handleBackToTemplates = () => {
        setInputMode('select');
        setSelectedTemplate(null);
        setTemplateData(null);
    };

    // /jobs/{id} polling is the single source of truth for progress and stage data.
    const applyAuthoritativeProgress = useCallback((payload: {
        job_id?: string | null;
        created_at?: string | null;
        status?: string | null;
        current_stage?: string | null;
        current_stage_label?: string | null;
        progress_percentage?: number | null;
        stage_started_at?: string | null;
    }) => {
        const payloadJobId = payload.job_id ?? jobId ?? null;
        if (payloadJobId && progressJobRef.current && payloadJobId !== progressJobRef.current) {
            resetProgressGuards();
        }
        if (payloadJobId) {
            progressJobRef.current = payloadJobId;
        }

        const normalizedStatus = payload.status ? payload.status.toUpperCase() : null;
        const isTerminalStatus = normalizedStatus ? ['COMPLETED', 'FAILED', 'REJECTED'].includes(normalizedStatus) : false;

        let stageFromPayload = payload.current_stage ?? null;
        if (isTerminalStatus) {
            stageFromPayload = 'completion';
        }

        const stageOrder = stageFromPayload ? STAGE_ORDER_MAP[stageFromPayload] ?? null : null;
        const stageTimestampMs = payload.stage_started_at ? Date.parse(payload.stage_started_at) : null;
        const createdAtMs = payload.created_at ? Date.parse(payload.created_at) : null;
        const jobStartReference = jobStartTime ?? createdAtMs ?? null;

        const stageAfterJobStart =
            stageTimestampMs === null ||
            jobStartReference === null ||
            (!Number.isNaN(stageTimestampMs) && stageTimestampMs >= jobStartReference - 1000);

        const timestampForward =
            stageTimestampMs === null ||
            lastStageTimestampRef.current === null ||
            stageTimestampMs >= lastStageTimestampRef.current;

        const orderForward =
            stageOrder === null ||
            lastStageOrderRef.current === -1 ||
            stageOrder >= lastStageOrderRef.current;

        const shouldIgnore =
            !isTerminalStatus &&
            (!stageAfterJobStart || (stageTimestampMs !== null && !timestampForward) || (stageTimestampMs === null && !orderForward));

        if (shouldIgnore) {
            console.log('[PROGRESS-DEBUG] Ignoring stale stage payload', {
                stage: stageFromPayload,
                stageStartedAt: payload.stage_started_at,
                progress: payload.progress_percentage
            });
            return;
        }

        if (stageTimestampMs !== null && !Number.isNaN(stageTimestampMs)) {
            lastStageTimestampRef.current = stageTimestampMs;
        } else if (isTerminalStatus) {
            lastStageTimestampRef.current = Date.now();
        }

        if (stageOrder !== null) {
            lastStageOrderRef.current = Math.max(lastStageOrderRef.current, stageOrder);
        }

        const hasStageField = Object.prototype.hasOwnProperty.call(payload, 'current_stage') || isTerminalStatus;
        const hasLabelField = Object.prototype.hasOwnProperty.call(payload, 'current_stage_label') || hasStageField;
        const hasProgressField = Object.prototype.hasOwnProperty.call(payload, 'progress_percentage') || hasStageField;

        if (hasStageField) {
            setCurrentStage(stageFromPayload);
        }

        if (hasLabelField) {
            const labelFromPayload = payload.current_stage_label ?? null;
            const fallbackLabel = stageFromPayload ? STAGE_LABEL_MAP[stageFromPayload] ?? null : null;
            setCurrentStageLabel(labelFromPayload ?? fallbackLabel ?? null);
        }

        if (hasProgressField) {
            if (typeof payload.progress_percentage === 'number') {
                setProgressPercentage(payload.progress_percentage);
            } else if (stageFromPayload && STAGE_PROGRESS_MAP[stageFromPayload] !== undefined) {
                setProgressPercentage(STAGE_PROGRESS_MAP[stageFromPayload]);
            } else if (isTerminalStatus) {
                setProgressPercentage(100);
            } else {
                setProgressPercentage(null);
            }
        }
    }, [jobId, jobStartTime, resetProgressGuards]);

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
            // Cancel any in-flight poll request
            if (pollAbortControllerRef.current) {
                pollAbortControllerRef.current.abort();
            }
            if (pollIntervalRef.current) {
                clearInterval(pollIntervalRef.current);
            }
        };
    }, []);

    // Keep getTokenRef updated when Clerk refreshes the token
    // This prevents stale closure issues in long-running polling intervals
    useEffect(() => {
        getTokenRef.current = getToken;
    }, [getToken]);

    // Detect when approval is required
    useEffect(() => {
        if (approvalStatus?.requires_approval && approvalStatus.status.toUpperCase() === 'AWAITING_APPROVAL') {
            setStatus('AWAITING_APPROVAL');
            setShowApprovalModal(true);
        }
    }, [approvalStatus]);

    // Approval polling stays focused on human-in-the-loop flows.
    // Progress/state updates now rely exclusively on pollJobStatus to avoid race conditions.

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
            resetProgressGuards();
        }
    }, [jobId, resetProgressGuards]);

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

    // Persist progress tracking to localStorage on change
    useEffect(() => {
        if (currentStage) {
            localStorage.setItem('currentStage', currentStage);
        } else {
            localStorage.removeItem('currentStage');
        }
    }, [currentStage]);

    useEffect(() => {
        if (currentStageLabel) {
            localStorage.setItem('currentStageLabel', currentStageLabel);
        } else {
            localStorage.removeItem('currentStageLabel');
        }
    }, [currentStageLabel]);

    useEffect(() => {
        if (progressPercentage !== null) {
            localStorage.setItem('progressPercentage', progressPercentage.toString());
        } else {
            localStorage.removeItem('progressPercentage');
        }
    }, [progressPercentage]);

    // Persist displayedProgress - tracks what user saw
    useEffect(() => {
        if (displayedProgress > 0) {
            localStorage.setItem('displayedProgress', displayedProgress.toString());
        } else {
            localStorage.removeItem('displayedProgress');
        }
    }, [displayedProgress]);

    // Callback for JobProgress to report its current display value
    const handleProgressChange = useCallback((progress: number) => {
        setDisplayedProgress(progress);
    }, []);

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
        // Clear any stale progress before the new job starts polling
        setCurrentStage(null);
        setCurrentStageLabel(null);
        setProgressPercentage(null);
        setDisplayedProgress(0);
        resetProgressGuards();

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

        // Cancel any previous abort controller
        if (pollAbortControllerRef.current) {
            pollAbortControllerRef.current.abort();
        }

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

            // Create new AbortController for this request
            pollAbortControllerRef.current = new AbortController();
            const signal = pollAbortControllerRef.current.signal;

            try {
                console.log(`[DEBUG] Polling job status: GET ${apiUrl}/jobs/${id}`);
                // Use authenticatedFetch with getTokenRef to prevent stale closure
                // getTokenRef.current always has the latest token from Clerk
                const response = await authenticatedFetch(`${apiUrl}/jobs/${id}`, getTokenRef.current, {}, signal);

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
                            const finalCheckResponse = await authenticatedFetch(`${apiUrl}/jobs/${id}`, getTokenRef.current);
                            if (finalCheckResponse.ok) {
                                const finalData = await finalCheckResponse.json();
                                const finalStatus = finalData.status.toUpperCase();
                                console.log(`[DEBUG] Final check: job status is ${finalStatus}`);

                                if (finalStatus === 'COMPLETED') {
                                    // Job actually completed! Fetch results instead of showing error
                                    setLogs(prev => [...prev, 'Job completed (recovered from polling errors). Retrieving results...']);
                                    const resultResponse = await authenticatedFetch(`${apiUrl}/jobs/${id}/result`, getTokenRef.current);
                                    if (resultResponse.ok) {
                                        const resultData = await resultResponse.json();
                                        // Merge trace info from job data for observability
                                        setResults({
                                            ...resultData,
                                            job_id: finalData.job_id,
                                            trace_id: finalData.trace_id,
                                            trace_url: finalData.trace_url
                                        });
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
                console.log(`[DEBUG] Job ${id} status: ${normalizedStatus}, stage: ${data.current_stage}, label: ${data.current_stage_label}, progress: ${data.progress_percentage}%`);

                // Synchronize stage/progress from the authoritative job endpoint only.
                applyAuthoritativeProgress(data);

                if (normalizedStatus === 'COMPLETED') {
                    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);

                    setLogs(prev => [...prev, 'Job completed. Retrieving results...']);

                    // Fetch the JSON result for dashboard
                    try {
                        // CRITICAL FIX (Round 2): Fetch fresh job data with RETRY LOOP
                        // NEVER fall back to stale polling 'data' which may have undefined trace_id
                        // The issue: if polling had 401 errors, 'data' could be from a failed response
                        let freshJobData = null;
                        for (let attempt = 1; attempt <= 3; attempt++) {
                            try {
                                console.log(`[DEBUG] Fresh job fetch attempt ${attempt}/3`);
                                const freshJobResponse = await authenticatedFetch(
                                    `${apiUrl}/jobs/${id}`,
                                    getTokenRef.current
                                );
                                if (freshJobResponse.ok) {
                                    freshJobData = await freshJobResponse.json();
                                    console.log(`[DEBUG] Fresh job data retrieved:`, {
                                        job_id: freshJobData.job_id,
                                        trace_id: freshJobData.trace_id,
                                        trace_url: freshJobData.trace_url
                                    });
                                    break;
                                } else {
                                    console.warn(`[DEBUG] Fresh job fetch attempt ${attempt} returned ${freshJobResponse.status}`);
                                }
                                // Wait before retry (exponential backoff)
                                if (attempt < 3) {
                                    await new Promise(r => setTimeout(r, 1000 * attempt));
                                }
                            } catch (fetchErr) {
                                console.warn(`[DEBUG] Fresh job fetch attempt ${attempt} failed:`, fetchErr);
                                if (attempt < 3) {
                                    await new Promise(r => setTimeout(r, 1000 * attempt));
                                }
                            }
                        }

                        // If all retries failed, use job ID from URL param but mark trace as unavailable
                        if (!freshJobData) {
                            console.error('[DEBUG] Could not fetch fresh job data after 3 attempts - trace info will be unavailable');
                            freshJobData = {
                                job_id: id,
                                trace_id: undefined,
                                trace_url: undefined
                            };
                        }

                        const resultResponse = await authenticatedFetch(`${apiUrl}/jobs/${id}/result`, getTokenRef.current);

                        if (resultResponse.ok) {
                            const resultData = await resultResponse.json();
                            // Merge trace info from FRESH job data (NEVER stale polling data)
                            const finalResults = {
                                ...resultData,
                                job_id: freshJobData.job_id || id,
                                trace_id: freshJobData.trace_id,
                                trace_url: freshJobData.trace_url
                            };
                            console.log('[DEBUG] Setting results with:', {
                                job_id: finalResults.job_id,
                                trace_id: finalResults.trace_id,
                                trace_url: finalResults.trace_url
                            });
                            setResults(finalResults);
                            setLogs(prev => [...prev, 'Results retrieved successfully.']);
                        } else {
                            console.warn("Failed to retrieve JSON results, using fallback.");
                            // Fallback result object to allow download button to appear
                            const fallbackResults = {
                                job_id: freshJobData.job_id || id,
                                trace_id: freshJobData.trace_id,
                                trace_url: freshJobData.trace_url,
                                total_test_count: 0,
                                gamp_category: 'Unknown (JSON Missing)',
                                estimated_execution_time: 0,
                                document_name: 'Unknown',
                                timestamp: new Date().toISOString(),
                                workflow_session_id: 'N/A',
                                requirements_coverage: {},
                                pharmaceutical_compliance: {},
                                test_cases: []
                            };
                            console.log('[DEBUG] Setting fallback results with:', {
                                job_id: fallbackResults.job_id,
                                trace_id: fallbackResults.trace_id,
                                trace_url: fallbackResults.trace_url
                            });
                            setResults(fallbackResults);
                            setLogs(prev => [...prev, 'WARNING: Could not retrieve detailed results JSON. You can still try downloading the test suite.']);
                        }

                        // Always set status to COMPLETED if the backend says so
                        setStatus('COMPLETED');
                        fetchJobs(); // Refresh history

                    } catch (err) {
                        console.error("Error fetching results:", err);
                        // Even on error, set COMPLETED with fallback so user can try to download
                        // Try to get fresh job data for trace info with retry loop
                        let jobDataForFallback = { job_id: id, trace_id: undefined, trace_url: undefined };
                        for (let attempt = 1; attempt <= 3; attempt++) {
                            try {
                                console.log(`[DEBUG] Fallback job fetch attempt ${attempt}/3`);
                                const fallbackJobResponse = await authenticatedFetch(`${apiUrl}/jobs/${id}`, getTokenRef.current);
                                if (fallbackJobResponse.ok) {
                                    jobDataForFallback = await fallbackJobResponse.json();
                                    console.log(`[DEBUG] Fallback job data retrieved:`, {
                                        job_id: jobDataForFallback.job_id,
                                        trace_id: jobDataForFallback.trace_id,
                                        trace_url: jobDataForFallback.trace_url
                                    });
                                    break;
                                }
                                if (attempt < 3) await new Promise(r => setTimeout(r, 1000 * attempt));
                            } catch {
                                if (attempt < 3) await new Promise(r => setTimeout(r, 1000 * attempt));
                            }
                        }

                        setStatus('COMPLETED');
                        const errorFallbackResults = {
                            job_id: jobDataForFallback.job_id || id,
                            trace_id: jobDataForFallback.trace_id,
                            trace_url: jobDataForFallback.trace_url,
                            total_test_count: 0,
                            gamp_category: 'Error Loading Results',
                            estimated_execution_time: 0,
                            document_name: 'Unknown',
                            timestamp: new Date().toISOString(),
                            workflow_session_id: 'N/A',
                            requirements_coverage: {},
                            pharmaceutical_compliance: {},
                            test_cases: []
                        };
                        console.log('[DEBUG] Setting error fallback results with:', {
                            job_id: errorFallbackResults.job_id,
                            trace_id: errorFallbackResults.trace_id,
                            trace_url: errorFallbackResults.trace_url
                        });
                        setResults(errorFallbackResults);
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
                    // Use setState callback to avoid stale closure - compare against current state
                    setStatus(prevStatus => {
                        if (normalizedStatus !== prevStatus) {
                            console.log(`[DEBUG] Status changed: ${prevStatus} → ${normalizedStatus}`);
                            return normalizedStatus as JobStatus;
                        }
                        return prevStatus;
                    });
                }

            } catch (e: any) {
                // Ignore AbortError - happens on unmount/navigation, not a real error
                if (e.name === 'AbortError') {
                    console.log('[DEBUG] Poll request aborted (navigation/unmount)');
                    return;
                }

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
    }, [getToken, fetchJobs, applyAuthoritativeProgress]);

    // Resume async operations on mount (state already initialized via lazy init)
    // CRITICAL: Validate that localStorage job still exists on server before trusting it
    useEffect(() => {
        if (!isLoaded) return;

        // State is already restored from localStorage via lazy initialization
        // But we MUST validate the job exists on server - localStorage may be stale
        // (e.g., server restarted and in-memory jobs were lost)
        const validateAndResume = async () => {
            // If no job to validate, clear validating state immediately
            if (!jobId || status === 'IDLE') {
                console.log('[DEBUG] No localStorage state to restore');
                setIsValidating(false);
                return;
            }

            const apiUrl = getApiBaseUrl();
            console.log(`[DEBUG] Validating localStorage job ${jobId} (status: ${status})`);

            // CRITICAL: Validate job exists on server BEFORE trusting localStorage
            // After the early return above, we know jobId exists and status !== 'IDLE'
            try {
                console.log(`[DEBUG] Fetching job status from ${apiUrl}/jobs/${jobId}`);
                const response = await authenticatedFetch(`${apiUrl}/jobs/${jobId}`, getTokenRef.current);

                if (response.status === 404) {
                    // Job doesn't exist on server - localStorage is stale
                    console.warn(`[DEBUG] Job ${jobId} not found on server (404) - clearing stale localStorage`);
                    resetDashboard();
                    setLogs(['Previous job session expired (server may have restarted). Please submit a new job.']);
                    setIsValidating(false);
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

                    // Restore progress state from server (in case localStorage is stale)
                    applyAuthoritativeProgress(jobData);

                    // Resume polling if still active
                    if (serverStatus === 'PENDING' || serverStatus === 'PROCESSING') {
                        console.log(`[DEBUG] Job is active, resuming polling`);
                        pollJobStatus(jobId, apiUrl);
                    } else if (serverStatus === 'COMPLETED' && !results) {
                        // Fetch results for completed job
                        console.log(`[DEBUG] Job completed, fetching results`);
                        const resultResponse = await authenticatedFetch(`${apiUrl}/jobs/${jobId}/result`, getTokenRef.current);
                        if (resultResponse.ok) {
                            const resultData = await resultResponse.json();
                            // Merge trace info from job data for observability
                            setResults({
                                ...resultData,
                                job_id: jobData.job_id,
                                trace_id: jobData.trace_id,
                                trace_url: jobData.trace_url
                            });
                        }
                    } else if (serverStatus === 'AWAITING_APPROVAL') {
                        console.log(`[DEBUG] Job awaiting approval`);
                        setShowApprovalModal(true);
                        // Resume polling to get timeout updates
                        pollJobStatus(jobId, apiUrl);
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
            } finally {
                // Always clear validating state after server check completes
                setIsValidating(false);
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

    const handleExport = async (format: 'html' | 'json') => {
        if (!jobId) return;
        const apiUrl = getApiBaseUrl();
        const url = `${apiUrl}/jobs/${jobId}/export/${format}`;
        
        try {
            const response = await authenticatedFetch(url, getToken);
            if (!response.ok) throw new Error('Export failed');
            
            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = `test_suite_${jobId}.${format}`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(downloadUrl);
        } catch (e) {
            console.error("Export error:", e);
            alert("Failed to export file");
        }
    };

    const handleView = async () => {
        if (!jobId) return;
        const apiUrl = getApiBaseUrl();
        const url = `${apiUrl}/jobs/${jobId}/export/html`;
        
        try {
            const response = await authenticatedFetch(url, getToken);
            if (!response.ok) throw new Error('View failed');
            
            const blob = await response.blob();
            const viewUrl = window.URL.createObjectURL(blob);
            window.open(viewUrl, '_blank');
            
            // Note: We can't easily revokeObjectURL here because the new window needs it.
            // Browsers will clean it up when the document is unloaded, but for a new window/tab
            // it persists until that tab is closed.
            // A timeout is a reasonable compromise if we want to be cleaner, but 
            // keeping it alive is safer for the user experience.
        } catch (e) {
            console.error("View error:", e);
            alert("Failed to view file");
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
        // Reset progress tracking
        setCurrentStage(null);
        setCurrentStageLabel(null);
        setProgressPercentage(null);
        // Reset displayed progress
        setDisplayedProgress(0);
        // Reset template state
        setInputMode('select');
        setSelectedTemplate(null);
        setTemplateData(null);
        resetProgressGuards();

        // Explicit localStorage clears (belt and suspenders - useEffects should handle this too)
        localStorage.removeItem('activeJobId');
        localStorage.removeItem('activeJobStatus');
        localStorage.removeItem('jobLogs');
        localStorage.removeItem('jobStartTime');
        localStorage.removeItem('currentStage');
        localStorage.removeItem('currentStageLabel');
        localStorage.removeItem('progressPercentage');
        localStorage.removeItem('displayedProgress');
    };

    const handleApprovalSubmitted = () => {
        // Approval submitted - refetch status and close modal
        setShowApprovalModal(false);
        refetchApprovalStatus();
        setLogs(prev => [...prev, 'Human approval decision submitted. Resuming workflow...']);
        setStatus('PROCESSING');
    };

    const hasAuthoritativeProgress = progressPercentage !== null || currentStage !== null || currentStageLabel !== null;

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

            {/* 3D Background Layer */}
            <Background3D />

            <Layout>
                <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-12">

                    {/* Header / Hero Section */}
                    <div className="flex justify-between items-end border-b border-slate-800/50 pb-8">
                        <div>
                            <h1 className="font-display text-5xl font-bold text-white tracking-tight">
                                Validation <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-400">Intelligence</span>
                            </h1>
                            <p className="mt-4 text-xl text-slate-400 font-light max-w-2xl">
                                Generate GAMP-5 compliant test suites with AI precision.
                            </p>
                        </div>
                        {['COMPLETED', 'FAILED', 'EXPIRED'].includes(status) && (
                            <button
                                onClick={resetDashboard}
                                className="text-sm text-slate-400 hover:text-white transition-colors flex items-center gap-2 px-4 py-2 rounded-full border border-slate-700 hover:border-slate-500 hover:bg-slate-800/50"
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
                    <div className="min-h-[600px]">
                        <AnimatePresence mode="wait">
                            {status === 'AWAITING_APPROVAL' && (
                                <motion.div
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: -20 }}
                                    className="max-w-3xl mx-auto"
                                >
                                    <div className="glass-panel p-8 text-center space-y-6 border-amber-500/30 bg-amber-500/5">
                                        <div className="w-20 h-20 bg-amber-500/20 rounded-full flex items-center justify-center mx-auto animate-pulse">
                                            <svg className="w-10 h-10 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                            </svg>
                                        </div>
                                        <div>
                                            <h3 className="text-3xl font-display font-bold text-amber-400 mb-2">Human Insight Required</h3>
                                            <p className="text-slate-300 text-lg mb-4">
                                                {approvalStatus?.approval_reason || 'AI detected ambiguity in categorization'}
                                            </p>

                                            {approvalStatus?.categorization_result && (
                                                <div className="inline-block text-left mt-4 p-6 bg-slate-900/80 rounded-xl border border-slate-700/50 backdrop-blur-xl">
                                                    <p className="text-xs uppercase tracking-wider text-slate-500 mb-2">AI Recommendation</p>
                                                    <div className="flex items-center gap-4">
                                                        <span className="text-4xl font-display font-bold text-white">
                                                            {approvalStatus.categorization_result.gamp_category}
                                                        </span>
                                                        <div className="h-10 w-px bg-slate-700"></div>
                                                        <div>
                                                            <p className="text-sm text-blue-400 font-medium">Confidence Score</p>
                                                            <p className="text-2xl font-bold text-white">
                                                                {(approvalStatus.categorization_result.confidence_score * 100).toFixed(0)}%
                                                            </p>
                                                        </div>
                                                    </div>
                                                </div>
                                            )}

                                            {approvalStatus?.timeout_remaining_seconds != null && (
                                                <p className="text-sm text-amber-300/80 mt-6 font-mono">
                                                    AUTO-APPROVAL IN: {Math.floor(approvalStatus.timeout_remaining_seconds / 60)}:{String(approvalStatus.timeout_remaining_seconds % 60).padStart(2, '0')}
                                                </p>
                                            )}
                                        </div>
                                        <button
                                            onClick={() => setShowApprovalModal(true)}
                                            className="btn-primary bg-amber-600 hover:bg-amber-700 text-lg px-8 py-4 shadow-amber-500/20"
                                        >
                                            Review Decision
                                        </button>
                                    </div>
                                </motion.div>
                            )}

                            {status === 'IDLE' && (
                                <motion.div
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                    className="space-y-12"
                                >
                                    {/* Input Mode Selection */}
                                    {inputMode !== 'edit' && !selectedFile && (
                                        <div className="flex justify-center gap-6">
                                            <button
                                                onClick={() => setInputMode('select')}
                                                className={`group relative px-8 py-6 rounded-2xl transition-all duration-300 border ${inputMode === 'select'
                                                    ? 'bg-blue-600/10 border-blue-500/50 shadow-[0_0_30px_rgba(59,130,246,0.2)]'
                                                    : 'bg-slate-800/40 border-slate-700 hover:bg-slate-800/60 hover:border-slate-600'
                                                    }`}
                                            >
                                                <div className="flex flex-col items-center gap-3">
                                                    <div className={`p-3 rounded-xl ${inputMode === 'select' ? 'bg-blue-500 text-white' : 'bg-slate-700 text-slate-400 group-hover:text-white'} transition-colors`}>
                                                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
                                                        </svg>
                                                    </div>
                                                    <span className="font-medium text-lg">Use Template</span>
                                                </div>
                                            </button>

                                            <button
                                                onClick={() => setInputMode('upload')}
                                                className={`group relative px-8 py-6 rounded-2xl transition-all duration-300 border ${inputMode === 'upload'
                                                    ? 'bg-blue-600/10 border-blue-500/50 shadow-[0_0_30px_rgba(59,130,246,0.2)]'
                                                    : 'bg-slate-800/40 border-slate-700 hover:bg-slate-800/60 hover:border-slate-600'
                                                    }`}
                                            >
                                                <div className="flex flex-col items-center gap-3">
                                                    <div className={`p-3 rounded-xl ${inputMode === 'upload' ? 'bg-blue-500 text-white' : 'bg-slate-700 text-slate-400 group-hover:text-white'} transition-colors`}>
                                                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                                                        </svg>
                                                    </div>
                                                    <span className="font-medium text-lg">Upload URS File</span>
                                                </div>
                                            </button>
                                        </div>
                                    )}

                                    {/* Template Selector */}
                                    {inputMode === 'select' && !selectedFile && (
                                        <TemplateSelector
                                            onSelect={handleTemplateSelect}
                                            selectedId={selectedTemplate?.id || null}
                                        />
                                    )}

                                    {/* Template Editor */}
                                    {inputMode === 'edit' && selectedTemplate && templateData && (
                                        <TemplateEditor
                                            template={selectedTemplate}
                                            initialData={templateData}
                                            onSubmit={handleTemplateSubmit}
                                            onBack={handleBackToTemplates}
                                        />
                                    )}

                                    {/* File Upload */}
                                    {inputMode === 'upload' && !selectedFile && (
                                        <motion.div
                                            initial={{ opacity: 0, y: 20 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            className="max-w-3xl mx-auto"
                                        >
                                            <button
                                                onClick={() => setInputMode('select')}
                                                className="mb-6 flex items-center gap-2 text-slate-400 hover:text-white transition-colors"
                                            >
                                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                                                </svg>
                                                Back to Templates
                                            </button>
                                            <div className="glass-panel p-1">
                                                <FileUpload onFileSelect={handleFileSelect} isUploading={false} />
                                            </div>
                                        </motion.div>
                                    )}

                                    {/* Selected File Confirmation */}
                                    {selectedFile && (
                                        <motion.div
                                            initial={{ opacity: 0, scale: 0.95 }}
                                            animate={{ opacity: 1, scale: 1 }}
                                            className="max-w-2xl mx-auto"
                                        >
                                            <div className="glass-panel p-10 text-center space-y-8 border-blue-500/20">
                                                <div className="w-20 h-20 bg-blue-500/10 rounded-full flex items-center justify-center mx-auto border border-blue-500/20">
                                                    <svg className="w-10 h-10 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                                    </svg>
                                                </div>
                                                <div>
                                                    <h3 className="text-2xl font-display font-medium text-white mb-2">Ready to Generate</h3>
                                                    <p className="text-slate-400 text-lg">
                                                        Selected file: <span className="text-blue-400 font-mono">{selectedFile.name}</span>
                                                    </p>
                                                    <p className="text-sm text-slate-500 mt-2 font-mono">
                                                        {(selectedFile.size / 1024).toFixed(2)} KB
                                                    </p>
                                                </div>

                                                <div className="flex gap-4 justify-center">
                                                    <button
                                                        onClick={() => setSelectedFile(null)}
                                                        className="px-8 py-3 rounded-lg border border-slate-600 text-slate-300 hover:bg-slate-800 transition-colors"
                                                    >
                                                        Cancel
                                                    </button>
                                                    <button
                                                        onClick={handleGenerate}
                                                        data-generate-trigger
                                                        className="btn-primary flex items-center gap-3 text-lg px-8"
                                                    >
                                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                                        </svg>
                                                        Generate Test Suite
                                                    </button>
                                                </div>
                                            </div>
                                        </motion.div>
                                    )}

                                    {/* Feature Cards */}
                                    {inputMode === 'select' && !selectedFile && (
                                        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8">
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
                                    )}
                                </motion.div>
                            )}

                            {/* Processing State - Split View */}
                            {(status === 'PENDING' || status === 'PROCESSING' || status === 'APPROVED' || status === 'FAILED') && !isValidating && hasAuthoritativeProgress && (
                                <motion.div
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    className="grid grid-cols-1 lg:grid-cols-2 gap-8"
                                >
                                    {/* Left Column: Progress Timeline */}
                                    <div className="space-y-6">
                                        <h2 className="text-2xl font-display font-bold text-white flex items-center gap-3">
                                            <span className="w-2 h-8 bg-blue-500 rounded-full"></span>
                                            Generation Progress
                                        </h2>
                                        <JobProgress
                                            status={status}
                                            logs={logs}
                                            startTime={jobStartTime}
                                            jobId={jobId || undefined}
                                            currentStage={currentStage}
                                            currentStageLabel={currentStageLabel}
                                            progressPercentage={progressPercentage}
                                            initialDisplayProgress={displayedProgress}
                                            onProgressChange={handleProgressChange}
                                        />
                                    </div>

                                    {/* Right Column: Quiz / Waiting Activity */}
                                    <div className="space-y-6">
                                        <div className="flex items-center justify-between">
                                            <h2 className="text-2xl font-display font-bold text-white flex items-center gap-3">
                                                <span className="w-2 h-8 bg-cyan-500 rounded-full"></span>
                                                While You Wait
                                            </h2>
                                            <span className="text-xs font-mono text-cyan-400 border border-cyan-500/30 px-2 py-1 rounded">
                                                INTERACTIVE
                                            </span>
                                        </div>
                                        <div className="glass-panel p-6 border-cyan-500/20 bg-cyan-900/5">
                                            <InteractiveQuiz />
                                        </div>
                                    </div>
                                </motion.div>
                            )}

                            {/* Completed State - Results Dashboard */}
                            {status === 'COMPLETED' && results && (
                                <motion.div
                                    initial={{ opacity: 0, scale: 0.95 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    className="space-y-8"
                                >
                                    <div className="flex items-center justify-between">
                                        <h2 className="text-3xl font-display font-bold text-white flex items-center gap-4">
                                            <div className="p-2 bg-emerald-500/20 rounded-lg">
                                                <svg className="w-8 h-8 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                </svg>
                                            </div>
                                            Validation Results
                                        </h2>
                                    </div>

                                    <ComplianceDashboard results={results} onDownload={handleDownload} onExport={handleExport} onView={handleView} />
                                </motion.div>
                            )}

                            {/* Failed State (if no progress data) */}
                            {status === 'FAILED' && !hasAuthoritativeProgress && (
                                <motion.div
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    className="text-center py-12"
                                >
                                    {/* Check if this is a quota limit error */}
                                    {logs[logs.length - 1]?.toLowerCase().includes('daily job limit') ? (
                                        <div className="relative max-w-2xl mx-auto">
                                            {/* Glassmorphism card with animated border */}
                                            <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900/90 via-slate-800/80 to-slate-900/90 backdrop-blur-xl border border-amber-500/30 shadow-2xl">
                                                {/* Animated glow effect */}
                                                <div className="absolute inset-0 bg-gradient-to-r from-amber-500/0 via-amber-400/20 to-amber-500/0 animate-pulse" />

                                                <div className="relative p-12 text-center">
                                                    {/* Icon with glow */}
                                                    <div className="relative inline-flex items-center justify-center mb-8">
                                                        <div className="absolute inset-0 bg-amber-500/30 blur-2xl rounded-full animate-pulse" />
                                                        <div className="relative w-24 h-24 rounded-full bg-gradient-to-br from-amber-500/20 to-orange-600/20 border-2 border-amber-400/50 flex items-center justify-center backdrop-blur-sm">
                                                            <svg className="w-12 h-12 text-amber-400 drop-shadow-lg" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                                            </svg>
                                                        </div>
                                                    </div>

                                                    {/* Bold typography with gradient */}
                                                    <h3 className="text-4xl font-display font-black mb-4 bg-gradient-to-r from-amber-200 via-amber-300 to-orange-300 bg-clip-text text-transparent">
                                                        Daily Limit Reached
                                                    </h3>

                                                    <div className="space-y-4 mb-8">
                                                        <p className="text-lg text-slate-300 font-medium max-w-lg mx-auto leading-relaxed">
                                                            This is a <span className="text-amber-400 font-bold">thesis demonstration project</span> with limited daily usage to manage API costs.
                                                        </p>
                                                        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-amber-500/10 border border-amber-500/30">
                                                            <svg className="w-4 h-4 text-amber-400" fill="currentColor" viewBox="0 0 20 20">
                                                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                                                            </svg>
                                                            <span className="text-sm text-amber-300 font-semibold">Resets at midnight UTC</span>
                                                        </div>
                                                    </div>

                                                    <button
                                                        onClick={resetDashboard}
                                                        className="relative group px-8 py-3 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 text-white font-bold shadow-lg hover:shadow-amber-500/50 transition-all duration-300 hover:scale-105"
                                                    >
                                                        <span className="relative z-10">Got It</span>
                                                        <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-amber-600 to-orange-600 opacity-0 group-hover:opacity-100 transition-opacity" />
                                                    </button>

                                                    <p className="text-xs text-slate-500 mt-6">
                                                        Thank you for understanding! 🙏
                                                    </p>
                                                </div>
                                            </div>
                                        </div>
                                    ) : (
                                        <>
                                            <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-red-500/10 mb-6 border border-red-500/20">
                                                <svg className="w-10 h-10 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                </svg>
                                            </div>
                                            <h3 className="text-2xl font-display font-bold text-white mb-2">Generation Failed</h3>
                                            <p className="text-slate-400 mb-8 max-w-md mx-auto">An error occurred while processing your request. Please check the logs or try again.</p>
                                            <button onClick={resetDashboard} className="btn-primary">Try Again</button>

                                            <div className="mt-8 max-w-2xl mx-auto text-left">
                                                <div className="bg-slate-900/50 rounded-lg p-6 border border-red-500/20 font-mono text-sm text-red-400 shadow-inner">
                                                    {logs[logs.length - 1]}
                                                </div>
                                            </div>
                                        </>
                                    )}
                                </motion.div>
                            )}
                        </AnimatePresence>
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

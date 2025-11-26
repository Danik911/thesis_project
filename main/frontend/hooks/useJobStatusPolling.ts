import { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '@clerk/nextjs';

/**
 * JobStatusWithApproval interface matching backend API response
 * Endpoint: GET /jobs/{job_id}/approval-status
 */
interface JobStatusWithApproval {
    job_id: string;
    status: string;
    requires_approval: boolean;
    approval_reason: string | null;
    timeout_remaining_seconds: number | null;
    categorization_result: {
        gamp_category: number;
        confidence_score: number;
        has_ambiguity_signals: boolean;
        ambiguity_details: string;
        alternative_categories: number[];
        reasoning: string;
    } | null;
}

interface UseJobStatusPollingResult {
    data: JobStatusWithApproval | null;
    isLoading: boolean;
    error: string | null;
    refetch: () => Promise<void>;
}

/**
 * Custom hook for polling job approval status
 *
 * Polls GET /jobs/{job_id}/approval-status endpoint every 5 seconds
 * to detect AWAITING_APPROVAL status and categorization results
 *
 * NO FALLBACK LOGIC: All errors are exposed explicitly
 *
 * @param jobId - Job ID to poll (null disables polling)
 * @param intervalMs - Polling interval in milliseconds (default: 5000)
 * @returns {UseJobStatusPollingResult} Status data, loading state, errors, and refetch function
 */
export function useJobStatusPolling(
    jobId: string | null,
    intervalMs: number = 5000
): UseJobStatusPollingResult {
    const { getToken } = useAuth();
    const [data, setData] = useState<JobStatusWithApproval | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const intervalRef = useRef<NodeJS.Timeout | null>(null);

    /**
     * Fetch job approval status from backend
     * NO FALLBACK LOGIC: Errors are set explicitly, no default values
     */
    const fetchStatus = useCallback(async () => {
        if (!jobId) {
            setIsLoading(false);
            return;
        }

        try {
            const token = await getToken();
            if (!token) {
                throw new Error('Authentication token not available. Please sign in again.');
            }

            const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8080';
            const response = await fetch(`${apiUrl}/jobs/${jobId}/approval-status`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                // NO FALLBACK LOGIC: Expose HTTP errors explicitly
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errorText}`);
            }

            const statusData: JobStatusWithApproval = await response.json();

            // NO FALLBACK LOGIC: Validate response structure
            if (!statusData.job_id || !statusData.status) {
                throw new Error(`Invalid response structure: missing required fields (job_id or status)`);
            }

            setData(statusData);
            setError(null);
            setIsLoading(false);

        } catch (err: any) {
            // NO FALLBACK LOGIC: Expose errors with full diagnostics
            console.error('Job status polling error:', err);
            setError(err.message || 'Unknown error occurred while fetching job status');
            setIsLoading(false);
        }
    }, [jobId, getToken]);

    /**
     * Manual refetch function for user-triggered updates
     */
    const refetch = useCallback(async () => {
        setIsLoading(true);
        await fetchStatus();
    }, [fetchStatus]);

    /**
     * Setup polling interval with cleanup
     * Stops polling when jobId is null or component unmounts
     */
    useEffect(() => {
        if (!jobId) {
            setIsLoading(false);
            return;
        }

        // Initial fetch
        fetchStatus();

        // Setup polling interval
        intervalRef.current = setInterval(fetchStatus, intervalMs);

        // Cleanup on unmount or jobId change
        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
                intervalRef.current = null;
            }
        };
    }, [jobId, intervalMs, fetchStatus]);

    return { data, isLoading, error, refetch };
}

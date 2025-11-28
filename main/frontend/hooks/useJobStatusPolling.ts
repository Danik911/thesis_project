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

    // Track if a request is in-flight to prevent retry storms during token refresh
    const isRequestInFlight = useRef<boolean>(false);

    /**
     * Fetch job approval status from backend
     * NO FALLBACK LOGIC: Errors are set explicitly, no default values
     *
     * CRITICAL FIX (Issue 9): Handle Clerk JWT token expiration (60s default)
     * - On 401, wait for Clerk's background token refresh with exponential backoff
     * - Retry up to 3 times before reporting error
     * - Use longer delays (2s, 4s, 8s) to give Clerk time to refresh
     */
    const fetchStatus = useCallback(async (retryCount: number = 0) => {
        if (!jobId) {
            setIsLoading(false);
            return;
        }

        // Skip this fetch if a previous request is still in-flight (prevents retry storms)
        // Only check on initial call (retryCount=0), not during retry backoff
        if (retryCount === 0 && isRequestInFlight.current) {
            console.log('[HIL-POLL] Skipping poll - previous request still in flight');
            return;
        }

        // Mark request as in-flight only on initial call
        if (retryCount === 0) {
            isRequestInFlight.current = true;
        }

        const MAX_RETRIES = 5; // Increased from 3 to handle long-running workflows

        try {
            // CRITICAL FIX: Force refresh token on retry attempts to get a NEW token
            // On first attempt (retryCount=0), use cached token for performance
            // On retry attempts, force refresh to ensure we don't reuse expired token
            const shouldForceRefresh = retryCount > 0;
            const token = await getToken(shouldForceRefresh ? { forceRefresh: true } : undefined);
            if (!token) {
                throw new Error('Authentication token not available. Please sign in again.');
            }

            const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8080';
            const response = await fetch(`${apiUrl}/jobs/${jobId}/approval-status`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            // Handle 401 Unauthorized - token may have expired
            // CRITICAL FIX: Force token refresh on next retry
            if (response.status === 401 && retryCount < MAX_RETRIES) {
                const delay = Math.pow(2, retryCount + 1) * 1000; // Exponential backoff: 2s, 4s, 8s, 16s, 32s
                console.warn(`[HIL-POLL] JWT expired (401), forcing token refresh, retry ${retryCount + 1}/${MAX_RETRIES} in ${delay}ms...`);
                await new Promise(resolve => setTimeout(resolve, delay));
                // Retry with incremented counter - next call will force token refresh
                return fetchStatus(retryCount + 1);
            }

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
        } finally {
            // Always reset in-flight flag so next poll cycle can proceed
            isRequestInFlight.current = false;
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

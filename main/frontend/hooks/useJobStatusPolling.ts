import { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '@clerk/nextjs';
import { tokenManager } from '@/lib/tokenManager';

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
    // Progress tracking fields (from backend)
    current_stage: string | null;
    current_stage_label: string | null;
    progress_percentage: number | null;
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
 * CRITICAL FIXES:
 * 1. Uses TokenManager singleton for coordinated token refresh (prevents retry storms)
 * 2. Uses AbortController for proper cleanup on unmount/navigation
 * 3. Ignores AbortError to prevent console spam on navigation
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

    // AbortController ref for cancelling in-flight requests on unmount
    const abortControllerRef = useRef<AbortController | null>(null);

    // Track if a request is in-flight to prevent overlapping requests
    const isRequestInFlight = useRef<boolean>(false);

    /**
     * Fetch job approval status from backend
     * NO FALLBACK LOGIC: Errors are set explicitly, no default values
     *
     * CRITICAL FIX (Issue 9): Handle Clerk JWT token expiration (60s default)
     * - Uses TokenManager for coordinated refresh (prevents retry storms)
     * - Uses AbortController for cleanup on unmount
     * - Retry up to 5 times with exponential backoff
     */
    const fetchStatus = useCallback(async (retryCount: number = 0) => {
        if (!jobId) {
            setIsLoading(false);
            return;
        }

        // Skip if previous request still in flight (only on initial call)
        if (retryCount === 0 && isRequestInFlight.current) {
            console.log('[HIL-POLL] Skipping poll - previous request still in flight');
            return;
        }

        // Cancel any previous request
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
        }

        // Create new AbortController for this request
        abortControllerRef.current = new AbortController();
        const signal = abortControllerRef.current.signal;

        // Mark request as in-flight only on initial call
        if (retryCount === 0) {
            isRequestInFlight.current = true;
        }

        // Ensure TokenManager has the getToken function
        tokenManager.setGetTokenFn(getToken);

        const MAX_RETRIES = 5;

        try {
            // Use TokenManager for coordinated token refresh
            // First attempt uses cached token, retries force refresh
            const shouldForceRefresh = retryCount > 0;
            const token = await tokenManager.getToken(shouldForceRefresh);
            if (!token) {
                throw new Error('Authentication token not available. Please sign in again.');
            }

            const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8080';
            const response = await fetch(`${apiUrl}/jobs/${jobId}/approval-status`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                signal
            });

            // Handle 401 Unauthorized - token may have expired
            // TokenManager coordinates refresh to prevent parallel attempts
            if (response.status === 401 && retryCount < MAX_RETRIES) {
                const delay = Math.pow(2, retryCount + 1) * 1000; // 2s, 4s, 8s, 16s, 32s
                console.warn(`[HIL-POLL] JWT expired (401), coordinated refresh, retry ${retryCount + 1}/${MAX_RETRIES} in ${delay}ms...`);
                await new Promise(resolve => setTimeout(resolve, delay));
                // Retry with incremented counter - TokenManager will coordinate the refresh
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
            // Ignore AbortError - happens on unmount/navigation, not a real error
            if (err.name === 'AbortError') {
                console.log('[HIL-POLL] Request aborted (navigation/unmount)');
                return;
            }

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
            // Cancel any in-flight request
            if (abortControllerRef.current) {
                abortControllerRef.current.abort();
            }
            // Clear interval
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
                intervalRef.current = null;
            }
        };
    }, [jobId, intervalMs, fetchStatus]);

    return { data, isLoading, error, refetch };
}

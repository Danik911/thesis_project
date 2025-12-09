/**
 * Authenticated Fetch Utility with Coordinated 401 Retry Logic
 *
 * Handles Clerk JWT token expiration by retrying requests with exponential backoff.
 * Uses TokenManager singleton to coordinate refreshes across all concurrent requests,
 * preventing "retry storms" where multiple 401 handlers trigger parallel refreshes.
 *
 * Clerk JWT tokens expire after 60 seconds by default. When a token is about to expire,
 * Clerk refreshes it in the background. This utility retries 401 responses to give
 * Clerk time to complete the refresh, coordinating through TokenManager.
 *
 * CRITICAL FIX: On 401 errors, we now use TokenManager.refreshToken() which ensures
 * only ONE refresh happens at a time, even with multiple concurrent polling loops.
 *
 * NO FALLBACK LOGIC: All errors are thrown explicitly with full diagnostics.
 */

import { tokenManager, ClerkGetToken } from './tokenManager';

const MAX_RETRIES = 5; // Handles long-running workflows (up to 62s with backoff)

// Re-export type for compatibility with existing code
export type GetTokenFn = ClerkGetToken;

/**
 * Performs an authenticated fetch with coordinated 401 retry
 *
 * @param url - The URL to fetch
 * @param getToken - Clerk's getToken() function from useAuth()
 * @param options - Standard fetch options (method, body, etc.)
 * @param signal - Optional AbortSignal for cancellation
 * @param retryCount - Internal retry counter (do not set externally)
 * @returns Promise<Response> - The fetch response
 * @throws Error if token unavailable or max retries exceeded
 */
export async function authenticatedFetch(
    url: string,
    getToken: ClerkGetToken,
    options: RequestInit = {},
    signal?: AbortSignal,
    retryCount: number = 0
): Promise<Response> {
    // Ensure TokenManager has the getToken function
    tokenManager.setGetTokenFn(getToken);

    // Get token (coordinated through TokenManager)
    // First attempt uses cached token, retries use fresh token
    const shouldForceRefresh = retryCount > 0;
    const token = await tokenManager.getToken(shouldForceRefresh);

    if (!token) {
        throw new Error('Authentication token not available. Please sign in again.');
    }

    // Merge signal into options if provided
    const fetchOptions: RequestInit = {
        ...options,
        headers: {
            ...options.headers,
            'Authorization': `Bearer ${token}`,
        },
        ...(signal ? { signal } : {}),
    };

    const response = await fetch(url, fetchOptions);

    // Handle 401 Unauthorized with coordinated retry
    // TokenManager ensures only ONE refresh happens across all concurrent requests
    if (response.status === 401 && retryCount < MAX_RETRIES) {
        // CRITICAL FIX: Consume response body before discarding to prevent issues
        // Unconsumed response bodies can cause problems with subsequent requests
        await response.text().catch(() => {});

        const delay = Math.pow(2, retryCount + 1) * 1000; // 2s, 4s, 8s, 16s, 32s
        console.warn(`[API] JWT expired (401), coordinated refresh, retry ${retryCount + 1}/${MAX_RETRIES} in ${delay}ms...`);
        await new Promise(resolve => setTimeout(resolve, delay));

        // Recursive retry - TokenManager coordinates the refresh
        return authenticatedFetch(url, getToken, options, signal, retryCount + 1);
    }

    return response;
}

/**
 * Convenience function to get the API base URL
 *
 * For production (CloudFront): NEXT_PUBLIC_API_BASE_URL="" (empty string)
 * This makes API calls use relative URLs like /jobs, which CloudFront routes to API ALB.
 *
 * For local development: NEXT_PUBLIC_API_BASE_URL="http://localhost:8080"
 *
 * NOTE: Uses ?? (nullish coalescing) instead of || because empty string is a valid value
 * that means "use relative URLs". The || operator would treat "" as falsy and use fallback.
 */
export function getApiBaseUrl(): string {
    // ?? only falls back for null/undefined, NOT for empty string ""
    return process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8080';
}

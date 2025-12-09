/**
 * TokenManager Singleton
 *
 * Coordinates JWT token refresh across all concurrent requests to prevent
 * "retry storms" where multiple 401 handlers independently trigger token refreshes.
 *
 * Problem:
 * - Clerk JWT tokens expire after 60 seconds
 * - Multiple polling mechanisms (pollJobStatus 2s, useJobStatusPolling 5s) run concurrently
 * - Each has its own 5-retry exponential backoff
 * - Without coordination, a token expiration triggers 10+ parallel refresh attempts
 *
 * Solution:
 * - Single refreshPromise ensures only ONE refresh operation at a time
 * - Concurrent 401 handlers WAIT for the existing refresh instead of starting new ones
 * - After refresh completes, all waiting callers receive the same fresh token
 *
 * NO FALLBACK LOGIC: All errors are thrown explicitly with full diagnostics.
 */

// Type matches Clerk's useAuth().getToken signature
// Clerk uses { skipCache?: boolean } or similar options
type ClerkGetToken = (options?: { skipCache?: boolean }) => Promise<string | null>;

class TokenManager {
    private static instance: TokenManager;

    // The active refresh promise - shared across all concurrent callers
    private refreshPromise: Promise<string | null> | null = null;

    // The getToken function from Clerk, set by the first component that uses it
    private getTokenFn: ClerkGetToken | null = null;

    // Last successful token (cached for performance on non-refresh calls)
    private cachedToken: string | null = null;
    private tokenExpiresAt: number = 0;

    private constructor() {
        // Private constructor enforces singleton
    }

    /**
     * Get the singleton instance
     */
    public static getInstance(): TokenManager {
        if (!TokenManager.instance) {
            TokenManager.instance = new TokenManager();
        }
        return TokenManager.instance;
    }

    /**
     * Set the getToken function from Clerk
     * Must be called once when the app initializes (e.g., in _app.tsx or a provider)
     *
     * @param fn - Clerk's getToken function from useAuth()
     */
    public setGetTokenFn(fn: ClerkGetToken): void {
        this.getTokenFn = fn;
    }

    /**
     * Get a token, either from cache or by refreshing
     *
     * @param forceRefresh - If true, forces a new token even if cached
     * @returns Promise<string | null> - The JWT token
     * @throws Error if getTokenFn not set or token unavailable
     */
    public async getToken(forceRefresh: boolean = false): Promise<string | null> {
        if (!this.getTokenFn) {
            throw new Error('[TokenManager] getTokenFn not set. Call setGetTokenFn() first.');
        }

        // If not forcing refresh and we have a valid cached token, return it
        if (!forceRefresh && this.cachedToken && Date.now() < this.tokenExpiresAt) {
            return this.cachedToken;
        }

        // If a refresh is already in progress, wait for it
        if (this.refreshPromise) {
            console.log('[TokenManager] Waiting for existing token refresh...');
            return this.refreshPromise;
        }

        // Start a new refresh
        console.log('[TokenManager] Starting token refresh...');
        this.refreshPromise = this._doRefresh();

        try {
            const token = await this.refreshPromise;
            return token;
        } finally {
            // Clear the promise so next refresh can start
            this.refreshPromise = null;
        }
    }

    /**
     * Force a coordinated token refresh
     * All concurrent callers will wait for the same refresh operation
     *
     * @returns Promise<string | null> - The fresh JWT token
     */
    public async refreshToken(): Promise<string | null> {
        return this.getToken(true);
    }

    /**
     * Internal refresh implementation
     * Called only once even if multiple callers request a refresh simultaneously
     */
    private async _doRefresh(): Promise<string | null> {
        if (!this.getTokenFn) {
            throw new Error('[TokenManager] getTokenFn not set. Call setGetTokenFn() first.');
        }

        try {
            // Request a fresh token from Clerk
            // Note: Clerk's getToken with { skipCache: true } forces a fresh token
            const token = await this.getTokenFn({ skipCache: true });

            if (token) {
                // Cache the token with a conservative 50-second expiry
                // (Clerk tokens last 60s, we refresh 10s early)
                this.cachedToken = token;
                this.tokenExpiresAt = Date.now() + 50 * 1000;
                console.log('[TokenManager] Token refreshed successfully');
            } else {
                console.warn('[TokenManager] Token refresh returned null');
                this.cachedToken = null;
                this.tokenExpiresAt = 0;
            }

            return token;
        } catch (error) {
            console.error('[TokenManager] Token refresh failed:', error);
            this.cachedToken = null;
            this.tokenExpiresAt = 0;
            throw error;
        }
    }

    /**
     * Clear cached token (call on sign-out)
     */
    public clearCache(): void {
        this.cachedToken = null;
        this.tokenExpiresAt = 0;
        this.refreshPromise = null;
    }
}

// Export singleton instance
export const tokenManager = TokenManager.getInstance();

// Export type for external use
export type { ClerkGetToken };

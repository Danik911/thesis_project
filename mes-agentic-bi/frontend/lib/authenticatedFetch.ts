import { getApiBaseUrl } from '@/lib/apiBase';

/**
 * Fetch wrapper that attaches JWT Authorization header when a token is available.
 * Falls back to a plain fetch when auth is disabled.
 */
export async function authenticatedFetch(
  path: string,
  getAccessToken: () => Promise<string | null>,
  options: RequestInit = {}
): Promise<Response> {
  const token = await getAccessToken();
  const headers: Record<string, string> = {
    ...((options.headers as Record<string, string>) || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  return fetch(`${getApiBaseUrl()}${path}`, {
    ...options,
    headers,
  });
}

/**
 * LangFuse Metrics API Route
 *
 * Fetches aggregated observability metrics from LangFuse Public API.
 * Protected by Clerk authentication for GAMP-5 compliance.
 *
 * CRITICAL: Uses HTTP Basic Auth (NOT Bearer token) for LangFuse API.
 * CRITICAL: NO FALLBACK LOGIC - All errors return explicit error responses.
 */

import type { NextApiRequest, NextApiResponse } from 'next';
import { getAuth } from '@clerk/nextjs/server';

interface LangFuseMetric {
  date: string;
  countTraces: number;
  totalCost: number;
  usage: Array<{
    model: string;
    inputUsage: number;
    outputUsage: number;
    totalUsage: number;
  }>;
}

interface LangFuseAPIResponse {
  data: LangFuseMetric[];
  meta: {
    page: number;
    limit: number;
    totalItems: number;
    totalPages: number;
  };
}

interface APISuccessResponse {
  success: true;
  data: LangFuseMetric[];
  metadata: {
    fetchedAt: string;
    cacheAgeSeconds?: number;  // Exposes cache freshness for diagnostics
    itemCount: number;
  };
}

interface APIErrorResponse {
  success: false;
  error: string;
  details?: string;
}

type APIResponse = APISuccessResponse | APIErrorResponse;

// Cache for metrics (5-minute TTL to respect LangFuse rate limits)
let metricsCache: { data: LangFuseMetric[]; timestamp: number } | null = null;
const CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes

/**
 * GET /api/langfuse/summary
 *
 * Returns aggregated metrics from LangFuse for the authenticated user.
 * Implements 5-minute caching to respect LangFuse rate limits (~100 req/min).
 *
 * Authentication: Requires Clerk session (JWT token)
 * Caching: 5-minute server-side cache
 * Rate Limits: Respects LangFuse Cloud rate limits
 */
export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<APIResponse>
) {
  // Only allow GET requests
  if (req.method !== 'GET') {
    return res.status(405).json({
      success: false,
      error: 'Method not allowed',
      details: `Expected GET, received ${req.method}`,
    });
  }

  // Authenticate with Clerk
  const { userId } = getAuth(req);
  if (!userId) {
    return res.status(401).json({
      success: false,
      error: 'Unauthorized',
      details: 'Clerk authentication required. Please sign in.',
    });
  }

  // Check cache first (respect rate limits)
  const now = Date.now();
  if (metricsCache && (now - metricsCache.timestamp) < CACHE_TTL_MS) {
    const cacheAge = Math.round((now - metricsCache.timestamp) / 1000);
    console.log(`[LangFuse API] Cache hit (age: ${cacheAge}s, user: ${userId})`);
    return res.status(200).json({
      success: true,
      data: metricsCache.data,
      metadata: {
        fetchedAt: new Date(metricsCache.timestamp).toISOString(),
        cacheAgeSeconds: cacheAge,  // Exposes cache freshness for diagnostics
        itemCount: metricsCache.data.length,
      },
    });
  }

  // Fetch from LangFuse Public API
  try {
    const publicKey = process.env.LANGFUSE_PUBLIC_KEY;
    const secretKey = process.env.LANGFUSE_SECRET_KEY;
    const host = process.env.LANGFUSE_HOST || 'https://cloud.langfuse.com';

    // Validate credentials are configured
    if (!publicKey || !secretKey) {
      const errorMsg = 'LangFuse credentials not configured in environment';
      console.error(`[LangFuse API] ${errorMsg}`);
      return res.status(500).json({
        success: false,
        error: 'Configuration error',
        details: errorMsg + '. Add LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY to .env.local',
      });
    }

    // CRITICAL: Use HTTP Basic Auth (NOT Bearer token)
    // Common mistake: Authorization: Bearer {secretKey} - THIS WILL NOT WORK
    // Correct format: Authorization: Basic base64(publicKey:secretKey)
    const authString = Buffer.from(`${publicKey}:${secretKey}`).toString('base64');
    const authHeader = `Basic ${authString}`;

    // Fetch last 7 days of metrics from LangFuse daily endpoint
    const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString();
    const apiUrl = `${host}/api/public/metrics/daily?fromTimestamp=${sevenDaysAgo}&limit=100`;

    console.log(`[LangFuse API] Fetching metrics from ${host} (user: ${userId})`);
    const response = await fetch(apiUrl, {
      method: 'GET',
      headers: {
        'Authorization': authHeader,
        'Content-Type': 'application/json',
      },
    });

    // Handle API errors explicitly (NO FALLBACK)
    if (!response.ok) {
      const errorText = await response.text();
      const errorMsg = `LangFuse API returned ${response.status}: ${errorText}`;
      console.error(`[LangFuse API] ${errorMsg} (user: ${userId})`);

      // Return appropriate error status
      return res.status(response.status).json({
        success: false,
        error: 'LangFuse API error',
        details: errorMsg,
      });
    }

    // Parse response
    const langfuseData: LangFuseAPIResponse = await response.json();

    // Update cache
    metricsCache = {
      data: langfuseData.data,
      timestamp: now,
    };

    console.log(
      `[LangFuse API] Successfully fetched ${langfuseData.data.length} metrics ` +
      `(user: ${userId}, cached for ${CACHE_TTL_MS / 1000}s)`
    );

    return res.status(200).json({
      success: true,
      data: langfuseData.data,
      metadata: {
        fetchedAt: new Date(now).toISOString(),
        itemCount: langfuseData.data.length,
      },
    });

  } catch (error) {
    // CRITICAL: NO FALLBACK - Explicit error propagation
    const errorMsg = error instanceof Error ? error.message : 'Unknown error';
    console.error('[LangFuse API] Fetch failed:', errorMsg, error);

    return res.status(500).json({
      success: false,
      error: 'Failed to fetch metrics from LangFuse',
      details: errorMsg,
    });
  }
}

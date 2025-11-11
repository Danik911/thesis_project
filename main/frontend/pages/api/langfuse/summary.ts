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

interface LangFuseMetricsRow {
  time_dimension?: string;
  count_count?: string | null;
  sum_totalCost?: string | null;
}

interface LangFuseUsageRow {
  time_dimension?: string;
  providedModelName?: string | null;
  sum_inputTokens?: string | null;
  sum_outputTokens?: string | null;
  sum_totalTokens?: string | null;
}

interface LangFuseMetricsResponse<T> {
  data: T[];
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

// Cache for metrics (30-minute TTL to respect LangFuse rate limits)
let metricsCache: { data: LangFuseMetric[]; timestamp: number } | null = null;
const CACHE_TTL_MS = 30 * 60 * 1000; // 30 minutes

/**
 * GET /api/langfuse/summary
 *
 * Returns aggregated metrics from LangFuse for the authenticated user.
 * Implements 30-minute caching to respect LangFuse rate limits (~100 req/min).
 *
 * Authentication: Requires Clerk session (JWT token)
 * Caching: 30-minute server-side cache
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
    const host = process.env.LANGFUSE_HOST || process.env.LANGFUSE_BASE_URL || 'https://cloud.langfuse.com';

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

    const toNumber = (value: string | null | undefined): number => {
      if (value === null || value === undefined) {
        return 0;
      }
      const normalized = typeof value === 'string' ? value.trim() : String(value);
      if (!normalized) {
        return 0;
      }
      const parsed = Number(normalized);
      return Number.isFinite(parsed) ? parsed : 0;
    };

    // Prepare queries for the last 7 days worth of data
    const nowIso = new Date().toISOString();
    const sevenDaysAgoIso = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString();

    const dailyMetricsQuery = {
      view: 'traces',
      metrics: [
        { measure: 'count', aggregation: 'count' },
        { measure: 'totalCost', aggregation: 'sum' },
      ],
      timeDimension: { granularity: 'day' },
      fromTimestamp: sevenDaysAgoIso,
      toTimestamp: nowIso,
      config: { row_limit: 100 },
    };

    const usageMetricsQuery = {
      view: 'observations',
      dimensions: [{ field: 'providedModelName' }],
      metrics: [
        { measure: 'inputTokens', aggregation: 'sum' },
        { measure: 'outputTokens', aggregation: 'sum' },
        { measure: 'totalTokens', aggregation: 'sum' },
      ],
      timeDimension: { granularity: 'day' },
      fromTimestamp: sevenDaysAgoIso,
      toTimestamp: nowIso,
      config: { row_limit: 500 },
    };

    const buildMetricsUrl = (query: Record<string, unknown>) =>
      `${host}/api/public/metrics?query=${encodeURIComponent(JSON.stringify(query))}`;

    console.log(`[LangFuse API] Fetching metrics from ${host} (user: ${userId})`);
    const [dailyResponse, usageResponse] = await Promise.all([
      fetch(buildMetricsUrl(dailyMetricsQuery), {
        method: 'GET',
        headers: {
          Authorization: authHeader,
          'Content-Type': 'application/json',
        },
      }),
      fetch(buildMetricsUrl(usageMetricsQuery), {
        method: 'GET',
        headers: {
          Authorization: authHeader,
          'Content-Type': 'application/json',
        },
      }),
    ]);

    if (!dailyResponse.ok) {
      const errorText = await dailyResponse.text();
      const errorMsg = `LangFuse metrics query failed with ${dailyResponse.status}: ${errorText}`;
      console.error(`[LangFuse API] ${errorMsg} (user: ${userId})`);
      return res.status(dailyResponse.status).json({
        success: false,
        error: 'LangFuse API error',
        details: errorMsg,
      });
    }

    const dailyData: LangFuseMetricsResponse<LangFuseMetricsRow> = await dailyResponse.json();

    let usageData: LangFuseMetricsResponse<LangFuseUsageRow> | null = null;
    if (usageResponse.ok) {
      usageData = await usageResponse.json();
    } else {
      const warnText = await usageResponse.text();
      console.warn(
        `[LangFuse API] Usage metrics query failed with ${usageResponse.status}: ${warnText} (user: ${userId})`
      );
    }

    // Aggregate usage data by day and model
    const usageByDate = new Map<string, Map<string, { input: number; output: number; total: number }>>();
    usageData?.data.forEach(row => {
      const dateKeyRaw = row.time_dimension?.split('T')[0] ?? '';
      const dateKey = dateKeyRaw || new Date().toISOString().split('T')[0];
      const modelName = (row.providedModelName || 'Unspecified model').trim() || 'Unspecified model';

      const perDate = usageByDate.get(dateKey) ?? new Map();
      const existing = perDate.get(modelName) ?? { input: 0, output: 0, total: 0 };

      existing.input += toNumber(row.sum_inputTokens);
      existing.output += toNumber(row.sum_outputTokens);
      existing.total += toNumber(row.sum_totalTokens);

      perDate.set(modelName, existing);
      usageByDate.set(dateKey, perDate);
    });

    const metrics: LangFuseMetric[] = dailyData.data.map(row => {
      const dateKeyRaw = row.time_dimension?.split('T')[0] ?? '';
      const date = dateKeyRaw || new Date().toISOString().split('T')[0];
      const usageForDay = usageByDate.get(date);

      return {
        date,
        countTraces: Math.round(toNumber(row.count_count)),
        totalCost: Number.parseFloat(toNumber(row.sum_totalCost).toFixed(4)),
        usage: usageForDay
          ? Array.from(usageForDay.entries()).map(([model, usage]) => ({
          model,
          inputUsage: usage.input,
          outputUsage: usage.output,
          totalUsage: usage.total,
            }))
          : [],
      };
    });

    // Ensure metrics are sorted by date ascending for deterministic rendering
    metrics.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

    // Update cache
    metricsCache = {
      data: metrics,
      timestamp: now,
    };

    console.log(
      `[LangFuse API] Successfully fetched ${metrics.length} metrics ` +
      `(user: ${userId}, cached for ${CACHE_TTL_MS / 1000}s)`
    );

    return res.status(200).json({
      success: true,
      data: metrics,
      metadata: {
        fetchedAt: new Date(now).toISOString(),
        itemCount: metrics.length,
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

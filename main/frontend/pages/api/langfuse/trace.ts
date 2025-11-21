import type { NextApiRequest, NextApiResponse } from 'next';
import { getAuth } from '@clerk/nextjs/server';

interface LangfuseTracePayload {
  id: string;
  name?: string | null;
  timestamp?: string;
  userId?: string | null;
  environment?: string | null;
  tags?: string[] | null;
  totalCost?: number | null;
  latency?: number | null;
  htmlPath?: string;
  public?: boolean;
  observations?: Array<Record<string, unknown>>;
  scores?: Array<Record<string, unknown>>;
  [key: string]: unknown;
}

interface SuccessResponse {
  success: true;
  data: LangfuseTracePayload;
  metadata: {
    fetchedAt: string;
    traceId: string;
    cacheHit: boolean;
  };
}

interface ErrorResponse {
  success: false;
  error: string;
  details?: string;
}

type ApiResponse = SuccessResponse | ErrorResponse;

type CacheEntry = {
  payload: LangfuseTracePayload;
  timestamp: number;
};

const TRACE_CACHE_TTL_MS = 2 * 60 * 1000; // 2 minutes to prevent hammering Langfuse API
const traceCache = new Map<string, CacheEntry>();

const normalizeHost = (host: string): string => host.replace(/\/$/, '');

export default async function handler(req: NextApiRequest, res: NextApiResponse<ApiResponse>) {
  if (req.method !== 'GET') {
    return res.status(405).json({
      success: false,
      error: 'Method not allowed',
      details: `Expected GET, received ${req.method}`,
    });
  }

  const { userId } = getAuth(req);
  if (!userId) {
    return res.status(401).json({
      success: false,
      error: 'Unauthorized',
      details: 'Clerk authentication required. Please sign in.',
    });
  }

  const traceIdParam = req.query.traceId;
  const traceId = Array.isArray(traceIdParam) ? traceIdParam[0] : traceIdParam;

  if (!traceId || typeof traceId !== 'string') {
    return res.status(400).json({
      success: false,
      error: 'Missing traceId',
      details: 'Provide a Langfuse traceId query parameter',
    });
  }

  const now = Date.now();
  const cached = traceCache.get(traceId);
  if (cached && now - cached.timestamp < TRACE_CACHE_TTL_MS) {
    return res.status(200).json({
      success: true,
      data: cached.payload,
      metadata: {
        fetchedAt: new Date(cached.timestamp).toISOString(),
        traceId,
        cacheHit: true,
      },
    });
  }

  try {
    const publicKey = process.env.LANGFUSE_PUBLIC_KEY;
    const secretKey = process.env.LANGFUSE_SECRET_KEY;
    const host = process.env.LANGFUSE_HOST || process.env.LANGFUSE_BASE_URL || 'https://cloud.langfuse.com';

    if (!publicKey || !secretKey) {
      return res.status(500).json({
        success: false,
        error: 'Configuration error',
        details: 'LANGFUSE_PUBLIC_KEY or LANGFUSE_SECRET_KEY is missing from environment',
      });
    }

    const authHeader = `Basic ${Buffer.from(`${publicKey}:${secretKey}`).toString('base64')}`;
    const normalizedHost = normalizeHost(host);
    const fields = encodeURIComponent('core,io,observations,scores,metrics');
    const url = `${normalizedHost}/api/public/traces/${encodeURIComponent(traceId)}?fields=${fields}`;

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        Authorization: authHeader,
        Accept: 'application/json',
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      return res.status(response.status).json({
        success: false,
        error: 'Langfuse API error',
        details: `Trace fetch failed with ${response.status}: ${errorText}`,
      });
    }

    const payload = (await response.json()) as LangfuseTracePayload;
    traceCache.set(traceId, { payload, timestamp: now });

    return res.status(200).json({
      success: true,
      data: payload,
      metadata: {
        fetchedAt: new Date(now).toISOString(),
        traceId,
        cacheHit: false,
      },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return res.status(500).json({
      success: false,
      error: 'Trace fetch failed',
      details: message,
    });
  }
}

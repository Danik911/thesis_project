import type { NextApiRequest, NextApiResponse } from 'next';
import fs from 'node:fs';
import path from 'node:path';

type TracePayload = Record<string, unknown>;

type ApiResponse =
  | {
      success: true;
      data: TracePayload;
      metadata: { fetchedAt: string; traceId: string; cacheHit: boolean };
    }
  | {
      success: false;
      error: string;
      details?: string;
    };

type CacheEntry = { payload: TracePayload; timestamp: number };

const TRACE_CACHE_TTL_MS = 2 * 60 * 1000;
const traceCache = new Map<string, CacheEntry>();
let fallbackEnv: Record<string, string> | null = null;

const parseEnvFile = (filePath: string): Record<string, string> => {
  if (!fs.existsSync(filePath)) return {};
  const content = fs.readFileSync(filePath, 'utf8');
  const out: Record<string, string> = {};
  for (const rawLine of content.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith('#')) continue;
    const idx = line.indexOf('=');
    if (idx <= 0) continue;
    const key = line.slice(0, idx).trim();
    let value = line.slice(idx + 1).trim();
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }
    out[key] = value;
  }
  return out;
};

const loadFallbackEnv = (): Record<string, string> => {
  if (fallbackEnv) return fallbackEnv;
  const cwd = process.cwd();
  fallbackEnv = {
    ...parseEnvFile(path.resolve(cwd, '.env.local')),
    ...parseEnvFile(path.resolve(cwd, '../.env.local')),
  };
  return fallbackEnv;
};

const envValue = (key: string): string | undefined => process.env[key] || loadFallbackEnv()[key];

const normalizeHost = (host: string): string => host.replace(/\/$/, '');

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<ApiResponse>
) {
  if (req.method !== 'GET') {
    return res.status(405).json({
      success: false,
      error: 'Method not allowed',
      details: `Expected GET, received ${req.method}`,
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

  const publicKey = envValue('LANGFUSE_PUBLIC_KEY');
  const secretKey = envValue('LANGFUSE_SECRET_KEY');
  const host = envValue('LANGFUSE_HOST') || envValue('LANGFUSE_BASE_URL') || 'https://cloud.langfuse.com';

  if (!publicKey || !secretKey) {
    return res.status(500).json({
      success: false,
      error: 'Configuration error',
      details: 'LANGFUSE_PUBLIC_KEY or LANGFUSE_SECRET_KEY is missing from environment',
    });
  }

  try {
    const authHeader = `Basic ${Buffer.from(`${publicKey}:${secretKey}`).toString('base64')}`;
    const fields = encodeURIComponent('core,io,observations,scores,metrics');
    const normalizedHost = normalizeHost(host);
    const url = `${normalizedHost}/api/public/traces/${encodeURIComponent(traceId)}?fields=${fields}`;

    const response = await fetch(url, {
      method: 'GET',
      headers: { Authorization: authHeader, Accept: 'application/json' },
    });

    if (!response.ok) {
      const errorText = await response.text();
      return res.status(response.status).json({
        success: false,
        error: 'Langfuse API error',
        details: `Trace fetch failed with ${response.status}: ${errorText}`,
      });
    }

    const payload = (await response.json()) as TracePayload;
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
    return res.status(500).json({
      success: false,
      error: 'Trace fetch failed',
      details: error instanceof Error ? error.message : 'Unknown error',
    });
  }
}

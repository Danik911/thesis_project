import type { NextApiRequest, NextApiResponse } from 'next';
import fs from 'node:fs';
import path from 'node:path';

interface LangfuseMetric {
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

type ApiResponse =
  | {
      success: true;
      data: LangfuseMetric[];
      metadata: { fetchedAt: string; itemCount: number; cacheAgeSeconds?: number };
    }
  | {
      success: false;
      error: string;
      details?: string;
    };

let metricsCache: { data: LangfuseMetric[]; timestamp: number } | null = null;
const CACHE_TTL_MS = 30 * 60 * 1000;
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

const toNumber = (value: string | number | null | undefined): number => {
  if (value === null || value === undefined) return 0;
  const n = Number(typeof value === 'string' ? value.trim() : value);
  return Number.isFinite(n) ? n : 0;
};

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

  const now = Date.now();
  if (metricsCache && now - metricsCache.timestamp < CACHE_TTL_MS) {
    const cacheAgeSeconds = Math.round((now - metricsCache.timestamp) / 1000);
    return res.status(200).json({
      success: true,
      data: metricsCache.data,
      metadata: {
        fetchedAt: new Date(metricsCache.timestamp).toISOString(),
        itemCount: metricsCache.data.length,
        cacheAgeSeconds,
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
    const normalizedHost = normalizeHost(host);

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
      `${normalizedHost}/api/public/metrics?query=${encodeURIComponent(JSON.stringify(query))}`;

    const [dailyResponse, usageResponse] = await Promise.all([
      fetch(buildMetricsUrl(dailyMetricsQuery), {
        method: 'GET',
        headers: { Authorization: authHeader, 'Content-Type': 'application/json' },
      }),
      fetch(buildMetricsUrl(usageMetricsQuery), {
        method: 'GET',
        headers: { Authorization: authHeader, 'Content-Type': 'application/json' },
      }),
    ]);

    if (!dailyResponse.ok) {
      const errorText = await dailyResponse.text();
      return res.status(dailyResponse.status).json({
        success: false,
        error: 'Langfuse API error',
        details: `Metrics fetch failed with ${dailyResponse.status}: ${errorText}`,
      });
    }

    const dailyData = (await dailyResponse.json()) as {
      data: Array<{ time_dimension?: string; count_count?: string | null; sum_totalCost?: string | null }>;
    };

    const usageData = usageResponse.ok
      ? ((await usageResponse.json()) as {
          data: Array<{
            time_dimension?: string;
            providedModelName?: string | null;
            sum_inputTokens?: string | null;
            sum_outputTokens?: string | null;
            sum_totalTokens?: string | null;
          }>;
        })
      : { data: [] as Array<{ time_dimension?: string; providedModelName?: string | null; sum_inputTokens?: string | null; sum_outputTokens?: string | null; sum_totalTokens?: string | null }> };

    const usageByDate = new Map<string, Map<string, { input: number; output: number; total: number }>>();
    for (const row of usageData.data) {
      const date = row.time_dimension?.split('T')[0] || new Date().toISOString().split('T')[0];
      const model = (row.providedModelName || 'Unspecified model').trim() || 'Unspecified model';
      const perDate = usageByDate.get(date) ?? new Map<string, { input: number; output: number; total: number }>();
      const existing = perDate.get(model) ?? { input: 0, output: 0, total: 0 };
      existing.input += toNumber(row.sum_inputTokens);
      existing.output += toNumber(row.sum_outputTokens);
      existing.total += toNumber(row.sum_totalTokens);
      perDate.set(model, existing);
      usageByDate.set(date, perDate);
    }

    const metrics: LangfuseMetric[] = dailyData.data.map((row) => {
      const date = row.time_dimension?.split('T')[0] || new Date().toISOString().split('T')[0];
      const usage = usageByDate.get(date);
      return {
        date,
        countTraces: Math.round(toNumber(row.count_count)),
        totalCost: Number.parseFloat(toNumber(row.sum_totalCost).toFixed(4)),
        usage: usage
          ? Array.from(usage.entries()).map(([model, values]) => ({
              model,
              inputUsage: values.input,
              outputUsage: values.output,
              totalUsage: values.total,
            }))
          : [],
      };
    });

    metrics.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

    metricsCache = { data: metrics, timestamp: now };

    return res.status(200).json({
      success: true,
      data: metrics,
      metadata: { fetchedAt: new Date(now).toISOString(), itemCount: metrics.length },
    });
  } catch (error) {
    return res.status(500).json({
      success: false,
      error: 'Failed to fetch metrics from Langfuse',
      details: error instanceof Error ? error.message : 'Unknown error',
    });
  }
}

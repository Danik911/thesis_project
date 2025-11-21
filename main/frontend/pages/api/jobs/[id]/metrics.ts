import type { NextApiRequest, NextApiResponse } from 'next';
import { getAuth } from '@clerk/nextjs/server';

interface JobMetrics {
    totalTraces: number;
    totalCost: number;
    totalTokens: number;
    latency: number;
}

export default async function handler(
    req: NextApiRequest,
    res: NextApiResponse
) {
    if (req.method !== 'GET') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    const { userId } = getAuth(req);
    if (!userId) {
        return res.status(401).json({ error: 'Unauthorized' });
    }

    const { id } = req.query;
    if (!id || typeof id !== 'string') {
        return res.status(400).json({ error: 'Invalid job ID' });
    }

    try {
        const publicKey = process.env.LANGFUSE_PUBLIC_KEY;
        const secretKey = process.env.LANGFUSE_SECRET_KEY;
        const host = process.env.LANGFUSE_HOST || 'https://cloud.langfuse.com';

        if (!publicKey || !secretKey) {
            console.error('LangFuse credentials missing');
            return res.status(500).json({ error: 'Configuration error' });
        }

        const authString = Buffer.from(`${publicKey}:${secretKey}`).toString('base64');

        // Query traces with tag job_id:{id}
        // We use the /api/public/traces endpoint to list traces filtered by tag
        const params = new URLSearchParams({
            tags: `job_id:${id}`,
            limit: '100' // Assuming one job doesn't have > 100 root traces
        });

        const response = await fetch(`${host}/api/public/traces?${params}`, {
            headers: {
                'Authorization': `Basic ${authString}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error(`LangFuse API error: ${response.status} ${errorText}`);
            // Return empty metrics if not found or error, to avoid breaking UI
            return res.status(200).json({
                totalTraces: 0,
                totalCost: 0,
                totalTokens: 0,
                latency: 0
            });
        }

        const data = await response.json();
        const traces = data.data || [];

        // Aggregate metrics
        const metrics: JobMetrics = traces.reduce((acc: JobMetrics, trace: any) => {
            return {
                totalTraces: acc.totalTraces + 1,
                totalCost: acc.totalCost + (trace.totalCost || 0),
                totalTokens: acc.totalTokens + (trace.usage?.total || 0),
                latency: acc.latency + (trace.latency || 0)
            };
        }, {
            totalTraces: 0,
            totalCost: 0,
            totalTokens: 0,
            latency: 0
        });

        // Round cost to 4 decimals
        metrics.totalCost = Math.round(metrics.totalCost * 10000) / 10000;

        return res.status(200).json(metrics);

    } catch (error) {
        console.error('Failed to fetch job metrics:', error);
        return res.status(500).json({ error: 'Internal server error' });
    }
}

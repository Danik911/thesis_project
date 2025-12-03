import { useAuth } from '@clerk/nextjs';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import Layout from '../components/Layout';

interface Job {
    job_id: string;
    status: string;
    created_at: string;
    urs_filename: string;
    result_uri?: string;
}

export default function History() {
    const { isLoaded, userId, getToken } = useAuth();
    const router = useRouter();
    const [jobs, setJobs] = useState<Job[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchJobs = async () => {
            if (!isLoaded || !userId) return;

            try {
                const token = await getToken();
                const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8080';
                const response = await fetch(`${apiUrl}/jobs`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (response.ok) {
                    const data = await response.json();
                    setJobs(data);
                }
            } catch (error) {
                console.error('Failed to fetch jobs:', error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchJobs();
    }, [isLoaded, userId, getToken]);

    const handleRowClick = (jobId: string) => {
        router.push(`/jobs/${jobId}`);
    };

    if (!isLoaded || isLoading) {
        return (
            <Layout>
                <div className="flex items-center justify-center min-h-[60vh]">
                    <div className="animate-pulse flex flex-col items-center">
                        <div className="h-12 w-12 bg-blue-600/20 rounded-full mb-4 animate-ping"></div>
                        <div className="text-slate-400">Loading history...</div>
                    </div>
                </div>
            </Layout>
        );
    }

    return (
        <>
            <Head>
                <title>History - PharmaGen AI</title>
            </Head>
            <Layout>
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <h1 className="text-3xl font-bold text-white mb-8">Job History</h1>

                    <div className="bg-slate-800/50 rounded-xl overflow-hidden border border-slate-700">
                        {jobs.length === 0 ? (
                            <div className="p-8 text-center text-slate-400">No history available.</div>
                        ) : (
                            <table className="w-full text-left text-sm text-slate-400">
                                <thead className="bg-slate-900/50 text-slate-200 uppercase font-mono text-xs">
                                    <tr>
                                        <th className="px-6 py-4">Job ID</th>
                                        <th className="px-6 py-4">File</th>
                                        <th className="px-6 py-4">Status</th>
                                        <th className="px-6 py-4">Date</th>
                                        <th className="px-6 py-4">Actions</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-700">
                                    {jobs.map(job => (
                                        <tr
                                            key={job.job_id}
                                            className="hover:bg-slate-700/30 transition-colors"
                                        >
                                            <td className="px-6 py-4 font-mono text-xs text-blue-400">{job.job_id.substring(0, 8)}...</td>
                                            <td className="px-6 py-4">{job.urs_filename}</td>
                                            <td className="px-6 py-4">
                                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                                    job.status.toUpperCase() === 'COMPLETED' ? 'bg-emerald-500/10 text-emerald-400' :
                                                    job.status.toUpperCase() === 'FAILED' ? 'bg-red-500/10 text-red-400' :
                                                    job.status.toUpperCase() === 'EXPIRED' ? 'bg-amber-500/10 text-amber-400' :
                                                    job.status.toUpperCase() === 'AWAITING_APPROVAL' ? 'bg-amber-500/10 text-amber-400' :
                                                    'bg-blue-500/10 text-blue-400'
                                                }`}>
                                                    {job.status.toUpperCase() === 'AWAITING_APPROVAL' && (
                                                        <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                        </svg>
                                                    )}
                                                    {job.status.toUpperCase() === 'AWAITING_APPROVAL' ? 'AWAITING APPROVAL' : job.status.toUpperCase()}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4">{new Date(job.created_at).toLocaleDateString()} {new Date(job.created_at).toLocaleTimeString()}</td>
                                            <td className="px-6 py-4">
                                                <button
                                                    className="text-blue-400 hover:text-blue-300 transition-colors"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        handleRowClick(job.job_id);
                                                    }}
                                                >
                                                    View Details
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                    </div>
                </div>
            </Layout>
        </>
    );
}

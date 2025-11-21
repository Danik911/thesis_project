import Link from 'next/link';
import Head from 'next/head';
import Layout from '../components/Layout';

export default function Custom404() {
    return (
        <Layout>
            <Head>
                <title>Page Not Found - PharmaGen AI</title>
            </Head>
            <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
                <div className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-slate-800 mb-8 animate-bounce">
                    <span className="text-4xl">🔍</span>
                </div>
                <h1 className="text-4xl font-bold text-white mb-4">Page Not Found</h1>
                <p className="text-slate-400 text-lg mb-8 max-w-md">
                    The page you are looking for might have been removed, had its name changed, or is temporarily unavailable.
                </p>
                <Link
                    href="/dashboard"
                    className="btn-primary flex items-center gap-2"
                >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                    </svg>
                    Back to Dashboard
                </Link>
            </div>
        </Layout>
    );
}

import { useUser } from '@clerk/nextjs';
import Layout from '@/components/Layout';
import Head from 'next/head';

export default function Dashboard() {
  const { user, isLoaded } = useUser();

  // Derive display name with fallback chain
  const displayName = user?.fullName ??
    user?.firstName ??
    user?.primaryEmailAddress?.emailAddress ??
    'User';

  if (!isLoaded) {
    return (
      <Layout>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-64 mb-4"></div>
            <p className="text-sm text-gray-500 mb-8">
              Verifying your EU-compliant session...
            </p>
            <div className="card">
              <div className="h-4 bg-gray-200 rounded w-32 mb-4"></div>
              <div className="space-y-2">
                <div className="h-3 bg-gray-200 rounded w-48"></div>
                <div className="h-3 bg-gray-200 rounded w-56"></div>
                <div className="h-3 bg-gray-200 rounded w-64"></div>
              </div>
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <>
      <Head>
        <title>Dashboard - Pharmaceutical Test Generation</title>
        <meta name="description" content="GAMP-5 compliant pharmaceutical test generation dashboard" />
      </Head>
      <Layout>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Welcome Section */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">
              Welcome, {displayName}!
            </h1>
            <p className="mt-2 text-gray-600">
              Manage your pharmaceutical test generation workflows
            </p>
          </div>

          {/* User Profile Card */}
          <div className="card mb-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              User Profile
            </h2>
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-700 w-24">Name:</span>
                <span className="text-sm text-gray-900">
                  {user?.fullName ?? (`${user?.firstName ?? ''} ${user?.lastName ?? ''}`.trim() || 'Not provided')}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-700 w-24">Email:</span>
                <span className="text-sm text-gray-900">
                  {user?.primaryEmailAddress?.emailAddress ?? user?.emailAddresses[0]?.emailAddress ?? 'Not available'}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-700 w-24">User ID:</span>
                <span className="text-sm font-mono text-gray-600 text-xs">
                  {user?.id ?? 'Unknown'}
                </span>
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-gray-200">
              <p className="text-xs text-gray-500">
                ✓ ALCOA+ Attributable - All actions are linked to your user ID
              </p>
            </div>
          </div>

          {/* GAMP-5 Test Suite Generation Card */}
          <div className="card">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              GAMP-5 Test Suite Generation
            </h2>
            <p className="text-gray-600 mb-4">
              Generate compliant test suites for pharmaceutical software validation.
            </p>
            <div className="bg-blue-50 border border-blue-200 rounded p-4">
              <p className="text-sm text-blue-800">
                <span className="font-medium">Coming Soon:</span> Job submission interface will be available in the next phase.
                You&apos;ll be able to submit test generation requests and track their status.
              </p>
            </div>
          </div>

          {/* Compliance Notice */}
          <div className="mt-6 card bg-gray-50">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">
              Compliance Information
            </h3>
            <ul className="text-xs text-gray-600 space-y-1">
              <li>✓ GAMP-5 Category 5 - Configured software validation framework</li>
              <li>✓ ALCOA+ Principles - Attributable, Legible, Contemporaneous, Original, Accurate</li>
              <li>✓ 21 CFR Part 11 - Electronic records and signatures (in development)</li>
              <li>⚠️ EU Data Residency - Verify Clerk key is EU-specific before production</li>
            </ul>
          </div>
        </div>
      </Layout>
    </>
  );
}

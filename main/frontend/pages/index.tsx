import { useAuth } from '@clerk/nextjs'
import { useRouter } from 'next/router'
import { useEffect } from 'react'
import Header from '@/components/Header'
import Head from 'next/head'

export default function Home() {
  const { isSignedIn, isLoaded } = useAuth()
  const router = useRouter()

  // Redirect to dashboard if user is signed in
  useEffect(() => {
    if (isLoaded && isSignedIn) {
      router.push('/dashboard')
    }
  }, [isLoaded, isSignedIn, router])

  // Show loading state while checking auth
  if (!isLoaded) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-pulse text-center">
          <div className="h-8 w-8 bg-blue-600 rounded-full mx-auto mb-4"></div>
          <p className="text-gray-600 font-medium">Loading...</p>
          <p className="text-gray-500 text-sm mt-2">Verifying your session...</p>
        </div>
      </div>
    )
  }

  // Don't render if redirecting to dashboard
  if (isSignedIn) {
    return null
  }

  return (
    <>
      <Head>
        <title>Pharmaceutical Test Generation - GAMP-5 Compliant</title>
        <meta name="description" content="GAMP-5 compliant pharmaceutical test suite generation system" />
      </Head>
      <div className="min-h-screen bg-gray-50">
        <Header />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="card">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              Welcome to Pharmaceutical Test Generation
            </h2>
            <p className="text-gray-600 mb-4">
              Generate GAMP-5 compliant test suites for pharmaceutical software validation.
            </p>
            <p className="text-sm text-gray-500">
              Please sign in to access the test generation system.
            </p>
          </div>
        </main>
      </div>
    </>
  )
}

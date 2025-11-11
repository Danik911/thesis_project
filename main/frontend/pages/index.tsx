import { useAuth } from '@clerk/nextjs'
import Header from '@/components/Header'

export default function Home() {
  const { isSignedIn } = useAuth()

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="card">
          <h2 className="text-2xl font-semibold text-gray-900 mb-4">
            Welcome to Pharmaceutical Test Generation
          </h2>
          <p className="text-gray-600">
            {isSignedIn
              ? 'You are signed in. Start generating GAMP-5 compliant test suites.'
              : 'Please sign in to access the test generation system.'}
          </p>
        </div>
      </main>
    </div>
  )
}

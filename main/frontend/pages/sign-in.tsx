import { SignIn } from '@clerk/nextjs'
import Head from 'next/head'

export default function SignInPage() {
  return (
    <>
      <Head>
        <title>Sign In - Pharmaceutical Test Generation</title>
        <meta name="description" content="Sign in to access GAMP-5 compliant pharmaceutical test generation system" />
      </Head>
      <div className="min-h-screen flex flex-col bg-gray-50">
        <main role="main" className="flex-1 flex items-center justify-center">
          <div className="w-full max-w-md">
            <h1 className="sr-only">Sign In to Pharmaceutical Test Generation</h1>
            <SignIn
              path="/sign-in"
              routing="path"
              signUpUrl="/sign-up"
              afterSignInUrl="/"
            />
          </div>
        </main>
      </div>
    </>
  )
}

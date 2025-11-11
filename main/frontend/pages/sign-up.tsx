import { SignUp } from '@clerk/nextjs'
import Head from 'next/head'

export default function SignUpPage() {
  return (
    <>
      <Head>
        <title>Sign Up - Pharmaceutical Test Generation</title>
        <meta name="description" content="Create an account to access GAMP-5 compliant pharmaceutical test generation system" />
      </Head>
      <div className="min-h-screen flex flex-col bg-gray-50">
        <main role="main" className="flex-1 flex items-center justify-center">
          <div className="w-full max-w-md">
            <h1 className="sr-only">Sign Up for Pharmaceutical Test Generation</h1>
            <SignUp
              path="/sign-up"
              routing="path"
              signInUrl="/sign-in"
              afterSignUpUrl="/"
            />
          </div>
        </main>
      </div>
    </>
  )
}

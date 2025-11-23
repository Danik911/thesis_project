import Link from 'next/link'
import { SignInButton, SignedIn, SignedOut, UserButton } from '@clerk/nextjs'
import { QuestionMarkCircleIcon } from '@heroicons/react/24/outline'
import { useModal } from '@/context/ModalContext'

export default function Header() {
  const { openHowItWorks } = useModal();

  return (
    <header className="bg-slate-900/80 backdrop-blur-md border-b border-slate-700/50 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <Link
              href="/"
              className="focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900 rounded"
            >
              <div className="flex items-center gap-2 group">
                <div className="w-8 h-8 bg-blue-600/20 rounded-lg flex items-center justify-center shadow-[0_0_10px_rgba(59,130,246,0.5)] group-hover:shadow-[0_0_15px_rgba(59,130,246,0.8)] transition-all overflow-hidden border border-blue-500/30">
                  <img src="/logo.png" alt="PharmaGen AI Logo" className="w-full h-full object-cover" />
                </div>
                <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-cyan-300 cursor-pointer group-hover:from-blue-300 group-hover:to-cyan-200 transition-all">
                  PharmaGen <span className="text-slate-500 font-light text-sm">AI</span>
                </h1>
              </div>
            </Link>
          </div>
          <div className="flex items-center gap-6">
            <button
              onClick={openHowItWorks}
              className="text-sm font-medium text-slate-300 hover:text-white transition-colors flex items-center gap-2"
            >
              <QuestionMarkCircleIcon className="h-5 w-5" />
              <span className="hidden sm:inline">How It Works</span>
            </button>

            <div className="h-6 w-px bg-slate-700 mx-2"></div>

            <Link href="/generate" className="text-sm font-medium text-slate-300 hover:text-white transition-colors">
              Generate
            </Link>
            <Link href="/history" className="text-sm font-medium text-slate-300 hover:text-white transition-colors">
              History
            </Link>
            <SignedOut>
              <SignInButton mode="modal">
                <button className="btn-primary">
                  Sign In
                </button>
              </SignInButton>
            </SignedOut>
            <SignedIn>
              <div className="flex items-center gap-4">
                <UserButton
                  afterSignOutUrl="/"
                  appearance={{
                    elements: {
                      avatarBox: "w-9 h-9 border-2 border-blue-500/30 hover:border-blue-500/80 transition-colors"
                    }
                  }}
                />
              </div>
            </SignedIn>
          </div>
        </div>
      </div>
    </header>
  )
}

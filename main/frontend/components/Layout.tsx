import { Protect, RedirectToSignIn, useUser, UserButton } from '@clerk/nextjs';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { ReactNode, useEffect } from 'react';

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const { user, isLoaded } = useUser();
  const router = useRouter();

  const isActive = (path: string) => router.pathname === path;

  // Derive display name with fallback chain
  const displayName = user?.fullName ??
    user?.firstName ??
    user?.emailAddresses?.[0]?.emailAddress ??
    'User';

  // Focus management on route changes (WCAG 2.4.3 - Focus Order)
  useEffect(() => {
    const handleRouteChange = () => {
      const mainContent = document.getElementById('main-content');
      if (mainContent) {
        mainContent.focus();
      }
    };

    router.events.on('routeChangeComplete', handleRouteChange);
    return () => {
      router.events.off('routeChangeComplete', handleRouteChange);
    };
  }, [router.events]);

  return (
    <Protect
      fallback={<RedirectToSignIn />}
    >
      <div className="min-h-screen bg-slate-900 flex flex-col text-slate-100">
        {/* Header/Navigation (WCAG 1.3.1 - ARIA Landmarks) */}
        <header role="banner" className="sticky top-0 z-40">
          {/* Skip to main content link (WCAG 2.4.1 - Bypass Blocks) */}
          <a
            href="#main-content"
            className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:p-4 focus:bg-blue-600 focus:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 rounded-md shadow-lg"
          >
            Skip to main content
          </a>
          <nav role="navigation" aria-label="Main navigation" className="bg-slate-900/80 backdrop-blur-md border-b border-slate-700/50">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between items-center h-16">
                {/* Logo and Navigation Links */}
                <div className="flex items-center gap-8">
                  <Link
                    href="/dashboard"
                    className="focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900 rounded"
                  >
                    <div className="flex items-center gap-2 group">
                      <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center shadow-[0_0_10px_rgba(59,130,246,0.5)] group-hover:shadow-[0_0_15px_rgba(59,130,246,0.8)] transition-all">
                        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                        </svg>
                      </div>
                      <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-cyan-300 cursor-pointer group-hover:from-blue-300 group-hover:to-cyan-200 transition-all">
                        PharmaGen <span className="text-slate-400 font-light text-sm">AI</span>
                      </h1>
                    </div>
                  </Link>

                  <div className="hidden md:flex items-center gap-1">
                    <Link
                      href="/dashboard"
                      aria-current={isActive('/dashboard') ? 'page' : undefined}
                      className={`text-sm font-medium transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900 rounded-lg px-3 py-2 ${isActive('/dashboard')
                        ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                        : 'text-slate-400 hover:text-blue-300 hover:bg-slate-800'
                        }`}
                    >
                      Dashboard
                    </Link>
                    <Link
                      href="/history"
                      aria-current={isActive('/history') ? 'page' : undefined}
                      className={`text-sm font-medium transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900 rounded-lg px-3 py-2 ${isActive('/history')
                        ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                        : 'text-slate-400 hover:text-blue-300 hover:bg-slate-800'
                        }`}
                    >
                      History
                    </Link>
                  </div>
                </div>

                {/* User Profile and Button */}
                <div className="flex items-center gap-4">
                  {isLoaded && user ? (
                    <>
                      <span className="hidden sm:inline text-sm text-slate-300">
                        {displayName}
                      </span>
                      <UserButton
                        afterSignOutUrl="/"
                        appearance={{
                          elements: {
                            avatarBox: "w-9 h-9 border-2 border-blue-500/30 hover:border-blue-500/80 transition-colors"
                          }
                        }}
                      />
                    </>
                  ) : (
                    <div className="h-8 w-8 bg-slate-800 rounded-full animate-pulse"></div>
                  )}
                </div>
              </div>
            </div>
          </nav>
        </header>

        {/* Main Content (WCAG 1.3.1 - ARIA Landmarks) */}
        <main id="main-content" role="main" tabIndex={-1} className="flex-1 focus:outline-none relative">
          {/* Background ambient glow */}
          <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10 pointer-events-none">
            <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-600/10 rounded-full blur-[100px]"></div>
            <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-cyan-600/10 rounded-full blur-[100px]"></div>
          </div>
          {children}
        </main>

        {/* Footer (WCAG 1.3.1 - ARIA Landmarks) */}
        <footer role="contentinfo" className="bg-slate-900/80 backdrop-blur-md border-t border-slate-800 mt-auto">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="text-center space-y-2">
              <p className="text-xs text-slate-400">
                © 2025 Pharmaceutical Test Generation System
              </p>
              <p className="text-xs text-slate-600 font-mono">
                GAMP-5 Compliant | ALCOA+ Validated | 21 CFR Part 11 Ready
              </p>
            </div>
          </div>
        </footer>
      </div>
    </Protect>
  );
}

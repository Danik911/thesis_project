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
      <div className="min-h-screen bg-gray-50 flex flex-col">
        {/* Skip to main content link (WCAG 2.4.1 - Bypass Blocks) */}
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:top-0 focus:left-0 focus:z-50 focus:p-4 focus:bg-blue-600 focus:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-800"
        >
          Skip to main content
        </a>

        {/* Header/Navigation (WCAG 1.3.1 - ARIA Landmarks) */}
        <header role="banner">
          <nav role="navigation" aria-label="Main navigation" className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              {/* Logo and Navigation Links */}
              <div className="flex items-center gap-8">
                <Link
                  href="/dashboard"
                  className="focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2 rounded"
                >
                  <h1 className="text-xl font-semibold text-gray-900 cursor-pointer hover:text-blue-600 transition-colors">
                    Pharmaceutical Test Generation
                  </h1>
                </Link>

                <div className="hidden md:flex items-center gap-6">
                  <Link
                    href="/dashboard"
                    aria-current={isActive('/dashboard') ? 'page' : undefined}
                    className={`text-sm font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2 rounded px-2 py-1 ${
                      isActive('/dashboard')
                        ? 'text-blue-600'
                        : 'text-gray-600 hover:text-blue-600'
                    }`}
                  >
                    Dashboard
                  </Link>
                  <Link
                    href="/observability"
                    aria-current={isActive('/observability') ? 'page' : undefined}
                    className={`text-sm font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2 rounded px-2 py-1 ${
                      isActive('/observability')
                        ? 'text-blue-600'
                        : 'text-gray-600 hover:text-blue-600'
                    }`}
                  >
                    Observability
                  </Link>
                </div>
              </div>

              {/* User Profile and Button */}
              <div className="flex items-center gap-4">
                {isLoaded && user ? (
                  <>
                    <span className="hidden sm:inline text-sm text-gray-600">
                      {displayName}
                    </span>
                    <UserButton afterSignOutUrl="/" />
                  </>
                ) : (
                  <div className="h-8 w-8 bg-gray-200 rounded-full animate-pulse"></div>
                )}
              </div>
            </div>
          </div>
          </nav>
        </header>

        {/* Main Content (WCAG 1.3.1 - ARIA Landmarks) */}
        <main id="main-content" role="main" tabIndex={-1} className="flex-1 focus:outline-none">
          {children}
        </main>

        {/* Footer (WCAG 1.3.1 - ARIA Landmarks) */}
        <footer role="contentinfo" className="bg-white border-t mt-auto">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="text-center space-y-2">
              <p className="text-xs text-gray-500">
                © 2025 Pharmaceutical Test Generation System
              </p>
              <p className="text-xs text-gray-700">
                GAMP-5 Compliant | ALCOA+ Validated | 21 CFR Part 11 Ready
              </p>
            </div>
          </div>
        </footer>
      </div>
    </Protect>
  );
}

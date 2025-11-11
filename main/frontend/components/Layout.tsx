import { Protect, RedirectToSignIn, useUser, UserButton } from '@clerk/nextjs';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { ReactNode } from 'react';

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const { user, isLoaded } = useUser();
  const router = useRouter();

  const isActive = (path: string) => router.pathname === path;

  // Derive display name with fallback chain
  const displayName = user?.fullName ??
    (user?.firstName || user?.emailAddresses[0]?.emailAddress) ??
    'User';

  return (
    <Protect
      fallback={<RedirectToSignIn />}
    >
      <div className="min-h-screen bg-gray-50 flex flex-col">
        {/* Navigation */}
        <nav className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              {/* Logo and Navigation Links */}
              <div className="flex items-center gap-8">
                <Link href="/dashboard">
                  <h1 className="text-xl font-semibold text-gray-900 cursor-pointer hover:text-blue-600 transition-colors">
                    Pharmaceutical Test Generation
                  </h1>
                </Link>

                <div className="hidden md:flex items-center gap-6">
                  <Link
                    href="/dashboard"
                    className={`text-sm font-medium transition-colors ${
                      isActive('/dashboard')
                        ? 'text-blue-600'
                        : 'text-gray-600 hover:text-blue-600'
                    }`}
                  >
                    Dashboard
                  </Link>
                  <Link
                    href="/observability"
                    className={`text-sm font-medium transition-colors ${
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

        {/* Main Content */}
        <main className="flex-1">
          {children}
        </main>

        {/* Footer */}
        <footer className="bg-white border-t mt-auto">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="text-center space-y-2">
              <p className="text-xs text-gray-500">
                © 2025 Pharmaceutical Test Generation System
              </p>
              <p className="text-xs text-gray-400">
                GAMP-5 Compliant | ALCOA+ Validated | 21 CFR Part 11 Ready
              </p>
            </div>
          </div>
        </footer>
      </div>
    </Protect>
  );
}

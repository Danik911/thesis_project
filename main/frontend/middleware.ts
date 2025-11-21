import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server';

/**
 * Clerk Middleware for Next.js Pages Router
 *
 * This middleware enables Clerk authentication for API routes.
 * Required for getAuth() to work in API routes.
 *
 * Protection Strategy:
 * - API routes under /api/langfuse/* require authentication
 * - Public routes: sign-in, sign-up, homepage
 * - Protected routes: dashboard, observability
 */

// Define protected routes that require authentication
const isProtectedRoute = createRouteMatcher([
  '/dashboard(.*)',
  '/observability(.*)',
  '/api/langfuse(.*)',  // Protect LangFuse API routes
]);

export default clerkMiddleware((auth, req) => {
  // Protect routes that match the pattern
  if (isProtectedRoute(req)) {
    auth.protect();
  }
});

export const config = {
  // Match all routes except static files and internal Next.js routes
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - _next/data (Next.js data prefetch JSON)
     * - favicon.ico (favicon file)
     * - public files (public folder)
     */
    '/((?!_next/static|_next/image|_next/data|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
};

/**
 * Accessibility Testing Utility
 *
 * Integrates axe-core for runtime accessibility testing during development.
 *
 * GAMP-5 Compliance: Automated accessibility checks support validation documentation
 * for WCAG 2.1 AA and pharmaceutical UI standards.
 *
 * Features:
 * - Client-side only (prevents SSR errors)
 * - Development-only (not bundled in production)
 * - Dynamic imports (loaded only when needed)
 * - Outputs violations to browser console
 *
 * NO FALLBACK LOGIC: If axe-core fails to load or run, errors are thrown explicitly.
 */

import type React from 'react'

export const reportAccessibility = async (
  App: typeof React,
  config?: Record<string, unknown>
): Promise<void> => {
  if (
    typeof window !== 'undefined' &&
    process.env.NODE_ENV !== 'production'
  ) {
    try {
      const axe = await import('@axe-core/react')
      const ReactDOM = await import('react-dom')

      // Run axe-core with 1000ms debounce
      axe.default(App, ReactDOM, 1000, config)

      console.log('[Accessibility] axe-core initialized successfully')
    } catch (error) {
      // NO FALLBACK - Explicit error reporting
      console.error('[Accessibility] Failed to initialize axe-core:', error)
      throw new Error(
        `Accessibility testing initialization failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      )
    }
  }
}

export default reportAccessibility

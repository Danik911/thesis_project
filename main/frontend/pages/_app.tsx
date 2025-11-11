import '@/styles/globals.css'
import type { AppProps } from 'next/app'
import { ClerkProvider } from '@clerk/nextjs'
import React from 'react'
import reportAccessibility from '../utils/reportAccessibility'

// Initialize axe-core accessibility testing (development only)
if (process.env.NODE_ENV !== 'production') {
  reportAccessibility(React).catch((error) => {
    console.error('[Accessibility] Failed to initialize axe-core:', error);
  });
}

export default function App({ Component, pageProps }: AppProps) {
  return (
    <ClerkProvider {...pageProps}>
      <Component {...pageProps} />
    </ClerkProvider>
  )
}

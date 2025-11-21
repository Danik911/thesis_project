import '@/styles/globals.css'
import type { AppProps } from 'next/app'
import { ClerkProvider } from '@clerk/nextjs'
import Head from 'next/head'
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
      <Head>
        <title>PharmaGen AI</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>
      <Component {...pageProps} />
    </ClerkProvider>
  )
}

import '@/styles/globals.css'
import type { AppProps } from 'next/app'
import { ClerkProvider } from '@clerk/nextjs'
import Head from 'next/head'
import React from 'react'
import dynamic from 'next/dynamic'
import reportAccessibility from '../utils/reportAccessibility'
import { ModalProvider } from '@/context/ModalContext'
import { Space_Grotesk, Instrument_Sans } from 'next/font/google'

// Dynamic import for custom cursor (client-side only)
const CustomCursor = dynamic(() => import('@/components/CustomCursor'), {
  ssr: false,
})

// Initialize fonts
const spaceGrotesk = Space_Grotesk({
  subsets: ['latin'],
  variable: '--font-display',
  display: 'swap',
})

const instrumentSans = Instrument_Sans({
  subsets: ['latin'],
  variable: '--font-body',
  display: 'swap',
})

// Initialize axe-core accessibility testing (development only)
if (process.env.NODE_ENV !== 'production') {
  reportAccessibility(React).catch((error) => {
    console.error('[Accessibility] Failed to initialize axe-core:', error);
  });
}

export default function App({ Component, pageProps }: AppProps) {
  return (
    <ClerkProvider {...pageProps}>
      <ModalProvider>
        <Head>
          <title>PharmaGen AI</title>
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          <link rel="icon" href="/favicon.png" />
        </Head>
        <main className={`${spaceGrotesk.variable} ${instrumentSans.variable} font-sans`}>
          <CustomCursor />
          <Component {...pageProps} />
        </main>
      </ModalProvider>
    </ClerkProvider>
  )
}

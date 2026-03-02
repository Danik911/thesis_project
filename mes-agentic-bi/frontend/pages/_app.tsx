import '@/styles/globals.css'
import type { AppProps } from 'next/app'
import Head from 'next/head'
import { Space_Grotesk, Instrument_Sans } from 'next/font/google'

import { AuthProvider } from '@/lib/auth'

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

export default function App({ Component, pageProps }: AppProps) {
  return (
    <AuthProvider>
      <Head>
        <title>MES Agentic BI</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.png" />
      </Head>
      <main className={`${spaceGrotesk.variable} ${instrumentSans.variable} font-sans`}>
        <Component {...pageProps} />
      </main>
    </AuthProvider>
  )
}

import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import Script from 'next/script'
import './globals.css'
import { AuthProvider } from '@/components/AuthProvider'
import { ClarityAnalytics } from '@/components/ClarityAnalytics'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'OddWons - Prediction Market Analysis',
  description: 'AI-powered analysis for Kalshi and Polymarket prediction markets',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      {/* Google Ads Tag */}
      <Script
        src="https://www.googletagmanager.com/gtag/js?id=AW-17868225226"
        strategy="afterInteractive"
      />
      <Script id="google-ads" strategy="afterInteractive">
        {`
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('js', new Date());
          gtag('config', 'AW-17868225226');
        `}
      </Script>
      <body className={inter.className}>
        <ClarityAnalytics />
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  )
}

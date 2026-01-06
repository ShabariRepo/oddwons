'use client'

import Link from 'next/link'
import Image from 'next/image'
import { TrendingUp, Bell, BarChart3, Shield, Clock, Check, Zap, User, LogOut } from 'lucide-react'
import { useAuth } from '@/components/AuthProvider'

// SVG pattern for hero background - dollar bills with wings, logo, :D face
const heroPatternSvg = `
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
  <!-- Dollar bill with wings -->
  <g transform="translate(20, 20)" opacity="0.15">
    <rect x="0" y="8" width="40" height="24" rx="2" fill="%2322c55e" stroke="%2316a34a" stroke-width="1"/>
    <text x="20" y="24" font-size="14" text-anchor="middle" fill="%23166534" font-weight="bold">$</text>
    <!-- Left wing -->
    <path d="M-2 12 Q-12 8 -8 20 Q-4 16 0 20" fill="%2386efac" stroke="%2322c55e"/>
    <!-- Right wing -->
    <path d="M42 12 Q52 8 48 20 Q44 16 40 20" fill="%2386efac" stroke="%2322c55e"/>
  </g>

  <!-- :D face -->
  <g transform="translate(130, 30)" opacity="0.12">
    <circle cx="15" cy="15" r="15" fill="%23fbbf24" stroke="%23f59e0b" stroke-width="1"/>
    <circle cx="10" cy="12" r="2" fill="%2378350f"/>
    <circle cx="20" cy="12" r="2" fill="%2378350f"/>
    <path d="M8 18 Q15 26 22 18" fill="none" stroke="%2378350f" stroke-width="2" stroke-linecap="round"/>
  </g>

  <!-- Dollar bill with wings (offset) -->
  <g transform="translate(100, 100)" opacity="0.15">
    <rect x="0" y="8" width="40" height="24" rx="2" fill="%2322c55e" stroke="%2316a34a" stroke-width="1"/>
    <text x="20" y="24" font-size="14" text-anchor="middle" fill="%23166534" font-weight="bold">$</text>
    <!-- Left wing -->
    <path d="M-2 12 Q-12 8 -8 20 Q-4 16 0 20" fill="%2386efac" stroke="%2322c55e"/>
    <!-- Right wing -->
    <path d="M42 12 Q52 8 48 20 Q44 16 40 20" fill="%2386efac" stroke="%2322c55e"/>
  </g>

  <!-- :D face (offset) -->
  <g transform="translate(30, 120)" opacity="0.12">
    <circle cx="15" cy="15" r="15" fill="%23fbbf24" stroke="%23f59e0b" stroke-width="1"/>
    <circle cx="10" cy="12" r="2" fill="%2378350f"/>
    <circle cx="20" cy="12" r="2" fill="%2378350f"/>
    <path d="M8 18 Q15 26 22 18" fill="none" stroke="%2378350f" stroke-width="2" stroke-linecap="round"/>
  </g>

  <!-- OW logo representation -->
  <g transform="translate(150, 140)" opacity="0.1">
    <rect x="0" y="0" width="30" height="30" rx="6" fill="%234f46e5"/>
    <text x="15" y="22" font-size="12" text-anchor="middle" fill="white" font-weight="bold">OW</text>
  </g>

  <!-- OW logo representation (offset) -->
  <g transform="translate(60, 60)" opacity="0.1">
    <rect x="0" y="0" width="30" height="30" rx="6" fill="%234f46e5"/>
    <text x="15" y="22" font-size="12" text-anchor="middle" fill="white" font-weight="bold">OW</text>
  </g>
</svg>
`

const features = [
  {
    icon: TrendingUp,
    title: 'Cross-Platform Comparison',
    description: 'Compare the same markets on Kalshi and Polymarket to see how prices differ.',
  },
  {
    icon: Zap,
    title: 'AI Market Highlights',
    description: 'AI-powered summaries of notable markets, price movements, and market context.',
  },
  {
    icon: Bell,
    title: 'Smart Alerts',
    description: 'Get notified when markets you care about have significant price changes.',
  },
  {
    icon: BarChart3,
    title: 'Market Analytics',
    description: 'Historical data and volume trends to understand market dynamics.',
  },
  {
    icon: Shield,
    title: 'Research Tools',
    description: 'Context and analysis for every market to inform your decisions.',
  },
  {
    icon: Clock,
    title: 'Real-Time Updates',
    description: 'Market data refreshed every 15 minutes with premium real-time options.',
  },
]

const tiers = [
  {
    name: 'Basic',
    price: 9.99,
    features: [
      'Daily market digest',
      'Top 10 market highlights',
      'Email notifications',
      'Price movement alerts',
      '7-day free trial',
    ],
  },
  {
    name: 'Premium',
    price: 19.99,
    popular: true,
    features: [
      'Everything in Basic',
      'Real-time alerts',
      'Custom parameters',
      'SMS notifications',
      'Discord/Slack integration',
      '7-day free trial',
    ],
  },
  {
    name: 'Pro',
    price: 29.99,
    features: [
      'Everything in Premium',
      'Advanced patterns',
      'API access',
      'Priority support',
      'Early feature access',
      '7-day free trial',
    ],
  },
]

export default function LandingPage() {
  const { user, isAuthenticated, logout } = useAuth()

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link href="/" className="flex items-center gap-2">
              <Image
                src="/oddwons-logo.png"
                alt="OddWons"
                width={48}
                height={48}
                className="rounded-lg"
              />
              <span className="text-xl font-bold text-gray-900">OddWons</span>
            </Link>
            <div className="flex items-center gap-4">
              {isAuthenticated ? (
                <>
                  <Link href="/dashboard" className="flex items-center gap-2 text-sm font-medium text-gray-600 hover:text-gray-900">
                    <User className="w-4 h-4" />
                    {user?.name || user?.email?.split('@')[0] || 'Dashboard'}
                  </Link>
                  <button
                    onClick={logout}
                    className="flex items-center gap-1 text-sm font-medium text-gray-500 hover:text-gray-700"
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                </>
              ) : (
                <>
                  <Link href="/login" className="text-sm font-medium text-gray-600 hover:text-gray-900">
                    Sign in
                  </Link>
                  <Link
                    href="/register"
                    className="text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 px-4 py-2 rounded-lg transition-colors"
                  >
                    Get Started
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
        {/* Animated scrolling pattern background */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            backgroundImage: `url("data:image/svg+xml,${encodeURIComponent(heroPatternSvg)}")`,
            backgroundSize: '200px 200px',
            animation: 'scrollPattern 8s linear infinite',
          }}
        />
        <style jsx>{`
          @keyframes scrollPattern {
            0% {
              background-position: 0 0;
            }
            100% {
              background-position: 0 200px;
            }
          }
        `}</style>
        <div className="max-w-4xl mx-auto text-center relative z-10">
          <h1 className="text-5xl sm:text-6xl font-bold text-gray-900 leading-tight">
            Your{' '}
            <span className="text-primary-600">Prediction Market</span>{' '}
            Research Companion
          </h1>
          <p className="mt-6 text-xl text-gray-600 max-w-2xl mx-auto">
            AI-powered insights for Kalshi and Polymarket. Compare prices across platforms,
            get market highlights, and save hours of research.
          </p>
          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/register"
              className="w-full sm:w-auto px-8 py-4 text-lg font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-xl transition-colors"
            >
              Start Free Trial
            </Link>
            <Link
              href="/login"
              className="w-full sm:w-auto px-8 py-4 text-lg font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-xl transition-colors"
            >
              Sign In
            </Link>
          </div>
          <p className="mt-4 text-sm text-gray-500">No credit card required. 7-day free trial on all plans.</p>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900">Everything You Need to Research Markets</h2>
            <p className="mt-4 text-lg text-gray-600">
              Powerful tools to understand prediction markets and make informed decisions.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature) => (
              <div key={feature.title} className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mb-4">
                  <feature.icon className="w-6 h-6 text-primary-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{feature.title}</h3>
                <p className="text-gray-600">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900">Simple, Transparent Pricing</h2>
            <p className="mt-4 text-lg text-gray-600">
              Choose the plan that fits your trading style.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {tiers.map((tier) => (
              <div
                key={tier.name}
                className={`relative bg-white p-6 rounded-xl border-2 ${
                  tier.popular ? 'border-primary-500 shadow-lg' : 'border-gray-100'
                }`}
              >
                {tier.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <span className="bg-primary-600 text-white text-xs font-medium px-3 py-1 rounded-full">
                      Most Popular
                    </span>
                  </div>
                )}
                <h3 className="text-lg font-semibold text-gray-900">{tier.name}</h3>
                <p className="mt-4">
                  <span className="text-4xl font-bold text-gray-900">
                    {tier.price === 0 ? 'Free' : `$${tier.price}`}
                  </span>
                  {tier.price > 0 && <span className="text-gray-500">/month</span>}
                </p>
                <ul className="mt-6 space-y-3">
                  {tier.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-2">
                      <Check className="w-5 h-5 text-green-500 shrink-0 mt-0.5" />
                      <span className="text-sm text-gray-600">{feature}</span>
                    </li>
                  ))}
                </ul>
                <Link
                  href="/register"
                  className={`mt-8 block text-center py-3 px-4 rounded-lg font-medium transition-colors ${
                    tier.popular
                      ? 'bg-primary-600 text-white hover:bg-primary-700'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Get Started
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-primary-600">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-white">Ready to Save Time on Research?</h2>
          <p className="mt-4 text-lg text-primary-100">
            Join prediction market enthusiasts using OddWons for AI-powered market insights.
          </p>
          <Link
            href="/register"
            className="mt-8 inline-block px-8 py-4 text-lg font-medium text-primary-600 bg-white hover:bg-gray-100 rounded-xl transition-colors"
          >
            Start Your Free Trial
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <Image
                src="/oddwons-logo.png"
                alt="OddWons"
                width={32}
                height={32}
                className="rounded-lg"
              />
              <span className="text-lg font-bold text-white">OddWons</span>
            </div>
            <p className="text-gray-400 text-sm">
              &copy; {new Date().getFullYear()} OddWons. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}

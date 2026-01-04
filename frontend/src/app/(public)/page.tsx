'use client'

import Link from 'next/link'
import Image from 'next/image'
import { TrendingUp, Bell, BarChart3, Shield, Clock, Check } from 'lucide-react'

const features = [
  {
    icon: TrendingUp,
    title: 'Cross-Platform Analysis',
    description: 'Monitor Kalshi and Polymarket markets in one place with real-time price tracking.',
  },
  {
    icon: Zap,
    title: 'Pattern Detection',
    description: 'AI-powered detection of volume spikes, price movements, and arbitrage opportunities.',
  },
  {
    icon: Bell,
    title: 'Smart Alerts',
    description: 'Get notified instantly when high-value opportunities match your criteria.',
  },
  {
    icon: BarChart3,
    title: 'Advanced Analytics',
    description: 'Historical data analysis and performance tracking for informed decisions.',
  },
  {
    icon: Shield,
    title: 'Risk Assessment',
    description: 'Confidence scores and risk ratings for every detected opportunity.',
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
      'Top 5 opportunities',
      'Email notifications',
      'Basic pattern alerts',
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
                width={36}
                height={36}
                className="rounded-lg"
              />
              <span className="text-xl font-bold text-gray-900">OddWons</span>
            </Link>
            <div className="flex items-center gap-4">
              <Link href="/login" className="text-sm font-medium text-gray-600 hover:text-gray-900">
                Sign in
              </Link>
              <Link
                href="/register"
                className="text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 px-4 py-2 rounded-lg transition-colors"
              >
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-5xl sm:text-6xl font-bold text-gray-900 leading-tight">
            Find Profitable{' '}
            <span className="text-primary-600">Prediction Market</span>{' '}
            Opportunities
          </h1>
          <p className="mt-6 text-xl text-gray-600 max-w-2xl mx-auto">
            AI-powered analysis for Kalshi and Polymarket. Detect patterns, spot arbitrage,
            and get alerts for high-value opportunities before everyone else.
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
            <h2 className="text-3xl font-bold text-gray-900">Everything You Need to Win</h2>
            <p className="mt-4 text-lg text-gray-600">
              Powerful tools to analyze prediction markets and find profitable opportunities.
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
          <h2 className="text-3xl font-bold text-white">Ready to Find Your Edge?</h2>
          <p className="mt-4 text-lg text-primary-100">
            Join traders using OddWons to discover profitable prediction market opportunities.
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

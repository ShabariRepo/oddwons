'use client'

import { useEffect, useRef } from 'react'

interface TierBadgeProps {
  tier: 'BASIC' | 'PREMIUM' | 'PRO'
  daysLeft?: number // If on trial
}

export default function TierBadge({ tier, daysLeft }: TierBadgeProps) {
  const badgeRef = useRef<HTMLDivElement>(null)

  // Bubble/sparkle effect for PREMIUM and PRO
  useEffect(() => {
    if (!badgeRef.current || tier === 'BASIC') return

    const container = badgeRef.current
    const interval = setInterval(() => {
      createParticle(container, tier)
    }, tier === 'PRO' ? 100 : 200)

    return () => clearInterval(interval)
  }, [tier])

  const createParticle = (container: HTMLElement, tierType: string) => {
    const particle = document.createElement('div')
    const x = Math.random() * container.offsetWidth
    const size = 2 + Math.random() * 3

    const colors: Record<string, string[]> = {
      PREMIUM: ['#d4af37', '#f5e6c8', '#c9b896'], // Champagne
      PRO: ['#ffd700', '#ffec80', '#fff4cc'],      // Gold
    }
    const colorArray = colors[tierType] || colors.PRO
    const color = colorArray[Math.floor(Math.random() * 3)]

    particle.style.cssText = `
      position: absolute;
      left: ${x}px;
      bottom: 0;
      width: ${size}px;
      height: ${size}px;
      background: ${color};
      border-radius: 50%;
      pointer-events: none;
      animation: tier-bubble ${1.5 + Math.random()}s ease-out forwards;
      box-shadow: 0 0 ${size}px ${color};
    `

    container.appendChild(particle)
    setTimeout(() => particle.remove(), 2500)
  }

  // If on trial, show countdown
  if (daysLeft !== undefined && daysLeft > 0) {
    return (
      <div className="mx-3 mb-4 p-3 bg-gradient-to-r from-amber-50 to-yellow-50 border border-amber-200 rounded-xl">
        <div className="flex items-center gap-2">
          <span className="text-lg">⏳</span>
          <div>
            <p className="text-sm font-semibold text-amber-800">
              {daysLeft} day{daysLeft !== 1 ? 's' : ''} left on trial
            </p>
            <p className="text-xs text-amber-600">{tier} plan</p>
          </div>
        </div>

        <style jsx global>{`
          @keyframes tier-bubble {
            0% {
              transform: translateY(0) scale(1);
              opacity: 0.8;
            }
            100% {
              transform: translateY(-40px) scale(0);
              opacity: 0;
            }
          }
        `}</style>
      </div>
    )
  }

  // Paid user badges
  const styles = {
    BASIC: {
      bg: 'bg-gradient-to-r from-yellow-400 to-amber-400',
      text: 'text-yellow-900',
      shadow: 'shadow-yellow-200',
    },
    PREMIUM: {
      bg: 'bg-gradient-to-r from-amber-200 via-yellow-100 to-amber-200',
      text: 'text-amber-800',
      shadow: 'shadow-amber-100',
    },
    PRO: {
      bg: 'bg-gradient-to-r from-yellow-400 via-amber-300 to-yellow-400',
      text: 'text-yellow-900',
      shadow: 'shadow-yellow-300',
    },
  }

  const style = styles[tier]

  return (
    <div className="mx-3 mb-4 relative overflow-visible">
      <div
        ref={badgeRef}
        className={`relative p-3 ${style.bg} rounded-xl shadow-lg ${style.shadow} overflow-visible`}
      >
        {/* Ribbon fold effect */}
        <div className="absolute -right-2 -top-2 w-4 h-4 bg-amber-600 rounded-sm transform rotate-45 opacity-30" />

        <div className="flex items-center justify-center gap-2">
          <span className="text-lg">
            {tier === 'BASIC' && '⭐'}
            {tier === 'PREMIUM' && '💎'}
            {tier === 'PRO' && '👑'}
          </span>
          <span className={`font-bold ${style.text}`}>{tier}</span>
        </div>
      </div>

      <style jsx global>{`
        @keyframes tier-bubble {
          0% {
            transform: translateY(0) scale(1);
            opacity: 0.8;
          }
          100% {
            transform: translateY(-40px) scale(0);
            opacity: 0;
          }
        }
      `}</style>
    </div>
  )
}

'use client'

import Image from 'next/image'

interface PatternItem {
  type: 'logo' | 'cash' | 'smile'
  x: number
  y: number
  rotate: number
  size: number
  delay: number
}

// Generate a grid of pattern items
const generatePattern = (): PatternItem[] => {
  const items: PatternItem[] = []
  const types: ('logo' | 'cash' | 'smile')[] = ['logo', 'cash', 'smile']

  // Create a grid pattern with deterministic positions (avoid hydration mismatch)
  for (let row = 0; row < 8; row++) {
    for (let col = 0; col < 10; col++) {
      const typeIndex = (row + col) % 3
      const seed = row * 10 + col
      items.push({
        type: types[typeIndex],
        x: col * 10 + (row % 2) * 5 + (seed % 3), // Staggered grid with slight variation
        y: row * 12 + (seed % 3),
        rotate: ((seed * 7) % 30) - 15, // -15 to +15 degrees
        size: 30 + (seed % 15), // 30-45px
        delay: (seed % 30) / 10, // 0-3s animation delay
      })
    }
  }
  return items
}

const PATTERN_ITEMS = generatePattern()

interface BrandPatternProps {
  className?: string
  opacity?: number
  animated?: boolean
}

export default function BrandPattern({
  className = '',
  opacity = 0.08,
  animated = true
}: BrandPatternProps) {
  return (
    <div className={`absolute inset-0 overflow-hidden pointer-events-none ${className}`}>
      {PATTERN_ITEMS.map((item, i) => (
        <div
          key={i}
          className={`absolute select-none ${animated ? 'animate-float' : ''}`}
          style={{
            left: `${item.x}%`,
            top: `${item.y}%`,
            transform: `rotate(${item.rotate}deg)`,
            opacity: opacity,
            animationDelay: animated ? `${item.delay}s` : undefined,
          }}
        >
          {item.type === 'logo' ? (
            <Image
              src="/oddwons-logo.png"
              alt=""
              width={item.size}
              height={item.size}
              className="rounded-lg"
            />
          ) : (
            <span style={{ fontSize: `${item.size}px` }}>
              {item.type === 'cash' ? '💸' : '😁'}
            </span>
          )}
        </div>
      ))}
    </div>
  )
}

'use client'

import { useEffect, useRef } from 'react'

interface SparkleCardProps {
  children: React.ReactNode
  active?: boolean
  className?: string
}

export default function SparkleCard({ children, active = false, className = '' }: SparkleCardProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!active || !containerRef.current) return

    const container = containerRef.current
    const sparkleInterval = setInterval(() => {
      createSparkle(container)
    }, 150)

    return () => clearInterval(sparkleInterval)
  }, [active])

  const createSparkle = (container: HTMLElement) => {
    const sparkle = document.createElement('div')
    sparkle.className = 'sparkle'

    // Random position along the card edges and inside
    const x = Math.random() * container.offsetWidth

    sparkle.style.cssText = `
      position: absolute;
      left: ${x}px;
      bottom: 0;
      width: ${4 + Math.random() * 4}px;
      height: ${4 + Math.random() * 4}px;
      background: radial-gradient(circle, #ffd700 0%, #ffec80 50%, transparent 70%);
      border-radius: 50%;
      pointer-events: none;
      animation: sparkle-float ${2 + Math.random() * 2}s ease-out forwards;
      box-shadow: 0 0 ${4 + Math.random() * 4}px #ffd700;
    `

    container.appendChild(sparkle)

    // Remove after animation
    setTimeout(() => sparkle.remove(), 4000)
  }

  return (
    <div
      ref={containerRef}
      className={`relative overflow-visible ${active ? 'ring-2 ring-yellow-400 shadow-[0_0_30px_rgba(255,215,0,0.3)]' : ''} ${className}`}
    >
      {children}

      <style jsx global>{`
        @keyframes sparkle-float {
          0% {
            transform: translateY(0) scale(1);
            opacity: 1;
          }
          100% {
            transform: translateY(-120px) scale(0);
            opacity: 0;
          }
        }
      `}</style>
    </div>
  )
}

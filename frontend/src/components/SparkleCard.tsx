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

    const createSparkle = () => {
      if (!container) return

      const sparkle = document.createElement('div')
      const x = Math.random() * container.offsetWidth
      const size = 4 + Math.random() * 6

      sparkle.style.cssText = `
        position: absolute;
        left: ${x}px;
        bottom: 0;
        width: ${size}px;
        height: ${size}px;
        background: radial-gradient(circle, #ffd700 0%, #ffec80 50%, transparent 70%);
        border-radius: 50%;
        pointer-events: none;
        z-index: 50;
        box-shadow: 0 0 ${size * 2}px #ffd700;
        animation: sparkle-float ${2 + Math.random() * 2}s ease-out forwards;
      `

      container.appendChild(sparkle)
      setTimeout(() => sparkle.remove(), 4000)
    }

    // Create initial sparkles
    for (let i = 0; i < 5; i++) {
      setTimeout(createSparkle, i * 200)
    }

    const interval = setInterval(createSparkle, 150)
    return () => clearInterval(interval)
  }, [active])

  return (
    <div
      ref={containerRef}
      className={`relative ${className}`}
      style={{ overflow: 'visible' }}
    >
      {children}

      <style jsx global>{`
        @keyframes sparkle-float {
          0% {
            transform: translateY(0) scale(1);
            opacity: 1;
          }
          100% {
            transform: translateY(-150px) scale(0);
            opacity: 0;
          }
        }
      `}</style>
    </div>
  )
}

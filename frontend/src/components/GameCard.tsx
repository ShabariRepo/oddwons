'use client'

import { useRef, useState } from 'react'
import Image from 'next/image'

interface GameCardProps {
  children: React.ReactNode
  className?: string
  showWatermark?: boolean
}

export default function GameCard({ children, className = '', showWatermark = true }: GameCardProps) {
  const cardRef = useRef<HTMLDivElement>(null)
  const [isHovered, setIsHovered] = useState(false)

  const handleMouseEnter = () => {
    setIsHovered(true)
    if (cardRef.current) {
      // Create green wisps
      for (let i = 0; i < 5; i++) {
        setTimeout(() => {
          if (cardRef.current) {
            createWisp(cardRef.current)
          }
        }, i * 100)
      }
    }
  }

  const handleMouseLeave = () => {
    setIsHovered(false)
  }

  const createWisp = (container: HTMLElement) => {
    const wisp = document.createElement('div')
    const x = Math.random() * container.offsetWidth
    const size = 6 + Math.random() * 8
    const xOffset = Math.random() > 0.5 ? '10px' : '-10px'

    wisp.style.cssText = `
      position: absolute;
      left: ${x}px;
      bottom: 20%;
      width: ${size}px;
      height: ${size * 1.5}px;
      background: radial-gradient(ellipse, rgba(34, 197, 94, 0.6) 0%, rgba(34, 197, 94, 0.2) 50%, transparent 70%);
      border-radius: 50%;
      pointer-events: none;
      animation: wisp-float ${1 + Math.random() * 0.5}s ease-out forwards;
      filter: blur(1px);
      --x-offset: ${xOffset};
    `

    container.appendChild(wisp)
    setTimeout(() => wisp.remove(), 1500)
  }

  return (
    <div
      ref={cardRef}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      className={`relative overflow-visible transition-all duration-300 ease-out ${
        isHovered
          ? 'transform -translate-y-2 scale-[1.02]'
          : ''
      } ${className}`}
      style={{
        boxShadow: isHovered
          ? '0 20px 40px -10px rgba(0, 0, 0, 0.15), 0 10px 20px -5px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)'
          : undefined
      }}
    >
      {/* Logo watermark */}
      {showWatermark && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-0">
          <Image
            src="/oddwons-logo.png"
            alt=""
            width={80}
            height={80}
            className="opacity-[0.04] select-none"
          />
        </div>
      )}

      {/* Card content */}
      <div className="relative z-10">
        {children}
      </div>

      <style jsx global>{`
        @keyframes wisp-float {
          0% {
            transform: translateY(0) scale(1);
            opacity: 0.8;
          }
          50% {
            transform: translateY(-30px) scale(1.2) translateX(var(--x-offset, 10px));
            opacity: 0.6;
          }
          100% {
            transform: translateY(-60px) scale(0.5);
            opacity: 0;
          }
        }
      `}</style>
    </div>
  )
}

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
      className={`relative overflow-hidden transition-all duration-200 ${isHovered ? 'animate-card-shake' : ''} ${className}`}
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

        @keyframes card-shake {
          0%, 100% { transform: translateX(0); }
          10% { transform: translateX(-2px) rotate(-0.5deg); }
          20% { transform: translateX(2px) rotate(0.5deg); }
          30% { transform: translateX(-2px) rotate(-0.5deg); }
          40% { transform: translateX(2px) rotate(0.5deg); }
          50% { transform: translateX(-1px); }
          60% { transform: translateX(1px); }
          70% { transform: translateX(-1px); }
          80% { transform: translateX(1px); }
          90% { transform: translateX(0); }
        }

        .animate-card-shake {
          animation: card-shake 0.5s ease-in-out;
        }
      `}</style>
    </div>
  )
}

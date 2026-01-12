'use client'

import { useEffect, useState, useCallback } from 'react'
import Image from 'next/image'
import BrandPattern from '@/components/BrandPattern'

interface Emoji {
  id: number
  emoji: string
  x: number
  y: number
  angle: number
  velocity: number
  rotation: number
  rotationSpeed: number
  opacity: number
  scale: number
}

type Mode = 'spinning' | 'equation'
type EquationPhase = 'logos' | 'moai' | 'heart' | 'smirk'

export default function FunPage() {
  const [emojis, setEmojis] = useState<Emoji[]>([])
  const [emojiId, setEmojiId] = useState(0)
  const [mode, setMode] = useState<Mode>('spinning')
  const [transitioning, setTransitioning] = useState(false)
  const [equationPhase, setEquationPhase] = useState<EquationPhase>('logos')
  const [phaseVisible, setPhaseVisible] = useState(true)

  const spawnEmoji = useCallback(() => {
    if (mode !== 'spinning') return

    const emoji = Math.random() > 0.5 ? '💵' : '💰'
    const angle = Math.random() * 360

    const newEmoji: Emoji = {
      id: emojiId,
      emoji,
      x: 0,
      y: 0,
      angle: angle * (Math.PI / 180),
      velocity: 3 + Math.random() * 4,
      rotation: Math.random() * 360,
      rotationSpeed: (Math.random() - 0.5) * 20,
      opacity: 1,
      scale: 0.8 + Math.random() * 0.6,
    }

    setEmojiId(prev => prev + 1)
    setEmojis(prev => [...prev, newEmoji])
  }, [emojiId, mode])

  // Spawn emojis periodically
  useEffect(() => {
    if (mode !== 'spinning') return

    const spawnInterval = setInterval(() => {
      spawnEmoji()
    }, 150)

    return () => clearInterval(spawnInterval)
  }, [spawnEmoji, mode])

  // Animate emojis
  useEffect(() => {
    if (mode !== 'spinning') return

    const animationInterval = setInterval(() => {
      setEmojis(prev =>
        prev
          .map(e => ({
            ...e,
            x: e.x + Math.cos(e.angle) * e.velocity,
            y: e.y + Math.sin(e.angle) * e.velocity,
            rotation: e.rotation + e.rotationSpeed,
            opacity: e.opacity - 0.008,
            velocity: e.velocity * 0.99,
          }))
          .filter(e => e.opacity > 0)
      )
    }, 16)

    return () => clearInterval(animationInterval)
  }, [mode])

  // Cycle through equation phases
  useEffect(() => {
    if (mode !== 'equation') return

    const phases: EquationPhase[] = ['logos', 'moai', 'heart', 'smirk']

    const cyclePhase = () => {
      // Fade out
      setPhaseVisible(false)

      setTimeout(() => {
        setEquationPhase(prev => {
          const currentIndex = phases.indexOf(prev)
          const nextIndex = (currentIndex + 1) % phases.length
          return phases[nextIndex]
        })
        // Fade in
        setPhaseVisible(true)
      }, 500)
    }

    const interval = setInterval(cyclePhase, 2500)
    return () => clearInterval(interval)
  }, [mode])

  const handleClick = () => {
    if (transitioning) return

    setTransitioning(true)

    setTimeout(() => {
      if (mode === 'spinning') {
        setEmojis([])
        setMode('equation')
        setEquationPhase('logos')
        setPhaseVisible(true)
      } else {
        setMode('spinning')
      }
      setTransitioning(false)
    }, 500)
  }

  return (
    <div
      className="fixed inset-0 overflow-hidden bg-gradient-to-br from-primary-50 via-white to-primary-100 cursor-pointer select-none"
      onClick={handleClick}
    >
      {/* Full page brand pattern */}
      <BrandPattern opacity={0.5} animated={true} />

      {/* Content container */}
      <div className={`absolute inset-0 flex items-center justify-center transition-opacity duration-500 ${transitioning ? 'opacity-0' : 'opacity-100'}`}>

        {/* Spinning Logo Mode */}
        {mode === 'spinning' && (
          <div className="relative">
            {/* Emojis container */}
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              {emojis.map(e => (
                <span
                  key={e.id}
                  className="absolute text-4xl sm:text-5xl md:text-6xl"
                  style={{
                    transform: `translate(${e.x}px, ${e.y}px) rotate(${e.rotation}deg) scale(${e.scale})`,
                    opacity: e.opacity,
                  }}
                >
                  {e.emoji}
                </span>
              ))}
            </div>

            {/* Glow effect behind logo */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div
                className="w-48 h-48 sm:w-64 sm:h-64 md:w-80 md:h-80 rounded-full blur-3xl animate-pulse"
                style={{
                  background: 'radial-gradient(circle, rgba(14, 165, 233, 0.4) 0%, rgba(14, 165, 233, 0) 70%)',
                }}
              />
            </div>

            {/* Spinning logo */}
            <div className="relative animate-spin-slow">
              <Image
                src="/oddwons-logo.png"
                alt="OddWons"
                width={300}
                height={300}
                className="w-48 h-48 sm:w-64 sm:h-64 md:w-[300px] md:h-[300px] drop-shadow-2xl"
                priority
              />
            </div>
          </div>
        )}

        {/* Equation Mode */}
        {mode === 'equation' && (
          <div className={`flex flex-col items-center justify-center gap-4 sm:gap-6 md:gap-8 transition-opacity duration-500 ${phaseVisible ? 'opacity-100' : 'opacity-0'}`}>
            {equationPhase === 'logos' && (
              <div className="flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4 md:gap-6">
                {/* Kalshi */}
                <div className="flex items-center justify-center w-20 h-20 sm:w-28 sm:h-28 md:w-36 md:h-36 bg-white rounded-2xl shadow-lg p-3">
                  <Image
                    src="/logos/kalshi-logo.png"
                    alt="Kalshi"
                    width={120}
                    height={120}
                    className="w-full h-full object-contain"
                  />
                </div>

                <span className="text-4xl sm:text-5xl md:text-6xl font-bold text-primary-600">+</span>

                {/* Polymarket */}
                <div className="flex items-center justify-center w-20 h-20 sm:w-28 sm:h-28 md:w-36 md:h-36 bg-white rounded-2xl shadow-lg p-3">
                  <Image
                    src="/logos/polymarket-logo.png"
                    alt="Polymarket"
                    width={120}
                    height={120}
                    className="w-full h-full object-contain"
                  />
                </div>

                <span className="text-4xl sm:text-5xl md:text-6xl font-bold text-primary-600">+</span>

                {/* OddWons */}
                <div className="flex items-center justify-center w-20 h-20 sm:w-28 sm:h-28 md:w-36 md:h-36 bg-white rounded-2xl shadow-lg p-3">
                  <Image
                    src="/oddwons-logo.png"
                    alt="OddWons"
                    width={120}
                    height={120}
                    className="w-full h-full object-contain"
                  />
                </div>

                <span className="text-4xl sm:text-5xl md:text-6xl font-bold text-primary-600">=</span>

                {/* Moai */}
                <span className="text-7xl sm:text-8xl md:text-9xl">🗿</span>
              </div>
            )}

            {equationPhase === 'moai' && (
              <span className="text-[120px] sm:text-[180px] md:text-[240px] animate-pulse">🗿</span>
            )}

            {equationPhase === 'heart' && (
              <span className="text-[120px] sm:text-[180px] md:text-[240px] animate-pulse">❤️</span>
            )}

            {equationPhase === 'smirk' && (
              <span className="text-[120px] sm:text-[180px] md:text-[240px] animate-pulse">😏</span>
            )}
          </div>
        )}
      </div>

      {/* Fun text */}
      <div className="absolute bottom-6 sm:bottom-10 left-0 right-0 text-center px-4">
        <p className="text-lg sm:text-xl md:text-2xl font-bold text-primary-600 animate-bounce">
          Prediction Markets On Crack
        </p>
        <p className="text-xs sm:text-sm text-gray-400 mt-2">
          tap anywhere
        </p>
      </div>
    </div>
  )
}

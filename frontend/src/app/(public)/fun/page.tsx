'use client'

import { useEffect, useState, useCallback } from 'react'
import Image from 'next/image'
import { BrandPattern } from '@/components/BrandPattern'

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

export default function FunPage() {
  const [emojis, setEmojis] = useState<Emoji[]>([])
  const [emojiId, setEmojiId] = useState(0)

  const spawnEmoji = useCallback(() => {
    const emoji = Math.random() > 0.5 ? '💵' : '💰'
    const angle = Math.random() * 360
    const velocity = 3 + Math.random() * 4

    const newEmoji: Emoji = {
      id: emojiId,
      emoji,
      x: 0,
      y: 0,
      angle: angle * (Math.PI / 180),
      velocity,
      rotation: Math.random() * 360,
      rotationSpeed: (Math.random() - 0.5) * 20,
      opacity: 1,
      scale: 0.8 + Math.random() * 0.6,
    }

    setEmojiId(prev => prev + 1)
    setEmojis(prev => [...prev, newEmoji])
  }, [emojiId])

  // Spawn emojis periodically
  useEffect(() => {
    const spawnInterval = setInterval(() => {
      spawnEmoji()
    }, 150)

    return () => clearInterval(spawnInterval)
  }, [spawnEmoji])

  // Animate emojis
  useEffect(() => {
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
  }, [])

  return (
    <div className="fixed inset-0 overflow-hidden bg-gradient-to-br from-primary-50 via-white to-primary-100">
      {/* Full page brand pattern */}
      <BrandPattern opacity={0.5} animated={true} />

      {/* Centered spinning logo with emojis */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="relative">
          {/* Emojis container */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            {emojis.map(e => (
              <span
                key={e.id}
                className="absolute text-6xl select-none"
                style={{
                  transform: `translate(${e.x}px, ${e.y}px) rotate(${e.rotation}deg) scale(${e.scale})`,
                  opacity: e.opacity,
                  transition: 'none',
                }}
              >
                {e.emoji}
              </span>
            ))}
          </div>

          {/* Glow effect behind logo */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div
              className="w-80 h-80 rounded-full blur-3xl animate-pulse"
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
              className="drop-shadow-2xl"
              priority
            />
          </div>
        </div>
      </div>

      {/* Fun text */}
      <div className="absolute bottom-10 left-0 right-0 text-center">
        <p className="text-2xl font-bold text-primary-600 animate-bounce">
          Prediction Markets On Crack
        </p>
      </div>
    </div>
  )
}

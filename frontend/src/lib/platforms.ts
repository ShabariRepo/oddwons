// Platform branding configuration for OddWons

export const PLATFORMS = {
  kalshi: {
    name: 'Kalshi',
    color: '#00D26A',        // Kalshi green
    colorDark: '#00A855',
    colorLight: '#E6FFF2',
    logo: '/logos/kalshi-logo.png',
    logoWhite: '/logos/kalshi-logo-white.svg',
  },
  polymarket: {
    name: 'Polymarket',
    color: '#6366F1',        // Polymarket indigo
    colorDark: '#4F46E5',
    colorLight: '#EEF2FF',
    logo: '/logos/polymarket-logo.png',
    logoWhite: '/logos/polymarket-logo-white.svg',
  },
} as const

export type PlatformKey = keyof typeof PLATFORMS

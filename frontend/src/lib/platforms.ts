// Platform branding configuration for OddWons

export const PLATFORMS = {
  kalshi: {
    name: 'Kalshi',
    color: '#00D26A',        // Kalshi green
    colorDark: '#00A855',
    colorLight: '#E6FFF2',
    logo: '/logos/kalshi-logo.svg',
    logoWhite: '/logos/kalshi-logo-white.svg',
  },
  polymarket: {
    name: 'Polymarket',
    color: '#7C3AED',        // Polymarket purple
    colorDark: '#6D28D9',
    colorLight: '#EDE9FE',
    logo: '/logos/polymarket-logo.svg',
    logoWhite: '/logos/polymarket-logo-white.svg',
  },
} as const

export type PlatformKey = keyof typeof PLATFORMS

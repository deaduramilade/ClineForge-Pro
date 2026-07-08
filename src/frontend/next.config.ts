import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  experimental: {
    // Enable server actions (Next.js 14)
    serverActions: {
      allowedOrigins: ['localhost:3000'],
    },
  },
  // Support Arabic and English
  i18n: {
    locales: ['en', 'ar'],
    defaultLocale: 'en',
    localeDetection: true,
  },
}

export default nextConfig

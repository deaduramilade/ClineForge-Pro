const nextConfig = {
  experimental: {
    serverActions: {
      allowedOrigins: ['localhost:3000'],
    },
  },
  i18n: {
    locales: ['en', 'ar'],
    defaultLocale: 'en',
  },
}

export default nextConfig

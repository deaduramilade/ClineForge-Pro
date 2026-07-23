/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    // Enable server actions (Next.js 14)
    serverActions: {
      allowedOrigins: ['localhost:3000'],
    },
  },
}

export default nextConfig

/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  async rewrites() {
    return [
      { source: '/api/:path*', destination: 'http://localhost:8001/api/:path*' },
    ]
  },
}

export default nextConfig

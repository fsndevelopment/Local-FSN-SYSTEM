/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  // Disable loading indicators
  experimental: {
    optimizePackageImports: [],
  },
  // For Netlify deployment - regular Next.js
  images: {
    unoptimized: true,
  },
  // Remove rewrites for static export
  // async rewrites() {
  //   return [
  //     {
  //       source: '/api/v1/:path*',
  //       destination: 'http://localhost:8000/api/v1/:path*',
  //     },
  //     {
  //       source: '/health',
  //       destination: 'http://localhost:8000/health',
  //     },
  //   ]
  // },
}

export default nextConfig

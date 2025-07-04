import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Critical for Docker deployments
  output: 'standalone',
  
  // Remove conditional assetPrefix - keep it simple
  trailingSlash: false,
  
  // Optimize images for Docker
  images: {
    unoptimized: true,
    domains: ['localhost'],
  },

  // Webpack configuration
  webpack: (config, { dev, isServer }) => {
    // Only add alias if it doesn't exist
    if (!config.resolve.alias['@']) {
      config.resolve.alias['@'] = path.resolve(__dirname, 'src')
    }
    
    // Optimize for production
    if (!dev && !isServer) {
      config.optimization.splitChunks.cacheGroups = {
        ...config.optimization.splitChunks.cacheGroups,
        commons: {
          name: 'commons',
          chunks: 'initial',
          minChunks: 2,
          priority: 10
        }
      }
    }
    
    return config
  },

  // Add proper headers for static assets
  async headers() {
    return [
      {
        source: '/_next/static/(.*)',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
      {
        source: '/static/(.*)',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
    ]
  },

  // Performance optimizations
  experimental: {
    optimizePackageImports: ['lucide-react'],
  },

  // Security headers
  poweredByHeader: false,
  generateEtags: false,
}

export default nextConfig
/************************************
 * Next.js configuration
 ************************************/

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  // Using pages directory (traditional Next.js)
  
  // Static file handling
  trailingSlash: true,
  
  // API routes configuration
  async rewrites() {
    return [
      {
        source: '/api/vibe-coding',
        destination: '/api/vibe-coding',
      },
      {
        source: '/api/vibe-coding/status/:job_id',
        destination: '/api/status/:job_id',
      },
      {
        source: '/api/vibe-coding/files/:job_id',
        destination: '/api/files/:job_id',
      },
      {
        source: '/api/download/:job_id',
        destination: '/api/download/:job_id',
      }
    ]
  },

  // Handle static assets
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'Access-Control-Allow-Origin',
            value: '*',
          },
          {
            key: 'Access-Control-Allow-Methods',
            value: 'GET, POST, PUT, DELETE, OPTIONS',
          },
          {
            key: 'Access-Control-Allow-Headers',
            value: 'Content-Type, Authorization',
          },
        ],
      },
    ]
  },

  // Webpack configuration for handling static files
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.resolve.fallback = {
        fs: false,
        path: false,
        os: false,
      }
    }
    return config
  },

  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.VERCEL_URL 
      ? `https://${process.env.VERCEL_URL}` 
      : 'http://localhost:3000',
  },
}

module.exports = nextConfig
'use client'
import { VibeInput } from '@/components/vibe/VibeInput'

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900">
      <div className="container mx-auto py-12">
        <div className="text-center mb-12">
          <h1 className="text-6xl font-bold mb-6 bg-gradient-to-r from-purple-400 via-pink-400 to-blue-400 bg-clip-text text-transparent">
            Vibe Coding Platform
          </h1>
          <p className="text-2xl text-gray-300 mb-4">
            Describe your vibe, get a complete project
          </p>
          <p className="text-lg text-gray-400">
            Watch 5 AI agents collaborate to bring your vision to life
          </p>
        </div>
        <VibeInput />
      </div>
    </div>
  )
}
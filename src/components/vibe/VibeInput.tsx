'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { apiClient } from '@/lib/api/production-client'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Card } from '@/components/ui/card'
import { Loader2, Sparkles, Zap } from 'lucide-react'
import { motion } from 'framer-motion'

export function VibeInput() {
  const [vibe, setVibe] = useState('')
  const [isCreating, setIsCreating] = useState(false)
  const [error, setError] = useState('')
  const router = useRouter()

  const exampleVibes = [
    "Create a modern task manager with drag-and-drop, dark mode, and team collaboration",
    "Build a social media app with real-time chat, stories, and user profiles",
    "Design a landing page for a SaaS product with pricing tables and testimonials",
    "Develop a dashboard for analytics with charts, filters, and data visualization"
  ]

  const handleCreateProject = async () => {
    if (!vibe.trim()) return

    setIsCreating(true)
    setError('')

    try {
      console.log('🚀 Creating vibe project:', vibe)
      
      // Create job with real backend
      const job = await apiClient.createVibeJob(vibe, {
        projectType: 'web',
        complexity: 'simple'
      })

      console.log('✅ Job created:', job)
      
      // Navigate to generation page
      router.push(`/generate/${job.id}`)
      
    } catch (error: any) {
      console.error('❌ Failed to create job:', error)
      setError(error.message || 'Failed to create project')
    } finally {
      setIsCreating(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <Card className="p-8 bg-gradient-to-br from-purple-900/20 to-blue-900/20 border-purple-500/20 backdrop-blur-xl">
          <div className="text-center mb-8">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
              className="inline-block"
            >
              <Sparkles className="w-16 h-16 mx-auto mb-4 text-purple-400" />
            </motion.div>
            
            <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-400 via-pink-400 to-blue-400 bg-clip-text text-transparent mb-4">
              Describe Your Vibe
            </h1>
            
            <p className="text-xl text-gray-300 mb-2">
              Tell our AI agents what you want to build
            </p>
            
            <p className="text-gray-400">
              Watch 5 AI agents collaborate to bring your vision to life
            </p>
          </div>

          <div className="space-y-6">
            {/* Example buttons */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {exampleVibes.map((example, index) => (
                <motion.button
                  key={index}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setVibe(example)}
                  className="p-3 text-left text-sm bg-gray-800/50 hover:bg-gray-700/50 border border-gray-600/30 rounded-lg transition-all"
                >
                  <Zap className="w-4 h-4 inline mr-2 text-yellow-400" />
                  {example}
                </motion.button>
              ))}
            </div>

            {/* Main input */}
            <Textarea
              placeholder="I want to build a modern web application with..."
              value={vibe}
              onChange={(e) => setVibe(e.target.value)}
              className="min-h-32 bg-black/20 border-purple-500/30 text-white placeholder:text-gray-500 text-lg resize-none"
            />

            {/* Error message */}
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-4 bg-red-900/20 border border-red-500/30 rounded-lg text-red-300"
              >
                {error}
              </motion.div>
            )}

            {/* Submit button */}
            <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
              <Button
                onClick={handleCreateProject}
                disabled={!vibe.trim() || isCreating}
                className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-semibold py-4 text-lg"
                size="lg"
              >
                {isCreating ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    Creating Your Project...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-5 h-5 mr-2" />
                    Generate Project with AI Agents
                  </>
                )}
              </Button>
            </motion.div>
          </div>
        </Card>
      </motion.div>
    </div>
  )
}
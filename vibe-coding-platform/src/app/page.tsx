'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { Sparkles, ArrowRight, Zap, Code, Brain } from 'lucide-react'

export default function HomePage() {
  const router = useRouter()

  // Auto-redirect to vibe coding workspace after a brief intro
  useEffect(() => {
    const timer = setTimeout(() => {
      router.push('/vibe/create')
    }, 3000)

    return () => clearTimeout(timer)
  }, [router])

  const handleSkipIntro = () => {
    router.push('/vibe/create')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-pink-500/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse delay-2000"></div>
      </div>

      {/* Content */}
      <div className="relative z-10 text-center space-y-8 px-4">
        {/* Logo and Title */}
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1 }}
          className="space-y-6"
        >
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
            className="mx-auto w-24 h-24 bg-gradient-to-r from-purple-500 to-pink-500 rounded-2xl flex items-center justify-center shadow-2xl"
          >
            <Sparkles className="w-12 h-12 text-white" />
          </motion.div>

          <div className="space-y-4">
            <h1 className="text-6xl md:text-8xl font-bold bg-gradient-to-r from-purple-400 via-pink-400 to-cyan-400 bg-clip-text text-transparent">
              Vibe
            </h1>
            <h2 className="text-2xl md:text-3xl text-white font-light">
              Coding Platform
            </h2>
          </div>
        </motion.div>

        {/* Tagline */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.5 }}
          className="space-y-4"
        >
          <p className="text-xl md:text-2xl text-slate-300 max-w-3xl mx-auto leading-relaxed">
            Describe your <span className="text-purple-400 font-semibold">vibe</span>, 
            watch AI agents <span className="text-pink-400 font-semibold">collaborate</span> 
            to build your <span className="text-cyan-400 font-semibold">complete project</span>
          </p>
          <p className="text-lg text-slate-400">
            The future of coding is here
          </p>
        </motion.div>

        {/* Features */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 1 }}
          className="flex flex-wrap items-center justify-center gap-8 text-slate-300"
        >
          <div className="flex items-center space-x-2">
            <Brain className="w-5 h-5 text-purple-400" />
            <span>AI-Powered</span>
          </div>
          <div className="flex items-center space-x-2">
            <Zap className="w-5 h-5 text-yellow-400" />
            <span>Lightning Fast</span>
          </div>
          <div className="flex items-center space-x-2">
            <Code className="w-5 h-5 text-green-400" />
            <span>Production Ready</span>
          </div>
        </motion.div>

        {/* CTA Button */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 1.5 }}
          className="space-y-4"
        >
          <button
            onClick={handleSkipIntro}
            className="group px-8 py-4 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 rounded-2xl font-semibold text-white text-lg transition-all hover:scale-105 hover:shadow-2xl hover:shadow-purple-500/25"
          >
            <span className="flex items-center space-x-2">
              <span>Start Creating</span>
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </span>
          </button>
          
          <p className="text-sm text-slate-500">
            Starting automatically in <motion.span
              key={Math.floor(Date.now() / 1000)}
              initial={{ scale: 1.2, color: '#a855f7' }}
              animate={{ scale: 1, color: '#64748b' }}
              transition={{ duration: 1 }}
            >
              3
            </motion.span> seconds...
          </p>
        </motion.div>

        {/* Floating Elements */}
        <div className="absolute inset-0 pointer-events-none">
          {[...Array(20)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute w-2 h-2 bg-white/20 rounded-full"
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
              }}
              animate={{
                y: [0, -100, 0],
                opacity: [0, 1, 0],
                scale: [0, 1, 0],
              }}
              transition={{
                duration: Math.random() * 3 + 2,
                repeat: Infinity,
                delay: Math.random() * 2,
              }}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

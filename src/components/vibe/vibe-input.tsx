'use client'

import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Sparkles, 
  Wand2, 
  Brain, 
  Zap, 
  ArrowRight, 
  Lightbulb,
  Code,
  Palette,
  Globe,
  Smartphone,
  Database,
  Shield,
  CheckCircle2,
  Plus,
  X
} from 'lucide-react'
import { useVibeStore } from '@/stores/vibe-store'
import { useAgentStore } from '@/stores/agent-store'
import { 
  ProjectType, 
  ComplexityLevel, 
  VibeInputData, 
  ProjectPreferences,
  VibeExample 
} from '@/types'

interface VibeInputProps {
  onSubmit: (data: VibeInputData, preferences: ProjectPreferences) => void
  className?: string
}

const projectTypeIcons = {
  [ProjectType.WEB_APP]: Globe,
  [ProjectType.MOBILE_APP]: Smartphone,
  [ProjectType.API]: Database,
  [ProjectType.DESKTOP_APP]: Code,
  [ProjectType.CLI_TOOL]: Shield,
  [ProjectType.LIBRARY]: Plus,
  [ProjectType.MICROSERVICE]: Database,
  [ProjectType.FULLSTACK]: Globe,
}

const complexityColors = {
  [ComplexityLevel.SIMPLE]: 'text-green-400 border-green-400/30 bg-green-400/10',
  [ComplexityLevel.MODERATE]: 'text-blue-400 border-blue-400/30 bg-blue-400/10',
  [ComplexityLevel.COMPLEX]: 'text-orange-400 border-orange-400/30 bg-orange-400/10',
  [ComplexityLevel.ENTERPRISE]: 'text-purple-400 border-purple-400/30 bg-purple-400/10',
}

const vibeExamples: VibeExample[] = [
  {
    id: '1',
    title: 'Social Media Dashboard',
    description: 'A modern social media management dashboard with real-time analytics and post scheduling',
    category: ProjectType.WEB_APP,
    complexity: ComplexityLevel.COMPLEX,
    tags: ['React', 'Dashboard', 'Analytics', 'Real-time'],
  },
  {
    id: '2',
    title: 'Task Manager App',
    description: 'A minimalist task management application with drag-and-drop functionality and team collaboration',
    category: ProjectType.WEB_APP,
    complexity: ComplexityLevel.MODERATE,
    tags: ['Productivity', 'Collaboration', 'Drag & Drop'],
  },
  {
    id: '3',
    title: 'E-commerce API',
    description: 'A RESTful API for an e-commerce platform with payment processing and inventory management',
    category: ProjectType.API,
    complexity: ComplexityLevel.COMPLEX,
    tags: ['REST API', 'Payments', 'Inventory'],
  },
  {
    id: '4',
    title: 'Blog Platform',
    description: 'A clean and fast blog platform with markdown support and SEO optimization',
    category: ProjectType.WEB_APP,
    complexity: ComplexityLevel.SIMPLE,
    tags: ['Blog', 'Markdown', 'SEO'],
  },
]

export default function VibeInput({ onSubmit, className = '' }: VibeInputProps) {
  const { vibeInput, projectPreferences, setVibeInput, setProjectPreferences } = useVibeStore()
  const { initializeAgents } = useAgentStore()
  
  const [description, setDescription] = useState(vibeInput.description)
  const [isAdvanced, setIsAdvanced] = useState(false)
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [detectedType, setDetectedType] = useState<ProjectType | null>(null)
  const [customFeatures, setCustomFeatures] = useState<string[]>(vibeInput.features || [])
  const [newFeature, setNewFeature] = useState('')
  
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px'
    }
  }, [description])

  // AI-powered suggestions and type detection
  useEffect(() => {
    if (description.length > 10) {
      setIsAnalyzing(true)
      
      // Simulate AI analysis
      const timer = setTimeout(() => {
        // Simple keyword-based detection (in real app, this would be AI-powered)
        const lowercaseDesc = description.toLowerCase()
        
        if (lowercaseDesc.includes('api') || lowercaseDesc.includes('backend') || lowercaseDesc.includes('server')) {
          setDetectedType(ProjectType.API)
        } else if (lowercaseDesc.includes('mobile') || lowercaseDesc.includes('app') || lowercaseDesc.includes('ios') || lowercaseDesc.includes('android')) {
          setDetectedType(ProjectType.MOBILE_APP)
        } else if (lowercaseDesc.includes('web') || lowercaseDesc.includes('website') || lowercaseDesc.includes('dashboard')) {
          setDetectedType(ProjectType.WEB_APP)
        } else if (lowercaseDesc.includes('cli') || lowercaseDesc.includes('command') || lowercaseDesc.includes('terminal')) {
          setDetectedType(ProjectType.CLI_TOOL)
        } else {
          setDetectedType(ProjectType.WEB_APP) // Default
        }

        // Generate suggestions
        const newSuggestions = [
          'Add user authentication and authorization',
          'Include responsive design for mobile devices',
          'Implement real-time updates with WebSocket',
          'Add dark/light theme toggle',
          'Include comprehensive testing suite',
        ]
        setSuggestions(newSuggestions)
        setIsAnalyzing(false)
      }, 1000)

      return () => clearTimeout(timer)
    }
  }, [description])

  const handleSubmit = () => {
    if (!description.trim()) return

    const inputData: VibeInputData = {
      description: description.trim(),
      projectType: detectedType || vibeInput.projectType,
      complexity: vibeInput.complexity,
      languages: vibeInput.languages,
      frameworks: vibeInput.frameworks,
      features: customFeatures,
    }

    // Initialize agents for the new project
    initializeAgents()
    
    onSubmit(inputData, projectPreferences)
  }

  const addFeature = () => {
    if (newFeature.trim() && !customFeatures.includes(newFeature.trim())) {
      const updated = [...customFeatures, newFeature.trim()]
      setCustomFeatures(updated)
      setVibeInput({ features: updated })
      setNewFeature('')
    }
  }

  const removeFeature = (feature: string) => {
    const updated = customFeatures.filter(f => f !== feature)
    setCustomFeatures(updated)
    setVibeInput({ features: updated })
  }

  const applyExample = (example: VibeExample) => {
    setDescription(example.description)
    setDetectedType(example.category)
    setVibeInput({
      description: example.description,
      projectType: example.category,
      complexity: example.complexity,
    })
  }

  return (
    <div className={`w-full max-w-4xl mx-auto space-y-8 ${className}`}>
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center space-y-4"
      >
        <div className="flex items-center justify-center space-x-3">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            className="p-3 bg-gradient-to-r from-purple-500 to-pink-500 rounded-2xl"
          >
            <Sparkles className="w-8 h-8 text-white" />
          </motion.div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
            Describe Your Vibe
          </h1>
        </div>
        <p className="text-lg text-slate-400 max-w-2xl mx-auto">
          Tell us what you want to build in natural language. Our AI agents will collaborate to bring your vision to life.
        </p>
      </motion.div>

      {/* Examples */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="space-y-4"
      >
        <h3 className="text-lg font-semibold text-white flex items-center space-x-2">
          <Lightbulb className="w-5 h-5 text-yellow-400" />
          <span>Quick Start Examples</span>
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {vibeExamples.map((example, index) => {
            const Icon = projectTypeIcons[example.category]
            return (
              <motion.button
                key={example.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 + index * 0.1 }}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => applyExample(example)}
                className="p-4 bg-slate-800/50 border border-slate-700/50 rounded-xl text-left hover:border-purple-500/50 transition-all group"
              >
                <div className="flex items-start space-x-3">
                  <div className="p-2 bg-purple-500/20 rounded-lg group-hover:bg-purple-500/30 transition-colors">
                    <Icon className="w-5 h-5 text-purple-400" />
                  </div>
                  <div className="flex-1 space-y-2">
                    <h4 className="font-semibold text-white group-hover:text-purple-400 transition-colors">
                      {example.title}
                    </h4>
                    <p className="text-sm text-slate-400 line-clamp-2">
                      {example.description}
                    </p>
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 text-xs rounded-full border ${complexityColors[example.complexity]}`}>
                        {example.complexity}
                      </span>
                      <div className="flex space-x-1">
                        {example.tags.slice(0, 3).map((tag) => (
                          <span key={tag} className="px-2 py-1 text-xs bg-slate-700/50 text-slate-300 rounded-full">
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </motion.button>
            )
          })}
        </div>
      </motion.div>

      {/* Main Input */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="space-y-6"
      >
        <div className="relative">
          <textarea
            ref={textareaRef}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe your project idea... (e.g., 'I want to build a social media dashboard with real-time analytics, dark mode, and user authentication')"
            className="w-full min-h-[120px] p-6 bg-slate-900/50 border border-slate-700/50 rounded-2xl text-white placeholder-slate-400 focus:border-purple-500/50 focus:ring-2 focus:ring-purple-500/20 focus:outline-none resize-none transition-all"
            rows={3}
          />
          
          {/* AI Analysis Indicator */}
          <AnimatePresence>
            {isAnalyzing && (
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                className="absolute top-4 right-4 flex items-center space-x-2 px-3 py-2 bg-purple-500/20 border border-purple-500/30 rounded-lg"
              >
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                >
                  <Brain className="w-4 h-4 text-purple-400" />
                </motion.div>
                <span className="text-sm text-purple-400">Analyzing...</span>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Detected Type */}
          <AnimatePresence>
            {detectedType && !isAnalyzing && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                className="absolute bottom-4 right-4 flex items-center space-x-2 px-3 py-2 bg-green-500/20 border border-green-500/30 rounded-lg"
              >
                <CheckCircle2 className="w-4 h-4 text-green-400" />
                <span className="text-sm text-green-400">
                  Detected: {detectedType.replace('_', ' ')}
                </span>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* AI Suggestions */}
        <AnimatePresence>
          {suggestions.length > 0 && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="space-y-3"
            >
              <h4 className="text-sm font-semibold text-white flex items-center space-x-2">
                <Wand2 className="w-4 h-4 text-purple-400" />
                <span>AI Suggestions</span>
              </h4>
              <div className="space-y-2">
                {suggestions.map((suggestion, index) => (
                  <motion.button
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    onClick={() => {
                      if (!customFeatures.includes(suggestion)) {
                        const updated = [...customFeatures, suggestion]
                        setCustomFeatures(updated)
                        setVibeInput({ features: updated })
                      }
                    }}
                    className="w-full p-3 bg-slate-800/30 border border-slate-700/30 rounded-lg text-left hover:border-purple-500/50 hover:bg-slate-800/50 transition-all text-sm text-slate-300 hover:text-white"
                  >
                    <div className="flex items-center space-x-2">
                      <Plus className="w-4 h-4 text-purple-400" />
                      <span>{suggestion}</span>
                    </div>
                  </motion.button>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Custom Features */}
        <div className="space-y-4">
          <h4 className="text-sm font-semibold text-white">Features & Requirements</h4>
          
          {/* Add Feature Input */}
          <div className="flex space-x-2">
            <input
              type="text"
              value={newFeature}
              onChange={(e) => setNewFeature(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && addFeature()}
              placeholder="Add a custom feature..."
              className="flex-1 px-4 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-white placeholder-slate-400 focus:border-purple-500/50 focus:outline-none"
            />
            <button
              onClick={addFeature}
              disabled={!newFeature.trim()}
              className="px-4 py-2 bg-purple-500 hover:bg-purple-600 disabled:bg-slate-700 disabled:cursor-not-allowed rounded-lg transition-colors"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>

          {/* Feature Tags */}
          {customFeatures.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {customFeatures.map((feature) => (
                <motion.div
                  key={feature}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="flex items-center space-x-2 px-3 py-2 bg-purple-500/20 border border-purple-500/30 rounded-lg"
                >
                  <span className="text-sm text-purple-300">{feature}</span>
                  <button
                    onClick={() => removeFeature(feature)}
                    className="text-purple-400 hover:text-purple-300 transition-colors"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </motion.div>
              ))}
            </div>
          )}
        </div>

        {/* Advanced Options Toggle */}
        <button
          onClick={() => setIsAdvanced(!isAdvanced)}
          className="flex items-center space-x-2 text-sm text-purple-400 hover:text-purple-300 transition-colors"
        >
          <Palette className="w-4 h-4" />
          <span>{isAdvanced ? 'Hide' : 'Show'} Advanced Options</span>
        </button>

        {/* Advanced Options */}
        <AnimatePresence>
          {isAdvanced && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="space-y-6 p-6 bg-slate-900/30 border border-slate-700/30 rounded-xl"
            >
              {/* Project Type */}
              <div className="space-y-3">
                <label className="text-sm font-semibold text-white">Project Type</label>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {Object.values(ProjectType).map((type) => {
                    const Icon = projectTypeIcons[type]
                    const isSelected = (detectedType || vibeInput.projectType) === type
                    return (
                      <button
                        key={type}
                        onClick={() => {
                          setDetectedType(type)
                          setVibeInput({ projectType: type })
                        }}
                        className={`p-3 border rounded-lg transition-all ${
                          isSelected
                            ? 'border-purple-500 bg-purple-500/20 text-purple-300'
                            : 'border-slate-700 hover:border-slate-600 text-slate-400 hover:text-slate-300'
                        }`}
                      >
                        <Icon className="w-5 h-5 mx-auto mb-2" />
                        <div className="text-xs font-medium">
                          {type.replace('_', ' ')}
                        </div>
                      </button>
                    )
                  })}
                </div>
              </div>

              {/* Complexity */}
              <div className="space-y-3">
                <label className="text-sm font-semibold text-white">Complexity Level</label>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {Object.values(ComplexityLevel).map((level) => {
                    const isSelected = vibeInput.complexity === level
                    return (
                      <button
                        key={level}
                        onClick={() => setVibeInput({ complexity: level })}
                        className={`p-3 border rounded-lg transition-all ${
                          isSelected
                            ? complexityColors[level]
                            : 'border-slate-700 hover:border-slate-600 text-slate-400 hover:text-slate-300'
                        }`}
                      >
                        <div className="text-sm font-medium capitalize">
                          {level}
                        </div>
                      </button>
                    )
                  })}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Generate Button */}
        <motion.button
          onClick={handleSubmit}
          disabled={!description.trim()}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="w-full p-4 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 disabled:from-slate-700 disabled:to-slate-700 disabled:cursor-not-allowed rounded-xl font-semibold text-white transition-all flex items-center justify-center space-x-3"
        >
          <Zap className="w-5 h-5" />
          <span>Generate Project</span>
          <ArrowRight className="w-5 h-5" />
        </motion.button>
      </motion.div>
    </div>
  )
}
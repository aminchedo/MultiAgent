'use client'
import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { useJobStore } from '@/stores/job-store'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Code, 
  FileText, 
  TestTube, 
  BookOpen, 
  CheckCircle, 
  Download,
  Loader2,
  Sparkles
} from 'lucide-react'

const agents = [
  {
    id: 'planner',
    name: 'Project Planner',
    icon: FileText,
    color: 'text-blue-400',
    bgColor: 'bg-blue-400/10',
    description: 'Analyzing requirements and creating project structure'
  },
  {
    id: 'code_generator',
    name: 'Code Generator',
    icon: Code,
    color: 'text-green-400',
    bgColor: 'bg-green-400/10',
    description: 'Generating React components and application logic'
  },
  {
    id: 'tester',
    name: 'Test Engineer',
    icon: TestTube,
    color: 'text-yellow-400',
    bgColor: 'bg-yellow-400/10',
    description: 'Creating unit tests and integration tests'
  },
  {
    id: 'doc_generator',
    name: 'Documentation Writer',
    icon: BookOpen,
    color: 'text-purple-400',
    bgColor: 'bg-purple-400/10',
    description: 'Writing documentation and README files'
  },
  {
    id: 'reviewer',
    name: 'Code Reviewer',
    icon: CheckCircle,
    color: 'text-pink-400',
    bgColor: 'bg-pink-400/10',
    description: 'Reviewing code quality and optimization'
  }
]

export default function GenerationPage() {
  const params = useParams() as { jobId?: string }
  const jobId = (params?.jobId || '') as string
  const { 
    currentJob, 
    agentProgress, 
    files, 
    isLoading, 
    error,
    fetchJobStatus,
    startPolling,
    stopPolling,
    downloadProject
  } = useJobStore()
  
  const [isDownloading, setIsDownloading] = useState(false)

  useEffect(() => {
    if (jobId) {
      // Initial fetch
      fetchJobStatus(jobId)
      
      // Start polling
      startPolling(jobId)
      
      // Cleanup on unmount
      return () => stopPolling()
    }
  }, [jobId, fetchJobStatus, startPolling, stopPolling])

  const handleDownload = async () => {
    if (!jobId) return
    
    setIsDownloading(true)
    try {
      const blob = await downloadProject(jobId)
      
      // Create download link
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `vibe-project-${jobId}.zip`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Download failed:', error)
    } finally {
      setIsDownloading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin mx-auto mb-4 text-purple-400" />
          <p className="text-gray-300">Loading project...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="p-6 bg-red-900/20 border border-red-500/30 rounded-lg">
            <p className="text-red-300 mb-4">Error: {error}</p>
            <button 
              onClick={() => window.history.back()}
              className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700"
            >
              Go Back
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (!currentJob) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin mx-auto mb-4 text-purple-400" />
          <p className="text-gray-300">Loading project details...</p>
        </div>
      </div>
    )
  }

  const isCompleted = currentJob.status === 'completed'
  const currentAgent = agents.find(agent => agent.id === currentJob.current_agent)

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900">
      <div className="max-w-6xl mx-auto p-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
            className="inline-block mb-4"
          >
            <Sparkles className="w-12 h-12 text-purple-400" />
          </motion.div>
          
          <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent mb-2">
            AI Agents at Work
          </h1>
          
          <p className="text-gray-300 mb-4">
            {currentJob.description}
          </p>
          
          {/* Progress Bar */}
          <div className="w-full bg-gray-800 rounded-full h-3 mb-4">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${currentJob.progress || 0}%` }}
              transition={{ duration: 0.5 }}
              className="bg-gradient-to-r from-purple-500 to-blue-500 h-3 rounded-full"
            />
          </div>
          
          <p className="text-sm text-gray-400">
            {currentJob.progress || 0}% Complete
          </p>
        </motion.div>

        {/* Current Agent Status */}
        {currentAgent && !isCompleted && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="mb-8"
          >
            <div className={`p-6 rounded-2xl ${currentAgent.bgColor} border border-purple-500/20`}>
              <div className="flex items-center mb-4">
                <currentAgent.icon className={`w-8 h-8 mr-3 ${currentAgent.color}`} />
                <div>
                  <h3 className="text-xl font-semibold text-white">
                    {currentAgent.name} is working...
                  </h3>
                  <p className="text-gray-300">{currentAgent.description}</p>
                </div>
                <Loader2 className="w-6 h-6 animate-spin ml-auto text-purple-400" />
              </div>
            </div>
          </motion.div>
        )}

        {/* Agent Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {agents.map((agent, index) => {
            const progress = agentProgress[agent.id]
            const isActive = currentJob.current_agent === agent.id
            const isDone = currentJob.progress >= (index + 1) * 20
            
            return (
              <motion.div
                key={agent.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className={`p-6 rounded-2xl border transition-all ${
                  isActive 
                    ? `${agent.bgColor} border-purple-500/50` 
                    : isDone 
                    ? 'bg-green-900/20 border-green-500/30' 
                    : 'bg-gray-800/50 border-gray-600/30'
                }`}
              >
                <div className="flex items-center mb-4">
                  <agent.icon className={`w-8 h-8 mr-3 ${
                    isDone ? 'text-green-400' : isActive ? agent.color : 'text-gray-500'
                  }`} />
                  <div className="flex-1">
                    <h3 className="font-semibold text-white">{agent.name}</h3>
                    <p className="text-sm text-gray-400">{agent.description}</p>
                  </div>
                  {isActive && <Loader2 className="w-5 h-5 animate-spin text-purple-400" />}
                  {isDone && <CheckCircle className="w-5 h-5 text-green-400" />}
                </div>
                
                {isActive && (
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: '100%' }}
                      transition={{ duration: 2, repeat: Infinity }}
                      className="bg-gradient-to-r from-purple-500 to-blue-500 h-2 rounded-full"
                    />
                  </div>
                )}
              </motion.div>
            )
          })}
        </div>

        {/* Generated Files */}
        {files.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8"
          >
            <h2 className="text-2xl font-bold text-white mb-4">Generated Files</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {files.map((file, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: index * 0.1 }}
                  className="p-4 bg-gray-800/50 border border-gray-600/30 rounded-lg"
                >
                  <div className="flex items-center mb-2">
                    <Code className="w-5 h-5 text-blue-400 mr-2" />
                    <span className="text-sm text-gray-300 font-mono">{file.path}</span>
                  </div>
                  <div className="text-xs text-gray-500">
                    {file.language} • {file.size} bytes • Created by {file.created_by}
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Download Button */}
        {isCompleted && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center"
          >
            <button
              onClick={handleDownload}
              disabled={isDownloading}
              className="px-8 py-4 bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700 text-white font-semibold rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {isDownloading ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin inline" />
                  Downloading...
                </>
              ) : (
                <>
                  <Download className="w-5 h-5 mr-2 inline" />
                  Download Project
                </>
              )}
            </button>
            <p className="text-sm text-gray-400 mt-2">
              Get your complete React project as a ZIP file
            </p>
          </motion.div>
        )}
      </div>
    </div>
  )
}
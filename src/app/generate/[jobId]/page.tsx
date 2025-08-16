'use client'
import { useParams } from 'next/navigation'
import { useEffect, useState } from 'react'
import { useEnhancedWebSocket } from '@/hooks/use-enhanced-websocket'
import { useJobStore } from '@/stores/job-store'
import { AgentOrchestra } from '@/components/agents/agent-orchestra'
import { FileExplorer } from '@/components/files/FileExplorer'
import { CodePreview } from '@/components/files/CodePreview'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { 
  Download, 
  ExternalLink, 
  RefreshCw, 
  CheckCircle2, 
  AlertCircle,
  Clock
} from 'lucide-react'

export default function EnhancedGeneratePage() {
  const { jobId } = useParams<{ jobId: string }>()
  const [selectedFile, setSelectedFile] = useState<any>(null)
  
  const { 
    isConnected, 
    lastMessage, 
    connectionAttempts, 
    reconnect 
  } = useEnhancedWebSocket(jobId)
  
  const { 
    currentJob, 
    agentProgress, 
    files, 
    jobStatus 
  } = useJobStore()

  const getOverallProgress = () => {
    const agents = ['planner', 'code_generator', 'tester', 'doc_generator', 'reviewer']
    const totalProgress = agents.reduce((sum, agent) => {
      return sum + (agentProgress[agent]?.progress || 0)
    }, 0)
    return Math.round(totalProgress / agents.length)
  }

  const getStatusIcon = () => {
    switch (jobStatus) {
      case 'completed':
        return <CheckCircle2 className="w-5 h-5 text-green-400" />
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-red-400" />
      case 'running':
        return <RefreshCw className="w-5 h-5 text-blue-400 animate-spin" />
      default:
        return <Clock className="w-5 h-5 text-yellow-400" />
    }
  }

  const deployToVercel = async () => {
    try {
      // Implementation for Vercel deployment
      console.log('Deploying to Vercel...')
      alert('Deployment feature coming soon!')
    } catch (error) {
      console.error('Deployment failed:', error)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-purple-900/20 to-black">
      <div className="container mx-auto p-6">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">
                🎨 Vibe Coding in Progress
              </h1>
              <p className="text-gray-400">
                Job ID: {jobId}
              </p>
            </div>
            
            <div className="flex items-center gap-4">
              <Badge variant={isConnected ? 'default' : 'destructive'}>
                {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
              </Badge>
              
              <div className="flex items-center gap-2">
                {getStatusIcon()}
                <Badge variant="outline">
                  {jobStatus || 'pending'}
                </Badge>
              </div>
            </div>
          </div>
          
          {/* Overall Progress */}
          <Card className="p-4 bg-gray-900/50 border-gray-700">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-white">Overall Progress</span>
              <span className="text-sm text-gray-400">{getOverallProgress()}%</span>
            </div>
            <Progress value={getOverallProgress()} className="h-2" />
          </Card>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Agent Orchestra */}
          <div className="lg:col-span-3">
            <AgentOrchestra />
          </div>
          
          {/* File Explorer */}
          <div className="lg:col-span-1">
            <FileExplorer
              jobId={jobId}
              files={files}
              onFileSelect={setSelectedFile}
              selectedFile={selectedFile}
            />
          </div>
          
          {/* Code Preview */}
          <div className="lg:col-span-2">
            <CodePreview file={selectedFile} jobId={jobId} />
          </div>
        </div>

        {/* Actions */}
        {jobStatus === 'completed' && files.length > 0 && (
          <Card className="p-6 bg-gradient-to-r from-green-900/20 to-blue-900/20 border-green-500/20">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xl font-bold text-white mb-2">
                  🎉 Project Generated Successfully!
                </h3>
                <p className="text-gray-400">
                  Your project is ready with {files.length} files
                </p>
              </div>
              
              <div className="flex gap-3">
                <Button variant="outline" onClick={deployToVercel}>
                  <ExternalLink className="w-4 h-4 mr-2" />
                  Deploy to Vercel
                </Button>
                
                <Button>
                  <Download className="w-4 h-4 mr-2" />
                  Download Project
                </Button>
              </div>
            </div>
          </Card>
        )}

        {/* Connection Issues */}
        {!isConnected && connectionAttempts > 0 && (
          <Card className="p-4 bg-red-900/20 border-red-500/20">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-red-400" />
                <span className="text-red-300">
                  Connection lost. Attempting to reconnect... ({connectionAttempts}/5)
                </span>
              </div>
              
              <Button size="sm" variant="outline" onClick={reconnect}>
                <RefreshCw className="w-4 h-4 mr-2" />
                Retry
              </Button>
            </div>
          </Card>
        )}
      </div>
    </div>
  )
}
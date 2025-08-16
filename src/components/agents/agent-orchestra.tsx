'use client'
import { useJobStore } from '@/stores/job-store'
import { AgentCard } from './AgentCard'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { 
  Brain, 
  Code, 
  TestTube, 
  FileText, 
  Eye,
  Sparkles
} from 'lucide-react'

const agentConfig = {
  planner: {
    name: 'Project Planner',
    description: 'Architecting the project structure',
    icon: Brain,
    color: 'text-blue-400',
    bgColor: 'bg-blue-400/10'
  },
  code_generator: {
    name: 'Code Generator',
    description: 'Writing production-ready code',
    icon: Code,
    color: 'text-green-400',
    bgColor: 'bg-green-400/10'
  },
  tester: {
    name: 'Quality Tester',
    description: 'Ensuring code quality & testing',
    icon: TestTube,
    color: 'text-purple-400',
    bgColor: 'bg-purple-400/10'
  },
  doc_generator: {
    name: 'Documentation',
    description: 'Creating comprehensive docs',
    icon: FileText,
    color: 'text-orange-400',
    bgColor: 'bg-orange-400/10'
  },
  reviewer: {
    name: 'Code Reviewer',
    description: 'Final review & optimization',
    icon: Eye,
    color: 'text-red-400',
    bgColor: 'bg-red-400/10'
  }
}

export function AgentOrchestra() {
  const { agentProgress } = useJobStore()

  const getOverallStatus = () => {
    const agents = Object.keys(agentConfig)
    const completed = agents.filter(agent => 
      agentProgress[agent]?.status === 'completed'
    ).length
    
    if (completed === agents.length) return 'completed'
    if (completed > 0) return 'running'
    return 'pending'
  }

  const getOverallProgress = () => {
    const agents = Object.keys(agentConfig)
    const totalProgress = agents.reduce((sum, agent) => {
      return sum + (agentProgress[agent]?.progress || 0)
    }, 0)
    return Math.round(totalProgress / agents.length)
  }

  const status = getOverallStatus()
  const progress = getOverallProgress()

  return (
    <Card className="p-6 bg-gray-900/50 border-gray-700">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-500/20 rounded-lg">
            <Sparkles className="w-6 h-6 text-purple-400" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">AI Agent Orchestra</h2>
            <p className="text-gray-400 text-sm">
              Collaborative AI agents working together
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <Badge 
            variant={status === 'completed' ? 'default' : status === 'running' ? 'secondary' : 'outline'}
            className="text-sm"
          >
            {status === 'completed' ? '🎉 Complete' : 
             status === 'running' ? '⚡ Running' : '⏳ Pending'}
          </Badge>
          
          <div className="text-right">
            <div className="text-sm font-medium text-white">{progress}%</div>
            <div className="text-xs text-gray-400">Overall Progress</div>
          </div>
        </div>
      </div>

      {/* Agent Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {Object.entries(agentConfig).map(([agentType, config]) => {
          const progress = agentProgress[agentType]
          const Icon = config.icon
          
          return (
            <div
              key={agentType}
              className={`p-4 rounded-lg border transition-all duration-300 ${
                progress?.status === 'completed' 
                  ? 'bg-green-500/10 border-green-500/30' 
                  : progress?.status === 'running'
                  ? 'bg-blue-500/10 border-blue-500/30'
                  : 'bg-gray-800/50 border-gray-600'
              }`}
            >
              <div className="flex items-center gap-3 mb-3">
                <div className={`p-2 rounded-lg ${config.bgColor}`}>
                  <Icon className={`w-5 h-5 ${config.color}`} />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-white text-sm">
                    {config.name}
                  </h3>
                  <p className="text-gray-400 text-xs">
                    {config.description}
                  </p>
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-400">Progress</span>
                  <span className="text-white font-medium">
                    {progress?.progress || 0}%
                  </span>
                </div>
                
                <div className="w-full bg-gray-700 rounded-full h-1.5">
                  <div 
                    className={`h-1.5 rounded-full transition-all duration-500 ${
                      progress?.status === 'completed' 
                        ? 'bg-green-500' 
                        : progress?.status === 'running'
                        ? 'bg-blue-500'
                        : 'bg-gray-600'
                    }`}
                    style={{ width: `${progress?.progress || 0}%` }}
                  />
                </div>
                
                <div className="text-xs text-gray-400">
                  {progress?.currentTask || progress?.status || 'Waiting...'}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Agent Messages */}
      <div className="mt-6 p-4 bg-gray-800/30 rounded-lg">
        <h4 className="text-sm font-medium text-white mb-3">Recent Activity</h4>
        <div className="space-y-2 max-h-32 overflow-y-auto">
          {Object.entries(agentProgress).map(([agentType, progress]) => 
            progress?.messages?.slice(-1).map((message, index) => (
              <div key={`${agentType}-${index}`} className="flex items-start gap-2 text-xs">
                <span className={`font-medium ${agentConfig[agentType as keyof typeof agentConfig]?.color}`}>
                  {agentConfig[agentType as keyof typeof agentConfig]?.name}:
                </span>
                <span className="text-gray-300">{message}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </Card>
  )
}
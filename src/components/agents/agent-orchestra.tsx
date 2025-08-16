'use client'

import React, { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Brain, 
  Code, 
  TestTube, 
  FileText, 
  Shield, 
  Zap, 
  MessageCircle, 
  CheckCircle, 
  AlertCircle, 
  Clock,
  Activity,
  ArrowRight,
  Sparkles
} from 'lucide-react'
import { useAgentStore, useAgents, useAgentProgress, useActivePhase } from '@/stores/agent-store'
import { Agent, AgentType, AgentStatus, AgentProgress } from '@/types'

interface AgentOrchestraProps {
  className?: string
  showDetails?: boolean
}

const agentIcons = {
  [AgentType.PLANNER]: Brain,
  [AgentType.CODE_GENERATOR]: Code,
  [AgentType.TESTER]: TestTube,
  [AgentType.DOC_GENERATOR]: FileText,
  [AgentType.REVIEWER]: Shield,
}

const agentColors = {
  [AgentType.PLANNER]: 'from-blue-500 to-cyan-500',
  [AgentType.CODE_GENERATOR]: 'from-green-500 to-emerald-500',
  [AgentType.TESTER]: 'from-orange-500 to-yellow-500',
  [AgentType.DOC_GENERATOR]: 'from-purple-500 to-violet-500',
  [AgentType.REVIEWER]: 'from-red-500 to-pink-500',
}

const statusColors = {
  [AgentStatus.IDLE]: 'text-slate-400 border-slate-700',
  [AgentStatus.WORKING]: 'text-green-400 border-green-500 shadow-green-500/20',
  [AgentStatus.COMPLETED]: 'text-blue-400 border-blue-500 shadow-blue-500/20',
  [AgentStatus.ERROR]: 'text-red-400 border-red-500 shadow-red-500/20',
  [AgentStatus.PAUSED]: 'text-yellow-400 border-yellow-500 shadow-yellow-500/20',
}

const phaseDescriptions = {
  planning: 'Analyzing requirements and designing architecture',
  coding: 'Generating high-quality code and components',
  testing: 'Creating comprehensive tests and quality assurance',
  documenting: 'Writing documentation and user guides',
  reviewing: 'Final review and optimization',
  idle: 'Waiting for next task...',
}

export default function AgentOrchestra({ className = '', showDetails = true }: AgentOrchestraProps) {
  const agents = useAgents()
  const agentProgress = useAgentProgress()
  const activePhase = useActivePhase()
  const { selectedAgent, setSelectedAgent, addAgentLog, addCollaboration } = useAgentStore()
  
  const [collaborationLines, setCollaborationLines] = useState<Array<{
    from: string
    to: string
    id: string
    timestamp: number
  }>>([])

  // Simulate agent collaboration
  useEffect(() => {
    if (activePhase === 'idle') return

    const interval = setInterval(() => {
      const workingAgents = agents.filter(a => a.status === AgentStatus.WORKING)
      if (workingAgents.length >= 2) {
        const from = workingAgents[Math.floor(Math.random() * workingAgents.length)]
        const to = workingAgents.find(a => a.id !== from.id)
        
        if (to) {
          const collaborationId = `collab-${Date.now()}`
          setCollaborationLines(prev => [
            ...prev.slice(-4), // Keep last 5 lines
            {
              from: from.id,
              to: to.id,
              id: collaborationId,
              timestamp: Date.now(),
            }
          ])

          // Add collaboration to store
          addCollaboration({
            fromAgent: from.id,
            toAgent: to.id,
            message: `${from.name} collaborating with ${to.name}`,
            type: 'notification',
            data: { phase: activePhase },
          })

          // Remove line after animation
          setTimeout(() => {
            setCollaborationLines(prev => prev.filter(line => line.id !== collaborationId))
          }, 2000)
        }
      }
    }, 3000)

    return () => clearInterval(interval)
  }, [agents, activePhase, addCollaboration])

  // Simulate progress updates
  useEffect(() => {
    if (activePhase === 'idle') return

    const interval = setInterval(() => {
      agents.forEach(agent => {
        if (agent.status === AgentStatus.WORKING && Math.random() > 0.7) {
          addAgentLog({
            agentId: agent.id,
            message: getRandomLogMessage(agent.type, activePhase),
            level: 'info',
            metadata: { phase: activePhase },
          })
        }
      })
    }, 2000)

    return () => clearInterval(interval)
  }, [agents, activePhase, addAgentLog])

  const getRandomLogMessage = (agentType: AgentType, phase: string): string => {
    const messages = {
      [AgentType.PLANNER]: [
        'Analyzing project requirements...',
        'Designing system architecture...',
        'Planning component structure...',
        'Optimizing data flow...',
      ],
      [AgentType.CODE_GENERATOR]: [
        'Generating React components...',
        'Creating API endpoints...',
        'Implementing business logic...',
        'Optimizing code structure...',
      ],
      [AgentType.TESTER]: [
        'Writing unit tests...',
        'Creating integration tests...',
        'Running test suites...',
        'Validating edge cases...',
      ],
      [AgentType.DOC_GENERATOR]: [
        'Writing README documentation...',
        'Creating API documentation...',
        'Generating code comments...',
        'Preparing user guides...',
      ],
      [AgentType.REVIEWER]: [
        'Reviewing code quality...',
        'Checking best practices...',
        'Validating security measures...',
        'Optimizing performance...',
      ],
    }
    
    const agentMessages = messages[agentType]
    return agentMessages[Math.floor(Math.random() * agentMessages.length)]
  }

  const getAgentPosition = (index: number, total: number) => {
    const angle = (index * 2 * Math.PI) / total
    const radius = 120
    const centerX = 150
    const centerY = 150
    
    return {
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
    }
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Phase Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center space-y-2"
      >
        <div className="flex items-center justify-center space-x-2">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
            className="p-2 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg"
          >
            <Activity className="w-5 h-5 text-white" />
          </motion.div>
          <h2 className="text-2xl font-bold text-white">Agent Orchestra</h2>
        </div>
        <p className="text-slate-400 capitalize">
          {phaseDescriptions[activePhase as keyof typeof phaseDescriptions]}
        </p>
      </motion.div>

      {/* Central Orchestra Visualization */}
      <div className="relative w-full h-80 bg-slate-900/30 border border-slate-700/30 rounded-2xl overflow-hidden">
        {/* Background Grid */}
        <div className="absolute inset-0 opacity-10">
          <svg width="100%" height="100%">
            <defs>
              <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
                <path d="M 20 0 L 0 0 0 20" fill="none" stroke="currentColor" strokeWidth="1"/>
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
          </svg>
        </div>

        {/* Central Hub */}
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2"
        >
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
            className="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center shadow-lg"
          >
            <Sparkles className="w-8 h-8 text-white" />
          </motion.div>
        </motion.div>

        {/* Agents */}
        {agents.map((agent, index) => {
          const position = getAgentPosition(index, agents.length)
          const Icon = agentIcons[agent.type]
          const progress = agentProgress[agent.id]
          
          return (
            <motion.div
              key={agent.id}
              initial={{ opacity: 0, scale: 0 }}
              animate={{ 
                opacity: 1, 
                scale: 1,
                x: position.x - 30,
                y: position.y - 30,
              }}
              transition={{ delay: index * 0.1 }}
              className="absolute w-16 h-16 cursor-pointer group"
              onClick={() => setSelectedAgent(selectedAgent === agent.id ? null : agent.id)}
            >
              {/* Agent Avatar */}
              <motion.div
                animate={{
                  scale: agent.status === AgentStatus.WORKING ? [1, 1.1, 1] : 1,
                  rotate: agent.status === AgentStatus.WORKING ? [0, 5, -5, 0] : 0,
                }}
                transition={{
                  duration: 2,
                  repeat: agent.status === AgentStatus.WORKING ? Infinity : 0,
                }}
                className={`w-16 h-16 rounded-full border-2 flex items-center justify-center relative overflow-hidden ${statusColors[agent.status]}`}
              >
                {/* Background Gradient */}
                <div className={`absolute inset-0 bg-gradient-to-br ${agentColors[agent.type]} opacity-20`} />
                
                {/* Icon */}
                <Icon className="w-6 h-6 relative z-10" />
                
                {/* Progress Ring */}
                {agent.status === AgentStatus.WORKING && (
                  <motion.svg
                    className="absolute inset-0 w-full h-full transform -rotate-90"
                    initial={{ pathLength: 0 }}
                    animate={{ pathLength: agent.progress / 100 }}
                    transition={{ duration: 0.5 }}
                  >
                    <circle
                      cx="32"
                      cy="32"
                      r="30"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      pathLength="1"
                    />
                  </motion.svg>
                )}

                {/* Status Indicator */}
                <div className="absolute -top-1 -right-1">
                  {agent.status === AgentStatus.WORKING && (
                    <motion.div
                      animate={{ scale: [1, 1.2, 1] }}
                      transition={{ duration: 1, repeat: Infinity }}
                      className="w-4 h-4 bg-green-500 rounded-full"
                    />
                  )}
                  {agent.status === AgentStatus.COMPLETED && (
                    <div className="w-4 h-4 bg-blue-500 rounded-full flex items-center justify-center">
                      <CheckCircle className="w-3 h-3 text-white" />
                    </div>
                  )}
                  {agent.status === AgentStatus.ERROR && (
                    <div className="w-4 h-4 bg-red-500 rounded-full flex items-center justify-center">
                      <AlertCircle className="w-3 h-3 text-white" />
                    </div>
                  )}
                </div>
              </motion.div>

              {/* Agent Label */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="absolute -bottom-6 left-1/2 transform -translate-x-1/2 text-xs text-center"
              >
                <div className="bg-slate-800/90 px-2 py-1 rounded-md whitespace-nowrap">
                  <div className="font-medium text-white">{agent.name}</div>
                  {progress && (
                    <div className="text-slate-400 text-xs">
                      {progress.progress}%
                    </div>
                  )}
                </div>
              </motion.div>
            </motion.div>
          )
        })}

        {/* Collaboration Lines */}
        <AnimatePresence>
          {collaborationLines.map((line) => {
            const fromAgent = agents.find(a => a.id === line.from)
            const toAgent = agents.find(a => a.id === line.to)
            
            if (!fromAgent || !toAgent) return null
            
            const fromPos = getAgentPosition(agents.indexOf(fromAgent), agents.length)
            const toPos = getAgentPosition(agents.indexOf(toAgent), agents.length)
            
            return (
              <motion.svg
                key={line.id}
                className="absolute inset-0 w-full h-full pointer-events-none"
                initial={{ opacity: 0 }}
                animate={{ opacity: [0, 1, 0] }}
                exit={{ opacity: 0 }}
                transition={{ duration: 2 }}
              >
                <motion.line
                  x1={fromPos.x}
                  y1={fromPos.y}
                  x2={toPos.x}
                  y2={toPos.y}
                  stroke="url(#collaborationGradient)"
                  strokeWidth="2"
                  strokeDasharray="5,5"
                  initial={{ pathLength: 0 }}
                  animate={{ pathLength: 1 }}
                  transition={{ duration: 1 }}
                />
                <defs>
                  <linearGradient id="collaborationGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#8b5cf6" />
                    <stop offset="100%" stopColor="#ec4899" />
                  </linearGradient>
                </defs>
                
                {/* Message Indicator */}
                <motion.circle
                  r="3"
                  fill="#8b5cf6"
                  initial={{ 
                    cx: fromPos.x, 
                    cy: fromPos.y 
                  }}
                  animate={{ 
                    cx: toPos.x, 
                    cy: toPos.y 
                  }}
                  transition={{ duration: 1 }}
                />
              </motion.svg>
            )
          })}
        </AnimatePresence>
      </div>

      {/* Agent Details Panel */}
      <AnimatePresence>
        {showDetails && selectedAgent && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-slate-900/50 border border-slate-700/50 rounded-xl p-6 space-y-4"
          >
            {(() => {
              const agent = agents.find(a => a.id === selectedAgent)
              const progress = agentProgress[selectedAgent]
              
              if (!agent || !progress) return null
              
              const Icon = agentIcons[agent.type]
              
              return (
                <>
                  {/* Agent Header */}
                  <div className="flex items-center space-x-4">
                    <div className={`p-3 rounded-xl bg-gradient-to-br ${agentColors[agent.type]} bg-opacity-20`}>
                      <Icon className="w-6 h-6 text-white" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-white">{agent.name}</h3>
                      <p className="text-slate-400">{agent.description}</p>
                    </div>
                    <div className={`px-3 py-1 rounded-full text-sm ${statusColors[agent.status]}`}>
                      {agent.status.replace('_', ' ')}
                    </div>
                  </div>

                  {/* Current Task */}
                  {progress.taskName && (
                    <div className="space-y-2">
                      <h4 className="text-sm font-medium text-white flex items-center space-x-2">
                        <Clock className="w-4 h-4 text-purple-400" />
                        <span>Current Task</span>
                      </h4>
                      <div className="p-3 bg-slate-800/50 rounded-lg">
                        <p className="text-slate-300">{progress.taskName}</p>
                        <div className="mt-2 flex items-center space-x-2">
                          <div className="flex-1 bg-slate-700 rounded-full h-2">
                            <motion.div
                              className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full"
                              initial={{ width: 0 }}
                              animate={{ width: `${progress.progress}%` }}
                              transition={{ duration: 0.5 }}
                            />
                          </div>
                          <span className="text-sm text-slate-400">{progress.progress}%</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Capabilities */}
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium text-white">Capabilities</h4>
                    <div className="flex flex-wrap gap-2">
                      {agent.capabilities.map((capability) => (
                        <span
                          key={capability}
                          className="px-2 py-1 text-xs bg-slate-700/50 text-slate-300 rounded-full"
                        >
                          {capability}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Recent Logs */}
                  {progress.logs.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="text-sm font-medium text-white flex items-center space-x-2">
                        <MessageCircle className="w-4 h-4 text-blue-400" />
                        <span>Recent Activity</span>
                      </h4>
                      <div className="space-y-1 max-h-32 overflow-y-auto">
                        {progress.logs.slice(-5).map((log) => (
                          <div
                            key={log.id}
                            className="p-2 bg-slate-800/30 rounded text-sm text-slate-300"
                          >
                            <div className="flex items-center space-x-2">
                              <div className={`w-2 h-2 rounded-full ${
                                log.level === 'error' ? 'bg-red-400' :
                                log.level === 'warning' ? 'bg-yellow-400' :
                                log.level === 'success' ? 'bg-green-400' : 'bg-blue-400'
                              }`} />
                              <span>{log.message}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )
            })()}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
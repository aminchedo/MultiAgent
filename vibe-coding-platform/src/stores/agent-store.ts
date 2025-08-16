import { create } from 'zustand'
import { devtools, subscribeWithSelector } from 'zustand/middleware'
import { 
  Agent, 
  AgentType, 
  AgentStatus, 
  AgentProgress, 
  AgentLog, 
  AgentCollaboration 
} from '@/types'

interface AgentStore {
  // Agents
  agents: Agent[]
  agentProgress: Record<string, AgentProgress>
  agentLogs: AgentLog[]
  agentCollaborations: AgentCollaboration[]
  
  // Current activity
  activePhase: 'planning' | 'coding' | 'testing' | 'documenting' | 'reviewing' | 'idle'
  leadAgent: string | null
  
  // UI state
  showAgentDetails: boolean
  selectedAgent: string | null
  
  // Actions
  initializeAgents: () => void
  updateAgentStatus: (agentId: string, status: AgentStatus, progress?: number) => void
  updateAgentProgress: (agentId: string, progress: Partial<AgentProgress>) => void
  addAgentLog: (log: Omit<AgentLog, 'id' | 'timestamp'>) => void
  addCollaboration: (collaboration: Omit<AgentCollaboration, 'timestamp'>) => void
  setActivePhase: (phase: string, leadAgent?: string) => void
  setSelectedAgent: (agentId: string | null) => void
  setShowAgentDetails: (show: boolean) => void
  clearLogs: () => void
  resetAgents: () => void
}

const createInitialAgents = (): Agent[] => [
  {
    id: 'planner-agent',
    type: AgentType.PLANNER,
    name: 'Architect',
    description: 'Plans project structure and analyzes requirements',
    status: AgentStatus.IDLE,
    progress: 0,
    capabilities: [
      'Requirements Analysis',
      'Architecture Design',
      'Technology Selection',
      'Project Planning',
    ],
    avatar: '🏗️',
  },
  {
    id: 'code-generator-agent',
    type: AgentType.CODE_GENERATOR,
    name: 'CodeCrafter',
    description: 'Generates high-quality code files and components',
    status: AgentStatus.IDLE,
    progress: 0,
    capabilities: [
      'React Components',
      'TypeScript Generation',
      'API Development',
      'Database Schema',
      'UI Components',
    ],
    avatar: '⚡',
  },
  {
    id: 'testing-agent',
    type: AgentType.TESTER,
    name: 'TestGuardian',
    description: 'Creates comprehensive tests and quality assurance',
    status: AgentStatus.IDLE,
    progress: 0,
    capabilities: [
      'Unit Testing',
      'Integration Testing',
      'E2E Testing',
      'Performance Testing',
      'Security Testing',
    ],
    avatar: '🛡️',
  },
  {
    id: 'doc-generator-agent',
    type: AgentType.DOC_GENERATOR,
    name: 'DocMaster',
    description: 'Generates documentation and guides',
    status: AgentStatus.IDLE,
    progress: 0,
    capabilities: [
      'README Generation',
      'API Documentation',
      'Code Comments',
      'User Guides',
      'Technical Specs',
    ],
    avatar: '📚',
  },
  {
    id: 'reviewer-agent',
    type: AgentType.REVIEWER,
    name: 'QualityGuard',
    description: 'Reviews code quality and best practices',
    status: AgentStatus.IDLE,
    progress: 0,
    capabilities: [
      'Code Review',
      'Best Practices',
      'Performance Optimization',
      'Security Review',
      'Accessibility Check',
    ],
    avatar: '🔍',
  },
]

export const useAgentStore = create<AgentStore>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      // Initial state
      agents: [],
      agentProgress: {},
      agentLogs: [],
      agentCollaborations: [],
      activePhase: 'idle',
      leadAgent: null,
      showAgentDetails: false,
      selectedAgent: null,

      // Actions
      initializeAgents: () => {
        const agents = createInitialAgents()
        const agentProgress: Record<string, AgentProgress> = {}
        
        agents.forEach(agent => {
          agentProgress[agent.id] = {
            agentId: agent.id,
            taskId: '',
            taskName: 'Waiting for task...',
            progress: 0,
            status: 'idle',
            startTime: new Date(),
            logs: [],
          }
        })

        set({ agents, agentProgress })
      },

      updateAgentStatus: (agentId, status, progress) =>
        set((state) => ({
          agents: state.agents.map(agent =>
            agent.id === agentId
              ? { ...agent, status, progress: progress ?? agent.progress }
              : agent
          ),
          agentProgress: {
            ...state.agentProgress,
            [agentId]: {
              ...state.agentProgress[agentId],
              status: status === AgentStatus.WORKING ? 'working' 
                     : status === AgentStatus.COMPLETED ? 'completed'
                     : status === AgentStatus.ERROR ? 'error' : 'idle',
              progress: progress ?? state.agentProgress[agentId]?.progress ?? 0,
            },
          },
        })),

      updateAgentProgress: (agentId, progress) =>
        set((state) => ({
          agentProgress: {
            ...state.agentProgress,
            [agentId]: {
              ...state.agentProgress[agentId],
              ...progress,
            },
          },
        })),

      addAgentLog: (log) =>
        set((state) => {
          const newLog: AgentLog = {
            ...log,
            id: `log-${Date.now()}-${Math.random()}`,
            timestamp: new Date(),
          }
          
          return {
            agentLogs: [...state.agentLogs, newLog].slice(-100), // Keep last 100 logs
            agentProgress: {
              ...state.agentProgress,
              [log.agentId]: {
                ...state.agentProgress[log.agentId],
                logs: [...(state.agentProgress[log.agentId]?.logs || []), newLog].slice(-20),
              },
            },
          }
        }),

      addCollaboration: (collaboration) =>
        set((state) => {
          const newCollaboration: AgentCollaboration = {
            ...collaboration,
            timestamp: new Date(),
          }
          
          return {
            agentCollaborations: [...state.agentCollaborations, newCollaboration].slice(-50),
          }
        }),

      setActivePhase: (phase, leadAgent) =>
        set({ 
          activePhase: phase as any, 
          leadAgent: leadAgent || null,
        }),

      setSelectedAgent: (agentId) =>
        set({ selectedAgent: agentId }),

      setShowAgentDetails: (show) =>
        set({ showAgentDetails: show }),

      clearLogs: () =>
        set({ agentLogs: [], agentCollaborations: [] }),

      resetAgents: () => {
        const agents = createInitialAgents()
        const agentProgress: Record<string, AgentProgress> = {}
        
        agents.forEach(agent => {
          agentProgress[agent.id] = {
            agentId: agent.id,
            taskId: '',
            taskName: 'Ready to start...',
            progress: 0,
            status: 'idle',
            startTime: new Date(),
            logs: [],
          }
        })

        set({
          agents,
          agentProgress,
          agentLogs: [],
          agentCollaborations: [],
          activePhase: 'idle',
          leadAgent: null,
        })
      },
    })),
    { name: 'agent-store' }
  )
)

// Selectors
export const useAgents = () => useAgentStore((state) => state.agents)
export const useAgentProgress = () => useAgentStore((state) => state.agentProgress)
export const useActivePhase = () => useAgentStore((state) => state.activePhase)
export const useAgentLogs = () => useAgentStore((state) => state.agentLogs)
export const useAgentCollaborations = () => useAgentStore((state) => state.agentCollaborations)
export const useSelectedAgent = () => useAgentStore((state) => state.selectedAgent)

// Helper selectors
export const useAgentById = (id: string) => 
  useAgentStore((state) => state.agents.find(agent => agent.id === id))

export const useAgentProgressById = (id: string) =>
  useAgentStore((state) => state.agentProgress[id])

export const useActiveAgents = () =>
  useAgentStore((state) => 
    state.agents.filter(agent => 
      agent.status === AgentStatus.WORKING || agent.status === AgentStatus.COMPLETED
    )
  )
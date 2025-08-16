import { create } from 'zustand'
import { apiClient } from '@/lib/api/production-client'

interface JobState {
  currentJob: any | null
  agentProgress: Record<string, any>
  files: any[]
  isConnected: boolean
  isLoading: boolean
  error: string | null
  jobStatus: string
  
  // Actions
  setCurrentJob: (job: any) => void
  updateAgentProgress: (agentType: string, progress: any) => void
  addFile: (file: any) => void
  updateFile: (filePath: string, content: any) => void
  setConnected: (connected: boolean) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  setJobStatus: (status: string) => void
  addAgentMessage: (agent: string, message: string) => void
  
  // API Actions
  createJob: (description: string, preferences?: any) => Promise<any>
  fetchJobStatus: (jobId: string) => Promise<any>
  downloadProject: (jobId: string) => Promise<Blob>
  
  // Polling
  startPolling: (jobId: string) => void
  stopPolling: () => void
}

let pollingInterval: NodeJS.Timeout | null = null

export const useJobStore = create<JobState>((set, get) => ({
  currentJob: null,
  agentProgress: {},
  files: [],
  isConnected: false,
  isLoading: false,
  error: null,
  jobStatus: 'pending',
  
  setCurrentJob: (job) => set({ currentJob: job }),
  updateAgentProgress: (agentType, progress) => set((state) => ({
    agentProgress: { ...state.agentProgress, [agentType]: progress }
  })),
  addFile: (file) => set((state) => ({ files: [...state.files, file] })),
  updateFile: (filePath, content) => set((state) => ({
    files: state.files.map(f => f.path === filePath ? { ...f, content } : f)
  })),
  setConnected: (connected) => set({ isConnected: connected }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  setJobStatus: (status) => set({ jobStatus: status }),
  addAgentMessage: (agent, message) => set((state) => ({
    agentProgress: {
      ...state.agentProgress,
      [agent]: {
        ...state.agentProgress[agent],
        messages: [...(state.agentProgress[agent]?.messages || []), message]
      }
    }
  })),
  
  // API Actions
  createJob: async (description: string, preferences = {}) => {
    set({ isLoading: true, error: null })
    try {
      const response = await apiClient.createVibeJob(description, preferences)
      
      if (response.error || !response.data) {
        throw new Error(response.error || 'Failed to create job')
      }
      
      set({ currentJob: response.data, isLoading: false })
      return response.data
    } catch (error: any) {
      set({ error: error.message, isLoading: false })
      throw error
    }
  },
  
  fetchJobStatus: async (jobId: string) => {
    try {
      const response = await apiClient.getJobStatus(jobId)
      
      if (response.error || !response.data) {
        throw new Error(response.error || 'Failed to fetch job status')
      }
      
      const job = response.data
      set({ currentJob: job })
      
      // Update agent progress based on current agent
      if (job.current_agent) {
        set((state) => ({
          agentProgress: {
            ...state.agentProgress,
            [job.current_agent]: {
              status: 'working',
              progress: job.progress,
              task: job.current_agent
            }
          }
        }))
      }
      
      // Update files if available
      if (job.files && job.files.length > 0) {
        set({ files: job.files })
      }
      
      return job
    } catch (error: any) {
      set({ error: error.message })
      throw error
    }
  },
  
  downloadProject: async (jobId: string) => {
    try {
      const response = await apiClient.downloadJob(jobId)
      
      if (response.error || !response.data) {
        throw new Error(response.error || 'Failed to download project')
      }
      
      return response.data
    } catch (error: any) {
      set({ error: error.message })
      throw error
    }
  },
  
  // Polling
  startPolling: (jobId: string) => {
    // Stop existing polling
    get().stopPolling()
    
    // Start new polling
    pollingInterval = setInterval(async () => {
      try {
        const job = await get().fetchJobStatus(jobId)
        
        // Stop polling if job is completed or failed
        if (job.status === 'completed' || job.status === 'failed') {
          get().stopPolling()
        }
      } catch (error) {
        console.error('Polling error:', error)
        get().stopPolling()
      }
    }, 2000) // Poll every 2 seconds
  },
  
  stopPolling: () => {
    if (pollingInterval) {
      clearInterval(pollingInterval)
      pollingInterval = null
    }
  }
}))
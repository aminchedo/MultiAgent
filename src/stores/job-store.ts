import { create } from 'zustand'

interface JobState {
	currentJob: any | null
	agentProgress: Record<string, any>
	files: any[]
	isConnected: boolean
	setCurrentJob: (job: any) => void
	updateAgentProgress: (agentType: string, progress: any) => void
	addFile: (file: any) => void
	setConnected: (connected: boolean) => void
}

export const useJobStore = create<JobState>((set) => ({
	currentJob: null,
	agentProgress: {},
	files: [],
	isConnected: false,
	setCurrentJob: (job) => set({ currentJob: job }),
	updateAgentProgress: (agentType, progress) => set((state) => ({
		agentProgress: { ...state.agentProgress, [agentType]: progress }
	})),
	addFile: (file) => set((state) => ({ files: [...state.files, file] })),
	setConnected: (connected) => set({ isConnected: connected })
}))
import { create } from 'zustand'
import { devtools, subscribeWithSelector } from 'zustand/middleware'
import { 
  VibeProject, 
  VibeInputData, 
  ProjectPreferences, 
  ProjectType, 
  ComplexityLevel, 
  JobStatus,
  VirtualFile 
} from '@/types'

interface VibeStore {
  // Current project state
  currentProject: VibeProject | null
  isGenerating: boolean
  generationProgress: number
  generationPhase: 'input' | 'planning' | 'coding' | 'testing' | 'reviewing' | 'complete'
  
  // Vibe input
  vibeInput: VibeInputData
  projectPreferences: ProjectPreferences
  
  // Project history
  recentProjects: VibeProject[]
  
  // UI state
  isLoading: boolean
  error: string | null
  
  // Actions
  setVibeInput: (input: Partial<VibeInputData>) => void
  setProjectPreferences: (prefs: Partial<ProjectPreferences>) => void
  startGeneration: (input: VibeInputData, prefs: ProjectPreferences) => Promise<void>
  updateGenerationProgress: (progress: number, phase?: string) => void
  setCurrentProject: (project: VibeProject | null) => void
  addRecentProject: (project: VibeProject) => void
  updateProjectFiles: (files: VirtualFile[]) => void
  setError: (error: string | null) => void
  setLoading: (loading: boolean) => void
  resetGeneration: () => void
}

const initialVibeInput: VibeInputData = {
  description: '',
  projectType: ProjectType.WEB_APP,
  complexity: ComplexityLevel.MODERATE,
  languages: ['typescript'],
  frameworks: ['react'],
  features: [],
}

const initialProjectPreferences: ProjectPreferences = {
  codeStyle: 'functional',
  testing: true,
  documentation: true,
  deployment: 'vercel',
  database: 'none',
  authentication: 'none',
}

export const useVibeStore = create<VibeStore>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      // Initial state
      currentProject: null,
      isGenerating: false,
      generationProgress: 0,
      generationPhase: 'input',
      vibeInput: initialVibeInput,
      projectPreferences: initialProjectPreferences,
      recentProjects: [],
      isLoading: false,
      error: null,

      // Actions
      setVibeInput: (input) =>
        set((state) => ({
          vibeInput: { ...state.vibeInput, ...input },
        })),

      setProjectPreferences: (prefs) =>
        set((state) => ({
          projectPreferences: { ...state.projectPreferences, ...prefs },
        })),

      startGeneration: async (input, prefs) => {
        set({
          isGenerating: true,
          generationProgress: 0,
          generationPhase: 'planning',
          vibeInput: input,
          projectPreferences: prefs,
          error: null,
        })

        try {
          // Create new project
          const newProject: VibeProject = {
            id: `project-${Date.now()}`,
            name: input.description.split(' ').slice(0, 3).join(' ') || 'New Project',
            description: input.description,
            type: input.projectType || ProjectType.WEB_APP,
            languages: input.languages || ['typescript'],
            frameworks: input.frameworks || ['react'],
            complexity: input.complexity || ComplexityLevel.MODERATE,
            features: input.features || [],
            status: JobStatus.RUNNING,
            createdAt: new Date(),
            updatedAt: new Date(),
            files: [],
          }

          set({ currentProject: newProject })

          // Here we would typically call the backend API
          // For now, we'll simulate the process
          console.log('Starting project generation...', { input, prefs })
          
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Generation failed',
            isGenerating: false,
          })
        }
      },

      updateGenerationProgress: (progress, phase) =>
        set((state) => ({
          generationProgress: progress,
          generationPhase: (phase as any) || state.generationPhase,
        })),

      setCurrentProject: (project) =>
        set({ currentProject: project }),

      addRecentProject: (project) =>
        set((state) => {
          const filtered = state.recentProjects.filter(p => p.id !== project.id)
          return {
            recentProjects: [project, ...filtered].slice(0, 10), // Keep last 10
          }
        }),

      updateProjectFiles: (files) =>
        set((state) => ({
          currentProject: state.currentProject
            ? { ...state.currentProject, files }
            : null,
        })),

      setError: (error) => set({ error }),

      setLoading: (loading) => set({ isLoading: loading }),

      resetGeneration: () =>
        set({
          isGenerating: false,
          generationProgress: 0,
          generationPhase: 'input',
          currentProject: null,
          error: null,
        }),
    })),
    { name: 'vibe-store' }
  )
)

// Selectors for common use cases
export const useCurrentProject = () => useVibeStore((state) => state.currentProject)
export const useIsGenerating = () => useVibeStore((state) => state.isGenerating)
export const useGenerationProgress = () => useVibeStore((state) => ({
  progress: state.generationProgress,
  phase: state.generationPhase,
}))
export const useVibeInput = () => useVibeStore((state) => state.vibeInput)
export const useProjectPreferences = () => useVibeStore((state) => state.projectPreferences)
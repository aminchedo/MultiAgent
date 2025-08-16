export interface JobStatus {
  id: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  created_at: string
  updated_at: string
  user_id?: string
  project_type: 'web_app' | 'api' | 'mobile_app' | 'desktop_app' | 'cli_tool' | 'library' | 'microservice' | 'fullstack'
  complexity: 'simple' | 'moderate' | 'complex' | 'enterprise'
  description: string
  result_files?: GeneratedFile[]
  error_message?: string
}

export interface AgentProgress {
  agent_type: 'planner' | 'code_generator' | 'tester' | 'doc_generator' | 'reviewer'
  status: 'idle' | 'running' | 'completed' | 'error'
  progress: number
  current_task: string
  messages: AgentMessage[]
  start_time: string
  end_time?: string
  error?: string
}

export interface AgentMessage {
  agent?: string
  content: string
  timestamp?: string
  metadata?: Record<string, any>
}

export interface GeneratedFile {
  path: string
  content: string
  language: string
  size: number
  created_by?: 'planner' | 'code_generator' | 'tester' | 'doc_generator' | 'reviewer'
  is_binary?: boolean
  download_url?: string
}

export interface WebSocketMessage {
  type: 'status' | 'log' | 'agent_message' | 'progress' | 'error' | 'completion'
  job_id?: string
  agent?: string
  data?: any
  content?: string
  timestamp: string
  metadata?: Record<string, any>
}
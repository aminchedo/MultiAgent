// Core Types for Vibe Coding Platform
export interface VibeProject {
  id: string
  name: string
  description: string
  type: ProjectType
  languages: string[]
  frameworks: string[]
  complexity: ComplexityLevel
  features: string[]
  status: JobStatus
  createdAt: Date
  updatedAt: Date
  files: VirtualFile[]
  preview?: PreviewData
}

export interface VirtualFile {
  id: string
  path: string
  name: string
  content: string
  language: string
  size: number
  lastModified: Date
  isDirectory: boolean
  children?: VirtualFile[]
}

export interface PreviewData {
  url?: string
  type: 'static' | 'react' | 'node' | 'python' | 'api'
  status: 'loading' | 'ready' | 'error'
  logs: string[]
  dependencies?: Record<string, string>
}

// Agent Types
export interface Agent {
  id: string
  type: AgentType
  name: string
  description: string
  status: AgentStatus
  progress: number
  currentTask?: string
  capabilities: string[]
  avatar?: string
}

export interface AgentProgress {
  agentId: string
  taskId: string
  taskName: string
  progress: number
  status: 'idle' | 'working' | 'completed' | 'error'
  startTime: Date
  estimatedCompletion?: Date
  logs: AgentLog[]
}

export interface AgentLog {
  id: string
  agentId: string
  message: string
  level: 'info' | 'warning' | 'error' | 'success'
  timestamp: Date
  metadata?: Record<string, any>
}

export interface AgentCollaboration {
  fromAgent: string
  toAgent: string
  message: string
  type: 'request' | 'response' | 'notification'
  timestamp: Date
  data?: any
}

// Enums matching backend
export enum JobStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

export enum ProjectType {
  WEB_APP = 'web_app',
  API = 'api',
  MOBILE_APP = 'mobile_app',
  DESKTOP_APP = 'desktop_app',
  CLI_TOOL = 'cli_tool',
  LIBRARY = 'library',
  MICROSERVICE = 'microservice',
  FULLSTACK = 'fullstack'
}

export enum ComplexityLevel {
  SIMPLE = 'simple',
  MODERATE = 'moderate',
  COMPLEX = 'complex',
  ENTERPRISE = 'enterprise'
}

export enum AgentType {
  PLANNER = 'planner',
  CODE_GENERATOR = 'code_generator',
  TESTER = 'tester',
  DOC_GENERATOR = 'doc_generator',
  REVIEWER = 'reviewer'
}

export enum AgentStatus {
  IDLE = 'idle',
  WORKING = 'working',
  COMPLETED = 'completed',
  ERROR = 'error',
  PAUSED = 'paused'
}

export enum MessageType {
  STATUS = 'status',
  LOG = 'log',
  AGENT_MESSAGE = 'agent_message',
  PROGRESS = 'progress',
  ERROR = 'error',
  COMPLETION = 'completion'
}

// WebSocket Types
export interface WebSocketMessage {
  id: string
  type: MessageType
  jobId?: string
  agentId?: string
  data: any
  timestamp: Date
}

// Vibe Input Types
export interface VibeInputData {
  description: string
  projectType?: ProjectType
  complexity?: ComplexityLevel
  languages?: string[]
  frameworks?: string[]
  features?: string[]
  style?: ProjectStyle
  deadline?: Date
}

export interface ProjectStyle {
  theme: 'modern' | 'minimal' | 'colorful' | 'professional' | 'playful'
  primaryColor?: string
  layout: 'single-page' | 'multi-page' | 'dashboard' | 'blog' | 'ecommerce'
  animations: 'none' | 'subtle' | 'moderate' | 'rich'
}

export interface VibeExample {
  id: string
  title: string
  description: string
  category: ProjectType
  complexity: ComplexityLevel
  tags: string[]
  preview?: string
}

export interface ProjectPreferences {
  codeStyle: 'functional' | 'oop' | 'mixed'
  testing: boolean
  documentation: boolean
  deployment: 'none' | 'vercel' | 'netlify' | 'heroku' | 'aws'
  database?: 'none' | 'sqlite' | 'postgres' | 'mongodb' | 'firebase'
  authentication?: 'none' | 'jwt' | 'oauth' | 'auth0' | 'firebase'
}

// Editor Types
export interface EditorConfig {
  theme: 'dark' | 'light' | 'auto'
  fontSize: number
  fontFamily: string
  tabSize: number
  wordWrap: boolean
  minimap: boolean
  lineNumbers: boolean
  autoFormat: boolean
  keyBindings: 'default' | 'vim' | 'emacs'
}

export interface CodeFile {
  id: string
  path: string
  content: string
  language: string
  isDirty: boolean
  lastSaved: Date
  errors: CodeError[]
  warnings: CodeWarning[]
}

export interface CodeError {
  line: number
  column: number
  message: string
  severity: 'error' | 'warning' | 'info'
  code?: string
}

export interface CodeWarning extends CodeError {
  fixable: boolean
  suggestion?: string
}

// Export Types
export interface ExportFormat {
  id: string
  name: string
  description: string
  icon: string
  extension?: string
  type: 'archive' | 'repository' | 'deployment' | 'single-file'
}

export interface ExportOptions {
  format: ExportFormat
  includeFiles: string[]
  includeDependencies: boolean
  includeDocumentation: boolean
  includeTests: boolean
  customConfig?: Record<string, any>
}

export interface DeploymentTarget {
  id: string
  name: string
  description: string
  icon: string
  supportsNodejs: boolean
  supportsStatic: boolean
  supportsPython: boolean
  configRequired: string[]
}

export interface DeploymentConfig {
  target: DeploymentTarget
  domain?: string
  envVars?: Record<string, string>
  buildCommand?: string
  outputDirectory?: string
  region?: string
}

// Collaboration Types
export interface Collaborator {
  id: string
  name: string
  email: string
  avatar?: string
  role: 'owner' | 'editor' | 'viewer'
  status: 'online' | 'offline' | 'away'
  cursor?: CursorPosition
  lastSeen: Date
}

export interface CursorPosition {
  fileId: string
  line: number
  column: number
  selection?: {
    startLine: number
    startColumn: number
    endLine: number
    endColumn: number
  }
}

export interface Permission {
  resource: string
  action: 'read' | 'write' | 'delete' | 'share'
  allowed: boolean
}

// Sandbox Types
export interface SandboxEnvironment {
  id: string
  type: 'browser' | 'node' | 'python' | 'static'
  status: 'starting' | 'ready' | 'error' | 'destroyed'
  url?: string
  logs: SandboxLog[]
  dependencies: Record<string, string>
  environment: Record<string, string>
}

export interface SandboxLog {
  id: string
  level: 'log' | 'warn' | 'error' | 'info'
  message: string
  timestamp: Date
  source: 'stdout' | 'stderr' | 'system'
}

// Gallery Types
export interface CommunityProject {
  id: string
  name: string
  description: string
  author: {
    id: string
    name: string
    avatar?: string
  }
  tags: string[]
  category: ProjectType
  complexity: ComplexityLevel
  likes: number
  forks: number
  views: number
  createdAt: Date
  updatedAt: Date
  thumbnail?: string
  isPublic: boolean
  isFeatured: boolean
}

export interface ProjectCategory {
  id: string
  name: string
  description: string
  icon: string
  color: string
  count: number
}

export interface FilterOptions {
  categories: string[]
  complexity: ComplexityLevel[]
  languages: string[]
  frameworks: string[]
  sortBy: 'popular' | 'recent' | 'trending' | 'name'
  timeRange: '24h' | '7d' | '30d' | 'all'
}

// UI Types
export interface Toast {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  description?: string
  duration?: number
  action?: {
    label: string
    onClick: () => void
  }
}

export interface Modal {
  id: string
  type: string
  props: Record<string, any>
  onClose: () => void
}

// Search and Suggestions
export interface AISuggestion {
  id: string
  type: 'completion' | 'fix' | 'optimization' | 'refactor'
  title: string
  description: string
  code?: string
  confidence: number
  applicableFiles: string[]
  category: 'performance' | 'security' | 'style' | 'functionality'
}

export interface SearchResult {
  id: string
  type: 'file' | 'function' | 'variable' | 'class' | 'import'
  title: string
  description: string
  file: string
  line: number
  column: number
  preview: string
  relevance: number
}

// Animation Types
export interface AnimationConfig {
  duration: number
  easing: string
  delay?: number
  stagger?: number
}

export interface ThemeConfig {
  name: string
  colors: {
    primary: string
    secondary: string
    accent: string
    background: string
    foreground: string
    muted: string
    border: string
  }
  fonts: {
    sans: string
    mono: string
  }
  animations: {
    fast: string
    normal: string
    slow: string
  }
}
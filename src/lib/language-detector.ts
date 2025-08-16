<<<<<<< HEAD
/**
 * Language Detection Utility
 * 
 * This module provides client-side language detection to complement the backend
 * language detection system. It can be used for frontend validation or fallback scenarios.
 */

export type SupportedLanguage = 'python' | 'javascript' | 'java' | 'go' | 'rust' | 'php' | 'ruby' | 'cpp'
export type ProjectType = 'CLI_TOOL' | 'WEB_APP' | 'API' | 'MOBILE_APP' | 'LIBRARY' | 'DESKTOP_APP' | 'DATA_ANALYSIS' | 'MACHINE_LEARNING'

interface LanguageIndicators {
  [key: string]: string[]
}

const LANGUAGE_INDICATORS: LanguageIndicators = {
  python: [
    'python', 'py', 'pip', 'django', 'flask', 'fastapi', 'pandas', 'numpy',
    'speech', 'audio', 'microphone', 'recognition', 'translation', 'persian',
    'farsi', 'scikit-learn', 'tensorflow', 'pytorch', 'matplotlib', 'seaborn',
    'jupyter', 'anaconda', 'conda', 'virtualenv', 'pipenv', 'poetry'
  ],
  javascript: [
    'javascript', 'js', 'node', 'nodejs', 'npm', 'react', 'vue', 'angular',
    'express', 'next.js', 'nextjs', 'typescript', 'ts', 'webpack', 'babel',
    'jquery', 'lodash', 'moment', 'axios', 'fetch', 'web', 'frontend', 'dashboard'
  ],
  java: [
    'java', 'spring', 'springboot', 'maven', 'gradle', 'junit', 'hibernate',
    'jpa', 'servlet', 'tomcat', 'eclipse', 'intellij'
  ],
  go: [
    'go', 'golang', 'goroutine', 'gin', 'fiber', 'echo', 'beego'
  ],
  rust: [
    'rust', 'cargo', 'tokio', 'serde', 'actix', 'warp'
  ],
  php: [
    'php', 'laravel', 'symfony', 'composer', 'wordpress', 'drupal'
  ],
  ruby: [
    'ruby', 'rails', 'gem', 'bundler', 'sinatra', 'rspec'
  ],
  cpp: [
    'c++', 'cpp', 'cmake', 'boost', 'qt', 'opengl', 'opencv'
  ]
}

const PROJECT_TYPE_INDICATORS = {
  CLI_TOOL: ['cli', 'command line', 'terminal', 'script', 'automation', 'tool'],
  WEB_APP: ['web', 'website', 'frontend', 'ui', 'dashboard', 'react', 'vue', 'angular'],
  API: ['api', 'rest', 'graphql', 'endpoint', 'service', 'microservice', 'backend'],
  MOBILE_APP: ['mobile', 'android', 'ios', 'app', 'react native', 'flutter'],
  LIBRARY: ['library', 'package', 'module', 'framework', 'sdk'],
  DESKTOP_APP: ['desktop', 'gui', 'window', 'application', 'electron'],
  DATA_ANALYSIS: ['data', 'analysis', 'analytics', 'visualization', 'chart', 'graph'],
  MACHINE_LEARNING: ['machine learning', 'ml', 'ai', 'neural', 'model', 'training']
}

/**
 * Detect the primary programming language from a project description
 */
export function detectLanguage(description: string): SupportedLanguage {
  const lowerDesc = description.toLowerCase()
  const scores: { [key: string]: number } = {}

  // Initialize scores
  Object.keys(LANGUAGE_INDICATORS).forEach(lang => {
    scores[lang] = 0
  })

  // Calculate scores based on keyword matches
  Object.entries(LANGUAGE_INDICATORS).forEach(([lang, indicators]) => {
    indicators.forEach(indicator => {
      if (lowerDesc.includes(indicator)) {
        scores[lang] += 1
      }
    })
  })

  // Find the language with the highest score
  const maxScore = Math.max(...Object.values(scores))
  const detectedLanguage = Object.entries(scores).find(([_, score]) => score === maxScore)?.[0]

  // Apply specific rules for better accuracy
  if (lowerDesc.includes('speech') || lowerDesc.includes('audio') || lowerDesc.includes('persian')) {
    return 'python' // Python is better for speech processing
  }

  if (lowerDesc.includes('web') || lowerDesc.includes('react') || lowerDesc.includes('dashboard')) {
    return 'javascript' // JavaScript is better for web apps
  }

  // Return detected language or default to Python
  return (detectedLanguage as SupportedLanguage) || 'python'
}

/**
 * Determine the project type based on description and language
 */
export function determineProjectType(description: string, language?: SupportedLanguage): ProjectType {
  const lowerDesc = description.toLowerCase()
  const scores: { [key: string]: number } = {}

  // Initialize scores
  Object.keys(PROJECT_TYPE_INDICATORS).forEach(type => {
    scores[type] = 0
  })

  // Calculate scores based on keyword matches
  Object.entries(PROJECT_TYPE_INDICATORS).forEach(([type, indicators]) => {
    indicators.forEach(indicator => {
      if (lowerDesc.includes(indicator)) {
        scores[type] += 1
      }
    })
  })

  // Apply language-specific biases
  if (language === 'javascript') {
    if (lowerDesc.includes('react') || lowerDesc.includes('vue') || lowerDesc.includes('angular')) {
      scores.WEB_APP += 3
    }
    if (lowerDesc.includes('express') || lowerDesc.includes('fastify') || lowerDesc.includes('koa')) {
      scores.API += 3
    }
  }

  if (language === 'python') {
    if (lowerDesc.includes('data') || lowerDesc.includes('analysis')) {
      scores.DATA_ANALYSIS += 3
    }
    if (lowerDesc.includes('ml') || lowerDesc.includes('machine learning') || lowerDesc.includes('ai')) {
      scores.MACHINE_LEARNING += 3
    }
  }

  // Find the project type with the highest score
  const maxScore = Math.max(...Object.values(scores))
  const detectedType = Object.entries(scores).find(([_, score]) => score === maxScore)?.[0]

  return (detectedType as ProjectType) || 'CLI_TOOL'
}

/**
 * Validate if the detected language matches the project requirements
 */
export function validateLanguageMatch(description: string, detectedLanguage: SupportedLanguage): boolean {
  const lowerDesc = description.toLowerCase()
  
  // Strong validation rules
  if (detectedLanguage === 'python') {
    // Python should not be used for explicit React/web requests
    if (lowerDesc.includes('react') || lowerDesc.includes('jsx') || lowerDesc.includes('frontend')) {
      return false
    }
  }

  if (detectedLanguage === 'javascript') {
    // JavaScript should not be used for data science/ML requests
    if (lowerDesc.includes('data science') || lowerDesc.includes('machine learning') || lowerDesc.includes('tensorflow')) {
      return false
    }
  }

  return true
}

/**
 * Get language-specific file extensions
 */
export function getLanguageExtensions(language: SupportedLanguage): string[] {
  const extensions = {
    python: ['.py', '.pyx', '.pyi'],
    javascript: ['.js', '.jsx', '.ts', '.tsx'],
    java: ['.java'],
    go: ['.go'],
    rust: ['.rs'],
    php: ['.php'],
    ruby: ['.rb'],
    cpp: ['.cpp', '.cc', '.cxx', '.h', '.hpp']
  }

  return extensions[language] || []
}

/**
 * Get language-specific package managers
 */
export function getPackageManager(language: SupportedLanguage): string {
  const managers = {
    python: 'pip',
    javascript: 'npm',
    java: 'maven',
    go: 'go mod',
    rust: 'cargo',
    php: 'composer',
    ruby: 'gem',
    cpp: 'cmake'
  }

  return managers[language] || 'unknown'
}

/**
 * Generate language-specific project structure
 */
export function getProjectStructure(language: SupportedLanguage, projectType: ProjectType): string[] {
  if (language === 'python') {
    if (projectType === 'WEB_APP') {
      return ['app.py', 'templates/', 'static/', 'requirements.txt', 'README.md']
    }
    if (projectType === 'CLI_TOOL') {
      return ['main.py', 'requirements.txt', 'README.md']
    }
    if (projectType === 'DATA_ANALYSIS') {
      return ['analysis.py', 'data/', 'notebooks/', 'requirements.txt', 'README.md']
    }
  }

  if (language === 'javascript') {
    if (projectType === 'WEB_APP') {
      return ['src/App.jsx', 'src/components/', 'public/', 'package.json', 'README.md']
    }
    if (projectType === 'API') {
      return ['server.js', 'routes/', 'middleware/', 'package.json', 'README.md']
    }
  }

  return ['main.' + getLanguageExtensions(language)[0].slice(1), 'README.md']
=======
export function detectLanguage(description: string): string {
  const lowerDesc = description.toLowerCase()
  
  // Python indicators
  const pythonKeywords = [
    'python', 'py', 'pip', 'django', 'flask', 'pandas', 'numpy',
    'speech', 'recognition', 'audio', 'microphone', 'persian', 'farsi',
    'automation', 'script', 'cli', 'command line', 'data science'
  ]
  
  // JavaScript indicators
  const jsKeywords = [
    'javascript', 'js', 'react', 'node', 'npm', 'web', 'frontend',
    'backend', 'api', 'server', 'express', 'nextjs', 'dashboard'
  ]
  
  // Count matches
  const pythonScore = pythonKeywords.filter(kw => lowerDesc.includes(kw)).length
  const jsScore = jsKeywords.filter(kw => lowerDesc.includes(kw)).length
  
  // Determine language
  if (pythonScore > jsScore) return 'python'
  if (jsScore > pythonScore) return 'javascript'
  
  // Default based on specific patterns to prevent React fallback
  if (lowerDesc.includes('speech') || lowerDesc.includes('audio')) return 'python'
  if (lowerDesc.includes('web') || lowerDesc.includes('react')) return 'javascript'
  
  // Final fallback to prevent React default
  return 'python'
}

export function determineProjectType(description: string, detectedLanguage?: string): string {
  const lowerDesc = description.toLowerCase()
  const language = detectedLanguage || detectLanguage(description)
  
  if (language === 'python') {
    if (lowerDesc.includes('speech') || lowerDesc.includes('audio') || lowerDesc.includes('cli')) {
      return 'CLI_TOOL'
    }
    if (lowerDesc.includes('web') || lowerDesc.includes('flask') || lowerDesc.includes('django')) {
      return 'WEB_APP'
    }
    return 'CLI_TOOL' // Default for Python
  }
  
  if (language === 'javascript') {
    if (lowerDesc.includes('react') || lowerDesc.includes('web') || lowerDesc.includes('dashboard')) {
      return 'WEB_APP'
    }
    if (lowerDesc.includes('api') || lowerDesc.includes('server')) {
      return 'API'
    }
    return 'WEB_APP' // Default for JavaScript
  }
  
  return 'CLI_TOOL' // General fallback
}

export const testCases = [
  {
    description: "Write a Python script that captures audio from the microphone, recognizes spoken Persian (Farsi), and translates it to English text",
    expectedLanguage: "python",
    expectedType: "CLI_TOOL"
  },
  {
    description: "Build a React web application with dashboard and charts",
    expectedLanguage: "javascript", 
    expectedType: "WEB_APP"
  },
  {
    description: "Create a Node.js REST API with Express and MongoDB",
    expectedLanguage: "javascript",
    expectedType: "API"
  }
]

export function validateLanguageDetection(): boolean {
  console.log('🧪 Testing frontend language detection...')
  
  let allPassed = true
  
  for (const testCase of testCases) {
    const detectedLang = detectLanguage(testCase.description)
    const detectedType = determineProjectType(testCase.description, detectedLang)
    
    const langMatch = detectedLang === testCase.expectedLanguage
    const typeMatch = detectedType === testCase.expectedType
    
    console.log(`Test: ${testCase.description.substring(0, 50)}...`)
    console.log(`Language - Expected: ${testCase.expectedLanguage}, Got: ${detectedLang} ${langMatch ? '✅' : '❌'}`)
    console.log(`Type - Expected: ${testCase.expectedType}, Got: ${detectedType} ${typeMatch ? '✅' : '❌'}`)
    
    if (!langMatch || !typeMatch) {
      allPassed = false
    }
  }
  
  console.log(`🎯 Frontend detection tests: ${allPassed ? '✅ PASSED' : '❌ FAILED'}`)
  return allPassed
>>>>>>> origin/main
}
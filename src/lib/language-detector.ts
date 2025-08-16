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
}
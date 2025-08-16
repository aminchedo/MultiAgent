/**
 * Language Detection Module for Frontend
 * 
 * This module provides intelligent language detection based on project descriptions
 * to ensure the correct programming language is selected for code generation.
 */

export enum ProjectType {
  CLI_TOOL = "cli_tool",
  WEB_APP = "web_app",
  API = "api",
  MOBILE_APP = "mobile_app",
  LIBRARY = "library",
  DESKTOP_APP = "desktop_app",
  DATA_ANALYSIS = "data_analysis",
  MACHINE_LEARNING = "machine_learning"
}

export function detectLanguage(description: string): string {
  /**
   * Detect the primary programming language from a project description.
   * 
   * @param description - Natural language project description
   * @returns Detected programming language (python, javascript, java, etc.)
   */
  const descriptionLower = description.toLowerCase();
  
  // Comprehensive language indicators
  const languageIndicators = {
    'python': [
      'python', 'py', 'pip', 'django', 'flask', 'fastapi', 'pandas', 'numpy', 
      'speech', 'audio', 'microphone', 'recognition', 'translation', 'persian', 
      'farsi', 'scikit-learn', 'tensorflow', 'pytorch', 'matplotlib', 'seaborn',
      'jupyter', 'anaconda', 'conda', 'virtualenv', 'pipenv', 'poetry'
    ],
    'javascript': [
      'javascript', 'js', 'node', 'nodejs', 'npm', 'react', 'vue', 'angular', 
      'express', 'next.js', 'nextjs', 'typescript', 'ts', 'webpack', 'babel',
      'jquery', 'lodash', 'moment', 'axios', 'fetch'
    ],
    'java': [
      'java', 'spring', 'springboot', 'maven', 'gradle', 'junit', 'hibernate',
      'jpa', 'servlet', 'jsp', 'android', 'kotlin'
    ],
    'go': [
      'go', 'golang', 'gin', 'echo', 'gorilla', 'cobra', 'viper'
    ],
    'rust': [
      'rust', 'cargo', 'actix', 'tokio', 'serde', 'clap'
    ],
    'csharp': [
      'c#', 'csharp', '.net', 'dotnet', 'asp.net', 'entity framework', 'linq'
    ],
    'php': [
      'php', 'laravel', 'symfony', 'composer', 'wordpress', 'drupal'
    ],
    'ruby': [
      'ruby', 'rails', 'gem', 'bundler', 'rake'
    ],
    'swift': [
      'swift', 'ios', 'xcode', 'cocoa', 'swiftui'
    ],
    'kotlin': [
      'kotlin', 'android', 'jetpack', 'compose'
    ]
  };
  
  let maxMatches = 0;
  let detectedLanguage = 'python'; // Default fallback
  
  for (const [language, indicators] of Object.entries(languageIndicators)) {
    const matches = indicators.filter(ind => descriptionLower.includes(ind)).length;
    if (matches > maxMatches) {
      maxMatches = matches;
      detectedLanguage = language;
    }
  }
  
  return detectedLanguage;
}

export function determineProjectType(description: string, detectedLanguage?: string): ProjectType {
  /**
   * Determine the project type based on description and detected language.
   * 
   * @param description - Natural language project description
   * @param detectedLanguage - Previously detected programming language
   * @returns ProjectType enum value
   */
  if (detectedLanguage === undefined) {
    detectedLanguage = detectLanguage(description);
  }
  
  const descriptionLower = description.toLowerCase();
  
  // Web application indicators
  if (descriptionLower.includes('web') || 
      descriptionLower.includes('website') || 
      descriptionLower.includes('frontend') ||
      descriptionLower.includes('react') ||
      descriptionLower.includes('vue') ||
      descriptionLower.includes('angular') ||
      descriptionLower.includes('dashboard') ||
      descriptionLower.includes('ui') ||
      descriptionLower.includes('user interface')) {
    return ProjectType.WEB_APP;
  }
  
  // API indicators
  if (descriptionLower.includes('api') || 
      descriptionLower.includes('backend') ||
      descriptionLower.includes('server') ||
      descriptionLower.includes('rest') ||
      descriptionLower.includes('graphql') ||
      descriptionLower.includes('microservice')) {
    return ProjectType.API;
  }
  
  // Mobile app indicators
  if (descriptionLower.includes('mobile') || 
      descriptionLower.includes('app') ||
      descriptionLower.includes('ios') ||
      descriptionLower.includes('android') ||
      descriptionLower.includes('flutter') ||
      descriptionLower.includes('react native')) {
    return ProjectType.MOBILE_APP;
  }
  
  // Data analysis indicators
  if (descriptionLower.includes('data') || 
      descriptionLower.includes('analysis') ||
      descriptionLower.includes('analytics') ||
      descriptionLower.includes('visualization') ||
      descriptionLower.includes('chart') ||
      descriptionLower.includes('plot')) {
    return ProjectType.DATA_ANALYSIS;
  }
  
  // Machine learning indicators
  if (descriptionLower.includes('machine learning') || 
      descriptionLower.includes('ml') ||
      descriptionLower.includes('ai') ||
      descriptionLower.includes('neural') ||
      descriptionLower.includes('model') ||
      descriptionLower.includes('training')) {
    return ProjectType.MACHINE_LEARNING;
  }
  
  // Library indicators
  if (descriptionLower.includes('library') || 
      descriptionLower.includes('package') ||
      descriptionLower.includes('module') ||
      descriptionLower.includes('sdk') ||
      descriptionLower.includes('framework')) {
    return ProjectType.LIBRARY;
  }
  
  // Desktop app indicators
  if (descriptionLower.includes('desktop') || 
      descriptionLower.includes('gui') ||
      descriptionLower.includes('application') ||
      descriptionLower.includes('window')) {
    return ProjectType.DESKTOP_APP;
  }
  
  // Default to CLI tool for scripts and utilities
  return ProjectType.CLI_TOOL;
}

export function getLanguageSpecificPrompt(description: string, language: string, projectType: ProjectType): string {
  /**
   * Generate a language-specific prompt for better code generation.
   * 
   * @param description - Original project description
   * @param language - Detected programming language
   * @param projectType - Determined project type
   * @returns Enhanced prompt for code generation
   */
  const basePrompt = `Create a ${projectType} project in ${language} for: ${description}`;
  
  const languageSpecificEnhancements = {
    'python': {
      [ProjectType.CLI_TOOL]: 'Include proper error handling, logging, and command-line argument parsing.',
      [ProjectType.WEB_APP]: 'Use Flask or FastAPI for the backend, include proper API documentation.',
      [ProjectType.API]: 'Use FastAPI with automatic API documentation, include proper validation.',
      [ProjectType.DATA_ANALYSIS]: 'Include pandas, numpy, and matplotlib for data processing and visualization.',
      [ProjectType.MACHINE_LEARNING]: 'Include scikit-learn or tensorflow, proper model training and evaluation.',
      [ProjectType.LIBRARY]: 'Include proper package structure, setup.py, and comprehensive documentation.'
    },
    'javascript': {
      [ProjectType.WEB_APP]: 'Use React with modern hooks, include responsive design and proper state management.',
      [ProjectType.API]: 'Use Express.js with proper middleware, include API documentation.',
      [ProjectType.CLI_TOOL]: 'Use Node.js with commander.js for CLI interface.',
      [ProjectType.LIBRARY]: 'Include proper package.json, TypeScript definitions, and documentation.'
    }
  };
  
  const enhancement = languageSpecificEnhancements[language as keyof typeof languageSpecificEnhancements]?.[projectType];
  
  return enhancement ? `${basePrompt}. ${enhancement}` : basePrompt;
}

// Export default functions for compatibility
export default {
  detectLanguage,
  determineProjectType,
  getLanguageSpecificPrompt,
  ProjectType
};
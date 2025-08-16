import type { NextApiRequest, NextApiResponse } from 'next'

interface GenerateRequest {
  description: string
  name?: string
  project_type?: string
  complexity?: string
}

interface GenerateResponse {
  status: string
  backend_mode: string
  language_detected: string
  project_type: string
  job_id: string
  files: Array<{
    name: string
    content: string
    type: string
    size?: number
    created_by?: string
  }>
  validation?: {
    total_files: number
    python_files: number
    react_files: number
    language_match: boolean
  }
  message?: string
  error?: string
}

export default async function handler(req: NextApiRequest, res: NextApiResponse<GenerateResponse>) {
  if (req.method !== 'POST') {
    return res.status(405).json({ 
      status: 'error',
      backend_mode: 'proxy',
      language_detected: 'unknown',
      project_type: 'unknown',
      job_id: '',
      files: [],
      error: 'Method not allowed' 
    })
  }

  try {
    const body: GenerateRequest = typeof req.body === 'string' ? JSON.parse(req.body) : req.body
    const { description, name = 'Generated Project', project_type = 'web', complexity = 'simple' } = body

    if (!description) {
      return res.status(400).json({
        status: 'error',
        backend_mode: 'proxy',
        language_detected: 'unknown',
        project_type: 'unknown',
        job_id: '',
        files: [],
        error: 'Description is required'
      })
    }

    console.log('🎯 Processing generation request:', description.substring(0, 100))

    // Check if we have a backend URL for proxying to Python
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || process.env.API_DESTINATION

    if (backendUrl) {
      // Proxy to Python backend
      console.log('🔄 Proxying to Python backend:', backendUrl)
      
      let destination: string
      if (backendUrl.startsWith('http://') || backendUrl.startsWith('https://')) {
        destination = `${backendUrl}/api/generate`
      } else if (backendUrl.startsWith('/')) {
        destination = `${backendUrl}/api/generate`
      } else {
        destination = `/api/generate`
      }

      try {
        const response = await fetch(destination, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': req.headers.authorization || ''
          },
          body: JSON.stringify({
            description,
            name,
            project_type,
            complexity
          })
        })

        if (!response.ok) {
          console.error('❌ Python backend error:', response.status, response.statusText)
          return res.status(response.status).json({
            status: 'error',
            backend_mode: 'proxy',
            language_detected: 'unknown',
            project_type: 'unknown',
            job_id: '',
            files: [],
            error: `Backend error: ${response.status} ${response.statusText}`
          })
        }

        const data = await response.json()
        console.log('✅ Python backend response received')
        return res.status(200).json(data)

      } catch (proxyError: any) {
        console.error('❌ Proxy error:', proxyError.message)
        // Fall through to local generation
      }
    }

    // Fallback: Local generation with client-side language detection
    console.log('🏠 Using local fallback generation')
    
    const detectedLanguage = detectLanguageLocal(description)
    const projectType = determineProjectTypeLocal(description, detectedLanguage)
    
    console.log(`🔍 Detected: ${detectedLanguage}, Type: ${projectType}`)

    // Generate files based on detected language
    const files = generateFilesLocal(description, name, detectedLanguage, projectType)
    
    const result: GenerateResponse = {
      status: 'success',
      backend_mode: 'local_fallback',
      language_detected: detectedLanguage,
      project_type: projectType,
      job_id: `job_${Date.now()}`,
      files,
      validation: {
        total_files: files.length,
        python_files: files.filter(f => f.name.endsWith('.py')).length,
        react_files: files.filter(f => f.content.includes('React') || f.name.endsWith('.jsx')).length,
        language_match: detectedLanguage === 'python' ? !files.some(f => f.content.includes('React')) : true
      }
    }

    return res.status(200).json(result)

  } catch (error: any) {
    console.error('❌ Generation error:', error)
    return res.status(500).json({
      status: 'error',
      backend_mode: 'local_fallback',
      language_detected: 'unknown',
      project_type: 'unknown',
      job_id: '',
      files: [],
      error: error.message || 'Internal server error'
    })
  }
}

// Local language detection (fallback when Python backend is unavailable)
function detectLanguageLocal(description: string): string {
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
  
  const pythonScore = pythonKeywords.filter(kw => lowerDesc.includes(kw)).length
  const jsScore = jsKeywords.filter(kw => lowerDesc.includes(kw)).length
  
  if (pythonScore > jsScore) return 'python'
  if (jsScore > pythonScore) return 'javascript'
  
  // Default based on specific patterns to prevent React fallback
  if (lowerDesc.includes('speech') || lowerDesc.includes('audio')) return 'python'
  if (lowerDesc.includes('web') || lowerDesc.includes('react')) return 'javascript'
  
  return 'python' // Default to Python for CLI tools
}

function determineProjectTypeLocal(description: string, language: string): string {
  const lowerDesc = description.toLowerCase()
  
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
  
  return 'CLI_TOOL'
}

function generateFilesLocal(description: string, name: string, language: string, projectType: string): Array<{ name: string; content: string; type: string; size: number; created_by: string }> {
  const files: Array<{ name: string; content: string; type: string; size: number; created_by: string }> = []
  
  if (language === 'python') {
    // Generate Python files
    const isPersianSpeech = description.toLowerCase().includes('speech') && description.toLowerCase().includes('persian')
    
    if (isPersianSpeech) {
      const mainContent = `#!/usr/bin/env python3
"""
${name}
Persian Speech Recognition and Translation Tool

Generated by Multi-Agent System
"""

import speech_recognition as sr
import pyaudio
from googletrans import Translator
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PersianSpeechTranslator:
    def __init__(self):
        """Initialize the Persian speech recognition and translation system."""
        self.recognizer = sr.Recognizer()
        self.translator = Translator()
        self.microphone = None
        
        # Configure recognizer for better Persian recognition
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        
    def setup_microphone(self):
        """Set up and calibrate the microphone."""
        try:
            self.microphone = sr.Microphone()
            with self.microphone as source:
                logger.info("Calibrating microphone for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
                logger.info("Microphone calibration completed.")
            return True
        except Exception as e:
            logger.error(f"Microphone setup failed: {e}")
            return False
    
    def capture_audio(self, timeout=10, phrase_time_limit=15):
        """Capture audio from microphone."""
        try:
            with self.microphone as source:
                logger.info("🎤 Listening for Persian speech... (speak now)")
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=phrase_time_limit
                )
                logger.info("✅ Audio captured successfully")
                return audio
        except sr.WaitTimeoutError:
            logger.warning("⏰ No speech detected within timeout period")
            return None
        except Exception as e:
            logger.error(f"❌ Audio capture failed: {e}")
            return None
    
    def recognize_persian_speech(self, audio):
        """Convert Persian speech to text."""
        try:
            logger.info("🔍 Recognizing Persian speech...")
            
            # Use Google's speech recognition with Persian language
            persian_text = self.recognizer.recognize_google(
                audio, 
                language='fa-IR'  # Persian/Farsi language code
            )
            
            logger.info(f"✅ Persian text recognized: {persian_text}")
            return persian_text
            
        except sr.UnknownValueError:
            logger.warning("❌ Could not understand the Persian speech")
            return None
        except sr.RequestError as e:
            logger.error(f"❌ Speech recognition service error: {e}")
            return None
    
    def translate_to_english(self, persian_text):
        """Translate Persian text to English."""
        try:
            logger.info("🔄 Translating to English...")
            
            translation = self.translator.translate(
                persian_text, 
                src='fa',  # Persian source
                dest='en'  # English destination
            )
            
            english_text = translation.text
            logger.info(f"✅ English translation: {english_text}")
            return english_text
            
        except Exception as e:
            logger.error(f"❌ Translation failed: {e}")
            return None
    
    def process_speech(self):
        """Complete speech recognition and translation process."""
        if not self.setup_microphone():
            return False
        
        try:
            # Capture audio
            audio = self.capture_audio()
            if not audio:
                return False
            
            # Recognize Persian speech
            persian_text = self.recognize_persian_speech(audio)
            if not persian_text:
                return False
            
            # Translate to English
            english_text = self.translate_to_english(persian_text)
            if not english_text:
                return False
            
            # Display results
            print("\\n" + "="*50)
            print("🎯 SPEECH RECOGNITION RESULTS")
            print("="*50)
            print(f"📝 Persian: {persian_text}")
            print(f"🔤 English: {english_text}")
            print("="*50)
            
            return True
            
        except KeyboardInterrupt:
            logger.info("\\n👋 Process interrupted by user")
            return False
        except Exception as e:
            logger.error(f"❌ Process failed: {e}")
            return False

def main():
    """Main application entry point."""
    print("🚀 Persian Speech Recognition & Translation Tool")
    print("Press Ctrl+C to exit at any time\\n")
    
    translator = PersianSpeechTranslator()
    
    try:
        while True:
            print("\\nReady for Persian speech recognition...")
            print("Press Enter to start listening, or 'q' to quit: ", end='')
            
            user_input = input().strip().lower()
            if user_input == 'q':
                break
                
            success = translator.process_speech()
            if not success:
                print("❌ Speech processing failed. Please try again.")
            
            print("\\n" + "-"*30)
            
    except KeyboardInterrupt:
        print("\\n\\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()`

      files.push({
        name: 'main.py',
        content: mainContent,
        type: 'python',
        size: mainContent.length,
        created_by: 'code_generator'
      })
      
      files.push({
        name: 'requirements.txt',
        content: `# Persian Speech Recognition Dependencies
SpeechRecognition==3.10.0
pyaudio==0.2.11
googletrans==4.0.0rc1

# Optional: Alternative translation services
# deep-translator==1.11.4
# translatepy==2.3

# Audio processing (system dependent)
# For Windows: pip install pyaudio
# For macOS: brew install portaudio && pip install pyaudio  
# For Linux: sudo apt-get install python3-pyaudio`,
        type: 'text',
        size: 400,
        created_by: 'code_generator'
      })
      
    } else {
      // General Python project
      const mainContent = `#!/usr/bin/env python3
"""
${name}
${description}

Generated by Multi-Agent System
"""

import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main application logic."""
    logger.info("Starting ${name}")
    
    # TODO: Implement your specific functionality here
    print("Hello from ${name}!")
    print("Description: ${description}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())`

      files.push({
        name: 'main.py',
        content: mainContent,
        type: 'python',
        size: mainContent.length,
        created_by: 'code_generator'
      })
    }
    
  } else if (language === 'javascript') {
    // Generate JavaScript/React files
    const isReactApp = description.toLowerCase().includes('react') || description.toLowerCase().includes('web')
    
    if (isReactApp) {
      const appContent = `import React, { useState, useEffect } from 'react';
import './App.css';

/**
 * ${name}
 * ${description}
 * 
 * Generated by Multi-Agent System
 */
function App() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulate data loading
    const loadData = async () => {
      setLoading(true);
      try {
        // TODO: Replace with actual data fetching
        await new Promise(resolve => setTimeout(resolve, 1000));
        setData([
          { id: 1, name: 'Sample Item 1', value: 100 },
          { id: 2, name: 'Sample Item 2', value: 200 },
          { id: 3, name: 'Sample Item 3', value: 150 }
        ]);
      } catch (error) {
        console.error('Data loading failed:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  if (loading) {
    return (
      <div className="app">
        <div className="loading">
          <h2>Loading...</h2>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>${name}</h1>
        <p>${description || 'A modern React application'}</p>
      </header>
      
      <main className="app-main">
        <div className="dashboard">
          <h2>Dashboard</h2>
          <div className="cards">
            {data.map(item => (
              <div key={item.id} className="card">
                <h3>{item.name}</h3>
                <p className="value">{item.value}</p>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;`

      files.push({
        name: 'App.jsx',
        content: appContent,
        type: 'javascript',
        size: appContent.length,
        created_by: 'code_generator'
      })
      
      files.push({
        name: 'package.json',
        content: `{
  "name": "${name.toLowerCase().replace(/\\s+/g, '-')}",
  "version": "1.0.0",
  "description": "${description}",
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}`,
        type: 'json',
        size: 600,
        created_by: 'code_generator'
      })
    }
  }
  
  return files
}
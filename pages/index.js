import Head from 'next/head'
import { useState, useEffect } from 'react'

export default function Home() {
  const [vibePrompt, setVibePrompt] = useState('')
  const [projectType, setProjectType] = useState('web')
  const [framework, setFramework] = useState('react')
  const [isGenerating, setIsGenerating] = useState(false)
  const [currentJob, setCurrentJob] = useState(null)
  const [jobStatus, setJobStatus] = useState(null)
  const [generatedFiles, setGeneratedFiles] = useState([])

  const submitVibePrompt = async () => {
    if (!vibePrompt.trim() || vibePrompt.length < 10) {
      alert('Please enter a vibe prompt of at least 10 characters')
      return
    }

    setIsGenerating(true)
    setCurrentJob(null)
    setJobStatus(null)
    setGeneratedFiles([])

    try {
      const response = await fetch('/api/vibe-coding', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          vibe_prompt: vibePrompt,
          project_type: projectType,
          framework: framework
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const result = await response.json()
      setCurrentJob(result.job_id)
      
      // Start monitoring
      monitorJob(result.job_id)

    } catch (error) {
      alert(`Failed to start generation: ${error.message}`)
      setIsGenerating(false)
    }
  }

  const monitorJob = async (jobId) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`/api/vibe-coding/status/${jobId}`)
        
        if (response.ok) {
          const status = await response.json()
          setJobStatus(status)

          if (status.status === 'completed') {
            clearInterval(pollInterval)
            setIsGenerating(false)
            
            // Get generated files
            const filesResponse = await fetch(`/api/vibe-coding/files/${jobId}`)
            if (filesResponse.ok) {
              const filesData = await filesResponse.json()
              setGeneratedFiles(filesData.files || [])
            }
          } else if (status.status === 'failed') {
            clearInterval(pollInterval)
            setIsGenerating(false)
            alert(`Generation failed: ${status.message}`)
          }
        }
      } catch (error) {
        console.error('Monitoring error:', error)
      }
    }, 3000)
  }

  const downloadProject = async () => {
    if (!currentJob) return

    try {
      const response = await fetch(`/api/download/${currentJob}`)
      
      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `vibe-project-${currentJob}.zip`
        a.click()
        window.URL.revokeObjectURL(url)
      } else {
        alert('Download failed')
      }
    } catch (error) {
      alert(`Download error: ${error.message}`)
    }
  }

  return (
    <>
      <Head>
        <title>Vibe Coding Platform</title>
        <meta name="description" content="Transform creative prompts into functional software with AI agents" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 text-white">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center mb-12">
            <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              🎨 Vibe Coding Platform
            </h1>
            <p className="text-xl text-gray-300 max-w-2xl mx-auto">
              Transform your creative vision into functional software using sophisticated AI agents
            </p>
          </div>

          <div className="max-w-4xl mx-auto">
            <div className="bg-gray-800 rounded-2xl p-8 shadow-2xl mb-8">
              <h2 className="text-2xl font-semibold mb-6">Create Your Project</h2>
              
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium mb-2">Vibe Prompt</label>
                  <textarea
                    value={vibePrompt}
                    onChange={(e) => setVibePrompt(e.target.value)}
                    placeholder="Describe your project vibe... e.g., 'Create a cozy coffee shop website with warm colors and easy navigation'"
                    className="w-full h-32 px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    disabled={isGenerating}
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Project Type</label>
                    <select
                      value={projectType}
                      onChange={(e) => setProjectType(e.target.value)}
                      className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
                      disabled={isGenerating}
                    >
                      <option value="web">Web Application</option>
                      <option value="landing">Landing Page</option>
                      <option value="blog">Blog</option>
                      <option value="dashboard">Dashboard</option>
                      <option value="portfolio">Portfolio</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">Framework</label>
                    <select
                      value={framework}
                      onChange={(e) => setFramework(e.target.value)}
                      className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
                      disabled={isGenerating}
                    >
                      <option value="react">React</option>
                      <option value="vue">Vue.js</option>
                      <option value="vanilla">Vanilla JS</option>
                    </select>
                  </div>
                </div>

                <button
                  onClick={submitVibePrompt}
                  disabled={isGenerating || !vibePrompt.trim()}
                  className="w-full py-4 px-6 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:from-gray-600 disabled:to-gray-600 rounded-lg font-semibold text-lg transition-all duration-200 disabled:cursor-not-allowed"
                >
                  {isGenerating ? '🤖 AI Agents Working...' : '🚀 Generate Project'}
                </button>
              </div>
            </div>

            {jobStatus && (
              <div className="bg-gray-800 rounded-2xl p-8 shadow-2xl mb-8">
                <h3 className="text-xl font-semibold mb-4">🤖 AI Agents Progress</h3>
                
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-300">{jobStatus.message}</span>
                    <span className="text-blue-400 font-semibold">{jobStatus.progress}%</span>
                  </div>

                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div 
                      className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${jobStatus.progress}%` }}
                    ></div>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
                    {Object.entries(jobStatus.agent_status || {}).map(([agent, status]) => (
                      <div key={agent} className={`p-3 rounded-lg text-center ${
                        status === 'completed' ? 'bg-green-600' :
                        status === 'processing' ? 'bg-yellow-600' : 'bg-gray-600'
                      }`}>
                        <div className="text-sm font-medium capitalize">{agent}</div>
                        <div className="text-xs mt-1">
                          {status === 'completed' ? '✅ Done' :
                           status === 'processing' ? '⚡ Working' : '⏳ Pending'}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {generatedFiles.length > 0 && (
              <div className="bg-gray-800 rounded-2xl p-8 shadow-2xl">
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-xl font-semibold">📁 Generated Files ({generatedFiles.length})</h3>
                  <button
                    onClick={downloadProject}
                    className="px-6 py-2 bg-green-600 hover:bg-green-700 rounded-lg font-medium transition-colors"
                  >
                    📥 Download Project
                  </button>
                </div>

                <div className="space-y-2">
                  {generatedFiles.map((file, index) => (
                    <div key={index} className="flex justify-between items-center p-3 bg-gray-700 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <span className="text-2xl">
                          {file.type === 'typescript-react' ? '⚛️' :
                           file.type === 'stylesheet' ? '🎨' :
                           file.type === 'configuration' ? '⚙️' :
                           file.type === 'documentation' ? '📄' : '📄'}
                        </span>
                        <span className="font-medium">{file.name}</span>
                      </div>
                      <span className="text-gray-400 text-sm">
                        {file.size < 1024 ? `${file.size}B` : `${Math.round(file.size/1024)}KB`}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <style jsx global>{`
        * {
          box-sizing: border-box;
          padding: 0;
          margin: 0;
        }

        html,
        body {
          max-width: 100vw;
          overflow-x: hidden;
          font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Oxygen,
            Ubuntu, Cantarell, Fira Sans, Droid Sans, Helvetica Neue, sans-serif;
        }

        a {
          color: inherit;
          text-decoration: none;
        }
      `}</style>
    </>
  )
}
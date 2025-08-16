'use client'

import React, { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Monitor,
  Smartphone,
  Tablet,
  Laptop,
  RefreshCw,
  ExternalLink,
  Download,
  Share2,
  Settings,
  Eye,
  Code,
  Terminal,
  Globe,
  Zap,
  Play,
  Square,
  AlertCircle,
  CheckCircle,
  Clock,
  Maximize2,
  RotateCcw
} from 'lucide-react'
import { VirtualFile, PreviewData, SandboxEnvironment } from '@/types'

interface LivePreviewProps {
  files: VirtualFile[]
  previewData?: PreviewData
  onRefresh: () => void
  className?: string
}

type ViewportSize = {
  name: string
  width: number
  height: number
  icon: React.ComponentType<any>
}

const viewportSizes: ViewportSize[] = [
  { name: 'Desktop', width: 1920, height: 1080, icon: Monitor },
  { name: 'Laptop', width: 1366, height: 768, icon: Laptop },
  { name: 'Tablet', width: 768, height: 1024, icon: Tablet },
  { name: 'Mobile', width: 375, height: 667, icon: Smartphone },
]

type PreviewMode = 'iframe' | 'split' | 'code' | 'fullscreen'

export default function LivePreview({
  files,
  previewData,
  onRefresh,
  className = '',
}: LivePreviewProps) {
  const [selectedViewport, setSelectedViewport] = useState(viewportSizes[0])
  const [previewMode, setPreviewMode] = useState<PreviewMode>('iframe')
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [sandboxUrl, setSandboxUrl] = useState<string | null>(null)
  const [logs, setLogs] = useState<Array<{
    id: string
    level: 'log' | 'warn' | 'error' | 'info'
    message: string
    timestamp: Date
  }>>([])
  const [showConsole, setShowConsole] = useState(false)
  const [orientation, setOrientation] = useState<'portrait' | 'landscape'>('portrait')
  
  const iframeRef = useRef<HTMLIFrameElement>(null)

  // Generate preview content
  const generatePreviewContent = () => {
    const htmlFile = files.find(f => f.path.endsWith('.html') || f.name === 'index.html')
    const cssFiles = files.filter(f => f.path.endsWith('.css'))
    const jsFiles = files.filter(f => f.path.endsWith('.js') || f.path.endsWith('.jsx'))

    if (!htmlFile) {
      // Generate basic HTML if none exists
      return `
        <!DOCTYPE html>
        <html lang="en">
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>Live Preview</title>
          <style>
            ${cssFiles.map(f => f.content).join('\n')}
          </style>
        </head>
        <body>
          <div id="root">
            <h1>Welcome to your project!</h1>
            <p>Your generated files will appear here.</p>
          </div>
          <script>
            // Console capture
            const originalLog = console.log;
            const originalWarn = console.warn;
            const originalError = console.error;
            
            window.addEventListener('message', (event) => {
              if (event.data.type === 'console') {
                switch(event.data.level) {
                  case 'log': originalLog(...event.data.args); break;
                  case 'warn': originalWarn(...event.data.args); break;
                  case 'error': originalError(...event.data.args); break;
                }
              }
            });
            
            console.log = (...args) => {
              parent.postMessage({type: 'console', level: 'log', args}, '*');
              originalLog(...args);
            };
            console.warn = (...args) => {
              parent.postMessage({type: 'console', level: 'warn', args}, '*');
              originalWarn(...args);
            };
            console.error = (...args) => {
              parent.postMessage({type: 'console', level: 'error', args}, '*');
              originalError(...args);
            };
            
            ${jsFiles.map(f => f.content).join('\n')}
          </script>
        </body>
        </html>
      `
    }

    // Inject CSS and JS into existing HTML
    let content = htmlFile.content
    
    // Inject CSS
    if (cssFiles.length > 0) {
      const cssContent = cssFiles.map(f => f.content).join('\n')
      const styleTag = `<style>\n${cssContent}\n</style>`
      content = content.replace('</head>', `${styleTag}\n</head>`)
    }

    // Inject JS with console capture
    if (jsFiles.length > 0) {
      const jsContent = jsFiles.map(f => f.content).join('\n')
      const scriptTag = `
        <script>
          // Console capture for parent window
          const originalLog = console.log;
          const originalWarn = console.warn;
          const originalError = console.error;
          
          console.log = (...args) => {
            parent.postMessage({type: 'console', level: 'log', args}, '*');
            originalLog(...args);
          };
          console.warn = (...args) => {
            parent.postMessage({type: 'console', level: 'warn', args}, '*');
            originalWarn(...args);
          };
          console.error = (...args) => {
            parent.postMessage({type: 'console', level: 'error', args}, '*');
            originalError(...args);
          };
          
          ${jsContent}
        </script>
      `
      content = content.replace('</body>', `${scriptTag}\n</body>`)
    }

    return content
  }

  // Handle iframe messages
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.data.type === 'console') {
        const newLog = {
          id: `log-${Date.now()}-${Math.random()}`,
          level: event.data.level,
          message: event.data.args.join(' '),
          timestamp: new Date(),
        }
        setLogs(prev => [...prev.slice(-99), newLog]) // Keep last 100 logs
      }
    }

    window.addEventListener('message', handleMessage)
    return () => window.removeEventListener('message', handleMessage)
  }, [])

  // Refresh preview
  const handleRefresh = async () => {
    setIsRefreshing(true)
    onRefresh()
    
    // Reload iframe
    if (iframeRef.current) {
      const content = generatePreviewContent()
      const blob = new Blob([content], { type: 'text/html' })
      const url = URL.createObjectURL(blob)
      setSandboxUrl(url)
      
      // Clean up previous URL
      return () => URL.revokeObjectURL(url)
    }

    setTimeout(() => setIsRefreshing(false), 1000)
  }

  // Initialize preview
  useEffect(() => {
    if (files.length > 0) {
      handleRefresh()
    }
  }, [files])

  const getViewportDimensions = () => {
    if (orientation === 'landscape' && selectedViewport.name !== 'Desktop') {
      return {
        width: selectedViewport.height,
        height: selectedViewport.width,
      }
    }
    return {
      width: selectedViewport.width,
      height: selectedViewport.height,
    }
  }

  const dimensions = getViewportDimensions()
  const scale = Math.min(1, Math.min(800 / dimensions.width, 600 / dimensions.height))

  return (
    <div className={`flex flex-col h-full bg-slate-900/30 border border-slate-700/30 rounded-xl overflow-hidden ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-700/30 bg-slate-800/50">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <Eye className="w-5 h-5 text-purple-400" />
            <h3 className="text-lg font-semibold text-white">Live Preview</h3>
          </div>
          
          {/* Status Indicator */}
          <div className="flex items-center space-x-2">
            {previewData?.status === 'loading' && (
              <div className="flex items-center space-x-2 text-yellow-400">
                <Clock className="w-4 h-4 animate-spin" />
                <span className="text-sm">Loading...</span>
              </div>
            )}
            {previewData?.status === 'ready' && (
              <div className="flex items-center space-x-2 text-green-400">
                <CheckCircle className="w-4 h-4" />
                <span className="text-sm">Ready</span>
              </div>
            )}
            {previewData?.status === 'error' && (
              <div className="flex items-center space-x-2 text-red-400">
                <AlertCircle className="w-4 h-4" />
                <span className="text-sm">Error</span>
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* Viewport Selector */}
          <div className="flex items-center space-x-1 bg-slate-700/50 rounded-lg p-1">
            {viewportSizes.map((viewport) => {
              const Icon = viewport.icon
              return (
                <button
                  key={viewport.name}
                  onClick={() => setSelectedViewport(viewport)}
                  className={`p-2 rounded transition-colors ${
                    selectedViewport.name === viewport.name
                      ? 'bg-purple-500 text-white'
                      : 'text-slate-400 hover:text-white hover:bg-slate-600/50'
                  }`}
                  title={`${viewport.name} (${viewport.width}×${viewport.height})`}
                >
                  <Icon className="w-4 h-4" />
                </button>
              )
            })}
          </div>

          {/* Orientation Toggle */}
          {selectedViewport.name !== 'Desktop' && (
            <button
              onClick={() => setOrientation(orientation === 'portrait' ? 'landscape' : 'portrait')}
              className="p-2 rounded hover:bg-slate-700/50 transition-colors"
              title={`Rotate to ${orientation === 'portrait' ? 'landscape' : 'portrait'}`}
            >
              <RotateCcw className="w-4 h-4 text-slate-400" />
            </button>
          )}

          {/* Console Toggle */}
          <button
            onClick={() => setShowConsole(!showConsole)}
            className={`p-2 rounded transition-colors ${
              showConsole 
                ? 'bg-purple-500/20 text-purple-400' 
                : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
            }`}
            title="Toggle console"
          >
            <Terminal className="w-4 h-4" />
          </button>

          {/* Refresh Button */}
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="p-2 rounded hover:bg-slate-700/50 transition-colors disabled:opacity-50"
            title="Refresh preview"
          >
            <RefreshCw className={`w-4 h-4 text-slate-400 ${isRefreshing ? 'animate-spin' : ''}`} />
          </button>

          {/* External Link */}
          {sandboxUrl && (
            <button
              onClick={() => window.open(sandboxUrl, '_blank')}
              className="p-2 rounded hover:bg-slate-700/50 transition-colors"
              title="Open in new tab"
            >
              <ExternalLink className="w-4 h-4 text-slate-400" />
            </button>
          )}
        </div>
      </div>

      {/* Preview Area */}
      <div className="flex-1 flex flex-col">
        {files.length === 0 ? (
          <div className="flex-1 flex items-center justify-center text-slate-400">
            <div className="text-center">
              <Globe className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <h4 className="text-lg font-medium mb-2">No Preview Available</h4>
              <p className="text-sm">Generate a project to see the live preview</p>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center p-4 bg-slate-800/20">
            {/* Device Frame */}
            <div 
              className="relative bg-white rounded-lg shadow-2xl overflow-hidden border border-slate-600"
              style={{
                width: dimensions.width * scale,
                height: dimensions.height * scale,
                transform: `scale(${scale})`,
                transformOrigin: 'center',
              }}
            >
              {/* Device Header */}
              {selectedViewport.name !== 'Desktop' && (
                <div className="h-6 bg-slate-800 flex items-center justify-center">
                  <div className="flex space-x-1">
                    <div className="w-1 h-1 bg-slate-600 rounded-full"></div>
                    <div className="w-1 h-1 bg-slate-600 rounded-full"></div>
                    <div className="w-1 h-1 bg-slate-600 rounded-full"></div>
                  </div>
                </div>
              )}

              {/* Preview Frame */}
              <div className="relative w-full h-full">
                {sandboxUrl ? (
                  <iframe
                    ref={iframeRef}
                    src={sandboxUrl}
                    className="w-full h-full border-0"
                    sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals"
                    title="Live Preview"
                  />
                ) : (
                  <div className="flex items-center justify-center h-full bg-slate-100">
                    <div className="text-center text-slate-600">
                      <Zap className="w-8 h-8 mx-auto mb-2" />
                      <p>Preparing preview...</p>
                    </div>
                  </div>
                )}

                {/* Loading Overlay */}
                {isRefreshing && (
                  <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                    <div className="bg-white rounded-lg p-4 flex items-center space-x-3">
                      <RefreshCw className="w-5 h-5 animate-spin text-purple-500" />
                      <span className="text-slate-700">Refreshing...</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Console */}
        <AnimatePresence>
          {showConsole && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 200, opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="border-t border-slate-700/30 bg-slate-900/50"
            >
              <div className="h-full flex flex-col">
                {/* Console Header */}
                <div className="flex items-center justify-between p-3 border-b border-slate-700/30">
                  <div className="flex items-center space-x-2">
                    <Terminal className="w-4 h-4 text-slate-400" />
                    <span className="text-sm font-medium text-white">Console</span>
                    {logs.length > 0 && (
                      <span className="text-xs text-slate-500">({logs.length})</span>
                    )}
                  </div>
                  <button
                    onClick={() => setLogs([])}
                    className="text-xs text-slate-400 hover:text-white transition-colors"
                  >
                    Clear
                  </button>
                </div>

                {/* Console Content */}
                <div className="flex-1 overflow-auto p-3 font-mono text-sm">
                  {logs.length === 0 ? (
                    <div className="text-slate-500 italic">Console output will appear here...</div>
                  ) : (
                    <div className="space-y-1">
                      {logs.map((log) => (
                        <div
                          key={log.id}
                          className={`flex items-start space-x-2 ${
                            log.level === 'error' ? 'text-red-400' :
                            log.level === 'warn' ? 'text-yellow-400' :
                            log.level === 'info' ? 'text-blue-400' : 'text-slate-300'
                          }`}
                        >
                          <span className="text-xs text-slate-500 mt-0.5 flex-shrink-0">
                            {log.timestamp.toLocaleTimeString()}
                          </span>
                          <span className="break-all">{log.message}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Footer Info */}
      <div className="px-4 py-2 border-t border-slate-700/30 bg-slate-800/50 text-xs text-slate-500">
        <div className="flex justify-between items-center">
          <span>
            {selectedViewport.name} • {dimensions.width}×{dimensions.height}
            {scale < 1 && ` • ${Math.round(scale * 100)}% scale`}
          </span>
          <span>
            {files.length} file{files.length !== 1 ? 's' : ''} loaded
          </span>
        </div>
      </div>
    </div>
  )
}
'use client'

import React, { useRef, useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import Editor, { loader, OnMount } from '@monaco-editor/react'
import * as monaco from 'monaco-editor'
import { 
  Save, 
  Copy, 
  Download, 
  Maximize2, 
  Minimize2, 
  Settings, 
  Users,
  Search,
  Replace,
  Zap,
  Eye,
  EyeOff,
  Edit,
  AlertCircle,
  X
} from 'lucide-react'
import { CodeFile, EditorConfig, Collaborator } from '@/types'

// Configure Monaco loader
loader.config({
  paths: {
    vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.45.0/min/vs'
  }
})

interface MonacoEditorProps {
  file: CodeFile | null
  onContentChange: (content: string) => void
  onSave: () => void
  config: EditorConfig
  collaborators?: Collaborator[]
  isReadOnly?: boolean
  className?: string
}

const languageMap: Record<string, string> = {
  'js': 'javascript',
  'jsx': 'javascript',
  'ts': 'typescript',
  'tsx': 'typescript',
  'html': 'html',
  'htm': 'html',
  'css': 'css',
  'scss': 'scss',
  'sass': 'sass',
  'less': 'less',
  'json': 'json',
  'md': 'markdown',
  'mdx': 'markdown',
  'py': 'python',
  'rb': 'ruby',
  'php': 'php',
  'java': 'java',
  'go': 'go',
  'rs': 'rust',
  'cpp': 'cpp',
  'c': 'c',
  'sh': 'shell',
  'yml': 'yaml',
  'yaml': 'yaml',
  'xml': 'xml',
  'sql': 'sql',
  'dockerfile': 'dockerfile',
}

const getLanguageFromFile = (filename: string): string => {
  const ext = filename.split('.').pop()?.toLowerCase()
  return languageMap[ext || ''] || 'plaintext'
}

export default function MonacoEditor({
  file,
  onContentChange,
  onSave,
  config,
  collaborators = [],
  isReadOnly = false,
  className = '',
}: MonacoEditorProps) {
  const editorRef = useRef<monaco.editor.IStandaloneCodeEditor | null>(null)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [showMinimap, setShowMinimap] = useState(config.minimap)
  const [showCollaborators, setShowCollaborators] = useState(true)
  const [isSearchOpen, setIsSearchOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [replaceQuery, setReplaceQuery] = useState('')

  const language = file ? getLanguageFromFile(file.path) : 'plaintext'

  // Handle editor mount
  const handleEditorDidMount: OnMount = (editor, monaco) => {
    editorRef.current = editor

    // Set up keyboard shortcuts
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
      onSave()
    })

    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyF, () => {
      setIsSearchOpen(true)
    })

    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyH, () => {
      setIsSearchOpen(true)
    })

    // Set up error handling
    monaco.editor.onDidCreateModel((model) => {
      model.onDidChangeContent(() => {
        const markers = monaco.editor.getModelMarkers({ resource: model.uri })
        console.log('Editor markers:', markers)
      })
    })

    // Auto-format on paste
    editor.onDidPaste(() => {
      if (config.autoFormat) {
        editor.getAction('editor.action.formatDocument')?.run()
      }
    })

    // Set initial focus
    editor.focus()
  }

  // Update editor options when config changes
  useEffect(() => {
    if (editorRef.current) {
      editorRef.current.updateOptions({
        fontSize: config.fontSize,
        fontFamily: config.fontFamily,
        tabSize: config.tabSize,
        wordWrap: config.wordWrap ? 'on' : 'off',
        minimap: { enabled: showMinimap },
        lineNumbers: config.lineNumbers ? 'on' : 'off',
        readOnly: isReadOnly,
        theme: config.theme === 'dark' ? 'vs-dark' : 'vs',
      })
    }
  }, [config, showMinimap, isReadOnly])

  // Handle content change
  const handleContentChange = (value: string | undefined) => {
    if (value !== undefined) {
      onContentChange(value)
    }
  }

  // Search and replace functionality
  const handleSearch = () => {
    if (editorRef.current && searchQuery) {
      editorRef.current.getAction('actions.find')?.run()
    }
  }

  const handleReplace = () => {
    if (editorRef.current && searchQuery) {
      editorRef.current.getAction('editor.action.startFindReplaceAction')?.run()
    }
  }

  // Format document
  const formatDocument = () => {
    if (editorRef.current) {
      editorRef.current.getAction('editor.action.formatDocument')?.run()
    }
  }

  // Copy content to clipboard
  const copyToClipboard = async () => {
    if (file?.content) {
      try {
        await navigator.clipboard.writeText(file.content)
        console.log('Content copied to clipboard')
      } catch (err) {
        console.error('Failed to copy content:', err)
      }
    }
  }

  // Download file
  const downloadFile = () => {
    if (file) {
      const blob = new Blob([file.content], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = file.path.split('/').pop() || 'file.txt'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    }
  }

  if (!file) {
    return (
      <div className={`flex items-center justify-center h-full bg-slate-900/30 border border-slate-700/30 rounded-xl ${className}`}>
        <div className="text-center text-slate-400">
          <Edit className="w-16 h-16 mx-auto mb-4 opacity-50" />
          <h3 className="text-lg font-medium mb-2">No file selected</h3>
          <p className="text-sm">Select a file from the explorer to start editing</p>
        </div>
      </div>
    )
  }

  return (
    <div className={`relative flex flex-col h-full bg-slate-900/30 border border-slate-700/30 rounded-xl overflow-hidden ${className} ${isFullscreen ? 'fixed inset-0 z-50' : ''}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-slate-700/30 bg-slate-800/50">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-white truncate max-w-48">
              {file.path.split('/').pop()}
            </span>
            {file.isDirty && (
              <div className="w-2 h-2 bg-orange-400 rounded-full" title="Unsaved changes" />
            )}
          </div>
          
          {/* Language Badge */}
          <span className="px-2 py-1 text-xs bg-purple-500/20 text-purple-300 rounded-full">
            {language}
          </span>
        </div>

        <div className="flex items-center space-x-2">
          {/* Collaborators */}
          {collaborators.length > 0 && showCollaborators && (
            <div className="flex items-center space-x-1">
              {collaborators.slice(0, 3).map((collaborator) => (
                <div
                  key={collaborator.id}
                  className="w-6 h-6 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center text-xs text-white font-medium"
                  title={collaborator.name}
                >
                  {collaborator.name[0]}
                </div>
              ))}
              {collaborators.length > 3 && (
                <div className="w-6 h-6 rounded-full bg-slate-600 flex items-center justify-center text-xs text-white">
                  +{collaborators.length - 3}
                </div>
              )}
            </div>
          )}

          {/* Action Buttons */}
          <button
            onClick={() => setIsSearchOpen(!isSearchOpen)}
            className="p-1.5 rounded hover:bg-slate-700/50 transition-colors"
            title="Search (Ctrl+F)"
          >
            <Search className="w-4 h-4 text-slate-400" />
          </button>

          <button
            onClick={formatDocument}
            className="p-1.5 rounded hover:bg-slate-700/50 transition-colors"
            title="Format document"
          >
            <Zap className="w-4 h-4 text-slate-400" />
          </button>

          <button
            onClick={copyToClipboard}
            className="p-1.5 rounded hover:bg-slate-700/50 transition-colors"
            title="Copy to clipboard"
          >
            <Copy className="w-4 h-4 text-slate-400" />
          </button>

          <button
            onClick={downloadFile}
            className="p-1.5 rounded hover:bg-slate-700/50 transition-colors"
            title="Download file"
          >
            <Download className="w-4 h-4 text-slate-400" />
          </button>

          <button
            onClick={() => setShowSettings(!showSettings)}
            className="p-1.5 rounded hover:bg-slate-700/50 transition-colors"
            title="Editor settings"
          >
            <Settings className="w-4 h-4 text-slate-400" />
          </button>

          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="p-1.5 rounded hover:bg-slate-700/50 transition-colors"
            title={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
          >
            {isFullscreen ? (
              <Minimize2 className="w-4 h-4 text-slate-400" />
            ) : (
              <Maximize2 className="w-4 h-4 text-slate-400" />
            )}
          </button>
        </div>
      </div>

      {/* Search Bar */}
      {isSearchOpen && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="p-3 border-b border-slate-700/30 bg-slate-800/50"
        >
          <div className="flex items-center space-x-2">
            <div className="flex-1 flex space-x-2">
              <input
                type="text"
                placeholder="Search..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                className="flex-1 px-3 py-1.5 bg-slate-700 border border-slate-600 rounded text-white text-sm focus:border-purple-500 focus:outline-none"
              />
              <input
                type="text"
                placeholder="Replace..."
                value={replaceQuery}
                onChange={(e) => setReplaceQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleReplace()}
                className="flex-1 px-3 py-1.5 bg-slate-700 border border-slate-600 rounded text-white text-sm focus:border-purple-500 focus:outline-none"
              />
            </div>
            <button
              onClick={handleSearch}
              className="px-3 py-1.5 bg-purple-500 hover:bg-purple-600 rounded text-white text-sm transition-colors"
            >
              Find
            </button>
            <button
              onClick={handleReplace}
              className="px-3 py-1.5 bg-purple-500 hover:bg-purple-600 rounded text-white text-sm transition-colors"
            >
              Replace
            </button>
            <button
              onClick={() => setIsSearchOpen(false)}
              className="p-1.5 rounded hover:bg-slate-700/50 transition-colors"
            >
              <X className="w-4 h-4 text-slate-400" />
            </button>
          </div>
        </motion.div>
      )}

      {/* Settings Panel */}
      {showSettings && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="p-3 border-b border-slate-700/30 bg-slate-800/50"
        >
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={showMinimap}
                onChange={(e) => setShowMinimap(e.target.checked)}
                className="rounded border-slate-600 bg-slate-700 text-purple-500 focus:ring-purple-500"
              />
              <span className="text-sm text-slate-300">Minimap</span>
            </label>
            
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={showCollaborators}
                onChange={(e) => setShowCollaborators(e.target.checked)}
                className="rounded border-slate-600 bg-slate-700 text-purple-500 focus:ring-purple-500"
              />
              <span className="text-sm text-slate-300">Collaborators</span>
            </label>

            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={config.autoFormat}
                onChange={(e) => console.log('Auto format:', e.target.checked)}
                className="rounded border-slate-600 bg-slate-700 text-purple-500 focus:ring-purple-500"
              />
              <span className="text-sm text-slate-300">Auto Format</span>
            </label>

            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={config.wordWrap}
                onChange={(e) => console.log('Word wrap:', e.target.checked)}
                className="rounded border-slate-600 bg-slate-700 text-purple-500 focus:ring-purple-500"
              />
              <span className="text-sm text-slate-300">Word Wrap</span>
            </label>
          </div>
        </motion.div>
      )}

      {/* Editor */}
      <div className="flex-1 relative">
        <Editor
          height="100%"
          language={language}
          value={file.content}
          onChange={handleContentChange}
          onMount={handleEditorDidMount}
          theme={config.theme === 'dark' ? 'vs-dark' : 'vs'}
          options={{
            fontSize: config.fontSize,
            fontFamily: config.fontFamily,
            tabSize: config.tabSize,
            wordWrap: config.wordWrap ? 'on' : 'off',
            minimap: { enabled: showMinimap },
            lineNumbers: config.lineNumbers ? 'on' : 'off',
            readOnly: isReadOnly,
            automaticLayout: true,
            scrollBeyondLastLine: false,
            renderWhitespace: 'selection',
            bracketPairColorization: { enabled: true },
            guides: {
              indentation: true,
              bracketPairs: true,
            },
            suggest: {
              showKeywords: true,
              showSnippets: true,
            },
            quickSuggestions: {
              other: true,
              comments: true,
              strings: true,
            },
            folding: true,
            foldingStrategy: 'indentation',
            showFoldingControls: 'always',
            renderValidationDecorations: 'on',
          }}
        />

        {/* Error Indicators */}
        {file.errors.length > 0 && (
          <div className="absolute bottom-4 right-4 bg-red-500/20 border border-red-500/50 rounded-lg p-2">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 text-red-400" />
              <span className="text-sm text-red-300">
                {file.errors.length} error{file.errors.length > 1 ? 's' : ''}
              </span>
            </div>
          </div>
        )}

        {/* Save Indicator */}
        {file.isDirty && (
          <div className="absolute top-4 right-4 bg-orange-500/20 border border-orange-500/50 rounded-lg p-2">
            <div className="flex items-center space-x-2">
              <Save className="w-4 h-4 text-orange-400" />
              <span className="text-sm text-orange-300">Unsaved changes</span>
            </div>
          </div>
        )}
      </div>

      {/* Status Bar */}
      <div className="flex items-center justify-between px-3 py-2 border-t border-slate-700/30 bg-slate-800/50 text-xs text-slate-400">
        <div className="flex items-center space-x-4">
          <span>Line 1, Column 1</span>
          <span>{language}</span>
          <span>{file.content.split('\n').length} lines</span>
          <span>{file.content.length} characters</span>
        </div>
        
        <div className="flex items-center space-x-2">
          {file.errors.length > 0 && (
            <span className="text-red-400">{file.errors.length} errors</span>
          )}
          {file.warnings.length > 0 && (
            <span className="text-yellow-400">{file.warnings.length} warnings</span>
          )}
          <span>UTF-8</span>
        </div>
      </div>
    </div>
  )
}
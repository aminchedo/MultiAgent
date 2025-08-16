'use client'
import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Copy, Eye, ExternalLink } from 'lucide-react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'

interface FileItem {
  path: string
  content: string
  language: string
  size: number
  created_by: string
}

interface CodePreviewProps {
  file: FileItem | null
  jobId: string
}

export function CodePreview({ file, jobId }: CodePreviewProps) {
  const [copied, setCopied] = useState(false)

  const copyToClipboard = async () => {
    if (!file) return
    
    try {
      await navigator.clipboard.writeText(file.content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      console.error('Failed to copy:', error)
    }
  }

  const getLanguageFromPath = (path: string) => {
    const ext = path.split('.').pop()?.toLowerCase()
    switch (ext) {
      case 'js': return 'javascript'
      case 'ts': return 'typescript'
      case 'jsx': return 'jsx'
      case 'tsx': return 'tsx'
      case 'py': return 'python'
      case 'html': return 'html'
      case 'css': return 'css'
      case 'json': return 'json'
      case 'md': return 'markdown'
      default: return 'text'
    }
  }

  const previewInNewTab = () => {
    if (!file) return
    
    const blob = new Blob([file.content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    window.open(url, '_blank')
  }

  if (!file) {
    return (
      <Card className="h-full bg-gray-900/50 border-gray-700">
        <div className="p-8 text-center text-gray-500">
          <Eye className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>Select a file to preview</p>
        </div>
      </Card>
    )
  }

  return (
    <Card className="h-full bg-gray-900/50 border-gray-700 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-700 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h3 className="font-mono text-sm text-white">{file.path}</h3>
          <Badge variant="secondary" className="text-xs">
            {file.language}
          </Badge>
          <Badge variant="outline" className="text-xs">
            by {file.created_by}
          </Badge>
        </div>
        
        <div className="flex gap-2">
          <Button size="sm" variant="ghost" onClick={copyToClipboard}>
            <Copy className="w-4 h-4" />
            {copied ? 'Copied!' : 'Copy'}
          </Button>
          
          <Button size="sm" variant="ghost" onClick={previewInNewTab}>
            <ExternalLink className="w-4 h-4" />
          </Button>
        </div>
      </div>
      
      {/* Content */}
      <div className="flex-1 overflow-hidden">
        <SyntaxHighlighter
          language={getLanguageFromPath(file.path)}
          style={vscDarkPlus}
          customStyle={{
            margin: 0,
            padding: '1rem',
            background: 'transparent',
            fontSize: '0.875rem',
            height: '100%',
            overflow: 'auto'
          }}
          showLineNumbers
          wrapLines
        >
          {file.content}
        </SyntaxHighlighter>
      </div>
    </Card>
  )
}
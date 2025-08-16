'use client'
import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  File, 
  Folder, 
  Download, 
  Eye, 
  Code, 
  FileText, 
  Image as ImageIcon,
  PlayCircle 
} from 'lucide-react'
interface FileItem {
  path: string
  content: string
  language: string
  size: number
  created_by: string
  is_binary: boolean
  type: 'file' | 'folder'
}

interface FileExplorerProps {
  jobId: string
  files: FileItem[]
  onFileSelect: (file: FileItem) => void
  selectedFile?: FileItem
}

export function FileExplorer({ jobId, files, onFileSelect, selectedFile }: FileExplorerProps) {
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set())

  const getFileIcon = (file: FileItem) => {
    if (file.type === 'folder') return <Folder className="w-4 h-4" />
    
    const ext = file.path.split('.').pop()?.toLowerCase()
    switch (ext) {
      case 'js':
      case 'ts':
      case 'jsx':
      case 'tsx':
      case 'py':
        return <Code className="w-4 h-4 text-blue-400" />
      case 'md':
      case 'txt':
        return <FileText className="w-4 h-4 text-green-400" />
      case 'png':
      case 'jpg':
      case 'svg':
        return <ImageIcon className="w-4 h-4 text-purple-400" />
      case 'html':
        return <PlayCircle className="w-4 h-4 text-orange-400" />
      default:
        return <File className="w-4 h-4 text-gray-400" />
    }
  }

  const buildFileTree = (files: FileItem[]) => {
    const tree: any = {}
    
    files.forEach(file => {
      const parts = file.path.split('/')
      let current = tree
      
      parts.forEach((part, index) => {
        if (index === parts.length - 1) {
          current[part] = file
        } else {
          if (!current[part]) {
            current[part] = {}
          }
          current = current[part]
        }
      })
    })
    
    return tree
  }

  const renderFileTree = (tree: any, path = '') => {
    return Object.entries(tree).map(([name, item]: [string, any]) => {
      const fullPath = path ? `${path}/${name}` : name
      
      if (item.path) {
        // It's a file
        return (
          <div
            key={fullPath}
            onClick={() => onFileSelect(item)}
            className={`flex items-center gap-2 p-2 rounded cursor-pointer hover:bg-gray-700/50 transition-colors ${
              selectedFile?.path === item.path ? 'bg-purple-600/20 border border-purple-500/30' : ''
            }`}
          >
            {getFileIcon(item)}
            <span className="text-sm font-mono">{name}</span>
            <span className="text-xs text-gray-500 ml-auto">
              {Math.round(item.size / 1024)}KB
            </span>
          </div>
        )
      } else {
        // It's a folder
        const isExpanded = expandedFolders.has(fullPath)
        
        return (
          <div key={fullPath}>
            <div
              onClick={() => {
                const newExpanded = new Set(expandedFolders)
                if (isExpanded) {
                  newExpanded.delete(fullPath)
                } else {
                  newExpanded.add(fullPath)
                }
                setExpandedFolders(newExpanded)
              }}
              className="flex items-center gap-2 p-2 rounded cursor-pointer hover:bg-gray-700/50 transition-colors"
            >
              <Folder className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
              <span className="text-sm font-semibold">{name}</span>
            </div>
            
            {isExpanded && (
              <div className="ml-4 border-l border-gray-600 pl-2">
                {renderFileTree(item, fullPath)}
              </div>
            )}
          </div>
        )
      }
    })
  }

  const downloadFile = async (file: FileItem) => {
    try {
      const blob = new Blob([file.content], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      
      const a = document.createElement('a')
      a.href = url
      a.download = file.path.split('/').pop() || 'file'
      a.click()
      
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Failed to download file:', error)
    }
  }

  const downloadAllFiles = async () => {
    try {
      const { default: JSZip } = await import('jszip')
      const zip = new JSZip()
      
      files.forEach(file => {
        if (file.type === 'file') {
          zip.file(file.path, file.content)
        }
      })
      
      const blob = await zip.generateAsync({ type: 'blob' })
      const url = URL.createObjectURL(blob)
      
      const a = document.createElement('a')
      a.href = url
      a.download = `project-${jobId}.zip`
      a.click()
      
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Failed to download project:', error)
    }
  }

  const fileTree = buildFileTree(files.filter(f => f.type === 'file'))

  return (
    <Card className="h-full bg-gray-900/50 border-gray-700">
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-white">Project Files</h3>
          <div className="flex gap-2">
            {selectedFile && (
              <Button
                size="sm"
                variant="ghost"
                onClick={() => downloadFile(selectedFile)}
              >
                <Download className="w-4 h-4" />
              </Button>
            )}
            
            <Button
              size="sm"
              variant="ghost"
              onClick={downloadAllFiles}
              disabled={files.length === 0}
            >
              <Download className="w-4 h-4 mr-1" />
              All
            </Button>
          </div>
        </div>
      </div>
      
      <ScrollArea className="h-96">
        <div className="p-4">
          {files.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              <File className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>No files generated yet</p>
            </div>
          ) : (
            renderFileTree(fileTree)
          )}
        </div>
      </ScrollArea>
    </Card>
  )
}
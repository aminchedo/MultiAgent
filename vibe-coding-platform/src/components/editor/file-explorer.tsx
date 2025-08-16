'use client'

import React, { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Folder,
  FolderOpen,
  File,
  Search,
  Plus,
  MoreHorizontal,
  Edit3,
  Trash2,
  Copy,
  Download,
  FileText,
  Image,
  Code,
  Settings,
  Database,
  Globe,
  Smartphone,
  Package,
  ChevronRight,
  ChevronDown,
  Filter,
} from 'lucide-react'
import { VirtualFile } from '@/types'

interface FileExplorerProps {
  files: VirtualFile[]
  selectedFile: string | null
  onFileSelect: (path: string) => void
  onFileCreate: (path: string, isDirectory: boolean) => void
  onFileDelete: (path: string) => void
  onFileRename: (oldPath: string, newPath: string) => void
  className?: string
}

const getFileIcon = (fileName: string, isDirectory: boolean) => {
  if (isDirectory) return Folder
  
  const ext = fileName.split('.').pop()?.toLowerCase()
  
  switch (ext) {
    case 'js':
    case 'jsx':
    case 'ts':
    case 'tsx':
    case 'vue':
    case 'svelte':
      return Code
    case 'json':
    case 'xml':
    case 'yaml':
    case 'yml':
      return Database
    case 'html':
    case 'htm':
      return Globe
    case 'css':
    case 'scss':
    case 'sass':
    case 'less':
      return Palette
    case 'md':
    case 'mdx':
    case 'txt':
      return FileText
    case 'png':
    case 'jpg':
    case 'jpeg':
    case 'gif':
    case 'svg':
    case 'webp':
      return Image
    case 'package':
    case 'lock':
      return Package
    default:
      return File
  }
}

const getFileColor = (fileName: string, isDirectory: boolean) => {
  if (isDirectory) return 'text-blue-400'
  
  const ext = fileName.split('.').pop()?.toLowerCase()
  
  switch (ext) {
    case 'js':
    case 'jsx':
      return 'text-yellow-400'
    case 'ts':
    case 'tsx':
      return 'text-blue-400'
    case 'vue':
      return 'text-green-400'
    case 'svelte':
      return 'text-orange-400'
    case 'json':
      return 'text-yellow-400'
    case 'html':
    case 'htm':
      return 'text-orange-400'
    case 'css':
    case 'scss':
    case 'sass':
      return 'text-pink-400'
    case 'md':
    case 'mdx':
      return 'text-purple-400'
    case 'png':
    case 'jpg':
    case 'jpeg':
    case 'gif':
    case 'svg':
    case 'webp':
      return 'text-green-400'
    default:
      return 'text-slate-400'
  }
}

interface FileTreeItemProps {
  file: VirtualFile
  level: number
  isSelected: boolean
  onSelect: (path: string) => void
  onToggle: (path: string) => void
  expandedFolders: Set<string>
  searchQuery: string
}

function FileTreeItem({
  file,
  level,
  isSelected,
  onSelect,
  onToggle,
  expandedFolders,
  searchQuery,
}: FileTreeItemProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [newName, setNewName] = useState(file.name)
  const [showMenu, setShowMenu] = useState(false)

  const Icon = getFileIcon(file.name, file.isDirectory)
  const color = getFileColor(file.name, file.isDirectory)
  const isExpanded = expandedFolders.has(file.path)
  const isVisible = !searchQuery || file.name.toLowerCase().includes(searchQuery.toLowerCase())

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (file.isDirectory) {
      onToggle(file.path)
    }
  }

  const handleSelect = () => {
    onSelect(file.path)
  }

  const handleRename = () => {
    setIsEditing(false)
    // Call rename callback here
    console.log('Rename:', file.path, 'to', newName)
  }

  if (!isVisible) return null

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      className="relative"
    >
      {/* File/Folder Row */}
      <motion.div
        className={`flex items-center space-x-2 px-2 py-1 rounded-lg cursor-pointer group transition-all ${
          isSelected 
            ? 'bg-purple-500/20 border-l-2 border-purple-500' 
            : 'hover:bg-slate-800/50'
        }`}
        style={{ paddingLeft: `${level * 16 + 8}px` }}
        onClick={handleSelect}
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.99 }}
      >
        {/* Expand/Collapse Button */}
        {file.isDirectory && (
          <button
            onClick={handleToggle}
            className="p-0.5 rounded hover:bg-slate-700/50 transition-colors"
          >
            {isExpanded ? (
              <ChevronDown className="w-4 h-4 text-slate-400" />
            ) : (
              <ChevronRight className="w-4 h-4 text-slate-400" />
            )}
          </button>
        )}

        {/* File Icon */}
        <div className={`flex-shrink-0 ${color}`}>
          {file.isDirectory && isExpanded ? (
            <FolderOpen className="w-4 h-4" />
          ) : (
            <Icon className="w-4 h-4" />
          )}
        </div>

        {/* File Name */}
        {isEditing ? (
          <input
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onBlur={handleRename}
            onKeyPress={(e) => e.key === 'Enter' && handleRename()}
            className="flex-1 bg-slate-800 border border-slate-600 rounded px-2 py-0.5 text-sm text-white focus:outline-none focus:border-purple-500"
            autoFocus
          />
        ) : (
          <span className="flex-1 text-sm text-slate-200 truncate">
            {file.name}
          </span>
        )}

        {/* File Size */}
        {!file.isDirectory && (
          <span className="text-xs text-slate-500">
            {(file.size / 1024).toFixed(1)}KB
          </span>
        )}

        {/* Context Menu Button */}
        <button
          onClick={(e) => {
            e.stopPropagation()
            setShowMenu(!showMenu)
          }}
          className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-slate-700/50 transition-all"
        >
          <MoreHorizontal className="w-3 h-3 text-slate-400" />
        </button>
      </motion.div>

      {/* Context Menu */}
      <AnimatePresence>
        {showMenu && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -10 }}
            className="absolute right-0 top-8 z-50 bg-slate-800 border border-slate-700 rounded-lg shadow-lg py-1 min-w-[120px]"
          >
            <button
              onClick={() => {
                setIsEditing(true)
                setShowMenu(false)
              }}
              className="w-full flex items-center space-x-2 px-3 py-2 text-sm text-slate-300 hover:bg-slate-700/50 transition-colors"
            >
              <Edit3 className="w-3 h-3" />
              <span>Rename</span>
            </button>
            <button
              onClick={() => {
                console.log('Copy:', file.path)
                setShowMenu(false)
              }}
              className="w-full flex items-center space-x-2 px-3 py-2 text-sm text-slate-300 hover:bg-slate-700/50 transition-colors"
            >
              <Copy className="w-3 h-3" />
              <span>Copy</span>
            </button>
            {!file.isDirectory && (
              <button
                onClick={() => {
                  console.log('Download:', file.path)
                  setShowMenu(false)
                }}
                className="w-full flex items-center space-x-2 px-3 py-2 text-sm text-slate-300 hover:bg-slate-700/50 transition-colors"
              >
                <Download className="w-3 h-3" />
                <span>Download</span>
              </button>
            )}
            <div className="border-t border-slate-700 my-1" />
            <button
              onClick={() => {
                console.log('Delete:', file.path)
                setShowMenu(false)
              }}
              className="w-full flex items-center space-x-2 px-3 py-2 text-sm text-red-400 hover:bg-red-500/10 transition-colors"
            >
              <Trash2 className="w-3 h-3" />
              <span>Delete</span>
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Children (if expanded) */}
      <AnimatePresence>
        {file.isDirectory && isExpanded && file.children && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            {file.children
              .sort((a, b) => {
                if (a.isDirectory && !b.isDirectory) return -1
                if (!a.isDirectory && b.isDirectory) return 1
                return a.name.localeCompare(b.name)
              })
              .map((child) => (
                <FileTreeItem
                  key={child.path}
                  file={child}
                  level={level + 1}
                  isSelected={child.path === onSelect}
                  onSelect={onSelect}
                  onToggle={onToggle}
                  expandedFolders={expandedFolders}
                  searchQuery={searchQuery}
                />
              ))}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

export default function FileExplorer({
  files,
  selectedFile,
  onFileSelect,
  onFileCreate,
  onFileDelete,
  onFileRename,
  className = '',
}: FileExplorerProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set())
  const [viewMode, setViewMode] = useState<'tree' | 'list'>('tree')
  const [sortBy, setSortBy] = useState<'name' | 'size' | 'modified'>('name')
  const [showNewFileMenu, setShowNewFileMenu] = useState(false)

  // Build file tree structure
  const fileTree = useMemo(() => {
    const tree: VirtualFile[] = []
    const pathMap = new Map<string, VirtualFile>()

    // Sort files by path depth to build tree properly
    const sortedFiles = [...files].sort((a, b) => {
      const aDepth = a.path.split('/').length
      const bDepth = b.path.split('/').length
      return aDepth - bDepth
    })

    sortedFiles.forEach(file => {
      const pathParts = file.path.split('/')
      const fileName = pathParts[pathParts.length - 1]
      const parentPath = pathParts.slice(0, -1).join('/')

      const fileNode: VirtualFile = {
        ...file,
        name: fileName,
        children: file.isDirectory ? [] : undefined,
      }

      pathMap.set(file.path, fileNode)

      if (parentPath === '' || parentPath === '.') {
        tree.push(fileNode)
      } else {
        const parent = pathMap.get(parentPath)
        if (parent && parent.children) {
          parent.children.push(fileNode)
        }
      }
    })

    return tree
  }, [files])

  const toggleFolder = (path: string) => {
    const newExpanded = new Set(expandedFolders)
    if (newExpanded.has(path)) {
      newExpanded.delete(path)
    } else {
      newExpanded.add(path)
    }
    setExpandedFolders(newExpanded)
  }

  const createNewFile = (isDirectory: boolean) => {
    const name = isDirectory ? 'New Folder' : 'new-file.txt'
    const path = selectedFile ? `${selectedFile}/${name}` : name
    onFileCreate(path, isDirectory)
    setShowNewFileMenu(false)
  }

  return (
    <div className={`h-full flex flex-col bg-slate-900/30 border border-slate-700/30 rounded-xl ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-slate-700/30">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-white">Files</h3>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setViewMode(viewMode === 'tree' ? 'list' : 'tree')}
              className="p-2 rounded-lg hover:bg-slate-800/50 transition-colors"
              title={`Switch to ${viewMode === 'tree' ? 'list' : 'tree'} view`}
            >
              <Filter className="w-4 h-4 text-slate-400" />
            </button>
            <div className="relative">
              <button
                onClick={() => setShowNewFileMenu(!showNewFileMenu)}
                className="p-2 rounded-lg bg-purple-500/20 hover:bg-purple-500/30 transition-colors"
                title="Create new file or folder"
              >
                <Plus className="w-4 h-4 text-purple-400" />
              </button>
              
              <AnimatePresence>
                {showNewFileMenu && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95, y: -10 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: -10 }}
                    className="absolute right-0 top-12 z-50 bg-slate-800 border border-slate-700 rounded-lg shadow-lg py-1 min-w-[140px]"
                  >
                    <button
                      onClick={() => createNewFile(false)}
                      className="w-full flex items-center space-x-2 px-3 py-2 text-sm text-slate-300 hover:bg-slate-700/50 transition-colors"
                    >
                      <File className="w-3 h-3" />
                      <span>New File</span>
                    </button>
                    <button
                      onClick={() => createNewFile(true)}
                      className="w-full flex items-center space-x-2 px-3 py-2 text-sm text-slate-300 hover:bg-slate-700/50 transition-colors"
                    >
                      <Folder className="w-3 h-3" />
                      <span>New Folder</span>
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search files..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-white placeholder-slate-400 focus:border-purple-500/50 focus:outline-none transition-colors"
          />
        </div>
      </div>

      {/* File Tree */}
      <div className="flex-1 overflow-auto p-2">
        {fileTree.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-400">
            <Folder className="w-12 h-12 mb-4 opacity-50" />
            <p className="text-center">No files yet</p>
            <p className="text-sm text-slate-500 mt-1">
              Generate a project to see files here
            </p>
          </div>
        ) : (
          <div className="space-y-1">
            {fileTree
              .sort((a, b) => {
                if (a.isDirectory && !b.isDirectory) return -1
                if (!a.isDirectory && b.isDirectory) return 1
                
                switch (sortBy) {
                  case 'size':
                    return b.size - a.size
                  case 'modified':
                    return new Date(b.lastModified).getTime() - new Date(a.lastModified).getTime()
                  default:
                    return a.name.localeCompare(b.name)
                }
              })
              .map((file) => (
                <FileTreeItem
                  key={file.path}
                  file={file}
                  level={0}
                  isSelected={file.path === selectedFile}
                  onSelect={onFileSelect}
                  onToggle={toggleFolder}
                  expandedFolders={expandedFolders}
                  searchQuery={searchQuery}
                />
              ))}
          </div>
        )}
      </div>

      {/* Footer Stats */}
      <div className="p-3 border-t border-slate-700/30 text-xs text-slate-500">
        <div className="flex justify-between">
          <span>{files.length} files</span>
          <span>
            {(files.reduce((total, file) => total + file.size, 0) / 1024).toFixed(1)}KB total
          </span>
        </div>
      </div>
    </div>
  )
}
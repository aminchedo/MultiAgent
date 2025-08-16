'use client'
import { useEffect, useState, useCallback } from 'react'
import { useJobStore } from '@/stores/job-store'

interface WebSocketMessage {
  type: string
  job_id: string
  agent_type?: string
  data: any
  timestamp: string
}

export function useEnhancedWebSocket(jobId: string) {
  const [ws, setWs] = useState<WebSocket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [connectionAttempts, setConnectionAttempts] = useState(0)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  
  const { 
    updateAgentProgress, 
    addFile, 
    updateFile, 
    setJobStatus,
    addAgentMessage 
  } = useJobStore()

  const connect = useCallback(() => {
    if (ws?.readyState === WebSocket.OPEN) return

    try {
      const websocket = new WebSocket(`ws://localhost:8000/ws?job_id=${jobId}`)
      
      websocket.onopen = () => {
        console.log('✅ WebSocket connected')
        setIsConnected(true)
        setConnectionAttempts(0)
        setWs(websocket)
      }

      websocket.onmessage = (event) => {
        const message: WebSocketMessage = JSON.parse(event.data)
        setLastMessage(message)
        
        console.log('📨 WebSocket message:', message)
        
        switch (message.type) {
          case 'agent_progress':
            updateAgentProgress(message.agent_type!, {
              progress: message.data.progress,
              status: message.data.status,
              currentTask: message.data.current_task,
              messages: message.data.messages || []
            })
            break
            
          case 'agent_message':
            addAgentMessage(message.agent_type!, message.data.message)
            break
            
          case 'file_generated':
            addFile({
              path: message.data.path,
              content: message.data.content,
              language: message.data.language,
              size: message.data.size,
              created_by: message.data.created_by,
              is_binary: message.data.is_binary || false,
              type: 'file'
            })
            break
            
          case 'file_updated':
            updateFile(message.data.path, message.data.content)
            break
            
          case 'job_status':
            setJobStatus(message.data.status)
            break
            
          case 'job_complete':
            setJobStatus('completed')
            console.log('🎉 Job completed!', message.data)
            break
            
          case 'error':
            console.error('❌ Agent error:', message.data)
            break
        }
      }

      websocket.onclose = () => {
        console.log('🔌 WebSocket disconnected')
        setIsConnected(false)
        setWs(null)
        
        // Auto-reconnect with exponential backoff
        if (connectionAttempts < 5) {
          const delay = Math.pow(2, connectionAttempts) * 1000
          setTimeout(() => {
            setConnectionAttempts(prev => prev + 1)
            connect()
          }, delay)
        }
      }

      websocket.onerror = (error) => {
        console.error('❌ WebSocket error:', error)
        setIsConnected(false)
      }

    } catch (error) {
      console.error('❌ Failed to connect WebSocket:', error)
    }
  }, [jobId, connectionAttempts])

  useEffect(() => {
    if (jobId) {
      connect()
    }

    return () => {
      if (ws) {
        ws.close()
      }
    }
  }, [jobId, connect])

  const sendMessage = useCallback((message: any) => {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message))
    }
  }, [ws])

  return {
    isConnected,
    lastMessage,
    connectionAttempts,
    sendMessage,
    reconnect: connect
  }
}
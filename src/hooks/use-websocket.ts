import { useEffect, useState } from 'react'
import { WebSocketManager } from '../lib/websocket/manager'
import { useJobStore } from '../stores/job-store'

export const useWebSocket = (jobId?: string) => {
	const [ws] = useState(() => new WebSocketManager())
	const [isConnected, setIsConnected] = useState(false)
	const { updateAgentProgress, addFile, setConnected } = useJobStore()

	useEffect(() => {
		const connect = async () => {
			try {
				await ws.connect(jobId)
				setIsConnected(true)
				setConnected(true)

				ws.subscribe('agent_message', (message: any) => {
					const agent = message.agent || 'unknown'
					updateAgentProgress(agent, {
						...(message.metadata || {}),
						status: 'running',
						message: message.content
					})
				})

				ws.subscribe('progress', (message: any) => {
					const agent = message.agent || 'workflow'
					updateAgentProgress(agent, {
						...(message.metadata || {}),
						status: 'running',
						progress: message.metadata?.progress
					})
				})

				ws.subscribe('file_generated', (message: any) => {
					addFile(message.data)
				})
			} catch (error) {
				console.error('WebSocket connection failed:', error)
			}
		}

		connect()
	}, [jobId])

	return { isConnected }
}
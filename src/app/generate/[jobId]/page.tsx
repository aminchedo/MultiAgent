'use client'
import { useParams } from 'next/navigation'
import { useWebSocket } from '@/hooks/use-websocket'
import { useJobStore } from '@/stores/job-store'
import { AgentCard } from '@/components/agents/AgentCard'

export default function GeneratePage() {
	const params = useParams()
	const jobId = (params as any)?.jobId as string
	const { isConnected } = useWebSocket(jobId)
	const { agentProgress, files } = useJobStore()

	const agentKeys = ['planner', 'code_generator', 'tester', 'doc_generator', 'reviewer']

	return (
		<div className="container mx-auto py-8">
			<h1 className="text-3xl font-bold mb-8">Generating Your Project</h1>
			<div className="mb-6">
				<span className={`inline-block px-3 py-1 rounded-full text-sm ${
					isConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
				}`}> {isConnected ? 'Connected' : 'Disconnected'} </span>
			</div>
			<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
				{agentKeys.map(agentType => (
					<AgentCard
						key={agentType}
						agentType={agentType}
						progress={agentProgress[agentType]?.progress || 0}
						status={agentProgress[agentType]?.status || 'waiting'}
						currentTask={agentProgress[agentType]?.current_task || agentProgress[agentType]?.message || 'Waiting to start...'}
					/>
				))}
			</div>
			{files.length > 0 && (
				<div>
					<h2 className="text-2xl font-bold mb-4">Generated Files</h2>
					<div className="space-y-2">
						{files.map((file, index) => (
							<div key={index} className="p-3 border rounded">
								<span className="font-mono">{file.path}</span>
							</div>
						))}
					</div>
				</div>
			)}
		</div>
	)
}
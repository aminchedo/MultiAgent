'use client'

interface AgentCardProps {
	agentType: string
	progress: number
	status: string
	currentTask: string
}

export const AgentCard: React.FC<AgentCardProps> = ({ 
	agentType, 
	progress, 
	status, 
	currentTask 
}) => {
	return (
		<div className="p-4 border rounded">
			<div className="flex items-center gap-3 mb-3">
				<div className="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center text-white">
					{agentType[0]?.toUpperCase()}
				</div>
				<div>
					<h3 className="font-semibold">{agentType} Agent</h3>
					<p className="text-sm text-gray-600">{status}</p>
				</div>
			</div>
			<div className="w-full bg-gray-200 rounded h-2 mb-2">
				<div className="bg-blue-600 h-2 rounded" style={{ width: `${progress}%` }} />
			</div>
			<p className="text-sm text-gray-700">{currentTask}</p>
		</div>
	)
}
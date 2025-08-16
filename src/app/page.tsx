'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { VibeInput } from '@/components/vibe/VibeInput'
import { VibeCodingAPI } from '@/lib/api/client'

export default function HomePage() {
	const router = useRouter()
	const [api] = useState(() => new VibeCodingAPI())

	const ensureAuth = async () => {
		try {
			if (!api.getToken()) {
				await api.login('admin', 'admin')
			}
		} catch (e) {
			console.error('Auth failed', e)
		}
	}

	const handleVibeSubmit = async (description: string) => {
		try {
			await ensureAuth()
			const job = await api.createJob({
				name: 'Vibe Project',
				description,
				project_type: 'web_app',
				languages: ['python', 'typescript'],
				frameworks: ['fastapi', 'nextjs'],
				complexity: 'simple',
				features: ['realtime', 'auth'],
				mode: 'full'
			})
			router.push(`/generate/${job.job_id}`)
		} catch (error) {
			console.error('Failed to create job:', error)
		}
	}

	return (
		<div className="container mx-auto py-12">
			<div className="text-center mb-12">
				<h1 className="text-4xl font-bold mb-4">Vibe Coding Platform</h1>
				<p className="text-xl text-gray-600">Describe your vibe, get a complete project</p>
			</div>
			<div className="max-w-2xl mx-auto">
				<VibeInput onSubmit={handleVibeSubmit} />
			</div>
		</div>
	)
}
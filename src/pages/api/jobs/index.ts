import type { NextApiRequest, NextApiResponse } from 'next'
import { jobsStore, type JobRecord } from './store'

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
	if (req.method !== 'POST') {
		return res.status(405).json({ error: 'Method not allowed' })
	}

	try {
		const backend = process.env.NEXT_PUBLIC_API_URL
		const body = typeof req.body === 'string' ? JSON.parse(req.body || '{}') : req.body || {}
		const description: string = body?.prompt || body?.description || 'AI generated project'

		if (backend) {
			// Proxy to real backend endpoint mapping
			const resp = await fetch(`${backend}/api/generate`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ prompt: description })
			})
			if (!resp.ok) {
				return res.status(resp.status).json({ error: `Upstream error ${resp.status}` })
			}
			const data = await resp.json()
			return res.status(200).json({ job_id: data.job_id })
		}

		const id = `job_${Math.random().toString(36).slice(2, 10)}`
		const createdAt = Date.now()
		const job: JobRecord = { id, description, createdAt }
		jobsStore.set(id, job)
		return res.status(200).json({ job_id: id })
	} catch (err: any) {
		return res.status(500).json({ error: err?.message || 'Failed to create job' })
	}
}
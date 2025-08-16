"use client"
import { useEffect, useState } from 'react'

export default function HealthBanner() {
	const [status, setStatus] = useState<'ok' | 'error' | 'loading'>('loading')

	useEffect(() => {
		let mounted = true
		fetch('/api/health')
			.then((r) => {
				if (!mounted) return
				setStatus(r.ok ? 'ok' : 'error')
			})
			.catch(() => {
				if (!mounted) return
				setStatus('error')
			})
		return () => {
			mounted = false
		}
	}, [])

	if (status === 'loading') return null

	return (
		<div className={`w-full text-center py-2 ${status === 'ok' ? 'bg-green-700/40 text-green-200' : 'bg-red-800/40 text-red-200'}`}>
			{status === 'ok' ? '✅ Connected to backend' : '⚠ Backend unreachable, using mock data'}
		</div>
	)
}
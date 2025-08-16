import { VibeCodingAPI } from './src/lib/api/client'

async function testBackend() {
	const api = new VibeCodingAPI()
	try {
		const res = await fetch('http://localhost:8000/health')
		console.log('Backend /health status:', res.status)
		console.log('Backend /health JSON:', await res.json())

		// Optional: authenticate and try a dry-run generate
		await api.login('admin', 'admin')
		const job = await api.createJob({
			name: 'Test Job',
			description: 'Build a simple React app',
			project_type: 'web_app',
			languages: ['python'],
			frameworks: [],
			complexity: 'simple',
			features: [],
			mode: 'dry'
		})
		console.log('Job response:', job)
	} catch (error) {
		console.error('Backend connection failed:', error)
	}
}

testBackend()
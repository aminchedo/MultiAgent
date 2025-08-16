/************************************
 * Next.js configuration
 ************************************/

/** @type {import('next').NextConfig} */
const nextConfig = {
	reactStrictMode: true,
	async rewrites() {
		// Get the backend API URL from environment or default to localhost:8000
		const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
		
		return [
			{
				source: '/api/:path*',
				destination: `${apiUrl}/api/:path*`
			}
		]
	},
	async headers() {
		return [
			{
				source: '/ws/:path*',
				headers: [
					{ key: 'Connection', value: 'Upgrade' },
					{ key: 'Upgrade', value: 'websocket' }
				]
			}
		]
	}
}

module.exports = nextConfig
/************************************
 * Next.js configuration
 ************************************/

/** @type {import('next').NextConfig} */
const nextConfig = {
	reactStrictMode: true,
	async rewrites() {
		// Ensure we have a valid API URL
		const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
		
		// Ensure the destination starts with a valid prefix
		const destination = apiUrl.startsWith('http://') || apiUrl.startsWith('https://') || apiUrl.startsWith('/')
			? `${apiUrl}/api/:path*`
			: `/${apiUrl}/api/:path*`;
			
		return [
			{
				source: '/api/:path*',
				destination: destination
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
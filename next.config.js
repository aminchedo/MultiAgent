/************************************
 * Next.js configuration
 ************************************/

/** @type {import('next').NextConfig} */
const nextConfig = {
	reactStrictMode: true,
	async rewrites() {
		// Ensure we have a valid API URL with safe fallback
		const apiUrl = process.env.NEXT_PUBLIC_API_URL || process.env.API_DESTINATION
		
		if (!apiUrl) {
			// No external API configured; use local Next.js API routes
			return []
		}
		
		// Normalize the destination to ensure it starts with a valid prefix
		let destination
		if (apiUrl.startsWith('http://') || apiUrl.startsWith('https://')) {
			destination = `${apiUrl}/api/:path*`
		} else if (apiUrl.startsWith('/')) {
			destination = `${apiUrl}/api/:path*`
		} else {
			// Fallback to local API if the URL is malformed
			return []
		}
			
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
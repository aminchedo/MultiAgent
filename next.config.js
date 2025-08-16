/************************************
 * Next.js configuration
 ************************************/

/** @type {import('next').NextConfig} */
const nextConfig = {
	reactStrictMode: true,
	async rewrites() {
		const apiUrl = process.env.NEXT_PUBLIC_API_URL || process.env.API_DESTINATION
		if (!apiUrl) return []
		let destination
		if (apiUrl.startsWith('http://') || apiUrl.startsWith('https://')) {
			destination = `${apiUrl}/api/:path*`
		} else if (apiUrl.startsWith('/')) {
			destination = `${apiUrl}/api/:path*`
		} else {
			return []
		}
		return [
			{ source: '/api/:path*', destination }
		]
	},
	async redirects() {
		return [
			{ source: '/legacy', destination: '/legacy/index.html', permanent: false }
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
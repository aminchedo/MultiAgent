/************************************
 * Next.js configuration
 ************************************/

/** @type {import('next').NextConfig} */
const nextConfig = {
	reactStrictMode: true,
	async rewrites() {
		return [
			{
				source: '/api/:path*',
				destination: process.env.NEXT_PUBLIC_API_URL + '/api/:path*'
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
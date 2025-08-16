import './globals.css'
import HealthBanner from '@/components/health/HealthBanner'

export default function RootLayout({ children }: { children: React.ReactNode }) {
	return (
		<html lang="en">
			<body>
				<HealthBanner />
				{children}
			</body>
		</html>
	)
}
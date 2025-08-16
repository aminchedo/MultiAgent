'use client'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/use-auth'

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
	const { user, refreshToken } = useAuth()
	const [isChecking, setIsChecking] = useState(true)
	const router = useRouter()

	useEffect(() => {
		const checkAuth = async () => {
			if (!user) {
				const ok = await refreshToken()
				if (!ok) {
					router.push('/')
					return
				}
			}
			setIsChecking(false)
		}
		checkAuth()
	}, [user])

	if (isChecking) return null
	return <>{children}</>
}

export default ProtectedRoute
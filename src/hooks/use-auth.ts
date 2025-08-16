import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { VibeCodingAPI } from '@/lib/api/client'
import { useAuthStore } from '@/stores/auth-store'

export const useAuth = () => {
	const [user, setUser] = useAuthStore(state => [state.user, state.setUser])
	const [isLoading, setIsLoading] = useState(false)
	const router = useRouter()
	const api = new VibeCodingAPI()

	const login = async (username: string, password: string) => {
		try {
			setIsLoading(true)
			const response = await api.login(username, password)
			setUser({ username })
			return { success: true, response }
		} catch (error: any) {
			return { success: false, error: error?.message || 'Login failed' }
		} finally {
			setIsLoading(false)
		}
	}

	const logout = async () => {
		localStorage.removeItem('vibe_coding_token')
		setUser(null)
		router.push('/')
	}

	const refreshToken = async () => {
		// Basic token presence check for now
		return !!localStorage.getItem('vibe_coding_token')
	}

	return { user, login, logout, refreshToken, isLoading }
}
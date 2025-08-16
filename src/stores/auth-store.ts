import { create } from 'zustand'

interface User {
	username: string
}

interface AuthState {
	user: User | null
	token: string | null
	setUser: (user: User | null) => void
	setToken: (token: string | null) => void
}

export const useAuthStore = create<AuthState>((set) => ({
	user: null,
	token: null,
	setUser: (user) => set({ user }),
	setToken: (token) => set({ token })
}))
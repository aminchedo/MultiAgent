import { create } from 'zustand'

interface User {
  username: string
  // Add other user properties as needed
}

interface AuthState {
  user: User | null
  setUser: (user: User | null) => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  setUser: (user) => set({ user }),
}))
import { create } from 'zustand'
import axios from 'axios'

const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api').replace(/\/$/, '')
const TOKEN_KEY = 'token'
const USER_KEY = 'user'

function readStoredUser() {
  try {
    const value = localStorage.getItem(USER_KEY)
    return value ? JSON.parse(value) : null
  } catch {
    localStorage.removeItem(USER_KEY)
    return null
  }
}

function clearSession() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

const useAuthStore = create((set, get) => ({
  user: readStoredUser(),
  token: localStorage.getItem(TOKEN_KEY),
  isLoading: false,
  isInitialized: false,
  error: null,

  initialize: async () => {
    if (get().isInitialized) return
    const token = get().token
    if (!token) {
      set({ isInitialized: true })
      return
    }

    set({ isLoading: true, error: null })
    try {
      const response = await axios.get(`${API_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      const user = response.data.user
      set({ user, isInitialized: true })
      localStorage.setItem(USER_KEY, JSON.stringify(user))
    } catch {
      clearSession()
      set({ user: null, token: null, isInitialized: true })
    } finally {
      set({ isLoading: false })
    }
  },

  login: async credentials => {
    set({ isLoading: true, error: null })
    try {
      const response = await axios.post(`${API_URL}/auth/login`, credentials)
      if (!response.data.success || !response.data.token) {
        const error = response.data.message || 'Login failed'
        set({ error })
        return { success: false, error }
      }

      const { token, user } = response.data
      localStorage.setItem(TOKEN_KEY, token)
      localStorage.setItem(USER_KEY, JSON.stringify(user))
      set({ token, user, isInitialized: true })
      return { success: true }
    } catch (err) {
      const error = err.response?.data?.detail || err.response?.data?.message || 'Login failed'
      set({ error })
      return { success: false, error }
    } finally {
      set({ isLoading: false })
    }
  },

  fetchProfile: async () => {
    set({ isInitialized: false })
    await get().initialize()
  },

  logout: () => {
    clearSession()
    set({ user: null, token: null, isInitialized: true, error: null })
  },

  isAuthenticated: () => Boolean(get().token && get().user),

  hasRole: role => get().user?.role === role,

  hasAnyRole: roles => roles.includes(get().user?.role),
}))

export { useAuthStore }

import { create } from 'zustand'
import axios from 'axios'

const API_URL = 'http://localhost:8000/api'

const useAuthStore = create((set, get) => {
  // Initialize from localStorage
  const savedUser = JSON.parse(localStorage.getItem('user')) || null
  const savedToken = localStorage.getItem('token') || null

  // Auto-fetch profile if token exists but no user
  if (savedToken && !savedUser) {
    axios.get(`${API_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${savedToken}` }
    }).then(response => {
      set({ user: response.data.user })
      localStorage.setItem('user', JSON.stringify(response.data.user))
    }).catch(() => {
      set({ user: null, token: null })
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    })
  }

  return {
    user: savedUser,
    token: savedToken,
    isLoading: false,
    error: null,

    login: async (credentials) => {
      set({ isLoading: true, error: null })
      try {
        const response = await axios.post(`${API_URL}/auth/login`, credentials)
        if (response.data.success) {
          set({ token: response.data.token, user: response.data.user })
          localStorage.setItem('token', response.data.token)
          localStorage.setItem('user', JSON.stringify(response.data.user))
          return { success: true }
        } else {
          return { success: false, error: response.data.message || 'Login failed' }
        }
      } catch (err) {
        const errMsg = err.response?.data?.detail || err.message || 'Login failed'
        set({ error: errMsg })
        return { success: false, error: errMsg }
      } finally {
        set({ isLoading: false })
      }
    },

    fetchProfile: async () => {
      const { token } = get()
      if (!token) return
      set({ isLoading: true })
      try {
        const response = await axios.get(`${API_URL}/auth/me`, {
          headers: { Authorization: `Bearer ${token}` }
        })
        set({ user: response.data.user })
        localStorage.setItem('user', JSON.stringify(response.data.user))
      } catch (err) {
        get().logout()
      } finally {
        set({ isLoading: false })
      }
    },

    logout: () => {
      set({ user: null, token: null })
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    },

    isAuthenticated: () => {
      return !!get().token
    },

    hasRole: (role) => {
      return get().user?.role === role
    },

    hasAnyRole: (roles) => {
      return roles.includes(get().user?.role)
    }
  }
})

export { useAuthStore }

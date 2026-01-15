import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

const backendBaseUrl = (import.meta.env.VITE_BACKEND_URL || 'http://localhost:8001').replace(/\/$/, '')
const API_BASE = `${backendBaseUrl}/api`

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('token'))
  const isLoading = ref(false)
  const error = ref(null)

  // Set up axios interceptor
  if (token.value) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
  }

  async function login(credentials) {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await axios.post(`${API_BASE}/auth/login`, credentials)
      const { token: newToken, user: userData } = response.data
      
      token.value = newToken
      user.value = userData
      
      localStorage.setItem('token', newToken)
      axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`
      
      return { success: true }
    } catch (err) {
      error.value = err.response?.data?.message || 'Login failed'
      return { success: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  async function register(userData) {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await axios.post(`${API_BASE}/auth/register`, userData)
      const { token: newToken, user: newUser } = response.data
      
      token.value = newToken
      user.value = newUser
      
      localStorage.setItem('token', newToken)
      axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`
      
      return { success: true }
    } catch (err) {
      error.value = err.response?.data?.message || 'Registration failed'
      return { success: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  async function fetchProfile() {
    if (!token.value) return
    
    try {
      const response = await axios.get(`${API_BASE}/auth/me`)
      user.value = response.data.user
    } catch (err) {
      // Token might be invalid, logout
      logout()
    }
  }

  function logout() {
    user.value = null
    token.value = null
    localStorage.removeItem('token')
    delete axios.defaults.headers.common['Authorization']
  }

  function isAuthenticated() {
    return !!token.value && !!user.value
  }

  function hasRole(role) {
    return user.value?.role === role
  }

  function hasAnyRole(roles) {
    return roles.includes(user.value?.role)
  }

  return {
    user,
    token,
    isLoading,
    error,
    login,
    register,
    fetchProfile,
    logout,
    isAuthenticated,
    hasRole,
    hasAnyRole
  }
})
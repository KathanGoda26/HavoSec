import axios from 'axios'

const fallbackHost = typeof window !== 'undefined' ? window.location.hostname : 'localhost'
// The dev server proxies API requests to the local backend, including LAN clients.
export const API_BASE_URL = (import.meta.env.VITE_API_URL || (import.meta.env.DEV ? '/api' : `http://${fallbackHost}:8000/api`)).replace(/\/$/, '')

const apiClient = axios.create({ baseURL: API_BASE_URL, timeout: 15000 })
let unauthorizedHandler = null

export const setUnauthorizedHandler = handler => { unauthorizedHandler = handler }

apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

apiClient.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401 && unauthorizedHandler) unauthorizedHandler()
    return Promise.reject(error)
  }
)

export function getApiError(error, fallback = 'Request failed') {
  if (!error.response && error.code === 'ERR_NETWORK') return 'Cannot reach the backend. Check that the backend server is running and try again.'
  return error.response?.data?.detail || error.response?.data?.message || fallback
}

export default apiClient

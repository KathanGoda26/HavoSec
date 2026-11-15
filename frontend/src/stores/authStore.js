import { create } from 'zustand'
import apiClient, { getApiError, setUnauthorizedHandler } from '@/services/apiClient'
import { normalizeRole, USER_ROLES } from '@/constants/auth'

const TOKEN_KEY = 'token'
const USER_KEY = 'user'
const normalizeUser = user => user ? { ...user, role: normalizeRole(user.role) } : null

function readStoredUser() {
  try { return normalizeUser(JSON.parse(localStorage.getItem(USER_KEY))) }
  catch { localStorage.removeItem(USER_KEY); return null }
}
function clearSession() { localStorage.removeItem(TOKEN_KEY); localStorage.removeItem(USER_KEY) }

const useAuthStore = create((set, get) => ({
  user: readStoredUser(),
  token: localStorage.getItem(TOKEN_KEY),
  isInitializing: false,
  isInitialized: false,
  isSessionValidated: false,
  error: null,

  restoreSession: async (force = false) => {
    if (get().isInitialized && !force) return
    const token = get().token || localStorage.getItem(TOKEN_KEY)
    if (!token) { set({ user: null, token: null, isInitialized: true, isSessionValidated: false, error: null }); return }
    set({ isInitializing: true, error: null })
    try {
      const { data } = await apiClient.get('/auth/me')
      const user = normalizeUser(data.user)
      localStorage.setItem(USER_KEY, JSON.stringify(user))
      set({ user, token, isInitialized: true, isSessionValidated: true, error: null })
    } catch (error) {
      const status = error.response?.status
      if ([401, 403, 404].includes(status)) {
        clearSession()
        set({ user: null, token: null, isInitialized: true, isSessionValidated: false, error: null })
      } else {
        set({ isInitialized: true, isSessionValidated: false, error: 'The secure session could not be validated. Check the backend connection and retry.' })
      }
    } finally { set({ isInitializing: false }) }
  },

  initialize: () => get().restoreSession(),
  retrySession: () => { set({ isInitialized: false }); return get().restoreSession(true) },

  login: async credentials => {
    set({ isInitializing: true, error: null })
    try {
      const { data } = await apiClient.post('/auth/login', { email: credentials.email, password: credentials.password })
      if (!data.success || !data.token || !data.user) throw new Error('Invalid authentication response')
      const user = normalizeUser(data.user)
      localStorage.setItem(TOKEN_KEY, data.token)
      localStorage.setItem(USER_KEY, JSON.stringify(user))
      set({ token: data.token, user, isInitialized: true, isSessionValidated: true, error: null })
      return { success: true, user }
    } catch (error) {
      const message = getApiError(error, 'Login failed')
      set({ error: message, isSessionValidated: false })
      return { success: false, error: message }
    } finally { set({ isInitializing: false }) }
  },

  fetchProfile: () => get().restoreSession(true),
  logout: () => { clearSession(); sessionStorage.clear(); set({ user: null, token: null, isInitialized: true, isSessionValidated: false, error: null }) },
  isAuthenticated: () => Boolean(get().token && get().user && get().isSessionValidated),
  hasRole: role => get().user?.role === normalizeRole(role),
  hasAnyRole: roles => roles.map(normalizeRole).includes(get().user?.role),
  can: permission => get().user?.permissions?.includes(permission) || get().user?.role === USER_ROLES.SUPERADMIN,
}))

setUnauthorizedHandler(() => {
  const state = useAuthStore.getState()
  if (!state.token) return
  state.logout()
  if (!window.location.pathname.startsWith('/auth/')) {
    const redirect = `${window.location.pathname}${window.location.search}`
    window.location.assign(`/auth/login?redirect=${encodeURIComponent(redirect)}`)
  }
})

export { useAuthStore }

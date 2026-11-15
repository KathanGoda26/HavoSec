import React, { lazy, Suspense, useEffect } from 'react'
import { Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { PLATFORM_ROLES, getAuthenticatedHome } from '@/constants/auth'

const Home = lazy(() => import('@/views/Home'))
const About = lazy(() => import('@/views/About'))
const Blog = lazy(() => import('@/views/Blog'))
const BookDemo = lazy(() => import('@/views/BookDemo'))
const Pricing = lazy(() => import('@/views/Pricing'))
const VulnerabilityDetail = lazy(() => import('@/views/VulnerabilityDetail'))
const NotFound = lazy(() => import('@/views/NotFound'))

const Login = lazy(() => import('@/views/auth/Login'))
const ForgotPassword = lazy(() => import('@/views/auth/ForgotPassword'))
const ResetPassword = lazy(() => import('@/views/auth/ResetPassword'))
const VerifyEmail = lazy(() => import('@/views/auth/VerifyEmail'))

const Dashboard = lazy(() => import('@/views/dashboard/Dashboard'))
const Projects = lazy(() => import('@/dashboard/projects/Projects'))
const Assets = lazy(() => import('@/dashboard/assets/Assets'))
const MissionControl = lazy(() => import('@/dashboard/missions/MissionControl'))
const MissionDetail = lazy(() => import('@/dashboard/missions/MissionControl').then(module => ({ default: module.MissionDetail })))
const SecurityRuns = lazy(() => import('@/dashboard/security-runs/SecurityRuns'))
const SecurityRunDetail = lazy(() => import('@/dashboard/security-runs/SecurityRuns').then(module => ({ default: module.SecurityRunDetail })))
const AssetDetail = lazy(() => import('@/dashboard/assets/Assets').then(module => ({ default: module.AssetDetail })))
const ProjectLayout = lazy(() => import('@/dashboard/projects/Projects').then(module => ({ default: module.ProjectLayout })))
const ProjectOverview = lazy(() => import('@/dashboard/projects/Projects').then(module => ({ default: module.ProjectOverview })))
const Overview = lazy(() => import('@/views/dashboard/Overview'))
const AttackInsights = lazy(() => import('@/views/dashboard/AttackInsights'))
const DefenseMetrics = lazy(() => import('@/views/dashboard/DefenseMetrics'))
const SystemHealth = lazy(() => import('@/views/dashboard/SystemHealth'))
const ActivityLogs = lazy(() => import('@/views/dashboard/ActivityLogs'))
const Settings = lazy(() => import('@/views/dashboard/Settings'))
const ArchitectureMap = lazy(() => import('@/views/dashboard/ArchitectureMap'))
const GitHubCallback = lazy(() => import('@/views/dashboard/GitHubCallback'))

function AuthBoundary({ children, guest = false, allowedRoles = null }) {
  const location = useLocation()
  const navigate = useNavigate()
  const initialize = useAuthStore(state => state.initialize)
  const isInitialized = useAuthStore(state => state.isInitialized)
  const isInitializing = useAuthStore(state => state.isInitializing)
  const authError = useAuthStore(state => state.error)
  const retrySession = useAuthStore(state => state.retrySession)
  const logout = useAuthStore(state => state.logout)
  const isAuthenticated = useAuthStore(state => state.isAuthenticated())
  const userRole = useAuthStore(state => state.user?.role)

  useEffect(() => {
    initialize()
  }, [initialize])

  if (!isInitialized || isInitializing) {
    return <div className="route-loading" role="status" aria-live="polite">Loading secure session...</div>
  }

  if (!guest && authError && !isAuthenticated) {
    const leaveSession = () => {
      logout()
      navigate('/auth/login', { replace: true })
    }

    return (
      <div className="route-loading auth-unavailable" role="alert">
        <div className="auth-unavailable-card">
          <span className="auth-unavailable-label">Session unavailable</span>
          <h1>We couldn&apos;t verify your session.</h1>
          <p>{authError}</p>
          <div className="auth-unavailable-actions">
            <button type="button" className="auth-retry-button" onClick={retrySession}>Retry connection</button>
            <button type="button" className="auth-logout-button" onClick={leaveSession}>Log out</button>
          </div>
        </div>
      </div>
    )
  }

  if (guest && isAuthenticated) {
    return <Navigate to={getAuthenticatedHome(userRole)} replace />
  }

  if (!guest && !isAuthenticated) {
    const redirect = `${location.pathname}${location.search}`
    return <Navigate to={`/auth/login?redirect=${encodeURIComponent(redirect)}`} replace />
  }

  if (!guest && allowedRoles && !allowedRoles.includes(userRole)) {
    return <Navigate to="/dashboard/overview" replace />
  }

  return children
}

function AppRoutes() {
  return (
    <Suspense fallback={<div className="route-loading" role="status" aria-live="polite">Loading page...</div>}>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/about" element={<About />} />
        <Route path="/blog" element={<Blog />} />
        <Route path="/book-demo" element={<BookDemo />} />
        <Route path="/pricing" element={<Pricing />} />
        <Route path="/vulnerability/:id" element={<VulnerabilityDetail />} />

        <Route path="/login" element={<Navigate to="/auth/login" replace />} />
        <Route path="/auth/login" element={<AuthBoundary guest><Login /></AuthBoundary>} />
        <Route path="/auth/forgot-password" element={<AuthBoundary guest><ForgotPassword /></AuthBoundary>} />
        <Route path="/auth/reset-password" element={<AuthBoundary guest><ResetPassword /></AuthBoundary>} />
        <Route path="/auth/verify-email" element={<AuthBoundary guest><VerifyEmail /></AuthBoundary>} />
        <Route path="/integrations/github/callback" element={<AuthBoundary><GitHubCallback /></AuthBoundary>} />

        <Route path="/dashboard" element={<AuthBoundary><Dashboard /></AuthBoundary>}>
          <Route index element={<Navigate to="/dashboard/overview" replace />} />
          <Route path="overview" element={<Overview />} />
          <Route path="projects" element={<Projects />} />
          <Route path="assets" element={<Assets />} />
          <Route path="assets/:assetId" element={<AssetDetail />} />
          <Route path="missions" element={<MissionControl />} />
          <Route path="missions/:missionId" element={<MissionDetail />} />
          <Route path="security-runs" element={<SecurityRuns />} />
          <Route path="security-runs/:runId" element={<SecurityRunDetail />} />
          <Route path="projects/:projectId" element={<ProjectLayout />}>
            <Route index element={<Navigate to="overview" replace />} />
            <Route path="overview" element={<ProjectOverview />} />
            <Route path="assets" element={<Assets />} />
            <Route path="assets/:assetId" element={<AssetDetail />} />
            <Route path="security-runs" element={<SecurityRuns />} />
            <Route path="security-runs/:runId" element={<SecurityRunDetail />} />
            <Route path="findings" element={<AttackInsights />} />
            <Route path="remediation" element={<DefenseMetrics />} />
            <Route path="activity" element={<ActivityLogs />} />
            <Route path="*" element={<Navigate to="overview" replace />} />
          </Route>
          <Route path="findings" element={<AttackInsights />} />
          <Route path="attack-insights" element={<Navigate to="/dashboard/findings" replace />} />
          <Route path="remediation" element={<DefenseMetrics />} />
          <Route path="defense-metrics" element={<Navigate to="/dashboard/remediation" replace />} />
          <Route path="system-health" element={<AuthBoundary allowedRoles={PLATFORM_ROLES}><Navigate to="/admin/platform-health" replace /></AuthBoundary>} />
          <Route path="activity" element={<ActivityLogs />} />
          <Route path="activity-logs" element={<Navigate to="/dashboard/activity" replace />} />
          <Route path="settings" element={<Settings />} />
          <Route path="scan-results" element={<Navigate to="/dashboard/security-runs" replace />} />
          <Route path="architecture-map" element={<ArchitectureMap />} />
        </Route>

        <Route path="/admin" element={<AuthBoundary allowedRoles={PLATFORM_ROLES}><Dashboard /></AuthBoundary>}>
          <Route index element={<Navigate to="/admin/platform-health" replace />} />
          <Route path="platform-health" element={<SystemHealth />} />
          <Route path="settings" element={<Settings platform />} />
          <Route path="*" element={<Navigate to="/admin/platform-health" replace />} />
        </Route>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  )
}

export default AppRoutes

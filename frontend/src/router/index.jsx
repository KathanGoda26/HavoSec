import React, { useEffect } from 'react'
import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'

import {
  Home,
  About,
  Blog,
  BookDemo,
  Pricing,
  VulnerabilityDetail,
  NotFound,
} from '@/pages/public'
import {
  Login,
  ForgotPassword,
  ResetPassword,
  VerifyEmail,
} from '@/pages/auth'
import {
  Dashboard,
  Overview,
  AttackInsights,
  DefenseMetrics,
  SystemHealth,
  ActivityLogs,
  Settings,
  ScanResults,
  ArchitectureMap,
} from '@/pages/dashboard'

function AuthBoundary({ children, guest = false }) {
  const location = useLocation()
  const initialize = useAuthStore(state => state.initialize)
  const isInitialized = useAuthStore(state => state.isInitialized)
  const isLoading = useAuthStore(state => state.isLoading)
  const isAuthenticated = useAuthStore(state => state.isAuthenticated())

  useEffect(() => {
    initialize()
  }, [initialize])

  if (!isInitialized || isLoading) {
    return <div className="route-loading" role="status" aria-live="polite">Loading secure session...</div>
  }

  if (guest && isAuthenticated) {
    return <Navigate to="/dashboard/overview" replace />
  }

  if (!guest && !isAuthenticated) {
    const redirect = `${location.pathname}${location.search}`
    return <Navigate to={`/auth/login?redirect=${encodeURIComponent(redirect)}`} replace />
  }

  return children
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/about" element={<About />} />
      <Route path="/blog" element={<Blog />} />
      <Route path="/book-demo" element={<BookDemo />} />
      <Route path="/pricing" element={<Pricing />} />
      <Route path="/vulnerability/:id" element={<VulnerabilityDetail />} />

      <Route path="/auth/login" element={<AuthBoundary guest><Login /></AuthBoundary>} />
      <Route path="/auth/forgot-password" element={<ForgotPassword />} />
      <Route path="/auth/reset-password" element={<ResetPassword />} />
      <Route path="/auth/verify-email" element={<VerifyEmail />} />

      <Route path="/dashboard" element={<AuthBoundary><Dashboard /></AuthBoundary>}>
        <Route index element={<Navigate to="/dashboard/overview" replace />} />
        <Route path="overview" element={<Overview />} />
        <Route path="attack-insights" element={<AttackInsights />} />
        <Route path="defense-metrics" element={<DefenseMetrics />} />
        <Route path="system-health" element={<SystemHealth />} />
        <Route path="activity-logs" element={<ActivityLogs />} />
        <Route path="settings" element={<Settings />} />
        <Route path="scan-results" element={<ScanResults />} />
        <Route path="architecture-map" element={<ArchitectureMap />} />
      </Route>

      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}

export default AppRoutes

import React, { useEffect } from 'react'
import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'

import Home from '@/views/Home'
import About from '@/views/About'
import Blog from '@/views/Blog'
import BookDemo from '@/views/BookDemo'
import Pricing from '@/views/Pricing'
import VulnerabilityDetail from '@/views/VulnerabilityDetail'
import NotFound from '@/views/NotFound'
import Login from '@/views/auth/Login'
import ForgotPassword from '@/views/auth/ForgotPassword'
import ResetPassword from '@/views/auth/ResetPassword'
import VerifyEmail from '@/views/auth/VerifyEmail'
import Dashboard from '@/views/dashboard/Dashboard'
import Overview from '@/views/dashboard/Overview'
import AttackInsights from '@/views/dashboard/AttackInsights'
import DefenseMetrics from '@/views/dashboard/DefenseMetrics'
import SystemHealth from '@/views/dashboard/SystemHealth'
import ActivityLogs from '@/views/dashboard/ActivityLogs'
import Settings from '@/views/dashboard/Settings'
import ScanResults from '@/views/dashboard/ScanResults'
import ArchitectureMap from '@/views/dashboard/ArchitectureMap'

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

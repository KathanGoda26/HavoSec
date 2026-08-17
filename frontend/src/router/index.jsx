import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'

// Public pages
import Home from '@/views/Home'
import About from '@/views/About'
import Blog from '@/views/Blog'
import BookDemo from '@/views/BookDemo'
import Pricing from '@/views/Pricing'
import VulnerabilityDetail from '@/views/VulnerabilityDetail'
import NotFound from '@/views/NotFound'

// Auth pages
import Login from '@/views/auth/Login'
import ForgotPassword from '@/views/auth/ForgotPassword'
import ResetPassword from '@/views/auth/ResetPassword'
import VerifyEmail from '@/views/auth/VerifyEmail'

// Dashboard pages
import Dashboard from '@/views/dashboard/Dashboard'
import Overview from '@/views/dashboard/Overview'
import AttackInsights from '@/views/dashboard/AttackInsights'
import DefenseMetrics from '@/views/dashboard/DefenseMetrics'
import SystemHealth from '@/views/dashboard/SystemHealth'
import ActivityLogs from '@/views/dashboard/ActivityLogs'
import Settings from '@/views/dashboard/Settings'
import ScanResults from '@/views/dashboard/ScanResults'
import ArchitectureMap from '@/views/dashboard/ArchitectureMap'

// Protected route wrapper
function ProtectedRoute({ children }) {
  const isAuthenticated = useAuthStore(state => state.isAuthenticated)
  if (!isAuthenticated()) {
    return <Navigate to="/auth/login" replace />
  }
  return children
}

// Guest route wrapper (redirect to dashboard if already authenticated)
function GuestRoute({ children }) {
  const isAuthenticated = useAuthStore(state => state.isAuthenticated)
  if (isAuthenticated()) {
    return <Navigate to="/dashboard/overview" replace />
  }
  return children
}

function AppRoutes() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/" element={<Home />} />
      <Route path="/about" element={<About />} />
      <Route path="/blog" element={<Blog />} />
      <Route path="/book-demo" element={<BookDemo />} />
      <Route path="/pricing" element={<Pricing />} />
      <Route path="/vulnerability/:id" element={<VulnerabilityDetail />} />

      {/* Auth routes */}
      <Route path="/auth/login" element={<GuestRoute><Login /></GuestRoute>} />
      <Route path="/auth/forgot-password" element={<ForgotPassword />} />
      <Route path="/auth/reset-password" element={<ResetPassword />} />
      <Route path="/auth/verify-email" element={<VerifyEmail />} />

      {/* Dashboard routes */}
      <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>}>
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

      {/* Catch all route - 404 */}
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}

export default AppRoutes

import React, { useMemo } from 'react'
import { useLocation } from 'react-router-dom'
import Navigation from '@/components/Navigation'
import Footer from '@/components/Footer'
import AppRoutes from '@/router/index'

function Layout() {
  const location = useLocation()

  const showNavigation = useMemo(() => {
    const hideNavRoutes = ['/auth/login']
    const isDashboard = location.pathname.startsWith('/dashboard')
    return !hideNavRoutes.includes(location.pathname) && !isDashboard
  }, [location.pathname])

  return (
    <div className="layout-container">
      {showNavigation && <Navigation />}

      <main className={`main-content ${showNavigation ? 'with-nav' : 'full-page'}`}>
        <AppRoutes />
      </main>

      {showNavigation && <Footer />}

      {/* Global Toast/Notification Container */}
      <div id="toast-container" className="toast-container">
        {/* Toasts will be dynamically added here */}
      </div>
    </div>
  )
}

export default Layout

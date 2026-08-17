import React from 'react'
import { useLocation } from 'react-router-dom'
import Navigation from '@/components/Navigation'
import Footer from '@/components/Footer'
import AppRoutes from '@/router/index'

function Layout() {
  const { pathname } = useLocation()
  const isDashboard = pathname.startsWith('/dashboard')
  const isAuth = pathname.startsWith('/auth/')
  const showPublicChrome = !isDashboard && !isAuth

  return (
    <div className={`layout-container ${isDashboard ? 'dashboard-layout' : 'public-layout'}`}>
      {showPublicChrome && <Navigation />}

      <main className={`main-content ${showPublicChrome ? 'with-nav' : 'full-page'}`}>
        <AppRoutes />
      </main>

      {showPublicChrome && <Footer />}
      <div id="toast-container" className="toast-container" />
    </div>
  )
}

export default Layout

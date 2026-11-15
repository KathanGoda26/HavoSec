import React, { useEffect } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from '@/components/ui/Sidebar'
import DynamicSEO from '@/components/DynamicSEO'
import { useThemeStore } from '@/stores/themeStore'

function Dashboard() {
  const initializeTheme = useThemeStore(state => state.initializeTheme)
  useEffect(() => { initializeTheme() }, [initializeTheme])

  return (
    <div className="dashboard-layout">
      <DynamicSEO page="dashboard" />
      <Sidebar />
      <main className="dashboard-main">
        <div className="content-wrapper">
          <Outlet />
        </div>
      </main>
    </div>
  )
}

export default Dashboard

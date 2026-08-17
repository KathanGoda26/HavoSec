import React from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from '@/components/ui/Sidebar'
import DynamicSEO from '@/components/DynamicSEO'

function Dashboard() {
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

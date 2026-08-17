import React, { useState, useMemo } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { useThemeStore } from '@/stores/themeStore'
import {
  HomeIcon,
  ShieldCheckIcon,
  ChartBarIcon,
  HeartIcon,
  DocumentTextIcon,
  CogIcon,
  SunIcon,
  MoonIcon,
  ArrowRightOnRectangleIcon,
} from '@heroicons/react/24/outline'

const mainNavItems = [
  { name: 'Overview', path: '/dashboard/overview', icon: HomeIcon },
  { name: 'Attack Insights', path: '/dashboard/attack-insights', icon: ShieldCheckIcon },
  { name: 'Defense Metrics', path: '/dashboard/defense-metrics', icon: ChartBarIcon },
  { name: 'System Health', path: '/dashboard/system-health', icon: HeartIcon },
]

const analyticsNavItems = [
  { name: 'Activity Logs', path: '/dashboard/activity-logs', icon: DocumentTextIcon },
  { name: 'Settings', path: '/dashboard/settings', icon: CogIcon },
]

function Sidebar() {
  const location = useLocation()
  const navigate = useNavigate()
  const [isCollapsed, setIsCollapsed] = useState(false)
  const isDark = useThemeStore(state => state.isDark)
  const toggleTheme = useThemeStore(state => state.toggleTheme)
  const user = useAuthStore(state => state.user)
  const logout = useAuthStore(state => state.logout)

  const userInitials = useMemo(() => {
    if (!user) return 'U'
    return `${user.firstName?.[0] || ''}${user.lastName?.[0] || ''}`.toUpperCase()
  }, [user])

  const toggleCollapse = () => setIsCollapsed(!isCollapsed)

  const handleLogout = async () => {
    logout()
    navigate('/auth/login')
  }

  return (
    <aside className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        <div className="logo-wrapper">
          <img src="/logo1.png" alt="HavoSec Logo" className="logo-icon" />
          {!isCollapsed && <span className="logo-text">HavoSec</span>}
        </div>
        <button
          onClick={toggleCollapse}
          className="collapse-btn"
          title={isCollapsed ? 'Expand' : 'Collapse'}
        >
          {isCollapsed ? (
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor" className="icon-sm">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
            </svg>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor" className="icon-sm">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          )}
        </button>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-section">
          {!isCollapsed && <div className="nav-section-title">Main</div>}
          <ul className="nav-list">
            {mainNavItems.map(item => (
              <li key={item.name}>
                <Link
                  to={item.path}
                  className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
                  title={isCollapsed ? item.name : ''}
                >
                  <item.icon className="nav-icon" />
                  {!isCollapsed && <span className="nav-text">{item.name}</span>}
                </Link>
              </li>
            ))}
          </ul>
        </div>

        <div className="nav-section">
          {!isCollapsed && <div className="nav-section-title">Analytics</div>}
          <ul className="nav-list">
            {analyticsNavItems.map(item => (
              <li key={item.name}>
                <Link
                  to={item.path}
                  className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
                  title={isCollapsed ? item.name : ''}
                >
                  <item.icon className="nav-icon" />
                  {!isCollapsed && <span className="nav-text">{item.name}</span>}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </nav>

      <div className="sidebar-footer">
        <div className="user-profile">
          <div className="user-avatar">{userInitials}</div>
          {!isCollapsed && (
            <div className="user-info">
              <div className="user-name">{user?.firstName} {user?.lastName}</div>
              <div className="user-role">{user?.role}</div>
            </div>
          )}
        </div>
        <div className="sidebar-actions">
          <button
            onClick={toggleTheme}
            className="action-btn"
            title={isDark ? 'Light Mode' : 'Dark Mode'}
          >
            {isDark ? <SunIcon className="icon-sm" /> : <MoonIcon className="icon-sm" />}
          </button>
          <button onClick={handleLogout} className="action-btn logout" title="Logout">
            <ArrowRightOnRectangleIcon className="icon-sm" />
          </button>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar

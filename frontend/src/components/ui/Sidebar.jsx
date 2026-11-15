import React, { useMemo, useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { useThemeStore } from '@/stores/themeStore'
import { getNavigationSections, roleLabels } from '@/dashboard/navigation/navigation'
import {
  SunIcon, MoonIcon, ArrowRightOnRectangleIcon,
  Bars3Icon, XMarkIcon,
} from '@heroicons/react/24/outline'

function Sidebar() {
  const navigate = useNavigate()
  const [mobileOpen, setMobileOpen] = useState(false)
  const isDark = useThemeStore(state => state.isDark)
  const toggleTheme = useThemeStore(state => state.toggleTheme)
  const user = useAuthStore(state => state.user)
  const navSections = useMemo(() => getNavigationSections(user?.role), [user?.role])
  const logout = useAuthStore(state => state.logout)
  const initials = useMemo(() => {
    const value = `${user?.firstName?.[0] || ''}${user?.lastName?.[0] || ''}`.trim()
    return value.toUpperCase() || user?.email?.[0]?.toUpperCase() || 'U'
  }, [user])

  const closeMobile = () => setMobileOpen(false)
  const handleNavSelect = event => {
    closeMobile()
    // A mouse click leaves the active link focused, which keeps the desktop
    // rail expanded through :focus-within even after the pointer leaves.
    // Blur only clicked links; keyboard focus still expands the navigation.
    if (event.detail > 0) {
      const selectedLink = event.currentTarget
      window.requestAnimationFrame(() => selectedLink.blur())
    }
  }
  const handleLogout = () => { logout(); navigate('/auth/login') }

  return (
    <>
      <button className="dashboard-mobile-menu" onClick={() => setMobileOpen(true)} aria-label="Open dashboard menu" aria-expanded={mobileOpen} aria-controls="dashboard-sidebar"><Bars3Icon /></button>
      <button className={`sidebar-backdrop ${mobileOpen ? 'is-visible' : ''}`} onClick={closeMobile} aria-label="Close dashboard menu" />
      <aside id="dashboard-sidebar" className={`sidebar ${mobileOpen ? 'is-open' : ''}`} aria-label="Dashboard navigation">
        <div className="sidebar-header">
          <div className="logo-wrapper"><img src="/logo1.png" alt="" className="logo-icon" /><span className="sidebar-label logo-text">HavoSec</span></div>
          <button className="sidebar-mobile-close" onClick={closeMobile} aria-label="Close dashboard menu"><XMarkIcon /></button>
        </div>
        <nav className="sidebar-nav">
          {navSections.map(section => <div className="nav-section" key={section.id}>
          <p id={`navigation-${section.id}`} className="sidebar-label nav-section-title">{section.label}</p>
          <ul className="nav-list" aria-labelledby={`navigation-${section.id}`}>
            {section.items.map(item => (
              <li key={item.name}>
                <NavLink to={item.path} onClick={handleNavSelect} title={item.name} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
                  <span className="nav-icon-wrap"><item.icon className="nav-icon" /></span><span className="sidebar-label nav-text">{item.name}</span>
                </NavLink>
              </li>
            ))}
          </ul>
          </div>)}
        </nav>
        <div className="sidebar-footer">
          <div className="user-profile"><div className="user-avatar">{initials}</div><div className="sidebar-label user-info"><div className="user-name">{`${user?.firstName || ''} ${user?.lastName || ''}`.trim() || 'HavoSec User'}</div><div className="user-role">{roleLabels[user?.role] || 'User'}</div></div></div>
          <div className="sidebar-actions">
            <button onClick={toggleTheme} className="action-btn" title={isDark ? 'Use light mode' : 'Use dark mode'}>{isDark ? <SunIcon /> : <MoonIcon />}<span className="sidebar-label">{isDark ? 'Light mode' : 'Dark mode'}</span></button>
            <button onClick={handleLogout} className="action-btn logout" title="Sign out"><ArrowRightOnRectangleIcon /><span className="sidebar-label">Sign out</span></button>
          </div>
        </div>
      </aside>
    </>
  )
}

export default Sidebar

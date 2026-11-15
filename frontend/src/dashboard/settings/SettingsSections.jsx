import React from 'react'
import { Cog6ToothIcon, MoonIcon, ShieldCheckIcon, SunIcon } from '@heroicons/react/24/outline'

export function Toggle({ checked, onChange, label, description, disabled = false }) {
  return (
    <label className={`settings-toggle-row ${disabled ? 'is-disabled' : ''}`}>
      <span><span className="settings-toggle-label">{label}</span><span className="settings-toggle-description">{description}</span></span>
      <input className="settings-toggle-input" type="checkbox" checked={checked} onChange={onChange} disabled={disabled} />
      <span className="settings-toggle-control" aria-hidden="true" />
    </label>
  )
}

export function AccountSection({ user }) {
  const userName = `${user?.firstName || ''} ${user?.lastName || ''}`.trim() || 'Your account'
  return (
    <section className="settings-card" aria-labelledby="profile-heading">
      <div className="settings-card-heading"><div className="settings-card-icon"><ShieldCheckIcon /></div><div><h2 id="profile-heading">Account</h2><p>Your current signed-in identity.</p></div></div>
      <dl className="settings-details">
        <div><dt>Name</dt><dd>{userName}</dd></div><div><dt>Email</dt><dd>{user?.email || 'Not available'}</dd></div><div><dt>Access level</dt><dd className="settings-role">{user?.role || 'Not available'}</dd></div><div><dt>Organization</dt><dd>{user?.company || 'Not specified'}</dd></div>
      </dl>
      <p className="settings-helper"><Cog6ToothIcon className="icon-xs" /> Account and permission changes are not available on this page.</p>
    </section>
  )
}

export function AppearanceSection({ isDark, toggleTheme }) {
  return (
    <section className="settings-card" aria-labelledby="appearance-heading">
      <div className="settings-card-heading"><div className="settings-card-icon"><SunIcon /></div><div><h2 id="appearance-heading">Appearance</h2><p>Theme changes apply immediately across the dashboard.</p></div></div>
      <Toggle checked={isDark} onChange={toggleTheme} label="Dark interface" description={isDark ? 'Dark mode is active across the dashboard.' : 'Light mode is active across the dashboard.'} />
      <div className="settings-theme-preview" aria-hidden="true">{isDark ? <MoonIcon className="icon-sm" /> : <SunIcon className="icon-sm" />}<span>{isDark ? 'Dark mode' : 'Light mode'}</span></div>
    </section>
  )
}

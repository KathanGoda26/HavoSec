import React, { useEffect, useState } from 'react'
import {
  BellAlertIcon,
  CheckCircleIcon,
  CircleStackIcon,
  EnvelopeIcon,
} from '@heroicons/react/24/outline'
import { useAuthStore } from '@/stores/authStore'
import { useThemeStore } from '@/stores/themeStore'

import { AccountSection, AppearanceSection, Toggle } from '@/dashboard/settings/SettingsSections'
import { defaultPreferences, readPreferences, savePreferences as persistPreferences, resetPreferences as clearPreferences } from '@/dashboard/settings/preferences'
import GitHubIntegration from '@/dashboard/settings/GitHubIntegration'

function Settings({ platform = false }) {
  const user = useAuthStore(state => state.user)
  const isDark = useThemeStore(state => state.isDark)
  const toggleTheme = useThemeStore(state => state.toggleTheme)
  const [preferences, setPreferences] = useState(readPreferences)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!saved) return undefined
    const timeout = window.setTimeout(() => setSaved(false), 2600)
    return () => window.clearTimeout(timeout)
  }, [saved])

  const updatePreference = key => event => {
    setSaved(false)
    setError('')
    setPreferences(current => ({ ...current, [key]: event.target.checked }))
  }

  const savePreferences = () => {
    setSaved(false)
    setError('')
    try {
      persistPreferences(preferences)
      setSaved(true)
    } catch {
      setError('Preferences could not be saved. Check browser storage permissions and try again.')
    }
  }

  const resetPreferences = () => {
    setSaved(false)
    setError('')
    try {
      clearPreferences()
      setPreferences({ ...defaultPreferences })
    } catch {
      setError('Preferences could not be reset. Check browser storage permissions and try again.')
    }
  }

  return (
    <div className="settings-page">
      <div className="page-header settings-page-header">
        <div><p className="settings-eyebrow">{platform ? 'Platform' : 'Workspace'}</p><h1 className="page-title" data-testid="settings-title">{platform ? 'Platform Settings' : 'Settings'}</h1><p className="page-subtitle">{platform ? 'Personal dashboard preferences. Platform-wide configuration is not connected yet.' : 'Manage your personal dashboard experience in this browser.'}</p></div>
        {saved && <div className="settings-saved" role="status"><CheckCircleIcon className="icon-sm" /> Preferences saved</div>}
      </div>

      {error && <p className="settings-helper" role="alert">{error}</p>}
      <div className="settings-grid">
        <AccountSection user={user} />
        <AppearanceSection isDark={isDark} toggleTheme={toggleTheme} />
        <GitHubIntegration />

        <section className="settings-card settings-card-wide" aria-labelledby="alerts-heading">
          <div className="settings-card-heading"><div className="settings-card-icon"><BellAlertIcon /></div><div><h2 id="alerts-heading">Notification preferences · Preview</h2><p>Saved locally only. Notification delivery and compact table layouts are not connected yet.</p></div></div>
          <div className="settings-toggles">
            <Toggle checked={preferences.emailAlerts} onChange={updatePreference('emailAlerts')} label="Email notifications" description="Preference for future workspace email updates." />
            <Toggle checked={preferences.criticalAlerts} onChange={updatePreference('criticalAlerts')} label="Critical threat alerts" description="Preference for future critical threat notifications." disabled={!preferences.emailAlerts} />
            <Toggle checked={preferences.weeklyReport} onChange={updatePreference('weeklyReport')} label="Weekly security report" description="Preference for a future weekly security summary." />
            <Toggle checked={preferences.compactTables} onChange={updatePreference('compactTables')} label="Compact data tables" description="Preview preference; does not change current table layouts." />
          </div>
        </section>

        <section className="settings-card settings-card-wide settings-actions-card" aria-label="Save preferences">
          <div className="settings-actions-copy"><div className="settings-card-icon"><CircleStackIcon /></div><div><strong>Save your browser preferences</strong><span>Shared by both settings pages in this browser; not synced to your account. Reset does not change your theme.</span></div></div>
          <div className="settings-actions"><button type="button" className="settings-secondary-button" onClick={resetPreferences}>Reset defaults</button><button type="button" className="settings-primary-button" onClick={savePreferences}><EnvelopeIcon className="icon-sm" /> Save preferences</button></div>
        </section>
      </div>
    </div>
  )
}

export default Settings

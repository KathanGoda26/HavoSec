import React, { useMemo, useEffect } from 'react'
import { useContentStore } from '@/stores/contentStore'

function Settings() {
  const contentStore = useContentStore()

  useEffect(() => {
    async function loadContent() {
      try {
        if (contentStore.fetchClientDashboard) {
          await contentStore.fetchClientDashboard()
        }
      } catch (error) {
        console.warn('Could not load client dashboard content, using defaults:', error)
      }
    }
    loadContent()
  }, [])

  const pageTitle = useMemo(() => {
    return contentStore.clientDashboard?.settings?.title || 'Dashboard Settings'
  }, [contentStore.clientDashboard?.settings?.title])

  const pageDescription = useMemo(() => {
    return contentStore.clientDashboard?.settings?.description || 'Configure your dashboard preferences and settings'
  }, [contentStore.clientDashboard?.settings?.description])

  const contentText = useMemo(() => {
    return contentStore.clientDashboard?.settings?.contentText || 'This section will allow you to customize your dashboard experience and manage preferences.'
  }, [contentStore.clientDashboard?.settings?.contentText])

  const allowCustomization = useMemo(() => {
    return contentStore.clientDashboard?.settings?.allowCustomization !== false
  }, [contentStore.clientDashboard?.settings?.allowCustomization])

  const enableNotifications = useMemo(() => {
    return contentStore.clientDashboard?.settings?.enableNotifications !== false
  }, [contentStore.clientDashboard?.settings?.enableNotifications])

  return (
    <div className="settings-page">
      <h1 className="page-title" data-testid="settings-title">{pageTitle}</h1>
      <p className="page-subtitle">{pageDescription}</p>

      <div className="settings-content">
        {/* Placeholder for Settings */}
        <div className="placeholder-content glass">
          <h2>Dashboard Settings</h2>
          <p>{contentText}</p>
          <div className="mt-6 space-y-3">
            {allowCustomization && (
              <div className="setting-item">
                <span className="setting-icon">✓</span>
                <span>User Customization Enabled</span>
              </div>
            )}
            {enableNotifications && (
              <div className="setting-item">
                <span className="setting-icon">🔔</span>
                <span>Notifications Enabled</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Settings

import React, { useState, useRef, useEffect } from 'react'
import { useNotificationsStore } from '@/stores/notificationsStore'
import { useAuthStore } from '@/stores/authStore'

function NotificationsDropdown() {
  const notificationsStore = useNotificationsStore()
  const authStore = useAuthStore()
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef(null)

  function getNotificationIcon(type) {
    const iconPaths = {
      info: 'M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12zm8.706-1.442c1.146-.573 2.437.463 2.126 1.706l-.709 2.836.042-.02a.75.75 0 01.67 1.34l-.04.022c-1.147.573-2.438-.463-2.127-1.706l.71-2.836-.042.02a.75.75 0 11-.671-1.34l.041-.022zM12 9a.75.75 0 100-1.5.75.75 0 000 1.5z',
      success: 'M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12zm13.36-1.814a.75.75 0 10-1.22-.872l-3.236 4.53L9.53 12.22a.75.75 0 00-1.06 1.06l2.25 2.25a.75.75 0 001.14-.094l3.75-5.25z',
      warning: 'M9.401 3.003c1.155-2 4.043-2 5.197 0l7.355 12.748c1.154 2-.29 4.5-2.599 4.5H4.645c-2.309 0-3.752-2.5-2.598-4.5L9.4 3.003zM12 8.25a.75.75 0 01.75.75v3.75a.75.75 0 01-1.5 0V9a.75.75 0 01.75-.75zm0 8.25a.75.75 0 100-1.5.75.75 0 000 1.5z',
      error: 'M12 2.25c-5.385 0-9.75 4.365-9.75 9.75s4.365 9.75 9.75 9.75 9.75-4.365 9.75-9.75S17.385 2.25 12 2.25zm-1.72 6.97a.75.75 0 10-1.06 1.06L10.94 12l-1.72 1.72a.75.75 0 101.06 1.06L12 13.06l1.72 1.72a.75.75 0 101.06-1.06L13.06 12l1.72-1.72a.75.75 0 10-1.06-1.06L12 10.94l-1.72-1.72z',
      security: 'M12.516 2.17a.75.75 0 00-1.032 0 11.209 11.209 0 01-7.877 3.08.75.75 0 00-.722.515A12.74 12.74 0 002.25 9.75c0 5.942 4.064 10.933 9.563 12.348a.749.749 0 00.374 0c5.499-1.415 9.563-6.406 9.563-12.348 0-1.39-.223-2.73-.635-3.985a.75.75 0 00-.722-.516l-.143.001c-2.996 0-5.717-1.17-7.734-3.08zm3.094 8.016a.75.75 0 10-1.22-.872l-3.236 4.53L9.53 12.22a.75.75 0 00-1.06 1.06l2.25 2.25a.75.75 0 001.14-.094l3.75-5.25z'
    }
    return iconPaths[type] || iconPaths.info
  }

  function formatTime(dateString) {
    if (!dateString) return ''
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)
    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString()
  }

  const toggleDropdown = () => {
    const newOpen = !isOpen
    setIsOpen(newOpen)
    if (newOpen) notificationsStore.fetchNotifications()
  }

  const handleNotificationClick = (notification) => {
    if (!notification.read) notificationsStore.markAsRead(notification.id)
    if (notification.link) window.location.href = notification.link
  }

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('click', handleClickOutside)
    if (authStore.user?.id) {
      notificationsStore.connectWebSocket(authStore.user.id)
      notificationsStore.requestBrowserNotificationPermission()
    }
    notificationsStore.fetchNotifications()
    return () => {
      document.removeEventListener('click', handleClickOutside)
      notificationsStore.disconnectWebSocket()
    }
  }, [])

  return (
    <div className="notifications-dropdown" ref={dropdownRef}>
      <button className={`notification-bell ${notificationsStore.unreadCount > 0 ? 'has-unread' : ''}`} onClick={toggleDropdown} data-testid="notification-bell">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="bell-icon">
          <path fillRule="evenodd" d="M5.25 9a6.75 6.75 0 0113.5 0v.75c0 2.123.8 4.057 2.118 5.52a.75.75 0 01-.297 1.206c-1.544.57-3.16.99-4.831 1.243a3.75 3.75 0 11-7.48 0 24.585 24.585 0 01-4.831-1.244.75.75 0 01-.298-1.205A8.217 8.217 0 005.25 9.75V9zm4.502 8.9a2.25 2.25 0 104.496 0 25.057 25.057 0 01-4.496 0z" clipRule="evenodd" />
        </svg>
        {notificationsStore.unreadCount > 0 && (
          <span className="badge">{notificationsStore.unreadCount > 99 ? '99+' : notificationsStore.unreadCount}</span>
        )}
      </button>

      {isOpen && (
        <div className="dropdown-panel glass" data-testid="notifications-panel">
          <div className="dropdown-header">
            <h3>Notifications</h3>
            <div className="header-actions">
              {notificationsStore.unreadCount > 0 && (
                <button onClick={() => notificationsStore.markAllAsRead()} className="mark-all-btn">Mark all read</button>
              )}
            </div>
          </div>

          <div className="dropdown-body">
            {notificationsStore.isLoading ? (
              <div className="loading-state"><div className="loading-spinner"></div></div>
            ) : notificationsStore.notifications.length === 0 ? (
              <div className="empty-state">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor" className="empty-icon">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
                </svg>
                <p>No notifications yet</p>
              </div>
            ) : (
              <div className="notifications-list">
                {notificationsStore.notifications.map(notification => (
                  <div
                    key={notification.id}
                    className={`notification-item ${!notification.read ? 'unread' : ''} ${notification.type}`}
                    onClick={() => handleNotificationClick(notification)}
                  >
                    <div className="notification-icon">
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                        <path fillRule="evenodd" d={getNotificationIcon(notification.type)} clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="notification-content">
                      <p className="notification-title">{notification.title}</p>
                      <p className="notification-message">{notification.message}</p>
                      <span className="notification-time">{formatTime(notification.createdAt)}</span>
                    </div>
                    <button onClick={e => { e.stopPropagation(); notificationsStore.deleteNotification(notification.id) }} className="delete-btn" aria-label="Delete notification">×</button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {notificationsStore.notifications.length > 0 && (
            <div className="dropdown-footer">
              <button onClick={() => notificationsStore.clearAll()} className="clear-all-btn">Clear all</button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default NotificationsDropdown

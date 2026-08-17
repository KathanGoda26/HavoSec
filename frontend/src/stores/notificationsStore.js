import { create } from 'zustand'

const useNotificationsStore = create((set, get) => ({
  // Static notifications store — no API/WebSocket calls
  notifications: [],
  unreadCount: 0,
  isLoading: false,
  isConnected: false,

  // Derived getters
  get hasUnread() {
    return get().unreadCount > 0
  },

  get recentNotifications() {
    return get().notifications.slice(0, 5)
  },

  // All functions are no-ops in static mode
  fetchNotifications: () => {},
  markAsRead: () => {},
  markAllAsRead: () => {},
  deleteNotification: () => {},
  clearAll: () => {},
  connectWebSocket: () => {},
  disconnectWebSocket: () => {},
  requestBrowserNotificationPermission: () => {},
  addNotification: () => {},
}))

export { useNotificationsStore }

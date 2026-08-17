import { create } from 'zustand'

const useDashboardStore = create(() => ({
  // Static dashboard store — populated with mock data
  overview: {
    stats: [
      { label: 'Total Threats', value: '1,284', change: '+12%', changeType: 'negative', icon: 'shield' },
      { label: 'System Health', value: '98.2%', change: '+0.5%', changeType: 'positive', icon: 'heart' },
      { label: 'Active Scans', value: '42', change: '-2', changeType: 'neutral', icon: 'activity' },
      { label: 'Security Score', value: '85/100', change: '+5', changeType: 'positive', icon: 'star' }
    ]
  },
  attackInsights: {
    threatLevel: 'Moderate',
    topAttacks: [
      { type: 'SQL Injection', count: 450, trend: 'up' },
      { type: 'XSS', count: 320, trend: 'down' },
      { type: 'Brute Force', count: 280, trend: 'stable' }
    ]
  },
  defenseMetrics: {
    blockedRequests: '12.5k',
    wafEfficiency: '99.9%'
  },
  activityLogs: [
    { id: 1, message: 'Malicious IP blocked: 192.168.1.105', time: '2 mins ago', type: 'security' },
    { id: 2, message: 'New vulnerability scan completed', time: '15 mins ago', type: 'info' },
    { id: 3, message: 'Admin login from unrecognized device', time: '1 hour ago', type: 'warning' },
    { id: 4, message: 'System backup successful', time: '3 hours ago', type: 'success' }
  ],
  systemHealth: {
    cpu: 45,
    memory: 62,
    disk: 38,
    uptime: '15d 4h 22m'
  },
  isLoading: false,
  error: null,

  // All fetch functions are no-ops in static mode
  fetchOverview: () => {},
  fetchAttackInsights: () => {},
  fetchDefenseMetrics: () => {},
  fetchActivityLogs: () => {},
  fetchSystemHealth: () => {},
  exportLogs: () => {},
  startRealTimeUpdates: () => {},
}))

export { useDashboardStore }

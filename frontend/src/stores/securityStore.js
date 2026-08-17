import { create } from 'zustand'

const useSecurityStore = create((set, get) => ({
  // Static security store — populated with mock data
  currentScan: {
    id: 'SCAN-2024-001',
    status: 'completed',
    progress: 100,
    startedAt: new Date(Date.now() - 7200000),
    vulnerabilities: [
      { id: 'VULN-001', title: 'SQL Injection in Login', severity: 'critical', cvss: 9.8, status: 'open' },
      { id: 'VULN-002', title: 'Cross-Site Scripting', severity: 'high', cvss: 7.5, status: 'patched' },
      { id: 'VULN-003', title: 'Weak Password Policy', severity: 'medium', cvss: 5.3, status: 'open' }
    ]
  },
  scanHistory: [
    { id: 'SCAN-2024-001', status: 'completed', date: '2024-01-20' },
    { id: 'SCAN-2023-099', status: 'completed', date: '2024-01-15' }
  ],
  isScanning: false,
  workflows: [
    { id: 1, name: 'Full Network Audit', description: 'Deep scan of all network components' },
    { id: 2, name: 'Web App Security', description: 'Focused scan on web vulnerabilities' }
  ],
  agentStatus: {
    online: 12,
    offline: 2,
    busy: 5
  },
  statistics: {
    totalScans: 156,
    threatsBlocked: 2450,
    avgRemediationTime: '4.2h'
  },
  error: null,

  // All actions are no-ops in static mode
  fetchWorkflows: () => {},
  startScan: () => {},
  fetchAgentStatus: () => {},
  fetchStatistics: () => {},
  fetchHistory: () => {},

  // Getters
  getWorkflowById: (id) => {
    return get().workflows.find(w => w.id === id)
  },
  hasActiveScan: () => {
    const state = get()
    return state.isScanning || (state.currentScan && state.currentScan.status === 'started')
  }
}))

export { useSecurityStore }

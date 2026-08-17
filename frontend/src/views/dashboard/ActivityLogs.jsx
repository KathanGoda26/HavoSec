import React, { useState, useMemo, useEffect } from 'react'
import { useContentStore } from '@/stores/contentStore'

const mockLogsData = [
  {
    id: 'EVT-9081',
    time: '2026-06-01 11:45:22',
    category: 'Auth Guard',
    description: 'Successful administrator login detected',
    ip: '10.0.0.101',
    severity: 'low',
    status: 'resolved'
  },
  {
    id: 'EVT-9076',
    time: '2026-06-01 11:32:05',
    category: 'Firewall',
    description: 'XSS payload attempt detected in search parameters',
    ip: '192.168.4.15',
    severity: 'high',
    status: 'blocked'
  },
  {
    id: 'EVT-9069',
    time: '2026-06-01 11:21:49',
    category: 'IDS Scan',
    description: 'Automated TCP port sweep detected across backend range',
    ip: '203.0.113.80',
    severity: 'medium',
    status: 'resolved'
  },
  {
    id: 'EVT-9055',
    time: '2026-06-01 11:10:12',
    category: 'WAF Block',
    description: 'SQL Injection signature matches request body parameters',
    ip: '185.190.140.2',
    severity: 'critical',
    status: 'blocked'
  },
  {
    id: 'EVT-9042',
    time: '2026-06-01 10:55:34',
    category: 'Integrity',
    description: 'Unscheduled software update check completed',
    ip: '127.0.0.1',
    severity: 'low',
    status: 'resolved'
  },
  {
    id: 'EVT-9031',
    time: '2026-06-01 10:32:18',
    category: 'Auth Guard',
    description: 'Brute-force attack warning: 5 failed attempts reached',
    ip: '94.200.12.65',
    severity: 'high',
    status: 'quarantined'
  },
  {
    id: 'EVT-9022',
    time: '2026-06-01 09:44:10',
    category: 'IDS Scan',
    description: 'File integrity check: /var/www/html matches baseline hashes',
    ip: '10.0.0.1',
    severity: 'low',
    status: 'resolved'
  },
  {
    id: 'EVT-9011',
    time: '2026-06-01 09:12:04',
    category: 'WAF Block',
    description: 'Attempt to download sensitive file /etc/passwd denied',
    ip: '198.51.100.42',
    severity: 'critical',
    status: 'blocked'
  }
]

function ActivityLogs() {
  const contentStore = useContentStore()

  const [searchQuery, setSearchQuery] = useState('')
  const [activeFilter, setActiveFilter] = useState('all')

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
    return contentStore.clientDashboard?.activityLogs?.title || 'Activity Logs'
  }, [contentStore.clientDashboard?.activityLogs?.title])

  const pageDescription = useMemo(() => {
    return contentStore.clientDashboard?.activityLogs?.description || 'View and analyze security activity logs'
  }, [contentStore.clientDashboard?.activityLogs?.description])

  const filteredLogs = useMemo(() => {
    return mockLogsData.filter(log => {
      // Severity Filter
      if (activeFilter !== 'all' && log.severity !== activeFilter) {
        return false
      }

      // Search query matching description, category, or IP
      if (searchQuery.trim() !== '') {
        const query = searchQuery.toLowerCase()
        const descMatch = log.description.toLowerCase().includes(query)
        const ipMatch = log.ip.toLowerCase().includes(query)
        const categoryMatch = log.category.toLowerCase().includes(query)
        return descMatch || ipMatch || categoryMatch
      }

      return true
    })
  }, [activeFilter, searchQuery])

  return (
    <div className="activity-logs-page">
      <div className="page-header">
        <div>
          <h1 className="page-title" data-testid="activity-logs-title">{pageTitle}</h1>
          <p className="page-subtitle">{pageDescription}</p>
        </div>
      </div>

      <div className="logs-content">
        {/* Search & Filtering Controls */}
        <div className="controls-bar">
          <div className="search-input-wrapper">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth="2"
              stroke="currentColor"
              className="search-icon"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.637 10.637z"
              />
            </svg>
            <input
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              type="text"
              placeholder="Search security description or source IP..."
              className="search-input"
            />
          </div>

          <div className="filter-buttons">
            {['all', 'critical', 'high', 'medium', 'low'].map(filter => (
              <button
                key={filter}
                onClick={() => setActiveFilter(filter)}
                className={`filter-btn ${activeFilter === filter ? 'active' : ''}`}
              >
                {filter === 'all' ? 'All Logs' : filter.charAt(0).toUpperCase() + filter.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Logs Glass Table */}
        <div className="glass ui-card">
          <table className="ui-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Event ID</th>
                <th>Category</th>
                <th>Description</th>
                <th>Source IP</th>
                <th>Severity</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {filteredLogs.map(log => (
                <tr key={log.id}>
                  <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-dim)' }}>
                    {log.time}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, fontSize: '0.8rem' }}>
                    {log.id}
                  </td>
                  <td>
                    <span style={{ fontWeight: 600, fontSize: '0.8rem', color: '#a78bfa' }}>
                      {log.category}
                    </span>
                  </td>
                  <td>{log.description}</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>
                    {log.ip}
                  </td>
                  <td>
                    <span className={`severity-badge ${log.severity}`}>
                      {log.severity}
                    </span>
                  </td>
                  <td>
                    <span className={`status-badge status-${log.status}`}>
                      {log.status}
                    </span>
                  </td>
                </tr>
              ))}
              {filteredLogs.length === 0 && (
                <tr>
                  <td colSpan="7" style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-dim)' }}>
                    No matching security logs found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default ActivityLogs

import React, { useState, useEffect, useRef, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { Chart, registerables } from 'chart.js'
import { useDashboardStore } from '@/stores/dashboardStore'
import { useContentStore } from '@/stores/contentStore'
import Widget from '@/components/ui/Widget'
import Card from '@/components/ui/Card'
import SecurityScanner from '@/components/SecurityScanner'
import {
  ShieldCheckIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  HeartIcon,
  BugAntIcon,
  FireIcon,
  EyeIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline'

Chart.register(...registerables)

function formatDate(dateString) {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now - date

  if (diff < 60000) return 'Just now'
  if (diff < 3600000) return Math.floor(diff / 60000) + 'm ago'
  if (diff < 86400000) return Math.floor(diff / 3600000) + 'h ago'
  return Math.floor(diff / 86400000) + 'd ago'
}

function getEventIcon(eventType) {
  const icons = {
    attack_blocked: ShieldCheckIcon,
    malware_detected: BugAntIcon,
    ddos_mitigated: FireIcon,
    intrusion_attempt: ExclamationTriangleIcon,
    vulnerability_scan: EyeIcon,
  }
  const Icon = icons[eventType] || ExclamationTriangleIcon
  return <Icon className="icon-xs" />
}

function Overview() {
  const dashboardStore = useDashboardStore()
  const contentStore = useContentStore()

  const timelineCanvasRef = useRef(null)
  const attackTypesCanvasRef = useRef(null)

  const [loading, setLoading] = useState(true)
  const [recentEvents, setRecentEvents] = useState([])

  const overview = useDashboardStore(state => state.overview)

  // Dynamic content from content store with fallbacks
  const pageTitle = useMemo(() => {
    return contentStore.clientDashboard?.pageTitle || 'Security Overview'
  }, [contentStore.clientDashboard?.pageTitle])

  const pageDescription = useMemo(() => {
    return (
      contentStore.clientDashboard?.pageDescription ||
      'Real-time security monitoring and threat analysis'
    )
  }, [contentStore.clientDashboard?.pageDescription])

  const stats = useMemo(() => {
    return (
      contentStore.clientDashboard?.stats || [
        { label: 'Total Events' },
        { label: 'Events (24h)' },
        { label: 'Blocked Attacks' },
        { label: 'System Uptime' },
      ]
    )
  }, [contentStore.clientDashboard?.stats])

  const threatActivityEnabled = useMemo(() => {
    return contentStore.clientDashboard?.charts?.threatActivity?.enabled !== false
  }, [contentStore.clientDashboard?.charts?.threatActivity?.enabled])

  const threatActivityTitle = useMemo(() => {
    return (
      contentStore.clientDashboard?.charts?.threatActivity?.title ||
      'Threat Activity (Last 7 Days)'
    )
  }, [contentStore.clientDashboard?.charts?.threatActivity?.title])

  const attackTypesEnabled = useMemo(() => {
    return contentStore.clientDashboard?.charts?.attackTypes?.enabled !== false
  }, [contentStore.clientDashboard?.charts?.attackTypes?.enabled])

  const attackTypesTitle = useMemo(() => {
    return (
      contentStore.clientDashboard?.charts?.attackTypes?.title ||
      'Attack Types Distribution'
    )
  }, [contentStore.clientDashboard?.charts?.attackTypes?.title])

  const showCharts = useMemo(() => {
    return threatActivityEnabled || attackTypesEnabled
  }, [threatActivityEnabled, attackTypesEnabled])

  useEffect(() => {
    let active = true

    async function loadData() {
      try {
        await dashboardStore.fetchOverview()
        try {
          if (contentStore.fetchClientDashboard) {
            await contentStore.fetchClientDashboard()
          }
        } catch (contentError) {
          console.warn(
            'Could not load client dashboard content, using defaults:',
            contentError
          )
        }

        if (active) {
          setRecentEvents([
            {
              id: '1',
              eventType: 'attack_blocked',
              severity: 'high',
              description: 'SQL injection attack blocked on login endpoint',
              source: { ip: '192.168.1.100' },
              status: 'blocked',
              createdAt: new Date(Date.now() - 300000), // 5 minutes ago
            },
            {
              id: '2',
              eventType: 'malware_detected',
              severity: 'critical',
              description: 'Malware signature detected in file upload',
              source: { ip: '10.0.0.15' },
              status: 'quarantined',
              createdAt: new Date(Date.now() - 900000), // 15 minutes ago
            },
            {
              id: '3',
              eventType: 'ddos_mitigated',
              severity: 'medium',
              description: 'DDoS attack attempt mitigated successfully',
              source: { ip: '203.0.113.50' },
              status: 'resolved',
              createdAt: new Date(Date.now() - 1800000), // 30 minutes ago
            },
          ])
          setLoading(false)
        }
      } catch (error) {
        console.error('Failed to load overview data:', error)
        if (active) {
          setLoading(false)
        }
      }
    }

    loadData()

    return () => {
      active = false
    }
  }, [])

  // Create & clean up Chart.js instances
  useEffect(() => {
    if (loading) return

    let timelineChartInstance = null
    let attackTypesChartInstance = null

    // Timeline Chart
    if (threatActivityEnabled && timelineCanvasRef.current) {
      const labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
      const data = [12, 19, 8, 15, 22, 18, 25]

      timelineChartInstance = new Chart(timelineCanvasRef.current, {
        type: 'line',
        data: {
          labels,
          datasets: [
            {
              label: 'Security Events',
              data,
              borderColor: 'rgb(139, 92, 246)',
              backgroundColor: 'rgba(139, 92, 246, 0.1)',
              fill: true,
              tension: 0.4,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false,
            },
          },
          scales: {
            y: {
              beginAtZero: true,
            },
          },
        },
      })
    }

    // Attack Types Chart
    if (attackTypesEnabled && attackTypesCanvasRef.current) {
      const data = [30, 25, 20, 15, 10]
      const labels = ['Malware', 'Phishing', 'DDoS', 'Intrusion', 'Other']

      attackTypesChartInstance = new Chart(attackTypesCanvasRef.current, {
        type: 'doughnut',
        data: {
          labels,
          datasets: [
            {
              data,
              backgroundColor: [
                '#8b5cf6',
                '#10b981',
                '#f59e0b',
                '#ef4444',
                '#6b7280',
              ],
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'bottom',
            },
          },
        },
      })
    }

    return () => {
      if (timelineChartInstance) timelineChartInstance.destroy()
      if (attackTypesChartInstance) attackTypesChartInstance.destroy()
    }
  }, [loading, threatActivityEnabled, attackTypesEnabled])

  return (
    <div className="overview-page">
      <div className="page-header">
        <div>
          <h1 className="page-title" data-testid="overview-title">{pageTitle}</h1>
          <p className="page-subtitle">{pageDescription}</p>
        </div>
        <SecurityScanner />
      </div>

      {loading ? (
        <div className="loading-container" data-testid="loading-overview">
          <div className="loading-spinner-large"></div>
          <p>Loading security data...</p>
        </div>
      ) : (
        <div className="overview-content">
          {/* Stats Grid */}
          <section className="stats-section" data-testid="stats-section">
            <div className="stats-grid">
              <Widget
                title={stats[0]?.label || 'Total Events'}
                value={overview.totalEvents || 0}
                icon={ShieldCheckIcon}
                color="blue"
                data-testid="total-events-card"
              />

              <Widget
                title={stats[1]?.label || 'Events (24h)'}
                subtitle="Last 24 hours"
                value={overview.events24h || 0}
                icon={ClockIcon}
                color="green"
                trend={overview.trends?.percentage || 0}
                data-testid="events-24h-card"
              />

              <Widget
                title={stats[2]?.label || 'Blocked Attacks'}
                value={overview.blockedAttacks || 0}
                icon={ExclamationTriangleIcon}
                color="red"
                data-testid="blocked-attacks-card"
              />

              <Widget
                title={stats[3]?.label || 'System Uptime'}
                value={overview.systemUptime || 0}
                icon={HeartIcon}
                color="purple"
                format="percentage"
                data-testid="system-uptime-card"
              />
            </div>
          </section>

          {/* Charts Section */}
          {showCharts && (
            <section className="charts-section">
              <div className="charts-grid">
                {/* Threat Timeline Chart */}
                {threatActivityEnabled && (
                  <Card
                    title={threatActivityTitle}
                    icon={ShieldCheckIcon}
                    data-testid="threat-timeline-chart"
                  >
                    <div className="chart-container">
                      <canvas ref={timelineCanvasRef}></canvas>
                    </div>
                  </Card>
                )}

                {/* Attack Types Distribution */}
                {attackTypesEnabled && (
                  <Card
                    title={attackTypesTitle}
                    icon={ChartBarIcon}
                    data-testid="attack-types-chart"
                  >
                    <div className="chart-container">
                      <canvas ref={attackTypesCanvasRef}></canvas>
                    </div>
                  </Card>
                )}
              </div>
            </section>
          )}

          {/* Recent Events */}
          <section className="recent-events-section" data-testid="recent-events">
            <div className="section-header">
              <h2 className="section-title">Recent Security Events</h2>
              <Link to="/dashboard/activity-logs" className="view-all-link">
                View All Logs →
              </Link>
            </div>

            <div className="events-list glass">
              {recentEvents.map(event => (
                <div
                  key={event.id}
                  className="event-item"
                  data-testid={`event-${event.id}`}
                >
                  <div className={`event-icon severity-${event.severity}`}>
                    {getEventIcon(event.eventType)}
                  </div>
                  <div className="event-content">
                    <p className="event-description">{event.description}</p>
                    <p className="event-meta">
                      {event.eventType} • {event.source?.ip || 'Unknown'} •{' '}
                      {formatDate(event.createdAt)}
                    </p>
                  </div>
                  <div className="event-status">
                    <span className={`status-badge status-${event.status}`}>
                      {event.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      )}
    </div>
  )
}

export default Overview

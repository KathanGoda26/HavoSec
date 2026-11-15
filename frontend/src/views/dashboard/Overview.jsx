import React, { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { Chart, registerables } from 'chart.js'
import Widget from '@/components/ui/Widget'
import Card from '@/components/ui/Card'
import ResourceState from '@/components/ui/ResourceState'
import usePollingResource from '@/hooks/usePollingResource'
import { useThemeStore } from '@/stores/themeStore'
import { ShieldCheckIcon, ClockIcon, ExclamationTriangleIcon, ChartBarIcon } from '@heroicons/react/24/outline'
import { FINDING_STATUS_LABELS } from '@/dashboard/findings/status'
import { RUN_STATUS_LABELS } from '@/dashboard/security-runs/status'
import { ACTIVITY_TYPES } from '@/dashboard/activity/activity'
import { SEVERITY_COLORS } from '@/dashboard/overview/overview'
import { securityApi, displayDate } from '@/services/securityApi'

Chart.register(...registerables)

function Overview() {
  const severityCanvasRef = useRef(null)
  const isDark = useThemeStore(state => state.isDark)
  const { data, loading, error, reload } = usePollingResource(() => securityApi.getOverview({}), [])
  const severity = data ? Object.entries(data.severity_counts).map(([name, count]) => ({ name, count })) : []

  useEffect(() => {
    if (!severityCanvasRef.current || !data?.open_findings) return undefined
    const chart = new Chart(severityCanvasRef.current, {
      type: 'doughnut',
      data: { labels: severity.map(item => item.name), datasets: [{ data: severity.map(item => item.count), backgroundColor: severity.map(item => SEVERITY_COLORS[item.name] || '#64748b') }] },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { color: isDark ? '#c4bfd4' : '#5c566b' } } } },
    })
    return () => chart.destroy()
  }, [data, isDark])

  if (loading || error) return <ResourceState loading={loading} error={error} onRetry={reload} noun="security overview" />
  const latest = data.latest_security_run
  return <div className="overview-page">
    <div className="page-header"><div><h1 className="page-title" data-testid="overview-title">Overview</h1><p className="page-subtitle">Live organization-scoped security posture and recent lifecycle activity.</p></div><Link to="/dashboard/security-runs" className="btn-primary">Security Runs</Link></div>
    <div className="overview-content">
      <section className="stats-section" aria-label="Workspace summary"><div className="stats-grid">
        <Widget title="Security Score" value="—" subtitle="Scoring model unavailable" icon={ShieldCheckIcon} />
        <Widget title="Open Findings" value={data.open_findings} subtitle="Unresolved findings" icon={ChartBarIcon} />
        <Widget title="Critical Findings" value={data.critical_findings} subtitle="Critical and unresolved" icon={ExclamationTriangleIcon} />
        <Widget title="Latest Security Run" value={latest ? displayDate(latest.started_at) : '—'} subtitle={latest ? RUN_STATUS_LABELS[latest.status] : 'No security runs'} icon={ClockIcon} />
      </div></section>
      <section className="charts-section"><div className="charts-grid">
        <Card title="Assessment Coverage" icon={ShieldCheckIcon}><div className="empty-state"><h3>Unavailable</h3><p>HavoSec does not yet calculate a legitimate security score or historical coverage trend.</p></div></Card>
        <Card title="Severity Distribution" icon={ChartBarIcon}>{data.open_findings ? <div className="chart-container"><canvas ref={severityCanvasRef} role="img" aria-label={severity.map(item => `${item.name}: ${item.count}`).join('; ')} /></div> : <p>No open findings recorded. This does not establish that the workspace is secure.</p>}</Card>
      </div></section>
      <section className="recent-events-section"><div className="section-header"><h2 className="section-title">Recent Findings</h2><Link to="/dashboard/findings" className="view-all-link">View Findings →</Link></div><div className="events-list glass">{data.recent_findings.map(finding => <div key={finding.id} className="event-item"><div className={`event-icon severity-${finding.severity}`}><ShieldCheckIcon className="icon-xs" /></div><div className="event-content"><p className="event-description">{finding.title}</p><p className="event-meta">{finding.location || 'Location unavailable'} · {displayDate(finding.last_detected_at)}</p></div><span className={`severity-badge ${finding.severity}`}>{finding.severity}</span><span className="status-badge">{FINDING_STATUS_LABELS[finding.status] || finding.status}</span></div>)}{!data.recent_findings.length && <p>No findings recorded.</p>}</div></section>
      <section className="recent-events-section"><div className="section-header"><h2 className="section-title">Recent Security Runs</h2><Link to="/dashboard/security-runs" className="view-all-link">View Runs →</Link></div><div className="events-list glass">{data.recent_runs.map(run => <div key={run.id} className="event-item"><div className="event-icon"><ClockIcon className="icon-xs" /></div><div className="event-content"><Link to={`/dashboard/security-runs/${run.id}`} className="event-description">{run.type}</Link><p className="event-meta">{displayDate(run.started_at || run.created_at)}</p></div><span className="status-badge">{RUN_STATUS_LABELS[run.status] || run.status}</span></div>)}{!data.recent_runs.length && <p>No security runs recorded.</p>}</div></section>
      <Card title="Remediation"><p>{data.counts.remediations} remediation records.</p><Link to="/dashboard/remediation">Review Remediation →</Link></Card>
      <section className="recent-events-section"><div className="section-header"><h2 className="section-title">Recent Activity</h2><Link to="/dashboard/activity" className="view-all-link">View Activity →</Link></div><div className="events-list glass">{data.recent_activity.map(event => <div key={event.id} className="event-item"><div className="event-icon"><ChartBarIcon className="icon-xs" /></div><div className="event-content"><p className="event-description">{event.message}</p><p className="event-meta">{ACTIVITY_TYPES[event.event_type] || event.event_type} · {displayDate(event.created_at)}</p></div></div>)}{!data.recent_activity.length && <p>No activity recorded.</p>}</div></section>
    </div>
  </div>
}

export default Overview

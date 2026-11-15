import React, { useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import ResourceState from '@/components/ui/ResourceState'
import usePollingResource from '@/hooks/usePollingResource'
import { securityApi, displayDate } from '@/services/securityApi'
import { ACTIVITY_TYPES, activityView, filterActivity } from '@/dashboard/activity/activity'

function ActivityLogs() {
  const { projectId } = useParams()
  const [searchQuery, setSearchQuery] = useState('')
  const [eventType, setEventType] = useState('all')
  const { data, loading, error, reload } = usePollingResource(
    () => securityApi.listActivity({ limit: 100, ...(projectId ? { project_id: projectId } : {}) }), [projectId])
  const events = useMemo(() => (data?.items || []).map(activityView), [data])
  const filteredLogs = useMemo(() => filterActivity(events, { query: searchQuery, eventType }), [events, searchQuery, eventType])

  return <div className="activity-logs-page">
    <div className="page-header"><div><h1 className="page-title" data-testid="activity-logs-title">Activity</h1><p className="page-subtitle">Recorded project, security run, finding, and remediation lifecycle events.</p></div></div>
    <ResourceState loading={loading} error={error} onRetry={reload} noun="activity" />
    {!loading && !error && <div className="logs-content">
      <div className="controls-bar"><div className="search-input-wrapper"><svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor" className="search-icon"><path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.637 10.637z" /></svg><input value={searchQuery} onChange={event => setSearchQuery(event.target.value)} type="text" placeholder="Search events, entity, project, or actor…" aria-label="Search activity" className="search-input" /></div>
        <select className="search-input" aria-label="Filter activity by event type" value={eventType} onChange={event => setEventType(event.target.value)}><option value="all">All event types</option>{Object.entries(ACTIVITY_TYPES).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select>
      </div>
      <div className="glass ui-card"><table className="ui-table"><thead><tr><th>Timestamp</th><th>Event Type</th><th>Description</th><th>Entity</th><th>Project</th><th>Actor</th></tr></thead><tbody>
        {filteredLogs.map(log => <tr key={log.id}><td>{displayDate(log.created_at)}</td><td><span className="status-badge">{ACTIVITY_TYPES[log.eventType] || log.eventType}</span></td><td>{log.description}</td><td>{log.entity_type} · {log.entity_id}</td><td>{log.project_id}</td><td>{log.actor_id}</td></tr>)}
        {!filteredLogs.length && <tr><td colSpan="6" style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-dim)' }}>No matching activity is recorded.</td></tr>}
      </tbody></table></div>
    </div>}
  </div>
}

export default ActivityLogs

import React, { useMemo, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import ResourceState from '@/components/ui/ResourceState'
import usePollingResource from '@/hooks/usePollingResource'
import { securityApi, displayDate, findingAnalysis } from '@/services/securityApi'
import { getApiError } from '@/services/apiClient'
import { FINDING_STATUS_LABELS } from '@/dashboard/findings/status'
import { useAuthStore } from '@/stores/authStore'
import { USER_ROLES } from '@/constants/auth'

const SEVERITIES = ['critical', 'high', 'medium', 'low', 'info']

function Findings() {
  const { projectId } = useParams()
  const [searchParams] = useSearchParams()
  const selectedProjectId = projectId || searchParams.get('project_id') || ''
  const role = useAuthStore(state => state.user?.role)
  const canManage = role === USER_ROLES.ADMIN || role === USER_ROLES.SUPERADMIN
  const [severity, setSeverity] = useState('')
  const [status, setStatus] = useState('')
  const [selected, setSelected] = useState(null)
  const [mutationError, setMutationError] = useState('')
  const params = { limit: 100, ...(selectedProjectId && { project_id: selectedProjectId }),
    ...(severity && { severity }), ...(status && { status }) }
  const { data, loading, error, reload } = usePollingResource(
    () => securityApi.listFindings(params), [selectedProjectId, severity, status])
  const findings = data?.items || []
  const counts = useMemo(() => Object.fromEntries(SEVERITIES.map(level =>
    [level, findings.filter(finding => finding.severity === level).length])), [findings])
  const sorted = useMemo(() => [...findings].sort((a, b) =>
    SEVERITIES.indexOf(a.severity) - SEVERITIES.indexOf(b.severity) ||
    (b.last_detected_at || '').localeCompare(a.last_detected_at || '')), [findings])

  const updateStatus = async (finding, nextStatus) => {
    setMutationError('')
    try {
      const updated = await securityApi.updateFinding(finding.id, nextStatus)
      setSelected(updated); reload()
    } catch (requestError) {
      setMutationError(getApiError(requestError, 'The finding status could not be updated.'))
    }
  }

  return <div className="attack-insights-page">
    <h1 className="page-title">Findings</h1>
    <p className="page-subtitle">Normalized scanner findings scoped to your organization and selected project.</p>
    <div className="filters-section" aria-label="Finding filters">
      <select className="filter-btn" value={severity} onChange={event => setSeverity(event.target.value)} aria-label="Severity">
        <option value="">All severities</option>{SEVERITIES.map(value => <option key={value} value={value}>{value}</option>)}
      </select>
      <select className="filter-btn" value={status} onChange={event => setStatus(event.target.value)} aria-label="Status">
        <option value="">All statuses</option>{Object.entries(FINDING_STATUS_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
      </select>
    </div>
    <ResourceState loading={loading} error={error} onRetry={reload} noun="findings" />
    {!loading && !error && <>
      <div className="summary-grid">{SEVERITIES.slice(0, 4).map(level => <div key={level} className={`summary-card ${level}`}>
        <div className="card-content"><h4>{level}</h4><p className="card-value">{counts[level]}</p><span className="card-label">Visible findings</span></div>
      </div>)}</div>
      {sorted.length ? <div className="vulnerabilities-section"><h2>Discovered Findings</h2><div className="vulnerabilities-list">
        {sorted.map(finding => {
          const analysis = findingAnalysis(finding)
          return <div key={finding.id} className={`vuln-card ${finding.severity}`}>
            <div className="vuln-header"><div className="vuln-title-section"><h4>{finding.title}</h4><span className="vuln-id">{finding.source_metadata?.rule_id || finding.id}</span></div>
              <div className="vuln-badges"><span className={`severity-badge ${finding.severity}`}>{finding.severity}</span>
                <span className="cvss-badge">{FINDING_STATUS_LABELS[finding.status] || finding.status}</span>
                {analysis?.priority && <span className={`priority-badge ${analysis.priority}`}>{analysis.priority} priority</span>}
              </div></div>
            <p className="vuln-description">{finding.description}</p>
            <p className="vuln-description">{finding.location || finding.affected_component || 'Location unavailable'} · Last detected {displayDate(finding.last_detected_at)}</p>
            <div className="vuln-actions"><button type="button" className="btn-secondary" onClick={() => { setSelected(finding); setMutationError('') }}>View Details</button>
              {(finding.last_security_run_id || finding.security_run_id) && <Link className="btn-secondary" to={`/dashboard/security-runs/${finding.last_security_run_id || finding.security_run_id}`}>View Run</Link>}</div>
          </div>
        })}
      </div></div> : <div className="empty-state"><h2>No Findings</h2><p>No findings match this workspace and filter. This does not establish that the repository is secure.</p></div>}
    </>}

    {selected && <div className="modal-overlay" onClick={() => setSelected(null)}>
      <div className="modal-container" role="dialog" aria-modal="true" aria-labelledby="finding-heading" onClick={event => event.stopPropagation()}>
        <div className="modal-header"><h2 id="finding-heading">{selected.title}</h2><button type="button" className="close-btn" aria-label="Close finding" onClick={() => setSelected(null)}>×</button></div>
        <div className="modal-body">
          <p>{selected.description}</p>
          <div className="technical-grid">
            <div className="tech-detail"><span className="label">Severity:</span><span className="value">{selected.severity}</span></div>
            <div className="tech-detail"><span className="label">Confidence:</span><span className="value">{selected.confidence ?? 'Not assessed'}</span></div>
            <div className="tech-detail"><span className="label">Location:</span><span className="value">{selected.location || 'Unavailable'}</span></div>
            <div className="tech-detail"><span className="label">Commit:</span><span className="value">{selected.source_metadata?.commit_sha || 'Unavailable'}</span></div>
          </div>
          <div className="detail-section"><h4>Scanner Evidence</h4><p>Rule: {selected.evidence?.rule_id || 'Unavailable'}</p><p>{selected.evidence?.scanner_message || 'No scanner message available.'}</p></div>
          {findingAnalysis(selected) && <div className="detail-section"><h4>Agent Analysis</h4><p>{findingAnalysis(selected).risk_summary}</p><h4>Recommended Remediation</h4><p>{findingAnalysis(selected).remediation}</p></div>}
          {!findingAnalysis(selected) && <div className="detail-section"><h4>Analysis</h4><p>This finding contains deterministic scanner analysis only.</p></div>}
          {mutationError && <p role="alert" className="form-error">{mutationError}</p>}
        </div>
        <div className="modal-footer">
          {canManage && selected.status !== 'resolved' && <select value={selected.status} onChange={event => updateStatus(selected, event.target.value)} aria-label="Update finding status">
            {Object.entries(FINDING_STATUS_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>}
          <button type="button" onClick={() => setSelected(null)} className="btn-secondary">Close</button>
        </div>
      </div>
    </div>}
  </div>
}

export default Findings

import React, { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import Card from '@/components/ui/Card'
import ResourceState from '@/components/ui/ResourceState'
import usePollingResource from '@/hooks/usePollingResource'
import { securityApi, displayDate, isActiveRun } from '@/services/securityApi'
import { getApiError } from '@/services/apiClient'
import { useAuthStore } from '@/stores/authStore'
import { USER_ROLES } from '@/constants/auth'
import { RUN_STATUS_LABELS } from './status'

function summaryText(summary) {
  if (!summary) return 'No result summary is available yet.'
  return `${summary.normalized_findings ?? 0} normalized findings · ${summary.agent_enriched ?? 0} agent enriched · ${summary.duration_seconds ?? '—'} seconds`
}

export default function SecurityRuns() {
  const { projectId } = useParams()
  const navigate = useNavigate()
  const role = useAuthStore(state => state.user?.role)
  const canManage = role === USER_ROLES.ADMIN || role === USER_ROLES.SUPERADMIN
  const [assetId, setAssetId] = useState('')
  const [type, setType] = useState('standard')
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')
  const { data, loading, error, reload } = usePollingResource(async () => {
    const params = projectId ? { project_id: projectId } : {}
    const [runs, assets] = await Promise.all([securityApi.listRuns(params), securityApi.listAssets(params)])
    return { runs: runs.items, assets: assets.items.filter(asset => asset.type === 'repository' && asset.status === 'active') }
  }, [projectId], { shouldPoll: value => value.runs.some(isActiveRun) })
  const base = projectId ? `/dashboard/projects/${projectId}/security-runs` : '/dashboard/security-runs'

  const createRun = async event => {
    event.preventDefault()
    const asset = data.assets.find(item => item.id === assetId)
    if (!asset) return
    setSubmitting(true); setSubmitError('')
    try {
      const run = await securityApi.createRun({ project_id: asset.project_id, asset_ids: [asset.id], type })
      navigate(`${base}/${run.id}`)
    } catch (requestError) {
      setSubmitError(getApiError(requestError, 'The security run could not be created.'))
    } finally { setSubmitting(false) }
  }

  return <div className="projects-page">
    <h1 className="page-title">Security Runs</h1>
    <p className="page-subtitle">Live static-analysis runs from the organization execution queue.</p>
    <ResourceState loading={loading} error={error} onRetry={reload} noun="security runs" />
    {!loading && !error && canManage && <Card title="New Security Run">
      <form onSubmit={createRun} className="dashboard-inline-form">
        <label>Repository asset<select value={assetId} onChange={event => setAssetId(event.target.value)} required>
          <option value="">Select an authorized repository</option>
          {data.assets.map(asset => <option key={asset.id} value={asset.id}>{asset.name} — {asset.target}</option>)}
        </select></label>
        <label>Run type<select value={type} onChange={event => setType(event.target.value)}>
          <option value="quick">Quick</option><option value="standard">Standard</option><option value="full">Full</option>
        </select></label>
        <button type="submit" className="btn-primary" disabled={submitting || !assetId}>{submitting ? 'Queueing…' : 'Queue Security Run'}</button>
      </form>
      {!data.assets.length && <p>No active repository asset is available.</p>}
      {submitError && <p role="alert" className="form-error">{submitError}</p>}
    </Card>}
    {!loading && !error && (data.runs.length ? <div className="projects-grid">{data.runs.map(run =>
      <Card key={run.id} title={`${run.type.charAt(0).toUpperCase()}${run.type.slice(1)} run`} footer={<Link to={`${base}/${run.id}`} className="btn-secondary">View Run</Link>}>
        <p>{run.id}</p><span className={`status-badge ${run.status}`}>{RUN_STATUS_LABELS[run.status] || run.status}</span>
        <div className="progress-container" aria-label={`${run.progress}% complete`}><div className="progress-fill" style={{ width: `${run.progress}%` }} /></div>
        <p>{summaryText(run.summary)}</p><p>Created {displayDate(run.created_at)}</p>
      </Card>)}</div> : <div className="empty-state"><h2>No Security Runs</h2><p>No runs have been created in this workspace.</p></div>)}
  </div>
}

export function SecurityRunDetail() {
  const { runId, projectId } = useParams()
  const role = useAuthStore(state => state.user?.role)
  const canManage = role === USER_ROLES.ADMIN || role === USER_ROLES.SUPERADMIN
  const [actionError, setActionError] = useState('')
  const base = projectId ? `/dashboard/projects/${projectId}/security-runs` : '/dashboard/security-runs'
  const { data, loading, error, reload } = usePollingResource(async () => {
    const run = await securityApi.getRun(runId)
    if (projectId && run.project_id !== projectId) {
      const mismatch = new Error('Security run does not belong to the selected project')
      mismatch.response = { status: 404, data: { detail: mismatch.message } }
      throw mismatch
    }
    const [asset, findings] = await Promise.all([
      securityApi.getAsset(run.asset_ids[0]), securityApi.listFindings({ security_run_id: run.id, limit: 100 })])
    return { run, asset, findings: findings.items }
  }, [runId, projectId], { shouldPoll: value => isActiveRun(value.run) })

  const cancel = async () => {
    setActionError('')
    try { await securityApi.cancelRun(runId); reload() }
    catch (requestError) { setActionError(getApiError(requestError, 'The run could not be cancelled.')) }
  }

  if (loading || error) return <ResourceState loading={loading} error={error} onRetry={reload} noun="security run" />
  const { run, asset, findings } = data
  return <div className="projects-page">
    <Link to={base}>← Security Runs</Link><h1 className="page-title">{run.type.charAt(0).toUpperCase()}{run.type.slice(1)} Run</h1>
    <p className="page-subtitle">{run.id} · {RUN_STATUS_LABELS[run.status] || run.status}</p>
    <Card title="Run Overview">
      <div className="progress-container" aria-label={`${run.progress}% complete`}><div className="progress-fill" style={{ width: `${run.progress}%` }} /></div>
      <p>Status: <span className={`status-badge ${run.status}`}>{RUN_STATUS_LABELS[run.status] || run.status}</span> · Progress: {run.progress}%</p>
      <p>{summaryText(run.summary)}</p>
      <p>Started: {displayDate(run.started_at)} · Completed: {displayDate(run.completed_at)}</p>
      <p>Commit: {run.commit_sha || 'Not recorded'} · Scanner: {run.scanner ? `${run.scanner} ${run.scanner_version || ''}` : 'Not started'}</p>
      <p>Analysis: {run.analysis_mode || 'Not started'}</p>
      {run.error && <p role="alert" className="form-error">{run.error}</p>}
      {canManage && isActiveRun(run) && <button type="button" className="btn-secondary" onClick={cancel}>Cancel Run</button>}
      {actionError && <p role="alert" className="form-error">{actionError}</p>}
    </Card>
    <Card title="Repository Asset"><Link to={`/dashboard/assets/${asset.id}`}>{asset.name}</Link><p>{asset.target}</p></Card>
    <Card title="Run Findings">
      {findings.length ? <ul>{findings.map(finding => <li key={finding.id}>{finding.title} <span className={`severity-badge ${finding.severity}`}>{finding.severity}</span></li>)}</ul>
        : <p>{isActiveRun(run) ? 'Findings will appear after analysis completes.' : 'No findings were recorded. This does not establish that the repository is secure.'}</p>}
      <Link to={`/dashboard/findings?project_id=${encodeURIComponent(run.project_id)}`}>View project findings</Link>
    </Card>
  </div>
}

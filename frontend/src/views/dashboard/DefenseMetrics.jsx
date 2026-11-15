import React, { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import ResourceState from '@/components/ui/ResourceState'
import usePollingResource from '@/hooks/usePollingResource'
import { securityApi, displayDate, isActiveVerification } from '@/services/securityApi'
import { summarizeRemediations, REMEDIATION_STATUS_LABELS, VERIFICATION_STATUS_LABELS, diffLineType } from '@/dashboard/remediation/status'
import { useAuthStore } from '@/stores/authStore'
import { USER_ROLES } from '@/constants/auth'
import { getApiError } from '@/services/apiClient'
import PullRequestPanel from '@/dashboard/remediation/PullRequestPanel'

const summaryCards = [
  ['pending', 'Pending', 'Proposals to review', 'threats'],
  ['in_progress', 'In Progress', 'Under preparation', 'hardening'],
  ['awaiting_approval', 'Awaiting Approval', 'Human review required', 'patches'],
  ['approved', 'Approved', 'Accepted proposals', 'compliance'],
]

function ShieldIcon() {
  return <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" /></svg>
}

function DiffView({ patch }) {
  if (!patch) return <p>No generated patch is available yet.</p>
  return <pre className="remediation-diff" aria-label="Proposed unified diff"><code>{patch.split('\n').map((line, index) =>
    <span className={`diff-line ${diffLineType(line)}`} key={`${index}-${line}`}>{line || ' '}{'\n'}</span>)}</code></pre>
}

function Metric({ label, value }) {
  return <div className="verification-metric"><span>{label}</span><strong>{value ?? '—'}</strong></div>
}

function DefenseMetrics() {
  const { projectId } = useParams()
  const role = useAuthStore(state => state.user?.role)
  const canManage = role === USER_ROLES.ADMIN || role === USER_ROLES.SUPERADMIN
  const [expandedId, setExpandedId] = useState(null)
  const [mutation, setMutation] = useState({ id: null, action: null, error: '' })
  const { data, loading, error, reload } = usePollingResource(async () => {
    const params = { limit: 100, ...(projectId ? { project_id: projectId } : {}) }
    const [remediations, findings] = await Promise.all([
      securityApi.listRemediations(params),
      securityApi.listFindings(params),
    ])
    return { remediations: remediations.items, findings: new Map(findings.items.map(finding => [finding.id, finding])) }
  }, [projectId], { shouldPoll: value => value.remediations.some(isActiveVerification) })
  const remediations = data?.remediations || []
  const counts = summarizeRemediations(remediations)

  const act = async (item, action) => {
    setMutation({ id: item.id, action, error: '' })
    try {
      if (action === 'verify') await securityApi.verifyRemediation(item.id)
      else await securityApi.updateRemediation(item.id, { status: action })
      reload()
    } catch (requestError) {
      setMutation({ id: item.id, action: null, error: getApiError(requestError, 'The remediation action could not be completed.') })
      return
    }
    setMutation({ id: null, action: null, error: '' })
  }

  return <div className="defense-metrics-page">
    <h1 className="page-title">Remediation</h1>
    <p className="page-subtitle">Organization-scoped remediation proposals. These records do not modify or deploy changes to source repositories.</p>
    <ResourceState loading={loading} error={error} onRetry={reload} noun="remediation proposals" />
    {!loading && !error && (remediations.length ? <div className="defense-content">
      <div className="summary-grid">{summaryCards.map(([status, title, label, className]) => <div className={`summary-card ${className}`} key={status}><div className="card-icon"><ShieldIcon /></div><div className="card-content"><h4>{title}</h4><p className="card-value">{counts[status]}</p><span className="card-label">{label}</span></div></div>)}</div>
      <div className="patches-section"><h2>Remediation Proposals</h2><p className="page-subtitle">Review the stored recommendation and proposed fix alongside its source Finding.</p>
        <div className="patches-list">{remediations.map(item => {
          const finding = data.findings.get(item.finding_id)
          const findingsPath = projectId ? `/dashboard/projects/${projectId}/findings` : `/dashboard/findings?project_id=${encodeURIComponent(item.project_id)}`
          const active = isActiveVerification(item)
          const verification = item.verification_result
          const proposal = item.proposal
          const busy = mutation.id === item.id && mutation.action
          return <article key={item.id} className="patch-card">
            <div className="patch-header"><div><h4>{item.summary}</h4><p className="patch-description">{item.recommendation || 'No recommendation has been recorded.'}</p></div><span className="status-badge">{REMEDIATION_STATUS_LABELS[item.status] || item.status}</span></div>
            <div className="patch-details">
              <div className="detail-item"><span className="label">Finding:</span><span className="value">{finding?.title || item.finding_id}</span></div>
              <div className="detail-item"><span className="label">Severity:</span><span className="value">{finding?.severity || 'Unavailable'}</span></div>
              <div className="detail-item"><span className="label">Validation:</span><span className="value">{item.validation_status || 'Unavailable'}</span></div>
              <div className="detail-item"><span className="label">Verification:</span><span className={`status-badge ${item.verification_status}`}>{VERIFICATION_STATUS_LABELS[item.verification_status] || item.verification_status}</span></div>
              <div className="detail-item"><span className="label">Project:</span><span className="value">{item.project_id}</span></div>
              <div className="detail-item"><span className="label">Source commit:</span><span className="value commit-value">{item.source_commit || 'Unavailable'}</span></div>
              <div className="detail-item"><span className="label">Created:</span><span className="value">{displayDate(item.created_at)}</span></div>
              <div className="detail-item"><span className="label">Updated:</span><span className="value">{displayDate(item.updated_at)}</span></div>
            </div>
            <div className="patch-actions">
              <Link to={findingsPath} className="btn-secondary">View Finding</Link>
              {canManage && !active && item.verification_status !== 'verified' && <button type="button" className="btn-primary" disabled={Boolean(busy)} onClick={() => act(item, 'verify')}>{busy === 'verify' ? 'Queueing…' : proposal ? 'Verify Fix' : 'Generate & Verify'}</button>}
              {canManage && item.status === 'awaiting_approval' && item.verification_status === 'verified' && <button type="button" className="btn-primary" disabled={Boolean(busy)} onClick={() => act(item, 'approved')}>{busy === 'approved' ? 'Approving…' : 'Approve'}</button>}
              {canManage && ['pending', 'awaiting_approval'].includes(item.status) && <button type="button" className="btn-secondary" disabled={Boolean(busy)} onClick={() => act(item, 'rejected')}>{busy === 'rejected' ? 'Rejecting…' : 'Reject'}</button>}
              <button type="button" className="btn-secondary" aria-expanded={expandedId === item.id} aria-controls={`${item.id}-review`} onClick={() => setExpandedId(expandedId === item.id ? null : item.id)}>{expandedId === item.id ? 'Close Review' : 'Review Details'}</button>
            </div>
            {mutation.id === item.id && mutation.error && <p role="alert" className="form-error remediation-action-error">{mutation.error}</p>}
            {expandedId === item.id && <section id={`${item.id}-review`} className="patch-section" aria-label={`Review ${item.summary}`}>
              <div className="review-block"><h4>Original evidence</h4><p>{finding?.description || 'Finding evidence is unavailable.'}</p><p><strong>Location:</strong> {finding?.location || 'Unavailable'} · <strong>Rule:</strong> {finding?.evidence?.rule_id || finding?.category || 'Unavailable'}</p></div>
              <div className="review-block"><h4>Proposed fix</h4><p>{proposal?.explanation || item.proposed_fix || 'A proposal has not been generated.'}</p><DiffView patch={proposal?.patch} />
                {proposal && <><p><strong>Expected security effect:</strong> {proposal.expected_security_effect}</p><p><strong>Affected files:</strong> {proposal.affected_files.join(', ')}</p><p><strong>Confidence:</strong> {Math.round(proposal.confidence * 100)}%</p>
                  <h4>Potential side effects</h4>{proposal.potential_side_effects?.length ? <ul>{proposal.potential_side_effects.map(value => <li key={value}>{value}</li>)}</ul> : <p>None reported by the proposal.</p>}
                  <h4>Recommended human tests</h4>{proposal.recommended_tests?.length ? <ul>{proposal.recommended_tests.map(value => <li key={value}>{value}</li>)}</ul> : <p>No repository-specific tests were recommended.</p>}</>}
              </div>
              <div className="review-block"><h4>Verification result</h4>{verification ? <><p>{verification.summary}</p><div className="verification-grid">
                <Metric label="Original still present" value={verification.original_finding_present == null ? 'Unknown' : verification.original_finding_present ? 'Yes' : 'No'} />
                <Metric label="Before findings" value={verification.before_finding_count} /><Metric label="After findings" value={verification.after_finding_count} />
                <Metric label="New findings" value={verification.new_findings_count} /><Metric label="Equal/higher regressions" value={verification.new_equal_or_higher_findings_count} />
                <Metric label="Scanner" value={`${verification.scanner} ${verification.scanner_version}`} />
              </div><p>Verified at {displayDate(verification.verified_at)}</p></> : <p>{active ? 'Verification is running in the isolated worker.' : 'This proposal has not been scanner-verified.'}</p>}</div>
              <PullRequestPanel remediation={item} canManage={canManage} />
              <p className="remediation-boundary">A verified result applies only to HavoSec’s isolated copy. No customer repository, branch, deployment, or original Finding is changed automatically.</p>
            </section>}
          </article>
        })}</div>
      </div>
    </div> : <div className="empty-state"><div className="empty-icon"><ShieldIcon /></div><h2>No Remediation Proposals</h2><p>No remediation proposals are recorded for this workspace.</p></div>)}
  </div>
}

export default DefenseMetrics

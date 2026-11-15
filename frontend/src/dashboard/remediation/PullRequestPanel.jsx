import React, { useCallback, useEffect, useState } from 'react'
import { ArrowTopRightOnSquareIcon, CheckCircleIcon, ClockIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'
import { securityApi, displayDate } from '@/services/securityApi'
import { getApiError } from '@/services/apiClient'

const ACTIVE_STATES = new Set(['queued', 'creating'])
const ACTIVE_REVERIFICATION = new Set(['queued', 'testing'])
const safeGitHubUrl = value => {
  try { const url = new URL(value); return url.protocol === 'https:' && url.hostname === 'github.com' ? url.href : null }
  catch { return null }
}

function TimelineItem({ complete, active, title, detail }) {
  return <li className={`${complete ? 'complete' : ''} ${active ? 'active' : ''}`}><span className="pr-timeline-icon">{complete ? <CheckCircleIcon /> : active ? <ClockIcon /> : <span />}</span><div><strong>{title}</strong><small>{detail}</small></div></li>
}

export default function PullRequestPanel({ remediation, canManage }) {
  const [eligibility, setEligibility] = useState(null)
  const [pullRequest, setPullRequest] = useState(null)
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState('')
  const load = useCallback(async () => {
    try {
      setEligibility(await securityApi.getPullRequestEligibility(remediation.id))
      try { setPullRequest(await securityApi.getPullRequest(remediation.id)) }
      catch (requestError) { if (requestError.response?.status !== 404) throw requestError }
      setError('')
    } catch (requestError) { setError(getApiError(requestError, 'Pull request status could not be loaded.')) }
    finally { setLoading(false) }
  }, [remediation.id])
  useEffect(() => { load() }, [load])
  useEffect(() => {
    if (!pullRequest || (!ACTIVE_STATES.has(pullRequest.status) && !ACTIVE_REVERIFICATION.has(pullRequest.reverification_status))) return undefined
    const interval = window.setInterval(load, 3500)
    return () => window.clearInterval(interval)
  }, [pullRequest, load])
  const createPullRequest = async () => {
    setCreating(true); setError('')
    try { setPullRequest(await securityApi.createPullRequest(remediation.id)) }
    catch (requestError) { setError(getApiError(requestError, 'The pull request could not be queued.')) }
    finally { setCreating(false) }
  }
  if (loading) return <section className="pr-panel"><p>Checking pull request readiness…</p></section>
  const url = safeGitHubUrl(pullRequest?.pr_url)
  const opened = ['open', 'closed', 'merged'].includes(pullRequest?.status)
  const checksFinished = pullRequest?.checks_status && !['pending', 'queued', 'in_progress', 'unknown'].includes(pullRequest.checks_status)
  const verified = pullRequest?.reverification_status === 'verified'
  return <section className="pr-panel" aria-label="GitHub pull request delivery">
    <div className="pr-panel-header"><div><h4>GitHub delivery</h4><p>Only the scanner-verified patch and exact verified source commit can be delivered.</p></div>{pullRequest && <span className={`integration-status ${pullRequest.status}`}>{pullRequest.status}</span>}</div>
    {error && <p className="form-error integration-error" role="alert"><ExclamationTriangleIcon className="icon-sm" /> {error}</p>}
    {!pullRequest ? <><div className={`pr-eligibility ${eligibility?.eligible ? 'eligible' : 'blocked'}`}><strong>{eligibility?.eligible ? 'Ready to create a pull request' : 'Pull request is not eligible yet'}</strong><span>Source integrity: {eligibility?.source_integrity_status || 'unknown'}</span></div>{!eligibility?.eligible && Boolean(eligibility?.reasons?.length) && <ul className="pr-reasons">{eligibility.reasons.map(reason => <li key={reason}>{reason}</li>)}</ul>}{canManage ? <button type="button" className="btn-primary" disabled={!eligibility?.eligible || creating} onClick={createPullRequest}>{creating ? 'Queueing…' : 'Create pull request'}</button> : eligibility?.eligible && <p className="settings-helper">An organization administrator can create this pull request.</p>}</> : <>
      <ul className="pr-timeline"><TimelineItem complete title="Request queued" detail={displayDate(pullRequest.created_at)} /><TimelineItem complete={opened} active={ACTIVE_STATES.has(pullRequest.status)} title="Branch and pull request" detail={opened ? `${pullRequest.repository_full_name} #${pullRequest.pr_number}` : pullRequest.status === 'failed' ? 'Delivery failed' : 'Secure worker is creating the branch'} /><TimelineItem complete={checksFinished} active={opened && !checksFinished} title="GitHub checks" detail={pullRequest.checks_status || 'Waiting'} /><TimelineItem complete={verified} active={ACTIVE_REVERIFICATION.has(pullRequest.reverification_status)} title="Exact commit re-verification" detail={pullRequest.reverification_status || 'Waiting'} /></ul>
      <div className="pr-summary-grid"><span><strong>Branch</strong>{pullRequest.branch}</span><span><strong>Readiness</strong>{pullRequest.readiness_status}</span><span><strong>Commit</strong><code>{pullRequest.commit_sha?.slice(0, 12) || 'Pending'}</code></span><span><strong>Updated</strong>{displayDate(pullRequest.updated_at)}</span></div>{pullRequest.error && <p className="form-error">{pullRequest.error}</p>}{url && <a className="btn-primary pr-github-link" href={url} target="_blank" rel="noreferrer">View on GitHub <ArrowTopRightOnSquareIcon className="icon-sm" /></a>}
    </>}
  </section>
}

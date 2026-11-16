import React, { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import Card from '@/components/ui/Card'
import ResourceState from '@/components/ui/ResourceState'
import { USER_ROLES } from '@/constants/auth'
import usePollingResource from '@/hooks/usePollingResource'
import { getApiError } from '@/services/apiClient'
import { displayDate, securityApi } from '@/services/securityApi'
import { useAuthStore } from '@/stores/authStore'

const missionPath = '/dashboard/missions'
const organizationQuery = organizationId => organizationId ? `?organization_id=${encodeURIComponent(organizationId)}` : ''
const organizationParams = organizationId => organizationId ? { organization_id: organizationId } : undefined
const pageSize = 25
const maxOffset = 100000
const activeStatuses = new Set(['queued', 'running', 'awaiting_approval'])
const taskLabels = {
  prepare: 'Prepare scope',
  assess: 'Assess fixture',
  summarize: 'Summarize results',
}
const statusLabels = {
  queued: 'Queued',
  running: 'Running',
  awaiting_approval: 'Awaiting approval',
  completed: 'Completed',
  partial: 'Partial',
  failed: 'Failed',
  cancelled: 'Cancelled',
  needs_review: 'Needs review',
}
const actionLabels = { allow: 'Allowed', deny: 'Denied', require_approval: 'Awaiting approval' }

async function loadOptions(list, filters) {
  const items = []
  for (let offset = 0; offset <= maxOffset; offset += 100) {
    const page = await list({ ...filters, limit: 100, offset })
    items.push(...page.items)
    if (!page.items.length || items.length >= page.total) break
  }
  return items
}

function MissionStatus({ status }) {
  return <span className={`status-badge ${status}`}>{statusLabels[status] || status}</span>
}

function CreateMission({ organizationId }) {
  const navigate = useNavigate()
  const [projectId, setProjectId] = useState('')
  const [assetId, setAssetId] = useState('')
  const [objective, setObjective] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')
  const inFlight = useRef(false)
  const mounted = useRef(false)
  const requestKeys = useRef(new Map())
  const scope = organizationParams(organizationId)
  const projects = usePollingResource(() => loadOptions(securityApi.listProjects, { ...scope, status: 'active' }), [organizationId])
  const repositories = usePollingResource(async () => {
    const assets = projectId ? await loadOptions(securityApi.listAssets, { ...scope, project_id: projectId, status: 'active' }) : []
    return { projectId, items: assets.filter(asset => asset.type === 'repository') }
  }, [organizationId, projectId])
  const assets = !repositories.loading && !repositories.error && repositories.data?.projectId === projectId
    ? repositories.data.items : []
  const canSubmit = assets.some(asset => asset.id === assetId) && objective.trim()

  useEffect(() => {
    mounted.current = true
    return () => { mounted.current = false }
  }, [])

  async function submit(event) {
    event.preventDefault()
    if (inFlight.current || !canSubmit) return
    inFlight.current = true
    setSubmitting(true)
    setSubmitError('')
    const payload = { project_id: projectId, asset_id: assetId, objective: objective.trim() }
    const signature = JSON.stringify(payload)
    try {
      if (!requestKeys.current.has(signature)) {
        // getRandomValues also works over HTTP when running the app on a LAN.
        const bytes = crypto.getRandomValues(new Uint8Array(16))
        requestKeys.current.set(signature, Array.from(bytes, byte => byte.toString(16).padStart(2, '0')).join(''))
      }
      const mission = await securityApi.createMission(payload, requestKeys.current.get(signature), scope)
      if (mounted.current) navigate(`${missionPath}/${mission.id}${organizationQuery(organizationId)}`)
    } catch (error) {
      const message = getApiError(error, 'The mission could not be created. Try submitting again.')
      setSubmitError(typeof message === 'string' ? message : 'Check the mission fields and try again.')
    } finally {
      inFlight.current = false
      setSubmitting(false)
    }
  }

  return <Card title="Create mission">
    <ResourceState loading={projects.loading} error={projects.error} onRetry={projects.reload} noun="active projects" />
    {!projects.loading && !projects.error && (projects.data.length ? <>
      <form className="dashboard-inline-form mission-form" onSubmit={submit}>
        <label>Project
          <select required value={projectId} disabled={submitting} onChange={event => {
            setProjectId(event.target.value)
            setAssetId('')
          }}>
            <option value="">Select a project</option>
            {projects.data.map(project => <option key={project.id} value={project.id}>{project.name}</option>)}
          </select>
        </label>
        <label>Repository asset
          <select required value={assetId} disabled={submitting || !assets.length} onChange={event => setAssetId(event.target.value)}>
            <option value="">Select a repository</option>
            {assets.map(asset => <option key={asset.id} value={asset.id}>{asset.name} ({asset.target})</option>)}
          </select>
        </label>
        <label className="mission-objective">Objective
          <textarea required maxLength={1000} value={objective} disabled={submitting} onChange={event => setObjective(event.target.value)} />
        </label>
        <button type="submit" className="btn-primary" disabled={submitting || !canSubmit}>{submitting ? 'Queueing…' : 'Queue mission'}</button>
      </form>
      {projectId && <ResourceState loading={repositories.loading} error={repositories.error} onRetry={repositories.reload} noun="repository assets" />}
      {projectId && repositories.data?.projectId === projectId && !repositories.loading && !repositories.error && !assets.length &&
        <p>This project has no active repository assets.</p>}
      {submitError && <p role="alert" className="form-error">{submitError}</p>}
    </> : <p>Create an active project before queueing a mission.</p>)}
  </Card>
}

function MissionWorkspace({ organizationId, canCreate }) {
  const [offset, setOffset] = useState(0)
  const { data, loading, error, reload } = usePollingResource(
    () => securityApi.listMissions({ ...organizationParams(organizationId), limit: pageSize, offset }), [organizationId, offset],
    { shouldPoll: page => page.items.some(mission => activeStatuses.has(mission.status)) })
  const page = data?.offset === offset ? data : null
  return <>
    {canCreate && <CreateMission organizationId={organizationId} />}
    <section className="mission-list" aria-label="Missions">
      <ResourceState loading={loading || (!page && !error)} error={error} onRetry={reload} noun="missions" />
      {!loading && !error && page && <>
        {page.items.length ? <div className="projects-grid">
          {page.items.map(mission => <Card key={mission.id} footer={
            <Link className="btn-secondary" to={`${missionPath}/${mission.id}${organizationQuery(organizationId)}`}>View mission</Link>
          }>
            <p>{mission.objective}</p>
            <MissionStatus status={mission.status} />
            <p>Updated {displayDate(mission.updated_at)}</p>
          </Card>)}
        </div> : <div className="empty-state"><h2>{offset ? 'No missions on this page' : 'No missions yet'}</h2></div>}
        {(offset > 0 || page.total > pageSize) && <nav className="project-tabs" aria-label="Mission pages">
          <button type="button" className="btn-secondary" disabled={offset === 0} onClick={() => setOffset(offset - pageSize)}>Previous</button>
          <button type="button" className="btn-secondary" disabled={offset + pageSize >= page.total || offset + pageSize > maxOffset} onClick={() => setOffset(offset + pageSize)}>Next</button>
        </nav>}
      </>}
    </section>
  </>
}

function PlatformMissionWorkspace() {
  const [params, setParams] = useSearchParams()
  const organizationId = params.get('organization_id')
  const { data, loading, error, reload } = usePollingResource(() => loadOptions(securityApi.listOrganizations), [])
  const activeOrganizations = data?.filter(organization => organization.status === 'active') || []
  const selected = activeOrganizations.find(organization => organization.id === organizationId)

  if (loading || error) return <ResourceState loading={loading} error={error} onRetry={reload} noun="organizations" />
  if (!activeOrganizations.length) return <div className="empty-state"><h2>No active organizations</h2></div>
  return <>
    <div className="dashboard-inline-form project-tabs">
      <label>Organization
        <select value={selected?.id || ''} onChange={event => {
          const id = event.target.value
          setParams(id ? { organization_id: id } : {})
        }}>
          <option value="">Select an organization</option>
          {activeOrganizations.map(organization => <option key={organization.id} value={organization.id}>{organization.name}</option>)}
        </select>
      </label>
    </div>
    {selected && <MissionWorkspace key={selected.id} organizationId={selected.id} canCreate />}
  </>
}

export default function MissionControl() {
  const role = useAuthStore(state => state.user?.role)
  return <div className="projects-page">
    <h1 className="page-title">Mission Control</h1>
    {role === USER_ROLES.SUPERADMIN
      ? <PlatformMissionWorkspace />
      : <MissionWorkspace canCreate={role === USER_ROLES.ADMIN} />}
  </div>
}

export function MissionDetail() {
  const { missionId } = useParams()
  const [params] = useSearchParams()
  const isPlatform = useAuthStore(state => state.user?.role === USER_ROLES.SUPERADMIN)
  const organizationId = isPlatform ? params.get('organization_id') : null
  if (isPlatform && !organizationId) {
    return <div className="projects-page"><Link to={missionPath}>Select an organization in Mission Control</Link></div>
  }
  return <MissionRecord key={JSON.stringify([organizationId, missionId])} missionId={missionId} organizationId={organizationId} />
}

function MissionRecord({ missionId, organizationId }) {
  const params = organizationParams(organizationId)
  const role = useAuthStore(state => state.user?.role)
  const [cancelling, setCancelling] = useState(false)
  const [cancelError, setCancelError] = useState('')
  const { data, loading, error, reload } = usePollingResource(
    () => securityApi.getMission(missionId, params), [missionId, organizationId],
    { shouldPoll: mission => activeStatuses.has(mission.status) })
  const mission = data
  const progress = mission?.orchestration
  const canManage = role === USER_ROLES.ADMIN || role === USER_ROLES.SUPERADMIN
  const canCancel = canManage && activeStatuses.has(mission?.status) && !mission?.cancel_requested_at
  const scope = usePollingResource(async () => {
    if (!mission) return null
    const [project, asset] = await Promise.allSettled([
      securityApi.getProject(mission.project_id, params),
      securityApi.getAsset(mission.asset_id, params),
    ])
    return { missionId: mission.id, project: project.value, asset: asset.value }
  }, [mission?.id])
  const names = scope.data?.missionId === mission?.id ? scope.data : null

  async function cancel() {
    setCancelling(true)
    setCancelError('')
    try {
      await securityApi.cancelMission(missionId, params)
      reload()
    } catch (requestError) {
      const message = getApiError(requestError, 'The cancellation request failed. Try again.')
      setCancelError(typeof message === 'string' ? message : 'The cancellation request failed. Try again.')
    } finally {
      setCancelling(false)
    }
  }

  return <div className="projects-page mission-detail">
    <Link to={`${missionPath}${organizationQuery(organizationId)}`}>← Mission Control</Link>
    <h1 className="page-title">Mission details</h1>
    <ResourceState loading={loading || (!mission && !error)} error={error} onRetry={reload} noun="mission" />
    {!loading && !error && mission && <Card title="Repository assessment">
      <MissionStatus status={mission.status} />
      <p>Updated {displayDate(mission.updated_at)}</p>
      <p className="mission-objective-text">{mission.objective}</p>
      <p>Project {organizationId ? names?.project?.name || mission.project_id
        : <Link to={`/dashboard/projects/${mission.project_id}/overview`}>{names?.project?.name || mission.project_id}</Link>}</p>
      <p>Repository asset {organizationId ? names?.asset?.name || mission.asset_id
        : <Link to={`/dashboard/assets/${mission.asset_id}`}>{names?.asset?.name || mission.asset_id}</Link>}</p>
      {names?.asset?.target && <p>{names.asset.target}</p>}
      {progress && <div aria-label="Fixture task progress">
        <p>{progress.completed.length} of {progress.total_tasks} fixture tasks complete</p>
        {progress.current_task && <p>Current task {taskLabels[progress.current_task] || progress.current_task}</p>}
        {!!progress.completed.length && <ul>
          {progress.completed.map(task => <li key={task.task_id}>{taskLabels[task.task_id] || task.task_id}</li>)}
        </ul>}
      </div>}
      {mission.cancel_requested_at && activeStatuses.has(mission.status) && <p role="status">Cancellation requested</p>}
      {canCancel && <button type="button" className="btn-secondary" onClick={cancel} disabled={cancelling}>
        {cancelling ? 'Requesting cancellation…' : 'Cancel mission'}
      </button>}
      {cancelError && <p className="form-error" role="alert">{cancelError}</p>}
      <button type="button" className="btn-secondary" onClick={reload}>Refresh status</button>
    </Card>}
    {canManage && mission && <MissionActions mission={mission} organizationId={organizationId} onChange={reload} />}
  </div>
}

function MissionActions({ mission, organizationId, onChange }) {
  const params = organizationParams(organizationId)
  const [pending, setPending] = useState(false)
  const [actionError, setActionError] = useState('')
  const active = activeStatuses.has(mission.status) && !mission.cancel_requested_at
  const { data, loading, error, reload } = usePollingResource(
    () => securityApi.listMissionActions(mission.id, params), [mission.id, organizationId, mission.status],
    { shouldPoll: () => active },
  )

  async function changeApproval(action, revoke) {
    setPending(true)
    setActionError('')
    try {
      if (revoke) {
        await securityApi.revokeMissionApproval(mission.id, action.operation, action.approval.id, action.digest, params)
      } else {
        await securityApi.approveMissionAction(mission.id, action.operation, action.digest, params)
      }
      reload()
      onChange()
    } catch (requestError) {
      const message = getApiError(requestError, 'The approval could not be updated.')
      setActionError(typeof message === 'string' ? message : 'The approval could not be updated.')
      reload()
    } finally {
      setPending(false)
    }
  }

  if (!loading && !error && !data?.length) return null
  return <Card title="Fixture actions">
    <ResourceState loading={loading} error={error} onRetry={reload} noun="fixture actions" />
    {!loading && !error && <ul>
      {data.map(action => {
        const approval = action.approval
        const granted = approval && !approval.revoked_at && Date.parse(approval.expires_at) > Date.now()
        const current = active && mission.orchestration?.current_task === action.operation
        const waiting = current && action.decision.outcome === 'require_approval'
        return <li key={action.operation}>
          <strong>{taskLabels[action.operation] || action.operation}</strong>
          <p>{action.result ? 'Completed' : granted ? 'Approved' : actionLabels[action.decision.outcome]}</p>
          {waiting && !granted && <button type="button" className="btn-primary" disabled={pending}
            onClick={() => changeApproval(action, false)}>Approve fixture action</button>}
          {current && granted && !action.result && <button type="button" className="btn-secondary" disabled={pending}
            onClick={() => changeApproval(action, true)}>Revoke approval</button>}
        </li>
      })}
    </ul>}
    {actionError && <p className="form-error" role="alert">{actionError}</p>}
  </Card>
}

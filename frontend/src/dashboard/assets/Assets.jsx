import React, { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import Card from '@/components/ui/Card'
import ResourceState from '@/components/ui/ResourceState'
import usePollingResource from '@/hooks/usePollingResource'
import { securityApi, displayDate } from '@/services/securityApi'
import { getApiError } from '@/services/apiClient'
import { useAuthStore } from '@/stores/authStore'
import { USER_ROLES } from '@/constants/auth'

const ASSET_TYPES = { repository: 'Repository', application: 'Application', domain: 'Domain', api: 'API', host: 'Host' }

export default function Assets() {
  const { projectId } = useParams()
  const { data, loading, error, reload } = usePollingResource(
    () => securityApi.listAssets(projectId ? { project_id: projectId } : {}), [projectId])
  const assets = data?.items || []
  const base = projectId ? `/dashboard/projects/${projectId}/assets` : '/dashboard/assets'
  return <div className="projects-page">
    <h1 className="page-title">Assets</h1>
    <p className="page-subtitle">Organization-scoped applications and repositories available to security runs.</p>
    <ResourceState loading={loading} error={error} onRetry={reload} noun="assets" />
    {!loading && !error && (assets.length ? <div className="projects-grid">{assets.map(asset =>
      <Card key={asset.id} title={asset.name} footer={<Link className="btn-primary" to={`${base}/${asset.id}`}>View Asset</Link>}>
        <p>{ASSET_TYPES[asset.type] || asset.type} · <span className="status-badge">{asset.status}</span></p>
        <p>{asset.target}</p><p>Updated {displayDate(asset.updated_at)}</p>
      </Card>)}</div> : <div className="empty-state"><h2>No Assets</h2><p>No assets are assigned to this workspace.</p></div>)}
  </div>
}

export function AssetDetail() {
  const { assetId, projectId } = useParams()
  const back = projectId ? `/dashboard/projects/${projectId}/assets` : '/dashboard/assets'
  const { data, loading, error, reload } = usePollingResource(async () => {
    const asset = await securityApi.getAsset(assetId)
    if (projectId && asset.project_id !== projectId) {
      const mismatch = new Error('Asset does not belong to the selected project')
      mismatch.response = { status: 404, data: { detail: mismatch.message } }
      throw mismatch
    }
    const findings = await securityApi.listFindings({ asset_id: assetId, limit: 100 })
    return { asset, findings: findings.items }
  }, [assetId, projectId])
  const role = useAuthStore(state => state.user?.role)
  const canManage = role === USER_ROLES.ADMIN || role === USER_ROLES.SUPERADMIN
  const [repositories, setRepositories] = useState([])
  const [repositoryId, setRepositoryId] = useState('')
  const [linking, setLinking] = useState(false)
  const [linkError, setLinkError] = useState('')
  useEffect(() => {
    let current = true
    securityApi.listGitHubRepositories().then(result => {
      if (current) setRepositories((result.items || []).filter(item => item.authorized && item.connection_status === 'active'))
    }).catch(() => { if (current) setRepositories([]) })
    return () => { current = false }
  }, [])
  if (loading || error) return <ResourceState loading={loading} error={error} onRetry={reload} noun="asset" />
  const { asset, findings } = data
  const linkRepository = async event => {
    event.preventDefault()
    if (!repositoryId) return
    setLinking(true); setLinkError('')
    try { await securityApi.linkAssetRepository(asset.id, Number(repositoryId)); reload() }
    catch (requestError) { setLinkError(getApiError(requestError, 'The repository could not be linked.')) }
    finally { setLinking(false) }
  }
  return <div className="projects-page">
    <Link to={back}>← Assets</Link><h1 className="page-title">{asset.name}</h1>
    <p className="page-subtitle">{ASSET_TYPES[asset.type] || asset.type} · {asset.target}</p>
    <Card title="Asset Context">
      <p>Status: <span className="status-badge">{asset.status}</span></p>
      <p>Project: {asset.project_id}</p>
      <p>Created {displayDate(asset.created_at)} · Updated {displayDate(asset.updated_at)}</p>
    </Card>
    <Card title="Source repository">
      {asset.source_control ? <div className="source-control-summary"><span className={`integration-status ${asset.source_control.connection_status}`}>{asset.source_control.connection_status.replace('_', ' ')}</span><strong>{asset.source_control.repository_full_name}</strong><span>Default branch: {asset.source_control.default_branch}</span></div> : <p>No GitHub repository is linked. A repository link is required before a verified remediation can become a pull request.</p>}
      {canManage && <form className="repository-link-form" onSubmit={linkRepository}><label htmlFor="asset-repository">{asset.source_control ? 'Change repository' : 'Link an authorized repository'}</label><div><select id="asset-repository" value={repositoryId} onChange={event => setRepositoryId(event.target.value)} disabled={linking}><option value="">Select repository</option>{repositories.map(repository => <option value={repository.repository_id} key={repository.repository_id}>{repository.full_name}</option>)}</select><button type="submit" className="btn-primary" disabled={!repositoryId || linking}>{linking ? 'Linking…' : 'Save link'}</button></div></form>}
      {!canManage && !asset.source_control && <p className="settings-helper">Ask an organization administrator to connect an authorized repository.</p>}
      {linkError && <p className="form-error" role="alert">{linkError}</p>}
    </Card>
    <section className="vulnerabilities-section"><h2>Asset Findings</h2>
      {findings.length ? <ul>{findings.map(finding => <li key={finding.id}>
        {finding.title} <span className={`severity-badge ${finding.severity}`}>{finding.severity}</span>
      </li>)}</ul> : <p>No findings are recorded for this asset. This does not establish that the asset is secure.</p>}
      <Link to={`/dashboard/findings?project_id=${encodeURIComponent(asset.project_id)}`}>View project findings</Link>
    </section>
  </div>
}

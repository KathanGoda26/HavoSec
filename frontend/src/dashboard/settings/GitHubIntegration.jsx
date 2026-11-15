import React, { useCallback, useEffect, useState } from 'react'
import { ArrowPathIcon, CodeBracketIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'
import { securityApi, displayDate } from '@/services/securityApi'
import { getApiError } from '@/services/apiClient'
import { useAuthStore } from '@/stores/authStore'
import { USER_ROLES } from '@/constants/auth'

export default function GitHubIntegration() {
  const role = useAuthStore(state => state.user?.role)
  const canManage = role === USER_ROLES.ADMIN || role === USER_ROLES.SUPERADMIN
  const [integration, setIntegration] = useState(null)
  const [repositories, setRepositories] = useState([])
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setError('')
    try {
      const connected = await securityApi.getGitHubIntegration()
      setIntegration(connected)
      if (connected) setRepositories((await securityApi.listGitHubRepositories()).items || [])
      else setRepositories([])
    } catch (requestError) { setError(getApiError(requestError, 'GitHub connection details could not be loaded.')) }
  }, [])

  useEffect(() => { load() }, [load])

  const connect = async () => {
    setBusy('connect'); setError('')
    try {
      const result = await securityApi.connectGitHub()
      window.location.assign(result.installation_url)
    } catch (requestError) {
      setError(getApiError(requestError, 'The GitHub connection could not be started.'))
      setBusy('')
    }
  }

  const refresh = async () => {
    setBusy('refresh'); setError('')
    try { setRepositories((await securityApi.refreshGitHubRepositories()).items || []) }
    catch (requestError) { setError(getApiError(requestError, 'Repositories could not be refreshed.')) }
    finally { setBusy('') }
  }

  const toggleRepository = async repository => {
    setBusy(String(repository.repository_id)); setError('')
    try {
      const updated = await securityApi.authorizeGitHubRepository(repository.repository_id, !repository.authorized)
      setRepositories(items => items.map(item => item.repository_id === updated.repository_id ? updated : item))
    } catch (requestError) { setError(getApiError(requestError, 'Repository access could not be updated.')) }
    finally { setBusy('') }
  }

  return <section className="settings-card settings-card-wide github-settings" aria-labelledby="github-heading">
    <div className="settings-card-heading">
      <div className="settings-card-icon"><CodeBracketIcon /></div>
      <div className="github-heading-copy"><h2 id="github-heading">GitHub integration</h2><p>Connect the organization installation and choose which repositories HavoSec may use for verified pull requests.</p></div>
      <span className={`integration-status ${integration?.status || 'disconnected'}`}>{integration?.status?.replace('_', ' ') || 'Not connected'}</span>
    </div>
    {error && <p className="form-error integration-error" role="alert"><ExclamationTriangleIcon className="icon-sm" /> {error}</p>}
    {!integration ? <div className="integration-empty"><p>No GitHub installation is connected to this organization.</p>{canManage && <button type="button" className="settings-primary-button" disabled={Boolean(busy)} onClick={connect}>{busy === 'connect' ? 'Opening GitHub…' : 'Connect GitHub'}</button>}</div> : <>
      <div className="integration-meta"><span><strong>Account</strong>{integration.account_login}</span><span><strong>Installation</strong>#{integration.installation_id}</span><span><strong>Last synced</strong>{displayDate(integration.last_synced_at)}</span></div>
      <div className="integration-toolbar"><div><strong>Repository access</strong><p>{repositories.filter(item => item.authorized).length} of {repositories.length} repositories authorized</p></div>{canManage && <><button type="button" className="settings-secondary-button" onClick={connect} disabled={Boolean(busy)}>Reconnect</button><button type="button" className="settings-secondary-button" onClick={refresh} disabled={Boolean(busy)}><ArrowPathIcon className={`icon-sm ${busy === 'refresh' ? 'is-spinning' : ''}`} /> Refresh</button></>}</div>
      <div className="repository-access-list">{repositories.length ? repositories.map(repository => <label className="repository-access-row" key={repository.repository_id}><span><strong>{repository.full_name}</strong><small>{repository.default_branch} · {repository.private ? 'Private' : 'Public'}</small></span><input type="checkbox" checked={repository.authorized} disabled={!canManage || Boolean(busy)} onChange={() => toggleRepository(repository)} /></label>) : <p>No repositories were returned by this installation.</p>}</div>
      <p className="settings-helper">Disconnecting or uninstalling the GitHub App is managed in GitHub. HavoSec never stores a personal access token.</p>
    </>}
  </section>
}

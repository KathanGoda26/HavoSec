import React, { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { securityApi } from '@/services/securityApi'
import { getApiError } from '@/services/apiClient'

export default function GitHubCallback() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const [error, setError] = useState('')
  useEffect(() => {
    const state = params.get('state')
    const installationId = params.get('installation_id')
    if (!state || !installationId) { setError('GitHub did not return the required installation details.'); return }
    securityApi.completeGitHubConnection({ state, installation_id: installationId })
      .then(() => navigate('/dashboard/settings?github=connected', { replace: true }))
      .catch(requestError => setError(getApiError(requestError, 'The GitHub installation could not be connected.')))
  }, [navigate, params])
  return <div className="route-loading" role="status"><div className="auth-unavailable-card"><span className="auth-unavailable-label">GitHub integration</span><h1>{error ? 'Connection needs attention' : 'Securing your connection…'}</h1><p>{error || 'HavoSec is validating the organization installation and repository access.'}</p>{error && <button type="button" className="auth-retry-button" onClick={() => navigate('/dashboard/settings', { replace: true })}>Return to settings</button>}</div></div>
}

import apiClient from './apiClient'

const page = response => response.data

export const securityApi = {
  listProjects: params => apiClient.get('/projects', { params }).then(page),
  getProject: (id, params) => apiClient.get(`/projects/${id}`, { params }).then(page),
  getOverview: params => apiClient.get('/domain/overview', { params }).then(page),
  listActivity: params => apiClient.get('/activity', { params }).then(page),
  listAssets: params => apiClient.get('/assets', { params }).then(page),
  getAsset: (id, params) => apiClient.get(`/assets/${id}`, { params }).then(page),
  listOrganizations: params => apiClient.get('/admin/clients/', { params }).then(page)
    .then(({ clients, total }) => ({ items: clients, total })),
  listMissions: params => apiClient.get('/missions', { params }).then(page),
  getMission: (id, params) => apiClient.get(`/missions/${id}`, { params }).then(page),
  cancelMission: (id, params) => apiClient.post(`/missions/${id}/cancel`, null, { params }).then(page),
  listMissionActions: (id, params) => apiClient.get(`/missions/${id}/actions`, { params }).then(page),
  approveMissionAction: (id, taskId, actionDigest, params) => apiClient.post(
    `/missions/${id}/actions/${taskId}/approve`, { action_digest: actionDigest }, { params },
  ).then(page),
  revokeMissionApproval: (id, taskId, approvalId, actionDigest, params) => apiClient.post(
    `/missions/${id}/actions/${taskId}/approvals/${approvalId}/revoke`, { action_digest: actionDigest }, { params },
  ).then(page),
  createMission: (payload, requestKey, params) => apiClient.post('/missions', payload, {
    params,
    headers: { 'Idempotency-Key': requestKey },
  }).then(page),
  linkAssetRepository: (id, repositoryId) => apiClient.put(`/assets/${id}/github-repository`, { repository_id: repositoryId }).then(page),
  listRuns: params => apiClient.get('/security-runs', { params }).then(page),
  getRun: id => apiClient.get(`/security-runs/${id}`).then(page),
  createRun: payload => apiClient.post('/security-runs', payload).then(page),
  cancelRun: id => apiClient.patch(`/security-runs/${id}/cancel`).then(page),
  listFindings: params => apiClient.get('/findings', { params }).then(page),
  getFinding: id => apiClient.get(`/findings/${id}`).then(page),
  updateFinding: (id, status) => apiClient.patch(`/findings/${id}`, { status }).then(page),
  listRemediations: params => apiClient.get('/remediations', { params }).then(page),
  getRemediation: id => apiClient.get(`/remediations/${id}`).then(page),
  verifyRemediation: id => apiClient.post(`/remediations/${id}/verify`).then(page),
  updateRemediation: (id, changes) => apiClient.patch(`/remediations/${id}`, changes).then(page),
  getPullRequestEligibility: id => apiClient.get(`/remediations/${id}/pull-request-eligibility`).then(page),
  createPullRequest: id => apiClient.post(`/remediations/${id}/pull-request`).then(page),
  getPullRequest: id => apiClient.get(`/remediations/${id}/pull-request`).then(page),
  getGitHubIntegration: () => apiClient.get('/integrations/github').then(page),
  connectGitHub: () => apiClient.post('/integrations/github/connect').then(page),
  completeGitHubConnection: params => apiClient.get('/integrations/github/callback', { params }).then(page),
  listGitHubRepositories: () => apiClient.get('/integrations/github/repositories').then(page),
  refreshGitHubRepositories: () => apiClient.post('/integrations/github/repositories/refresh').then(page),
  authorizeGitHubRepository: (repositoryId, authorized) => apiClient.patch(`/integrations/github/repositories/${repositoryId}`, { authorized }).then(page),
}

export const ACTIVE_RUN_STATUSES = new Set(['queued', 'running'])
export const TERMINAL_RUN_STATUSES = new Set(['completed', 'failed', 'cancelled'])
export const isActiveRun = run => ACTIVE_RUN_STATUSES.has(run?.status)
export const ACTIVE_VERIFICATION_STATUSES = new Set(['queued', 'testing'])
export const isActiveVerification = remediation => ACTIVE_VERIFICATION_STATUSES.has(remediation?.verification_status)

export function displayDate(value) {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '—' : date.toLocaleString()
}

export function findingAnalysis(finding) {
  return finding?.source_metadata?.agent_analysis || null
}

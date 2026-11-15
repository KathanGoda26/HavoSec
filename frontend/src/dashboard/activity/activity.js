export const ACTIVITY_TYPES = Object.freeze({
  project_created: 'Project created',
  project_updated: 'Project updated',
  project_archived: 'Project archived',
  asset_created: 'Asset created',
  asset_updated: 'Asset updated',
  asset_archived: 'Asset archived',
  security_run_created: 'Security run created',
  security_run_cancelled: 'Security run cancelled',
  security_run_started: 'Security run started',
  security_run_completed: 'Security run completed',
  security_run_failed: 'Security run failed',
  findings_created: 'Findings created',
  finding_created: 'Finding created',
  finding_updated: 'Finding updated',
  remediation_created: 'Remediation created',
  remediation_updated: 'Remediation updated',
  remediation_verification_queued: 'Remediation verification queued',
  remediation_verification_started: 'Remediation verification started',
  remediation_verified: 'Remediation verified',
  remediation_failed: 'Remediation failed',
})

export function activityView(event) {
  return {
    ...event,
    eventType: event.event_type,
    description: event.message,
    project: event.project_id,
    actor: event.actor_id,
    time: event.created_at,
  }
}

export function filterActivity(events, { query = '', severity = 'all', eventType = 'all' } = {}) {
  const search = query.trim().toLowerCase()
  return events.filter(event => {
    if (severity !== 'all' && event.severity !== severity) return false
    if (eventType !== 'all' && event.eventType !== eventType) return false
    return !search || [event.id, event.description, event.category, event.eventType,
      ACTIVITY_TYPES[event.eventType], event.project, event.actor, event.ip, event.status]
      .filter(Boolean).some(value => String(value).toLowerCase().includes(search))
  }).sort((a, b) => b.time.localeCompare(a.time) || a.id.localeCompare(b.id))
}

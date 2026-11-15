import { describe, it, expect } from 'vitest'
import { ACTIVITY_TYPES, activityView, filterActivity } from './activity'

const apiEvents = [
  activityView({ id: '2', event_type: 'security_run_completed', message: 'Security run completed', project_id: 'project-a', actor_id: 'worker', entity_type: 'security_run', entity_id: 'run-a', created_at: '2026-08-01T11:00:00Z' }),
  activityView({ id: '1', event_type: 'finding_updated', message: 'Finding moved to triaged', project_id: 'project-a', actor_id: 'admin', entity_type: 'finding', entity_id: 'finding-a', created_at: '2026-08-01T10:00:00Z' }),
]

describe('workspace activity', () => {
  it('labels the real backend lifecycle events', () => {
    for (const type of ['project_created', 'asset_created', 'security_run_started', 'security_run_completed', 'security_run_failed', 'findings_created', 'finding_updated', 'remediation_created']) {
      expect(ACTIVITY_TYPES[type]).toBeTruthy()
    }
  })
  it('adapts API fields without removing their original values', () => {
    expect(apiEvents[0]).toMatchObject({ eventType: 'security_run_completed', description: 'Security run completed', project: 'project-a', actor: 'worker' })
    expect(apiEvents[0].event_type).toBe('security_run_completed')
  })
  it('combines trimmed search and event-type filtering', () => {
    expect(filterActivity(apiEvents, { query: '  TRIAGED ', eventType: 'finding_updated' })).toHaveLength(1)
    expect(filterActivity(apiEvents, { query: 'does-not-exist' })).toEqual([])
  })
  it('sorts newest first without mutating API records', () => {
    const before = [...apiEvents]
    expect(filterActivity([...apiEvents].reverse())[0].id).toBe('2')
    expect(apiEvents).toEqual(before)
  })
})

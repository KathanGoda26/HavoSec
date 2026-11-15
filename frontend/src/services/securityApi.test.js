import { describe, expect, it } from 'vitest'
import { ACTIVE_RUN_STATUSES, TERMINAL_RUN_STATUSES, displayDate, findingAnalysis, isActiveRun } from './securityApi'

describe('security API presentation contracts', () => {
  it('polls only nonterminal runs', () => {
    expect([...ACTIVE_RUN_STATUSES]).toEqual(['queued', 'running'])
    expect([...TERMINAL_RUN_STATUSES]).toEqual(['completed', 'failed', 'cancelled'])
    expect(isActiveRun({ status: 'queued' })).toBe(true)
    expect(isActiveRun({ status: 'running' })).toBe(true)
    for (const status of TERMINAL_RUN_STATUSES) expect(isActiveRun({ status })).toBe(false)
  })

  it('does not fabricate dates or agent analysis', () => {
    expect(displayDate(null)).toBe('—')
    expect(displayDate('not-a-date')).toBe('—')
    expect(findingAnalysis({ source_metadata: {} })).toBeNull()
    expect(findingAnalysis({ source_metadata: { agent_analysis: { priority: 'high' } } })).toEqual({ priority: 'high' })
  })
})

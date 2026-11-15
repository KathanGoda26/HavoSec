import { describe, it, expect } from 'vitest'
import { demoRemediations } from './demoRemediations'
import { demoFindings } from '../findings/demoFindings'
import { REMEDIATION_STATUS, REMEDIATION_STATUS_LABELS, VERIFICATION_STATUS_LABELS, diffLineType, summarizeRemediations } from './status'

describe('remediation contracts', () => {
  it('links each demo proposal to an existing finding and its workspace context', () => {
    expect(new Set(demoRemediations.map(item => item.id)).size).toBe(demoRemediations.length)
    for (const item of demoRemediations) {
      const finding = demoFindings.find(finding => finding.id === item.findingId)
      expect(finding).toBeDefined()
      expect(item.project).toBe(finding.project)
      expect(item.asset).toBe(finding.asset)
      expect(item.actions.length).toBeGreaterThan(0)
      expect(item.validationPlan).toBeTruthy()
    }
  })
  it('derives card counts from proposals without inventing resolved fixes', () => {
    expect(summarizeRemediations(demoRemediations)).toEqual({ pending: 1, in_progress: 0, awaiting_approval: 1, approved: 0, rejected: 0, resolved: 0, failed: 0 })
  })
  it('supports all lifecycle labels and an empty data response', () => {
    for (const status of Object.values(REMEDIATION_STATUS)) expect(REMEDIATION_STATUS_LABELS[status]).toBeTruthy()
    expect(Object.values(summarizeRemediations([]))).toEqual([0, 0, 0, 0, 0, 0, 0])
    for (const status of ['not_started', 'queued', 'testing', 'verified', 'failed', 'inconclusive']) expect(VERIFICATION_STATUS_LABELS[status]).toBeTruthy()
  })
  it('classifies unified diff lines for a readable review', () => {
    expect(diffLineType('--- a/app.py')).toBe('header')
    expect(diffLineType('@@ -1 +1 @@')).toBe('hunk')
    expect(diffLineType('+safe()')).toBe('addition')
    expect(diffLineType('-unsafe()')).toBe('deletion')
    expect(diffLineType(' context')).toBe('context')
  })
})

import { describe, it, expect } from 'vitest'
import { demoFindings } from './demoFindings'
import { FINDING_STATUS, FINDING_STATUS_LABELS } from './status'

describe('demo finding contracts', () => {
  it('provides distinct fixture identities and future relationship fields', () => {
    expect(new Set(demoFindings.map(finding => finding.id)).size).toBe(demoFindings.length)
    for (const finding of demoFindings) {
      expect(finding.id).toMatch(/^DEMO-/)
      for (const key of ['project', 'asset', 'sourceRun', 'category', 'firstDetected', 'lastDetected', 'remediationStatus']) expect(finding[key]).toBeTruthy()
      expect(finding.cve).toBeNull()
      expect(finding.discoverySteps.length).toBeGreaterThan(0)
    }
  })
  it('keeps all demo findings open and defines labels for every lifecycle status', () => {
    expect(demoFindings.every(finding => finding.status === FINDING_STATUS.NEW)).toBe(true)
    for (const status of Object.values(FINDING_STATUS)) expect(FINDING_STATUS_LABELS[status]).toBeTruthy()
  })
})

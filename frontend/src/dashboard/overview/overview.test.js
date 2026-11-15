import { describe, it, expect } from 'vitest'
import { summarizeOverview } from './overview'
import { demoFindings } from '../findings/demoFindings'
import { demoRuns } from '../security-runs/demoRuns'
import { demoRemediations } from '../remediation/demoRemediations'
import { demoActivity } from '../activity/demoActivity'

describe('workspace overview', () => {
  it('derives metrics from shared fixtures without inventing a score', () => {
    const result = summarizeOverview({ findings: demoFindings, runs: demoRuns, remediations: demoRemediations, activity: demoActivity })
    expect(result.securityScore).toBeNull()
    expect(result.openFindings).toBe(2)
    expect(result.criticalFindings).toBe(1)
    expect(result.pendingRemediations).toBe(2)
    expect(result.lastRun.id).toBe('DEMO-RUN-001')
    expect(result.severity.reduce((sum, item) => sum + item.count, 0)).toBe(result.openFindings)
    expect(result.trend).toHaveLength(7)
    expect(result.trend.at(-1)).toEqual({ date: '2026-08-01', count: 2 })
  })
  it('excludes resolved findings from open totals but retains discovery history', () => {
    const findings = demoFindings.map(finding => ({ ...finding, status: 'resolved' }))
    const result = summarizeOverview({ findings })
    expect(result.openFindings).toBe(0)
    expect(result.criticalFindings).toBe(0)
    expect(result.recentFindings).toEqual([])
    expect(result.trend.at(-1).count).toBe(2)
  })
  it('handles empty data and queued-only runs without false security claims', () => {
    const result = summarizeOverview()
    expect(result.lastRun).toBeNull()
    expect(result.securityScore).toBeNull()
    expect(result.trend).toEqual([])
    expect(result.recentActivity).toEqual([])
    expect(summarizeOverview({ runs: demoRuns.filter(run => !run.startedAt) }).lastRun).toBeNull()
  })
  it('orders activity newest first without changing its source', () => {
    const before = demoActivity.map(event => event.id)
    const result = summarizeOverview({ activity: demoActivity })
    expect(result.recentActivity).toHaveLength(5)
    expect(result.recentActivity[0].time >= result.recentActivity[4].time).toBe(true)
    expect(demoActivity.map(event => event.id)).toEqual(before)
  })
})

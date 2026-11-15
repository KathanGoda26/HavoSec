import { describe, it, expect } from 'vitest'
import { demoRuns, getDemoRun, getRunFindings, RUN_STATUS, RUN_STATUS_LABELS } from './demoRuns'
import { demoFindings } from '../findings/demoFindings'
import { getDemoAsset } from '../assets/demoAssets'
import { demoProjects, filterProjectRecords } from '../projects/demoProjects'

describe('security run contracts', () => {
  it('uses unique IDs and valid project-scoped asset relationships', () => {
    expect(new Set(demoRuns.map(run => run.id)).size).toBe(demoRuns.length)
    for (const run of demoRuns) expect(getDemoAsset(run.assetId, run.projectId)).toBeDefined()
    for (const finding of demoFindings) expect(getRunFindings(demoFindings, getDemoRun(finding.sourceRun))).toContain(finding)
  })
  it('does not leak fixtures across projects or invent results for queued runs', () => {
    expect(getDemoRun(demoRuns[0].id, demoProjects[1].id)).toBeUndefined()
    expect(getDemoRun('missing')).toBeUndefined()
    expect(filterProjectRecords(demoRuns, demoProjects[1].id)).toEqual([])
    const queued = demoRuns.find(run => run.status === RUN_STATUS.QUEUED)
    expect(queued.startedAt).toBeNull()
    expect(queued.completedAt).toBeNull()
    expect(queued.progress).toBe(0)
    expect(getRunFindings(demoFindings, queued)).toEqual([])
  })
  it('defines every lifecycle label and keeps progress within bounds', () => {
    for (const status of Object.values(RUN_STATUS)) expect(RUN_STATUS_LABELS[status]).toBeTruthy()
    for (const run of demoRuns) { expect(run.progress).toBeGreaterThanOrEqual(0); expect(run.progress).toBeLessThanOrEqual(100) }
  })
})

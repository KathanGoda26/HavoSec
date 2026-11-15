import { describe, it, expect } from 'vitest'
import { demoProjects, getDemoProject, filterProjectRecords } from './demoProjects'
import { demoFindings } from '../findings/demoFindings'
import { demoRemediations } from '../remediation/demoRemediations'
import { demoActivity } from '../activity/demoActivity'

describe('project relationships', () => {
  it('has unique stable project identifiers', () => {
    expect(new Set(demoProjects.map(project => project.id)).size).toBe(demoProjects.length)
    expect(getDemoProject('missing')).toBeUndefined()
  })
  it('resolves every assigned project without assigning global activity arbitrarily', () => {
    for (const record of [...demoFindings, ...demoRemediations, ...demoActivity].filter(record => record.projectId)) expect(getDemoProject(record.projectId)).toBeDefined()
    expect(demoActivity.some(event => !event.projectId)).toBe(true)
  })
  it('shows only the selected project records, with empty and unknown projects empty', () => {
    for (const records of [demoFindings, demoRemediations, demoActivity]) {
      expect(filterProjectRecords(records, demoProjects[0].id).length).toBeGreaterThan(0)
      expect(filterProjectRecords(records, demoProjects[1].id)).toEqual([])
      expect(filterProjectRecords(records, 'unknown')).toEqual([])
      expect(filterProjectRecords(records)).toBe(records)
    }
  })
})

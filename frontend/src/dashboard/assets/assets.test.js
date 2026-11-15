import { describe, it, expect } from 'vitest'
import { demoAssets, getDemoAsset, ASSET_TYPES } from './demoAssets'
import { demoFindings } from '../findings/demoFindings'
import { demoProjects, getDemoProject, filterProjectRecords } from '../projects/demoProjects'

describe('asset relationships', () => {
  it('uses unique IDs and valid project/type references', () => {
    expect(new Set(demoAssets.map(asset => asset.id)).size).toBe(demoAssets.length)
    for (const asset of demoAssets) { expect(getDemoProject(asset.projectId)).toBeDefined(); expect(ASSET_TYPES[asset.type]).toBeTruthy() }
  })
  it('rejects unknown IDs and assets belonging to another project', () => {
    expect(getDemoAsset('missing')).toBeUndefined()
    expect(getDemoAsset(demoAssets[0].id, demoProjects[1].id)).toBeUndefined()
    expect(filterProjectRecords(demoAssets, demoProjects[1].id)).toEqual([])
  })
  it('resolves finding asset IDs in the same project and run snapshot', () => {
    for (const finding of demoFindings) {
      const asset = getDemoAsset(finding.assetId, finding.projectId)
      expect(asset).toBeDefined()
      expect(asset.reconnaissance.sourceRun).toBe(finding.sourceRun)
    }
  })
  it('keeps undiscovered assets explicitly without reconnaissance', () => {
    expect(demoAssets.some(asset => asset.reconnaissance === null)).toBe(true)
  })
})

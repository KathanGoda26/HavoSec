import { describe, expect, it } from 'vitest'
import { dashboardNavigation, getDashboardNavigation, getNavigationSections, roleLabels } from './navigation'
import { USER_ROLES, getAuthenticatedHome } from '../../constants/auth'

const existingPaths = [
  '/dashboard/overview', '/dashboard/projects', '/dashboard/assets', '/dashboard/missions', '/dashboard/findings',
  '/dashboard/security-runs',
  '/dashboard/remediation',
  '/dashboard/activity', '/dashboard/settings',
]

describe('navigation extraction compatibility', () => {
  it.each([USER_ROLES.ADMIN, USER_ROLES.USER])('groups %s workspace links without exposing platform entries', role => {
    const sections = getNavigationSections(role)
    expect(sections.map(section => section.label)).toEqual(['Workspace', 'Security', 'Operations', 'Management'])
    expect(sections.flatMap(section => section.items)).toEqual(getDashboardNavigation(role))
    expect(sections.find(section => section.id === 'security').items.map(item => item.name)).toEqual(['Projects', 'Assets', 'Mission Control', 'Findings', 'Security Runs', 'Remediation'])
  })
  it('adds only implemented platform pages for superadmin, without duplicate or empty groups', () => {
    const sections = getNavigationSections(USER_ROLES.SUPERADMIN)
    expect(sections[0].label).toBe('Platform')
    expect(sections[0].items.map(item => item.path)).toEqual(['/admin/platform-health', '/admin/settings'])
    const paths = sections.flatMap(section => section.items.map(item => item.path))
    expect(new Set(paths).size).toBe(paths.length)
    expect(sections.every(section => section.items.length)).toBe(true)
    expect(getNavigationSections(undefined)).toEqual([])
    expect(getNavigationSections('unknown')).toEqual([])
  })
  it.each([USER_ROLES.ADMIN, USER_ROLES.USER])('keeps platform health out of %s navigation', role => {
    expect(getDashboardNavigation(role).map(item => item.path)).toEqual(existingPaths)
    expect(roleLabels[role]).toBeTruthy()
  })

  it('offers implemented platform destinations only to superadmin', () => {
    const paths = getDashboardNavigation(USER_ROLES.SUPERADMIN).map(item => item.path)
    expect(paths).toContain('/admin/platform-health')
    expect(paths).not.toContain('/dashboard/system-health')
    expect(getAuthenticatedHome(USER_ROLES.SUPERADMIN)).toBe('/admin/platform-health')
    expect(getAuthenticatedHome(USER_ROLES.ADMIN)).toBe('/dashboard/overview')
    expect(getAuthenticatedHome(USER_ROLES.USER)).toBe('/dashboard/overview')
  })

  it('has unique paths and preserves existing icon components', () => {
    expect(new Set(dashboardNavigation.map(item => item.path)).size).toBe(dashboardNavigation.length)
    expect(dashboardNavigation.every(item => Boolean(item.icon))).toBe(true)
  })

  it('does not provide navigation for absent or unknown roles', () => {
    expect(getDashboardNavigation(undefined)).toEqual([])
    expect(getDashboardNavigation('unknown')).toEqual([])
  })

  it('supports legacy role aliases without maintaining a separate role state', () => {
    expect(getDashboardNavigation('super_admin')).toEqual(getDashboardNavigation('superadmin'))
  })
})

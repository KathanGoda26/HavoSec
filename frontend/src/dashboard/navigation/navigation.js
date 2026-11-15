import {
  HomeIcon, ShieldCheckIcon, ChartBarIcon, HeartIcon,
  DocumentTextIcon, Cog6ToothIcon, FolderIcon, CubeIcon, PlayCircleIcon, ClipboardDocumentListIcon,
} from '@heroicons/react/24/outline'
import { DASHBOARD_ROLES, USER_ROLES, normalizeRole } from '../../constants/auth'

export const roleLabels = Object.freeze({
  [USER_ROLES.SUPERADMIN]: 'Super Admin',
  [USER_ROLES.ADMIN]: 'Admin',
  [USER_ROLES.USER]: 'User',
})

export const NAVIGATION_SECTIONS = Object.freeze([
  { id: 'platform', label: 'Platform' },
  { id: 'workspace', label: 'Workspace' },
  { id: 'security', label: 'Security' },
  { id: 'operations', label: 'Operations' },
  { id: 'management', label: 'Management' },
])

// Only implemented destinations belong here; route guards remain independent.
export const dashboardNavigation = Object.freeze([
  { name: 'Overview', path: '/dashboard/overview', icon: HomeIcon, roles: DASHBOARD_ROLES, section: 'workspace' },
  { name: 'Projects', path: '/dashboard/projects', icon: FolderIcon, roles: DASHBOARD_ROLES, section: 'security' },
  { name: 'Assets', path: '/dashboard/assets', icon: CubeIcon, roles: DASHBOARD_ROLES, section: 'security' },
  { name: 'Mission Control', path: '/dashboard/missions', icon: ClipboardDocumentListIcon, roles: DASHBOARD_ROLES, section: 'security' },
  { name: 'Findings', path: '/dashboard/findings', icon: ShieldCheckIcon, roles: DASHBOARD_ROLES, section: 'security' },
  { name: 'Security Runs', path: '/dashboard/security-runs', icon: PlayCircleIcon, roles: DASHBOARD_ROLES, section: 'security' },
  { name: 'Remediation', path: '/dashboard/remediation', icon: ChartBarIcon, roles: DASHBOARD_ROLES, section: 'security' },
  { name: 'Activity', path: '/dashboard/activity', icon: DocumentTextIcon, roles: DASHBOARD_ROLES, section: 'operations' },
  { name: 'Settings', path: '/dashboard/settings', icon: Cog6ToothIcon, roles: DASHBOARD_ROLES, section: 'management' },
])

// Only implemented platform destinations are linked. Workspace pages remain
// available through the existing customer navigation until later increments.
export const platformNavigation = Object.freeze([
  { name: 'Platform Health', path: '/admin/platform-health', icon: HeartIcon, roles: [USER_ROLES.SUPERADMIN], section: 'platform' },
  { name: 'Platform Settings', path: '/admin/settings', icon: Cog6ToothIcon, roles: [USER_ROLES.SUPERADMIN], section: 'platform' },
])

export function getDashboardNavigation(role) {
  if (!role) return []
  const normalizedRole = normalizeRole(role)
  return [...platformNavigation, ...dashboardNavigation].filter(item => item.roles.includes(normalizedRole))
}

export function getNavigationSections(role) {
  const items = getDashboardNavigation(role)
  return NAVIGATION_SECTIONS.map(section => ({ ...section, items: items.filter(item => item.section === section.id) }))
    .filter(section => section.items.length > 0)
}

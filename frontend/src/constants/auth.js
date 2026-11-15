export const USER_ROLES = Object.freeze({ SUPERADMIN: 'superadmin', ADMIN: 'admin', USER: 'user' })
export const ROLE_ALIASES = Object.freeze({ super_admin: USER_ROLES.SUPERADMIN, 'super-admin': USER_ROLES.SUPERADMIN, viewer: USER_ROLES.USER, client: USER_ROLES.USER })
export const normalizeRole = role => ROLE_ALIASES[role] || role || USER_ROLES.USER
export const DASHBOARD_ROLES = Object.freeze(Object.values(USER_ROLES))
export const PLATFORM_ROLES = Object.freeze([USER_ROLES.SUPERADMIN])
export const getAuthenticatedHome = role => normalizeRole(role) === USER_ROLES.SUPERADMIN
  ? '/admin/platform-health'
  : '/dashboard/overview'

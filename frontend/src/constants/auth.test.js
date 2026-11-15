import { describe, expect, it } from 'vitest'
import { normalizeRole, USER_ROLES } from './auth'

describe('authentication roles', () => {
  it('normalizes compatible legacy roles', () => {
    expect(normalizeRole('super_admin')).toBe(USER_ROLES.SUPERADMIN)
    expect(normalizeRole('viewer')).toBe(USER_ROLES.USER)
  })

  it('does not elevate missing roles', () => {
    expect(normalizeRole()).toBe(USER_ROLES.USER)
  })
})

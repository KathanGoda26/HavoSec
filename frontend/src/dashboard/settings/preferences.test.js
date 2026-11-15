import { describe, expect, it } from 'vitest'
import { defaultPreferences, normalizePreferences, PREFERENCES_KEY, readPreferences, resetPreferences, savePreferences } from './preferences'

describe('browser settings preferences', () => {
  it('preserves existing boolean preferences and ignores unknown or invalid fields', () => {
    expect(normalizePreferences({ emailAlerts: false, criticalAlerts: 'false', weeklyReport: null, compactTables: true, role: 'superadmin' }))
      .toEqual({ emailAlerts: false, criticalAlerts: true, weeklyReport: true, compactTables: true })
  })

  it('returns defaults for missing, corrupt and unavailable storage', () => {
    for (const value of [null, '{broken', 'null', '42', '[]']) {
      expect(readPreferences({ getItem: () => value })).toEqual(defaultPreferences)
    }
    expect(readPreferences({ getItem: () => { throw new Error('Blocked') } })).toEqual(defaultPreferences)
  })

  it('round trips the legacy key and resets only preferences', () => {
    const values = new Map([['theme', 'dark']])
    const storage = { getItem: key => values.get(key) ?? null, setItem: (key, value) => values.set(key, value), removeItem: key => values.delete(key) }
    savePreferences({ ...defaultPreferences, emailAlerts: false }, storage)
    expect(values.has(PREFERENCES_KEY)).toBe(true)
    expect(readPreferences(storage).emailAlerts).toBe(false)
    resetPreferences(storage)
    expect(readPreferences(storage)).toEqual(defaultPreferences)
    expect(values.get('theme')).toBe('dark')
  })

  it('surfaces write/reset failures so the UI cannot claim success', () => {
    const fail = () => { throw new Error('Blocked') }
    expect(() => savePreferences(defaultPreferences, { setItem: fail })).toThrow('Blocked')
    expect(() => resetPreferences({ removeItem: fail })).toThrow('Blocked')
  })
})

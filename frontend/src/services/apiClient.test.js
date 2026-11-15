import { describe, expect, it } from 'vitest'
import { API_BASE_URL, getApiError } from './apiClient'

describe('development API connection', () => {
  it('uses the same-origin proxy unless explicitly configured', () => {
    expect(API_BASE_URL).toBe((import.meta.env.VITE_API_URL || '/api').replace(/\/$/, ''))
  })
  it('explains network failures without misreporting credentials', () => {
    expect(getApiError({ code: 'ERR_NETWORK' }, 'Login failed')).toContain('Cannot reach the backend')
    expect(getApiError({ response: { data: { detail: 'Invalid credentials' } } })).toBe('Invalid credentials')
    expect(getApiError({}, 'Login failed')).toBe('Login failed')
  })
})

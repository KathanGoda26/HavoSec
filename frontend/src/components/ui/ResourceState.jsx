import React from 'react'
import { getApiError } from '@/services/apiClient'

export default function ResourceState({ loading, error, onRetry, noun = 'data' }) {
  if (loading) return <div className="empty-state" role="status"><h2>Loading {noun}…</h2></div>
  if (!error) return null
  return <div className="empty-state" role="alert">
    <h2>Unable to load {noun}</h2>
    <p>{getApiError(error, `The ${noun} could not be loaded.`)}</p>
    <button type="button" className="btn-secondary" onClick={onRetry}>Try again</button>
  </div>
}

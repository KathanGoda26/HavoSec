import { useState, useCallback } from 'react'

// Static hook — no API calls
// Dynamic AI functionality to be implemented later
export function useAI() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // All functions return empty/null in static mode
  const searchSimilarCVEs = useCallback(async () => [], [])
  const searchSimilarIncidents = useCallback(async () => [], [])
  const analyzeVulnerability = useCallback(async () => null, [])
  const runSecurityScan = useCallback(async () => null, [])
  const createIncident = useCallback(async () => null, [])
  const applyPatch = useCallback(async () => null, [])
  const chatWithAI = useCallback(async () => "AI assistant is not yet available in static mode.", [])

  return {
    loading,
    error,
    searchSimilarCVEs,
    searchSimilarIncidents,
    analyzeVulnerability,
    runSecurityScan,
    createIncident,
    applyPatch,
    chatWithAI,
  }
}

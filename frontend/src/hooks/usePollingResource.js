import { useCallback, useEffect, useRef, useState } from 'react'

export default function usePollingResource(loader, dependencies, options = {}) {
  const { interval = 3000, shouldPoll = () => false, maxConsecutiveErrors = 3 } = options
  const [state, setState] = useState({ data: null, loading: true, error: null })
  const [revision, setRevision] = useState(0)
  const loaderRef = useRef(loader)
  const predicateRef = useRef(shouldPoll)
  loaderRef.current = loader
  predicateRef.current = shouldPoll

  useEffect(() => {
    let active = true
    let timer = null
    let latest = null
    let failures = 0
    const load = async initial => {
      if (initial) setState(previous => ({ ...previous, loading: true, error: null }))
      try {
        const data = await loaderRef.current()
        if (!active) return
        latest = data
        failures = 0
        setState({ data, loading: false, error: null })
        if (predicateRef.current(data)) timer = window.setTimeout(() => load(false), interval)
      } catch (error) {
        if (!active) return
        failures += 1
        setState(previous => ({ ...previous, loading: false, error }))
        if (latest && predicateRef.current(latest) && failures < maxConsecutiveErrors) {
          timer = window.setTimeout(() => load(false), interval)
        }
      }
    }
    load(true)
    return () => { active = false; if (timer) window.clearTimeout(timer) }
  // Callers provide primitive dependency values; refs keep callbacks from restarting polls.
  }, [...dependencies, revision, interval, maxConsecutiveErrors])

  const reload = useCallback(() => setRevision(value => value + 1), [])
  return { ...state, reload }
}

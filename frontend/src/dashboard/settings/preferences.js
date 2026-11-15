export const PREFERENCES_KEY = 'havosec-dashboard-preferences'
export const defaultPreferences = Object.freeze({ emailAlerts: true, criticalAlerts: true, weeklyReport: true, compactTables: false })

export function normalizePreferences(value) {
  return Object.fromEntries(Object.entries(defaultPreferences).map(([key, fallback]) => [
    key, typeof value?.[key] === 'boolean' ? value[key] : fallback,
  ]))
}

export function readPreferences(storage) {
  try {
    return normalizePreferences(JSON.parse((storage ?? localStorage).getItem(PREFERENCES_KEY)))
  } catch {
    return { ...defaultPreferences }
  }
}

export function savePreferences(value, storage = localStorage) {
  storage.setItem(PREFERENCES_KEY, JSON.stringify(normalizePreferences(value)))
}

export function resetPreferences(storage = localStorage) {
  storage.removeItem(PREFERENCES_KEY)
}

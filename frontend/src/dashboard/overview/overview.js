import { FINDING_STATUS } from '../findings/status'
import { REMEDIATION_STATUS } from '../remediation/status'

export const SEVERITY_COLORS = Object.freeze({ critical: '#ef4444', high: '#f59e0b', medium: '#eab308', low: '#10b981' })

export function summarizeOverview({ findings = [], runs = [], remediations = [], activity = [] } = {}) {
  const open = findings.filter(finding => finding.status !== FINDING_STATUS.RESOLVED)
  const severity = Object.keys(SEVERITY_COLORS).map(name => ({ name, count: open.filter(finding => finding.severity === name).length }))
  const dates = findings.map(finding => finding.firstDetected).filter(date => /^\d{4}-\d{2}-\d{2}$/.test(date || '') && Number.isFinite(Date.parse(date))).sort()
  // Seven days ending at the latest fixture observation, not a fabricated live week.
  const trend = []
  if (dates.length) {
    const end = new Date(dates[dates.length - 1] + 'T00:00:00Z')
    for (let offset = 6; offset >= 0; offset--) {
      const date = new Date(end)
      date.setUTCDate(end.getUTCDate() - offset)
      const day = date.toISOString().slice(0, 10)
      trend.push({ date: day, count: dates.filter(firstDetected => firstDetected <= day).length })
    }
  }
  const orderedRuns = [...runs].sort((a, b) => (b.startedAt || '').localeCompare(a.startedAt || '') || a.id.localeCompare(b.id))
  const severityRank = Object.keys(SEVERITY_COLORS)
  return {
    securityScore: null, // Requires an agreed scoring model and actual assessment coverage.
    openFindings: open.length,
    criticalFindings: open.filter(finding => finding.severity === 'critical').length,
    lastRun: orderedRuns.find(run => run.startedAt) || null,
    severity, trend,
    recentFindings: [...open].sort((a, b) => severityRank.indexOf(a.severity) - severityRank.indexOf(b.severity) || (b.lastDetected || '').localeCompare(a.lastDetected || '')).slice(0, 5),
    recentRuns: orderedRuns.slice(0, 5),
    recentActivity: [...activity].sort((a, b) => b.time.localeCompare(a.time)).slice(0, 5),
    pendingRemediations: remediations.filter(item => item.status !== REMEDIATION_STATUS.RESOLVED).length,
  }
}

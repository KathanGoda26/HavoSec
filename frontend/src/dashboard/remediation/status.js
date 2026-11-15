export const REMEDIATION_STATUS = Object.freeze({ PENDING: 'pending', IN_PROGRESS: 'in_progress', AWAITING_APPROVAL: 'awaiting_approval', APPROVED: 'approved', REJECTED: 'rejected', RESOLVED: 'resolved', FAILED: 'failed' })
export const REMEDIATION_STATUS_LABELS = Object.freeze({ pending: 'Pending', in_progress: 'In Progress', awaiting_approval: 'Awaiting Approval', approved: 'Approved', rejected: 'Rejected', resolved: 'Resolved', failed: 'Failed' })
export const VERIFICATION_STATUS_LABELS = Object.freeze({ not_started: 'Not started', queued: 'Queued', testing: 'Testing', verified: 'Verified', failed: 'Failed', inconclusive: 'Inconclusive' })

export function diffLineType(line) {
  if (line.startsWith('+++') || line.startsWith('---')) return 'header'
  if (line.startsWith('@@')) return 'hunk'
  if (line.startsWith('+')) return 'addition'
  if (line.startsWith('-')) return 'deletion'
  return 'context'
}

export function summarizeRemediations(items) {
  const counts = Object.fromEntries(Object.values(REMEDIATION_STATUS).map(status => [status, 0]))
  for (const item of items) {
    if (Object.hasOwn(counts, item.status)) counts[item.status] += 1
  }
  return counts
}

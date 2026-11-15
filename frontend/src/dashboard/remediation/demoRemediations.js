import { demoFindings } from '../findings/demoFindings'
import { REMEDIATION_STATUS } from './status'

// Read-only fixtures, not applied patches or persisted Findings-page drafts.
export const demoRemediations = demoFindings.map((finding, index) => ({
  id: `DEMO-REMEDIATION-${index + 1}`,
  findingId: finding.id,
  findingTitle: finding.title,
  project: finding.project,
  projectId: finding.projectId,
  asset: finding.asset,
  title: `Remediation for ${finding.title}`,
  proposedFix: finding.patch.description,
  actions: finding.patch.actions,
  status: index === 0 ? REMEDIATION_STATUS.PENDING : REMEDIATION_STATUS.AWAITING_APPROVAL,
  validationPlan: 'Review the proposal, test in an isolated environment, rerun the relevant security checks, and collect evidence before marking the finding resolved. None of these steps has been executed by this demo.',
}))

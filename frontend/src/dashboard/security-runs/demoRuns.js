import { demoAssets } from '../assets/demoAssets'

export const RUN_STATUS = Object.freeze({ QUEUED: 'queued', RUNNING: 'running', COMPLETED: 'completed', FAILED: 'failed', CANCELLED: 'cancelled' })
export const RUN_STATUS_LABELS = Object.freeze({ queued: 'Queued', running: 'Running', completed: 'Completed', failed: 'Failed', cancelled: 'Cancelled' })

// Illustrative snapshots only. No queue, scanner or agent is running.
export const demoRuns = [
  {
    id: 'DEMO-RUN-001', projectId: demoAssets[0].projectId, assetId: demoAssets[0].id,
    type: 'Application assessment', status: RUN_STATUS.COMPLETED, progress: 100,
    startedAt: '2026-08-01T09:00:00Z', completedAt: '2026-08-01T09:12:00Z',
    summary: 'Illustrative completed assessment with example findings. No actual tests were executed.',
    timeline: [
      { time: '09:00 UTC', message: 'Example assessment started' },
      { time: '09:04 UTC', message: 'Example reconnaissance recorded' },
      { time: '09:12 UTC', message: 'Example report completed' },
    ],
  },
  {
    id: 'DEMO-RUN-002', projectId: demoAssets[1].projectId, assetId: demoAssets[1].id,
    type: 'Repository assessment', status: RUN_STATUS.QUEUED, progress: 0,
    startedAt: null, completedAt: null,
    summary: 'Illustrative queued state. This is not submitted to a real execution queue.', timeline: [],
  },
]
export const getDemoRun = (id, projectId) => demoRuns.find(run => run.id === id && (!projectId || run.projectId === projectId))
export const getRunFindings = (findings, run) => findings.filter(finding => finding.sourceRun === run.id && finding.projectId === run.projectId && finding.assetId === run.assetId)

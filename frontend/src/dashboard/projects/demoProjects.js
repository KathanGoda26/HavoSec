// Shared illustrative workspace records. These are not backend organizations.
export const demoProjects = Object.freeze([
  { id: 'DEMO-PROJECT-001', name: 'Customer Portal (demo)', description: 'Example customer-facing web application.', status: 'Demo workspace' },
  { id: 'DEMO-PROJECT-002', name: 'Public API (demo)', description: 'An empty example project ready for future assets and security runs.', status: 'Demo workspace' },
])
export const DEFAULT_DEMO_PROJECT = demoProjects[0]

export const getDemoProject = id => demoProjects.find(project => project.id === id)
export const filterProjectRecords = (records, projectId) => projectId
  ? records.filter(record => record.projectId === projectId)
  : records

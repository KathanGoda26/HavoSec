import { DEFAULT_DEMO_PROJECT } from '../projects/demoProjects'

export const ASSET_TYPES = Object.freeze({ application: 'Application', repository: 'Repository', domain: 'Domain', api: 'API', host: 'Host', cloud: 'Cloud Resource', container: 'Container' })
// Illustrative inventory and observations, not live discovery results.
export const demoAssets = [
  {
    id: 'DEMO-ASSET-001', projectId: DEFAULT_DEMO_PROJECT.id,
    name: 'Web application (demo)', type: 'application', target: 'portal.example.test',
    description: 'Example customer portal application.',
    reconnaissance: {
      sourceRun: 'DEMO-RUN-001', observedAt: '2026-08-01',
      ports: [22, 80, 443, 3306, 8080],
      services: ['SSH (OpenSSH 8.2)', 'HTTP (nginx 1.18.0)', 'HTTPS (nginx 1.18.0)', 'MySQL (5.7.33)', 'HTTP-Proxy (8080)'],
      technologies: ['PHP 7.4', 'MySQL', 'nginx', 'WordPress 5.8', 'jQuery 3.6'],
    },
  },
  {
    id: 'DEMO-ASSET-002', projectId: DEFAULT_DEMO_PROJECT.id,
    name: 'Portal repository (demo)', type: 'repository', target: 'Example repository — not connected',
    description: 'Example source repository awaiting integration.', reconnaissance: null,
  },
]
export const DEFAULT_DEMO_ASSET = demoAssets[0]
export const getDemoAsset = (assetId, projectId) => demoAssets.find(asset => asset.id === assetId && (!projectId || asset.projectId === projectId))

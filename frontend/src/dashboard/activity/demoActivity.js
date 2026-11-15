import { ACTIVITY_TYPES } from './activity'
import { demoFindings } from '../findings/demoFindings'

// Historical illustrative events, not an audit trail of actions taken in this UI.
const legacySecurityEvents = [
  {
    id: 'EVT-9081',
    time: '2026-06-01 11:45:22',
    category: 'Auth Guard',
    description: 'Successful administrator login detected',
    ip: '10.0.0.101',
    severity: 'low',
    status: 'resolved'
  },
  {
    id: 'EVT-9076',
    time: '2026-06-01 11:32:05',
    category: 'Firewall',
    description: 'XSS payload attempt detected in search parameters',
    ip: '192.168.4.15',
    severity: 'high',
    status: 'blocked'
  },
  {
    id: 'EVT-9069',
    time: '2026-06-01 11:21:49',
    category: 'IDS Scan',
    description: 'Automated TCP port sweep detected across backend range',
    ip: '203.0.113.80',
    severity: 'medium',
    status: 'resolved'
  },
  {
    id: 'EVT-9055',
    time: '2026-06-01 11:10:12',
    category: 'WAF Block',
    description: 'SQL Injection signature matches request body parameters',
    ip: '185.190.140.2',
    severity: 'critical',
    status: 'blocked'
  },
  {
    id: 'EVT-9042',
    time: '2026-06-01 10:55:34',
    category: 'Integrity',
    description: 'Unscheduled software update check completed',
    ip: '127.0.0.1',
    severity: 'low',
    status: 'resolved'
  },
  {
    id: 'EVT-9031',
    time: '2026-06-01 10:32:18',
    category: 'Auth Guard',
    description: 'Brute-force attack warning: 5 failed attempts reached',
    ip: '94.200.12.65',
    severity: 'high',
    status: 'quarantined'
  },
  {
    id: 'EVT-9022',
    time: '2026-06-01 09:44:10',
    category: 'IDS Scan',
    description: 'File integrity check: /var/www/html matches baseline hashes',
    ip: '10.0.0.1',
    severity: 'low',
    status: 'resolved'
  },
  {
    id: 'EVT-9011',
    time: '2026-06-01 09:12:04',
    category: 'WAF Block',
    description: 'Attempt to download sensitive file /etc/passwd denied',
    ip: '198.51.100.42',
    severity: 'critical',
    status: 'blocked'
  }
]

const workspaceEvents = Object.keys(ACTIVITY_TYPES).filter(type => type !== 'security_event').map((eventType, index) => ({
  id: `DEMO-ACTIVITY-${index + 1}`,
  eventType,
  time: `2026-08-01 10:${String(index).padStart(2, '0')}:00`,
  category: ACTIVITY_TYPES[eventType],
  description: `${ACTIVITY_TYPES[eventType]} — illustrative workspace event`,
  project: demoFindings[0].project,
  projectId: demoFindings[0].projectId,
  actor: 'Demo workspace member',
  ip: null,
  severity: eventType.startsWith('finding_') ? 'high' : 'info',
  status: 'recorded',
}))

export const demoActivity = [
  ...workspaceEvents,
  ...legacySecurityEvents.map(event => ({ ...event, id: `DEMO-${event.id}`, eventType: event.id === 'EVT-9081' ? 'user_login' : 'security_event' })),
]

// Explicit fixtures, not live findings or verified CVE assignments.
import { FINDING_STATUS } from './status'
import { DEFAULT_DEMO_PROJECT } from '../projects/demoProjects'
import { DEFAULT_DEMO_ASSET } from '../assets/demoAssets'

const examples = [
    {
      id: 'CVE-2024-0001',
      cve: 'CVE-2024-0001',
      title: 'SQL Injection in Login Form',
      description: 'Improper input validation allows SQL injection attacks through the login form',
      severity: 'critical',
      cvss: 9.8,
      priority: 'immediate',
      component: 'Authentication Module',
      attackVector: 'Network',
      attackComplexity: 'Low',
      privilegesRequired: 'None',
      userInteraction: 'None',
      exploitAvailable: true,
      discoverySteps: [
        {
          title: 'Initial Reconnaissance',
          description: 'Scanner identified login form at /auth/login endpoint during automated crawling',
          code: 'GET /auth/login HTTP/1.1\nHost: target.com',
        },
        {
          title: 'Input Validation Testing',
          description: 'Tested various SQL injection payloads in username and password fields',
          code: 'username: admin\' OR \'1\'=\'1\npassword: anything',
        },
        {
          title: 'Vulnerability Confirmation',
          description: 'Successfully bypassed authentication using SQL injection, confirming the vulnerability',
          code: 'Response: 200 OK\nSet-Cookie: session=authenticated\nLocation: /dashboard',
        },
        {
          title: 'Impact Assessment',
          description: 'Verified ability to extract database contents and escalate privileges',
        },
      ],
      impact: {
        confidentiality: 'High',
        integrity: 'High',
        availability: 'High',
      },
      proofOfConcept: {
        description: 'The following payload demonstrates the SQL injection vulnerability:',
        code: `POST /auth/login HTTP/1.1
Host: target.com
Content-Type: application/json

{
  "username": "admin' OR '1'='1' --",
  "password": "anything"
}

Response: Successfully authenticated as admin`,
      },
      references: [
        {
          title: 'OWASP SQL Injection',
          url: 'https://owasp.org/www-community/attacks/SQL_Injection',
        },
        {
          title: 'CWE-89: SQL Injection',
          url: 'https://cwe.mitre.org/data/definitions/89.html',
        },
        {
          title: 'CVE-2024-0001 Details',
          url: 'https://nvd.nist.gov/vuln/detail/CVE-2024-0001',
        },
      ],
      patch: {
        version: '1.2.3',
        releaseDate: '2024-01-15',
        description: 'Security patch that implements parameterized queries and input validation',
        estimatedTime: '5-10 minutes',
        requiresRestart: true,
        actions: [
          'Replace direct SQL queries with parameterized statements',
          'Implement input validation and sanitization',
          'Add rate limiting to login endpoint',
          'Enable SQL injection detection in WAF',
          'Update authentication middleware',
        ],
        checklist: [
          'Backup current database',
          'Notify active users of upcoming restart',
          'Verify backup integrity',
          'Review patch notes and changelog',
        ],
      },
    },
    {
      id: 'CVE-2024-0002',
      cve: 'CVE-2024-0002',
      title: 'Cross-Site Scripting (XSS) Vulnerability',
      description: 'Reflected XSS vulnerability in search functionality',
      severity: 'high',
      cvss: 7.5,
      priority: 'high',
      component: 'Search Module',
      attackVector: 'Network',
      attackComplexity: 'Low',
      privilegesRequired: 'None',
      userInteraction: 'Required',
      exploitAvailable: false,
      discoverySteps: [
        {
          title: 'Endpoint Discovery',
          description: 'Identified search functionality at /search endpoint',
          code: 'GET /search?q=test HTTP/1.1',
        },
        {
          title: 'XSS Payload Testing',
          description: 'Tested various XSS payloads in search parameter',
          code: 'GET /search?q=<script>alert(1)</script>',
        },
        {
          title: 'Vulnerability Confirmation',
          description: 'Confirmed XSS execution in search results page',
          code: 'Response contained unescaped script tag in HTML',
        },
      ],
      impact: {
        confidentiality: 'Low',
        integrity: 'Low',
        availability: 'None',
      },
      proofOfConcept: {
        description: 'XSS payload that executes in user context:',
        code: `GET /search?q=<img src=x onerror=alert(document.cookie)>

Result: Cookie theft via JavaScript execution`,
      },
      references: [
        {
          title: 'OWASP XSS Guide',
          url: 'https://owasp.org/www-community/attacks/xss/',
        },
        {
          title: 'CWE-79: XSS',
          url: 'https://cwe.mitre.org/data/definitions/79.html',
        },
      ],
      patch: {
        version: '1.2.4',
        releaseDate: '2024-01-16',
        description: 'Implements output encoding and Content Security Policy',
        estimatedTime: '3-5 minutes',
        requiresRestart: false,
        actions: [
          'Add output encoding for user input',
          'Implement Content Security Policy headers',
          'Enable XSS protection in browser',
          'Sanitize search query parameters',
          'Update security middleware',
        ],
        checklist: [
          'Test search functionality after patch',
          'Verify CSP headers are present',
          'Check for any broken functionality',
        ],
      },
    },
  ]

export const demoFindings = examples.map((finding, index) => ({
  ...finding,
  id: `DEMO-FINDING-${index + 1}`,
  cve: null,
  status: FINDING_STATUS.NEW,
  projectId: DEFAULT_DEMO_PROJECT.id,
  project: DEFAULT_DEMO_PROJECT.name,
  assetId: DEFAULT_DEMO_ASSET.id,
  asset: DEFAULT_DEMO_ASSET.name,
  sourceRun: 'DEMO-RUN-001',
  category: index === 0 ? 'Injection' : 'Cross-site scripting',
  firstDetected: '2026-08-01',
  lastDetected: '2026-08-01',
  remediationStatus: 'Not started',
  references: finding.references.filter(reference => !reference.url.includes('nvd.nist.gov')),
}))

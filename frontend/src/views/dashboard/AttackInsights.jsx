import React, { useState, useMemo } from 'react'
import { useSecurityStore } from '@/stores/securityStore'
import { usePatchStore } from '@/stores/patchesStore'

function AttackInsights() {
  const securityStore = useSecurityStore()
  const patchStore = usePatchStore()

  // State
  const [selectedVuln, setSelectedVuln] = useState(null)
  const [patchModalVuln, setPatchModalVuln] = useState(null)
  const [patchChecklist, setPatchChecklist] = useState([])
  const [patchProgress, setPatchProgress] = useState({
    active: false,
    completed: false,
    percentage: 0,
    currentStep: '',
    logs: [],
  })

  // Mock vulnerabilities data with detailed discovery information
  const [vulnerabilitiesData, setVulnerabilitiesData] = useState([
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
  ])

  // Reconnaissance data
  const [openPorts] = useState([22, 80, 443, 3306, 8080])
  const [services] = useState([
    'SSH (OpenSSH 8.2)',
    'HTTP (nginx 1.18.0)',
    'HTTPS (nginx 1.18.0)',
    'MySQL (5.7.33)',
    'HTTP-Proxy (8080)',
  ])
  const [technologies] = useState([
    'PHP 7.4',
    'MySQL',
    'nginx',
    'WordPress 5.8',
    'jQuery 3.6',
  ])

  const hasScanResults = useMemo(() => vulnerabilitiesData.length > 0, [vulnerabilitiesData])

  const vulnerabilities = useMemo(() => {
    const summary = { critical: 0, high: 0, medium: 0, low: 0 }
    vulnerabilitiesData.forEach(v => {
      if (v.cvss >= 9.0) summary.critical++
      else if (v.cvss >= 7.0) summary.high++
      else if (v.cvss >= 4.0) summary.medium++
      else summary.low++
    })
    return summary
  }, [vulnerabilitiesData])

  const sortedVulnerabilities = useMemo(() => {
    return [...vulnerabilitiesData].sort((a, b) => b.cvss - a.cvss)
  }, [vulnerabilitiesData])

  const allChecklistComplete = useMemo(() => {
    return patchChecklist.length > 0 && patchChecklist.every(item => item === true)
  }, [patchChecklist])

  // Methods
  const showVulnDetails = (vuln) => {
    setSelectedVuln(vuln)
  }

  const closeVulnDetails = () => {
    setSelectedVuln(null)
  }

  const showPatchModal = (vuln) => {
    setSelectedVuln(null)
    setPatchModalVuln(vuln)
    setPatchChecklist(new Array(vuln.patch.checklist.length).fill(false))
    setPatchProgress({
      active: false,
      completed: false,
      percentage: 0,
      currentStep: '',
      logs: [],
    })
  }

  const closePatchModal = () => {
    setPatchModalVuln(null)
    setPatchChecklist([])
    setPatchProgress({
      active: false,
      completed: false,
      percentage: 0,
      currentStep: '',
      logs: [],
    })
  }

  const handleCheckboxChange = (index, checked) => {
    setPatchChecklist(prev => {
      const next = [...prev]
      next[index] = checked
      return next
    })
  }

  const applyPatch = async () => {
    if (!allChecklistComplete) return

    setPatchProgress({
      active: true,
      completed: false,
      percentage: 0,
      currentStep: 'Preparing patch environment...',
      logs: [{
        time: new Date().toLocaleTimeString(),
        message: 'Preparing patch environment...',
      }],
    })

    const steps = [
      { step: 'Downloading patch files...', duration: 1500, percentage: 40 },
      { step: 'Applying security fixes...', duration: 2000, percentage: 60 },
      { step: 'Running validation tests...', duration: 1500, percentage: 80 },
      { step: 'Finalizing patch...', duration: 1000, percentage: 100 },
    ]

    for (const stepInfo of steps) {
      // Wait for step duration
      await new Promise(resolve => setTimeout(resolve, stepInfo.duration))

      setPatchProgress(prev => ({
        ...prev,
        currentStep: stepInfo.step,
        percentage: stepInfo.percentage,
        logs: [
          ...prev.logs,
          {
            time: new Date().toLocaleTimeString(),
            message: stepInfo.step,
          },
        ],
      }))
    }

    // Wrap up
    await new Promise(resolve => setTimeout(resolve, 500))

    setPatchProgress(prev => ({
      ...prev,
      active: false,
      completed: true,
      logs: [
        ...prev.logs,
        {
          time: new Date().toLocaleTimeString(),
          message: '✓ Patch applied successfully!',
        },
      ],
    }))

    // Wait 2 seconds to show success message, then close modal and remove vulnerability
    await new Promise(resolve => setTimeout(resolve, 2000))

    // Add to patched vulnerabilities store
    patchStore.addPatchedVulnerability(patchModalVuln)

    // Remove the patched vulnerability from the list
    setVulnerabilitiesData(prev => prev.filter(v => v.id !== patchModalVuln.id))

    // Close the modal
    closePatchModal()
  }

  return (
    <div className="attack-insights-page">
      <h1 className="page-title">Attack Insights</h1>
      <p className="page-subtitle">
        Offensive security scan results - Vulnerabilities, exploits, and reconnaissance data
      </p>

      {/* Scan Results */}
      {hasScanResults ? (
        <div className="insights-content">
          {/* Vulnerability Summary Cards */}
          <div className="summary-grid">
            <div className="summary-card critical">
              <div className="card-icon">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth="1.5"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
                  />
                </svg>
              </div>
              <div className="card-content">
                <h4>Critical</h4>
                <p className="card-value">{vulnerabilities.critical}</p>
                <span className="card-label">CVSS 9.0-10.0</span>
              </div>
            </div>

            <div className="summary-card high">
              <div className="card-icon">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth="1.5"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
                  />
                </svg>
              </div>
              <div className="card-content">
                <h4>High</h4>
                <p className="card-value">{vulnerabilities.high}</p>
                <span className="card-label">CVSS 7.0-8.9</span>
              </div>
            </div>

            <div className="summary-card medium">
              <div className="card-icon">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth="1.5"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"
                  />
                </svg>
              </div>
              <div className="card-content">
                <h4>Medium</h4>
                <p className="card-value">{vulnerabilities.medium}</p>
                <span className="card-label">CVSS 4.0-6.9</span>
              </div>
            </div>

            <div className="summary-card low">
              <div className="card-icon">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth="1.5"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <div className="card-content">
                <h4>Low</h4>
                <p className="card-value">{vulnerabilities.low}</p>
                <span className="card-label">CVSS 0.1-3.9</span>
              </div>
            </div>
          </div>

          {/* Vulnerabilities List */}
          <div className="vulnerabilities-section">
            <h2>Discovered Vulnerabilities</h2>
            <div className="vulnerabilities-list">
              {sortedVulnerabilities.map(vuln => (
                <div
                  key={vuln.id}
                  className={`vuln-card ${vuln.severity}`}
                >
                  <div className="vuln-header">
                    <div className="vuln-title-section">
                      <h4>{vuln.title}</h4>
                      <span className="vuln-id">{vuln.cve || vuln.id}</span>
                    </div>
                    <div className="vuln-badges">
                      <span className={`severity-badge ${vuln.severity}`}>
                        {vuln.severity}
                      </span>
                      <span className="cvss-badge"> CVSS {vuln.cvss} </span>
                      <span className={`priority-badge ${vuln.priority}`}>
                        {vuln.priority} Priority
                      </span>
                    </div>
                  </div>

                  <p className="vuln-description">{vuln.description}</p>

                  <div className="vuln-details">
                    <div className="detail-row">
                      <span className="detail-label">Affected Component:</span>
                      <span className="detail-value">{vuln.component}</span>
                    </div>
                    <div className="detail-row">
                      <span className="detail-label">Attack Vector:</span>
                      <span className="detail-value">{vuln.attackVector}</span>
                    </div>
                    <div className="detail-row">
                      <span className="detail-label">Exploit Available:</span>
                      <span className={`detail-value ${vuln.exploitAvailable ? 'text-red' : 'text-green'}`}>
                        {vuln.exploitAvailable ? 'Yes' : 'No'}
                      </span>
                    </div>
                  </div>

                  <div className="vuln-actions">
                    <button onClick={() => showVulnDetails(vuln)} className="btn-secondary">
                      View Full Details
                    </button>
                    <button onClick={() => showPatchModal(vuln)} className="btn-primary">
                      Apply Patch
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Reconnaissance Data */}
          <div className="recon-section">
            <h2>Reconnaissance Data</h2>
            <div className="recon-grid">
              <div className="recon-card">
                <h4>Open Ports</h4>
                <div className="port-list">
                  {openPorts.map(port => (
                    <span key={port} className="port-badge">
                      {port}
                    </span>
                  ))}
                </div>
              </div>
              <div className="recon-card">
                <h4>Services Detected</h4>
                <ul className="service-list">
                  {services.map(service => (
                    <li key={service}>{service}</li>
                  ))}
                </ul>
              </div>
              <div className="recon-card">
                <h4>Technologies</h4>
                <div className="tech-list">
                  {technologies.map(tech => (
                    <span key={tech} className="tech-badge">
                      {tech}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="empty-state">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth="1.5"
            stroke="currentColor"
            className="empty-icon"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23-.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5"
            />
          </svg>
          <h2>No Attack Data Available</h2>
          <p>Run a security scan to see offensive security insights</p>
        </div>
      )}

      {/* Vulnerability Details Modal */}
      {selectedVuln && (
        <div className="modal-overlay" onClick={closeVulnDetails}>
          <div className="modal-container vuln-details-modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Vulnerability Details</h2>
              <button onClick={closeVulnDetails} className="close-btn">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth="1.5"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>

            <div className="modal-body">
              <div className="vuln-detail-header">
                <h3>{selectedVuln.title}</h3>
                <div className="badges">
                  <span className={`severity-badge ${selectedVuln.severity}`}>{selectedVuln.severity}</span>
                  <span className="cvss-badge">CVSS {selectedVuln.cvss}</span>
                </div>
              </div>

              {selectedVuln.discoverySteps && (
                <div className="detail-section">
                  <h4>How This Vulnerability Was Discovered</h4>
                  <div className="discovery-timeline">
                    {selectedVuln.discoverySteps.map((step, index) => (
                      <div key={index} className="timeline-item">
                        <div className="timeline-marker">{index + 1}</div>
                        <div className="timeline-content">
                          <h5>{step.title}</h5>
                          <p>{step.description}</p>
                          {step.code && (
                            <div className="code-block">
                              <pre>{step.code}</pre>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="detail-section">
                <h4>Technical Details</h4>
                <div className="tech-details-grid">
                  <div className="tech-detail">
                    <span className="label">CVE ID:</span>
                    <span className="value">{selectedVuln.cve}</span>
                  </div>
                  <div className="tech-detail">
                    <span className="label">CVSS Score:</span>
                    <span className="value">{selectedVuln.cvss} ({selectedVuln.severity})</span>
                  </div>
                  <div className="tech-detail">
                    <span className="label">Attack Vector:</span>
                    <span className="value">{selectedVuln.attackVector}</span>
                  </div>
                  <div className="tech-detail">
                    <span className="label">Attack Complexity:</span>
                    <span className="value">{selectedVuln.attackComplexity}</span>
                  </div>
                  <div className="tech-detail">
                    <span className="label">Privileges Required:</span>
                    <span className="value">{selectedVuln.privilegesRequired}</span>
                  </div>
                  <div className="tech-detail">
                    <span className="label">User Interaction:</span>
                    <span className="value">{selectedVuln.userInteraction}</span>
                  </div>
                </div>
              </div>

              {selectedVuln.impact && (
                <div className="detail-section">
                  <h4>Impact Analysis</h4>
                  <div className="impact-grid">
                    <div className="impact-item">
                      <span className="impact-label">Confidentiality:</span>
                      <span className={`impact-value impact-${selectedVuln.impact.confidentiality.toLowerCase()}`}>
                        {selectedVuln.impact.confidentiality}
                      </span>
                    </div>
                    <div className="impact-item">
                      <span className="impact-label">Integrity:</span>
                      <span className={`impact-value impact-${selectedVuln.impact.integrity.toLowerCase()}`}>
                        {selectedVuln.impact.integrity}
                      </span>
                    </div>
                    <div className="impact-item">
                      <span className="impact-label">Availability:</span>
                      <span className={`impact-value impact-${selectedVuln.impact.availability.toLowerCase()}`}>
                        {selectedVuln.impact.availability}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {selectedVuln.proofOfConcept && (
                <div className="detail-section">
                  <h4>Proof of Concept</h4>
                  <div className="poc-content">
                    <p>{selectedVuln.proofOfConcept.description}</p>
                    <div className="code-block">
                      <pre>{selectedVuln.proofOfConcept.code}</pre>
                    </div>
                  </div>
                </div>
              )}

              {selectedVuln.references && (
                <div className="detail-section">
                  <h4>References</h4>
                  <ul className="references-list">
                    {selectedVuln.references.map((ref, index) => (
                      <li key={index}>
                        <a href={ref.url} target="_blank" rel="noopener noreferrer">{ref.title}</a>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            <div className="modal-footer">
              <button onClick={closeVulnDetails} className="btn-secondary">
                Close
              </button>
              <button onClick={() => showPatchModal(selectedVuln)} className="btn-primary">
                Apply Patch
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Patch Application Modal */}
      {patchModalVuln && (
        <div className="modal-overlay" onClick={closePatchModal}>
          <div className="modal-container patch-modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Apply Security Patch</h2>
              <button onClick={closePatchModal} className="close-btn">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth="1.5"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>

            <div className="modal-body">
              <div className="patch-info">
                <h3>Patch for: {patchModalVuln.title}</h3>
                <p className="patch-description">{patchModalVuln.patch.description}</p>
              </div>

              <div className="patch-section">
                <h4>Patch Details</h4>
                <div className="patch-details-grid">
                  <div className="patch-detail">
                    <span className="label">Patch Version:</span>
                    <span className="value">{patchModalVuln.patch.version}</span>
                  </div>
                  <div className="patch-detail">
                    <span className="label">Release Date:</span>
                    <span className="value">{patchModalVuln.patch.releaseDate}</span>
                  </div>
                  <div className="patch-detail">
                    <span className="label">Estimated Time:</span>
                    <span className="value">{patchModalVuln.patch.estimatedTime}</span>
                  </div>
                  <div className="patch-detail">
                    <span className="label">Requires Restart:</span>
                    <span className="value">{patchModalVuln.patch.requiresRestart ? 'Yes' : 'No'}</span>
                  </div>
                </div>
              </div>

              <div className="patch-section">
                <h4>What This Patch Will Do</h4>
                <ul className="patch-actions-list">
                  {patchModalVuln.patch.actions.map((action, index) => (
                    <li key={index}>
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                        strokeWidth="1.5"
                        stroke="currentColor"
                        className="check-icon"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                        />
                      </svg>
                      {action}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="patch-section">
                <h4>Pre-Patch Checklist</h4>
                <div className="checklist">
                  {patchModalVuln.patch.checklist.map((item, index) => (
                    <label key={index} className="checkbox-item">
                      <input
                        type="checkbox"
                        checked={!!patchChecklist[index]}
                        onChange={e => handleCheckboxChange(index, e.target.checked)}
                      />
                      <span>{item}</span>
                    </label>
                  ))}
                </div>
              </div>

              {patchProgress.active && (
                <div className="patch-section">
                  <h4>Patch Progress</h4>
                  <div className="progress-container">
                    <div className="progress-bar">
                      <div
                        className="progress-fill"
                        style={{ width: `${patchProgress.percentage}%` }}
                      ></div>
                    </div>
                    <p className="progress-text">
                      {patchProgress.currentStep} ({patchProgress.percentage}%)
                    </p>
                  </div>
                  <div className="progress-logs">
                    {patchProgress.logs.map((log, index) => (
                      <div key={index} className="log-entry">
                        <span className="log-time">{log.time}</span>
                        <span className="log-message">{log.message}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {patchProgress.completed && (
                <div className="patch-section success-message">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth="1.5"
                    stroke="currentColor"
                    className="success-icon"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  <h4>Patch Applied Successfully!</h4>
                  <p>The vulnerability has been patched. Your system is now secure.</p>
                </div>
              )}
            </div>

            <div className="modal-footer">
              <button onClick={closePatchModal} className="btn-secondary">
                Cancel
              </button>
              <button
                onClick={applyPatch}
                disabled={!allChecklistComplete || patchProgress.active}
                className="btn-primary"
              >
                {patchProgress.active ? 'Applying...' : 'Apply Patch'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default AttackInsights

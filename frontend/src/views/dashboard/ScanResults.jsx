import React, { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSecurityStore } from '@/stores/securityStore'

function formatTime(date) {
  if (!date) return 'N/A'
  const d = new Date(date)
  return d.toLocaleString()
}

function getRiskClass(score) {
  if (score >= 80) return 'risk-critical'
  if (score >= 60) return 'risk-high'
  if (score >= 40) return 'risk-medium'
  return 'risk-low'
}

function ScanResults() {
  const navigate = useNavigate()
  const securityStore = useSecurityStore()

  const [activeTab, setActiveTab] = useState('vulnerabilities')
  const [progressPercentage, setProgressPercentage] = useState(0)
  const [activeAgents, setActiveAgents] = useState(0)
  const [timeElapsed, setTimeElapsed] = useState('0m 0s')

  const scanInfo = useMemo(() => securityStore.currentScan || {}, [securityStore.currentScan])
  const hasScanData = useMemo(() => !!securityStore.currentScan, [securityStore.currentScan])
  const scanStatus = useMemo(() => scanInfo.status || 'pending', [scanInfo.status])

  const totalAgents = 7

  // Mock vulnerabilities data
  const [vulnerabilitiesData] = useState([
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
      exploitAvailable: true,
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
      exploitAvailable: false,
    },
    {
      id: 'CVE-2024-0003',
      cve: 'CVE-2024-0003',
      title: 'Insecure Direct Object Reference',
      description: "Users can access other users' data by manipulating object IDs",
      severity: 'high',
      cvss: 8.1,
      priority: 'high',
      component: 'API Endpoints',
      attackVector: 'Network',
      exploitAvailable: true,
    },
    {
      id: 'CVE-2024-0004',
      cve: 'CVE-2024-0004',
      title: 'Weak Password Policy',
      description: 'Password policy allows weak passwords',
      severity: 'medium',
      cvss: 5.3,
      priority: 'medium',
      component: 'User Management',
      attackVector: 'Local',
      exploitAvailable: false,
    },
    {
      id: 'CVE-2024-0005',
      cve: 'CVE-2024-0005',
      title: 'Missing Security Headers',
      description: 'Application missing critical security headers',
      severity: 'low',
      cvss: 3.7,
      priority: 'low',
      component: 'Web Server',
      attackVector: 'Network',
      exploitAvailable: false,
    },
  ])

  // Vulnerabilities summary
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

  const totalVulnerabilities = useMemo(() => {
    return (
      vulnerabilities.critical +
      vulnerabilities.high +
      vulnerabilities.medium +
      vulnerabilities.low
    )
  }, [vulnerabilities])

  const sortedVulnerabilities = useMemo(() => {
    return [...vulnerabilitiesData].sort((a, b) => b.cvss - a.cvss)
  }, [vulnerabilitiesData])

  // Patches data
  const [patches] = useState([
    {
      id: 'PATCH-001',
      title: 'Security Update 2024-01',
      description: 'Critical security patches for authentication and SQL injection vulnerabilities',
      status: 'applied',
      vulnerabilitiesFixed: 2,
      appliedAt: new Date(Date.now() - 3600000),
      successRate: 100,
    },
    {
      id: 'PATCH-002',
      title: 'XSS Protection Update',
      description: 'Implements input sanitization and output encoding',
      status: 'pending',
      vulnerabilitiesFixed: 1,
      appliedAt: null,
      successRate: 0,
    },
  ])

  // AI Analysis
  const aiAnalysis = useMemo(() => ({
    summary:
      'Your system has 5 vulnerabilities with 1 critical issue requiring immediate attention. The overall security posture is moderate with several high-priority items that should be addressed within 48 hours.',
    riskScore: 72,
    attackSurface: 'Medium',
    remediationPriority: 'High',
    recommendations: [
      'Immediately patch SQL injection vulnerability (CVE-2024-0001)',
      'Implement Web Application Firewall (WAF) to protect against common attacks',
      'Enable multi-factor authentication for all user accounts',
      'Review and strengthen password policies',
      'Add security headers (CSP, HSTS, X-Frame-Options)',
    ],
  }), [])

  // Report summary
  const reportSummary =
    'This comprehensive security assessment identified 5 vulnerabilities across your infrastructure. ' +
    'Critical findings include SQL injection and IDOR vulnerabilities that require immediate remediation. ' +
    'The scan covered authentication, API security, and web application components. ' +
    'Detailed remediation steps and patches are available for all identified issues.'

  const tabs = useMemo(() => [
    {
      id: 'vulnerabilities',
      label: 'Vulnerabilities',
      count: totalVulnerabilities,
    },
    { id: 'patches', label: 'Patches & Fixes', count: patches.length },
    { id: 'analysis', label: 'AI Analysis', count: null },
    { id: 'report', label: 'Report', count: null },
  ], [totalVulnerabilities, patches.length])

  useEffect(() => {
    let startTimeStamp = Date.now()

    const intervalId = setInterval(() => {
      // Update progress
      setProgressPercentage(prev => {
        if (prev < 100 && scanStatus === 'running') {
          const next = Math.min(100, prev + Math.random() * 5)
          setActiveAgents(Math.min(totalAgents, Math.floor((next / 100) * totalAgents)))
          return next
        }
        return prev
      })

      // Update elapsed time
      const elapsed = Date.now() - startTimeStamp
      const minutes = Math.floor(elapsed / 60000)
      const seconds = Math.floor((elapsed % 60000) / 1000)
      setTimeElapsed(`${minutes}m ${seconds}s`)
    }, 1000)

    return () => clearInterval(intervalId)
  }, [scanStatus])

  return (
    <div className="scan-results-page">
      {/* Header */}
      <div className="results-header">
        <div>
          <h1>Security Scan Results</h1>
          <p className="subtitle">{scanInfo.target || 'No active scan'}</p>
        </div>
        <button onClick={() => navigate('/dashboard/overview')} className="btn-back">
          ← Back to Dashboard
        </button>
      </div>

      {/* No Scan State */}
      {!hasScanData ? (
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
          <h2>No Scan Results</h2>
          <p>Run a security scan to see detailed results here</p>
          <button onClick={() => navigate('/dashboard/overview')} className="btn-primary">
            Go to Dashboard
          </button>
        </div>
      ) : (
        <div className="results-content">
          {/* Progress Section */}
          <div className="progress-section">
            <div className="progress-card">
              <div className="progress-header">
                <h3>Scan Progress</h3>
                <span className={`status-badge ${scanStatus}`}>{scanStatus}</span>
              </div>

              <div className="progress-bar-container">
                <div className="progress-bar">
                  <div
                    className="progress-fill"
                    style={{ width: `${progressPercentage}%` }}
                  ></div>
                </div>
                <span className="progress-text">{Math.floor(progressPercentage)}% Complete</span>
              </div>

              <div className="progress-details">
                <div className="detail-item">
                  <span className="label">Started:</span>
                  <span className="value">{formatTime(scanInfo.startTime)}</span>
                </div>
                <div className="detail-item">
                  <span className="label">Estimated Time:</span>
                  <span className="value">{scanInfo.estimatedTime || '15-20 min'}</span>
                </div>
                <div className="detail-item">
                  <span className="label">Time Elapsed:</span>
                  <span className="value">{timeElapsed}</span>
                </div>
                <div className="detail-item">
                  <span className="label">Agents Running:</span>
                  <span className="value">{activeAgents}/{totalAgents}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Summary Cards */}
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

          {/* Tabs */}
          <div className="tabs-container">
            <div className="tabs">
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`tab ${activeTab === tab.id ? 'active' : ''}`}
                >
                  {tab.label}
                  {tab.count !== null && <span className="tab-badge">{tab.count}</span>}
                </button>
              ))}
            </div>

            {/* Tab Content */}
            <div className="tab-content">
              {/* Vulnerabilities Tab */}
              {activeTab === 'vulnerabilities' && (
                <div className="vulnerabilities-list">
                  {sortedVulnerabilities.map(vuln => (
                    <div key={vuln.id} className="vuln-card">
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
                        <button className="btn-secondary">View Details</button>
                        <button className="btn-primary">Apply Patch</button>
                      </div>
                    </div>
                  ))}

                  {sortedVulnerabilities.length === 0 && (
                    <div className="empty-message">
                      <p>No vulnerabilities found</p>
                    </div>
                  )}
                </div>
              )}

              {/* Patches Tab */}
              {activeTab === 'patches' && (
                <div className="patches-list">
                  {patches.map(patch => (
                    <div key={patch.id} className="patch-card">
                      <div className="patch-header">
                        <div>
                          <h4>{patch.title}</h4>
                          <p className="patch-description">{patch.description}</p>
                        </div>
                        <span className={`status-badge ${patch.status}`}>{patch.status}</span>
                      </div>

                      <div className="patch-details">
                        <div className="detail-item">
                          <span className="label">Vulnerabilities Fixed:</span>
                          <span className="value">{patch.vulnerabilitiesFixed}</span>
                        </div>
                        <div className="detail-item">
                          <span className="label">Applied:</span>
                          <span className="value">{formatTime(patch.appliedAt)}</span>
                        </div>
                        <div className="detail-item">
                          <span className="label">Success Rate:</span>
                          <span className="value">{patch.successRate}%</span>
                        </div>
                      </div>

                      <div className="patch-actions">
                        <button className="btn-secondary">View Changelog</button>
                        {patch.status === 'pending' && <button className="btn-primary">Apply Now</button>}
                        {patch.status === 'applied' && <button className="btn-secondary">Rollback</button>}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Analysis Tab */}
              {activeTab === 'analysis' && (
                <div className="analysis-section">
                  <div className="analysis-card">
                    <h3>AI-Powered Risk Analysis</h3>
                    <p className="analysis-summary">{aiAnalysis.summary}</p>

                    <div className="analysis-metrics">
                      <div className="metric">
                        <span className="metric-label">Overall Risk Score</span>
                        <div className={`risk-score ${getRiskClass(aiAnalysis.riskScore)}`}>
                          {aiAnalysis.riskScore}/100
                        </div>
                      </div>
                      <div className="metric">
                        <span className="metric-label">Attack Surface</span>
                        <span className="metric-value">{aiAnalysis.attackSurface}</span>
                      </div>
                      <div className="metric">
                        <span className="metric-label">Remediation Priority</span>
                        <span className="metric-value">{aiAnalysis.remediationPriority}</span>
                      </div>
                    </div>

                    <div className="recommendations">
                      <h4>Top Recommendations</h4>
                      <ul>
                        {aiAnalysis.recommendations.map((rec, index) => (
                          <li key={index}>{rec}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              )}

              {/* Report Tab */}
              {activeTab === 'report' && (
                <div className="report-section">
                  <div className="report-actions">
                    <button className="btn-primary">
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                        strokeWidth="1.5"
                        stroke="currentColor"
                        className="icon"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3"
                        />
                      </svg>
                      Download PDF Report
                    </button>
                    <button className="btn-secondary">
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                        strokeWidth="1.5"
                        stroke="currentColor"
                        className="icon"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3"
                        />
                      </svg>
                      Export as JSON
                    </button>
                    <button className="btn-secondary">
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                        strokeWidth="1.5"
                        stroke="currentColor"
                        className="icon"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M7.217 10.907a2.25 2.25 0 100 2.186m0-2.186c.18.324.283.696.283 1.093s-.103.77-.283 1.093m0-2.186l9.566-5.314m-9.566 7.5l9.566 5.314m0 0a2.25 2.25 0 103.935 2.186 2.25 2.25 0 00-3.935-2.186zm0-12.814a2.25 2.25 0 103.933-2.185 2.25 2.25 0 00-3.933 2.185z"
                        />
                      </svg>
                      Share Report
                    </button>
                  </div>

                  <div className="report-preview">
                    <h3>Executive Summary</h3>
                    <p>{reportSummary}</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ScanResults

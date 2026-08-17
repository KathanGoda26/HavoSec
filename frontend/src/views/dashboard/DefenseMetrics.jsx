import React, { useState, useMemo } from 'react'

function DefenseMetrics() {
  // Mock data
  const [threatsDetected] = useState(12)
  const [hardeningItems] = useState(8)
  const [patchesApplied] = useState(15)
  const [complianceScore] = useState(87)

  const [threats] = useState([
    {
      id: 1,
      title: 'Suspicious Login Attempt',
      description: 'Multiple failed login attempts from IP 192.168.1.100',
      severity: 'high',
      source: '192.168.1.100',
      action: 'Blocked',
      timestamp: '2 minutes ago',
    },
    {
      id: 2,
      title: 'Port Scan Detected',
      description: 'Systematic port scanning activity detected',
      severity: 'medium',
      source: '10.0.0.15',
      action: 'Monitored',
      timestamp: '15 minutes ago',
    },
    {
      id: 3,
      title: 'Malware Signature Match',
      description: 'Known malware signature detected in uploaded file',
      severity: 'critical',
      source: 'File Upload',
      action: 'Quarantined',
      timestamp: '1 hour ago',
    },
  ])

  const [hardeningRecommendations] = useState([
    {
      id: 1,
      title: 'Enable Multi-Factor Authentication',
      description: 'Implement MFA for all user accounts to enhance security',
      priority: 'high',
    },
    {
      id: 2,
      title: 'Update SSL/TLS Configuration',
      description: 'Disable weak ciphers and enable TLS 1.3',
      priority: 'high',
    },
    {
      id: 3,
      title: 'Implement Rate Limiting',
      description: 'Add rate limiting to API endpoints to prevent abuse',
      priority: 'medium',
    },
    {
      id: 4,
      title: 'Enable Security Headers',
      description: 'Add CSP, HSTS, and X-Frame-Options headers',
      priority: 'medium',
    },
  ])

  const [patches] = useState([
    {
      id: 'PATCH-001',
      title: 'Security Update 2024-01',
      description: 'Critical security patches for authentication and SQL injection vulnerabilities',
      status: 'applied',
      vulnerabilitiesFixed: 2,
      appliedAt: '2 days ago',
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
    {
      id: 'PATCH-003',
      title: 'Dependency Security Update',
      description: 'Updates vulnerable npm packages to latest secure versions',
      status: 'applied',
      vulnerabilitiesFixed: 5,
      appliedAt: '1 week ago',
      successRate: 100,
    },
  ])

  const hasDefenseData = useMemo(() => true, [])

  return (
    <div className="defense-metrics-page">
      <h1 className="page-title">Defense Metrics</h1>
      <p className="page-subtitle">
        Defensive security posture - Threat detection, hardening, and compliance
      </p>

      {/* Defense Results */}
      {hasDefenseData ? (
        <div className="defense-content">
          {/* Defense Summary Cards */}
          <div className="summary-grid">
            <div className="summary-card threats">
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
                <h4>Threats Detected</h4>
                <p className="card-value">{threatsDetected}</p>
                <span className="card-label">Last 24 hours</span>
              </div>
            </div>

            <div className="summary-card hardening">
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
                    d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z"
                  />
                </svg>
              </div>
              <div className="card-content">
                <h4>Hardening Items</h4>
                <p className="card-value">{hardeningItems}</p>
                <span className="card-label">Recommendations</span>
              </div>
            </div>

            <div className="summary-card patches">
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
                    d="M11.42 15.17L17.25 21A2.652 2.652 0 0021 17.25l-5.877-5.877M11.42 15.17l2.496-3.03c.317-.384.74-.626 1.208-.766M11.42 15.17l-4.655 5.653a2.548 2.548 0 11-3.586-3.586l6.837-5.63m5.108-.233c.55-.164 1.163-.188 1.743-.14a4.5 4.5 0 004.486-6.336l-3.276 3.277a3.004 3.004 0 01-2.25-2.25l3.276-3.276a4.5 4.5 0 00-6.336 4.486c.091 1.076-.071 2.264-.904 2.95l-.102.085m-1.745 1.437L5.909 7.5H4.5L2.25 3.75l1.5-1.5L7.5 4.5v1.409l4.26 4.26m-1.745 1.437l1.745-1.437m6.615 8.206L15.75 15.75M4.867 19.125h.008v.008h-.008v-.008z"
                  />
                </svg>
              </div>
              <div className="card-content">
                <h4>Patches Applied</h4>
                <p className="card-value">{patchesApplied}</p>
                <span className="card-label">This month</span>
              </div>
            </div>

            <div className="summary-card compliance">
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
                    d="M9 12.75L11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 01-1.043 3.296 3.745 3.745 0 01-3.296 1.043A3.745 3.745 0 0112 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 01-3.296-1.043 3.745 3.745 0 01-1.043-3.296A3.745 3.745 0 013 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 011.043-3.296 3.746 3.746 0 013.296-1.043A3.746 3.746 0 0112 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 013.296 1.043 3.746 3.746 0 011.043 3.296A3.745 3.745 0 0121 12z"
                  />
                </svg>
              </div>
              <div className="card-content">
                <h4>Compliance Score</h4>
                <p className="card-value">{complianceScore}%</p>
                <span className="card-label">CIS Benchmark</span>
              </div>
            </div>
          </div>

          {/* Threat Detection */}
          <div className="threats-section">
            <h2>Detected Threats</h2>
            <div className="threats-list">
              {threats.map(threat => (
                <div
                  key={threat.id}
                  className={`threat-card ${threat.severity}`}
                >
                  <div className="threat-header">
                    <div>
                      <h4>{threat.title}</h4>
                      <p className="threat-time">{threat.timestamp}</p>
                    </div>
                    <span className={`severity-badge ${threat.severity}`}>
                      {threat.severity}
                    </span>
                  </div>
                  <p className="threat-description">{threat.description}</p>
                  <div className="threat-details">
                    <span><strong>Source:</strong> {threat.source}</span>
                    <span><strong>Action:</strong> {threat.action}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Hardening Recommendations */}
          <div className="hardening-section">
            <h2>Security Hardening Recommendations</h2>
            <div className="hardening-list">
              {hardeningRecommendations.map(item => (
                <div key={item.id} className="hardening-card">
                  <div className="hardening-header">
                    <h4>{item.title}</h4>
                    <span className={`priority-badge ${item.priority}`}>
                      {item.priority} Priority
                    </span>
                  </div>
                  <p className="hardening-description">{item.description}</p>
                  <div className="hardening-actions">
                    <button className="btn-secondary">View Details</button>
                    <button className="btn-primary">Apply Fix</button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Patches */}
          <div className="patches-section">
            <h2>Security Patches</h2>
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
                      <span className="value">{patch.appliedAt || 'Pending'}</span>
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
              d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z"
            />
          </svg>
          <h2>No Defense Data Available</h2>
          <p>Run a security scan to see defensive metrics</p>
        </div>
      )}
    </div>
  )
}

export default DefenseMetrics
